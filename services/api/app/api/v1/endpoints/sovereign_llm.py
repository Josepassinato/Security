"""Sovereign LLM status endpoint — CARD-015 Tarefa #5 (admin panel backend).

What this exposes
-----------------

A read-only snapshot of the **Sovereign LLM deployment** (Modalidade A
— Mac Mini, or Modalidade B — VPS Llama) configured for the current
process. Pairs with the ``/settings/sovereign-llm`` panel in the web
app and with the bash helper ``$QUARRY_HOME/bin/healthcheck.sh``
shipped by ``scripts/sovereign-appliance/install-vps-linux.sh``.

The endpoint is **independent of** ``/llm/status``:

* ``/llm/status``           — answers "what cloud-BYOK LLM would this
  pod call right now?" (uses ``OPENAI_*`` + ``tenant_llm_credentials``).
* ``/llm/sovereign/status`` — answers "is the sovereign deployment up,
  what model is loaded, and what's the latency?"

When ``QUARRY_LLM_MODE`` is not a sovereign mode the endpoint still
returns ``200`` with ``active=false`` — operators can confirm
"the pod is on cloud-BYOK, sovereign deployment is not engaged" from
the same panel.

Contract
--------

* **Read-only.** No knobs to flip, no secrets returned (the API key —
  if any — is reported as a sentinel ``"sovereign"`` or a bearer
  redaction, never the raw value).
* **Probes on every call.** The active model + latency only make sense
  if measured live. The probe has a 3 s timeout and never raises —
  failures degrade to ``healthcheck.ok=false`` with a populated
  ``reason``.
* **Safe under air-gap.** The probe targets ``127.0.0.1`` or the
  WireGuard private IP — there is no outbound traffic to public
  hosts. Importing this module is safe in a fully air-gapped pod.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/llm/sovereign", tags=["llm"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class SovereignHealthcheck(BaseModel):
    """Live probe result. Always populated; ``ok`` says whether to trust it."""

    ok: bool = Field(description="True when the endpoint replied 2xx with a parseable model list.")
    runtime: Literal["ollama", "vllm", "unknown"] = Field(
        description="Best-effort detection from the probe response shape."
    )
    active_model: str | None = Field(
        default=None,
        description="First model identifier the runtime reports loaded. Null when ok=false.",
    )
    latency_ms: int = Field(description="Probe round-trip time in milliseconds.")
    reason: str = Field(default="", description="Human-readable failure reason when ok=false.")
    checked_at: datetime = Field(description="UTC timestamp the probe completed.")


class SovereignLlmStatus(BaseModel):
    """Snapshot the admin panel renders."""

    mode: Literal["cloud-byok", "sovereign-vps", "sovereign-mac"] = Field(
        description="Effective value of QUARRY_LLM_MODE (defaults to cloud-byok)."
    )
    active: bool = Field(
        description="True when mode is sovereign-* (panel surface). False when cloud-BYOK."
    )
    endpoint: str | None = Field(
        default=None,
        description="The base URL the sovereign LLM should answer on. Null when active=false.",
    )
    model: str | None = Field(
        default=None,
        description="The model identifier configured for the sovereign deployment.",
    )
    api_key_set: bool = Field(
        default=False,
        description="True when SOVEREIGN_*_API_KEY is set to a non-default bearer token (vLLM auth proxy).",
    )
    healthcheck: SovereignHealthcheck | None = Field(
        default=None,
        description="Live probe result. Null when active=false (no endpoint to probe).",
    )


# ---------------------------------------------------------------------------
# Mode + config resolution (mirrors agents/app/security/llm_resolver.py)
# ---------------------------------------------------------------------------


_VALID_MODES = {"cloud-byok", "sovereign-vps", "sovereign-mac"}
_DEFAULT_VPS_BASE = "http://127.0.0.1:11434/v1"
_DEFAULT_VPS_MODEL = "qwen2.5:14b-instruct-q4_K_M"
_DEFAULT_MAC_BASE = "http://127.0.0.1:11434/v1"
_DEFAULT_MAC_MODEL = "qwen2.5:14b-instruct-q4_K_M"


def _current_mode() -> str:
    raw = (os.getenv("QUARRY_LLM_MODE") or "").strip().lower()
    if raw in _VALID_MODES:
        return raw
    return "cloud-byok"


def _sovereign_config(mode: str) -> tuple[str, str, bool]:
    """Return ``(endpoint, model, api_key_is_explicit)`` for the given mode."""
    if mode == "sovereign-vps":
        prefix, default_base, default_model = "SOVEREIGN_VPS", _DEFAULT_VPS_BASE, _DEFAULT_VPS_MODEL
    elif mode == "sovereign-mac":
        prefix, default_base, default_model = "SOVEREIGN_MAC", _DEFAULT_MAC_BASE, _DEFAULT_MAC_MODEL
    else:
        raise ValueError(f"not a sovereign mode: {mode!r}")
    base = (os.getenv(f"{prefix}_BASE_URL") or "").strip() or default_base
    model = (os.getenv(f"{prefix}_MODEL") or "").strip() or default_model
    api_key_set = bool((os.getenv(f"{prefix}_API_KEY") or "").strip())
    return base, model, api_key_set


# ---------------------------------------------------------------------------
# Probe shim
# ---------------------------------------------------------------------------
#
# The probe implementation lives in ``services/agents/app/security/
# sovereign_healthcheck.py`` so the agents service can reuse it on the
# explain path without an HTTP hop to ``services/api``. We import it
# lazily here to avoid making ``services/api`` import the agents
# package at boot, which would create a hard dependency that the
# slim deployments don't need.
#
# When the agents service isn't installed alongside (single-binary
# tests, or a deployment that only ships the API), the import falls
# back to a no-op probe so the endpoint still returns a usable shape.


def _probe_module():
    """Try to import the canonical sovereign healthcheck implementation."""
    # First, try the in-process path (deployments that ship both services).
    try:
        from app.security import sovereign_healthcheck  # noqa: PLC0415

        return sovereign_healthcheck
    except Exception:  # noqa: BLE001
        pass

    # Fallback: add the agents service to the path. This is the layout
    # used by docker-compose and pytest in the monorepo.
    repo_root = Path(__file__).resolve().parents[5]
    agents_root = repo_root / "services" / "agents"
    if agents_root.is_dir() and str(agents_root) not in sys.path:
        sys.path.insert(0, str(agents_root))
    try:
        from app.security import sovereign_healthcheck  # noqa: PLC0415

        return sovereign_healthcheck
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/status",
    response_model=SovereignLlmStatus,
    summary="Current sovereign LLM deployment status (CARD-015 Modalidade A/B)",
)
async def sovereign_llm_status() -> SovereignLlmStatus:
    """Return the live status of the Sovereign LLM deployment.

    * **mode** comes from ``QUARRY_LLM_MODE`` (cloud-byok by default).
    * When mode is sovereign-*, the endpoint + model are resolved from
      ``SOVEREIGN_VPS_*`` / ``SOVEREIGN_MAC_*`` env vars, with the same
      defaults the agents resolver uses.
    * A live probe runs against the endpoint (3 s timeout) and reports
      ok/runtime/active_model/latency. Probes never raise.
    """
    mode = _current_mode()
    if mode == "cloud-byok":
        return SovereignLlmStatus(mode="cloud-byok", active=False)

    endpoint, model, api_key_set = _sovereign_config(mode)

    probe_mod = _probe_module()
    if probe_mod is None:
        # Healthcheck unavailable; report config but mark probe absent.
        return SovereignLlmStatus(
            mode=mode,  # type: ignore[arg-type]
            active=True,
            endpoint=endpoint,
            model=model,
            api_key_set=api_key_set,
            healthcheck=SovereignHealthcheck(
                ok=False,
                runtime="unknown",
                active_model=None,
                latency_ms=0,
                reason="probe module not available in this deployment",
                checked_at=datetime.now(timezone.utc),
            ),
        )

    health = await probe_mod.probe(endpoint)
    return SovereignLlmStatus(
        mode=mode,  # type: ignore[arg-type]
        active=True,
        endpoint=endpoint,
        model=model,
        api_key_set=api_key_set,
        healthcheck=SovereignHealthcheck(
            ok=health.ok,
            runtime=health.runtime,  # type: ignore[arg-type]
            active_model=health.active_model,
            latency_ms=health.latency_ms,
            reason=health.reason,
            checked_at=datetime.now(timezone.utc),
        ),
    )
