# Orchestrator Deep-Dive — `services/agents/`

**Card:** CARD-005
**Data:** 2026-05-15
**Status do orchestrator analisado:** commit `cfb83e92` (post-rebrand)
**Audiência:** equipe Quarry preparando customização vertical fintech BR

> Esta análise foi conduzida em **leitura estática** sobre `services/agents/`. Nenhum código foi modificado. Decisão de customização em [ADR-004](../adrs/ADR-004-orchestrator-fintech-br.md).

---

## 1. Visão geral

O serviço `agents` é um runtime LangGraph em Python (FastAPI) que orquestra agentes LLM para investigação de alertas de segurança. Dois pipelines coexistem:

| Pipeline | Arquivo | Topology | Status |
|---|---|---|---|
| **Investigator (v6, legado)** | `app/investigator/orchestrator.py` (407 linhas) | `START → recon → forensic → responder → report_writer → END` | Estável, em produção upstream |
| **Router (T2.2, v8.0)** | `app/orchestrator/router.py` (516 linhas) | `START → auto_triage → classify → fan_out → join → responder → END` | Ativo por padrão via flag `QUARRY_AGENT_PARALLEL_TOPOLOGY=1` |

O Router é o caminho **moderno**: leva alertas pelo auto-triage (TP/FP/benign), classifica sinais (phishing, identity, cloud, insider), executa 4 sub-agentes em paralelo via `asyncio.gather`, faz join e responde com um plano (dry-run).

O Investigator v6 fica como **fallback** orthogonal — invocado por endpoints específicos, não pelo router. Mantemos ambos.

---

## 2. Grafo LangGraph

```
PARALLEL MODE (default, QUARRY_AGENT_PARALLEL_TOPOLOGY=1)

    START
      │
      ▼
  auto_triage   ───►  TP / FP / benign
      │
   guard: status?
      ├── completed/failed → responder (dry-run) → END
      └── continue ▼
      classify_signals()       ◄── keyword bags
            │
   ┌────────┼────────┐────────────┐
   ▼        ▼        ▼            ▼
phishing identity   cloud      insider
   │        │        │            │
   └────────┴────────┴────────────┘
                │
            join_states          ◄── findings merge, dedup MITRE,
                │                    worst-verdict, max-confidence
                ▼
           responder (dry-run)
                │
                ▼
              END

SEQUENTIAL MODE (fallback)
    auto_triage → phishing → identity → cloud → insider → responder → END

INVESTIGATOR (v6, orthogonal)
    recon → forensic → responder → report_writer → END
    (cada nó wrapped por _safe_node — exception capture → status=failed → END)
```

---

## 3. State schema

`app/investigator/state.py` define `InvestigatorState` (Pydantic v2 BaseModel):

```python
class InvestigatorState(BaseModel):
    run_id: UUID
    case_id: str
    tenant_id: str = "default"
    alert_summary: str
    raw_alert: dict[str, Any]

    # Per-agent outputs
    recon: ReconFindings
    forensic: ForensicFindings
    responder: ResponderPlan
    report_md: str
    report_html: str

    # Caches
    enrichment_cache: dict[str, Any]
    context_bundle: dict[str, Any]   # T2.1/T2.3 JSON-serialisable

    # Audit trail
    audit_log: list[AuditEntry]

    # Control
    status: str        # pending | running | completed | failed
    error: str | None
    iteration: int
    max_iterations: int = 6

    # Cost telemetry
    cost_summary: dict[str, Any]
```

`AuditEntry` granular:

```python
class AuditEntry(BaseModel):
    id: UUID
    timestamp: datetime
    kind: StepKind   # RECON | FORENSIC | RESPONDER | REPORTER |
                     # TOOL_CALL | LLM_CALL | ERROR |
                     # EVIDENCE_CITED | DECISION_REASON
    agent: str
    summary: str
    input_hash: str | None    # SHA-256 do input serializado
    output_hash: str | None
    duration_ms: int
    metadata: dict[str, Any]
```

---

## 4. Agentes individuais

