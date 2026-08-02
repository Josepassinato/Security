# QUARRY — Technical & Agentic Assessment (12brain Quality Gate)
**Data:** 2026-06-19 · **URL:** https://quarry.12brain.org/ · **Modo:** READ-ONLY (sem alterar código, sem PR, sem deploy, sem install permanente) · **Versão:** 7.3.1 · **Repo:** `git@github.com:Josepassinato/Security.git` (branch `main`)

> **Veredito de uma linha:** Quarry é o **primeiro projeto da 12Brain que NÃO cabe no Quality Gate v1** — não por imaturidade, mas por **escala e natureza**: é uma plataforma agentic polyglot madura (AISOC) que **exige um Gate V2** com dimensão agentic + suporte multi-stack. Não force o v1.

---

## FASE 1 — Descoberta

| Item | Valor |
|---|---|
| **Caminho** | `/root/projetos/quarry` (15.117 arquivos rastreados) |
| **Git** | `Josepassinato/Security.git` · branch **main** · v7.3.1 |
| **Tipo** | **HÍBRIDO**: plataforma de agentes + workflow/SOAR engine + SaaS multi-tenant (AISOC — AI Security Operations Center) |
| **Frontend** | `apps/web` — **Next.js 16** + TS + SWR (pm2 `quarry-web`) |
| **Backend** | **Polyglot**: Python 3.11 (FastAPI) × ~10 serviços · Go 1.24/1.25 (ingest, enrichment, osquery-ext) · Node/TS (realtime) |
| **Monorepo** | pnpm 8.15 + Turbo · workspaces `apps/*` + `packages/*` (9 SDKs/libs) |
| **Bancos** | Postgres 16 (estado + RLS) · Neo4j 5 (knowledge graph) · ClickHouse (OLAP) · OpenSearch (Sigma/full-text) · **Qdrant (vetores/RAG)** · Redis (11 DBs por serviço) |
| **Filas** | **Kafka** (topics: `quarry.normalized_events`, `vulnerability.matches`, `security.graph_updates`, `quarry.alerts.fused`) + Zookeeper |
| **LLMs** | OpenAI (gpt-4o/mini default) · Anthropic Claude · Gemini · **local Ollama/vLLM/LiteLLM** (modo soberano/airgapped). BYOK por tenant (vault-encrypted) |
| **Agentes** | **LangGraph** StateGraph — pipeline `recon→forensic→responder→report_writer`; 4 agentes nomeados (Detect/Triage/Hunt/Respond) + memória institucional/sessão/working |
| **Workflows** | Playbook/SOAR engine (`http_request`, `notify`, `approval`, `condition`, osquery) com SSRF guard |
| **RAG/Vetores** | Qdrant (ATT&CK embeddings 3072-dim COSINE) + Anthropic Cybersec Skills Library; fallback heurístico |
| **Permissões** | JWT (OIDC/SAML SSO) + API keys (SHA-256, prefixo `aisoc_`) · RBAC 6 papéis (static + DB) · **multi-tenant via Postgres RLS** (`app.current_tenant_id`) |
| **Serviços externos** | 14+ feeds de threat-intel (VirusTotal, Mandiant, CrowdStrike, Shodan…) · STIX/TAXII/MISP/OTX · 50+ conectores SIEM/EDR/ITSM · S3 · Slack/Teams · MCP server |
| **Observabilidade** | OpenTelemetry (api+agents) · structlog JSON · Prometheus/Grafana · **audit log imutável hash-chained** · cost telemetry por execução LLM |

**Classificação:** **Plataforma de agentes / híbrido** (não é SaaS tradicional).

---

## FASE 2 — Diagnóstico técnico (read-only)

> Rodei só o que é barato e local (node_modules já presente). Build completo / pytest / go test / semgrep multi-serviço exigiriam Docker + installs pesados → **não executados** (restrição "não instalar"). Avaliados via CI existente + código.

