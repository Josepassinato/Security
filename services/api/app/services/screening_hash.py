"""Tamper-evident hash chain for sanctions screening decisions.

The ``screening_decisions`` table is append-only via the
``trg_screening_decisions_immutable`` trigger and tenant-isolated via RLS.
That defends against in-flight UPDATE/DELETE. It does NOT defend against a
privileged operator (or stolen DB credentials) issuing a
``TRUNCATE`` / ``DROP`` / ``ALTER TABLE … DISABLE TRIGGER ALL`` and forging a
replacement history that still satisfies the trigger.

For a sanctions evidence ledger that gap is unacceptable: the entire pitch is
that every screening decision is defensible in an OFAC/FinCEN/Bacen exam.
A hash chain closes it WITHOUT trusting Postgres. Every row stores:

* ``prev_hash``  — the ``entry_hash`` of the previous screening decision for
  the same tenant, or ``None`` for the genesis row.
* ``entry_hash`` — sha256 over a canonical serialization of this row's
  evidence-bearing fields, mixed with ``prev_hash``.

Anyone — including an external examiner — can replay the chain
deterministically and prove that no decision was deleted, reordered, or
silently rewritten. The verification logic is intentionally pure (no DB
access) so it can run on a CSV/JSON export as easily as on live rows.

This mirrors ``app.services.audit_hash`` (audit_log) and
``app.services.regulatory_hash`` (regulatory_communications); the chains are
independent and can be verified side by side during an inspection.

The set of hashed fields is deliberately exhaustive — it covers every field a
screening decision asserts (counterparty, list-of-record + version, engine
attribution, raw engine payload, derived score + ruler version, decision,
disposition, reviewer, rationale, screened_at). Adding a field is a
chain-breaking change and requires a schema migration + domain-tag bump.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

# Bump this tag if the hashed field set ever changes — it forces a clean
# break rather than a silent collision with v1 chains.
_DOMAIN_TAG = b"\x1fscreening-decisions-v1\x1f"


def _canonicalise(value: Any) -> Any:
    """Map non-JSON-native types into something ``json.dumps`` encodes deterministically."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        # ISO 8601 with explicit offset; required for chain stability across
        # DB drivers that may otherwise stringify with subtle differences.
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _canonicalise(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonicalise(v) for v in value]
    return str(value)


def compute_entry_hash(
    *,
    prev_hash: str | None,
    row_id: uuid.UUID,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID | None,
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
    engine_raw_result: dict[str, Any] | None,
    match_score: int,
    scoring_rule_version: str,
    decision: str,
    disposition: str,
    human_reviewer: str | None,
    rationale: str,
    screened_at: datetime,
    created_at: datetime,
) -> str:
    """Compute the SHA-256 hash of the canonical row contents + prev hash.

    ``engine_raw_result`` is hashed as persisted (the untouched engine payload);
    the chain is over the *stored* form, so tampering with the raw evidence is
    detectable.
    """
    body = {
        "id": _canonicalise(row_id),
        "tenant_id": _canonicalise(tenant_id),
        "case_id": _canonicalise(case_id),
        "counterparty_name": counterparty_name,
        "counterparty_normalized": counterparty_normalized,
        "counterparty_id": counterparty_id,
        "counterparty_id_type": counterparty_id_type,
        "matching_engine": matching_engine,
        "list_of_record": list_of_record,
        "list_source": list_source,
        "list_dataset": list_dataset,
        "list_version": list_version,
        "list_release_date": _canonicalise(list_release_date),
        "engine_raw_result": _canonicalise(engine_raw_result),
        "match_score": match_score,
        "scoring_rule_version": scoring_rule_version,
        "decision": decision,
        "disposition": disposition,
        "human_reviewer": human_reviewer,
        "rationale": rationale,
        "screened_at": _canonicalise(screened_at),
        "created_at": _canonicalise(created_at),
    }
    serialised = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    h = hashlib.sha256()
    h.update((prev_hash or "").encode("utf-8"))
    h.update(_DOMAIN_TAG)
    h.update(serialised.encode("utf-8"))
    return h.hexdigest()


def verify_chain(rows: list[dict[str, Any]]) -> tuple[bool, int | None, str | None]:
    """Replay ``rows`` (oldest → newest, same tenant) and verify the chain.

    Each row must expose the same field names as :func:`compute_entry_hash`
    plus ``prev_hash`` and ``entry_hash``.

    Returns ``(True, None, None)`` on success, or ``(False, index, reason)``
    pointing at the first violating row. A row missing ``entry_hash`` is
    treated as legacy / unchained and skipped — the chain "starts" from the
    first row that carries one. Once chained, a gap is a forgery signal.
    """
    prev_hash: str | None = None
    started = False
    for idx, row in enumerate(rows):
        stored = row.get("entry_hash")
        if stored is None:
            if started:
                return False, idx, "chain interrupted: entry_hash missing"
            continue
        started = True

        recorded_prev = row.get("prev_hash")
        if recorded_prev != prev_hash:
            return False, idx, "prev_hash mismatch"

        computed = compute_entry_hash(
            prev_hash=prev_hash,
            row_id=row["id"],
            tenant_id=row["tenant_id"],
            case_id=row.get("case_id"),
            counterparty_name=row["counterparty_name"],
            counterparty_normalized=row["counterparty_normalized"],
            counterparty_id=row["counterparty_id"],
            counterparty_id_type=row["counterparty_id_type"],
            matching_engine=row["matching_engine"],
            list_of_record=row["list_of_record"],
            list_source=row["list_source"],
            list_dataset=row["list_dataset"],
            list_version=row["list_version"],
            list_release_date=row["list_release_date"],
            engine_raw_result=row.get("engine_raw_result"),
            match_score=row["match_score"],
            scoring_rule_version=row["scoring_rule_version"],
            decision=row["decision"],
            disposition=row["disposition"],
            human_reviewer=row.get("human_reviewer"),
            rationale=row["rationale"],
            screened_at=row["screened_at"],
            created_at=row["created_at"],
        )
        if computed != stored:
            return False, idx, "entry_hash mismatch"
        prev_hash = computed
    return True, None, None


__all__ = [
    "compute_entry_hash",
    "verify_chain",
]