| Agente | Arquivo | Função | LLM (default) | Onde está o prompt | Tools |
|---|---|---|---|---|---|
| `auto_triage` | `app/agents/auto_triage_agent.py` | Classifica verdict: true_positive / false_positive / benign | `${QUARRY_LLM_MODEL}` → `gpt-4o-mini` | linhas 42-71, módulo-level `_SYSTEM_PROMPT` | enrichment, IOC extraction |
| `phishing` | `app/agents/phishing_agent.py` | Análise de phishing (sender, URLs, anexos) | `${QUARRY_LLM_MODEL}` | linhas 28-51, módulo-level | enrichment, ContextBundle |
| `identity` | `app/agents/identity_agent.py` | Auth anomalies (impossible travel, brute force, priv esc) | `${QUARRY_LLM_MODEL}` | linhas 27-58, módulo-level | ContextBundle |
| `cloud` | `app/agents/cloud_agent.py` | Cloud infra (storage exposure, IAM anomalies, drift) | `${QUARRY_LLM_MODEL}` | linhas 28-59, módulo-level | ContextBundle |
| `insider_threat` | `app/agents/insider_threat_agent.py` | Insider (exfil, off-hours, privilege abuse) | `${QUARRY_LLM_MODEL}` | linhas 28-62, módulo-level | ContextBundle |
| `recon` (v6) | `app/investigator/recon_agent.py` | IOC extract + MITRE map + threat actor ID | `${OPENAI_MODEL}` → `gpt-4o-mini` | linhas 32-47 | `enrich_ioc`, `map_to_mitre`, `extract_iocs` |
| `forensic` (v6) | `app/investigator/forensic_agent.py` | Timeline, artefatos, root cause, blast radius | `${OPENAI_MODEL}` | linhas 36-53 | `sha256_of` |
| `responder` (v6) | `app/investigator/responder_agent.py` | Plano (containment/eradication/recovery — dry-run) | `${OPENAI_MODEL}` | linhas 35-51 | `sha256_of` |
| `report_writer` (v6) | `app/investigator/report_writer_agent.py` | Síntese Markdown + HTML | `${OPENAI_MODEL}` | linhas 34-49 | `sha256_of` |

**Característica importante:** todos os `_SYSTEM_PROMPT` são strings module-level — **não há mecanismo de override por tenant nem por idioma**. Mais detalhes na seção 7.

---

## 5. Tools registry

`app/investigator/tools.py` (150+ linhas) expõe wrappers async puros:

| Tool | Função | I/O |
|---|---|---|
| `enrich_ioc(ioc_value, ioc_type)` | HTTP POST para enrichment service | `${ENRICHMENT_SERVICE_URL}/enrich` (default `http://enrichment:8080`), timeout 10s |
| `extract_iocs(text)` | Regex IP/domínio/hash/URL | função pura |
| `map_to_mitre(text)` | Keyword → MITRE technique (local) | bag local `_MITRE_KEYWORDS` |
| `sha256_of(obj)` | JSON canonical hash | `hashlib.sha256(json.dumps(...))` |
| `fetch_case(case_id, api_token)` | Case lookup | `${API_SERVICE_URL}/api/v1/cases/{id}` |
| `fetch_related_alerts(case_id, limit, api_token)` | Alerts agregados | `${API_SERVICE_URL}/api/v1/cases/{id}/alerts` |

Adicional em `app/tools/`:
- `mitre.py` — `lookup_technique`, `lookup_tactic` (subset MITRE local, ~13 techniques)
- `mitre_full.py` — retrieval por embeddings, hardcoded `text-embedding-3-large`
- `graph.py` — operações de attack graph (não auditado em detalhe)

**Não há registry plug-in formal.** Tools são funções soltas; cada agente importa explicitamente as que usa.

---

## 6. Three-tier memory

`app/memory/` implementa três níveis com unificador (`MemoryManager`):

### 6.1 Session (LRU em-processo)

- `app/memory/session.py` (70 linhas)
- `OrderedDict`-based LRU **por `run_id`**, maxsize 512
- TTL = duração da run; limpo em `session_clear()` no fim
- Thread-safe via `asyncio.Lock()`
- Zero I/O

### 6.2 Working (Redis com fallback)

- `app/memory/working.py` (80+ linhas)
- Key schema: `quarry:mem:working:{tenant_id}:{run_id}:{key}` (pós-rebrand)
- Default TTL 86.400s (24h), configurável
- Redis URL: `${REDIS_URL}`
- Fallback: dict em-processo se Redis indisponível

### 6.3 Institutional (PostgreSQL + opcional pgvector)

- `app/memory/institutional.py` (100+ linhas)
- Tabela `quarry_institutional_memory` (pós-rebrand do schema name na criação; tabela já existente em prod fica com nome legado)
  ```sql
  id UUID PRIMARY KEY
  tenant_id TEXT NOT NULL
  key TEXT NOT NULL
  value JSONB NOT NULL
  tags TEXT[] DEFAULT '{}'
  analyst_override BOOLEAN DEFAULT FALSE
  override_reason TEXT
  created_at TIMESTAMPTZ DEFAULT now()
  UNIQUE (tenant_id, key)
  ```
- Pool asyncpg min_size=1 max_size=3
- Fallback dict em-processo

