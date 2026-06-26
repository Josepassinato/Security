"""Tests for the portfolio screening report — the commercial aggregate.

The headline is the list-freshness index, and its honesty is the product: a
counterparty last screened against an older SDN build must surface as STALE, not
hide inside a "100% clean" claim. These tests lock that behaviour plus the
matching posture, the HITL-guaranteed "zero resolved without rationale", and the
portfolio-wide chain integrity passthrough.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.evidence_pack.narrative import render_narrative
from app.evidence_pack.portfolio import build_portfolio_report

_T1 = datetime(2026, 6, 20, 8, 0, 0, tzinfo=UTC)  # older SDN build
_T2 = datetime(2026, 6, 26, 18, 0, 0, tzinfo=UTC)  # current SDN build

_TEMPLATE = (
    Path(__file__).resolve().parents[3]
    / "customizations/compliance/dossier-templates/aml-portfolio-report-v1.html.j2"
)


def _row(**kw: Any) -> dict[str, Any]:
    base = {
        "counterparty_id": None,
        "counterparty_id_type": "CPF",
        "counterparty_name": "X",
        "counterparty_normalized": "x",
        "list_dataset": "us_ofac_sdn",
        "list_version": "v2",
        "list_release_date": _T2,
        "decision": "NO_MATCH",
        "disposition": "PENDING",
        "human_reviewer": None,
        "rationale": "",
        "screened_at": _T2,
    }
    base.update(kw)
    return base


def _portfolio() -> list[dict[str, Any]]:
    return [
        # A: screened twice; latest is current build → fresh, NO_MATCH
        _row(counterparty_id="111", counterparty_name="A", list_version="v1",
             list_release_date=_T1, screened_at=_T1),
        _row(counterparty_id="111", counterparty_name="A", list_version="v2",
             list_release_date=_T2, screened_at=_T2),
        # B: only screened against the OLD build → STALE, potential, pending
        _row(counterparty_id="222", counterparty_name="B", list_version="v1",
             list_release_date=_T1, screened_at=_T1, decision="POTENTIAL_MATCH",
             disposition="PENDING"),
        # C: name-only, current build, potential RESOLVED with reviewer+rationale
        _row(counterparty_id=None, counterparty_name="C Souza", counterparty_normalized="c souza",
             decision="POTENTIAL_MATCH", disposition="CLEARED_FALSE_POSITIVE",
             human_reviewer="bsa@optimus.com", rationale="weak alias, distinct DOB"),
    ]


def test_counts_distinct_counterparties() -> None:
    r = build_portfolio_report(_portfolio(), chain_ok=True)
    assert r["counterparty_count"] == 3


def test_freshness_index_flags_stale() -> None:
    r = build_portfolio_report(_portfolio(), chain_ok=True)
    assert r["freshness"]["fresh"] == 2
    assert r["freshness"]["stale"] == 1
    assert r["freshness"]["pct_current"] == 66.7
    assert r["current_build"]["us_ofac_sdn"]["list_version"] == "v2"
    stale_names = [c["counterparty_name"] for c in r["stale_counterparties"]]
    assert stale_names == ["B"]


def test_matching_posture() -> None:
    r = build_portfolio_report(_portfolio(), chain_ok=True)
    assert r["potential_matches"] == 2  # B (pending) + C (resolved); A is NO_MATCH
    assert r["resolved"] == 1
    assert r["pending_review"] == 1
    assert r["resolved_without_rationale"] == 0  # HITL constraint, proven from data


def test_chain_status_passthrough() -> None:
    ok = build_portfolio_report(_portfolio(), chain_ok=True)
    assert ok["chain"]["intact"] is True
    broken = build_portfolio_report(_portfolio(), chain_ok=False, chain_first_broken_index=7)
    assert broken["chain"]["intact"] is False
    assert broken["chain"]["first_broken_index"] == 7


def test_renders_headline_and_stale_and_integrity() -> None:
    r = build_portfolio_report(_portfolio(), chain_ok=True)
    html = render_narrative(
        _TEMPLATE.read_text(encoding="utf-8"),
        {"report": r, "tenant_name": "Optimus Fintech S.A.", "generated_at": "2026-06-26T21:00:00Z"},
    )
    assert "66.7%" in html
    assert "us_ofac_sdn" in html
    assert "B" in html  # stale counterparty surfaced
    assert "ÍNTEGRA" in html
    # zero-without-rationale proof shows the reassuring parenthetical
    assert "garantido por constraint" in html
