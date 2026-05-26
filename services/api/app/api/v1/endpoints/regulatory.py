"""Regulatory communications endpoints (Bacen 24h + ANPD).

Operacionaliza o fluxo de comunicação regulatória fim-a-fim:

* ``POST   /regulatory/communications/draft``
  Gera (ou retorna existente) um rascunho de comunicação Bacen 24h
  vinculado a um ``case_id``. Idempotente — mesma `(tenant, case, kind)`
  retorna o draft existente em vez de gerar novo.
* ``GET    /regulatory/communications``
  Lista artefatos do tenant. Filtros: ``case_id``, ``kind``, ``status``.
* ``GET    /regulatory/communications/{id}``
  Detalhe + verificação da hash chain pra esse `(tenant, kind)`.
* ``POST   /regulatory/communications/{id}/approve``
  Gate humano: aprova e dispara envio. Exige ``typed_name`` igual ao
  ``approver_email.split('@')[0]`` (anti-clique-acidental).
* ``POST   /regulatory/communications/expire-sweep``
  Job ops: marca como ``expired`` quem cruzou ``deadline_at`` sem envio.

UI (RegulatoryClock + diálogo typed-name + integração CaseWorkspace) vem
em sessão futura. Este módulo entrega só o backend — endpoints
testáveis via curl/HTTPie/pytest.

Trigger automático no classificador (Sprint+1)
─────────────────────────────────────────────
Quando um incidente é classificado como ``relevante`` pelo
auto-triage, o serviço deve chamar ``create_draft_for_case`` deste
módulo. O hook propriamente dito não é feito aqui pra evitar mexer no
agente em sessão de fundação backend — fica no SESSION-NOTES como
próximo passo.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AuthUser
from app.db.rls import TenantDBSession
from app.models.regulatory import RegulatoryCommunication
from app.services.regulatory_dispatch import (
    DispatchResult,
    get_dispatcher,
)
from app.services.regulatory_hash import compute_entry_hash, verify_chain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regulatory", tags=["regulatory"])

# ----------------------------------------------------------------------
# Pydantic schemas
# ----------------------------------------------------------------------


class DraftRequest(BaseModel):
    case_id: uuid.UUID
    kind: Literal["bacen", "anpd"] = "bacen"
    draft_md: str = Field(..., min_length=1, description="rascunho .md já renderizado")
    draft_meta: dict[str, Any] | None = None
    deadline_hours: int = Field(
        24, ge=1, le=720, description="janela regulatória em horas (default 24h Bacen)"
    )


class ApproveRequest(BaseModel):
    typed_name: str = Field(
        ..., min_length=1, description="nome digitado pelo aprovador (anti-clique)"
    )
    channel: Literal["email", "webhook", "sisbacen", "manual"]
    sent_to: str = Field(..., min_length=1, description="email/url destino")
    subject: str | None = None


class CommunicationRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    case_id: uuid.UUID | None
    kind: str
    status: str
    draft_md: str
    draft_meta: dict[str, Any] | None
    deadline_at: datetime
    submitted_at: datetime | None
    approver_email: str | None
    approver_typed_name: str | None
    sent_via: str | None
    sent_to: str | None
    dispatch_result: dict[str, Any] | None
    prev_hash: str | None
    entry_hash: str | None
    created_at: datetime

    @classmethod
    def from_model(cls, row: RegulatoryCommunication) -> "CommunicationRead":
        return cls(
            id=row.id,
            tenant_id=row.tenant_id,
            case_id=row.case_id,
            kind=row.kind,
            status=row.status,
            draft_md=row.draft_md,
            draft_meta=row.draft_meta,
            deadline_at=row.deadline_at,
            submitted_at=row.submitted_at,
            approver_email=row.approver_email,
            approver_typed_name=row.approver_typed_name,
            sent_via=row.sent_via,
            sent_to=row.sent_to,
            dispatch_result=row.dispatch_result,
            prev_hash=row.prev_hash,
            entry_hash=row.entry_hash,
            created_at=row.created_at,
        )


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


async def _latest_entry_hash(
    db: AsyncSession, tenant_id: uuid.UUID, kind: str
) -> str | None:
    """Pega o entry_hash mais recente desta (tenant, kind) — base da chain."""
    stmt = (
        select(RegulatoryCommunication.entry_hash)
        .where(
            RegulatoryCommunication.tenant_id == tenant_id,
            RegulatoryCommunication.kind == kind,
            RegulatoryCommunication.entry_hash.is_not(None),
        )
        .order_by(RegulatoryCommunication.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _seal(row: RegulatoryCommunication, prev_hash: str | None) -> None:
    """Calcula e grava entry_hash + prev_hash da linha."""
    row.prev_hash = prev_hash
    row.entry_hash = compute_entry_hash(
        prev_hash=prev_hash,
        row_id=row.id,
        tenant_id=row.tenant_id,
        case_id=row.case_id,
        kind=row.kind,
        status=row.status,
        draft_md=row.draft_md,
        draft_meta=row.draft_meta,
        deadline_at=row.deadline_at,
        submitted_at=row.submitted_at,
        approver_email=row.approver_email,
        approver_typed_name=row.approver_typed_name,
        sent_via=row.sent_via,
        sent_to=row.sent_to,
        dispatch_result=row.dispatch_result,
        created_at=row.created_at,
    )


# ----------------------------------------------------------------------
# Internal API — chamada pelo trigger automático do classificador
# ----------------------------------------------------------------------


async def create_draft_for_case(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    kind: Literal["bacen", "anpd"],
    draft_md: str,
    draft_meta: dict[str, Any] | None = None,
    deadline_hours: int = 24,
) -> RegulatoryCommunication:
    """Cria rascunho idempotente. Mesma `(tenant, case, kind)` ativa retorna o existente."""
    existing_stmt = (
        select(RegulatoryCommunication)
        .where(
            RegulatoryCommunication.tenant_id == tenant_id,
            RegulatoryCommunication.case_id == case_id,
            RegulatoryCommunication.kind == kind,
            RegulatoryCommunication.status.in_(["draft", "submitted"]),
        )
        .order_by(RegulatoryCommunication.created_at.desc())
        .limit(1)
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing is not None:
        return existing

    now = datetime.now(UTC)
    row = RegulatoryCommunication(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_id=case_id,
        kind=kind,
        status="draft",
        draft_md=draft_md,
        draft_meta=draft_meta,
        deadline_at=now + timedelta(hours=deadline_hours),
        created_at=now,
    )
    prev = await _latest_entry_hash(db, tenant_id, kind)
    _seal(row, prev)
    db.add(row)
    await db.flush()
    return row


# ----------------------------------------------------------------------
# HTTP endpoints
# ----------------------------------------------------------------------


@router.post(
    "/communications/draft",
    response_model=CommunicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_draft(
    payload: DraftRequest,
    db: TenantDBSession,
    user: AuthUser,
) -> CommunicationRead:
    """Cria rascunho de comunicação regulatória vinculado a um caso.

    Idempotente: se já existe rascunho ativo (``draft``/``submitted``)
    pra `(tenant, case, kind)`, retorna o existente em vez de criar.
    """
    row = await create_draft_for_case(
        db,
        tenant_id=user.tenant_id,
        case_id=payload.case_id,
        kind=payload.kind,
        draft_md=payload.draft_md,
        draft_meta=payload.draft_meta,
        deadline_hours=payload.deadline_hours,
    )
    await db.commit()
    return CommunicationRead.from_model(row)


@router.get(
    "/communications",
    response_model=list[CommunicationRead],
)
async def list_communications(
    db: TenantDBSession,
    user: AuthUser,
    case_id: Annotated[uuid.UUID | None, Query()] = None,
    kind: Annotated[Literal["bacen", "anpd"] | None, Query()] = None,
    status_filter: Annotated[
        Literal["draft", "submitted", "expired", "cancelled"] | None,
        Query(alias="status"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[CommunicationRead]:
    """Lista comunicações do tenant. RLS já restringe; filtros opcionais."""
    stmt = select(RegulatoryCommunication).order_by(
        RegulatoryCommunication.created_at.desc()
    )
    if case_id is not None:
        stmt = stmt.where(RegulatoryCommunication.case_id == case_id)
    if kind is not None:
        stmt = stmt.where(RegulatoryCommunication.kind == kind)
    if status_filter is not None:
        stmt = stmt.where(RegulatoryCommunication.status == status_filter)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return [CommunicationRead.from_model(r) for r in result.scalars().all()]


@router.get(
    "/communications/{comm_id}",
    response_model=CommunicationRead,
)
async def get_communication(
    comm_id: uuid.UUID,
    db: TenantDBSession,
    user: AuthUser,
) -> CommunicationRead:
    row = await db.get(RegulatoryCommunication, comm_id)
    if row is None or row.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="not found")
    return CommunicationRead.from_model(row)


@router.get(
    "/communications/{comm_id}/chain-verify",
)
async def chain_verify(
    comm_id: uuid.UUID,
    db: TenantDBSession,
    user: AuthUser,
) -> dict[str, Any]:
    """Replica a hash chain de (tenant, kind) até esta linha e valida."""
    target = await db.get(RegulatoryCommunication, comm_id)
    if target is None or target.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="not found")

    stmt = (
        select(RegulatoryCommunication)
        .where(
            RegulatoryCommunication.tenant_id == user.tenant_id,
            RegulatoryCommunication.kind == target.kind,
            RegulatoryCommunication.created_at <= target.created_at,
        )
        .order_by(RegulatoryCommunication.created_at.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    serialised = [
        {
            "id": r.id,
            "tenant_id": r.tenant_id,
            "case_id": r.case_id,
            "kind": r.kind,
            "status": r.status,
            "draft_md": r.draft_md,
            "draft_meta": r.draft_meta,
            "deadline_at": r.deadline_at,
            "submitted_at": r.submitted_at,
            "approver_email": r.approver_email,
            "approver_typed_name": r.approver_typed_name,
            "sent_via": r.sent_via,
            "sent_to": r.sent_to,
            "dispatch_result": r.dispatch_result,
            "created_at": r.created_at,
            "prev_hash": r.prev_hash,
            "entry_hash": r.entry_hash,
        }
        for r in rows
    ]
    ok, idx, reason = verify_chain(serialised)
    return {
        "ok": ok,
        "chain_length": len(serialised),
        "first_violation_index": idx,
        "reason": reason,
    }


@router.post(
    "/communications/{comm_id}/approve",
    response_model=CommunicationRead,
)
async def approve_and_send(
    comm_id: uuid.UUID,
    payload: ApproveRequest,
    db: TenantDBSession,
    user: AuthUser,
) -> CommunicationRead:
    """Gate humano + envio efetivo via dispatcher escolhido.

    Verifica typed_name == local-part do email do approver (anti-clique).
    Não aceita re-envio: depois de ``submitted`` é imutável.
    """
    row = await db.get(RegulatoryCommunication, comm_id)
    if row is None or row.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="not found")
    if row.status != "draft":
        raise HTTPException(
            status_code=409, detail=f"communication is not in draft state: {row.status}"
        )

    approver_email = user.email or ""
    expected_typed = approver_email.split("@", 1)[0]
    if payload.typed_name.strip().lower() != expected_typed.lower():
        raise HTTPException(
            status_code=400,
            detail=(
                "typed_name mismatch — digite o local-part do seu email "
                "(antes do @) pra confirmar a aprovação"
            ),
        )

    dispatcher = get_dispatcher(payload.channel)
    default_subject = (
        f"[Quarry] Comunicação regulatória {row.kind.upper()} — caso {row.case_id}"
    )
    result: DispatchResult = await dispatcher.send(
        subject=payload.subject or default_subject,
        body_md=row.draft_md,
        target=payload.sent_to,
        attachments={f"{row.kind}-{row.id}.md": row.draft_md.encode("utf-8")},
    )

    now = datetime.now(UTC)
    if result.ok:
        row.status = "submitted"
        row.submitted_at = now
        row.approver_id = user.user_id
        row.approver_email = approver_email
        row.approver_typed_name = payload.typed_name
        row.sent_via = payload.channel
        row.sent_to = payload.sent_to
    row.dispatch_result = result.to_jsonable()

    prev = await _latest_entry_hash(db, row.tenant_id, row.kind)
    if prev == row.entry_hash:
        # update vai mudar o entry_hash atual da linha; precisamos
        # chainar contra o que era prev antes — releitura.
        stmt = (
            select(RegulatoryCommunication.entry_hash)
            .where(
                RegulatoryCommunication.tenant_id == row.tenant_id,
                RegulatoryCommunication.kind == row.kind,
                RegulatoryCommunication.id != row.id,
                RegulatoryCommunication.entry_hash.is_not(None),
            )
            .order_by(RegulatoryCommunication.created_at.desc())
            .limit(1)
        )
        prev = (await db.execute(stmt)).scalar_one_or_none()
    _seal(row, prev)

    await db.commit()

    if not result.ok:
        # Sinaliza ao chamador que envio falhou (status fica em draft).
        raise HTTPException(
            status_code=502,
            detail={"dispatch_failed": result.to_jsonable()},
        )
    return CommunicationRead.from_model(row)


@router.post(
    "/communications/expire-sweep",
)
async def expire_sweep(
    db: TenantDBSession,
    user: AuthUser,
) -> dict[str, int]:
    """Job ops: marca como ``expired`` quem passou do prazo sem envio.

    Pode ser chamado por cron interno ou pelo próprio frontend ao carregar
    a página (idempotente). Retorna quantas linhas viraram expired.
    """
    now = datetime.now(UTC)
    stmt = (
        update(RegulatoryCommunication)
        .where(
            RegulatoryCommunication.tenant_id == user.tenant_id,
            RegulatoryCommunication.status == "draft",
            RegulatoryCommunication.deadline_at < now,
        )
        .values(status="expired", expired_at=now)
        .returning(RegulatoryCommunication.id)
    )
    result = await db.execute(stmt)
    expired_ids = result.scalars().all()

    # Re-selo de cada linha expirada — chain precisa refletir mudança.
    for cid in expired_ids:
        row = await db.get(RegulatoryCommunication, cid)
        if row is None:
            continue
        # prev = entry_hash da linha imediatamente anterior (não a deste row)
        stmt2 = (
            select(RegulatoryCommunication.entry_hash)
            .where(
                RegulatoryCommunication.tenant_id == row.tenant_id,
                RegulatoryCommunication.kind == row.kind,
                RegulatoryCommunication.id != row.id,
                RegulatoryCommunication.entry_hash.is_not(None),
                RegulatoryCommunication.created_at <= row.created_at,
            )
            .order_by(RegulatoryCommunication.created_at.desc())
            .limit(1)
        )
        prev = (await db.execute(stmt2)).scalar_one_or_none()
        _seal(row, prev)

    await db.commit()
    return {"expired_count": len(expired_ids)}


__all__ = ["router", "create_draft_for_case"]
