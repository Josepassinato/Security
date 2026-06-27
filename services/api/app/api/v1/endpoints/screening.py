"""Sanctions screening evidence layer — HTTP API.

Turns the screening libraries into a product surface. Endpoints:

* ``POST /api/v1/screening``                    intake: screen a counterparty → ledger
* ``GET  /api/v1/screening/portfolio``          portfolio report (JSON or ?format=html)
* ``GET  /api/v1/screening/verify-chain``       chain integrity for the tenant (F6)
* ``GET  /api/v1/screening/{id}``               one decision (tenant-scoped)
* ``GET  /api/v1/screening/{id}/dossier.html``  per-case dossier (HTML)

RBAC: reads = ``cases:read``; intake writes a sealed ledger record = ``cases:write``.
Tenant isolation is enforced two ways: the RLS-scoped ``TenantDBSession`` AND an
explicit ``tenant_id`` filter on every query (belt + suspenders for an evidence
ledger). The OpenSanctions API key comes from ``OPENSANCTIONS_API_KEY``; intake
returns 503 if it is unset rather than screening blind.

DB reads are delegated to small module-level helpers so the HTTP surface is
unit-testable without a database (override auth + monkeypatch the helpers).
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.api.v1.deps import AuthUser, require_permission
from app.db.rls import TenantDBSession
from app.evidence_pack import narrative as _ep_narrative
from app.evidence_pack.narrative import render_narrative, render_screening_case_dossier
from app.evidence_pack.portfolio import fetch_portfolio_report, latest_by_counterparty
from app.models.screening_decision import ScreeningDecision
from app.screening.intake import screen_and_record
from app.screening.opensanctions_client import OpenSanctionsClient
from app.services.screening_hash import verify_chain
from app.services.screening_ledger import record_screening_decision

router = APIRouter(prefix="/screening", tags=["screening"])

ReadAuth = Annotated[AuthUser, Depends(require_permission("cases:read"))]
WriteAuth = Annotated[AuthUser, Depends(require_permission("cases:write"))]

# Resolve relative to the narrative module so the path is correct in BOTH the
# repo layout and the container image (/app/app/evidence_pack/dossier_templates),
# and never raises at import time (parents[6] overran in the container).
_TEMPLATES = Path(_ep_narrative.__file__).resolve().parent / "dossier_templates"
_CASE_TEMPLATE = _TEMPLATES / "aml-screening-case-dossier-v1.html.j2"
_PORTFOLIO_TEMPLATE = _TEMPLATES / "aml-portfolio-report-v1.html.j2"

_VERIFY_METHOD = "GET /api/v1/screening/verify-chain"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ScreeningRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    counterparty_name: str = Field(min_length=1)
    counterparty_normalized: str | None = Field(default=None, description="Defaults to a lowercased trim of counterparty_name.")
    counterparty_id: str | None = None
    counterparty_id_type: str = "OTHER"
    counterparty_jurisdiction: str | None = None
    screening_trigger: str | None = Field(default=None, description="e.g. 'onboarding', 'transaction:<ref>'.")
    case_id: uuid.UUID | None = None
    list_dataset: str = "us_ofac_sdn"
    threshold: int = Field(default=85, ge=0, le=100, description="Per-tenant calibrated review threshold.")


class DecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    counterparty_name: str
    decision: str
    disposition: str
    match_score: int
    matching_engine: str
    list_of_record: str
    list_dataset: str
    list_version: str
    list_release_date: datetime
    screened_at: datetime
    entry_hash: str | None


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    disposition: str = Field(pattern="^(CLEARED_FALSE_POSITIVE|BLOCKED|REPORTED)$")
    rationale: str = Field(min_length=3, description="Written justification for the human disposition (required).")
    decision: str | None = Field(default=None, pattern="^(POTENTIAL_MATCH|TRUE_MATCH|ESCALATED)$")


_LIST_FIELDS = (
    "id",
    "counterparty_name",
    "counterparty_id",
    "counterparty_id_type",
    "counterparty_jurisdiction",
    "decision",
    "disposition",
    "match_score",
    "matching_engine",
    "list_of_record",
    "list_source",
    "list_dataset",
    "list_version",
    "list_release_date",
    "human_reviewer",
    "rationale",
    "screened_at",
    "created_at",
    "entry_hash",
)


# ---------------------------------------------------------------------------
# Helpers (monkeypatchable; keep the DB surface small + testable)
# ---------------------------------------------------------------------------


def _client() -> OpenSanctionsClient:
    key = os.getenv("OPENSANCTIONS_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="OPENSANCTIONS_API_KEY not configured")
    return OpenSanctionsClient(key)


async def _fetch_decision(db: Any, decision_id: uuid.UUID, tenant_id: uuid.UUID) -> ScreeningDecision:
    stmt = select(ScreeningDecision).where(ScreeningDecision.id == decision_id, ScreeningDecision.tenant_id == tenant_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="screening decision not found")
    return row


async def _load_tenant_rows(db: Any, tenant_id: uuid.UUID) -> list[dict[str, Any]]:
    stmt = (
        select(ScreeningDecision)
        .where(ScreeningDecision.tenant_id == tenant_id)
        .order_by(ScreeningDecision.created_at.asc(), ScreeningDecision.id.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [{c.name: getattr(r, c.name) for c in ScreeningDecision.__table__.columns} for r in rows]


# ---------------------------------------------------------------------------
# Routes — static paths declared BEFORE /{decision_id} so they aren't captured.
# ---------------------------------------------------------------------------


@router.get("")
async def list_decisions(
    user: ReadAuth,
    db: TenantDBSession,
    status: Annotated[str, Query(pattern="^(pending_review|all)$")] = "pending_review",
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[dict[str, Any]]:
    """Review queue. 'pending_review' (default) = the latest decision per
    counterparty that is a POTENTIAL_MATCH still PENDING. 'all' = every decision,
    newest first."""
    rows = await _load_tenant_rows(db, user.tenant_id)
    if status == "pending_review":
        items = [
            r for r in latest_by_counterparty(rows).values() if r.get("decision") == "POTENTIAL_MATCH" and r.get("disposition") == "PENDING"
        ]
    else:
        items = list(rows)
    items.sort(key=lambda r: str(r.get("screened_at") or ""), reverse=True)
    return [{k: r.get(k) for k in _LIST_FIELDS} for r in items[:limit]]


@router.post("", response_model=DecisionOut, status_code=201)
async def create_screening(body: ScreeningRequest, user: WriteAuth, db: TenantDBSession) -> ScreeningDecision:
    normalized = body.counterparty_normalized or body.counterparty_name.strip().lower()
    decision = await screen_and_record(
        db,
        _client(),
        tenant_id=user.tenant_id,
        counterparty_name=body.counterparty_name,
        counterparty_normalized=normalized,
        counterparty_id_type=body.counterparty_id_type,
        counterparty_id=body.counterparty_id,
        counterparty_jurisdiction=body.counterparty_jurisdiction,
        screening_trigger=body.screening_trigger,
        case_id=body.case_id,
        list_dataset=body.list_dataset,
        threshold=body.threshold,
    )
    await db.commit()
    return decision


@router.get("/portfolio")
async def portfolio_report(
    user: ReadAuth,
    db: TenantDBSession,
    format: Annotated[str, Query(pattern="^(json|html)$")] = "json",
) -> Any:
    report = await fetch_portfolio_report(db, user.tenant_id)
    if format == "html":
        html = render_narrative(
            _PORTFOLIO_TEMPLATE.read_text(encoding="utf-8"),
            {
                "report": report,
                "tenant_name": str(user.tenant_id),
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )
        return HTMLResponse(html)
    return report


@router.get("/verify-chain")
async def verify_chain_endpoint(user: ReadAuth, db: TenantDBSession) -> dict[str, Any]:
    rows = await _load_tenant_rows(db, user.tenant_id)
    ok, idx, reason = verify_chain(rows)
    return {"intact": ok, "decisions": len(rows), "first_broken_index": idx, "reason": reason}


@router.get("/{decision_id}", response_model=DecisionOut)
async def get_decision(decision_id: uuid.UUID, user: ReadAuth, db: TenantDBSession) -> ScreeningDecision:
    return await _fetch_decision(db, decision_id, user.tenant_id)


@router.get("/{decision_id}/dossier.html", response_class=HTMLResponse)
async def get_dossier(decision_id: uuid.UUID, user: ReadAuth, db: TenantDBSession) -> HTMLResponse:
    row = await _fetch_decision(db, decision_id, user.tenant_id)
    html = render_screening_case_dossier(
        decision=row,
        template_str=_CASE_TEMPLATE.read_text(encoding="utf-8"),
        tenant_name=str(user.tenant_id),
        verification_method=_VERIFY_METHOD,
    )
    return HTMLResponse(html)


@router.post("/{decision_id}/review", response_model=DecisionOut, status_code=201)
async def review_decision(decision_id: uuid.UUID, body: ReviewRequest, user: WriteAuth, db: TenantDBSession) -> ScreeningDecision:
    """Human disposition of a screening decision. Append-only: records a NEW
    chained decision (same counterparty + frozen engine/list attribution) carrying
    the reviewer's disposition + rationale — never an UPDATE. HITL is enforced by
    the writer + the DB CHECK (reviewer + rationale required to resolve)."""
    orig = await _fetch_decision(db, decision_id, user.tenant_id)
    new = await record_screening_decision(
        db,
        tenant_id=user.tenant_id,
        counterparty_name=orig.counterparty_name,
        counterparty_normalized=orig.counterparty_normalized,
        counterparty_id=orig.counterparty_id,
        counterparty_id_type=orig.counterparty_id_type,
        counterparty_jurisdiction=orig.counterparty_jurisdiction,
        screening_trigger="review",
        case_id=orig.case_id,
        matching_engine=orig.matching_engine,
        list_of_record=orig.list_of_record,
        list_source=orig.list_source,
        list_dataset=orig.list_dataset,
        list_version=orig.list_version,
        list_release_date=orig.list_release_date,
        engine_raw_result=orig.engine_raw_result,
        match_score=orig.match_score,
        scoring_rule_version=orig.scoring_rule_version,
        decision=body.decision or orig.decision,
        disposition=body.disposition,
        human_reviewer=user.email or str(user.user_id),
        rationale=body.rationale,
        screened_at=orig.screened_at,
    )
    await db.commit()
    return new
