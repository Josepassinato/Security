"""Screening intake — engine result → attributed ledger record (Phase 2).

Ponta-a-ponta: a counterparty name is screened against the OpenSanctions
source-of-record, the dataset build is stamped, the score is derived under a
versioned ruler, and the decision is written to the immutable ledger
**attributed to the engine** (matching_engine + list_of_record + version).

``prepare_screening_record`` is PURE (engine hit + version stamp in → ledger
fields out) so the attribution + scoring + decision logic is unit-tested without
network or DB. ``screen_and_record`` is the thin orchestration that calls the
client and the append-only writer.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.screening.opensanctions_client import OpenSanctionsClient
from app.screening.scoring import DEFAULT_THRESHOLD, decide, derive_match_score
from app.services.screening_ledger import record_screening_decision

# OpenSanctions dataset name -> our list_source enum (screening_decisions CHECK).
_DATASET_TO_SOURCE = {
    "us_ofac_sdn": "OFAC_SDN",
    "us_ofac_cons": "OFAC_CONSOLIDATED",
}

_LIST_OF_RECORD = "opensanctions"
_MATCHING_ENGINE = "opensanctions"


def _parse_release(release: str | None) -> datetime:
    if not release:
        # No release date = no defensible stamp; refuse rather than fake one.
        raise ValueError("OpenSanctions returned no dataset release date — cannot stamp the build")
    return datetime.fromisoformat(release)


def prepare_screening_record(
    *,
    top_hit: dict[str, Any] | None,
    list_dataset: str,
    list_version: str | None,
    list_release_date: str | None,
    threshold: int = DEFAULT_THRESHOLD,
    scoring_rule_version: str = "opensanctions-v1",
) -> dict[str, Any]:
    """Build the engine-derived ledger fields (PURE) from one screening run."""
    if not list_version:
        raise ValueError("OpenSanctions returned no dataset version — cannot stamp the build")
    list_source = _DATASET_TO_SOURCE.get(list_dataset)
    if list_source is None:
        raise ValueError(f"no list_source mapping for dataset {list_dataset!r}")

    if top_hit is None:
        match_score = 0
        engine_raw_result: dict[str, Any] = {"hits": []}
    else:
        match_score = derive_match_score(raw=top_hit, rule_version=scoring_rule_version)
        engine_raw_result = top_hit  # sacred: stored untouched

    return {
        "matching_engine": _MATCHING_ENGINE,
        "list_of_record": _LIST_OF_RECORD,
        "list_source": list_source,
        "list_dataset": list_dataset,
        "list_version": list_version,
        "list_release_date": _parse_release(list_release_date),
        "engine_raw_result": engine_raw_result,
        "match_score": match_score,
        "scoring_rule_version": scoring_rule_version,
        "decision": decide(match_score=match_score, threshold=threshold),
    }


async def screen_and_record(
    db: Any,
    client: OpenSanctionsClient,
    *,
    tenant_id: Any,
    counterparty_name: str,
    counterparty_normalized: str,
    counterparty_id_type: str,
    counterparty_id: str | None = None,
    counterparty_jurisdiction: str | None = None,
    screening_trigger: str | None = None,
    case_id: Any = None,
    list_dataset: str = "us_ofac_sdn",
    threshold: int = DEFAULT_THRESHOLD,
    scoring_rule_version: str = "opensanctions-v1",
) -> Any:
    """Screen a counterparty and append an attributed, immutable ledger record."""
    hits = await client.match(counterparty_name, scope=list_dataset)
    version, release = await client.dataset_version(list_dataset)
    fields = prepare_screening_record(
        top_hit=hits[0] if hits else None,
        list_dataset=list_dataset,
        list_version=version,
        list_release_date=release,
        threshold=threshold,
        scoring_rule_version=scoring_rule_version,
    )
    return await record_screening_decision(
        db,
        tenant_id=tenant_id,
        counterparty_name=counterparty_name,
        counterparty_normalized=counterparty_normalized,
        counterparty_id=counterparty_id,
        counterparty_id_type=counterparty_id_type,
        counterparty_jurisdiction=counterparty_jurisdiction,
        screening_trigger=screening_trigger,
        case_id=case_id,
        screened_at=datetime.now(UTC),
        disposition="PENDING",
        **fields,
    )


__all__ = ["prepare_screening_record", "screen_and_record"]
