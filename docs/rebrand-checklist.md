# Rebrand Checklist — AiSOC → Quarry

**Card:** CARD-004
**Data:** 2026-05-15
**Status:** Execução completa. Validação funcional pendente.

Inventário do que foi tocado no rebrand massivo (commits `dd342d0b` → `e6c9a979` → `cfb83e92`). Use este documento quando rodar a demo (CARD-002) para validar visualmente.

---

## ✅ Substituído

### Visual identity (Batch 1)

- [x] `apps/web/public/logo-mark.svg` — hexágono "quarry pit" + mark vermelho `#8B0000`
- [x] `apps/web/public/logo.svg` — lockup completo com wordmark "Quarry" em Fraunces
- [x] `apps/web/public/favicon.svg` — favicon minimal
- [x] `apps/web/public/og-image.svg` — 1200×630 social preview com tagline pós-mythos
- [x] `apps/web/public/manifest.json` — PWA: name "Quarry Responder", theme color `#0a0a0a`
- [x] `apps/docs/static/img/aisoc-social-card.png` → `quarry-social-card.png` (rename só, conteúdo do PNG não tocado — substituir em card visual futuro)
- [x] `docs/branding.md` — guidelines criadas

### Package names (Batch 2)

- [x] 9 npm workspaces: `@aisoc/{web,docs,types,mcp,ocsf,ui,sdk,realtime}` → `@quarry/*`
- [x] 15 Python `pyproject.toml` names: `aisoc-{api,agents,fusion,actions,ueba,threatintel,connectors,slack-bot,teams-bot,osquery-tls,purple-team,honeytokens,cli,sdk,plugin-sdk}` → `quarry-*`
- [x] 34 import statements `@aisoc/*` em código TS/TSX/JS/JSON

### Bulk rename (Batch 3)

- [x] **Env vars (152 distinct)**: `AISOC_*` → `QUARRY_*`
- [x] **Identifier casing**: `AiSOC` → `Quarry`, `aisoc` → `quarry`, `AISOC` → `QUARRY`, `Aisoc` → `Quarry`
- [x] **Helm chart**: `infra/helm/aisoc/` → `infra/helm/quarry/` (Chart.yaml, values, templates)
- [x] **Docker compose**: volumes/networks `aisoc-demo` → `quarry-demo`, `aisoc` → `quarry`
- [x] **Dev secrets**: `aisoc_dev_secret` → `quarry_dev_secret` (defaults só)
- [x] **Function name**: `remove_aisoc_images()` → `remove_quarry_images()` em uninstall scripts

### File/directory renames (git mv)

- [x] `packages/aisoc-cli/` → `packages/quarry-cli/`
- [x] `packages/aisoc-cli/src/aisoc_cli/` → `packages/quarry-cli/src/quarry_cli/`
- [x] `packages/sdk-py/src/aisoc_sdk/` → `quarry_sdk/`
- [x] `packages/plugin-sdk-py/src/aisoc_plugin_sdk/` → `quarry_plugin_sdk/`
- [x] `packages/sdk-go/aisoc/` → `quarry/`
- [x] `packages/plugin-sdk-go/aisoc/` → `quarry/`
- [x] `plugins/aisoc-direct/` → `plugins/quarry-direct/`
- [x] `services/osquery-extensions/internal/aisocapi/` → `quarryapi/`
- [x] `scripts/aisoc-{acceptance,demo,doctor}.ts` → `quarry-*.ts`
- [x] `services/slack-bot/app/services/aisoc_clients.py` → `quarry_clients.py`
- [x] `services/slack-bot/tests/test_aisoc_clients.py` → `test_quarry_clients.py`
- [x] `services/teams-bot/app/services/aisoc_clients.py` → `quarry_clients.py`
- [x] `services/actions/app/clients/aisoc_direct_client.py` → `quarry_direct_client.py`
- [x] `packs/aisoc-{fim-credentials,attck-persistence,inventory-baseline,attck-defense-evasion,fim-baseline}.yaml` → `quarry-*.yaml`
- [x] `profiles/auditd/aisoc.rules` → `quarry.rules`
- [x] `plans/aisoc_v8.0_north_star_plan_*.md` → `quarry_v8.0_*.md`
- [x] `plugins/community/_examples/hello-plugin/aisoc-plugin.yaml` → `quarry-plugin.yaml`

### Import updates (post-rename)

