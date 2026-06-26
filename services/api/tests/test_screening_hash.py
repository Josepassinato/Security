"""Tests for the sanctions-screening tamper-evident hash chain.

The hash chain is the mechanism that defends ``screening_decisions`` against a
privileged operator (or stolen DB credentials) that bypasses the immutability
trigger via ``ALTER TABLE … DISABLE TRIGGER ALL`` / ``TRUNCATE`` and forges a
replacement history. An external examiner can replay the chain on an export to
prove the screening history is intact.

This suite locks down the contract a compliance team relies on:

1. ``compute_entry_hash`` is deterministic (same row + prev_hash → same digest).
2. Mutating ANY evidence-bearing field changes the digest — including the
   sacred ``engine_raw_result``, the list version, and the derived score.
3. ``prev_hash`` is mixed in, so reordering decisions breaks verification.
4. ``verify_chain`` accepts a valid chain.
5. ``verify_chain`` rejects a deleted row, a rewritten row, a reordered row,
   and a row whose ``prev_hash`` doesn't link.
6. Legacy rows (no ``entry_hash``) are tolerated at the head; a gap after the
   chain has started is a forgery signal.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from app.services.screening_hash import compute_entry_hash, verify_chain


def _ts(seconds: int) -> datetime:
    return datetime(2026, 6, 26, 14, 0, seconds, tzinfo=UTC)


def _release() -> datetime:
    # OFAC SDN publication instant of the list-of-record.
    return datetime(2026, 6, 26, 8, 30, 0, tzinfo=UTC)


def _row(
    *,
    prev_hash: str | None,
    row_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    case_id: uuid.UUID | None = None,
    counterparty_name: str = "Joao da Silva",
    counterparty_normalized: str = "joao da silva",
    counterparty_id: str | None = "12345678901",
    counterparty_id_type: str = "CPF",
    counterparty_jurisdiction: str | None = "BR",
    screening_trigger: str | None = "onboarding",
    matching_engine: str = "complyadvantage",
    list_of_record: str = "opensanctions",
    list_source: str = "OFAC_SDN",
    list_dataset: str = "us_ofac_sdn",
    list_version: str = "20260626-01",
    list_release_date: datetime | None = None,
    engine_raw_result: dict[str, Any] | None = None,
    match_score: int = 90,
    scoring_rule_version: str = "v1",
    decision: str = "POTENTIAL_MATCH",
    disposition: str = "PENDING",
    human_reviewer: str | None = None,
    rationale: str = "",
    screened_at: datetime | None = None,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    """Build a row dict + its computed ``entry_hash`` for chain replay."""
    rid = row_id or uuid.UUID("11111111-1111-1111-1111-111111111111")
    tid = tenant_id or uuid.UUID("22222222-2222-2222-2222-222222222222")
    raw = engine_raw_result if engine_raw_result is not None else {"hits": [{"strength": "strong"}]}
    rel = list_release_date or _release()
    sat = screened_at or _ts(0)
    cat = created_at or _ts(0)
    digest = compute_entry_hash(
        prev_hash=prev_hash,
        row_id=rid,
        tenant_id=tid,
        case_id=case_id,
        counterparty_name=counterparty_name,
        counterparty_normalized=counterparty_normalized,
        counterparty_id=counterparty_id,
        counterparty_id_type=counterparty_id_type,
        counterparty_jurisdiction=counterparty_jurisdiction,
        screening_trigger=screening_trigger,
        matching_engine=matching_engine,
        list_of_record=list_of_record,
        list_source=list_source,
        list_dataset=list_dataset,
        list_version=list_version,
        list_release_date=rel,
        engine_raw_result=raw,
        match_score=match_score,
        scoring_rule_version=scoring_rule_version,
        decision=decision,
        disposition=disposition,
        human_reviewer=human_reviewer,
        rationale=rationale,
        screened_at=sat,
        created_at=cat,
    )
    return {
        "id": rid,
        "tenant_id": tid,
        "case_id": case_id,
        "counterparty_name": counterparty_name,
        "counterparty_normalized": counterparty_normalized,
        "counterparty_id": counterparty_id,
        "counterparty_id_type": counterparty_id_type,
        "counterparty_jurisdiction": counterparty_jurisdiction,
        "screening_trigger": screening_trigger,
        "matching_engine": matching_engine,
        "list_of_record": list_of_record,
        "list_source": list_source,
        "list_dataset": list_dataset,
        "list_version": list_version,
        "list_release_date": rel,
        "engine_raw_result": raw,
        "match_score": match_score,
        "scoring_rule_version": scoring_rule_version,
        "decision": decision,
        "disposition": disposition,
        "human_reviewer": human_reviewer,
        "rationale": rationale,
        "screened_at": sat,
        "created_at": cat,
        "prev_hash": prev_hash,
        "entry_hash": digest,
    }


def _kwargs(row: dict[str, Any]) -> dict[str, Any]:
    """Re-derive compute_entry_hash kwargs from a row dict."""
    return {
        "prev_hash": row["prev_hash"],
        "row_id": row["id"],
        "tenant_id": row["tenant_id"],
        "case_id": row.get("case_id"),
        "counterparty_name": row["counterparty_name"],
        "counterparty_normalized": row["counterparty_normalized"],
        "counterparty_id": row.get("counterparty_id"),
        "counterparty_id_type": row["counterparty_id_type"],
        "counterparty_jurisdiction": row.get("counterparty_jurisdiction"),
        "screening_trigger": row.get("screening_trigger"),
        "matching_engine": row["matching_engine"],
        "list_of_record": row["list_of_record"],
        "list_source": row["list_source"],
        "list_dataset": row["list_dataset"],
        "list_version": row["list_version"],
        "list_release_date": row["list_release_date"],
        "engine_raw_result": row.get("engine_raw_result"),
        "match_score": row["match_score"],
        "scoring_rule_version": row["scoring_rule_version"],
        "decision": row["decision"],
        "disposition": row["disposition"],
        "human_reviewer": row.get("human_reviewer"),
        "rationale": row["rationale"],
        "screened_at": row["screened_at"],
        "created_at": row["created_at"],
    }


def test_compute_entry_hash_is_deterministic() -> None:
    a = compute_entry_hash(**_kwargs(_row(prev_hash=None)))
    b = compute_entry_hash(**_kwargs(_row(prev_hash=None)))
    assert a == b


def test_name_only_screening_chains_and_differs() -> None:
    """A name-only screening (counterparty_id=None) hashes cleanly and is
    distinct from the same name carrying a document — None is evidence too."""
    with_doc = compute_entry_hash(**_kwargs(_row(prev_hash=None)))
    name_only = compute_entry_hash(**_kwargs(_row(prev_hash=None, counterparty_id=None)))
    assert with_doc != name_only
    chain = [_row(prev_hash=None, counterparty_id=None)]
    ok, idx, reason = verify_chain(chain)
    assert ok and idx is None and reason is None


@pytest.mark.parametrize(
    "field,new_value",
    [
        ("counterparty_name", "Maria Souza"),
        ("counterparty_normalized", "maria souza"),
        ("counterparty_id", "98765432100"),
        ("counterparty_id_type", "PASSPORT"),
        ("counterparty_jurisdiction", "US"),
        ("screening_trigger", "transaction:abc123"),
        ("matching_engine", "dowjones"),
        ("list_of_record", "ofac_public_file"),
        ("list_source", "UN"),
        ("list_dataset", "un_sc_sanctions"),
        ("list_version", "20260627-01"),
        ("match_score", 70),
        ("scoring_rule_version", "v2"),
        ("decision", "TRUE_MATCH"),
        ("disposition", "BLOCKED"),
        ("human_reviewer", "bsa.officer@optimus.com"),
        ("rationale", "name + DOB exact, confirmed SDN entity"),
    ],
)
def test_any_field_change_changes_digest(field: str, new_value: Any) -> None:
    base = compute_entry_hash(**_kwargs(_row(prev_hash=None)))
    mutated = compute_entry_hash(**_kwargs(_row(prev_hash=None, **{field: new_value})))
    assert base != mutated, f"mutating {field} must change the digest"


def test_list_release_date_change_changes_digest() -> None:
    """The list version's publication instant is evidence — tampering must show."""
    base = compute_entry_hash(**_kwargs(_row(prev_hash=None)))
    later = compute_entry_hash(
        **_kwargs(_row(prev_hash=None, list_release_date=datetime(2026, 6, 26, 9, 0, 0, tzinfo=UTC)))
    )
    assert base != later


