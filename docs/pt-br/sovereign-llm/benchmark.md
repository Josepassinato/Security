# Sovereign LLM — Benchmark

> **Status:** metodologia publicada · números reais pendentes
> **Última revisão:** 2026-05-26
> **Owner:** Quarry / 12Brain
>
> Este documento expõe a metodologia do benchmark da Quarry para as
> três modalidades de deployment (A — Mac Mini, B — VPS Llama, C — BYOK
> cloud). Conforme [`AGENTS.md`](../../../AGENTS.md), **as tabelas
> abaixo distinguem explicitamente o que foi medido do que ainda é
> estimativa de hardware/spec**. Nenhuma célula marcada como real
> contém número fabricado.

---

## 1. O que medimos

10 prompts representativos da carga de produção do Quarry, executados
três vezes contra cada combinação **(modalidade × modelo × hardware)**.
O suite vive em [`scripts/sovereign_benchmark.py`](../../../scripts/sovereign_benchmark.py)
e cobre:

| ID | Cenário | Razão |
|---|---|---|
| `phishing-triage` | Triagem de e-mail suspeito | Carga de fan-out — `services/agents/router_phishing` |
| `lateral-movement` | Telemetria de endpoint | Carga LangGraph — `services/agents/router_identity` |
| `pix-fraud` | Burst Pix-OUT | Carga regulatória — Bacen Res. 85/2021 PSC |
| `iam-anomaly` | AssumeRole anômalo | Carga cloud — AWS CloudTrail |
| `rfe-triggers` | Exfil massiva PII | Carga ANPD (24h) |
| `supply-chain` | Dep maliciosa CI/CD | Carga DevSecOps |
| `cloud-misconfig` | Bucket público | Carga posture |
| `open-finance` | Webhook abusivo | Carga Open Finance |
| `insider` | Vazamento pré-demissão | Carga insider-risk |
| `kyc-bypass` | Onboarding express | Carga antifraude SCD |

## 2. O que registramos por amostra

- `latency_ms` — wall-clock entre `POST /v1/chat/completions` e `200 OK`
- `prompt_tokens` / `completion_tokens` — do bloco `usage` da resposta
- `runtime` — auto-detectado (`ollama` / `vllm` / `openai` / `anthropic`)
- `error` — texto curto se a amostra falhou

E agregamos:

- Latência p50, p95, min, max, média (apenas amostras com `ok=true`)
- Tokens/s — mediana e média (completion ÷ latência por amostra)
- Tokens totais (prompt + completion)
- Contagem `n_attempted` vs `n_succeeded`

Falhas são **listadas, não diluídas** — amostras quebradas não entram
no agregado.

## 3. Hardware de referência

**Provedor canônico Modalidade B: Hostinger BR São Paulo** (dado no território
nacional, BRL nativo, sem cláusulas SCC/DPA LGPD). Hetzner DE entra como
alternativa offshore onde GPU dedicada é requisito (tier Pro).

| Modalidade | Tier | Hardware canônico (BR) | Alternativa (offshore) | Custo BRL/mês |
|---|---|---|---|---|
| A (Mac Mini) | único | Apple M4 Pro, 14-core CPU, 20-core GPU, 64 GB | — | one-time R$ 18.000 + eletricidade |
| B (VPS) | Light | Hostinger KVM 4 (4 vCPU, 16 GB, NVMe, SP) | — | ~R$ 95 |
| B (VPS) | Standard | Hostinger KVM 8 (8 vCPU, 32 GB, NVMe, SP) | Hetzner AX42 (DE — bare metal Ryzen 7 PRO 64 GB DDR5) | ~R$ 240 (BR) · ~R$ 800 (DE) |
| B (VPS) | Pro | Locaweb GPU / Magalu Cloud Compute / Oracle Cloud BR A10 *(em avaliação)* | Hetzner GEX130 (DE — Ryzen 9 + RTX 4000 SFF Ada 20 GB) | ~R$ 2.500–3.500 |
| C (cloud BYOK) | n/a | n/a | n/a | pay-per-use direto ao provedor |

## 4. Modelos avaliados

| Sigla | Provedor | Tamanho | Usado em |
|---|---|---|---|
| `qwen2.5-14b-q4` | open-source (Qwen) | 14B parâmetros, Q4_K_M | B-Standard, A |
| `llama3.1-8b-q4` | open-source (Meta) | 8B parâmetros, Q4_K_M | B-Light, A fallback |
| `llama3.3-70b-q4` | open-source (Meta) | 70B parâmetros, Q4_K_M | B-Pro, vLLM |
| `gpt-4o-mini` | OpenAI | proprietário | C (referência) |
| `claude-3-5-haiku` | Anthropic | proprietário | C (referência) |

