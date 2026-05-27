# SESSION-NOTES.md — Quarry

> Estado canônico entre sessões. Última sessão sempre escreve aqui.

---

## 2026-05-26 (PM) — CARD-016 Item 1 ENCERRADO: Bacen Evidence Engine estruturalmente completo

### Pivôt de posicionamento (esta sessão)
Categoria mudou de "Sovereign SOC" → **"Bacen Evidence Engine"**. Razão:
re-análise de durabilidade de moat indica que sovereign deployment +
citation reasoning viram commodity em 12–24 meses (Llama 4 / GPT-OSS +
frontier models com grounded output nativo). Único pilar que dura 3–5
anos é Bacen-native compliance — onde o roadmap concentra agora.
Detalhes em `.planning/private/POSITIONING.md` (atualizado) +
`.planning/private/CARD-016-bacen-evidence-engine.md` (novo).

Concorrente real revisado: **NÃO é Splunk/CrowdStrike — é a consultoria
+ planilha + Word que toda fintech Bacen-licenciada usa hoje** (PwC,
Deloitte, KPMG, boutiques BR cobrando R$ 40–120k/projeto).

### Modelo de licenciamento aprovado (open-core)
Core MIT em github.com/Josepassinato/Security (já público). Camada
premium futura (templates curated, hosted SaaS, KMS + e-CNPJ wiring,
auditor companion) sob BSL → Apache 2.0 em 4 anos. Padrão Sentry /
Posthog / Cal.com. Sem repo separado: monorepo dual-license em
`core/` + `enterprise/` (planejado).

### CARD-016 Item 1 — ENTREGUE (10 commits, ~4750 linhas, 123+ tests)

| Camada | Componentes | Arquivos |
|---|---|---|
| DSL | strict Pydantic + parser + regulation allowlist | `services/api/app/evidence_pack/{schema,parser}.py` |
| Sealing | Merkle chain + RFC 3161 TSA (mock+stub) + PKCS#7 e-CNPJ (mock+stub) | `merkle.py` `tsa.py` `signer.py` |
| Compiler | choreographer + 6 query types + MockRuntime | `compiler.py` |
| Renderer | HTML self-contained + WeasyPrint PDF | `renderer.py` |
| API endpoints | list, get, compile, preview.html, download.pdf, verify-chain | `endpoints/evidence_packs.py` + `endpoints/investigations.py` |
| DB | migration 046 + ORM (prev_hash + entry_hash) | `migrations/046_*.sql` + `models/investigation.py` |
| Ledger writer | vendored merkle + chain on every INSERT | `services/agents/app/investigator/ledger.py` |
| Content | 3 evidence packs reais (BCB 85 Art. 6, LGPD Art. 48, Bacen 24h) | `customizations/compliance/evidence-packs/*.yaml` |
| Operator UI | `/settings/evidence-packs` (list + compile + preview + PDF) | `apps/web/src/components/settings/EvidencePacksView.tsx` |
| CI guards | positioning anti-tagline lint + vendored merkle drift check | `.github/workflows/ci.yml` |

### Bloqueios não-engineering (acionáveis pelo José)

| Item | Custo | Destrava |
|---|---|---|
| Aplicar migration 046 em prod | $0 | Chain writer ativa |
| Renovar token Hostinger API (`/root/.secrets/hostinger.env`) | $0 | Provisionar VPS via MCP |
| Conta SafeWeb TSA (ICP-Brasil) | R$ 60–150/mês | TSA real → seal admissível em juízo |
| e-CNPJ A3 cert Increase Trainer (Serasa/Certisign) | R$ 250 + ~1h | Assinatura digital real |
| Advisor jurídico revisar 3 packs | R$ 5–10k | Packs go-to-market reais |
| Autorizar Hostinger KVM 8 BR (~R$ 240/mês) | R$ 240/mês | Benchmark Sovereign LLM real |

