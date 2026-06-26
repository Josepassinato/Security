"""Tests for Phase 2 screening intake — scoring + attribution (pure)."""

from __future__ import annotations

from datetime import datetime

import pytest
from app.screening.intake import prepare_screening_record
from app.screening.scoring import (
    DEFAULT_THRESHOLD,
    NO_MATCH,
    POTENTIAL_MATCH,
    decide,
    derive_match_score,
)


@pytest.mark.parametrize(
    "score,expected",
    [(1.0, 100), (0.85, 85), (0.7, 70), (0.0, 0), (0.846, 85)],
)
def test_derive_opensanctions_v1(score: float, expected: int) -> None:
    assert derive_match_score(raw={"score": score}, rule_version="opensanctions-v1") == expected


def test_derive_missing_score_is_zero() -> None:
    assert derive_match_score(raw={}, rule_version="opensanctions-v1") == 0


def test_derive_unknown_rule_raises() -> None:
    with pytest.raises(ValueError):
        derive_match_score(raw={"score": 1.0}, rule_version="made-up-v9")


def test_decide_threshold() -> None:
    assert decide(match_score=85) == POTENTIAL_MATCH
    assert decide(match_score=84) == NO_MATCH
    assert DEFAULT_THRESHOLD == 85
    # per-tenant calibration
    assert decide(match_score=70, threshold=70) == POTENTIAL_MATCH


def _hit(score: float = 1.0) -> dict:
    return {"id": "Q7747", "caption": "Vladimir Putin", "score": score, "match": True,
            "datasets": ["us_ofac_sdn"]}


def test_prepare_record_attributes_and_stamps() -> None:
    rec = prepare_screening_record(
        top_hit=_hit(1.0),
        list_dataset="us_ofac_sdn",
        list_version="20260626181135-nfz",
        list_release_date="2026-06-26T18:11:35+00:00",
    )
    # attribution
    assert rec["matching_engine"] == "opensanctions"
    assert rec["list_of_record"] == "opensanctions"
    assert rec["list_source"] == "OFAC_SDN"
    assert rec["list_version"] == "20260626181135-nfz"
    assert isinstance(rec["list_release_date"], datetime)
    # scoring + decision
    assert rec["match_score"] == 100
    assert rec["scoring_rule_version"] == "opensanctions-v1"
    assert rec["decision"] == POTENTIAL_MATCH
    # raw is sacred — stored untouched
    assert rec["engine_raw_result"] == _hit(1.0)


def test_prepare_record_no_hit_is_no_match() -> None:
    rec = prepare_screening_record(
        top_hit=None,
        list_dataset="us_ofac_sdn",
        list_version="v1",
        list_release_date="2026-06-26T18:11:35+00:00",
    )
    assert rec["match_score"] == 0
    assert rec["decision"] == NO_MATCH
    assert rec["engine_raw_result"] == {"hits": []}


def test_prepare_record_refuses_unstamped_build() -> None:
    # No version or no release date = no defensible carimbo → refuse, never fake.
    with pytest.raises(ValueError):
        prepare_screening_record(top_hit=_hit(), list_dataset="us_ofac_sdn",
                                 list_version=None, list_release_date="2026-06-26T18:11:35+00:00")
    with pytest.raises(ValueError):
        prepare_screening_record(top_hit=_hit(), list_dataset="us_ofac_sdn",
                                 list_version="v1", list_release_date=None)


def test_prepare_record_unknown_dataset_raises() -> None:
    with pytest.raises(ValueError):
        prepare_screening_record(top_hit=_hit(), list_dataset="mystery_list",
                                 list_version="v1", list_release_date="2026-06-26T18:11:35+00:00")
