"""Unit tests for CARD-015 sovereign LLM resolver + healthcheck.

Covers:

* ``QUARRY_LLM_MODE`` validation (valid / invalid / empty / unknown).
* ``sovereign-vps`` and ``sovereign-mac`` mode resolution with defaults
  and full env overrides.
* Sovereign mode bypasses the tenant DB lookup (no asyncpg pool created).
* Sovereign mode bypasses the air-gap policy (``QUARRY_AIRGAPPED=1`` does
  not gate the local endpoint).
* No API key configured still yields ``allowed=True`` (Ollama is open).
* Healthcheck probe correctly detects Ollama, vLLM, and failure paths.
"""
from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

_AGENTS_ROOT = Path(__file__).resolve().parents[1]
if str(_AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENTS_ROOT))


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    """Strip every env var the resolver/healthcheck consult."""
    for key in (
        "QUARRY_LLM_MODE",
        "QUARRY_AIRGAPPED",
        "SOVEREIGN_VPS_BASE_URL",
        "SOVEREIGN_VPS_MODEL",
        "SOVEREIGN_VPS_API_KEY",
        "SOVEREIGN_MAC_BASE_URL",
        "SOVEREIGN_MAC_MODEL",
        "SOVEREIGN_MAC_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
        "OPENAI_API_KEY",
        "LLM_BASE_URL",
        "LLM_MODEL",
        "LLM_API_KEY",
        "QUARRY_LLM_MODEL",
        "SOVEREIGN_HEALTHCHECK_TIMEOUT_S",
    ):
        monkeypatch.delenv(key, raising=False)


# ───────────────────────────────────────────────────────────────────────────
# Mode parsing
# ───────────────────────────────────────────────────────────────────────────


def test_current_llm_mode_defaults_to_cloud_when_unset():
    from app.security import llm_resolver

    assert llm_resolver._current_llm_mode() == "cloud-byok"


def test_current_llm_mode_accepts_sovereign_vps(monkeypatch):
    monkeypatch.setenv("QUARRY_LLM_MODE", "sovereign-vps")
    from app.security import llm_resolver

    assert llm_resolver._current_llm_mode() == "sovereign-vps"


def test_current_llm_mode_accepts_sovereign_mac(monkeypatch):
    monkeypatch.setenv("QUARRY_LLM_MODE", "sovereign-mac")
    from app.security import llm_resolver

    assert llm_resolver._current_llm_mode() == "sovereign-mac"


def test_current_llm_mode_normalises_case(monkeypatch):
    monkeypatch.setenv("QUARRY_LLM_MODE", "  Sovereign-VPS  ")
    from app.security import llm_resolver

    assert llm_resolver._current_llm_mode() == "sovereign-vps"


def test_current_llm_mode_unknown_falls_back_to_cloud(monkeypatch):
    monkeypatch.setenv("QUARRY_LLM_MODE", "magic-mode")
    from app.security import llm_resolver

    assert llm_resolver._current_llm_mode() == "cloud-byok"


# ───────────────────────────────────────────────────────────────────────────
# Sovereign resolution
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sovereign_vps_defaults(monkeypatch):
    monkeypatch.setenv("QUARRY_LLM_MODE", "sovereign-vps")
    from app.security import llm_resolver

    cfg = await llm_resolver.resolve_llm_config("any-tenant")

    assert cfg.allowed is True
    assert cfg.source == "sovereign-vps"
    assert cfg.base_url == "http://127.0.0.1:11434/v1"
    assert cfg.model == "qwen2.5:14b-instruct-q4_K_M"
    assert cfg.api_key == "sovereign"  # sentinel for keyless Ollama
    assert cfg.reason == ""


@pytest.mark.asyncio
async def test_sovereign_vps_full_override(monkeypatch):
    monkeypatch.setenv("QUARRY_LLM_MODE", "sovereign-vps")
    monkeypatch.setenv("SOVEREIGN_VPS_BASE_URL", "http://10.99.0.1:11434/v1")
    monkeypatch.setenv("SOVEREIGN_VPS_MODEL", "llama3.1:70b-instruct-q4_K_M")
    monkeypatch.setenv("SOVEREIGN_VPS_API_KEY", "bearer-token-xyz")
    from app.security import llm_resolver

    cfg = await llm_resolver.resolve_llm_config("any-tenant")

    assert cfg.allowed is True
    assert cfg.source == "sovereign-vps"
    assert cfg.base_url == "http://10.99.0.1:11434/v1"
    assert cfg.model == "llama3.1:70b-instruct-q4_K_M"
    assert cfg.api_key == "bearer-token-xyz"


@pytest.mark.asyncio
async def test_sovereign_mac_defaults(monkeypatch):
    monkeypatch.setenv("QUARRY_LLM_MODE", "sovereign-mac")
    from app.security import llm_resolver

    cfg = await llm_resolver.resolve_llm_config("any-tenant")

    assert cfg.allowed is True
    assert cfg.source == "sovereign-mac"
    assert cfg.base_url == "http://127.0.0.1:11434/v1"


