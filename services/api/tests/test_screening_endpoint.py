"""HTTP-layer tests for the screening endpoint module.

Mounts the router in a minimal FastAPI app (no DB/auth/MCP boot), overrides auth
and the tenant DB session, and monkeypatches the small DB helpers — so the HTTP
surface (routing, auth, schemas, render wiring) is tested in isolation. The
underlying screen/render/verify logic is covered by the unit + live tests.
"""

from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.api.v1.deps import CurrentUser, get_current_user  # noqa: E402
from app.api.v1.endpoints import screening  # noqa: E402
from app.db.rls import get_tenant_db  # noqa: E402

_TENANT = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _admin() -> CurrentUser:
    return CurrentUser(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        tenant_id=_TENANT,
        role="admin",
        email="test-admin@quarry.dev",
    )


class _DummyDB:
    """Stand-in for the tenant session; helpers are monkeypatched, so only the
    write path's ``await db.commit()`` actually touches it."""

    async def commit(self) -> None:
        return None


async def _stub_db():
    yield _DummyDB()


def _decision(**kw) -> SimpleNamespace:
    base = {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "counterparty_name": "Vladimir Putin",
        "counterparty_normalized": "vladimir putin",
        "decision": "POTENTIAL_MATCH",
        "disposition": "PENDING",
        "match_score": 100,
        "scoring_rule_version": "opensanctions-v1",
        "engine_raw_result": {"hits": []},
        "matching_engine": "opensanctions",
        "list_of_record": "opensanctions",
        "list_source": "OFAC_SDN",
        "list_dataset": "us_ofac_sdn",
        "list_version": "20260626181135-nfz",
        "list_release_date": datetime(2026, 6, 26, 18, 11, 35, tzinfo=UTC),
        "screened_at": datetime(2026, 6, 26, 14, 0, 0, tzinfo=UTC),
        "entry_hash": "b" * 64,
        "prev_hash": None,
        "counterparty_id": "P-1",
        "counterparty_id_type": "PASSPORT",
        "counterparty_jurisdiction": "RU",
        "screening_trigger": "onboarding",
        "case_id": None,
    }
    base.update(kw)
    return SimpleNamespace(**base)


