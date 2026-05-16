"""Format ContextBundle dicts for LLM prompts with sanitization (T2.1 / T2.3)."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

import structlog

from app.context.bundle import ContextBundle, ContextBundleBuilder
from app.investigator.prompt_sanitizer import sanitize_text
from app.tools.security_skills import format_security_skills_for_prompt

logger = structlog.get_logger()

_BUNDLE_APPEND_MAX_LEN = 8000


def stable_incident_uuid(case_id: str, tenant_id: str) -> uuid.UUID:
    """Deterministic UUID for bundle builder when ``case_id`` is not a UUID."""
    try:
        return uuid.UUID(str(case_id))
    except (ValueError, TypeError, AttributeError):
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"{tenant_id}:{case_id}")


def _bundle_state_for_investigator(
    *,
    case_id: str,
    tenant_id: str,
    alert_summary: str,
    raw_alert: dict[str, Any],
) -> SimpleNamespace:
    return SimpleNamespace(
        incident_id=stable_incident_uuid(case_id, tenant_id),
        tenant_id=tenant_id,
        alert_summary=alert_summary,
        raw_alert=raw_alert,
    )


async def prefetch_context_bundle_dict(
    *,
    case_id: str,
    tenant_id: str,
    alert_summary: str,
    raw_alert: dict[str, Any],
) -> dict[str, Any]:
    """Build a JSON-serialisable ContextBundle dict; never raises."""
    try:
        builder = ContextBundleBuilder()
        bundle = await builder.build(
            _bundle_state_for_investigator(
                case_id=case_id,
                tenant_id=tenant_id,
                alert_summary=alert_summary,
                raw_alert=raw_alert,
            )
        )
        return bundle.model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        safe_case = str(case_id).replace("\r", " ").replace("\n", " ")[:200]
        safe_tenant = str(tenant_id).replace("\r", " ").replace("\n", " ")[:120]
        logger.warning(
            "context_bundle.prefetch_failed",
            error=str(exc).replace("\r", " ").replace("\n", " ")[:500],
            case_id=safe_case,
            tenant_id=safe_tenant,
        )
        return {}


def format_bundle_prompt_append(bundle_dict: dict[str, Any] | None) -> str:
    """Return sanitized text to append to an LLM prompt, or empty string."""
    if not bundle_dict:
        return ""

    parts: list[str] = []

    # CARD-010: security skill references are carried alongside the normal
    # ContextBundle. They are third-party content and are rendered explicitly as
    # untrusted reference material for the agents.
    skill_append = format_security_skills_for_prompt(
        bundle_dict.get("security_skills_library") if isinstance(bundle_dict, dict) else []
    )
    if skill_append:
        parts.append(sanitize_text(skill_append, max_len=6000))

    # Only validate as ContextBundle when the core required fields are present.
    # This keeps security_skills_library usable even when the broader context
    # prefetcher is disabled or unavailable.
    if not isinstance(bundle_dict, dict) or "incident_id" not in bundle_dict:
        return "\n\n".join(parts)

    try:
        bundle = ContextBundle.model_validate(bundle_dict)
        lines = bundle.prompt_context_lines()
        if lines:
            parts.append(sanitize_text("\n".join(lines), max_len=_BUNDLE_APPEND_MAX_LEN))
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "context_bundle.format_failed",
            error=str(exc).replace("\r", " ").replace("\n", " ")[:500],
        )
    return "\n\n".join(part for part in parts if part)
