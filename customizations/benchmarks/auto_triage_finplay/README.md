# Auto-Triage FP Reduction Benchmark — FinPlay BR

> Mede honestamente o **auto-close rate** e **false-close rate** do
> `auto_triage_agent` contra um sample sintético de 100 alertas extraídos
> do dataset FinPlay BR (fintech regulada BR), com ground-truth embutido.

---

## Por que isso existe

O pitch comercial do Quarry cita "redução de falso-positivo" como argumento
contra SOC tradicional. Sem benchmark interno reproduzível, esse número vira
hype que fura em due diligence técnica. Este harness mede o número honesto,
versionado, e republicável a cada release do agente.

---

## Como rodar

### Pré-requisitos
1. Dataset FinPlay gerado em `customizations/datasets/br-fintech-generator/output/`
   (rodar `python generator.py` lá se ausente)
2. Para modo `wet`: chave OpenRouter em `/root/.api_keys/openrouter.env`
   (OPENROUTER_API_KEY=...) ou env var.

### Modo mock (zero custo, só baseline estática)
```bash
cd customizations/benchmarks/auto_triage_finplay
python3 run_benchmark.py --mode mock --size 100
```

### Modo wet (chama LLM via OpenRouter, ~$0.10 para 100 alertas)
```bash
python3 run_benchmark.py --mode wet --size 100
```

### Modo both (comparativo lado a lado)
```bash
python3 run_benchmark.py --mode both --size 100
```

### Smoke (10 alertas, ~$0.01)
```bash
python3 run_benchmark.py --mode wet --size 10
```

---

## Saída

`runs/YYYY-MM-DD-<sha>/`
- `alerts.jsonl` — sample sintetizado (com ground-truth)
- `results_baseline.jsonl` — output da baseline estática
- `results_llm.jsonl` — output do LLM auto-triage (modo wet)
- `summary.json` — métricas agregadas por estratégia
- `report.md` — relatório markdown publicável

---

## Métricas

| Métrica | O que significa |
|---|---|
| `auto_close_rate` | % alertas auto-fechados pelo agente |
| `false_close_rate` | % auto-fechados que eram TPs (**erro perigoso**) |
| `precision_close` | 1 − false_close_rate. Quão seguro é deixar fechar |
| `recall_tp_escalation` | % dos TPs que foram corretamente escalados ao humano |
| `latency_p50_ms` / `p95_ms` | tempo de classificação |
| `cost_usd_total` | custo OpenRouter da rodada |

---

## Reproduzibilidade

- `--seed 20260524` é canônico — runs são byte-stable.
- Modelo padrão: `openai/gpt-4o-mini` (configurável via `--model`).
- Resultado vai em `runs/` versionado por commit-sha do código + run-sha.
- Quando publicado em `/br#benchmark`, citar arquivo `summary.json`
  específico do run.

---

## Limitações honestas

- Dataset é **sintético** (FinPlay), não reflete distribuição real de fintech
  produção. Convidar prospect a rodar contra dataset próprio em piloto.
- Sample de 100 alertas é estável mas baixo — incrementar para 500 quando
  necessário (custo wet ~$0.50).
- LLM é não-determinístico mesmo com `temperature=0` (pequenas variações
  toleradas). Rodar 3× e mediar antes de publicar número final.
- Auto-triage agente do Quarry usa `langchain-openai`; este benchmark usa
  `httpx` direto para OpenRouter (evita instalar deps pesadas). O prompt
  é equivalente, mas implementações têm pequenas diferenças.

---

## Curador (Regra 11 step 0)

Capability `auto-triage-fp-benchmark` é **gap real do framework 12Brain**.
Quando este benchmark estabilizar, propor entrada em
`/root/12brain-framework/engenharias/INDEX.md` sob domínio
"Multi-agent / Eval" com tag `eval-fp-reduction` 🟢.
