"""Portfolio screening report — the aggregated, commercial artifact.

What a correspondent bank pays for: not one name, but proof the whole portfolio
of its client is clean and *provable*. This module turns the immutable
screening ledger into that proof.

The headline metric is the **list-freshness index**: of N counterparties, how
many were last screened against the *current* build of the sanctions list, and
how many against an older build (and are therefore queued for re-screening).
This is the honest framing — "all clean against version X" is only ever true at
an instant, because OFAC updates the SDN between screenings. A report that
hides stale screenings is a documented lie; this one surfaces them.

Design:
* ``build_portfolio_report`` is PURE (rows in → report dict out). It can run on
  a CSV/JSON export, mirroring ``screening_hash.verify_chain``. Unit-tested.
* ``fetch_portfolio_report`` is the thin DB wrapper: load the tenant's rows,
  verify the chain, build the report.

The "current state" of each counterparty is its **latest** screening decision
(max ``screened_at``); a case investigated many times resolves to one current
posture, exactly how a bank reads its book.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_RESOLVED_DISPOSITIONS = {"CLEARED_FALSE_POSITIVE", "BLOCKED", "REPORTED"}


def _cp_key(row: Mapping[str, Any]) -> tuple[str, str]:
    """Stable identity for a counterparty: document if present, else name."""
    cid = row.get("counterparty_id")
    if cid:
        return (str(row.get("counterparty_id_type") or ""), str(cid))
    return ("NAME", str(row.get("counterparty_normalized") or row.get("counterparty_name") or ""))


def build_portfolio_report(
    decisions: Sequence[Mapping[str, Any]],
    *,
    chain_ok: bool,
    chain_first_broken_index: int | None = None,
) -> dict[str, Any]:
    """Aggregate one tenant's screening decisions into a portfolio report.

    ``decisions`` are screening_decisions rows for a single tenant. ``chain_ok``
    / ``chain_first_broken_index`` come from ``screening_hash.verify_chain`` over
    the same rows — passed in so this function stays pure.
    """
    # Current build per dataset = the freshest release the portfolio has seen.
    current_build: dict[str, dict[str, Any]] = {}
    for row in decisions:
        ds = row.get("list_dataset")
        if ds is None:
            continue
        rel = row.get("list_release_date")
        cur = current_build.get(ds)
        if cur is None or (rel is not None and rel > cur["list_release_date"]):
            current_build[ds] = {
                "list_version": row.get("list_version"),
                "list_release_date": rel,
            }

    # Latest decision per counterparty = its current posture.
    latest: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in decisions:
        key = _cp_key(row)
        cur = latest.get(key)
        if cur is None or row.get("screened_at", "") > cur.get("screened_at", ""):
            latest[key] = row

    n = len(latest)
    fresh = 0
    stale_counterparties: list[dict[str, Any]] = []
    decision_breakdown: dict[str, int] = {}
    disposition_breakdown: dict[str, int] = {}
    potential = resolved = pending_review = resolved_without_rationale = 0

    for row in latest.values():
        decision_breakdown[row.get("decision", "?")] = decision_breakdown.get(row.get("decision", "?"), 0) + 1
        disposition_breakdown[row.get("disposition", "?")] = disposition_breakdown.get(row.get("disposition", "?"), 0) + 1

        # Freshness vs the current build of this row's dataset.
        ds = row.get("list_dataset")
        cur = current_build.get(ds) if ds is not None else None
        if cur is not None and row.get("list_release_date") == cur["list_release_date"]:
            fresh += 1
        else:
            stale_counterparties.append(
                {
                    "counterparty_name": row.get("counterparty_name"),
                    "counterparty_id": row.get("counterparty_id"),
                    "list_dataset": ds,
                    "screened_against_version": row.get("list_version"),
                    "screened_against_release": row.get("list_release_date"),
                    "current_version": cur["list_version"] if cur else None,
                    "current_release": cur["list_release_date"] if cur else None,
                }
            )

        if row.get("decision") == "POTENTIAL_MATCH":
            potential += 1
            disp = row.get("disposition")
            if disp in _RESOLVED_DISPOSITIONS:
                resolved += 1
                # Proven from data — the HITL CHECK constraint makes this 0.
                if not (row.get("human_reviewer") and (row.get("rationale") or "").strip()):
                    resolved_without_rationale += 1
            elif disp == "PENDING":
                pending_review += 1

    return {
        "counterparty_count": n,
        "current_build": current_build,
        "freshness": {
            "fresh": fresh,
            "stale": n - fresh,
            "pct_current": round(fresh / n * 100, 1) if n else 0.0,
        },
        "stale_counterparties": stale_counterparties,
        "potential_matches": potential,
        "resolved": resolved,
        "pending_review": pending_review,
        "resolved_without_rationale": resolved_without_rationale,
        "decision_breakdown": decision_breakdown,
        "disposition_breakdown": disposition_breakdown,
        "chain": {
            "intact": chain_ok,
            "first_broken_index": chain_first_broken_index,
        },
    }


async def fetch_portfolio_report(db: Any, tenant_id: Any) -> dict[str, Any]:
    """Load a tenant's screening decisions, verify the chain, build the report."""
    from sqlalchemy import select

    from app.models.screening_decision import ScreeningDecision
    from app.services.screening_hash import verify_chain

    stmt = (
        select(ScreeningDecision)
        .where(ScreeningDecision.tenant_id == tenant_id)
        .order_by(ScreeningDecision.created_at.asc(), ScreeningDecision.id.asc())
    )
    orm_rows = (await db.execute(stmt)).scalars().all()
    rows = [{c.name: getattr(r, c.name) for c in ScreeningDecision.__table__.columns} for r in orm_rows]
    ok, bad_idx, _reason = verify_chain(rows)
    return build_portfolio_report(rows, chain_ok=ok, chain_first_broken_index=bad_idx)


__all__ = ["build_portfolio_report", "fetch_portfolio_report"]
