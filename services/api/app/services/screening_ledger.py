"""Append-only writer for the sanctions screening evidence ledger.

Mirrors ``app.services.audit.emit_audit``: resolve the tenant's current chain
tail, compute this row's ``entry_hash`` over its canonical contents + the
previous hash, then INSERT. There is no update path — a changed disposition is
a NEW chained record (the immutability trigger blocks UPDATE/DELETE).

The HITL invariant ("a POTENTIAL_MATCH never auto-resolves") is enforced at the
DB layer (CHECK constraint ``chk_screening_potential_match_hitl``) AND here, so
a programming error surfaces as a clear ValueError instead of a constraint
violation deep in a transaction.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.screening_decision import ScreeningDecision
from app.services.screening_hash import compute_entry_hash


async def _resolve_prev_hash(db: AsyncSession, tenant_id: uuid.UUID) -> str | None:
    """Return the most recent ``entry_hash`` for ``tenant_id`` (the chain tail).

    Rows without an ``entry_hash`` (legacy / pre-chain) are skipped via the
    partial index ``idx_screening_chain_tail``.
    """
    stmt = (
        select(ScreeningDecision.entry_hash)
        .where(ScreeningDecision.tenant_id == tenant_id)
        .where(ScreeningDecision.entry_hash.is_not(None))
        .order_by(ScreeningDecision.created_at.desc(), ScreeningDecision.id.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


def _assert_hitl(*, decision: str, disposition: str, human_reviewer: str | None, rationale: str) -> None:
    """Enforce the human-in-the-loop invariants before we ever touch the DB."""
    if human_reviewer is not None and not (rationale or "").strip():
        raise ValueError("a human-reviewed decision requires a non-empty rationale")
    if decision == "POTENTIAL_MATCH" and disposition != "PENDING":
        if human_reviewer is None or not (rationale or "").strip():
            raise ValueError(
                "POTENTIAL_MATCH cannot be resolved without a human reviewer and rationale"
            )


async def record_screening_decision(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    counterparty_name: str,
    counterparty_normalized: str,
    counterparty_id: str,
    counterparty_id_type: str,
    matching_engine: str,
    list_of_record: str,
    list_source: str,
    list_dataset: str,
    list_version: str,
    list_release_date: datetime,
    engine_raw_result: dict[str, Any],
    match_score: int,
    scoring_rule_version: str,
    decision: str,
    disposition: str,
    screened_at: datetime,
    case_id: uuid.UUID | None = None,
    human_reviewer: str | None = None,
    rationale: str = "",
) -> ScreeningDecision:
    """Append one immutable, hash-chained screening decision and return it."""
    _assert_hitl(
        decision=decision,
        disposition=disposition,
        human_reviewer=human_reviewer,
        rationale=rationale,
    )

    row_id = uuid.uuid4()
    created_at = datetime.now(UTC)
    prev_hash = await _resolve_prev_hash(db, tenant_id)

    entry_hash = compute_entry_hash(
        prev_hash=prev_hash,
        row_id=row_id,
        tenant_id=tenant_id,
        case_id=case_id,
        counterparty_name=counterparty_name,
        counterparty_normalized=counterparty_normalized,
        counterparty_id=counterparty_id,
        counterparty_id_type=counterparty_id_type,
        matching_engine=matching_engine,
        list_of_record=list_of_record,
        list_source=list_source,
        list_dataset=list_dataset,
        list_version=list_version,
        list_release_date=list_release_date,
        engine_raw_result=engine_raw_result,
        match_score=match_score,
        scoring_rule_version=scoring_rule_version,
        decision=decision,
        disposition=disposition,
        human_reviewer=human_reviewer,
        rationale=rationale,
        screened_at=screened_at,
        created_at=created_at,
    )

    row = ScreeningDecision(
        id=row_id,
        tenant_id=tenant_id,
        case_id=case_id,
        counterparty_name=counterparty_name,
        counterparty_normalized=counterparty_normalized,
        counterparty_id=counterparty_id,
        counterparty_id_type=counterparty_id_type,
        matching_engine=matching_engine,
        list_of_record=list_of_record,
        list_source=list_source,
        list_dataset=list_dataset,
        list_version=list_version,
        list_release_date=list_release_date,
        engine_raw_result=engine_raw_result,
        match_score=match_score,
        scoring_rule_version=scoring_rule_version,
        decision=decision,
        disposition=disposition,
        human_reviewer=human_reviewer,
        rationale=rationale,
        screened_at=screened_at,
        created_at=created_at,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
    )
    db.add(row)
    await db.flush()
    return row


__all__ = ["record_screening_decision"]