### Surfaces públicas atualizadas (esta sessão)
- README.md → "Open-source Bacen Evidence Engine for Brazilian fintechs"
- GitHub repo description → mesma narrativa
- `/br/sovereign-llm` landing → reframado como deployment option (não wedge)
- 5 good-first-issue tickets seedados (#24-#28)
- GitHub Discussions habilitadas + 15 topics + 6 labels custom
- `.github/FUNDING.yml` scaffold (José precisa enrolar em GitHub Sponsors)
- `launch-announcement-drafts.md` (Twitter, LinkedIn, HN) — privado em `.planning/private/`

### Próxima sessão — opções

A — **CARD-016 Item 2** (real SafeWeb TSA wiring) — desbloqueado quando José
    obtiver credencial ICP-Brasil. Implementação ASN.1 da `TimeStampReq` +
    parsing do `TimeStampToken`. ~1.5 dia.

B — **CARD-016 Item 3** (real e-CNPJ PKCS#7 signing) — desbloqueado quando
    José tiver cert A3 + senha. Implementação PKCS#12 → PKCS#7 detached. ~1 dia.

C — **CARD-019** (Compliance Officer Copilot) — chat com retrieval grounded
    no Regulatory Knowledge Graph. Pré-requisito: Bacen RKG MVP (~4 sem) —
    Fase 1 do CARD-016 estendido. Conta como onboard do 1º cliente piloto.

D — **Frontend integration tests** — React Testing Library + MSW para o
    `EvidencePacksView` + `SovereignLlmView`. ~1 dia. Higiênico.

E — **Integration tests com Postgres real** — `services/api/tests/integration/`
    pro verify-chain endpoint + compile end-to-end com migration aplicada.
    ~1 dia. Necessário antes de qualquer piloto produção.

F — **Parar e levar pra revisão jurídica + comercial** — backlog técnico já
    grande pro estágio. Validação externa antes de mais engineering.

**Recomendação:** F (pausar engineering, rodar item-a-item de bloqueio
não-engenharia). Pipeline técnico está estrutural completo; o próximo
risco é dependência interna (jurídica + credenciais), não código.

### Arquivos críticos pra ler em sessão futura
- Esta nota
- `.planning/private/POSITIONING.md` — categoria + pilares + ICP
- `.planning/private/CARD-016-bacen-evidence-engine.md` — roadmap CARD-016
- `.planning/private/FUTURE-MOATS.md` — Items #3 e #4 com gatilhos
- `services/api/app/evidence_pack/` — toda a stack do Engine
- `customizations/compliance/evidence-packs/` — 3 packs
- `services/api/migrations/046_investigation_events_hash_chain.sql`

---

## 2026-05-26 — CARD-013 entregue em produção + CARD-014 backend foundation pronto (não-deployed)

### Objetivo
1. CARD-013 — Benchmark de redução de FP do auto-triage: rodar run publicável, criar componente `/br#benchmark`, doc reprodutibilidade, atualizar pitch.
2. CARD-014 backend foundation — schema + model + ledger hash chain + endpoint + dispatcher email/webhook/sisbacen + detector PII + template ANPD + testes pytest. UI fica pra próxima sessão.

### Status
✅ CARD-013 100% concluído e ao vivo em `https://quarry.12brain.org/br#benchmark`.
✅ CARD-014 backend completo no source — endpoints registrados, model + tests passando — mas **não** deployado: precisa de UI + rebuild imagem Docker + apply migration manual em prod DB (handoff abaixo).

### Entregas em produção (CARD-013)

**1. Benchmark publicável rodado em `customizations/benchmarks/auto_triage_finplay/runs/2026-05-26-bb5f7ccc/`**
- 100 alertas FinPlay BR (60 TP / 30 FP / 10 benign)
- Baseline (regras estáticas): auto-close 7%, false-close 0%
- Quarry auto-triage (gpt-4o-mini via OpenRouter): **auto-close 36%, false-close 0%, precision 100%, recall TP esc 100%, p95 2.5s, custo US$ 0.094/mil alertas**
- Delta +29pp / 5.1× a baseline — **resultado honesto e defensável em due diligence**
- Chave de inferência OpenRouter criada (dedicada, limite $10) — salva em `/root/.api_keys/openrouter-inference.env`. A `/root/.api_keys/openrouter.env` continua sendo a provisioning key (não funciona pra inferência — foi o motivo do 401 do run anterior `f8f772cf`)

**2. Componente novo `apps/web/src/components/landing/br/BenchmarkBR.tsx`**
- Numero gigante 36% em serif (Fraunces), padrão anti-AI design do `/br`
- Tabela comparativa baseline vs Quarry
- Grid de 3 métricas (precisão, recall, custo)
- Hedges humanos: "Dataset é sintético...em piloto rodamos contra os teus alertas reais"
- Link pra metodologia: `/docs/pt-br/benchmark-auto-triage`
- Anchor `#benchmark` adicionado ao NavBR
- Renumeração de seções: 03→04 (custo), 04→05 (deliverables), 05→06 (disqualifier), 06→07 (FAQ)

**3. Doc `docs/pt-br/benchmark-auto-triage.md` (canônico de reprodutibilidade)**
- Resultado público vigente + comandos de reprodução
- Limitações honestas (dataset sintético, 100 alertas é estável mas pouco, provider drift)
- Como rodar contra dataset próprio em piloto
- Curador note: capability `auto-triage-fp-benchmark` é gap real — quando estabilizar, propor INDEX.md

**4. Pitch deck `docs/pt-br/pitch-deck.md` atualizado**
- Slide 03 (a prova) ganhou parágrafo com 36% / 5.1× / zero false-close / custo / link `/br#benchmark`
- Slide 08 (status) adicionou linha "Benchmark interno de auto-triage publicado"
- Slide referências adiciona link pro `/br#benchmark` + metodologia

**5. Deploy seletivo aplicado**
- Sandbox: `/root/sandbox/quarry_2026-05-26-c13c14/` (2.6G, reflink — usar pra rollback até confirmação)
- rsync 8 web files + 2 docs + dir `customizations/benchmarks/`
- `pnpm build` prod: 65/65 páginas, zero erro
- `pm2 restart quarry-web --update-env`
- Smoke 5 rotas (`/`, `/br`, `/opensource`, `/demo-cinematografica`, `/api/health`) todas 200
- `/br` tamanho subiu 76506 → 87494 bytes (+11KB do BenchmarkBR)
- Conteúdo confirmado: id="benchmark", "36%", run "bb5f7ccc"

**6. Memória `project-quarry-positioning` atualizada**
- Adicionado bloco sobre o benchmark medido (CARD-013, 2026-05-26)
- Aviso explícito: "Nunca prometer >80% redução FP sem novo benchmark"

### CARD-014 backend foundation (no source, **não-deployed**)

**Arquivos novos:**
- `services/api/migrations/045_regulatory_communications.sql` — tabela append-only com RLS + hash chain por (tenant, kind) + trigger anti-DELETE + check constraints
- `services/api/app/models/regulatory.py` — SQLAlchemy model RegulatoryCommunication
- `services/api/app/services/regulatory_hash.py` — compute_entry_hash + verify_chain (domain separator `regulatory-comm-v1`, distinto do audit-log)
- `services/api/app/services/regulatory_dispatch.py` — interface RegulatoryDispatcher + 3 impls (EmailDispatcher SMTP, WebhookDispatcher POST, SisbacenDispatcher stub explícito) + factory `get_dispatcher`
- `services/api/app/services/pii_breach_detector.py` — heurística com 3 sinais (PII categories em findings, severity+escala, MITRE exfil techniques) — conservadora deliberada
- `services/api/app/api/v1/endpoints/regulatory.py` — 6 endpoints: POST draft (idempotente), GET list, GET detail, GET chain-verify, POST approve (typed-name check + dispatch), POST expire-sweep + função interna `create_draft_for_case` pra trigger automático
- `apps/web/src/components/demo/anpdReport.ts` — espelha bacenReport.ts mas pra LGPD Art. 48 §1º + IN ANPD 03/2024
- Testes: `test_regulatory_hash.py` (12), `test_regulatory_dispatch.py` (8), `test_pii_breach_detector.py` (9) — **29/29 passando**

**Arquivos modificados:**
- `services/api/app/api/v1/router.py` — `regulatory` adicionado em imports + `include_router(regulatory.router)` após compliance
- `services/api/app/models/__init__.py` — `RegulatoryCommunication` exposto

**Reuso (Regra 11):**
- `audit_hash.py` (pattern + hash chain semantics): reusado conceitualmente, não importado direto (campos diferentes; domain separator distinto pra evitar colisão)
- `bacenReport.ts` (CARD-012): anpdReport.ts é espelho intencional pra manter consistência visual/estrutural
- `compliance.py` endpoint (pattern Pydantic + router): inspiração — não reusado código

### O que NÃO está pronto (handoff explícito pra próxima sessão)

**1. Aplicar migration em prod**
A migration `045_regulatory_communications.sql` precisa ser aplicada manualmente:
```bash
# Em prod (container quarry-demo-api ou DB direto):
docker exec -i quarry-demo-api psql $DATABASE_URL < services/api/migrations/045_regulatory_communications.sql
# OU rebuild a imagem core-api → auto-aplica via app/main.py se ENV != production
```
A função `current_tenant_id()` está em 002_rls.sql e a tabela `aisoc_cases` em 012 — ambas pré-requisitos, já em prod.

**2. Rebuild imagem Docker `quarry-core-api`**
Endpoint `/api/v1/regulatory/*` só responde após:
```bash
cd services/api
docker build -t ghcr.io/beenuar/quarry-core-api:CARD-014-backend .
docker push ghcr.io/beenuar/quarry-core-api:CARD-014-backend
# Update docker-compose.demo.yml tag → docker-compose up -d quarry-demo-api
```

**3. UI completa (próxima sessão grande)**
- `apps/web/src/components/cases/RegulatoryClock.tsx` — cronômetro 24h, alerta vermelho ao cruzar 6h
- Integrar painel "Comunicação Bacen 24h" em `CaseWorkspace.tsx` com 3 estados (draft/submitted/expired)
- Botão "Aprovar e enviar" + diálogo typed-name verification
- Endpoint preview `.md` (reuso direto do bacenReport.ts)
- Wiring do anpdReport.ts no demo cinematográfico (botão paralelo ao Bacen)

**4. Trigger automático no classificador (Sprint+1)**
- Hook em `services/agents/app/agents/auto_triage_agent.py` ou orchestrator: quando verdict=true_positive + severity high/critical, chamar `create_draft_for_case` em paralelo
- Idempotente — chamadas múltiplas não criam drafts duplicados

**5. Hardening da migration**
- UPDATE atualmente livre — quando UI entrar, restringir a `submitted_at`, `dispatch_result`, `expired_at` (campos do approve flow), bloquear mutação de `draft_md` após status='draft'

### Estado pós-sessão

**Git working tree (dirty, sem commit ainda):**
- `M` 9 arquivos (page.tsx, 5 componentes BR, pitch-deck.md, router.py, models/__init__.py)
- `??` 13 novos (BenchmarkBR.tsx, anpdReport.ts, benchmark-auto-triage.md, customizations/benchmarks/, 5 backend services, regulatory endpoint, migration 045, 3 test files, regulatory.py model)
- Os 6 .pdf/.pptx/.mp4 modificados em `docs/pitch/` e `apps/web/public/papers/` são alterações espúrias antigas (provavelmente git-lfs/binário), não desta sessão

**PM2:**
- `quarry-web` online uptime ~13min após restart pós-deploy CARD-013
- `quarry-api` NÃO está em PM2 — roda como container Docker `quarry-demo-api` (image `ghcr.io/beenuar/quarry-core-api:latest`)

**Sandbox:** `/root/sandbox/quarry_2026-05-26-c13c14/` (2.6G) preservado pra rollback até confirmação do José

**Nginx:** SEM mudanças. Continua sem basic_auth (decisão da sessão 2026-05-24)

**Memória atualizada:**
- `project-quarry-positioning` — adicionado bloco "Número de auto-triage medido (CARD-013)"

### Próximas ações sugeridas (prioridade do José)

1. **Validar visualmente** o BenchmarkBR em `https://quarry.12brain.org/br#benchmark` (especial: tipografia 36%, tabela, hedges humanos). Aprovar ou ajustar.
2. **Commit CARD-013 + CARD-014 backend** (mensagem sugerida em duas commits separadas).
3. **Decidir quando rodar migration 045 em prod** (pode esperar até UI estar pronta).
4. **Planejar sessão CARD-014 UI** — 4-5 dias de trabalho frontend (RegulatoryClock + CaseWorkspace integration + typed-name dialog + E2E).
5. **Planejar CARD-015** (Mac Mini sovereign appliance) ou outro card do SPRINT-FINTECH-BR-2026-06.

---

## 2026-05-24 — CARD-012 entregue + auditoria do pitch + Sprint Fintech BR 2026-06 planejado

### Objetivo
1. Remover basic auth de `https://quarry.12brain.org` para fase de testes abertos.
2. Entregar CARD-012 — relatório regulatório Bacen 24h auto-gerado no demo.
3. Auditar relatório técnico/comercial (CEO/CTO) contra código real e propor caminho.
4. Abrir cards e planejar Sprint Fintech BR 2026-06.

### Status
✅ Tudo concluído em produção (auth + CARD-012) e em planejamento (3 cards + sprint doc + ROADMAP atualizado).

### Entregas em produção

**1. Basic auth removida de `https://quarry.12brain.org`**
- Editado `/etc/nginx/sites-available/quarry.12brain.org` (comentadas linhas 28-29 `auth_basic*`)
- Backup em `/etc/nginx/sites-available/quarry.12brain.org.bak-2026-05-23-noauth`
- `htpasswd` mantido intacto em `/etc/nginx/.htpasswd-quarry`
- `robots.txt` + `X-Robots-Tag: noindex, nofollow, noarchive` permanecem → não vai pro Google
- Smoke 4 rotas: `/`, `/br`, `/opensource`, `/demo-cinematografica`, `/api/health`, `/robots.txt` todas 200 sem auth
- Reativação: `cp .bak-2026-05-23-noauth → quarry.12brain.org && systemctl reload nginx`

**2. CARD-012 — Comunicação Bacen 24h auto-gerada no demo**
- Novo `apps/web/src/components/demo/bacenReport.ts` — gerador puro (160 linhas), zero deps
- Novo `apps/web/src/components/demo/bacenReport.test.ts` — 10 testes vitest
- Update `apps/web/src/components/demo/CinematicPixDemo.tsx` — botão "Baixar comunicação (.md)" na seção "Final reveal" quando `state.reportReady=true`
- 14/14 tests verdes (4 cinematicScenario + 10 bacenReport)
- Build sandbox/prod: 65 páginas, zero erro
- Validação Playwright sandbox + prod: download dispara, arquivo `bacen-24h-YYYYMMDD-HHmm.md` (~5.5KB), 8 content checks (header, Res. BCB 85/2021 Art. 9, LGPD, IN BCB 314, BRL, 5 artefatos com `[x]`, tabelas escapadas)
- Deploy: rsync seletivo (3 arquivos) → `pnpm build` prod → `pm2 restart quarry-web` (~3s downtime)
- Live em `https://quarry.12brain.org/demo-cinematografica` (fase complete = botão amarelo aparece)

### Auditoria do relatório técnico/comercial CEO/CTO

Recebi documento "Relatorio_Tecnico_Estrategico_Quarry.pdf" do José para validar contra código real. Veredicto: parcialmente fiel, com 5 claims que furam em due diligence técnica.

**Confere ✅:** air-gapped/Ollama, self-host/VPC, multiagent LangGraph, auto-triage, response actions (block_ip/isolate_host com gate), cadeia probatória CARD-011+CARD-012, MIT-licensed.

**Diverge ❌:**
- 🔴 "Zero exfiltration / LLM 100% local" — só vale em air-gap; default usa OpenAI/Anthropic via `llm_resolver.py`
- 🔴 "4 agentes" — código tem 9; workflow orquestra 5
- 🔴 "Pay-per-incident" — não existe; modelo é per-ingest/assinatura
- 🟠 "Resposta autônoma" — gate humano HMAC ChatOps (decisão técnica correta, exagero do doc)
- 🟠 ">80% FP reduction" — sem benchmark interno
- 🟡 "Brasil e EUA" — foco real é só BR fintech

Recomendação ao José: **mix** — descartar claims perigosos (LLM local default, pay-per-incident, resposta autônoma, EUA), construir o que vira moat (benchmark FP, Bacen real, sovereign LLM opcional), reorganizar narrativa onde só falta copy.

### Cards abertos para Sprint Fintech BR 2026-06

Arquivos novos em `docs/pt-br/`:
- `CARD-013-benchmark-fp-reduction.md` — benchmark reproduzível auto-triage vs baseline, ~3.5d
- `CARD-014-auto-bacen-24h-real.md` — cronômetro 24h + envio com gate humano + ledger + ANPD, ~10-12d
- `CARD-015-mac-mini-sovereign-appliance.md` — Sovereign LLM 3 modalidades opcionais (A: Mac Mini físico, B: VPS Llama dedicada, C: BYOK cloud default), ~16-18d + R$ 18k CAPEX + R$ 800/mês VPS + R$ 5-10k jurídico
- `SPRINT-FINTECH-BR-2026-06.md` — narrativa, ordem (13 → 14 → 15), gates de qualidade, parking lot 016-022

ROADMAP.md ganhou bloco no topo apontando pro novo sprint, sem apagar histórico v4-v8.

### Mac Mini + VPS Llama (decisão estratégica)

José incorporou no CARD-015 que **as modalidades A (Mac Mini) e B (VPS Llama) são opcionais** — não substituem o BYOK cloud default (Modalidade C). Cliente escolhe no onboarding por perfil:
- Fintech com sala-cofre + IPO/M&A → Modalidade A (soberania física + lógica, R$ 18k CAPEX)
- Fintech Seed/A sem espaço físico → Modalidade B (soberania lógica, R$ 320-3.500/mês OPEX)
- Sem preocupação de soberania → Modalidade C (default existente, sem mudança)

Isso resolve o paradoxo "SOC econômico + zero exfiltration" de forma honesta. Mac Mini M4 Pro 64GB rodando MLX com Qwen 14B Q4 entrega ~30 tok/s — sustenta ~500 alertas/dia (fintech Seed/A típica).

### Estado pós-deploy
- Git: working tree DIRTY (sem commit ainda)
  - 6 modificados (CARD-009/011 + CARD-012 + ROADMAP)
  - novos: `apps/web/src/app/br/`, `home-pt/`, `opensource/`, `bacenReport*`, `.planning/`, `docs/pt-br/CARD-013-15*` + `SPRINT-FINTECH-BR-2026-06.md`, 4 dirs `artifacts/*`, backup `page.tsx.bak-2026-05-23`
- Sandboxes: `/root/sandbox/quarry_2026-05-23-home/` (1.4GB) + `/root/sandbox/quarry_2026-05-23-card012/` (300MB) preservados pra rollback até confirmação
- PM2 `quarry-web` online (último restart ~00:55 BRT 2026-05-24 pós-CARD-012)
- Nginx: SEM basic_auth (htpasswd preservado pra reativar)
- Demo containers Docker (api/agents/realtime/ingest): inalterados

### Próxima sessão — recomendações em ordem

1. **Commit do estado atual** (4 entregas + 3 cards + sprint doc + ROADMAP). Hoje tudo está em working tree.
2. **Limpar sandboxes** (1.7GB) após confirmação de que prod tá sólido.
3. **Iniciar CARD-013** (benchmark FP). Sem ele, pitch atualizado fica sem dado central.
4. Discutir CAPEX Mac Mini (~R$ 18k) ANTES de iniciar Fase 2 do CARD-015 — pode ficar pra julho se necessário.
5. (Opcional) Reescrever versão revisada do "Relatorio_Tecnico_Estrategico_Quarry" em `docs/pt-br/` corrigindo os 5 claims, pronta pra próxima reunião CEO/CTO.

### Gotchas registrados

- **Turbopack rejeita symlink absoluto fora do project root** — em sandbox, não tente `ln -s` do `node_modules`. Use `pnpm install` (cache global torna isso ~4s).
- **Nginx rate limit `quarry_html`** continua ativo (defesa). Playwright em paralelo precisa abortar `**/*_rsc=*` antes de `goto`. Test scripts já incorporam.
- **Script Playwright em /tmp falha** com `ERR_MODULE_NOT_FOUND` — Node ESM resolver não busca node_modules da pwd. Copiar pra `/root/openclaw/` (que tem playwright) resolve.
- **`pnpm start` no quarry tem `-p 3000` hardcoded** — para outros portos use `npx next start -p XXXX`.

### Artefatos
- `/tmp/card012-evidence/` — sandbox screenshots + `.md` baixado
- `/tmp/card012-prod-evidence/` — prod screenshots + `.md` baixado
- `/tmp/quarry-sandbox-card012.log` — log do servidor sandbox
- Cards: `docs/pt-br/CARD-013/014/015*.md` + `SPRINT-FINTECH-BR-2026-06.md`

---

## 2026-05-23 (parte 3) — Home institucional 12Brain (`/` PT-BR) ENTREGUE

### Objetivo
Resolver lacuna identificada no teste de usabilidade desta sessão: a home `/` era a OSS herdada do AiSOC (dark tech, inglês, 16 seções), não falava da empresa 12Brain e não posicionava o Quarry comercialmente. José pediu "fazer a página inicial que fala da empresa e do produto".

### Status
✅ DEPLOY EM PRODUÇÃO. Live em `https://quarry.12brain.org/`. Home OSS preservada em `https://quarry.12brain.org/opensource`.

### O que foi feito

**Rota `/` substituída por home institucional PT-BR (dark tech):**
- Novo `apps/web/src/app/page.tsx` (90 linhas) com metadata PT-BR, JSON-LD `Organization` apontando 12Brain Solutions LLC + endereço Coconut Creek FL + contato@12brain.org.
- Novo `apps/web/src/components/landing/home-pt/sections.tsx` (425 linhas) com 10 componentes:
  1. `HomeNav` — 12Brain logo + Produto · Para quem é · Fintechs BR · Open-source · Demo · "Falar com a 12Brain"
  2. `HeroEmpresa` — "Infraestrutura de segurança econômica para fintechs que crescem rápido" + pill "12Brain Solutions LLC · Coconut Creek, FL"
  3. `QuemSomos` — 01 — A empresa: 3 parágrafos + 3 stats (13 produtos · 2021 · MIT)
  4. `ProdutoQuarry` — 02 — O produto: 3 cards (4 agentes · 69 conectores · air-gap)
  5. `ParaQuemE` — 03 — Para quem é: 3 personas (Fintech Seed/A, Dev team enxuto, Quem cansou de MSSP) + "Para quem não é" (disqualifier)
  6. `StatGigante` — 04 — Em números: `R$ 27,40` em 88-160px + comparativo MSSP R$ 180-620
  7. `CaminhoDuplo` — 05 — Por onde começar: 2 cards (A → /br · B → /opensource)
  8. `DemoBanner` — 06 — Ver funcionando: link grande pra /demo-cinematografica
  9. `FaqHome` — 07 — 5 perguntas comerciais (gratuito? cloud próprio? mantenedor? e se a 12Brain sumir? contato?)
  10. `FooterHome` — Footer com 12Brain Solutions LLC, contato@12brain.org, links produto/empresa/código

**Home OSS preservada em `/opensource`:**
- Movido `apps/web/src/app/page.tsx` → `apps/web/src/app/opensource/page.tsx` (16 seções intactas, dark, inglês)
- Canonical atualizado `/` → `/opensource`
- Backup do prod salvo em `apps/web/src/app/page.tsx.bak-2026-05-23`

### Processo (Regra Zero + Regra 5 + Regra 6)
1. Teste de usabilidade Playwright em prod identificou gap (home OSS sem identidade empresa/produto comercial)
2. Plano de 10 seções apresentado e aprovado pelo José
3. Sandbox `/root/sandbox/quarry_2026-05-23-home/` criado via rsync (sem node_modules/.next/.git)
4. Build sandbox: `pnpm install` + `pnpm build` — 64 páginas geradas, zero erro
5. Servidor sandbox em `next start -p 3033`, Playwright validou desktop+mobile, CTAs (`/br`, `/opensource`), FAQ accordion
6. Aprovação explícita do José
7. Deploy seletivo: cp dos 3 arquivos (page.tsx, opensource/page.tsx, home-pt/sections.tsx) para prod
8. `pnpm build` em prod + `pm2 restart quarry-web` (downtime ~3s)
9. Smoke test local (4 rotas, 200 OK) + público via basic auth (4 rotas, 200 OK)
10. Screenshot final em produção confirma renderização correta (1 H1 + 7 H2s exatamente como projetado)

### Smoke test pós-deploy (Regra de Ouro — Zero Deploy sem Teste Real)

**Local 127.0.0.1:3014:**
- `/` → 200 (30ms)
- `/opensource` → 200 (12ms)
- `/br` → 200 (9ms)
- `/demo-cinematografica` → 200 (9ms)

**Público `https://quarry.12brain.org` (basic auth `smoke-test`):**
- `/` → 200 (64ms)
- `/opensource` → 200 (68ms)
- `/br` → 200 (72ms)
- `/demo-cinematografica` → 200 (54ms)

**Keywords na nova `/` em produção:**
| keyword | count |
|---|---|
| 12Brain Solutions | 15 |
| Coconut Creek | 6 |
| Quarry | 62 |
| fintech | 20 |
| BACEN | 10 |
| MSSP | 15 |
| R$ 27,40 | 2 |
| Conhecer o Quarry | 1 |
| Sou fintech BR | 1 |
| Quero auto-hospedar | 1 |
| contato@12brain.org | 5 |
| Falar com a 12Brain | 2 |
| MIT-licensed | 11 |
| Open-source | 5 |

**Keywords em `/opensource` (home OSS preservada):**
| keyword | count |
|---|---|
| Quarry | 129 |
| open-source | 19 |
| 69 connector | 9 |
| agent | 65 |
| MIT | 36 |

### Achados do teste de usabilidade pré-deploy (ainda válidos)
| Sev | Página | Issue | Status |
|---|---|---|---|
| 🔴 P0 | `/` mobile | Nginx 503 rate limit `quarry_html` em prefetch RSC paralelo | **Conhecido**, mitigação: bloquear `*?_rsc=*` em testes Playwright |
| 🟠 P1 | `/br` mobile | Scroll horizontal mínimo | **Não corrigido nesta entrega** — ticket aberto |
| 🟡 P2 | `/demo` | 2 H1s na mesma página | **Não corrigido nesta entrega** |
| 🟡 P2 | mobile | Tap targets <40px no nav OSS | **Resolvido na nova HomeNav** (hamburger 44×44) |

### Artefatos
- `/root/projetos/quarry/artifacts/usability-2026-05-23/` — screenshots desktop+mobile sandbox + prod, report.json, scripts Playwright
- `/root/sandbox/quarry_2026-05-23-home/` — sandbox preservado pra rollback até confirmação
- Backup prod em `apps/web/src/app/page.tsx.bak-2026-05-23`

### Gotcha registrado
Nginx em `quarry.12brain.org` tem rate limit zone `quarry_html`. Playwright em paralelo (prefetch RSC `?_rsc=...`) dispara 503 mesmo quando rotas individuais funcionam. **Mitigação em testes**: `page.route('**/*?_rsc=*', r => r.abort())` antes do `goto`.

### Próximas opções
- Liberar `robots.txt` (remover Disallow: /) quando José decidir abrir SEO
- Considerar mover home OSS pra `/en` (i18n) ou rotear por Accept-Language header
- Validar stat `R$ 27,40` com dado real de benchmark interno (hoje é placeholder também na /br)
- Fix do scroll horizontal mobile na /br (issue P1 aberto)
- Foto institucional do José na seção `QuemSomos` (decidiu manter só texto editorial nesta entrega)

---

## 2026-05-23 (parte 2) — CARD-009 (landing /br) + CARD-011 (overlay regulatório) ENTREGUES

### Objetivo
Fechar o gap entre demo (forte) e landing (genérica) identificado na parte 1 desta sessão. Criar `/br` dedicado fintech BR + amarrar o demo aos artefatos regulatórios Bacen.

### Status
✅ DEPLOY EM PRODUÇÃO. Live em `https://quarry.12brain.org/br` e `https://quarry.12brain.org/demo-cinematografica`.

### O que foi feito

**CARD-009 — Landing fintech BR (coexistência com OSS global):**
- Nova rota `apps/web/src/app/br/page.tsx` (○ Static, gerada em build time)
- 8 componentes novos em `apps/web/src/components/landing/br/`:
  `NavBR`, `HeroBR`, `BacenChecklistBR`, `CostComparisonBR`,
  `RegulatoryDeliverablesBR`, `DisqualifierBR`, `FaqBR`, `FooterBR`
- Design segue `/root/RULES-anti-ai-design.md`: Fraunces+Inter mix, bg
  off-white quente `#f7f4ef`, itálico terra-cota em headline, layout 12-col
  assimétrico, eyebrow `01 — proporção`, stat gigante `R$ 27,40` em 120-160px,
  disqualifier section ("Para quem isso não é"), soft CTAs ("ver a plataforma →"),
  tabela dry MSSP vs Quarry, FAQ editorial sem cards repetidos.
- Link discreto `Para fintechs BR` adicionado ao StickyNav global (1 linha).
- Fraunces carregada via `next/font/google` apenas na rota /br.
- `tailwind.config.ts` ganhou `serif: ['var(--font-fraunces)', 'Georgia', ...]`
  (additive — não afeta páginas sem variable injetada).
- Home global `/` permaneceu intacta (16 seções OSS, zero risco).

**CARD-011 — Overlay regulatório no demo cinematográfico:**
- `cinematicScenario.ts`: novo tipo `DemoRegulatoryArtifact` +
  const `REGULATORY_ARTIFACTS` com 5 artefatos timed:
  - s=11 — Res. BCB 85/2021 Art. 3/4 — PSC em execução
  - s=50 — Res. BCB 85/2021 Art. 8 — Registro de incidente relevante
  - s=105 — LGPD Art. 48/50 — Cadeia probatória arquivada
  - s=190 — Res. BCB 85/2021 Art. 9 — Relógio de comunicação 24h ligado
  - s=250 — IN BCB 314 — Evidência arquivada como teste periódico
- `getDemoState()` agora retorna `visibleRegulatoryArtifacts` + `activeRegulatoryArtifact`
- `CinematicPixDemo.tsx`: novo `<section data-testid="regulatory-overlay">`
  entre o hero brief e a timeline de fases — painel âmbar gradient com badge
  "Regulação ativa", título do artifact corrente, detalhe pt-BR, e lateral
  com checklist dos 5 artefatos (verde quando satisfeito).
- Lucide icons: `Landmark` e `Scale` adicionados ao import.
- Teste novo em `cinematicScenario.test.ts`: valida cardinalidade ≥5, estado
  inicial vazio, estado final completo, e que toda norma cita `Res.`/`IN BCB`/`LGPD`.

### Processo (Regra Zero + Regra 5 + Regra 6)
1. Mapeamento de impacto: listei deps + leitura de RULES-anti-ai-design.md
2. Sandbox em `/root/sandbox/quarry_2026-05-23` (rsync sem node_modules/.next/git)
3. Implementação completa no sandbox
4. `pnpm test` no scenario — 4/4 passando (3 originais + 1 novo)
5. `pnpm build` no sandbox — 64 páginas, zero erro
6. `next start -p 3019` no sandbox + Playwright validando visualmente
7. Aprovação explícita do José antes de tocar em prod
8. rsync seletivo sandbox → prod (apenas arquivos fonte alterados)
9. `pnpm build` no prod, `pm2 restart quarry-web` (downtime ~3s)
10. Smoke test público com Playwright (basic auth `smoke-test`)

### Smoke test pós-deploy (Regra de Ouro — Zero Deploy sem Teste Real)

**Local 127.0.0.1:3014:**
- `/br` → 200 (4ms)
- `/demo-cinematografica` → 200

**Público `https://quarry.12brain.org` (via basic auth):**
- `/br` → 200 (45ms)
- `/demo-cinematografica` → 200, overlay element `[data-testid=regulatory-overlay]` presente
- `/` (home) → link "Para fintechs BR" presente no nav
- `/robots.txt` → `Disallow: /` mantido (noindex correto)

**Cobertura de keywords na `/br` em produção:**
| keyword | count |
|---|---|
| Bacen | 10 |
| fintech | 16 |
| BCB 85 | 7 |
| IN BCB | 3 |
| LGPD | 2 |
| Pix | 9 |
| Series Seed | 2 |
| cadeia probatória | 2 |
| comunicação ao Bacen | 2 |
| em até 24 horas | 1 |

**Cobertura na `/demo-cinematografica` em produção (após overlay):**
| keyword | count (antes) | count (depois) |
|---|---|---|
| Res. BCB 85 | 0 | 3 |
| IN BCB 314 | 0 | 2 |
| LGPD | 0 | 1 |
| Política de Segurança | 0 | 1 |
| Cadeia probatória | 0 | 1 |
| Bacen | 1 | 2 |

### Gotcha registrado
Nginx em `quarry.12brain.org` tem rate limit zone `quarry_html`. Playwright
em paralelo (prefetch RSC `?_rsc=...`) dispara 503 mesmo com /br funcionando.
Smoke test deve rotear `**/*_rsc=*` para `route.abort()` ou aguardar 10s
entre páginas. Não é bug — é defesa.

### Estado pós-deploy
- Git: working tree DIRTY (sem commit ainda — usuário decide)
- Sandbox preservada em `/root/sandbox/quarry_2026-05-23` (1.4GB)
- PM2 `quarry-web` online, restartado às ~22:38 UTC
- Containers Docker do demo (api/agents/realtime/ingest): inalterados
- Nginx + SSL + htpasswd: inalterados
- 6 usuários htpasswd ativos + `smoke-test` (criado nesta sessão)

### Arquivos novos/alterados
| arquivo | tipo |
|---|---|
| `apps/web/src/app/br/page.tsx` | novo |
| `apps/web/src/components/landing/br/NavBR.tsx` | novo |
| `apps/web/src/components/landing/br/HeroBR.tsx` | novo |
| `apps/web/src/components/landing/br/BacenChecklistBR.tsx` | novo |
| `apps/web/src/components/landing/br/CostComparisonBR.tsx` | novo |
| `apps/web/src/components/landing/br/RegulatoryDeliverablesBR.tsx` | novo |
| `apps/web/src/components/landing/br/DisqualifierBR.tsx` | novo |
| `apps/web/src/components/landing/br/FaqBR.tsx` | novo |
| `apps/web/src/components/landing/br/FooterBR.tsx` | novo |
| `apps/web/src/components/landing/sections/StickyNav.tsx` | +1 link `/br` |
| `apps/web/src/components/demo/CinematicPixDemo.tsx` | +overlay section + 2 icons |
| `apps/web/src/components/demo/cinematicScenario.ts` | +REGULATORY_ARTIFACTS |
| `apps/web/src/components/demo/cinematicScenario.test.ts` | +1 test bloco |
| `apps/web/tailwind.config.ts` | +serif fontFamily |
| `.planning/SESSION-NOTES.md` | atualizado |

### Próxima sessão — opções
A — **Pricing fintech BR concreto** (CARD-010): definir números reais
    (não mais "R$ 2,4k – 9,8k a definir"), publicar tabela em `/br#custo`.
B — **CARD-012: Relatório regulatório Bacen auto-gerado** — gerar arquivo
    .pdf/.md no Case Workspace que sirva como comunicação imediata em 24h.
C — **Entregar credencial p/ 1º revisor externo de mercado** (prospect-demo-1)
    com onboarding email pt-BR linkando direto `/br` e `/demo-cinematografica`.
D — **DNS quarry.com.br dedicado apontando direto pra /br** (estratégia
    long-term — segrega audiência BR sem competir com SEO OSS internacional).

Recomendação: **C primeiro** (validar que o material atual converte conversa
em interesse antes de evoluir features). Tempo: 1 prospect, 1 conversa, ajuste
baseado em feedback real.

### Riscos novos identificados
- `R$ 2,4k – 9,8k a definir` no /br é texto provisório — precisa virar pricing
  real antes de mandar pra prospect, senão soa amador.
- Memória "project-quarry-positioning" salva a tese central — manter sincronizada
  se o pitch mudar.
- Sandbox de 1.4GB acumula — apagar após confirmação do José (Regra 6).

---

## 2026-05-23 (parte 1) — Smoke test do demo público + reforço de posicionamento

### Objetivo
Continuar de onde parou (último commit `8ba5262a` em 16/05): validar end-to-end que `https://quarry.12brain.org` entrega o demo cinematográfico correto, e checar se a comunicação pública carrega o posicionamento estratégico (SOC econômico BACEN-compliant para fintechs iniciantes).

### Status
✅ CONCLUÍDO — smoke test passou; gaps de posicionamento identificados.

### O que foi feito
1. Diagnóstico de estado: working tree clean, 4 containers UP 3h (`quarry-demo-api`, `quarry-demo-agents`, `quarry-demo-realtime`, `quarry-ingest`), nginx + SSL + basic-auth OK.
2. Criado usuário htpasswd `smoke-test` em `/etc/nginx/.htpasswd-quarry`, senha em `/root/.quarry-smoke-pass` (chmod 600).
3. Smoke test HTTP (curl) — todos endpoints 200, latência 60-450ms:
   - `/` 200 (450ms)
   - `/demo-cinematografica` 200 (63ms)
   - `/api/health` 200 (103ms)
   - `/robots.txt` 200 (noindex correto)
   - sem auth → 401 (gate funcionando)
4. Smoke test E2E Playwright em `?speed=fast&record=1`:
   - Navigation 1.4s
   - Demo full flow ready em 13.5s (modo fast 18x; real-time ~4m30s confere com `cinematicScenario.ts`)
   - Marker `[data-demo-ready="true"]` dispara corretamente
   - Artefatos: `artifacts/smoke-test-2026-05-23/` (3 PNGs + texto + report.json + console.log)

### Cobertura de posicionamento — achados

**Demo cinematográfica (página `/demo-cinematografica`):** ✅ ALINHADA com fintech BR

| Sinal | Status |
|---|---|
| Painel "Cost vs Human Analyst" com números (R$ 27,40 IA vs CUSTO HUMANO) | ✅ presente |
| Cenário FinPlay Pagamentos, R$ 1,84 mi em fraude Pix organizada | ✅ presente |
| 14 menções a "Pix", queries em `pix.transferências`, SIM swap | ✅ presente |
| "Open Finance Bacen" citado como fonte de dado | ✅ menção única |
| Dataset sintético FinPlay com 500 transações suspeitas | ✅ presente |
| Compliance referenciada | ✅ presente |

**Landing pública (página `/`):** ❌ DESALINHADA — totalmente OSS-genérica

- Title: `Quarry — open-source AI Security Operations Center`
- Hero: "Detect. Triage. Hunt. Respond. Quarry is the open agentic Security Operations Center."
- Zero menções: BACEN, fintech, Pix, Brasil, Res. BCB 85, LGPD, Open Finance.
- Foco da home: 69 connectors, 6998 detections, MIT, self-host, air-gap, LangGraph/Kafka/Neo4j.

**Conclusão:** quem chega na home não vê que Quarry é SOC econômico pra fintech BR. A diferenciação vive **só** dentro do demo (que precisa ser linkado de propósito ou demonstrado em call).

### Gaps acionáveis (em ordem de impacto comercial)

1. **Landing fintech BR** (mais alto impacto pré-vendas).
   - Hero alternativo: "SOC econômico para fintechs BR que precisam passar pela inspeção BACEN sem queimar caixa."
   - Bloco com checklist BACEN coberto (Política de Segurança Cibernética, registro de incidentes, comunicação 24h, controles Res. BCB 85/2021).
   - Comparativo: "MSSP tradicional R$ 80-300k/mês vs Quarry R$ X/mês".
   - Hospedar em `/br` ou trocar `/` dependendo da estratégia (OSS vs comercial BR pode coexistir).
2. **Cenário cinematográfico cita "Open Finance Bacen" mas não amarra a obrigação regulatória.** Adicionar overlay/badge "Este incidente exige comunicação ao BACEN em 24h" e "Esta evidência atende Item X da Política de Segurança Cibernética".
3. **Relatório regulatório auto-gerado** (CARD-009 candidato): template de comunicação ao BACEN/CSIRT, evidências formatadas para auditor, mapeamento controle ↔ detecção.
4. **Pricing fintech BR** (CARD-010 candidato): Seed (R$ X), Series A (R$ Y), comparação MSSP enterprise.

### Estado das integrações
- Domínio: `https://quarry.12brain.org` ✅ ativo, SSL Let's Encrypt, basic auth
- Containers: 4 UP, healthy, logs JSON em `/var/log/nginx/quarry.access.json`
- Robots: noindex/nofollow correto
- Git: working tree limpo, commit corrente `8ba5262a`
- Repo remoto: `git@github.com:Josepassinato/quarry.git`

### Riscos / pontos de atenção
- **Posicionamento estratégico (BACEN-econômico fintech BR) não chega ao visitante público da landing.** Demo é forte, mas precisa de motivo pra alguém clicar/pedir acesso.
- Auth basic com 6 usuários (`meta-demo-1/2`, `prospect-demo-1/2`, `internal-demo`, `smoke-test`) — falta rotação documentada, sem registro de qual senha foi pra qual revisor.
- Containers rodando sem PM2 (Docker direto via `docker-compose.demo.yml`) — checar restart policy se VPS reboot.
- API expõe `/api/health` (200) mas `/api/v1/health` retorna 404 — confirmar se é só nomenclatura ou se há rota faltando antes de mandar pra revisor técnico.

### Próxima sessão — opções
A — **CARD-009: Landing fintech BR** (mexer em `apps/web/src/app/page.tsx` ou criar `/br`). Alto impacto comercial.
B — **CARD-010: Pricing + comparativo MSSP**. Combina com A.
C — **CARD-011: Overlay regulatório BACEN dentro do demo** (badge "comunicar ao BACEN em 24h", mapeamento Res. BCB 85). Menor escopo.
D — **CARD-012: Relatório regulatório auto-gerado** (template comunicação BACEN/CSIRT). Maior valor técnico.
E — Iniciar ciclo de revisor externo agora com material atual (entregar credencial pra 1º prospect-demo e capturar feedback antes de evoluir).

Recomendação: **A + C juntos** numa sessão — landing posiciona + demo amarra regulação. Vira pitch coerente do clique até a evidência.

### Arquivos críticos pra ler em sessão futura
- Esta nota: `.planning/SESSION-NOTES.md`
- `/root/.claude/projects/-root/memory/project_quarry_positioning.md` (tese central)
- `apps/web/src/components/demo/cinematicScenario.ts` (linhas do roteiro)
- `apps/web/src/app/page.tsx` (landing pra reescrever — provavelmente)
- `docs/operations/storage-and-review-boundary.md` (regras VPS vs GitHub)
- `REVIEW_GUIDE.md` (onboarding de revisor externo)
- `customizations/datasets/br-fintech-generator/` (gerador FinPlay)
- `artifacts/smoke-test-2026-05-23/` (screenshots + json deste smoke)
