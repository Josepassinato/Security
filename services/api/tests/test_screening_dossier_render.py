"""Tests for the F4 sandboxed dossier renderer motor.

Locks the contract the AML dossier depends on:

1. The real per-case template renders §1/§2/§6 from a screening_decisions row.
2. The list-version "carimbo" (§2) and the chain hashes (§6) appear verbatim —
   they are the product's spine.
3. Name-only screening (no document) renders the explicit fallback, not a blank.
4. autoescape neutralises hostile counterparty data (no HTML injection into PDF).
5. The sandbox blocks SSTI — a template probing dunder internals is refused.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from app.evidence_pack.narrative import (
    render_dossier_pdf,
    render_narrative,
    render_screening_case_dossier,
)
from app.evidence_pack.renderer import WeasyPrintUnavailableError
from jinja2.exceptions import SecurityError

_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "app/evidence_pack/dossier_templates/aml-screening-case-dossier-v1.html.j2"


def _template() -> str:
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


def _decision(**overrides: Any) -> dict[str, Any]:
    base = {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "case_id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "counterparty_name": "Joao da Silva",
        "counterparty_id": "12345678901",
        "counterparty_id_type": "CPF",
        "counterparty_jurisdiction": "BR",
        "screening_trigger": "onboarding",
        "matching_engine": "complyadvantage",
        "list_of_record": "opensanctions",
        "list_source": "OFAC_SDN",
        "list_dataset": "us_ofac_sdn",
        "list_version": "20260626181135-nfz",
        "list_release_date": datetime(2026, 6, 26, 18, 11, 35, tzinfo=UTC),
        "match_score": 0,
        "scoring_rule_version": "opensanctions-v1",
        "engine_raw_result": {"hits": []},
        "decision": "NO_MATCH",
        "disposition": "PENDING",
        "human_reviewer": None,
        "rationale": "",
        "screened_at": datetime(2026, 6, 26, 14, 0, 0, tzinfo=UTC),
        "prev_hash": "a" * 64,
        "entry_hash": "b" * 64,
    }
    base.update(overrides)
    return base


def _render(**overrides: Any) -> str:
    return render_screening_case_dossier(
        decision=_decision(**overrides),
        template_str=_template(),
        tenant_name="Optimus Fintech S.A.",
        verification_method="GET /api/v1/screening/{id}/verify-chain",
    )


def test_template_file_exists() -> None:
    assert _TEMPLATE_PATH.is_file(), f"missing template: {_TEMPLATE_PATH}"


def test_renders_solid_sections() -> None:
    html = _render()
    # §1 identity
    assert "Joao da Silva" in html
    assert "12345678901" in html
    assert "Optimus Fintech S.A." in html
    # §2 the version carimbo — the product's spine
    assert "20260626181135-nfz" in html
    assert "us_ofac_sdn" in html
    # §6 chain integrity
    assert "b" * 64 in html  # entry_hash
    assert "a" * 64 in html  # prev_hash


def test_renders_matching_disposition_ownership() -> None:
    """§3/§4/§5 now render from real ledger data (no placeholders)."""
    html = _render()
    assert "PENDENTE" not in html
    # §3 matching — from real fields
    assert "Resultado do Matching" in html
    assert "NO_MATCH" in html
    assert "opensanctions-v1" in html
    # §4 disposition — automated path (no human reviewer)
    assert "Disposição Humana" in html
    assert "Decisão automática" in html
    # §5 ownership — honest limit (OFAC 50% rule not evaluated in scope)
    assert "50% da OFAC" in html


def test_human_review_renders_reviewer_and_rationale() -> None:
    html = _render(
        decision="POTENTIAL_MATCH",
        disposition="CLEARED_FALSE_POSITIVE",
        human_reviewer="bsa@optimus.com",
        rationale="weak alias, distinct DOB",
    )
    assert "bsa@optimus.com" in html
    assert "weak alias, distinct DOB" in html


def test_name_only_screening_renders_fallback() -> None:
    html = _render(counterparty_id=None)
    assert "Screening por nome" in html


def test_autoescape_neutralises_hostile_counterparty_name() -> None:
    html = _render(counterparty_name="<script>alert('x')</script>")
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_sandbox_blocks_ssti() -> None:
    with pytest.raises(SecurityError):
        render_narrative("{{ ().__class__.__bases__ }}", {})


def test_pdf_render_optional_stack() -> None:
    """PDF is best-effort: returns a PDF byte stream, or raises the documented
    WeasyPrintUnavailableError when the native stack is absent."""
    try:
        pdf = render_dossier_pdf(_render())
    except WeasyPrintUnavailableError:
        pytest.skip("WeasyPrint native stack unavailable in this environment")
    assert pdf[:4] == b"%PDF"
