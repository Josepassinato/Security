"""Tests for the re-screening staleness selector (pure)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.screening.rescreen import select_stale_counterparties

_T1 = datetime(2026, 6, 20, 8, 0, 0, tzinfo=UTC)
_T2 = datetime(2026, 6, 26, 18, 0, 0, tzinfo=UTC)


def _row(**kw: Any) -> dict[str, Any]:
    base = {
        "counterparty_id": None,
        "counterparty_id_type": "CPF",
        "counterparty_name": "X",
        "counterparty_normalized": "x",
        "list_dataset": "us_ofac_sdn",
        "list_version": "v2",
        "screened_at": _T2,
    }
    base.update(kw)
    return base


def _portfolio() -> list[dict[str, Any]]:
    return [
        # A: screened v1 then v2 → latest is current → NOT stale
        _row(counterparty_id="A", counterparty_name="A", list_version="v1", screened_at=_T1),
        _row(counterparty_id="A", counterparty_name="A", list_version="v2", screened_at=_T2),
        # B: only old build → STALE
        _row(counterparty_id="B", counterparty_name="B", list_version="v1", screened_at=_T1),
        # C: current → not stale
        _row(counterparty_id="C", counterparty_name="C", list_version="v2", screened_at=_T2),
        # D: stale but on a DIFFERENT dataset → excluded
        _row(counterparty_id="D", counterparty_name="D", list_dataset="un_sc_sanctions", list_version="old"),
    ]


def test_selects_only_stale_on_target_dataset() -> None:
    stale = select_stale_counterparties(_portfolio(), list_dataset="us_ofac_sdn", current_version="v2")
    assert [c["counterparty_name"] for c in stale] == ["B"]


def test_latest_decision_wins_no_false_stale() -> None:
    # A's older v1 record must not make A stale — only the latest decision counts.
    stale = select_stale_counterparties(_portfolio(), list_dataset="us_ofac_sdn", current_version="v2")
    assert "A" not in [c["counterparty_name"] for c in stale]


def test_all_current_means_nothing_to_do() -> None:
    rows = [_row(counterparty_id="A", counterparty_name="A"), _row(counterparty_id="C", counterparty_name="C")]
    assert select_stale_counterparties(rows, list_dataset="us_ofac_sdn", current_version="v2") == []


def test_empty() -> None:
    assert select_stale_counterparties([], list_dataset="us_ofac_sdn", current_version="v2") == []
