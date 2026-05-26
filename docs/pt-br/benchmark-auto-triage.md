# Benchmark — Auto-Triage FP Reduction (FinPlay BR)

> Como o número de redução de falso-positivo publicado em `/br#benchmark` é
> medido, reproduzido e auditado. Documento canônico do CARD-013.

---

## Por que esse documento existe

O pitch comercial do Quarry citava ">80% de redução de falso-positivo" sem
benchmark. Em due diligence técnica de fintech, o número fura na primeira
pergunta. Este harness mede o número honesto, versionado por commit, contra
dataset com ground-truth embutido — e republicável a cada release do agente.

Quem precisa refazer:
- prospect cético que quer validar o claim antes de comprar
- equipe de InfoSec da fintech que quer rodar contra alertas próprios
- auditor independente conferindo afirmação comercial

---

## Resultado público vigente

| Estratégia | n | auto-close | falso-fech. | precisão | recall TP | p50 | p95 | custo USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline (regras estáticas) | 100 | 7.0% | 0.0% | 100.0% | 100.0% | 0 | 0 | $0.0000 |
| Quarry auto-triage (gpt-4o-mini) | 100 | **36.0%** | **0.0%** | 100.0% | 100.0% | 1800 | 2498 | $0.0094 |

- Run: `2026-05-26-bb5f7ccc`
- Dataset: FinPlay BR sintético, 100 alertas, distribuição 60/30/10
  (true_positive / false_positive / benign)
- Delta: **+29pp** auto-close (5.1× a baseline), zero erro de fechamento
- Custo: **~US$ 0,094 por mil alertas** processados

Onde o arquivo vive:
- `customizations/benchmarks/auto_triage_finplay/runs/2026-05-26-bb5f7ccc/summary.json`
- `customizations/benchmarks/auto_triage_finplay/runs/2026-05-26-bb5f7ccc/report.md`
- amostras: `alerts.jsonl`, `results_baseline.jsonl`, `results_llm.jsonl`

---

## Como reproduzir

### Pré-requisitos

1. **Dataset FinPlay** já gerado em
   `customizations/datasets/br-fintech-generator/output/` — se ausente, rodar
   `python generator.py` dentro daquele diretório.
2. **Chave OpenRouter de inferência** (não a provisioning). Salvar em
   `/root/.api_keys/openrouter-inference.env` no formato
   `OPENROUTER_API_KEY=sk-or-v1-...`, ou exportar como variável de ambiente.
   O harness lê o env primeiro, depois `/root/.api_keys/openrouter.env`.
3. Python 3.11+, dependências do harness: `httpx`, `numpy` (já instaladas no
   ambiente padrão do Quarry).

### Comandos

```bash
cd customizations/benchmarks/auto_triage_finplay

# Smoke barato (10 alertas, ~$0.001)
python3 run_benchmark.py --mode wet --size 10

# Run publicável (100 alertas, ~$0.01)
python3 run_benchmark.py --mode both --size 100

# Run estendido (500 alertas, ~$0.05)
python3 run_benchmark.py --mode both --size 500 --seed 20260524
```

Cada execução cria
`runs/YYYY-MM-DD-<sha>/{alerts,results_baseline,results_llm}.jsonl +
summary.json + report.md`. O `<sha>` é hash dos parâmetros do run — runs
idênticos colidem propositalmente.

### Modos

| Modo | O que roda | Custo | Quando usar |
|---|---|---|---|
| `mock` | baseline estática + LLM mock (resposta fixa) | $0 | dev, CI |
| `wet` | LLM real via OpenRouter | ~$0.01–0.05 | publicação |
| `both` | baseline + LLM real lado a lado | igual `wet` | comparativo |

---

## Métricas — definições

| Métrica | O que mede | Por que importa |
|---|---|---|
| `auto_close_rate` | % alertas que o agente fechou sem chegar ao humano | quanto trabalho economiza |
| `false_close_rate` | % auto-fechados que eram TPs | **erro perigoso** — não pode subir |
| `precision_close` | 1 − false_close_rate | quão seguro é deixar fechar |
| `recall_tp_escalation` | % dos TPs corretamente escalados | quantas ameaças reais chegam |
| `latency_p50_ms`, `latency_p95_ms` | tempo do alerta até verdict | UX e custo operacional |
| `cost_usd_total` | custo OpenRouter do run | unit economics defensáveis |