| Check | Resultado | Fonte |
|---|---|---|
| **web type-check** (`tsc --noEmit`) | ✅ **0 erros** | executado |
| **web lint** (eslint) | ✅ **0 erros / 6 warnings** | executado |
| **pnpm audit** (monorepo node) | 🔴 **2 critical · 14 high · 42 moderate · 7 low** | executado |
| build (web/MCP) | não rodado (next 16; CI próprio faz) | CI `ci.yml` |
| Python lint/type (ruff+mypy) | configurado e no CI (`ruff check services/`) | `ruff.toml`, `ci.yml:150-166` |
| Testes | **246 arquivos**: 183 pytest + 47 vitest + 16 go | repo |
| CodeQL | ✅ ativo (`.github/workflows/codeql.yml`) | repo |
| **CI próprio** | ✅ **9 workflows** (web lint/tsc/vitest/build, MCP, Python ruff/mypy/pytest, compose-smoke, validate-detections/playbooks, graph-schema) | `.github/workflows/` |

**Score técnico preliminar (estilo-v1, só engenharia node):** alto — tsc limpo + lint limpo. **MAS** o `pnpm audit` (2 crit/14 high) **dispararia hard-block de `security_critical` no v1** → precisa triagem (provável dev/transitivo, a confirmar).

**Score técnico ajustado (maturidade global): ~85/100.** Penalizado pelas CVEs do audit; sustentado por CI robusto + 246 testes + tipos limpos.

---

## FASE 3 — Avaliação Agentic

Quarry **já implementa** a maioria dos controles que um Gate agentic exigiria. Classificação de risco:

| Vetor | Controle existente | Evidência | Risco |
|---|---|---|---|
| **Prompt injection** | Sanitizer 8-camadas (strip de `<|im_start|>`/`[INST]`/jailbreaks), wrapping `<UNTRUSTED_DATA>`, system-prompt instrui a tratar refs como não-confiáveis, cap 2k/campo, depth-6 | `services/agents/app/investigator/prompt_sanitizer.py` | 🟢 **BAIXO** |
| **Vazamento de contexto/tenant** | RLS por tenant + filtro `tenant_id`; **mas índices de vetor são globais** (isolamento só no query layer) | `llm_resolver.py:296`, AGENTS.md | 🟡 **MÉDIO** |
| **Tool misuse** | Tools = HTTP enrichment + RAG + IOC regex; **sem shell/exec/eval**; SSRF guard (bloqueia IMDS/privados) | `investigator/tools.py`, `playbook/ssrf_guard.py` | 🟢 **BAIXO** |
| **Runaway loops** | `max_iterations=10`, timeout por step clamp `[1,900]s`, rate-limit token-bucket no /explain | `models/state.py:89`, `playbook/bounds.py` | 🟢 **BAIXO** |
| **Permission escalation** | Guardrails 3-tier (auto/review/escalation) + steps de `approval` humano + RBAC | `policy/guardrails.py` | 🟡 **MÉDIO** |
| **Custo por execução** | Cost telemetry por call (`aisoc_run_costs`), dashboard por tenant; **porém SEM budget hard pré-bloqueante** (só pós-hoc) | `core/cost_telemetry.py` | 🟡 **MÉDIO** |
| **Observabilidade/tracing** | OTEL (api+agents), structlog, audit imutável hash-chained; **gaps**: realtime sem tracing, invocações de tool não-traçadas, aprovações de agente não no audit_log | `core/telemetry.py`, migr. 043 | 🟡 **MÉDIO** |

**Score agentic: ~78/100.** Postura **forte** (raro nesse nível); pontos a endurecer: isolamento de vetor por tenant, budget hard de tokens, tracing de tool + realtime, audit de decisões do agente.

---

## FASE 4 — Compatibilidade com o Quality Gate