@pytest.fixture
def app_client() -> TestClient:
    app = FastAPI()
    app.include_router(screening.router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = _admin
    app.dependency_overrides[get_tenant_db] = _stub_db
    return TestClient(app)


def test_routes_registered() -> None:
    paths = {r.path for r in screening.router.routes}
    assert "/screening" in paths
    assert "/screening/portfolio" in paths
    assert "/screening/verify-chain" in paths
    assert "/screening/{decision_id}" in paths
    assert "/screening/{decision_id}/dossier.html" in paths


def test_auth_required_without_override() -> None:
    app = FastAPI()
    app.include_router(screening.router, prefix="/api/v1")
    client = TestClient(app)
    r = client.get("/api/v1/screening/verify-chain")
    assert r.status_code in (401, 403)


def test_create_screening(app_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(screening, "_client", lambda: object())

    async def _fake_screen(db, client, **kw):
        assert kw["tenant_id"] == _TENANT
        assert kw["counterparty_name"] == "Vladimir Putin"
        return _decision()

    monkeypatch.setattr(screening, "screen_and_record", _fake_screen)
    r = app_client.post("/api/v1/screening", json={"counterparty_name": "Vladimir Putin"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["decision"] == "POTENTIAL_MATCH"
    assert body["list_version"] == "20260626181135-nfz"
    assert body["matching_engine"] == "opensanctions"


def test_intake_503_without_api_key(app_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENSANCTIONS_API_KEY", raising=False)
    r = app_client.post("/api/v1/screening", json={"counterparty_name": "X"})
    assert r.status_code == 503


def test_get_decision(app_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_fetch(db, decision_id, tenant_id):
        return _decision(id=decision_id)

    monkeypatch.setattr(screening, "_fetch_decision", _fake_fetch)
    did = "11111111-1111-1111-1111-111111111111"
    r = app_client.get(f"/api/v1/screening/{did}")
    assert r.status_code == 200
    assert r.json()["id"] == did


def test_dossier_html_has_carimbo(app_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_fetch(db, decision_id, tenant_id):
        return _decision(id=decision_id)

    monkeypatch.setattr(screening, "_fetch_decision", _fake_fetch)
    r = app_client.get("/api/v1/screening/11111111-1111-1111-1111-111111111111/dossier.html")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "20260626181135-nfz" in r.text  # §2 version carimbo
    assert "b" * 64 in r.text  # §6 entry_hash


def test_portfolio_json(app_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_report(db, tenant_id):
        return {"counterparty_count": 3, "freshness": {"pct_current": 66.7}}

    monkeypatch.setattr(screening, "fetch_portfolio_report", _fake_report)
    r = app_client.get("/api/v1/screening/portfolio")
    assert r.status_code == 200
    assert r.json()["counterparty_count"] == 3  # not shadowed by /{decision_id}


def test_verify_chain_empty(app_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_rows(db, tenant_id):
        return []

    monkeypatch.setattr(screening, "_load_tenant_rows", _fake_rows)
    r = app_client.get("/api/v1/screening/verify-chain")
    assert r.status_code == 200
    assert r.json() == {"intact": True, "decisions": 0, "first_broken_index": None, "reason": None}


def _row(cid: str, decision: str, disposition: str) -> dict:
    return {
        "id": uuid.uuid4(),
        "counterparty_id": cid,
        "counterparty_id_type": "CPF",
        "counterparty_name": cid,
        "counterparty_normalized": cid.lower(),
        "counterparty_jurisdiction": None,
        "decision": decision,
        "disposition": disposition,
        "match_score": 90,
        "matching_engine": "opensanctions",
        "list_of_record": "opensanctions",
        "list_source": "OFAC_SDN",
        "list_dataset": "us_ofac_sdn",
        "list_version": "v2",
        "list_release_date": datetime(2026, 6, 26, tzinfo=UTC),
        "human_reviewer": None,
        "rationale": "",
        "screened_at": datetime(2026, 6, 26, tzinfo=UTC),
        "created_at": datetime(2026, 6, 26, tzinfo=UTC),
        "entry_hash": "x" * 64,
    }


def test_list_pending_review(app_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        _row("A", "POTENTIAL_MATCH", "PENDING"),  # in queue
        _row("B", "NO_MATCH", "PENDING"),  # not a potential match
        _row("C", "POTENTIAL_MATCH", "CLEARED_FALSE_POSITIVE"),  # already resolved
    ]

    async def _fake_rows(db, tenant_id):
        return rows

    monkeypatch.setattr(screening, "_load_tenant_rows", _fake_rows)
    r = app_client.get("/api/v1/screening?status=pending_review")
    assert r.status_code == 200
    assert [d["counterparty_name"] for d in r.json()] == ["A"]


def test_review_appends_disposition(app_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_fetch(db, decision_id, tenant_id):
        return _decision(id=decision_id, decision="POTENTIAL_MATCH", disposition="PENDING")

    captured: dict = {}

    async def _fake_record(db, **kw):
        captured.update(kw)
        return _decision(decision=kw["decision"], disposition=kw["disposition"])

    monkeypatch.setattr(screening, "_fetch_decision", _fake_fetch)
    monkeypatch.setattr(screening, "record_screening_decision", _fake_record)
    r = app_client.post(
        "/api/v1/screening/11111111-1111-1111-1111-111111111111/review",
        json={"disposition": "CLEARED_FALSE_POSITIVE", "rationale": "weak alias, distinct DOB"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["disposition"] == "CLEARED_FALSE_POSITIVE"
    # append-only review: trigger='review', reviewer = the authed user, rationale carried through
    assert captured["screening_trigger"] == "review"
    assert captured["human_reviewer"] == "test-admin@quarry.dev"
    assert captured["rationale"] == "weak alias, distinct DOB"


def test_review_requires_rationale(app_client: TestClient) -> None:
    r = app_client.post(
        "/api/v1/screening/11111111-1111-1111-1111-111111111111/review",
        json={"disposition": "BLOCKED"},  # missing rationale → 422
    )
    assert r.status_code == 422
