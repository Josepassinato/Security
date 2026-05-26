# Benchmark — Auto-Triage FP Reduction (FinPlay BR)

**Run:** `2026-05-26 00:26:32` (sha `bb5f7ccc`)
**Dataset:** FinPlay BR synthetic (100 alertas)
**Metodologia:** ver `docs/pt-br/benchmark-auto-triage.md`

## Distribuição de ground-truth

| Ground truth | Count |
|---|---|
| true_positive | 60 |
| false_positive | 30 |
| benign | 10 |

## Resultados por estratégia

| Estratégia | Auto-close | False-close | Precisão | Recall TP esc. | p50 ms | p95 ms | USD |
|---|---|---|---|---|---|---|---|
| baseline_static | 7.0% | 0.0% | 100.0% | 100.0% | 0 | 0 | $0.0000 |
| llm_auto_triage:openai/gpt-4o-mini | 36.0% | 0.0% | 100.0% | 100.0% | 1800 | 2498 | $0.0094 |

## Definições

- **Auto-close rate** — % alertas que o agente fechou sem chegar ao humano.
- **False-close rate** — % auto-fechados que eram TPs (erros perigosos).
- **Precisão (close)** — 1 - false_close_rate. Quão seguro é deixar fechar.
- **Recall TP escalation** — % TPs que foram corretamente escalados ao humano.
- **Latência p50/p95** — tempo de classificação por alerta.

## Comparativo

- LLM auto-close vs baseline: +29.0pp
- LLM false-close vs baseline: +0.0pp (melhor segurança operacional)

---

_Gerado pelo Quarry CARD-013 Auto-Triage Benchmark — reproduzível com `--seed 20260524`._