| Pergunta | Resposta |
|---|---|
| **Usa o `12brain-quality-gate@v1` sem alterações?** | ❌ **NÃO.** v1 é **node-only**, assume um `package.json` na raiz e mede só build/lint/tsc/audit/semgrep de frontend. Em Quarry ele (a) só enxergaria `apps/web` (ignora ~70% Python/Go/Elixir), (b) quebraria no monorepo pnpm/turbo (mesmo gap do Toolsber), (c) **não tem nenhuma dimensão agentic** — justo o core-risk do projeto. |
| **Precisa de v1.1?** | Parcialmente necessário, **insuficiente.** v1.1 (input `working-directory` p/ monorepo) resolve só o problema estrutural do node — não cobre Python/Go nem agentes. |
| **Precisa de um Gate V2 para agentes?** | ✅ **SIM — Quarry é o caso que justifica o V2.** Exige: (1) adapters polyglot (Python ruff/mypy/pytest/pip-audit/bandit; Go vet/govulncheck; semgrep multi-lang), (2) **pilar Agentic novo** (prompt-injection defense presente? loop bounds? tool allowlist sem exec? cost cap? tenant isolation em vetores? agent audit/tracing?), (3) suporte a monorepo/multi-serviço. |
| **Esforço estimado** | **v1.1 (working-dir):** ~0,5–1 dia (já pendente do Toolsber). **Gate V2 MVP (Python + agentic, schema novo):** ~**2–4 semanas**. Atenuado porque **Quarry já tem os padrões** — o V2 pode usá-lo como *referência canônica* do que checar. |

---

## FASE 5 — Entregável (scores, blockers, riscos, recomendação)

### Scores
- **Score técnico:** ~**85/100** (CI robusto + 246 testes + tipos limpos; −audit 2crit/14high)
- **Score agentic:** ~**78/100** (defesas fortes; gaps de isolamento de vetor, cost cap, tracing de tool)
- **Maturidade:** **8/10** (plataforma v7.3.1 com CI, observabilidade, RLS, vault, airgap mode)

### 🔴 Blockers (para entrar no gate HOJE)
1. **Incompatibilidade estrutural com v1** — node-only vs polyglot monorepo (não roda de forma significativa).
2. **Ausência de dimensão agentic no v1** — o maior risco do projeto fica sem cobertura.
3. **pnpm audit: 2 critical + 14 high** — dispararia hard-block; exige triagem (prod vs dev/transitivo).

### 🟡 Warnings (não-bloqueantes)
- 6 warnings de lint no web · isolamento de vetor só no query-layer · sem budget hard de tokens · realtime sem tracing · OIDC id-token sem verificação de assinatura (comentado "use JWKS in prod") · dev-mode auth bypass (gated, mas perigoso se vazar p/ prod) · `/metrics` aberto se sem `METRICS_TOKEN` fora de prod.

### Riscos principais
- **Cost runaway** (sem cap pré-bloqueante) — observável mas não impedido.
- **Cross-tenant via RAG** (índices globais) — mitigado por filtro, mas sem isolamento físico.
- **Auth gaps de produção** (OIDC sig, OIDC state em memória, dev bypass) — baixos se config de prod correta; auditar antes de GA.

### Recomendação final
- **NÃO** plugar o v1 (nem v1.1) como gate de mérito do Quarry. Seria teatro de qualidade (mediria 30% do produto e zero do risco agentic).
- **Quarry = projeto-âncora do Gate V2.** Usar este assessment como **input de design** do V2 (ele já implementa o "estado da arte" que o V2 deve verificar nos outros projetos).
- **Curto prazo (sem novo gate):** Quarry **já tem CI superior** ao v1 — manter o CI próprio como fonte de verdade; só adicionar **pip-audit/bandit + govulncheck + triagem do pnpm audit** (jobs que faltam) e um **smoke agentic** (testes de prompt-injection já existem em `tests/`).

### Plano D1 específico (quando V2 existir)
1. **v1.1 primeiro** (input `working-directory`) — desbloqueia node de monorepo (compartilhado com Toolsber).
2. **Adapter Python** no gate: `ruff` + `mypy` + `pytest` + `pip-audit` + `bandit` por serviço (Quarry já tem ruff/mypy/pytest no CI → fácil mapear).
3. **Pilar Agentic V2** (schema NOVO, fora do contrato congelado do v1): checagens estáticas de — sanitizer de prompt presente · loop bounds (`max_iterations`/timeouts) · tool allowlist sem exec/shell · cost cap configurado · tenant isolation em retrieval · agent runs no audit/tracing.
4. **Baseline read-only** em CI próprio do Quarry (sem branch protection), comparar com este assessment.
5. **Backend Go/Elixir:** jobs `govulncheck`/`go vet` (fase posterior).

**Decisão executiva sugerida:** Quarry **não entra imediatamente** no ecossistema v1 — ele **define a necessidade do Gate V2** e deve ser o piloto/referência dele.
