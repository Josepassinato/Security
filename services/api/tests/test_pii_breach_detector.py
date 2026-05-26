"""Tests for pii_breach_detector — heurística que aciona notificação ANPD.

A heurística é conservadora deliberadamente: prefere falso-positivo
(rascunho ANPD descartável) a falso-negativo (multa LGPD Art. 52 II).
Os testes lockam essa postura.
"""

from __future__ import annotations

import pytest

from app.services.pii_breach_detector import assess


def test_no_signals_returns_not_breach():
    a = assess(
        findings=[{"title": "Failed login", "description": "wrong password"}],
        severity="low",
        accounts_correlated=2,
        mitre_techniques=[],
    )
    assert not a.is_pii_breach
    assert a.signals == []


def test_cpf_in_finding_triggers_breach():
    a = assess(
        findings=[
            {"title": "Vazamento", "description": "CPF exposto em log público", "evidence": "log.json"}
        ],
        severity="low",
        accounts_correlated=1,
        mitre_techniques=[],
    )
    assert a.is_pii_breach
    assert "cpf" in a.categories_detected
    assert "pii_categories_in_findings" in a.signals


def test_high_severity_at_scale_triggers_even_without_pii_words():
    a = assess(
        findings=[{"title": "Bulk anomaly", "description": "abnormal volume on endpoint"}],
        severity="critical",
        accounts_correlated=500,
        mitre_techniques=[],
    )
    assert a.is_pii_breach
    assert "high_severity_at_scale" in a.signals


def test_exfil_technique_triggers_breach():
    a = assess(
        findings=[{"title": "x", "description": "y"}],
        severity="medium",
        accounts_correlated=3,
        mitre_techniques=["T1530"],
    )
    assert a.is_pii_breach
    assert any(s.startswith("exfil_technique") for s in a.signals)


def test_multiple_signals_accumulate():
    a = assess(
        findings=[
            {"title": "Pix fraudulento", "description": "chave pix vazada", "evidence": "raw cpf"},
        ],
        severity="high",
        accounts_correlated=200,
        mitre_techniques=["T1567", "T1078"],
    )
    assert a.is_pii_breach
    assert len(a.signals) >= 2
    assert {"cpf", "pix_key"}.issubset(set(a.categories_detected))


def test_to_jsonable_is_serializable():
    import json

    a = assess(
        findings=[{"title": "x", "description": "cpf"}],
        severity="high",
        accounts_correlated=100,
        mitre_techniques=["T1530"],
    )
    payload = a.to_jsonable()
    serialised = json.dumps(payload)
    parsed = json.loads(serialised)
    assert parsed["is_pii_breach"] is True
    assert "cpf" in parsed["categories_detected"]


def test_high_severity_below_threshold_does_not_trigger_scale_signal_alone():
    # Sob threshold default 50: severity high sozinho não dispara
    a = assess(
        findings=[{"title": "Anomaly", "description": "weird traffic"}],
        severity="high",
        accounts_correlated=10,
        mitre_techniques=[],
    )
    assert not a.is_pii_breach


def test_scale_threshold_is_inclusive():
    # exatamente 50 (default) deve disparar
    a = assess(
        findings=[{"title": "x", "description": "y"}],
        severity="critical",
        accounts_correlated=50,
        mitre_techniques=[],
    )
    assert "high_severity_at_scale" in a.signals
