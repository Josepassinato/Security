# Plano de Execução — Fintech BR (Quarry, 2026-06 a 2026-08)

**Versão:** 1.0 (2026-05-24)
**Janela:** 6-8 semanas (~final de julho 2026)
**Objetivo macro:** transformar o "Relatorio_Tecnico_Estrategico_Quarry.pdf" inteiro em verdade verificável em produto + reescrever a versão definitiva (v2) sem claims que furam em due diligence técnica.
**Critério de sucesso final:** um CTO de fintech regulada lê o doc v2, valida cada claim contra `quarry.12brain.org`, e não acha nenhuma divergência ou exagero.

---

## Por que este plano existe

A auditoria de 2026-05-24 do documento original identificou 5 claims que furam em due diligence técnica:

| Claim do doc | Status atual no produto |
|---|---|
| ">80% redução FP" | ❌ sem benchmark interno |
| "Zero exfiltration / LLM 100% local" | ❌ vale só em modo air-gap; default é cloud BYOK |
| "Compliance automática Bacen" | 🟡 rascunho .md apenas no demo (CARD-012 entregue 2026-05-24) |
| "Resposta autônoma" | 🟠 produto tem gate humano (decisão correta) |
| "Pay-per-incident" | ❌ não existe; modelo é per-ingest/assinatura |
| "Brasil e EUA" | ❌ foco real é só BR fintech regulada |

Sem fechar isso, o pitch quebra na primeira sessão técnica. **Este plano fecha os 3 gaps viáveis, descarta os 2 perigosos, e reescreve a narrativa.**

---

## Estrutura de prioridades

### P0 — bloqueiam pitch defensável (Sprint Fintech BR 2026-06, ~4 semanas)

1. **CARD-013** — Benchmark FP reduction (~3.5d)
2. **CARD-014** — Auto-comunicação Bacen 24h real (~10-12d)
3. **CARD-015** — Sovereign LLM 3 modalidades opcionais (~16-18d + CAPEX)
4. **Reescrita do documento v2** (~2d, gera novo deliverable comercial)

### P1 — fechar moats regulatórios (Sprint 2026-07a, ~2 semanas)

5. **CARD-016** — Notificação titulares de dados (LGPD Art. 48 caput) (~5d)
6. **CARD-017** — Cross-mapping SOC2 / ISO27001 controles (~5d)
7. **CARD-018** — Pricing fintech BR concreto (~3d, substitui placeholder)

### P2 — comercial e operacional (Sprint 2026-07b, ~2 semanas)

8. **CARD-019** — Onboarding 1º revisor externo (prospect-demo-1) (~3d)
9. **CARD-020** — Domínio `quarry.com.br` dedicado para `/br` (~1d)
10. **Ajustes copy do pitch** ("4 agentes" → "5 orquestrados + 4 especialistas"; "resposta autônoma" → "assistida com gate") (~1d)

### P3 — escala (parking lot, sob demanda)

11. **CARD-021** — Sovereign Appliance pré-instalado pra venda (após 3+ clientes pagantes)
12. **CARD-022** — Sovereign Linux + GPU alternativa Modalidade A
13. **CARD-099** — Expansão EUA (não antes de 2027)

---

## Roadmap semanal

