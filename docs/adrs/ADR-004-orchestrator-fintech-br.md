# ADR-004: Estratégia de customização do orchestrator para fintech BR

**Data:** 2026-05-15
**Status:** ACEITO (decisão de arquitetura; implementação faseada)
**Decisores:** José Passinato · Claude
**Card relacionado:** CARD-005 (deep-dive do orchestrator)
**Documento de suporte:** [`docs/pt-br/orchestrator-deep-dive.md`](../pt-br/orchestrator-deep-dive.md)
**Predecessores:** [ADR-001](ADR-001-fork-aisoc.md), [ADR-002](ADR-002-fork-strategy.md), [ADR-003](ADR-003-rebrand-strategy.md)

---

## Contexto

A análise do orchestrator (CARD-005) revelou um sistema LangGraph bem desenhado mas com **rigidez crítica** para o caso de uso Quarry: prompts hardcoded sem override por tenant/idioma, LLM model global, ausência de agente regulatório BR, e sem viewer humano do Investigation Ledger.

Quarry precisa diferenciar-se do AiSOC genérico justamente onde o upstream **não** quis ir: regulamentação BACEN, idioma português, threat intel local. Esta ADR define **como** plugamos isso sem forkar o `services/agents/` inteiro.

---

## Decisão

### 1. Princípio orientador

**Tudo que diverge entra em `customizations/`. Código herdado (`services/`, `apps/`) só é tocado por refactors estruturais ínfimos que viabilizam o plug-in — não por features.**

Refactors estruturais permitidos no código herdado (escopo limitado):

1. Externalizar `_SYSTEM_PROMPT` para banco (tabela `agent_prompts`)
2. Adicionar campo `brazilian_context: BrazilianContext | None = None` em `InvestigatorState`
3. Adicionar 5º slot `"bacen_compliance"` em `classify_signals()` e `_resolve_runner()`
4. Adicionar tabela `compliance_events` complementar ao Ledger

Tudo o resto (prompts pt-BR, tools BR, agente compliance, hunts, evidence collectors) mora em `customizations/`.

### 2. Sprint plan (3 etapas)

#### Sprint A — Plug-in points (refactor estrutural mínimo)

Sem features ainda. Apenas viabilizar plug-in:

- [ ] Tabela `agent_prompts(tenant_id, agent_name, language, system_prompt, version, active, created_at)` em migration nova (`migrations/9XX_agent_prompts.sql`)
- [ ] `app/core/prompts.py::get_system_prompt(agent_name, tenant_id, language) → str` com fallback para constante hardcoded existente
- [ ] Refactor de 5 agentes (auto_triage, phishing, identity, cloud, insider) + 4 v6 (recon, forensic, responder, report_writer) — substituir `_SYSTEM_PROMPT` por `await get_system_prompt(...)`
- [ ] Builtin prompts EN ficam como string default constant — preserva comportamento upstream
- [ ] Adicionar `brazilian_context: BrazilianContext | None = None` em `InvestigatorState` (Pydantic, opcional, não quebra runs antigas)
- [ ] Adicionar tabela `compliance_events(id, run_id, tenant_id, regulatory_framework, risk_level, action_required, notification_sent_at, created_at)` (migration nova)
- [ ] Adicionar key `"bacen_compliance"` reservado em `classify_signals()` + branch no `_resolve_runner()` retornando agente customization

**Critério de pronto:** todos os testes existentes continuam verdes. Comportamento default não muda. Apenas hooks ficam disponíveis.

#### Sprint B — Camada Quarry-BR (em `customizations/`)

Com hooks prontos, popular customizações:

- [ ] `customizations/prompts/{auto_triage,phishing,identity,cloud,insider,recon,forensic,responder}/pt-BR.md` — versões portuguesas + tuned para fintech BR (BACEN-aware)
- [ ] `customizations/prompts/bacen_compliance/pt-BR.md` — system prompt do novo agente
- [ ] Migration seed inicial populando `agent_prompts` com versões pt-BR para tenants Quarry-BR
- [ ] `customizations/agents/bacen_compliance_agent.py` — implementação:
  - Inputs: `recon.threat_actors`, `forensic.root_cause_hypothesis`, `responder.recommended_actions`
  - Outputs: `compliance_status`, `regulatory_risk`, `notification_required`, `article_reference` (Lei 12.865, Resolução BACEN 4.658, LGPD)
- [ ] `customizations/tools/`:
  - `lookup_bacen_warning(cpf_or_cnpj)` — CCS-BACEN consulta
  - `enrich_pix_chave(chave)` — DICT lookup
  - `lookup_lgpd_data_subject(cpf)` — flag se sujeito é protegido
  - `check_sanctions_list(entity)` — OFAC + COAF + listas nacionais
- [ ] `customizations/hunts/pt-br/` — hunts referenciando os 11 patterns em `customizations/threat-intel/br-fintech/` (PIX-001, PIX-002, PIX-003, VSH-001, SEN-001, ATO-001, BOL-001, QR-001, EWL-001, MAL-001, MAL-002)

**Critério de pronto:** demo Quarry-BR mostra investigation com prompt pt-BR + agente BACEN respondendo + tools BR enriquecendo IOCs locais.

#### Sprint C — Auditoria + UI