def test_engine_raw_result_is_tamper_evident() -> None:
    """The untouched engine payload is sacred — rewriting it breaks the chain."""
    base = compute_entry_hash(**_kwargs(_row(prev_hash=None)))
    forged = compute_entry_hash(
        **_kwargs(_row(prev_hash=None, engine_raw_result={"hits": []}))
    )
    assert base != forged


def test_verify_chain_accepts_valid_chain() -> None:
    r1 = _row(prev_hash=None, created_at=_ts(0))
    r2 = _row(prev_hash=r1["entry_hash"], row_id=uuid.uuid4(), created_at=_ts(1), decision="NO_MATCH")
    r3 = _row(prev_hash=r2["entry_hash"], row_id=uuid.uuid4(), created_at=_ts(2),
              disposition="CLEARED_FALSE_POSITIVE", human_reviewer="rev@x.com", rationale="cleared")
    ok, idx, reason = verify_chain([r1, r2, r3])
    assert ok and idx is None and reason is None


def test_verify_chain_rejects_rewritten_row() -> None:
    r1 = _row(prev_hash=None, created_at=_ts(0))
    r2 = _row(prev_hash=r1["entry_hash"], row_id=uuid.uuid4(), created_at=_ts(1))
    # Retroactively "fix" a disposition without re-chaining — the forgery we exist to catch.
    r2_forged = dict(r2)
    r2_forged["disposition"] = "CLEARED_FALSE_POSITIVE"
    ok, idx, reason = verify_chain([r1, r2_forged])
    assert not ok and idx == 1 and reason == "entry_hash mismatch"


