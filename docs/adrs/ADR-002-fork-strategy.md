# ADR-002: Estratégia de fork e merge de upstream

**Data:** 2026-05-15
**Status:** ACEITO
**Decisores:** José Passinato (founder, Increase Trainer Inc.) · Claude (assistente técnico)
**Card relacionado:** CARD-003 (fork e setup do Quarry)
**Predecessor:** [ADR-001 — Decisão de fork condicional](ADR-001-fork-aisoc.md)

---

## Contexto

ADR-001 estabeleceu **GO condicional** para forkar AiSOC. As 10 condições não-negociáveis incluíam fixar SHA do upstream, rebrand completo antes de produção, cherry-pick manual de features, monorepo independente. Esta ADR formaliza **como** o fork foi executado e **como** trataremos manutenção contra upstream daqui pra frente.

---

## Decisão

### 1. Tipo de fork: mirror clone para repositório privado novo

**Não usamos o botão "Fork" do GitHub.** Em vez disso:

```bash
git clone --mirror https://github.com/beenuar/AiSOC.git aisoc.git
gh repo create Josepassinato/quarry --private
cd aisoc.git
git push --mirror git@github.com:Josepassinato/quarry.git
```

**Razões:**

- **Privacidade**: GitHub não permite forks privados de repos públicos. Fork tradicional aparece na lista pública de forks do upstream — incompatível com ADR-001 (Cyble tratada como concorrente potencial).
- **Independência**: mirror clone não cria relação de fork no GitHub. Sem "fork-of" badge, sem botão de "sync fork", sem indução a pull passivo.
- **Histórico preservado**: `--mirror` traz todos os branches, tags (v3.0.0, v5.1.0, v7.2.0, v7.3.0, v7.3.1) e refs históricas. Audit trail completo.
- **PR refs rejeitados**: GitHub bloqueia push de `refs/pull/*` (server-managed). Esperado e ignorado.

### 2. Commit fixado como base do fork

- **Upstream:** `github.com/beenuar/AiSOC`
- **SHA:** `28ce9f6bba8d997de04244be963ea3f2c38f0084`
- **Data do commit:** 2026-05-15 16:40:34 +0530
- **Mensagem:** `fix(workspace): unblock pnpm lint + pnpm build, correct exports.types ordering`
- **Data do fork (push final para Quarry):** 2026-05-15

Esta é a base imutável. Toda evolução Quarry-específica vai por cima.

### 3. Visibilidade e ownership

- Repositório `Josepassinato/quarry` — **privado**
- Owner GitHub: Josepassinato (José Passinato)
- Owner legal: Increase Trainer Inc. (EIN 87-1490358, Coconut Creek FL)
- Nenhum colaborador adicional ainda

### 4. Estratégia de merge de upstream

**Política:** cherry-pick manual, nunca pull passivo.

**Rotina prevista:**

1. **Não configurar remote `upstream` por default.** Quem quiser observar upstream faz manual: `git remote add upstream-aisoc https://github.com/beenuar/AiSOC.git && git fetch upstream-aisoc`.
2. **Review trimestral** (ou ad-hoc quando algo crítico aparecer no roadmap do AiSOC). Auditor lê o CHANGELOG.md upstream desde a última review e cataloga: (a) features interessantes, (b) bugfixes que se aplicam ao código herdado intocado, (c) breaking changes a evitar.
3. **Cherry-pick por commit individual.** `git cherry-pick <sha>` no branch Quarry, com:
   - Mensagem original preservada + sufixo `[cherry-pick from aisoc:<sha>]`
   - PR review obrigatório, mesmo solo
   - Atualização do `NOTICE.md` se necessário
4. **Bugfix crítico de segurança** (CVE em deps, falha de auth, etc.) é exceção: pode ser cherry-pick imediato sem aguardar review trimestral, mas com PR retroativo no dia útil seguinte.

**O que NÃO fazer:**

- ❌ `git pull upstream-aisoc main` — nunca
- ❌ Merge de branch upstream inteiro — nunca
- ❌ Submodule de AiSOC — nunca
- ❌ Cherry-pick em massa de "tudo desde a última semana" — incompatível com review humano

### 5. Decisão revisitável em 90 dias

Conforme ADR-001 — em 2026-08-15, reavaliar se faz sentido cadência mais frequente de upstream, condicionado a:

- AiSOC consolidar 2-3 contribuidores externos significativos (não-Cyble, >10 commits cada)
- Versionamento estabilizar (1 major/trimestre, não 5/semana)
- Cyble publicamente endossar AiSOC com modelo de governance formal

