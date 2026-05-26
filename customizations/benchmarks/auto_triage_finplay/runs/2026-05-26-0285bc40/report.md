# Benchmark — Auto-Triage FP Reduction (FinPlay BR)

**Run:** `2026-05-26 00:25:18` (sha `0285bc40`)
**Dataset:** FinPlay BR synthetic (10 alertas)
**Metodologia:** ver `docs/pt-br/benchmark-auto-triage.md`

## Distribuição de ground-truth

| Ground truth | Count |
|---|---|
| true_positive | 6 |
| false_positive | 3 |
| benign | 1 |

## Resultados por estratégia

| Estratégia | Auto-close | False-close | Precisão | Recall TP esc. | p50 ms | p95 ms | USD |
|---|---|---|---|---|---|---|---|
| llm_auto_triage:openai/gpt-4o-mini | 0.0% | 0.0% | 100.0% | 100.0% | 11 | 48 | $0.0000 |

## Definições

- **Auto-close rate** — % alertas que o agente fechou sem chegar ao humano.
- **False-close rate** — % auto-fechados que eram TPs (erros perigosos).
- **Precisão (close)** — 1 - false_close_rate. Quão seguro é deixar fechar.
- **Recall TP escalation** — % TPs que foram corretamente escalados ao humano.
- **Latência p50/p95** — tempo de classificação por alerta.

## Comparativo

_(rode com `--mode both` para comparativo)_

---

_Gerado pelo Quarry CARD-013 Auto-Triage Benchmark — reproduzível com `--seed 20260524`._