@pytest.mark.asyncio
async def test_sovereign_bypasses_db_lookup(monkeypatch):
    """Sovereign mode must NOT attempt to import or use asyncpg."""
    monkeypatch.setenv("QUARRY_LLM_MODE", "sovereign-vps")
    from app.security import llm_resolver

    # Sabotage the lazy ledger import path; if sovereign mode tries to
    # use it the test fails loudly.
    def _explode(*_args, **_kwargs):
        raise AssertionError("sovereign mode must not consult the database")

    monkeypatch.setattr(llm_resolver, "_fetch_tenant_credential", _explode)

    cfg = await llm_resolver.resolve_llm_config("any-tenant")
    assert cfg.allowed is True
    assert cfg.source == "sovereign-vps"


@pytest.mark.asyncio
async def test_sovereign_bypasses_airgap(monkeypatch):
    """QUARRY_AIRGAPPED=1 must not block a sovereign deployment."""
    monkeypatch.setenv("QUARRY_LLM_MODE", "sovereign-vps")
    monkeypatch.setenv("QUARRY_AIRGAPPED", "1")
    from app.security import llm_resolver

    cfg = await llm_resolver.resolve_llm_config("any-tenant")
    assert cfg.allowed is True
    assert cfg.reason == ""


@pytest.mark.asyncio
async def test_sovereign_invalid_mode_falls_back_to_cloud(monkeypatch):
    """Typo in QUARRY_LLM_MODE must not silently engage sovereign mode."""
    monkeypatch.setenv("QUARRY_LLM_MODE", "sovereign-vp")  # typo
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from app.security import llm_resolver

    cfg = await llm_resolver.resolve_llm_config(None)
    # Falls back to cloud-byok env baseline.
    assert cfg.allowed is True
    assert cfg.source == "environment"


# ───────────────────────────────────────────────────────────────────────────
# Healthcheck probe
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_probe_detects_ollama(monkeypatch):
    from app.security import sovereign_healthcheck

    def _handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "qwen2.5:14b-instruct-q4_K_M", "size": 9000000000}
                    ]
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(_handler)
    _OrigClient = httpx.AsyncClient  # capture before patching to avoid recursion
    monkeypatch.setattr(
        sovereign_healthcheck.httpx,
        "AsyncClient",
        lambda **kw: _OrigClient(transport=transport, **kw),
    )

    h = await sovereign_healthcheck.probe("http://10.99.0.1:11434/v1")
    assert h.ok is True
    assert h.runtime == "ollama"
    assert h.active_model == "qwen2.5:14b-instruct-q4_K_M"
    assert h.reason == ""


@pytest.mark.asyncio
async def test_probe_detects_vllm(monkeypatch):
    from app.security import sovereign_healthcheck

    def _handler(request: httpx.Request) -> httpx.Response:
        # Ollama endpoint returns 404 — vLLM doesn't have /api/tags
        if request.url.path == "/api/tags":
            return httpx.Response(404)
        if request.url.path == "/v1/models":
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "data": [{"id": "meta-llama/Llama-3.3-70B-Instruct", "object": "model"}],
                },
            )
        return httpx.Response(500)

    transport = httpx.MockTransport(_handler)
    _OrigClient = httpx.AsyncClient  # capture before patching to avoid recursion
    monkeypatch.setattr(
        sovereign_healthcheck.httpx,
        "AsyncClient",
        lambda **kw: _OrigClient(transport=transport, **kw),
    )

    h = await sovereign_healthcheck.probe("http://127.0.0.1:8000/v1")
    assert h.ok is True
    assert h.runtime == "vllm"
    assert h.active_model == "meta-llama/Llama-3.3-70B-Instruct"


@pytest.mark.asyncio
async def test_probe_unreachable_endpoint(monkeypatch):
    from app.security import sovereign_healthcheck

    def _handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    transport = httpx.MockTransport(_handler)
    _OrigClient = httpx.AsyncClient  # capture before patching to avoid recursion
    monkeypatch.setattr(
        sovereign_healthcheck.httpx,
        "AsyncClient",
        lambda **kw: _OrigClient(transport=transport, **kw),
    )

    h = await sovereign_healthcheck.probe("http://10.99.0.1:11434/v1")
    assert h.ok is False
    assert h.active_model is None
    assert "probe failed" in h.reason


@pytest.mark.asyncio
async def test_probe_returns_2xx_but_empty_models(monkeypatch):
    from app.security import sovereign_healthcheck

    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": [], "data": []})

    transport = httpx.MockTransport(_handler)
    _OrigClient = httpx.AsyncClient  # capture before patching to avoid recursion
    monkeypatch.setattr(
        sovereign_healthcheck.httpx,
        "AsyncClient",
        lambda **kw: _OrigClient(transport=transport, **kw),
    )

    h = await sovereign_healthcheck.probe("http://10.99.0.1:11434/v1")
    assert h.ok is False
    assert "no recognisable" in h.reason


def test_strip_v1_handles_trailing_slash():
    from app.security import sovereign_healthcheck

    assert sovereign_healthcheck._strip_v1("http://x/v1") == "http://x"
    assert sovereign_healthcheck._strip_v1("http://x/v1/") == "http://x"
    assert sovereign_healthcheck._strip_v1("http://x") == "http://x"
    assert sovereign_healthcheck._strip_v1("http://x/") == "http://x"