Até lá: **isolar e cherry-pick**.

### 6. Branch model Quarry

- **`main`** — protegida (ver seção 7), reflete o que está em produção (quando produção existir)
- **`develop`** — branch de trabalho default, onde features Quarry-specific aterrissam após PR
- **`feat/<scope>-<short-desc>`** — feature branches Quarry, mergem para `develop`
- **`upstream-sync/<yyyy-mm>`** — branches efêmeras pra revisão de cherry-picks de upstream, mergem para `develop` após review
- **`release/v<X.Y.Z>`** — branches de release, mergem para `main` quando estável

**Por enquanto:** apenas `main` existe (herdado). `develop` será criado no próximo card (rebrand) para evitar criar branch vazia agora.

### 7. Branch protection

Aplicar protection rules em `main` e `develop` **quando colaboradores adicionais existirem**. Por ora (1 desenvolvedor solo + Claude), protection criaria fricção sem ganho real — author pode quebrar tudo sozinho mesmo com PR auto-aprovado.

**Trigger pra ativar protection:**
- Quando segundo colaborador humano for adicionado, OU
- Quando primeiro cliente pagante for onboardado (independente de número de colaboradores)

**Regras planejadas (não ativas ainda):**
- `main`: requires PR review, requires status checks (CI + custom validations), no direct push, no force push, no branch deletion
- `develop`: requires PR review, requires status checks; permite admin bypass

### 8. Atribuição e licenciamento

Mantido conforme `LICENSE` (MIT, copyright AiSOC contributors preservado) e [`NOTICE.md`](../../NOTICE.md). Toda redistribuição comercial de Quarry honra:

- MIT do código herdado (cláusula de atribuição)
- DRL-1.1 das regras SigmaHQ (provenance per-rule)
- Apache-2.0 dos demais corpora (MITRE CAR, Splunk, Chronicle)
- LGPL-2.1 do pysigma (linkagem dinâmica — OK para SaaS hosted)

---

## Consequências

### Positivas

- Independência total do calendário e direção do AiSOC
- Sem indução narrativa a pull passivo
- Histórico completo preservado (auditável)
- Privacidade — Cyble não vê nosso código nem que forkamos
- Possibilidade de licenciar diferentemente código novo (proprietário) se em algum momento Quarry deixar de ser MIT

### Negativas (aceitas)

- Carga manual de auditar upstream periodicamente
- Risco de divergir tanto que cherry-pick fica impraticável
- Sem benefício do botão "Sync fork" do GitHub
- Dependências de segurança upstream chegam mais devagar — mitigado pela política de exceção pra CVEs

### Neutras

- Quarry é detectável publicamente como derivação se alguém comparar SHAs/conteúdo, mas atribuição em LICENSE/NOTICE já reconhece isso explicitamente.

---

## Implementação confirmada (2026-05-15)

- ✅ Repositório `Josepassinato/quarry` criado (privado)
- ✅ Mirror push concluído: branches (main + 10 feature branches) e tags (5 releases) preservados
- ✅ Clone local em `/root/projetos/quarry/`
- ✅ README.md em pt-BR criado; README original preservado em `README.AISOC.md`
- ✅ NOTICE.md com atribuições obrigatórias
- ✅ SKILL.md para Claude Code
- ✅ Estrutura `customizations/`, `infrastructure/`, `docs/pt-br/`, `docs/adrs/`
- ✅ ADR-001 copiado para `docs/adrs/ADR-001-fork-aisoc.md`
- ✅ ADR-002 (este documento)
- ⏳ CI custom workflow para `customizations/` — pendente (requer escopo `workflow` no token Git)
- ⏳ GitHub Secrets (ANTHROPIC, XAI, GOOGLE_AI, OPENAI) — aguardando definição de quais chaves usar
- ⏳ Branch protection — adiada até segundo colaborador ou primeiro cliente pagante
- ⏳ Validação funcional Card-002 — kit offline preparado em `docs/pt-br/CARD-002-demo-checklist.md`

---

## Referências

- [ADR-001 — Decisão de fork condicional](ADR-001-fork-aisoc.md)
- [`NOTICE.md`](../../NOTICE.md) — atribuições
- [`README.md`](../../README.md) — entrada Quarry
- [`docs/SKILL.md`](../SKILL.md) — instruções operacionais Claude
- [Upstream AiSOC](https://github.com/beenuar/AiSOC) — referência apenas
