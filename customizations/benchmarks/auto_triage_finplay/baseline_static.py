#!/usr/bin/env python3
"""Baseline estática (regra keyword + score) para comparar com auto-triage LLM.

Esta baseline representa o que um SIEM legado tradicional faz: classifica
alertas com base em regras determinísticas pré-definidas, sem reasoning
contextual. É proposital simples — quem perde ou ganha pra ela diz muito
sobre o ganho real do auto-triage agêntico.

Regras:
  1. Se severity in {critical, high} AND risk_score >= 0.70 → true_positive
  2. Senão, se severity == info → benign
  3. Senão → false_positive (auto-close conservador da baseline)
"""
from __future__ import annotations

import time
from typing import Any


AUTO_CLOSE_THRESHOLD = 0.85


def classify_static(alert: dict[str, Any]) -> dict[str, Any]:
    """Apply the static baseline rule and return a verdict dict."""
    t0 = time.monotonic()
    severity = (alert.get("severity") or "").lower()
    risk = float(alert.get("risk_score") or 0.0)

    if severity in {"critical", "high"} and risk >= 0.70:
        verdict = "true_positive"
        confidence = 0.95
        rationale = "Regra: severity ∈ {critical, high} e risk_score >= 0.70."
    elif severity == "info":
        verdict = "benign"
        confidence = 0.90
        rationale = "Regra: severity == info."
    else:
        verdict = "false_positive"
        confidence = 0.70
        rationale = "Regra: outros casos vão para revisão como FP."

    auto_closed = verdict in {"false_positive", "benign"} and confidence >= AUTO_CLOSE_THRESHOLD
    elapsed_ms = (time.monotonic() - t0) * 1000
    return {
        "verdict": verdict,
        "confidence": confidence,
        "rationale": rationale,
        "auto_closed": auto_closed,
        "latency_ms": elapsed_ms,
        "cost_usd": 0.0,
    }
