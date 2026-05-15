# ADR-003: Estratégia de rebrand AiSOC → Quarry

**Data:** 2026-05-15
**Status:** ACEITO (parcialmente executado — validação funcional pendente)
**Decisores:** José Passinato · Claude
**Card relacionado:** CARD-004
**Predecessores:** [ADR-001](ADR-001-fork-aisoc.md), [ADR-002](ADR-002-fork-strategy.md)

---

## Contexto

ADR-002 estabeleceu o fork independente Quarry. O código herdado ainda exibia "AiSOC" em **41.565 ocorrências** distribuídas em **4.775 arquivos** — package names, env vars, service names, UI strings, docs, helm chart, scripts. O CARD-004 exige rebrand visível sem perder atribuição legal nem quebrar runtime.

Decisão técnica forçada pelo blast radius: como o VPS de produção não atende o pré-requisito de RAM para subir a demo (5.8 GB available vs. 8 GB exigidos), **a validação runtime foi delegada para outra máquina** (José executa offline via `docs/pt-br/CARD-002-demo-checklist.md`). O rebrand foi feito **confiando em CI estático** (lint, typecheck, codeql) como rede de segurança, conforme escolha explícita do José.

## Decisão

### 1. Execução em batches commit-by-commit

Para tornar regressões reversíveis sem precisar refazer tudo:

| Batch | Escopo | Commit |
|---|---|---|
| **1** — Visual identity | logos SVG, favicon, OG image, PWA manifest, branding guide | `dd342d0b` |
| **2** — Package names | `@aisoc/*` → `@quarry/*` (9 npm workspaces) + `aisoc-*` → `quarry-*` (15 pyproject names) + 34 imports | `e6c9a979` |
| **3** — Bulk rename | env vars `AISOC_*` (152 distinct), Pascal/lower/upper-case strings, helm dir, scripts, SDK dirs, file/dir renames via `git mv` | `cfb83e92` |

Cada commit isolável via `git revert` se quebrar runtime no laptop do José.

### 2. Preservações (não-negociáveis)

Arquivos cujo conteúdo **deve** manter "AiSOC":

| Arquivo | Razão |
|---|---|
| `LICENSE` | MIT clause obriga preservação do copyright "AiSOC contributors" |
| `NOTICE.md` | Atribuições obrigatórias (MIT + DRL-1.1 + Apache + LGPL) |
| `README.AISOC.md` | Cópia integral do README upstream, referência técnica congelada |
| `README.md` | Texto descritivo do fork — cita AiSOC como upstream por nome |
| `docs/SKILL.md` | Idem — guia Claude Code que descreve relação de fork |
| `docs/adrs/ADR-001-fork-aisoc.md` | Decisão histórica de fork — filename + conteúdo |
| `docs/adrs/ADR-002-fork-strategy.md` | Política de cherry-pick — cita AiSOC explicitamente |
| `docs/community-feedback/2026-05-12/AiSOC_*.md` | Snapshot histórico de feedback comunitário recebido |
| `services/api/migrations/028_aisoc_cases_case_number.sql` | Migration histórica — alembic checksum protege ordem |
| `CHANGELOG.md`, `ROADMAP.md` (URLs GitHub) | Issue/PR links apontam para `beenuar/AiSOC` — histórico do upstream |
| `.github/workflows-disabled/` | Fora do escopo ativo |

### 3. Paleta visual

| Token | Hex | Uso |
|---|---|---|
| `quarry-red` | `#8B0000` | acentos, branding mark |
| `quarry-charcoal` | `#1a1a1a` | fundos dark, primário |
| `quarry-bone` | `#f7f4ef` | off-white, fundos claros |
| `quarry-ink` | `#0a0a0a` | texto sobre claro |
| `quarry-rust` | `#a8482e` | hover de red |
| `quarry-gravel` | `#3a3a3a` | bordas, separadores |
| `quarry-ash` | `#9a9a9a` | metadata |

Detalhes completos em [`docs/branding.md`](../branding.md).

### 4. Tipografia

- **Marketing/landing**: Fraunces (serif, variable) + Inter (sans, variable). Italic permitido em pull quotes. Alinha com `/root/RULES-anti-ai-design.md`.
- **Console autenticado**: Inter exclusivo. Dashboards são utilitários (regra anti-AI design 12Brain).
- **Code/logs/JSON**: JetBrains Mono ou fallback monospace do upstream.

### 5. Logos