```
Semana 1 (já: 2026-05-23/24)                                  ✅ COMPLETO
  ├─ Basic auth removida                                       ✅
  ├─ CARD-012: rascunho Bacen 24h .md no demo                  ✅
  ├─ Auditoria pitch vs código                                 ✅
  ├─ CARDs 013/014/015 + Sprint doc abertos                    ✅
  └─ Commits + push remoto                                     ✅

Semana 2 (2026-06-02 a 2026-06-08)                            P0
  ├─ CARD-013 Benchmark FP (~3.5d)                            [Claude]
  │  ├─ Curador: consult-catalog benchmark eval
  │  ├─ Schema ground-truth no FinPlay generator
  │  ├─ Script Python + baseline regra-estática
  │  ├─ Componente /br#benchmark
  │  └─ Doc reproduzibilidade
  ├─ Reescrita do documento v2 (~2d)                          [Claude]
  │  ├─ Substituir 80% por número real do CARD-013
  │  ├─ Trocar "100% local" por "3 modalidades opcionais"
  │  ├─ Trocar "pay-per-incident" por "ingest/SLA-credit"
  │  ├─ Trocar "resposta autônoma" por "assistida com gate"
  │  ├─ Tirar "EUA"; focar BR
  │  └─ Salvar em docs/pt-br/Relatorio_Tecnico_Estrategico_Quarry_v2.md
  └─ Decisão José: CAPEX Mac Mini (~R$ 18k) — vai/não-vai?

Semana 3 (2026-06-09 a 2026-06-15)                            P0
  └─ CARD-014 Fase 1 (~5d)                                    [Claude]
     ├─ Schema regulatory_communications + migração
     ├─ Endpoint CRUD + trigger automático
     └─ Hash-chain ledger (cadeia probatória)

Semana 4 (2026-06-16 a 2026-06-22)                            P0
  ├─ CARD-014 Fase 2 (~5d)                                    [Claude]
  │  ├─ Adapter envio e-mail (Zoho SMTP reuso) + webhook
  │  ├─ Detector PII breach + ANPD template
  │  └─ Painel RegulatoryClock no CaseWorkspace
  └─ CARD-015 Fase 1 paralela (~7d) — VPS Llama               [Claude]
     ├─ Provisionar Hetzner AX42 (~R$ 800/mês)
     ├─ Script install-vps-linux.sh
     ├─ Adapter sovereign-vps no resolver
     └─ Benchmark Modalidade B vs C

Semana 5 (2026-06-23 a 2026-06-29)                            P0
  ├─ CARD-014 Fase 3 (~2d) — fechamento                       [Claude]
  │  ├─ Diálogo aprovação typed-name 1-clique
  │  ├─ E2E tests + smoke público
  │  └─ Doc PT-BR auto-bacen-24h
  └─ CARD-015 Fase 2 (~7d) — Mac Mini, SE aprovado            [Claude]
     ├─ Comprar Mac Mini M4 Pro 64GB
     ├─ Script install-mac.sh (MLX + Qwen 14B)
     └─ Adapter sovereign-mac + benchmark

Semana 6 (2026-06-30 a 2026-07-06)                            P0
  ├─ CARD-015 Fase 3 (~3d) — conformidade + comercial         [Claude]
  │  ├─ Doc conformidade Bacen (rascunho + revisão jurídica)
  │  ├─ Landing /br/sovereign-llm com seletor 3 modalidades
  │  └─ Pitch deck atualizado: 2 slides A físico, B lógico
  └─ Marco 1: Sprint Fintech BR 2026-06 ENCERRADO            🎯
     ├─ Doc v2 publicado
     ├─ Demo gera Bacen 24h + envia + ledger
     ├─ Modalidades A e B documentadas, B em prod
     └─ Pitch defensável contra qualquer CTO técnico

Semana 7 (2026-07-07 a 2026-07-13)                            P1
  ├─ CARD-016 Notificação titulares LGPD (~5d)                [Claude]
  └─ CARD-018 Pricing fintech BR concreto (~3d)               [José + Claude]
     ├─ José define números base (margem, custo Mac Mini etc)
     ├─ Reuso stripe-credits do @12brain/auth-billing
     └─ Substituir placeholder R$ 2,4k–9,8k no /br

Semana 8 (2026-07-14 a 2026-07-20)                            P1+P2
  ├─ CARD-017 SOC2/ISO27001 cross-mapping (~5d)               [Claude]
  ├─ CARD-019 Onboarding 1º revisor externo (~3d)             [José + Claude]
  └─ CARD-020 Domínio quarry.com.br dedicado (~1d)            [José]
     └─ Marco 2: Pacote para 1º prospect pagante              🎯
```

---

## Decisões do José que destravam o plano

Sem essas decisões, partes do plano travam. Coletar idealmente até **2026-06-01**.

| # | Decisão | Impacto se NÃO | Custo |
|---|---|---|---|
| D1 | Compra Mac Mini M4 Pro 64GB para CARD-015 Fase 2 | Modalidade A fica "documentada mas não validada"; pitch sustenta com B+C apenas | R$ ~18k one-time |
| D2 | Contratação advogado externo para revisão conformidade Bacen | Doc conformidade vira "rascunho próprio" sem chancela | R$ 5-10k one-time |
| D3 | Provisionar VPS Hetzner AX42 para validação Modalidade B | CARD-015 Fase 1 não roda | R$ ~800/mês |
| D4 | Identificar 1º prospect-demo-1 (fintech BR concreta) | CARD-019 fica em hold | esforço comercial 1-2 conversas |
| D5 | Domínio quarry.com.br | CARD-020 fica em hold | R$ ~60/ano |
| D6 | Quem reescreve doc v2: eu sozinho ou em conjunto com José | Doc fica sem validação editorial | tempo |

---

## Gates de qualidade (cada CARD)

Inegociáveis a cada CARD entregue:

- [ ] **Regra Zero** — mapear impacto + testar antes/depois
- [ ] **Regra 5** — sandbox separada em `/root/sandbox/quarry_*`
- [ ] **Regra 6** — deploy com aprovação explícita
- [ ] **Regra 11 step 0** — `consult-catalog <kw>` rodado ANTES da primeira linha
- [ ] **Regra de Ouro** — smoke test pós-deploy contra `https://quarry.12brain.org`
- [ ] Memória relevante atualizada
- [ ] SESSION-NOTES.md atualizado
- [ ] Commit organizado em mensagens descritivas
- [ ] Push pra remote `Josepassinato/Security` (branch main)

---

## Métricas de sucesso

Por marco:

**Marco 1 (final semana 6 — Sprint Fintech BR encerrado):**
- [ ] Doc v2 publicado em `docs/pt-br/Relatorio_Tecnico_Estrategico_Quarry_v2.md`
- [ ] Todo claim do doc v2 verificável em `quarry.12brain.org`
- [ ] Benchmark FP publicado em `/br#benchmark` com metodologia reproduzível
- [ ] Demo do fluxo Bacen 24h: caso criado → rascunho gerado em <30s → humano aprova → e-mail enviado → ledger registra (E2E em <5min)
- [ ] Modalidade B (VPS Llama) rodando em produção com benchmark publicado
- [ ] Modalidade A (Mac Mini) validada **ou** marcada como "disponível mediante contato" (depende D1)

**Marco 2 (final semana 8 — Pacote prospect):**
- [ ] Pricing fintech BR no `/br` com números reais (sem "a definir")
- [ ] LGPD Art. 48 caput coberto (notificação titulares automatizada)
- [ ] SOC2 + ISO27001 cross-mapping publicado
- [ ] 1º prospect-demo-1 onboarded com credencial individual
- [ ] (Opcional) `quarry.com.br` ativo apontando pra `/br`

---

## Riscos macro do plano

| # | Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|---|
| R1 | Benchmark CARD-013 mostra FP <50% | Média | Alto (mata "80%" e exige reposição do pitch) | Investigar prompts do auto-triage antes de publicar; ajustar antes de divulgar |
| R2 | CAPEX Mac Mini negado | Média | Médio (pitch sustenta com B+C) | Modalidade B já cobre 80% do valor comercial |
| R3 | SMTP enterprise indisponível pra teste CARD-014 | Baixa | Médio | Adapter plugável + stub configurável; cliente real configura no onboarding |
| R4 | Advogado externo sem agenda em junho | Alta | Médio (doc conformidade fica "draft") | Buscar 2-3 escritórios em paralelo; emergência interna assume com ressalva |
| R5 | Sprint extrapola 6 semanas | Alta | Baixo (cards 016+ escorregam pra agosto) | Priorizar P0 estrito; P1 pode escorregar sem comprometer pitch |
| R6 | José sem disponibilidade pra decisões D1-D6 | Média | Alto | Pré-respostas neste doc; consulta direta toda segunda-feira da semana |

---

## Capacidade necessária

- **Claude (eu):** ~6 semanas full-time-equivalent (~30h/semana de execução), dependendo de quantos sprints paralelos
- **José:** ~5-8h/semana — aprovações de deploy + decisões D1-D6 + revisão de doc v2 + identificação de prospect
- **Advogado externo (1x):** ~6-10h consulta para doc conformidade Bacen
- **Recursos VPS:** Hetzner AX42 ~R$ 800/mês a partir da semana 4

**Total CAPEX:** ~R$ 23-28k (Mac Mini + jurídico) — ambos opcionais conforme decisões D1/D2
**Total OPEX:** ~R$ 800/mês durante sprint (VPS), pode descontinuar pós-validação ou virar pro do cliente

---

## Como atualizar este plano

- Cada CARD concluído: status check aqui + memória `project-quarry-positioning` se mudou narrativa
- Decisões D1-D6 respondidas: mover pra seção "decisões fechadas" com timestamp
- Marco atingido: atualizar critério em "Métricas de sucesso" + screenshot/link
- Risco materializado: documentar mitigação efetiva em "Riscos macro"
- Cards novos abertos (016, 017, etc): adicionar arquivos `CARD-NNN-*.md` + linha aqui

---

## Próxima ação concreta (recomendada para a próxima sessão)

**Iniciar CARD-013** (Benchmark FP) imediatamente porque:
1. É o mais barato (~3.5d, zero CAPEX)
2. Desbloqueia reescrita do doc v2 (precisa do número real)
3. Não depende de decisões D1-D6
4. Resultado vira asset comercial reusável (slide de pitch + página /br#benchmark)

Em paralelo, José responde D1 (Mac Mini CAPEX) — destrava a Modalidade A do CARD-015.

---

## Histórico de revisões

| Versão | Data | Mudança |
|---|---|---|
| 1.0 | 2026-05-24 | Plano inicial pós-auditoria do doc CEO/CTO |