### 6.4 MemoryManager (API unificada)

```python
class MemoryManager:
    async def write_session(key, value)
    async def write_working(key, value, ttl=86_400)
    async def write_institutional(key, value, tags=None,
                                  analyst_override=False, override_reason=None)
    async def recall(key, tiers=["session","working","institutional"])
```

---

## 7. Investigation Ledger

`app/investigator/ledger.py` (321 linhas) — log append-only persistido em Postgres.

### Schema (migration `services/api/migrations/008_investigation_ledger.sql`)

**`investigation_runs`** — runs por case
```
id, tenant_id, case_id, alert_summary, raw_alert JSONB, model_used,
status, started_at, completed_at, iterations, total_tokens, total_cost_usd
```

**`investigation_events`** — eventos append-only (immutable trigger)
```
id, run_id, tenant_id, seq UNIQUE(run_id,seq),
ts, kind, agent, summary, payload JSONB,
input_hash, output_hash, duration_ms, created_at
```

**`investigation_artifacts`** — outputs maiores (report_md, etc.)
```
id, run_id, event_id, tenant_id, kind, content TEXT, sha256, size_bytes
```

### Write path

- **Best-effort:** se DB indisponível, log warning e continua (agent job é investigar, não bookkeeping)
- Tenant resolution: string `tenant_ref` → UUID lookup em `tenants` (cached na primeira call por run)
- RLS via `set_config('app.tenant_id', tenant_uuid, true)` antes de writes
- Payloads truncados a 8000 chars

### Replay & audit

- **Não encontrei endpoint de replay HTTP.** Pode existir em `services/api` (não auditado). UI viewer também não localizado.
- Ledger é append-only + immutable via trigger. Seq monotônico por run.

---

## 8. Pontos de extensão — onde Quarry pluga

### 8.1 Adicionar custom agents

**Não há registry plug-in formal.** Padrão atual:
1. Criar `app/agents/my_agent.py` com `async def run_my_agent(state) → state`
2. Registrar manualmente no `app/agents/__init__.py` (re-export)
3. Modificar `app/orchestrator/router.py` para adicionar como node ou capability no fan-out
4. Adicionar keyword bag em `classify_signals()` se for sub-agent

**Risco:** mudanças em `router.py` quebram cherry-pick de upstream se eles também tocarem o arquivo. Mitigação: extrair `_resolve_runner()` para registry table na primeira customização.

### 8.2 Substituir prompts

**Problema crítico para Quarry:** todos os `_SYSTEM_PROMPT` são strings module-level, **não configuráveis** por tenant ou idioma.

**Estratégia recomendada (definida em ADR-004):**

1. Criar tabela `agent_prompts(tenant_id, agent_name, language, system_prompt, version, active, created_at)`
2. Adicionar `app/core/prompts.py` com `async def get_system_prompt(agent_name, tenant_id, language)`
3. Refactor cada agente:
   ```python
   prompt = await get_system_prompt("phishing", state.tenant_id, "pt-BR")
   messages = [SystemMessage(content=prompt), ...]
   ```
4. Builtin prompts hardcoded ficam como **fallback default**, banco overrides

### 8.3 Adicionar custom tools

Padrão: função async em `app/tools/my_tool.py`, importar onde precisa.

Para BACEN/fintech BR, exemplos previstos:
- `lookup_bacen_warning(cpf_or_cnpj)` — consulta lista CCS-BACEN
- `enrich_pix_chave(chave)` — DICT (Diretório de Identificadores de Contas Transacionais)
- `lookup_lgpd_data_subject(cpf)` — verificar se cidadão é titular protegido LGPD
- `check_sanctions_list(entity)` — OFAC + sanções nacionais

### 8.4 Modificar state schema

`InvestigatorState` é Pydantic. Adicionar campos opcionais não quebra runs antigas:

```python
class InvestigatorState(BaseModel):
    # ... fields existentes ...
    brazilian_context: BrazilianContext | None = None  # opcional
```

Onde:

```python
class BrazilianContext(BaseModel):
    bacen_entity_status: dict[str, str]  # CNPJs/CPFs em lista BACEN
    lgpd_data_subject: bool
    sanctioned_jurisdictions: list[str]
    pld_risk_score: float | None = None
```

### 8.5 Skills Anthropic (mukul975)

Hook óbvio: `_resolve_runner()` em `router.py` já suporta lazy imports via `importlib.import_module()`. Plug-in seria:

```python
if name == "skill_cyber_threat":
    return getattr(agents_pkg, "run_skill_cyber_threat")
```

