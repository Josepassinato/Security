"""HTTP-layer tests for the evidence-pack endpoint module.

Mounts the router in a minimal FastAPI app so we don't drag the whole
service init (DB, auth, MCP server, etc) into the test boot. That
keeps these tests fast and isolated to the API surface we own.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.api.v1.endpoints import evidence_packs  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    # Fresh app per test prevents catalog cache bleed between tests
    # (the cache is module-level on evidence_packs._load_catalog).
    evidence_packs._load_catalog.cache_clear()
    app = FastAPI()
    app.include_router(evidence_packs.router, prefix="/api/v1")
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
