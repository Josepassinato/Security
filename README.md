# Quarry

> Plataforma técnica de SOC para fintech brasileira regulada pelo Bacen.
> Detecção, raciocínio assistido e cadeia probatória citável.

**Status:** em validação técnica · **Versão:** 0.0.0-dev · **Owner:** [Increase Trainer Inc.](https://increasetrainer.com)

---

## O que é Quarry

Quarry é uma plataforma técnica de SOC (Security Operations Center) em desenvolvimento, baseada em fork independente do projeto open-source [AiSOC](https://github.com/beenuar/AiSOC) (commit `28ce9f6b`, MIT). A base técnica entrega:

- **Orquestrador LangGraph** com router paralelo (phishing, identity, cloud, insider)
- **Investigation Ledger** — cada prompt LLM + resposta + ferramentas chamadas, persistido e auditável
- **Eval harness em CI** com 5 suítes deterministicas (MITRE accuracy, alert reduction, investigation completeness, response quality, schema/coverage)
- **MCP server** para integração com Claude Desktop, Cursor, Cody e outros assistentes
- **Detection corpus** multi-fonte (SigmaHQ, MITRE CAR, Splunk Security Content, Chronicle) com provenance per-regra

Sobre essa fundação, Quarry adiciona uma **camada de customizações** em `customizations/`:

- Hunts e regras Sigma calibradas para o ecossistema brasileiro (BACEN, PIX, LGPD)
- Compliance evidence automation para auditorias locais
- Prompts em pt-BR
- Integrações com infraestrutura nacional (em escopo)

---

## Status atual

| Etapa | Status |
|---|---|
| Auditoria técnica do AiSOC ([ADR-001](docs/adrs/ADR-001-fork-aisoc.md)) | ✅ Concluída — recomendação GO condicional |
| Fork (mirror clone privado) — Quarry repo criado ([ADR-002](docs/adrs/ADR-002-fork-strategy.md)) | ✅ Concluído |
| Rebrand AiSOC → Quarry ([ADR-003](docs/adrs/ADR-003-rebrand-strategy.md)) | ✅ Concluído — validação runtime offline pendente |
| Deep-dive do LangGraph orchestrator | ✅ [docs/pt-br/orchestrator-deep-dive.md](docs/pt-br/orchestrator-deep-dive.md) |
| Estratégia customização fintech BR ([ADR-004](docs/adrs/ADR-004-orchestrator-fintech-br.md)) | ✅ Aprovada — implementação por sprints A/B/C |
| Catálogo TTPs BR fintech | ✅ 11 patterns em `customizations/threat-intel/br-fintech/` (PIX/VSH/SEN/ATO/BOL/QR/EWL/MAL) |
| Validação funcional (demo local end-to-end) | ⏳ Pendente — ver `docs/pt-br/CARD-002-demo-checklist.md` |
| Roadmap Quarry independente | ⏳ Próximo card |

> **Rebrand concluído** em commits `dd342d0b` → `e6c9a979` → `cfb83e92`. Logos, workspaces `@quarry/*`, env vars `QUARRY_*`, helm chart, scripts, SDKs e arquivos com `aisoc` no nome — todos renomeados. Atribuições legais (LICENSE, NOTICE, README.AISOC.md, ADR-001/002) preservadas conforme cláusula MIT.

---

## Estrutura do repositório

```
quarry/
├── README.md                      # este arquivo (pt-BR)
├── README.AISOC.md                # README original do AiSOC (preservado integral)
├── LICENSE                        # MIT (herdado do AiSOC, mantido conforme cláusulas)
├── NOTICE.md                      # Atribuições obrigatórias (AiSOC, detection corpora)
│
├── apps/                          # Frontend Next.js (herdado, será rebrand)
├── services/                      # 14 microsserviços Python + Go (herdado)
├── packages/                      # SDKs (herdado)
├── detections/                    # Corpus de regras (herdado, com provenance)
├── playbooks/                     # Playbooks de resposta (herdado)
│
├── customizations/                # ⭐ TUDO QUE É QUARRY-SPECIFIC VAI AQUI
│   ├── detections/                #   Sigma rules customizadas (BR, BACEN, PIX)
│   ├── hunts/                     #   Hunt templates em pt-BR
│   ├── prompts/                   #   Prompts customizados Quarry
│   └── compliance/                #   BACEN, LGPD evidence automation
│
├── infrastructure/                # ⭐ Deploy próprio Quarry
│   ├── vps/                       #   Configs específicas VPS Hostinger
│   └── deploy/                    #   Scripts de deploy
│
└── docs/
    ├── SKILL.md                   # ⭐ Instruções para Claude Code trabalhando no Quarry
    ├── adrs/                      #   Architecture Decision Records
    │   ├── ADR-001-fork-aisoc.md
    │   └── ADR-002-fork-strategy.md
    └── pt-br/                     #   Documentação operacional em português
```

---

## Princípios de design

1. **Customização separada de upstream.** Tudo que é Quarry-specific vive em `customizations/` ou `infrastructure/`. O código herdado não é modificado exceto via cards explícitos de rebrand. Isso permite cherry-pick controlado de melhorias upstream se necessário.

2. **Inglês para código, português para docs operacionais.** Identificadores, comentários inline, mensagens de log, commits convencionais (`feat:`, `fix:`) em inglês. Manuais, runbooks, ADRs, comunicação com clientes em português.

3. **Adversarial agent assumptions.** Operadores humanos podem ser hostis ou comprometidos. Auditoria é design constraint, não feature opcional. Tudo o que o agente faz tem que ser explicável e revertível.

4. **Atribuição rigorosa.** [`NOTICE.md`](NOTICE.md) lista AiSOC + cada corpus de detecção (SigmaHQ/DRL-1.1, MITRE CAR/Apache, Splunk/Apache, Chronicle/Apache). Sistema de provenance herdado preserva linhagem por regra.

5. **Não competir com AiSOC em features genéricas.** Quarry diferencia em vertical brasileiro (compliance BACEN/LGPD, hunts pt-BR, integrações nacionais), não em re-implementar o que upstream já entrega.

---

## Como contribuir

Por enquanto Quarry é privado e desenvolvido por Increase Trainer Inc. Contribuição externa não está aberta. Quando abrir, este README será atualizado.

---

## Links importantes

- 📘 [ADR-001 — Decisão de fork](docs/adrs/ADR-001-fork-aisoc.md) — análise da decisão GO condicional
- 📘 [ADR-002 — Estratégia de fork e upstream](docs/adrs/ADR-002-fork-strategy.md) — como tratamos merges de cima
- 🧭 [Fronteira GitHub/VPS/artefatos](docs/operations/storage-and-review-boundary.md) — o que fica versionado e o que fica operacional
- 🔎 [REVIEW_GUIDE.md](REVIEW_GUIDE.md) — guia para revisão externa do código
- 🤖 [SKILL.md](docs/SKILL.md) — instruções para Claude Code trabalhar neste repo
- 📜 [README.AISOC.md](README.AISOC.md) — README original do AiSOC (referência técnica preservada)
- 📜 [LICENSE](LICENSE) — MIT
- 📜 [NOTICE.md](NOTICE.md) — atribuições obrigatórias

---

_Forked from AiSOC commit `28ce9f6bba8d997de04244be963ea3f2c38f0084` em 2026-05-15._
