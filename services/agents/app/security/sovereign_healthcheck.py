"""Healthcheck for CARD-015 Sovereign LLM deployments (Modalidade A/B).

Why a separate module
---------------------

``llm_resolver.resolve_llm_config`` is on the explain hot path and is
called on *every* alert render. Probing the sovereign endpoint
synchronously inside the resolver would add 50–500 ms to each explain
request — unacceptable. Instead we expose an explicit ``probe()`` that
the admin panel (``/settings/sovereign-llm``) and operational tooling
call out-of-band.

The probe is OpenAI-compatible-API aware:

* **Ollama** — replies on ``GET /api/tags`` (lists pulled models). This
  endpoint is on the *root*, not under ``/v1``, so we strip the
  trailing ``/v1`` segment before probing.
* **vLLM**  — exposes the OpenAI server's ``GET /v1/models``.

Both probes return JSON; we summarise the first available model name
plus a latency measurement so the admin panel can show "active model:
qwen2.5:14b-instruct-q4_K_M, 80 ms".

This module makes *no* outbound calls to ``api.openai.com`` and is
safe to import in an air-gapped environment.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


_DEFAULT_TIMEOUT_S = float(os.getenv("SOVEREIGN_HEALTHCHECK_TIMEOUT_S", "3.0"))


@dataclass(frozen=True)
class SovereignHealth:
    """Outcome of probing a Sovereign LLM endpoint.

    Attributes:
        ok: ``True`` when the endpoint responded with a 2xx and we
            could parse at least one model name. ``False`` on any
            transport/parse failure.
        endpoint: The base URL we probed (always populated for logs).
        runtime: ``"ollama"`` | ``"vllm"`` | ``"unknown"`` — best-effort
            detection from the response shape.
        active_model: The first model name the runtime reports loaded.
            ``None`` when ``ok=False`` or the response was empty.
        latency_ms: Round-trip time of the probe HTTP request.
        reason: Short human-readable failure reason. Empty when
            ``ok=True``.
    """

    ok: bool
    endpoint: str
    runtime: str
    active_model: str | None
    latency_ms: int
    reason: str


def _strip_v1(base_url: str) -> str:
    """Return ``base_url`` with a trailing ``/v1`` removed (Ollama root)."""
    cleaned = (base_url or "").rstrip("/")
    if cleaned.endswith("/v1"):
        return cleaned[:-3]
    return cleaned


def _extract_active_model(payload: Any) -> tuple[str, str | None]:
    """Best-effort runtime + model detection from probe JSON.

    Returns ``(runtime, model_name_or_None)``.

    * Ollama ``/api/tags``  →  ``{"models": [{"name": "qwen…", ...}, ...]}``
    * vLLM ``/v1/models``   →  ``{"data": [{"id": "meta-llama/…", ...}, ...]}``
    """
    if not isinstance(payload, dict):
        return "unknown", None
    if isinstance(payload.get("models"), list) and payload["models"]:
        first = payload["models"][0]
        if isinstance(first, dict) and isinstance(first.get("name"), str):
            return "ollama", first["name"]
    if isinstance(payload.get("data"), list) and payload["data"]:
        first = payload["data"][0]
        if isinstance(first, dict) and isinstance(first.get("id"), str):
            return "vllm", first["id"]
    return "unknown", None


async def probe(base_url: str, *, timeout_s: float | None = None) -> SovereignHealth:
    """Probe a Sovereign LLM endpoint and return a structured health record.

    The probe tries Ollama (``/api/tags``) first, then vLLM
    (``/v1/models``). The first successful 2xx with a parseable model
    list wins. Both attempts share the same ``timeout_s`` budget.

    This function never raises. Failures degrade to ``ok=False`` with
    a populated ``reason`` so the admin panel can render a clear
    "endpoint down" state without surfacing a stack trace.
    """
    timeout = timeout_s if timeout_s is not None else _DEFAULT_TIMEOUT_S
    root = _strip_v1(base_url)
    started = time.perf_counter()

    async with httpx.AsyncClient(timeout=timeout) as client:
        # Try Ollama first.
        try:
            resp = await client.get(f"{root}/api/tags")
            if 200 <= resp.status_code < 300:
                runtime, model = _extract_active_model(resp.json())
                if model is not None:
                    return SovereignHealth(
                        ok=True,
                        endpoint=base_url,
                        runtime=runtime,
                        active_model=model,
                        latency_ms=int((time.perf_counter() - started) * 1000),
                        reason="",
                    )
        except (httpx.RequestError, ValueError):
            # network error or non-JSON body — fall through to vLLM probe
            pass

        # Try vLLM (OpenAI-compatible).
        try:
            resp = await client.get(f"{root}/v1/models")
            if 200 <= resp.status_code < 300:
                runtime, model = _extract_active_model(resp.json())
                if model is not None:
                    return SovereignHealth(
                        ok=True,
                        endpoint=base_url,
                        runtime=runtime,
                        active_model=model,
                        latency_ms=int((time.perf_counter() - started) * 1000),
                        reason="",
                    )
        except (httpx.RequestError, ValueError) as exc:
            logger.warning(
                "sovereign.probe_failed",
                endpoint=base_url,
                error=str(exc),
            )
            return SovereignHealth(
                ok=False,
                endpoint=base_url,
                runtime="unknown",
                active_model=None,
                latency_ms=int((time.perf_counter() - started) * 1000),
                reason=f"probe failed: {exc!s}",
            )

    return SovereignHealth(
        ok=False,
        endpoint=base_url,
        runtime="unknown",
        active_model=None,
        latency_ms=int((time.perf_counter() - started) * 1000),
        reason="endpoint returned no recognisable Ollama or vLLM response",
    )
