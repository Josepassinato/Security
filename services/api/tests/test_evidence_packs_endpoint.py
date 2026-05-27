"""HTTP-layer tests for the evidence-pack endpoint module.

Mounts the router in a minimal FastAPI app so we don't drag the whole
service init (DB, auth, MCP server, etc) into the test boot. That
keeps these tests fast and isolated to the API surface we own.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.api.v1.deps import CurrentUser, get_current_user  # noqa: E402
from app.api.v1.endpoints import evidence_packs  # noqa: E402


def _stub_admin_user() -> CurrentUser:
    """Bypass auth in tests via FastAPI dependency override.

    The ``test`` environment deliberately does NOT trigger the dev-auth
    shim (see ``AUTH_BYPASS_ENVIRONMENTS``), so the auth dependency must
    be overridden explicitly. We use a deterministic admin so role-based
    permission checks (settings:read / settings:write) pass.
    """
    return CurrentUser(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        role="admin",
        email="test-admin@quarry.dev",
    )


@pytest.fixture
def client() -> TestClient:
    # Fresh app per test prevents catalog cache bleed between tests
    # (the cache is module-level on evidence_packs._load_catalog).
    evidence_packs._load_catalog.cache_clear()
    app = FastAPI()
    app.include_router(evidence_packs.router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = _stub_admin_user
    return TestClient(app)


# ── list ───────────────────────────────────────────────────────────────────


def test_list_returns_the_bundled_bcb_85_pack(client: TestClient):
    resp = client.get("/api/v1/evidence-packs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    pack_ids = [p["pack_id"] for p in body["packs"]]
    assert "bcb-85-2021-art-6" in pack_ids


def test_list_sorts_by_regulation_then_article(client: TestClient):
    resp = client.get("/api/v1/evidence-packs")
    body = resp.json()
    sorted_summaries = sorted(
        body["packs"],
        key=lambda p: (p["regulation_code"], p["article"], p["pack_id"]),
    )
    assert body["packs"] == sorted_summaries


# ── get one ────────────────────────────────────────────────────────────────


def test_get_pack_returns_metadata(client: TestClient):
    resp = client.get("/api/v1/evidence-packs/bcb-85-2021-art-6")
    assert resp.status_code == 200
    body = resp.json()
    assert body["regulation_code"] == "BCB-85-2021"
    assert body["article"] == "Art. 6º"
    assert body["reporting_period"] == "90d"
    assert body["output_format"] == "BCB_RFI_v1"


def test_get_pack_404_for_unknown(client: TestClient):
    resp = client.get("/api/v1/evidence-packs/this-does-not-exist")
    assert resp.status_code == 404
    assert "unknown pack_id" in resp.json()["detail"]


# ── compile ────────────────────────────────────────────────────────────────


def test_compile_returns_sealed_bundle(client: TestClient):
    resp = client.post("/api/v1/evidence-packs/bcb-85-2021-art-6/compile")
    assert resp.status_code == 200
    body = resp.json()

    # Bundle identity
    assert body["pack_id"] == "bcb-85-2021-art-6"

    # All 5 step labels from the bundled pack
    step_labels = set(body["data"].keys())
    assert "Plano de resposta a incidentes vigente" in step_labels
    assert "Trilha de auditoria — decisões dos agentes" in step_labels

    # Sealing surface present and well-formed
    assert len(body["data_digest_hex"]) == 64
    assert body["timestamp"]["tsa_name"].startswith("MockTSA")
    assert body["timestamp"]["digest_hex"] == body["data_digest_hex"]
    assert body["signature"]["digest_hex"] == body["data_digest_hex"]
    assert body["signature"]["digest_algorithm"] == "SHA-256"
    assert len(body["hash_chain_entry_hash_hex"]) == 64

    # The production-verification gate must surface clearly
    assert body["mock_seal"] is True


def test_compile_404_for_unknown_pack(client: TestClient):
    resp = client.post("/api/v1/evidence-packs/nope/compile")
    assert resp.status_code == 404


# ── preview HTML ───────────────────────────────────────────────────────────


def test_preview_html_returns_self_contained_document(client: TestClient):
    resp = client.get("/api/v1/evidence-packs/bcb-85-2021-art-6/preview.html")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    body = resp.text
    assert body.startswith("<!DOCTYPE html>")
    assert "BCB-85-2021" in body
    # Mock-seal banner ships in this build
    assert "mock" in body.lower()


def test_preview_html_404_for_unknown_pack(client: TestClient):
    resp = client.get("/api/v1/evidence-packs/missing/preview.html")
    assert resp.status_code == 404


# ── auth gate (P0 regression guard) ────────────────────────────────────────


def test_endpoints_require_auth_when_no_override(monkeypatch):
    """All 5 endpoints must reject unauthenticated callers.

    Regression guard for the pre-patch state where every handler was
    anonymous. We override ``get_current_user`` with a stub that raises
    401 (mirroring its real "no credentials, no dev-auth" path) so the
    test doesn't need a real DB session for ``Depends(get_db)``.

    A 200 from any handler under this fixture means the auth dependency
    was silently dropped — the very regression we are guarding against.
    """
    from fastapi import HTTPException

    monkeypatch.setenv("ENV", "test")

    async def _no_creds() -> CurrentUser:
        raise HTTPException(status_code=401, detail="Not authenticated")

    evidence_packs._load_catalog.cache_clear()
    app = FastAPI()
    app.include_router(evidence_packs.router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = _no_creds
    bare = TestClient(app)

    for method, path in [
        ("GET", "/api/v1/evidence-packs"),
        ("GET", "/api/v1/evidence-packs/bcb-85-2021-art-6"),
        ("POST", "/api/v1/evidence-packs/bcb-85-2021-art-6/compile"),
        ("GET", "/api/v1/evidence-packs/bcb-85-2021-art-6/preview.html"),
        ("GET", "/api/v1/evidence-packs/bcb-85-2021-art-6/download.pdf"),
    ]:
        resp = bare.request(method, path)
        assert resp.status_code == 401, f"{method} {path} should require auth"


# ── PII redaction safety gate (P0 regression guard) ────────────────────────


def test_compile_refuses_when_pii_redaction_requested():
    """Packs requesting redacted PII must fail-loud until the redactor lands.

    The MockRuntime cannot honor ``include_redacted_pii: true`` — shipping
    raw rows under a "redacted" contract would leak CPFs to the ANPD
    notification. The compiler must refuse with EvidencePackError, surfaced
    by the endpoint as HTTP 422.
    """
    from app.evidence_pack.compiler import EvidenceCompiler, MockRuntime
    from app.evidence_pack.parser import EvidencePackError
    from app.evidence_pack.signer import MockSigner
    from app.evidence_pack.tsa import MockTsaClient

    evidence_packs._load_catalog.cache_clear()
    catalog = evidence_packs._load_catalog()
    pack = catalog.get("lgpd-art-48-anpd-48h") or catalog.get(
        "bacen-comunicado-44323-2024-24h"
    )
    if pack is None:  # pragma: no cover
        pytest.skip("no PII-redacting pack bundled in this build")

    compiler = EvidenceCompiler(
        runtime=MockRuntime(), tsa=MockTsaClient(), signer=MockSigner()
    )
    with pytest.raises(EvidencePackError, match="include_redacted_pii"):
        compiler.compile(pack)