**Blocker atual:** não há agente genérico tool-using parametrizado. Cada agente espera output JSON com schema fixo. Integrar skills exigiria criar um agente intermediário ou refactor de `auto_triage`.

---

## 9. Riscos identificados

| # | Risco | Severidade | Impacto Quarry |
|---|---|---|---|
| 9.1 | Prompts hardcoded, sem override por tenant/idioma | **CRÍTICO** | Sem isso, customização BR é fork pesado. Resolver em primeira sprint Quarry. |
| 9.2 | LLM model selecionado via `os.getenv` global, sem per-tenant | Alto | Quarry pode precisar mix de providers (Anthropic, Gemini, OpenAI) por classe de caso |
| 9.3 | Prompt injection via `raw_alert` — mitigação parcial em `prompt_sanitizer.sanitize_text()` | Médio | Auditar cobertura (todos os campos sanificados?) |
| 9.4 | Sem versioning de agentes — mudar prompt afeta live imediatamente | Médio | Implementar A/B + rollout staged junto com tabela `agent_prompts` |
| 9.5 | Embedding model `text-embedding-3-large` hardcoded em `mitre_full.py` | Baixo-Médio | Pode precisar embeddings pt-BR otimizados |
| 9.6 | Não há replay endpoint do Ledger via HTTP — UI viewer ausente | Médio | Para auditoria BACEN, Ledger precisa ser navegável por humanos |

---

## 10. Recomendações de customização vertical fintech BR

**Decisão consolidada em [ADR-004](../adrs/ADR-004-orchestrator-fintech-br.md).** Sumário:

1. **Tabela `agent_prompts`** com overrides pt-BR + Quarry-tuned em primeira sprint
2. **5º sub-agente `bacen_compliance`** (fan-out paralelo) acionado por keywords PLD/AML/sanções
3. **`BrazilianContext` no state** — adicionar campo opcional, popular via novo step de enrichment BR
4. **Tools BR**: `lookup_bacen_warning`, `enrich_pix_chave`, `lookup_lgpd_data_subject`, `check_sanctions_list`
5. **Tabela `compliance_events`** complementar ao Ledger, ligando run → framework regulatório (BACEN, LGPD, PCI-DSS)
6. **Hunts em pt-BR** em `customizations/hunts/` referenciando os 11 patterns BR fintech já catalogados em `customizations/threat-intel/br-fintech/` (CARD-006)
7. **Ledger viewer UI** — escopo de card de frontend futuro

---

## 11. Arquivos-chave citados

```
services/agents/app/
├── orchestrator/
│   ├── __init__.py
│   └── router.py                    # 516 linhas — Router T2.2 v8.0
├── investigator/
│   ├── __init__.py
│   ├── orchestrator.py              # 407 linhas — Investigator v6 legado
│   ├── state.py                     # 310 linhas — InvestigatorState + AuditEntry
│   ├── ledger.py                    # 321 linhas — Persistent ledger
│   ├── tools.py                     # ~150 linhas — enrich_ioc, extract_iocs, map_to_mitre
│   ├── recon_agent.py               # 32-47 prompt, gpt-4o-mini
│   ├── forensic_agent.py            # 36-53 prompt
│   ├── responder_agent.py           # 35-51 prompt
│   ├── report_writer_agent.py       # 34-49 prompt
│   ├── prompt_sanitizer.py
│   └── bundle_prompt.py
├── agents/                          # T2.2 sub-agents
│   ├── auto_triage_agent.py         # 42-71 prompt
│   ├── phishing_agent.py            # 28-51 prompt
│   ├── identity_agent.py            # 27-58 prompt
│   ├── cloud_agent.py               # 28-59 prompt
│   └── insider_threat_agent.py      # 28-62 prompt
├── memory/
│   ├── manager.py                   # unified MemoryManager
│   ├── session.py                   # 70 linhas LRU
│   ├── working.py                   # 80+ linhas Redis + fallback
│   └── institutional.py             # 100+ linhas Postgres
├── tools/
│   ├── mitre.py                     # local MITRE subset
│   ├── mitre_full.py                # embeddings text-embedding-3-large
│   └── graph.py
├── context/
│   └── bundle.py                    # ContextBundle T2.1
├── policy/
│   └── guardrails.py                # SSRF guard, tool policy
├── security/
│   └── llm_resolver.py              # BYOK + per-tenant creds (não usado nos agentes!)
├── llm/
│   └── contract.py                  # LLM Input Contract (anti-injection)
└── main.py                          # FastAPI app entry
```

---

_Documento gerado a partir de leitura estática + relatório Explore. Para customização efetiva, ler também [ADR-004](../adrs/ADR-004-orchestrator-fintech-br.md)._
