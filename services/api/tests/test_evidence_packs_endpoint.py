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


# ── P1.4 mock-seal hardening ───────────────────────────────────────────────


def test_compile_response_carries_seal_status_field(client: TestClient):
    """BundleResponse must expose seal_status='mock' for mock bundles.

    Per Parecer Jurídico Nº 012/2026 § II.5, contracts will reference
    `seal_status` directly — the bool `mock_seal` flag is too easy to
    forget to check. Both must coexist (backwards-compat).
    """
    resp = client.post("/api/v1/evidence-packs/bcb-85-2021-art-6/compile")
    assert resp.status_code == 200
    body = resp.json()
    assert body["mock_seal"] is True
    assert body["seal_status"] == "mock"


def test_preview_html_carries_persistent_watermark_on_mock(client: TestClient):
    """Mock-sealed HTML must include the every-page watermark.

    The warning banner alone is not enough — a reader who scrolls past
    it could mistake the document for real. The watermark element with
    `position: fixed` repeats on every PDF page.
    """
    resp = client.get("/api/v1/evidence-packs/bcb-85-2021-art-6/preview.html")
    body = resp.text
    assert 'class="watermark"' in body
    assert "DOCUMENTO NÃO ASSINADO" in body
    assert "AMBIENTE DE HOMOLOGAÇÃO" in body
    # CSS rule that makes it repeat on every page
    assert "position: fixed" in body


def test_compile_response_carries_event_id_and_cert_serial(client: TestClient):
    """P1.3 — Bundle must carry deterministic event_id + cert_serial.

    Per Parecer Jurídico Nº 012/2026 § III, every artifact carries an
    "identificador único imutável do evento" and a serial of the
    signing certificate.
    """
    import uuid

    resp = client.post("/api/v1/evidence-packs/bcb-85-2021-art-6/compile")
    body = resp.json()
    # event_id is a valid UUID string
    uuid.UUID(body["event_id"])
    # cert_serial is "—" for mock signer (no serial in DN)
    assert body["cert_serial"] == "—"


def test_download_pdf_refuses_mock_in_production(monkeypatch, client: TestClient):
    """In production env, download.pdf must 403 if the seal is mock.

    Last-line defense against an operator forwarding a homologation PDF
    to a regulator. Test, dev, demo envs continue to work.
    """
    monkeypatch.setenv("ENV", "production")
    resp = client.get("/api/v1/evidence-packs/bcb-85-2021-art-6/download.pdf")
    assert resp.status_code == 403
    assert "mock" in resp.json()["detail"].lower()


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


# ── PII pseudonimization (P1.5/P1.6) ──────────────────────────────────────


def test_compile_pseudonimizes_pii_for_regulatory_submission():
    """Packs requesting redacted PII receive HMAC-pseudonimized rows.

    The default export level (REGULATORY_SUBMISSION) replaces CPF,
    email, phone, etc. with deterministic ``{kind}_{hex16}`` tokens.
    The DPO can de-pseudonimize via the salt held in their vault.
    """
    from app.evidence_pack.compiler import EvidenceCompiler, MockRuntime
    from app.evidence_pack.pii import ExportLevel
    from app.evidence_pack.signer import MockSigner
    from app.evidence_pack.tsa import MockTsaClient

    evidence_packs._load_catalog.cache_clear()
    catalog = evidence_packs._load_catalog()
    pack = catalog.get("lgpd-art-48-anpd-res-15-2024") or catalog.get(
        "bacen-comunicado-44323-2024-24h"
    )
    if pack is None:  # pragma: no cover
        pytest.skip("no PII-redacting pack bundled in this build")

    runtime = MockRuntime(
        ledger_rows=[
            {"cpf": "12345678900", "email": "alice@example.com", "action": "login"},
            {"cpf": "98765432100", "email": "bob@example.com", "action": "export"},
        ]
    )
    compiler = EvidenceCompiler(
        runtime=runtime,
        tsa=MockTsaClient(),
        signer=MockSigner(),
        export_level=ExportLevel.REGULATORY_SUBMISSION,
    )
    bundle = compiler.compile(pack)
    assert bundle.export_level == ExportLevel.REGULATORY_SUBMISSION

    # Find the ledger_export step's output in bundle.data and verify
    # PII was pseudonimized (raw CPFs must NOT appear anywhere).
    flat = repr(bundle.data)
    assert "12345678900" not in flat
    assert "alice@example.com" not in flat
    assert "cpf_" in flat  # pseudonimized prefix appears
    assert "email_" in flat


def test_compile_strips_pii_for_executive_summary():
    """EXECUTIVE_SUMMARY level removes PII values entirely."""
    from app.evidence_pack.compiler import EvidenceCompiler, MockRuntime
    from app.evidence_pack.pii import ExportLevel
    from app.evidence_pack.signer import MockSigner
    from app.evidence_pack.tsa import MockTsaClient

    evidence_packs._load_catalog.cache_clear()
    catalog = evidence_packs._load_catalog()
    pack = catalog.get("lgpd-art-48-anpd-res-15-2024")
    if pack is None:  # pragma: no cover
        pytest.skip("no PII-redacting pack bundled")

    runtime = MockRuntime(
        ledger_rows=[{"cpf": "12345678900", "email": "x@y.com", "action": "login"}],
    )
    compiler = EvidenceCompiler(
        runtime=runtime,
        tsa=MockTsaClient(),
        signer=MockSigner(),
        export_level=ExportLevel.EXECUTIVE_SUMMARY,
    )
    bundle = compiler.compile(pack)
    flat = repr(bundle.data)
    assert "12345678900" not in flat
    assert "x@y.com" not in flat
    # The summary keeps the field with the redaction marker so callers
    # can still count rows by category.
    assert "[redacted]" in flat


def test_compile_endpoint_accepts_level_query_param(client: TestClient):
    """POST /compile?level=... must apply the requested PII tier."""
    resp = client.post(
        "/api/v1/evidence-packs/bcb-85-2021-art-6/compile"
        "?level=executive_summary"
    )
    assert resp.status_code == 200
    assert resp.json()["export_level"] == "executive_summary"

    # Default (no param) → regulatory_submission
    resp = client.post("/api/v1/evidence-packs/bcb-85-2021-art-6/compile")
    assert resp.json()["export_level"] == "regulatory_submission"


def test_compile_endpoint_rejects_unknown_level(client: TestClient):
    """Unknown export levels return 400 — fail-loud."""
    resp = client.post(
        "/api/v1/evidence-packs/bcb-85-2021-art-6/compile?level=garbage"
    )
    assert resp.status_code == 400
    assert "garbage" in resp.json()["detail"]


def test_pseudonimize_is_deterministic():
    """Same value + same salt = same pseudonym across calls."""
    from app.evidence_pack.pii import pseudonimize

    salt = b"0123456789abcdef" * 2
    a = pseudonimize("12345678900", salt=salt, kind="cpf")
    b = pseudonimize("12345678900", salt=salt, kind="cpf")
    c = pseudonimize("00000000000", salt=salt, kind="cpf")
    assert a == b
    assert a != c
    assert a.startswith("cpf_") and len(a) == len("cpf_") + 16
