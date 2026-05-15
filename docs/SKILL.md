# SKILL.md — Guia operacional para Claude Code no Quarry

> Este documento é lido por instâncias de Claude Code (ou agentes equivalentes) que trabalham neste repositório. Define o que Quarry é, como o código está estruturado, e quais regras NUNCA quebrar.

**Última atualização:** 2026-05-15
**Status do projeto:** validação técnica em curso — fork executado, rebrand ainda pendente

---

## 1. Contexto — o que é Quarry e por que existe

Quarry é um SaaS comercial de Security Operations Center (SOC) alimentado por IA, em desenvolvimento pela **Increase Trainer Inc.** O produto é forkado em mirror-clone do projeto open-source [AiSOC](https://github.com/beenuar/AiSOC) (MIT, commit `28ce9f6b`, fork em 2026-05-15).

**Diferenciação prevista:** Quarry foca no mercado brasileiro — hunts e regras Sigma específicas para ameaças locais, evidence automation para BACEN/LGPD, prompts em pt-BR, integrações com infraestrutura nacional. O upstream (AiSOC) atende mercado global genérico.

**Decisão estratégica (ver [ADR-001](adrs/ADR-001-fork-aisoc.md)):**
- Fork imediato, independente, em repositório privado.
- Cherry-pick manual de upstream — **nunca** `git pull` automático.
- AiSOC/Cyble tratados como concorrentes potenciais, não como parceiros.

---

## 2. Arquitetura herdada

```
Monorepo pnpm + turbo:

apps/
├── web/         Next.js 16 + React 19 — SOC console (35+ rotas)
└── docs/        Docusaurus (será removido ou rebrand)

services/        14 microsserviços, FastAPI (Python) + Go (ingest):
├── api/          API core (62k linhas, 67 testes) — auth, GraphQL, detection
├── agents/       LangGraph orchestrator + Investigation Ledger (33 testes)
├── ingest/       Hot path em Go
├── fusion/       Alert correlation
├── connectors/   50+ integrações (SIEMs, clouds, EDRs)
├── enrichment/   Threat intel lookups
├── realtime/     WebSocket fanout (Kafka consumer)
├── mcp/          MCP server TypeScript (Claude Desktop/Cursor)
├── ueba/, threatintel/, honeytokens/, purple-team/, osquery-tls/, actions/, slack-bot/, teams-bot/

packages/        SDKs (Python, TypeScript, CLI)

detections/      Corpus multi-fonte com provenance per-regra:
├── sigma-imports/      (DRL-1.1, SigmaHQ)
├── car-imports/        (Apache-2.0, MITRE CAR)
├── splunk-imports/     (Apache-2.0)
├── chronicle-imports/  (Apache-2.0)
└── (cloud|identity|endpoint|network|application|data-exfil)/  (native, Apache-2.0)

playbooks/       Playbooks de resposta (YAML)
```

**Infraestrutura completa exige (será cortada):** Postgres, Redis, Kafka+Zookeeper, ClickHouse, OpenSearch, Qdrant, Neo4j, Prometheus, Grafana + 13 app services = 20+ containers.

**MVP planejado (corte previsto em card futuro):** apenas api, agents, web, ingest, fusion, realtime, mcp + connectors mínimos. Substituir Kafka+Zookeeper por Redpanda. Adiar Neo4j/Qdrant/OpenSearch.

---

## 3. Camada de customização Quarry

**REGRA DE OURO:** tudo que é Quarry-specific vive em:

```
customizations/
├── detections/    Sigma rules calibradas pra BR (BACEN/PIX, fraudes locais)
├── hunts/         Hunt templates em pt-BR
├── prompts/       Prompts customizados Quarry (overrides aos do AiSOC)
└── compliance/    Evidence automation (BACEN, LGPD)

infrastructure/
├── vps/           Configs específicas pra VPS Hostinger (76.13.109.151)
└── deploy/        Scripts de deploy Quarry
```

**Por quê:** mantém customizações fisicamente separadas do código herdado. Permite (a) cherry-pick controlado de upstream sem conflito, (b) revisar PRs Quarry sem ruído de churn upstream, (c) eventualmente extrair customizações pra outro projeto.

**Quando você (Claude) precisar adicionar uma feature Quarry-specific:** sempre prefira `customizations/` ou `infrastructure/`. Modificar código em `services/`, `apps/`, `packages/` é exceção, e exige justificativa em commit + entrada em ADR.

---

## 4. Coding standards

### 4.1 Idioma

- **Inglês para código.** Identificadores, comentários inline, nomes de arquivos, mensagens de log, exceções.
- **Inglês para commits.** Padrão Conventional Commits do upstream: `feat(scope):`, `fix(scope):`, `chore(scope):`, `docs(scope):`, `refactor(scope):`.
- **Português para documentação operacional.** README de cliente, runbooks, ADRs, comunicação interna em `docs/pt-br/`.
- **Português para `customizations/`** quando o conteúdo é narrativo (descrições de hunts, prompts) — código em inglês mesmo dentro de customizations.

### 4.2 Convenções herdadas (manter)

- Python 3.11+, FastAPI, Pydantic v2, async/await sempre
- TypeScript 5.8+, ESM, vitest para testes
- `ruff` + `mypy` no Python (config centralizada em `ruff.toml` na raiz)
- `prettier` + `eslint` no Node
- `pnpm` para Node (workspace), `poetry` para Python

### 4.3 Não regredir

- Estrutura modular de serviços — não criar god-files
- Investigation Ledger é fonte de verdade de auditoria — toda decisão LLM passa por ele
- Provenance em detection rules nunca é removida
- Logs estruturados (`structlog`), não `print`

---

## 5. Princípios pós-Mythos (adversarial agent assumptions)

(Referência interna do José/Increase Trainer aos aprendizados pós-Mythos sobre design adversarial de agentes.)

1. **Operador pode ser hostil ou comprometido.** Toda ação do agente tem que ser auditável e revertível. Investigation Ledger é design constraint, não feature.
2. **LLM pode ser jailbroken/contornado.** Validar input de fato (LLM Input Contract já implementado no upstream em `services/agents/app/llm/contract.py` — manter ativo via `AISOC_AGENTS_LLM_CONTRACT_ENFORCED=1`).
3. **Tool calls precisam de policy guard.** Já existe `services/agents/app/policy/guardrails.py` + SSRF guard em playbook engine. Não enfraquecer.
4. **Custos (LLM tokens, API calls) são vetor de ataque.** Rate limiting + cost telemetry já existem no upstream — Quarry herda e estende quando relevante.
5. **Detection rules são código.** Versionar, revisar PR, validar contra dataset sintético antes de promover. Eval harness do upstream cobre o substrato; customizations precisam de seu próprio gate.

---

## 6. Como rodar localmente

> ⚠️ Não validado funcionalmente ainda neste VPS — Card-002 (demo end-to-end) está pendente em outra máquina. Ver `docs/pt-br/CARD-002-demo-checklist.md`.

**Quando for rodar pela primeira vez:**

```bash
# Pré-requisito: docker compose, pnpm 8+, Python 3.11+
git clone git@github.com:Josepassinato/quarry.git
cd quarry
cp .env.example .env
# Editar .env com keys (Anthropic, OpenAI/Gemini para embeddings, xAI)

# Demo "one-shot" (compose com 13 serviços):
pnpm aisoc:demo

# UI em http://localhost:3000
# API em http://localhost:8000/docs
```

**Não tente rodar full demo na VPS de produção 76.13.109.151** — RAM já está apertada com 60+ processos PM2 dos outros projetos 12Brain. Subir AiSOC stack causa OOM kill provável. Rodar em laptop ou VPS dedicado.

---

## 7. Como deployar (futuro)

Ainda não definido. Quando ADR-XXX de deploy strategy for escrito, este SKILL.md será atualizado com referência.

**Sketch provisório:**
- Domínio: `quarry.12brain.org` (DNS na Hostinger, já apontando para 76.13.109.151)
- Nginx reverse proxy → containers Quarry no mesmo VPS (após o corte de stack do MVP)
- TLS via Let's Encrypt (mesma rotina dos outros projetos)
- PM2 NÃO usado — Quarry roda em Docker Compose dedicado
- Backup: rsync de volumes Docker (postgres, clickhouse, qdrant) para storage externo

---

## 8. Regras invioláveis (CLAUDE: NUNCA quebre)

1. **NÃO** faça `git pull` do upstream AiSOC sem revisão manual + decisão registrada em ADR. O remote `upstream` pode ser configurado, mas merge é sempre cherry-pick.
2. **NÃO** modifique arquivos sob `services/`, `apps/`, `packages/`, `detections/` (herdados) sem que o commit cite o card que autoriza. Customizações vão em `customizations/`.
3. **NÃO** remova o sistema de `provenance` de detections — é obrigação legal das licenças DRL/Apache.
4. **NÃO** commite secrets (`.env`, API keys, tokens). Use GitHub Secrets via Actions. `.gitleaks` está ativo.
5. **NÃO** publique nada em registry público (`@quarry/*` workspaces, `quarry-mcp` bin, `ghcr.io/beenuar/*` imagens) sem confirmar que o registry/namespace de destino é controlado pela Increase Trainer Inc.
6. **NÃO** rode demo full stack na VPS de produção. Sempre em hardware separado até MVP cortado existir.
7. **NÃO** comunique com mantenedores do AiSOC em nome do Quarry sem direção do José. Tratamos como concorrentes (ADR-001).
8. **NÃO** rebrand parcial sem checklist completo. Quando o card de rebrand chegar, será atômico: ou Quarry inteiro, ou nada.

---

## 9. Onde estão as referências

- [`docs/adrs/`](adrs/) — toda decisão arquitetural escrita
- [`docs/pt-br/`](pt-br/) — runbooks operacionais e checklists em português
- [`README.AISOC.md`](../README.AISOC.md) — README original do AiSOC (referência técnica)
- [`NOTICE.md`](../NOTICE.md) — atribuições obrigatórias
- [Quarry no GitHub](https://github.com/Josepassinato/quarry) — repositório privado

---

## 10. Quando atualizar este arquivo

- Sempre que uma decisão grande (ADR) for tomada — adicionar referência aqui
- Sempre que a estrutura de pastas mudar significativamente
- Sempre que uma regra inviolável for criada, removida ou modificada
- Sempre que uma camada nova de customização for adicionada