- [x] `aisoc_cli` → `quarry_cli`
- [x] `aisoc_sdk` → `quarry_sdk`
- [x] `aisoc_plugin_sdk` → `quarry_plugin_sdk`
- [x] `aisocapi` → `quarryapi`

---

## 🚫 Preservado intencionalmente

### Atribuição legal (NUNCA renomear)

- [x] `LICENSE` — copyright "AiSOC contributors" (cláusula MIT)
- [x] `NOTICE.md` — atribuições obrigatórias multi-source
- [x] `README.AISOC.md` — README original do upstream, congelado (82KB)

### Documentação descritiva do fork

- [x] `README.md` — texto cita AiSOC como nome do upstream
- [x] `docs/SKILL.md` — guia Claude descreve relação de fork
- [x] `docs/adrs/ADR-001-fork-aisoc.md` — decisão histórica de fork
- [x] `docs/adrs/ADR-002-fork-strategy.md` — política upstream merge
- [x] `docs/community-feedback/2026-05-12/AiSOC_*.md` — feedback comunitário recebido

### Histórico de migrations

- [x] `services/api/migrations/028_aisoc_cases_case_number.sql` — alembic checksum

### URLs históricas em CHANGELOG/ROADMAP

- [x] `CHANGELOG.md` — issue/PR links continuam `github.com/beenuar/AiSOC`
- [x] `ROADMAP.md` — idem

### CI desabilitado

- [x] `.github/workflows-disabled/` — fora de escopo ativo

### Lockfiles (regenerados por tools)

- [x] `pnpm-lock.yaml`
- [x] `services/*/package-lock.json`

---

## 🔍 Validação pendente — execute na demo offline (CARD-002)

Quando rodar a demo em hardware adequado, verificar:

### UI visual

- [ ] HTML `<title>` mostra "Quarry" em todas as páginas (`apps/web/src/app/layout.tsx`)
- [ ] Logo na navbar é o novo SVG (hexágono + mark vermelho)
- [ ] Favicon na aba do browser é o Quarry favicon
- [ ] Cor dominante respeita paleta (`quarry-red` + charcoal + bone)
- [ ] Open Graph preview em redes sociais usa `og-image.svg` novo
- [ ] PWA install prompt mostra "Quarry Responder"

### Runtime

- [ ] `docker compose up` parte sem erro de "image not found" (imagens upstream `ghcr.io/beenuar/aisoc-*` ainda referenciadas em algumas paths — pode falhar; ver caveat em ADR-003 §8)
- [ ] Health checks dos serviços passam
- [ ] Login → dashboard renderiza
- [ ] Investigation Ledger UI mostra runs de teste
- [ ] Hunt manual executa do começo ao fim
- [ ] MCP server responde a `aisoc_list_alerts` (apesar do nome legado da tool — não tocado por compatibilidade do protocolo MCP)

### Env vars

- [ ] App lê todas as `QUARRY_*` corretamente (nenhum `KeyError` em logs)
- [ ] `.env.example` documenta vars com nomes novos
- [ ] Não há var `AISOC_*` órfã consumida em runtime

### Logs

- [ ] `pm2/docker logs` não mostram tracebacks de import error pós-rename
- [ ] Structured logs (`structlog`) reportam service names com prefixo `quarry-`

---

## 📋 Comandos úteis para a validação

```bash
# Conferir que UI não tem "AiSOC" visível
docker compose exec web sh -c 'grep -ri "AiSOC" .next/static 2>/dev/null | head -10'

# Conferir env vars em runtime
docker compose exec api env | grep -E '^(AISOC|QUARRY)_'

# Conferir imports Python carregando ok
docker compose exec api python -c 'import app.main' 2>&1 | tail -5
docker compose exec agents python -c 'import app.main' 2>&1 | tail -5

# Conferir HTML title
curl -s http://localhost:3000 | grep -oE '<title>[^<]+</title>'
```

---

## Erros conhecidos a esperar (não-bloqueantes)

- **Imagens Docker hardcoded** em `docker-compose.yml`: ainda apontam para `ghcr.io/beenuar/aisoc-{api,agents,realtime,web,...}`. Quando publicarmos versão Quarry no nosso registry, atualizar. Por ora, demo pode falhar no pull se essas imagens forem private — solução temporária: build local com `docker compose build`.
- **Migrations antigas** referenciam tabelas com nomes históricos. Schema do banco pode mostrar colunas com `aisoc_*` se já populado por seed legado.
- **Dependabot reativará** com novo PR mensal mesmo em modo security-only quando dependências críticas tiverem CVE.
