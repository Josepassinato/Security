"""F4 renderer motor — sandboxed Jinja2 for AML evidence dossiers.

Why a sandbox (engineering mandate, not optional):

* The narrative template is authored by a human (BSA officer). Rendering a
  template *string* with the default ``jinja2.Environment`` is a Server-Side
  Template Injection → RCE vector. Templates run here in
  ``jinja2.sandbox.SandboxedEnvironment``, which blocks dunder access and
  unsafe callables.
* The *values* rendered into the template (e.g. ``counterparty_name``, the
  engine's raw output) are influenced by third parties — an onboarding name
  could carry ``<script>`` or stray markup. ``autoescape`` is on, so every
  value is HTML-escaped unless explicitly wrapped as trusted ``Markup``.

This is the single motor behind both the per-case dossier and the portfolio
report; only the template string and the context differ. It deliberately does
NOT touch ``renderer.render_evidence_html`` — the existing Bacen evidence packs
keep their hardcoded, deterministic layout untouched.

Division of labour (signed): the BSA officer writes the template (the layout
that survives an OFAC exam is their domain); engineering guarantees that
rendering it is sandboxed and escaped.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from jinja2 import select_autoescape
from jinja2.sandbox import SandboxedEnvironment
from markupsafe import Markup

from app.evidence_pack.renderer import WeasyPrintUnavailableError

__all__ = [
    "render_narrative",
    "render_screening_case_dossier",
    "render_dossier_pdf",
]


# Fields the dossier template may read off a screening_decisions row. Kept
# explicit so an ORM object and a plain dict render identically, and so we
# never leak an unexpected attribute into a template's context.
_SCREENING_FIELDS = (
    "id",
    "tenant_id",
    "case_id",
    "counterparty_name",
    "counterparty_normalized",
    "counterparty_id",
    "counterparty_id_type",
    "counterparty_jurisdiction",
    "screening_trigger",
    "matching_engine",
    "list_of_record",
    "list_source",
    "list_dataset",
    "list_version",
    "list_release_date",
    "engine_raw_result",
    "match_score",
    "scoring_rule_version",
    "decision",
    "disposition",
    "human_reviewer",
    "rationale",
    "screened_at",
    "created_at",
    "prev_hash",
    "entry_hash",
)


def _build_env() -> SandboxedEnvironment:
    return SandboxedEnvironment(
        autoescape=select_autoescape(default=True, default_for_string=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_narrative(template_str: str, context: Mapping[str, Any]) -> str:
    """Render a Jinja2 narrative template in a sandbox with autoescape on.

    Raises ``jinja2.exceptions.SecurityError`` if the template attempts a
    sandbox-forbidden operation (dunder access, unsafe callable, …) and
    ``jinja2.exceptions.TemplateError`` on a malformed template.
    """
    env = _build_env()
    template = env.from_string(template_str)
    return template.render(**dict(context))


def _decision_mapping(decision: Any) -> dict[str, Any]:
    if isinstance(decision, Mapping):
        return dict(decision)
    return {field: getattr(decision, field, None) for field in _SCREENING_FIELDS}


def render_screening_case_dossier(
    *,
    decision: Any,
    template_str: str,
    tenant_name: str,
    verification_method: str,
    render_blocks: Mapping[str, str] | None = None,
) -> str:
    """Render the per-case screening dossier from one screening_decisions row.

    ``decision`` may be a ``ScreeningDecision`` ORM instance or a plain mapping.
    ``render_blocks`` carries the §3/§4/§5 prose the compliance team authors;
    each is treated as TRUSTED, already-sanitized HTML (wrapped as ``Markup``)
    — the caller is responsible for having produced it safely (ideally via this
    same motor). Counterparty/engine values are always autoescaped.
    """
    data = _decision_mapping(decision)
    data["tenant_name"] = tenant_name

    context: dict[str, Any] = {
        "decision": data,
        "verification_method": verification_method,
    }
    for key, value in (render_blocks or {}).items():
        context[key] = Markup(value)

    return render_narrative(template_str, context)


def render_dossier_pdf(html_str: str) -> bytes:
    """Render dossier HTML to PDF via WeasyPrint (same fallback contract as
    ``renderer.render_evidence_pdf``)."""
    try:
        from weasyprint import HTML  # noqa: PLC0415 — lazy: native stack optional
    except Exception as exc:  # ImportError / missing Cairo-Pango
        raise WeasyPrintUnavailableError(
            "WeasyPrint native stack unavailable; cannot render dossier PDF"
        ) from exc
    return HTML(string=html_str).write_pdf()