- `apps/web/public/logo-mark.svg` — hexágono estilizado (quarry pit) com mark central vermelho
- `apps/web/public/logo.svg` — full lockup com wordmark Fraunces "Quarry"
- `apps/web/public/favicon.svg` — versão minimal do mark
- `apps/web/public/og-image.svg` — 1200×630 social preview

Todos placeholders. Versão final encomendada quando MVP estiver de pé.

### 6. Taglines oficiais

- **EN:** Autonomous Threat Hunting for the Post-Mythos Era
- **PT-BR:** Caça Autônoma de Ameaças para a Era Pós-Mythos

### 7. Estratégia de validação

Como a demo full-stack não pôde rodar no VPS de produção:

1. **CI estático** (ci.yml, codeql.yml, check-openapi.yml, validate-detections.yml, validate-playbooks.yml, graph-schema-check.yml, quarantine-tracker.yml, compose-smoke.yml) roda no push e captura quebras óbvias de Python import / TypeScript types / YAML schema.
2. **Demo offline** (CARD-002 kit em `docs/pt-br/CARD-002-demo-checklist.md`) — José roda em laptop ou VPS dedicado, executa hunt + verifica Ledger + testa MCP.
3. **Rebrand-checklist** (`docs/rebrand-checklist.md`) lista o que foi tocado e o que NÃO foi, para revisão visual no browser.

### 8. Aceitar riscos residuais conhecidos

**Riscos aceitos pelo José em troca de velocidade:**

- ⚠️ **Strings em comentários/docstrings/test names** podem conter "aisoc" em contextos benignos não detectados pelo sed (ex.: variável local `aisoc_dev_secret` em alguns paths). Cleanup oportunístico em PRs futuros.
- ⚠️ **Kafka consumer groups** com nome `aisoc-*` no código foram renomeados para `quarry-*`. Em deploy novo (sem checkpoint anterior) sem impacto; em ambiente com offset acumulado, seria necessário declarar group reset.
- ⚠️ **Alembic migrations** preservadas com nomes originais. Schema do banco mantém colunas/índices nomeados com `aisoc_*` se já existiam. Não-bloqueante.
- ⚠️ **Imagens Docker** ainda apontam para `ghcr.io/beenuar/aisoc-*` no docker-compose herdado. Substituir por `ghcr.io/josepassinato/quarry-*` em card de deploy quando o registry Quarry existir.

### 9. ADR adicional (próximo)

Não rebrandear nada do orchestrator LLM logic neste card. Customização de prompts em pt-BR, agente BACEN compliance, hunts BR são escopo de [ADR-004 — Orchestrator customization for BR fintech](ADR-004-orchestrator-fintech-br.md).

---

## Consequências

### Positivas

- Identidade Quarry visível em todas as superfícies (UI, configs, package names, scripts, helm)
- Camadas de atribuição legal intactas
- Histórico do upstream preservado (CHANGELOG, ROADMAP, migrations, community-feedback)
- Rollback granular via `git revert` de batches isolados
- Branding documentado (docs/branding.md) para uso consistente futuro

### Negativas (aceitas)

- Validação runtime delegada — qualquer regressão silenciosa só aparece quando José rodar demo
- Diff gigante (~4.6k arquivos, 39k insertions/deletions) dificulta code review tradicional — mitigado por commit-batch-isolation
- Pode haver string "aisoc" residual em contextos não-críticos — aceito; cleanup futuro
- Próximo card que pegar features upstream (cherry-pick) vai gerar conflitos massivos por causa do rebrand — esperado, faz parte da política ADR-002

---

## Implementação (2026-05-15)

- ✅ Batch 1 (`dd342d0b`): visual identity + branding.md
- ✅ Batch 2 (`e6c9a979`): package names + workspaces
- ✅ Batch 3 (`cfb83e92`): bulk env vars + service names + helm + file/dir renames
- ✅ ADR-003 (este documento)
- ✅ docs/rebrand-checklist.md
- ⏳ Validação funcional pelo José (offline)

---

## Referências

- [ADR-001](ADR-001-fork-aisoc.md) — Decisão de fork condicional
- [ADR-002](ADR-002-fork-strategy.md) — Mirror clone + upstream merge policy
- [docs/branding.md](../branding.md) — Guidelines visuais
- [docs/rebrand-checklist.md](../rebrand-checklist.md) — Inventário do rebrand
- [docs/pt-br/CARD-002-demo-checklist.md](../pt-br/CARD-002-demo-checklist.md) — Validação offline