O par que importa é `auto_close_rate ↑` **e** `false_close_rate → 0`. Subir só
o primeiro é vandalizar o produto.

---

## Ground truth — como é gerado

O `synthesize_alerts.py` puxa cenários do FinPlay BR (Pix money mule, scraping
Open Finance, SIM swap, recurring payment FP, atualizações Windows assinadas,
etc), atribui label `true_positive` / `false_positive` / `benign` com `reason`
e mistura conforme distribuição parametrizável. Cada alerta carrega
`ground_truth` no JSONL — é o que o harness compara contra o `verdict` do
classificador.

Sample (truncado):
```json
{
  "alert_id": "alt-385589cc",
  "rule_id": "det-pix-001-money-mule-cashout",
  "severity": "critical",
  "summary": "Pix de R$ 3298.22 para conta laranja recém-criada",
  "ground_truth": "true_positive",
  "ground_truth_reason": "SCN-004-boleto-fraud-campaign"
}
```

Distribuição padrão: 60% TP, 30% FP, 10% benign. Ajustável via
`--ratio-tp/fp/benign`.

---

## Estabilidade e reproduzibilidade

- `--seed 20260524` é canônico — alerts.jsonl é byte-stable
- LLM com `temperature=0`, mas providers ainda variam (~1-2pp). Para número
  oficial publicado: rodar 3× e mediar
- `runs/` é versionado por hash dos parâmetros — runs idênticos sobrescrevem
- Para publicar: pinar `<sha>` no componente `BenchmarkBR.tsx` e citar em
  README

---

## Limitações honestas

1. **Dataset é sintético.** FinPlay reproduz distribuição plausível mas não
   reflete o mix real de cada fintech. Sempre dizer ao prospect: "rodamos
   contra os teus alertas dos últimos 30d em piloto e republicamos o número
   específico do teu ambiente".
2. **100 alertas é pouco.** Estável o suficiente pra detectar diferença de
   5pp+ mas não captura cauda longa. Run estendido (500) recomendado pra
   publicação anual.
3. **Provider drift.** O `gpt-4o-mini` evolui — número de hoje não vale pra
   sempre. Rodar antes de release e pinar versão exata do modelo no run.
4. **Auto-triage de produção usa `langchain-openai`**, este benchmark usa
   `httpx` direto. Prompts equivalentes, mas pequenas variações de
   formatação são possíveis. Quando o agente em produção mudar prompt, rodar
   benchmark de novo.
5. **Não cobre os outros agentes** (investigation, attack-path, enrichment).
   Fica para CARDs futuros — cada agente tem definição própria de "acerto".

---

## Como rodar contra dataset próprio (piloto)

1. Exportar alertas do tenant em formato JSONL com schema mínimo:
   ```
   {"alert_id":"...", "summary":"...", "severity":"...", "risk_score":0.42,
    "raw":{...}, "ground_truth":"true_positive|false_positive|benign",
    "ground_truth_reason":"..."}
   ```
2. Salvar em `customizations/benchmarks/auto_triage_finplay/runs/CUSTOM-<id>/alerts.jsonl`
3. Rodar:
   ```bash
   python3 run_benchmark.py --mode wet --alerts runs/CUSTOM-<id>/alerts.jsonl
   ```
4. O `ground_truth` precisa ser conhecido (alerts já triados manualmente). Se
   o tenant não tem ground truth: amostrar 100 alertas dos últimos 30d, fazer
   o operador rotular manualmente em planilha, importar — investimento de
   ~2h pra ter número honesto do ambiente.

---

## Curador (Regra 11)

Capability `auto-triage-fp-benchmark` foi catalogada como **gap real** quando
CARD-013 foi planejado. Quando este harness estabilizar (CI rodando weekly,
500-alert runs publicados), abrir entrada no
`/root/12brain-framework/engenharias/INDEX.md` sob domínio
"Multi-agent / Eval" — tag `eval-fp-reduction` 🟢.

---

## Mudanças

| Data | Run | Auto-close | Notas |
|---|---|---|---|
| 2026-05-24 | `f8f772cf` | 0% (LLM 401) | Run fracassado — chave provisioning. Inutilizável |
| 2026-05-26 | `bb5f7ccc` | 36% | **Primeiro run publicável**. Chave inference dedicada |