## 5. Resultados — status

> **Todas as células abaixo são `pending` até que rodemos o benchmark
> contra hardware real e publiquemos os JSONs em `artifacts/benchmark/`.**
> Nada nesta seção foi medido ainda. A spec de hardware acima vem
> da [CARD-015](./CARD-015-mac-mini-sovereign-appliance.md) e a
> de modelo vem dos benchmarks públicos publicados por Qwen / Meta /
> OpenAI / Anthropic — **não da nossa medição local**.

### 5.1 Latência p50 (segundos)

| Modelo \\ Modalidade | A (Mac Mini) | B-Light | B-Standard | B-Pro | C (cloud) |
|---|---|---|---|---|---|
| qwen2.5-14b-q4    | pending | pending | pending | — | — |
| llama3.1-8b-q4    | pending | pending | — | — | — |
| llama3.3-70b-q4   | — | — | — | pending | — |
| gpt-4o-mini       | — | — | — | — | pending |
| claude-3-5-haiku  | — | — | — | — | pending |

### 5.2 Throughput (tokens/s)

| Modelo \\ Modalidade | A | B-Light | B-Standard | B-Pro | C |
|---|---|---|---|---|---|
| qwen2.5-14b-q4    | pending | pending | pending | — | — |
| llama3.1-8b-q4    | pending | pending | — | — | — |
| llama3.3-70b-q4   | — | — | — | pending | — |
| gpt-4o-mini       | — | — | — | — | pending |
| claude-3-5-haiku  | — | — | — | — | pending |

### 5.3 Custo por 10 prompts

| Modalidade | Custo amortizado | Razão |
|---|---|---|
| A (Mac Mini) | R$ 0,06 amortizado | CAPEX ÷ 36 meses ÷ alertas/mês — **estimativa contábil, não medida** |
| B-Standard | R$ 0,003 | OPEX VPS ÷ throughput — **estimativa hardware** |
| B-Pro | R$ 0,013 | OPEX VPS ÷ throughput — **estimativa hardware** |
| C (gpt-4o-mini) | pending | uso real do tarifário OpenAI vigente |
| C (claude-3-5-haiku) | pending | uso real do tarifário Anthropic vigente |

## 6. Como reproduzir

```bash
# Modalidade B — VPS dedicada
python3 scripts/sovereign_benchmark.py \\
  --target sovereign-vps \\
  --base-url http://10.99.0.1:11434/v1 \\
  --model qwen2.5:14b-instruct-q4_K_M \\
  --output artifacts/benchmark/$(date +%Y%m%d)-vps-standard.json

# Modalidade C — OpenAI referência
python3 scripts/sovereign_benchmark.py \\
  --target cloud-byok \\
  --base-url https://api.openai.com/v1 \\
  --model gpt-4o-mini \\
  --api-key "$OPENAI_API_KEY" \\
  --output artifacts/benchmark/$(date +%Y%m%d)-openai.json

# Agregação cross-runs (geração da tabela acima)
python3 scripts/render_eval_charts.py \\
  --benchmark artifacts/benchmark/ \\
  --out docs/pt-br/sovereign-llm/benchmark-results-$(date +%Y%m%d).md
```

## 7. Anti-fabricação — regra inviolável

A célula desta tabela **só sai de `pending`** quando:

1. O JSON correspondente está commitado em `artifacts/benchmark/`
2. O JSON tem `n_succeeded ≥ 8/10` (taxa mínima)
3. O hardware está documentado por linha (CPU, RAM, disk, modelo de GPU se houver)
4. O run foi gravado por ≥ 2 pessoas independentes OU em CI com hash do hardware

Conforme [`AGENTS.md`](../../../AGENTS.md) seção *Learned User Preferences*:
*"Benchmark data and documentation must be transparent about what is
synthetic vs. real; never present fabricated metrics as actual
measured performance."*

## 8. Próximos passos

- [ ] Provisionar Hetzner AX42 (D3 — aguardando autorização R$ 800/mês)
- [ ] Rodar `sovereign_benchmark.py --target sovereign-vps` no Standard tier
- [ ] Rodar contra OpenAI gpt-4o-mini e Anthropic claude-3-5-haiku para a coluna C
- [ ] Adquirir Mac Mini M4 Pro (D1 — aguardando R$ 18k CAPEX) e rodar Modalidade A
- [ ] Publicar primeira tabela completa em `benchmark-results-YYYYMMDD.md`
- [ ] Atualizar `apps/web/src/components/landing/br/SovereignLlmBR.tsx` com link pro resultado
