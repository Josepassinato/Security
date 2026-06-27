"""Re-screening cadence (Phase 3) — act on list-freshness staleness.

OFAC updates the SDN between screenings; a name clean against yesterday's build
may be on today's. The portfolio freshness index DETECTS stale counterparties;
this is the job that ACTS: when OpenSanctions publishes a newer build of the
dataset, re-run every counterparty whose latest screening was against an older
build, appending a fresh chained record per counterparty (``screening_trigger =
'rescreen'``).

``select_stale_counterparties`` is PURE (latest-per-counterparty + the current
build version → who to re-screen) so the selection logic is unit-tested without
network or DB. ``rescreen_tenant`` is the thin orchestration that asks
OpenSanctions for the current build, loads the ledger, and re-screens the stale
set through the same append-only writer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import select

from app.evidence_pack.portfolio import latest_by_counterparty
from app.models.screening_decision import ScreeningDecision
from app.screening.intake import screen_and_record
from app.screening.opensanctions_client import OpenSanctionsClient
from app.screening.scoring import DEFAULT_THRESHOLD


def select_stale_counterparties(
    decisions: Sequence[Mapping[str, Any]],
    *,
    list_dataset: str,
    current_version: str,
) -> list[Mapping[str, Any]]:
    """Latest decision per counterparty on ``list_dataset`` whose ``list_version``
    is not the current build — the set to re-screen."""
    stale: list[Mapping[str, Any]] = []
    for row in latest_by_counterparty(decisions).values():
        if row.get("list_dataset") != list_dataset:
            continue
        if row.get("list_version") != current_version:
            stale.append(row)
    return stale


async def _load_decisions(db: Any, tenant_id: Any) -> list[dict[str, Any]]:
    stmt = (
        select(ScreeningDecision)
        .where(ScreeningDecision.tenant_id == tenant_id)
        .order_by(ScreeningDecision.created_at.asc(), ScreeningDecision.id.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [{c.name: getattr(r, c.name) for c in ScreeningDecision.__table__.columns} for r in rows]


async def rescreen_tenant(
    db: Any,
    client: OpenSanctionsClient,
    *,
    tenant_id: Any,
    list_dataset: str = "us_ofac_sdn",
    threshold: int = DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    """Re-screen every counterparty of ``tenant_id`` whose latest decision used an
    older build of ``list_dataset``. Returns a summary; commits the new records."""
    current_version, _release = await client.dataset_version(list_dataset)
    decisions = await _load_decisions(db, tenant_id)
    stale = select_stale_counterparties(decisions, list_dataset=list_dataset, current_version=current_version)

    rescreened = 0
    for cp in stale:
        await screen_and_record(
            db,
            client,
            tenant_id=tenant_id,
            counterparty_name=cp["counterparty_name"],
            counterparty_normalized=cp["counterparty_normalized"],
            counterparty_id_type=cp["counterparty_id_type"],
            counterparty_id=cp.get("counterparty_id"),
            counterparty_jurisdiction=cp.get("counterparty_jurisdiction"),
            screening_trigger="rescreen",
            case_id=cp.get("case_id"),
            list_dataset=list_dataset,
            threshold=threshold,
        )
        rescreened += 1

    if rescreened:
        await db.commit()

    return {
        "list_dataset": list_dataset,
        "current_version": current_version,
        "counterparties": len(latest_by_counterparty(decisions)),
        "stale": len(stale),
        "rescreened": rescreened,
    }


__all__ = ["select_stale_counterparties", "rescreen_tenant"]
