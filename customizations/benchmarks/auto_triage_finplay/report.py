#!/usr/bin/env python3
"""Renderiza o report.md do benchmark de auto-triage FP."""
from __future__ import annotations

import datetime as dt
from typing import Any


def render_report(
    summaries: list[dict[str, Any]],
    alerts: list[Any],
    timestamp: dt.datetime,
    run_sha: str,
) -> str:
    by_gt: dict[str, int] = {}
    for a in alerts:
        by_gt[a.ground_truth] = by_gt.get(a.ground_truth, 0) + 1

    lines: list[str] = []
    lines.append("# Benchmark — Auto-Triage FP Reduction (FinPlay BR)")
    lines.append("")
    lines.append(f"**Run:** `{timestamp:%Y-%m-%d %H:%M:%S}` (sha `{run_sha}`)")
    lines.append(f"**Dataset:** FinPlay BR synthetic ({len(alerts)} alertas)")
    lines.append("**Metodologia:** ver `docs/pt-br/benchmark-auto-triage.md`")
    lines.append("")
    lines.append("## Distribuição de ground-truth")
    lines.append("")
    lines.append("| Ground truth | Count |")
    lines.append("|---|---|")
    for k in ("true_positive", "false_positive", "benign"):
        lines.append(f"| {k} | {by_gt.get(k, 0)} |")
    lines.append("")
    lines.append("## Resultados por estratégia")
    lines.append("")
    lines.append("| Estratégia | Auto-close | False-close | Precisão | Recall TP esc. | p50 ms | p95 ms | USD |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for s in summaries:
        lines.append(
            f"| {s['strategy']} | "
            f"{s['auto_close_rate']*100:.1f}% | "
            f"{s['false_close_rate']*100:.1f}% | "
            f"{s['precision_close']*100:.1f}% | "
            f"{s['recall_tp_escalation']*100:.1f}% | "
            f"{s['latency_p50_ms']:.0f} | "
            f"{s['latency_p95_ms']:.0f} | "
            f"${s['cost_usd_total']:.4f} |"
        )
    lines.append("")
    lines.append("## Definições")
    lines.append("")
    lines.append("- **Auto-close rate** — % alertas que o agente fechou sem chegar ao humano.")
    lines.append("- **False-close rate** — % auto-fechados que eram TPs (erros perigosos).")
    lines.append("- **Precisão (close)** — 1 - false_close_rate. Quão seguro é deixar fechar.")
    lines.append("- **Recall TP escalation** — % TPs que foram corretamente escalados ao humano.")
    lines.append("- **Latência p50/p95** — tempo de classificação por alerta.")
    lines.append("")
    lines.append("## Comparativo")
    lines.append("")
    if len(summaries) >= 2:
        baseline = next((s for s in summaries if s["strategy"] == "baseline_static"), None)
        llm = next((s for s in summaries if s["strategy"].startswith("llm_")), None)
        if baseline and llm:
            delta_close = llm["auto_close_rate"] - baseline["auto_close_rate"]
            delta_fc = llm["false_close_rate"] - baseline["false_close_rate"]
            lines.append(
                f"- LLM auto-close vs baseline: "
                f"{'+' if delta_close >= 0 else ''}{delta_close*100:.1f}pp"
            )
            lines.append(
                f"- LLM false-close vs baseline: "
                f"{'+' if delta_fc >= 0 else ''}{delta_fc*100:.1f}pp "
                f"({'pior' if delta_fc > 0 else 'melhor'} segurança operacional)"
            )
    else:
        lines.append("_(rode com `--mode both` para comparativo)_")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_Gerado pelo Quarry CARD-013 Auto-Triage Benchmark — reproduzível com `--seed 20260524`._")
    return "\n".join(lines)
