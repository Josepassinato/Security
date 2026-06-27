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
from app.evidence_pack.narrative import render_narrative, render_screening_case_dossier
from app.evidence_pack.portfolio import fetch_portfolio_report
from app.models.screening_decision import ScreeningDecision
from app.screening.intake import screen_and_record
from app.screening.opensanctions_client import OpenSanctionsClient
from app.services.screening_hash import verify_chain

router = APIRouter(prefix="/screening", tags=["screening"])

ReadAuth = Annotated[AuthUser, Depends(require_permission("cases:read"))]
WriteAuth = Annotated[AuthUser, Depends(require_permission("cases:write"))]

_TEMPLATES = Path(__file__).resolve().parents[6] / "customizations/compliance/dossier-templates"
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