def test_verify_chain_rejects_reordered_rows() -> None:
    r1 = _row(prev_hash=None, created_at=_ts(0))
    r2 = _row(prev_hash=r1["entry_hash"], row_id=uuid.uuid4(), created_at=_ts(1))
    ok, idx, reason = verify_chain([r2, r1])
    assert not ok and idx == 0 and reason == "prev_hash mismatch"


def test_verify_chain_rejects_deleted_row() -> None:
    r1 = _row(prev_hash=None, created_at=_ts(0))
    r2 = _row(prev_hash=r1["entry_hash"], row_id=uuid.uuid4(), created_at=_ts(1))
    r3 = _row(prev_hash=r2["entry_hash"], row_id=uuid.uuid4(), created_at=_ts(2))
    # Drop the middle row: r3.prev_hash no longer links to r1.
    ok, idx, reason = verify_chain([r1, r3])
    assert not ok and idx == 1 and reason == "prev_hash mismatch"


def test_verify_chain_tolerates_legacy_head_but_not_mid_gap() -> None:
    legacy = _row(prev_hash=None)
    legacy["prev_hash"] = None
    legacy["entry_hash"] = None  # pre-chain row
    chained = _row(prev_hash=None, row_id=uuid.uuid4(), created_at=_ts(1))
    ok, _, _ = verify_chain([legacy, chained])
    assert ok

    # A NULL entry_hash AFTER the chain started is a deletion/forgery signal.
    gapped = _row(prev_hash=None, row_id=uuid.uuid4())
    gapped["entry_hash"] = None
    ok2, idx2, reason2 = verify_chain([chained, gapped])
    assert not ok2 and idx2 == 1 and "chain interrupted" in reason2