- [ ] Endpoint HTTP de replay no Ledger (não encontrado no código auditado — ou pluga em `services/api` existente)
- [ ] Viewer UI do Ledger em `apps/web/src/app/(app)/ledger/` — navega events por run, exibe prompt + response + tools chamadas
- [ ] Endpoint para extrair `compliance_events` filtrável por `regulatory_framework` (BACEN, LGPD, PCI-DSS)
- [ ] Relatório PDF/HTML compliance — usa `weasyprint` (já dep upstream) para gerar evidência auditável

**Critério de pronto:** auditor humano consegue replay completo de uma investigation + extrair evidência compliance.

### 3. O que NÃO faremos no orchestrator

- ❌ NÃO substituir LangGraph por outra biblioteca
- ❌ NÃO mover orchestrator pra `customizations/` — o substrato é genérico, só extensões são BR
- ❌ NÃO criar plug-in registry formal nesta fase — pattern atual de import explícito serve até termos 3+ plug-ins externos
- ❌ NÃO mexer no Investigator v6 legado além do refactor de prompts — duplicar trabalho com Router T2.2 que é o ativo
- ❌ NÃO fazer LLM-fine-tune próprio — prompts overridáveis cobrem 80% dos ganhos a 5% do custo

### 4. Heranças do upstream que mantemos sem mudança

- ✅ `app/llm/contract.py` (LLM Input Contract) — manter ativo via `QUARRY_AGENTS_LLM_CONTRACT_ENFORCED=1`
- ✅ `app/policy/guardrails.py` + SSRF guard em playbook engine
- ✅ `app/security/llm_resolver.py` (BYOK + per-tenant creds) — atualmente subutilizado (só explain endpoint usa). Quarry deve **ativar** nos agentes na Sprint A, fazendo cada agente usar `llm_resolver.get_llm(state.tenant_id)` em vez de `os.getenv("QUARRY_LLM_MODEL")` direto
- ✅ Three-tier memory (session/working/institutional) intacto
- ✅ Investigation Ledger schema intacto — apenas adicionamos `compliance_events` paralelo

### 5. Cherry-pick policy específica para o orchestrator

Para honrar [ADR-002](ADR-002-fork-strategy.md):

- Quando upstream mexer em `services/agents/app/orchestrator/router.py` → review trimestral cataloga + decide cherry-pick por commit individual
- Quando upstream adicionar novo sub-agent (ex.: `kubernetes_agent`) → avaliar valor para fintech BR, cherry-pick se relevante
- Quando upstream mexer em prompts EN → **ignorar** (nossos prompts vivem em banco via `agent_prompts`, não nas constantes hardcoded)
- Quando upstream refatorar state schema → **conflito provável** com `brazilian_context` field; resolver manualmente em cherry-pick

### 6. Métricas de sucesso

| Métrica | Alvo Sprint A | Alvo Sprint B | Alvo Sprint C |
|---|---|---|---|
| % agentes com prompt override pluggable | 100% | 100% | 100% |
| Agentes pt-BR ativos por default em tenant BR | 0 | 9 (5 router + 4 v6) | 9 |
| Sub-agente BACEN compliance disparando em fan-out | não | sim | sim |
| Tools BR disponíveis | 0 | 4+ | 4+ |
| Hunts pt-BR cobrindo patterns BR fintech | 0 | 8+ | 11 |
| Ledger viewer UI navegável por humano | não | não | sim |
| Endpoint replay Ledger | não | não | sim |

---

## Consequências

### Positivas

- Customização BR é aditiva, não destrutiva — facilita cherry-pick
- Camada `customizations/` fica autocontida (prompts, agents, tools, hunts) — pode até virar plugin público depois
- Override de prompts via banco abre porta para A/B testing e per-tenant tuning
- Agente BACEN é novo (não compete com upstream) — sem conflito futuro

### Negativas (aceitas)

- 4 refactors estruturais no código herdado (`agent_prompts` table + `BrazilianContext` field + `classify_signals` slot + `compliance_events` table) **criam conflito potencial com cherry-pick**. Aceitável dado o ganho.
- Tabela `agent_prompts` adiciona latência de 1 query Postgres por LLM call (mitigável com cache em-processo)
- Risco de drift entre prompts EN (default constante) e PT-BR (banco) se manutenção desigual
- Tools BR são P0 mas exigem APIs BACEN/SERASA — pode bater em rate-limit ou custos. Mock-first.

### Neutras

- Skills Anthropic (mukul975) continuam como possibilidade futura, não bloqueante. Hook em `_resolve_runner()` já permite plugar.

---

## Implementação faseada (após CARD-007)

A execução das Sprints A/B/C **não está coberta pelo CARD-005**. Esta ADR documenta a estratégia; cards futuros executam:

- CARD-XXX-A: refactor estrutural (Sprint A)
- CARD-XXX-B: prompts pt-BR + agente BACEN + tools BR (Sprint B)
- CARD-XXX-C: viewer Ledger + replay endpoint + compliance evidence UI (Sprint C)

---

## Referências

- [docs/pt-br/orchestrator-deep-dive.md](../pt-br/orchestrator-deep-dive.md) — análise técnica completa
- [customizations/threat-intel/br-fintech/](../../customizations/threat-intel/br-fintech/) — 11 patterns BR fintech (CARD-006)
- [ADR-001](ADR-001-fork-aisoc.md), [ADR-002](ADR-002-fork-strategy.md), [ADR-003](ADR-003-rebrand-strategy.md)
- Heranças preservadas: `app/llm/contract.py`, `app/policy/guardrails.py`, `app/security/llm_resolver.py`
