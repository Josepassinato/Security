# Sprint Fintech BR — 2026-06

> **Contexto:** após auditoria do relatório técnico/comercial (2026-05-24), identificamos 3 gaps entre o pitch atual e o que o produto entrega. Este sprint fecha esses gaps com **trabalho cirúrgico**: medir, automatizar, oferecer soberania. Resultado esperado: pitch totalmente defensável em due diligence técnica de fintech regulada BR + diferencial físico que nenhum SOC global tem.

**Início alvo:** 2026-06-02 (após CARD-012 estabilizar)
**Encerramento alvo:** 2026-06-28 (~4 semanas)
**Filosofia:** descartar claims hype, construir o que vira moat real, deixar default existente intocado.

---

## Origem dos cards

Auditoria 2026-05-24 contra documento técnico/comercial CEO/CTO identificou:

| Claim do doc | Gap real | Card que fecha |
|---|---|---|
| ">80% redução FP" sem benchmark | Sem evidência reproduzível | **CARD-013** |
| "Compliance automática Bacen 24h" | Hoje só rascunho `.md` — sem envio, sem cronômetro, sem ANPD | **CARD-014** |
| "Zero exfiltration / LLM 100% local" | Ollama 3B fraco; opção honesta de soberania não existe | **CARD-015** |
| "Resposta autônoma" | Decisão correta atual é gate humano — **NÃO mudar** | descartado (ver auditoria) |
| "Pay-per-incident" | Modelo inviável para fintech (CFO rejeita custo variável) | descartado |
| "Brasil + EUA" | Foco BR vence; EUA dispersa | descartado |

---

## Cards deste sprint

### CARD-013 — Benchmark de redução de falso-positivo
**Arquivo:** [docs/pt-br/CARD-013-benchmark-fp-reduction.md](./CARD-013-benchmark-fp-reduction.md)
**Estimativa:** ~3.5 dias
**Por que primeiro:** sem número real, todo o resto do pitch fica frágil. Bloqueia atualização do `docs/pt-br/pitch-deck.md`.
**Entrega chave:** seção `/br#benchmark` com número honesto + metodologia reproduzível.

### CARD-014 — Auto-comunicação Bacen 24h real
**Arquivo:** [docs/pt-br/CARD-014-auto-bacen-24h-real.md](./CARD-014-auto-bacen-24h-real.md)
**Estimativa:** ~10-12 dias (2 sprints)
**Por que segundo:** moat real vs Cyble/Mandiant. Hoje (após CARD-012) só temos rascunho `.md` no demo — produto real precisa do fluxo completo.
**Entrega chave:** cronômetro 24h no Case Workspace + envio com gate humano de 1-clique + ledger imutável + ANPD.

### CARD-015 — Sovereign LLM (Mac Mini OU VPS Llama — modalidades opcionais)
**Arquivo:** [docs/pt-br/CARD-015-mac-mini-sovereign-appliance.md](./CARD-015-mac-mini-sovereign-appliance.md)
**Estimativa:** ~16-18 dias + R$ 18k CAPEX Mac Mini + R$ 800/mês VPS validação + R$ 5-10k jurídico
**Por que terceiro:** diferencial físico vs cloud SOC; sustenta pitch "Zero exfiltration" honestamente. Modalidades A (Mac Mini físico) e B (VPS Llama) são **opcionais** — não substituem o BYOK cloud default.
**Entrega chave:** 3 modalidades documentadas (A físico, B lógico, C BYOK), seletor na landing, benchmark comparativo.

---

## Ordem de execução recomendada

```
Semana 1   ─ CARD-013 (benchmark)              [3.5d]
Semana 2-3 ─ CARD-014 (auto-Bacen real)        [10-12d]
Semana 3-5 ─ CARD-015 (sovereign LLM)          [16-18d, paralelizável em parte com CARD-014]
                  ↳ Fase 1: VPS Llama (Modalidade B)     [7d]
                  ↳ Fase 2: Mac Mini (Modalidade A)      [6-7d, depende de compra Mac]
                  ↳ Fase 3: Conformidade + comercial     [3d]
```

**Paralelização possível:** Fase 1 do CARD-015 (Modalidade B, VPS Llama) pode rodar paralela à parte final do CARD-014 — são módulos independentes (LLM target vs fluxo regulatório).

---

## Gates de qualidade (Regra Zero)

Cada card só é considerado pronto após:
- [ ] Sandbox + rsync seletivo + smoke test público (Regra 5/6)
- [ ] `consult-catalog <kw>` rodado ANTES da primeira linha de código (Regra 11 step 0)
- [ ] Memória relevante atualizada (`project-quarry-positioning` se mudar pitch)
- [ ] SESSION-NOTES.md atualizado ao fim de cada sub-entrega
- [ ] Smoke test pós-deploy contra `https://quarry.12brain.org` (Regra de Ouro)
- [ ] HISTORICO/CHANGELOG do projeto registrado

---

## Riscos macro do sprint

1. **CAPEX Mac Mini não aprovado** → Modalidade A do CARD-015 fica fora; pitch sustenta com B+C apenas.
2. **Advogado externo Bacen não disponível** no prazo → Doc conformidade fica como "rascunho próprio" + revisão jurídica como CARD-016 pós-sprint.
3. **Benchmark CARD-013 mostra FP reduction <50%** → revisar prompt do auto-triage antes de publicar; pitch só sai com número honesto, mesmo se modesto.
4. **CARD-014 esbarra em ausência de SMTP enterprise para teste** → adapter de envio fica como stub configurável; cliente real configura no onboarding.
5. **Sprint atrasa para 7+ semanas** → priorizar CARD-013 + CARD-014 (afetam pitch comercial direto); CARD-015 pode escorregar para julho sem comprometer fechamento de 1º prospect.

---

## Não-escopo deste sprint (parking lot)

- CARD-016 — Notificação automática a titulares de dados (LGPD Art. 48 caput)
- CARD-017 — Mapeamento SOC2 / ISO27001 cross-controls
- CARD-018 — Pricing fintech BR concreto (substituir "R$ 2,4k–9,8k a definir" no `/br`)
- CARD-019 — Onboarding 1º revisor externo (prospect-demo-1)
- CARD-020 — Domínio `quarry.com.br` dedicado pra `/br`
- CARD-021 — Sovereign Appliance pré-instalado pronto pra venda (após 3+ clientes pagantes)
- CARD-022 — Sovereign Appliance Linux + GPU (alternativa ao Mac Mini para clientes que rejeitam Apple)

---

## Como atualizar este documento

Cada card concluído:
1. Marca status no card individual (🟡 → ✅)
2. Adiciona linha aqui em "Cards deste sprint" com data de conclusão
3. Atualiza memória `project-quarry-positioning` se mudou o pitch
4. Move itens do "parking lot" pra cima conforme aprovação
