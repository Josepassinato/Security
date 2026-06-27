"""Match-score derivation + decision rule — isolated, configurable, versioned.

The mother rule: the product does not invent a number, it records what the
engine said (``engine_raw_result``, untouched) and derives a 0–100 ``match_score``
by a RULE that is versioned. Because the raw is stored, changing the ruler later
re-derives historical scores without re-screening — and every decision stamps
the ``scoring_rule_version`` it was computed under, so we can always prove which
ruler produced a given score.

The derivation rule is a sanction parameter: it belongs to the BSA/compliance
owner, not engineering. Engineering only wires the versioned function. Adding a
new ruler = a new entry in ``_RULES`` + a new version string; never edit an
existing one (that would silently re-score sealed history under the same name).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

# decision values (mirror the screening_decisions CHECK constraint)
NO_MATCH = "NO_MATCH"
POTENTIAL_MATCH = "POTENTIAL_MATCH"

# Default review threshold (sanction parameter; per-tenant configurable, calibrated
# by the compliance owner — NOT by engineering).
DEFAULT_THRESHOLD = 85


def _opensanctions_v1(raw: Mapping[str, Any]) -> int:
    """OpenSanctions /match returns a 0..1 ``score``. Map linearly to 0..100."""
    score = raw.get("score")
    if score is None:
        return 0
    return max(0, min(100, round(float(score) * 100)))


# version string -> pure deriver(raw_hit) -> 0..100
_RULES: dict[str, Callable[[Mapping[str, Any]], int]] = {
    "opensanctions-v1": _opensanctions_v1,
}


def derive_match_score(*, raw: Mapping[str, Any], rule_version: str) -> int:
    """Derive the 0–100 match_score from an engine hit under a named ruler."""
    try:
        rule = _RULES[rule_version]
    except KeyError as exc:
        raise ValueError(f"unknown scoring_rule_version {rule_version!r}; known: {sorted(_RULES)}") from exc
    return rule(raw)


def decide(*, match_score: int, threshold: int = DEFAULT_THRESHOLD) -> str:
    """Automatic decision from the score. At/above threshold a human must review
    (POTENTIAL_MATCH) — the engine never auto-confirms a TRUE_MATCH; that, and
    ESCALATED, come from human review downstream."""
    return POTENTIAL_MATCH if match_score >= threshold else NO_MATCH


__all__ = ["derive_match_score", "decide", "DEFAULT_THRESHOLD", "NO_MATCH", "POTENTIAL_MATCH"]
