# CARD-014 — Auto-comunicação Bacen 24h real (além do rascunho .md)

**Para:** José Passinato
**Por:** Claude (planejado em 2026-05-24)
**Status:** 🟡 PROPOSTO — aguardando alocação de sprint
**Razão:** CARD-012 (entregue 2026-05-23) gera rascunho `.md` de comunicação Bacen 24h dentro do demo. Próximo passo: o produto real precisa **enviar** essa comunicação (com gate humano de 1-clique), notificar ANPD se LGPD aplicável, e manter cronômetro 24h visível no Case Workspace. É O moat real vs Cyble/Mandiant no mercado fintech BR.

---

## Objetivo

Transformar o rascunho `.md` em fluxo regulatório operacional ponta-a-ponta dentro do Case Workspace, com:

1. **Cronômetro 24h** visível em todo caso classificado como relevante (Res. BCB 85/2021 Art. 8)
2. **Geração automática** do rascunho no momento da classificação (não só no demo)
3. **Gate humano de 1-clique** — botão "Aprovar e enviar" assina e marca como comunicado
4. **Envio efetivo** via canal configurável (e-mail para CSIRT-Bacen como MVP; futuro: API SISBACEN se publicada)
5. **Notificação ANPD** auto-disparada se evento for classificado como vazamento de PII (LGPD Art. 48 §1º)
6. **Ledger imutável** registra rascunho gerado, decisão humana, hora do envio, identidade do aprovador

---

## Por que importa

- Hoje o produto entrega "investigação" e "evidência"; **o que a fintech regulada compra é o cumprimento do prazo de 24h**
- Cyble/Mandiant fazem investigação genérica; **nenhum concorrente entrega o artefato regulatório fintech BR específico**
- Liga diretamente ao posicionamento `project-quarry-positioning` ("SOC econômico BACEN-compliant")
- Vira **case study comercial**: "Fintech X usou Quarry, fechou comunicação Bacen em 4h vs 23h ano anterior"

---

## Escopo

### Backend (`services/api` + `services/agents`)
- Novo módulo `services/api/app/api/v1/endpoints/regulatory.py` — endpoints CRUD para artefatos regulatórios
- Trigger automático no classificador: quando incidente vira "relevante", gera rascunho + abre cronômetro
- Ledger imutável: tabela `regulatory_communications` com hash chain (cadeia probatória LGPD Art. 48/50)
- Adapter de envio plugável: `e-mail`, `webhook`, futuro `sisbacen` (interface, não implementação SISBACEN agora)

### Frontend (`apps/web`)
- Componente novo `apps/web/src/components/cases/RegulatoryClock.tsx` — cronômetro 24h
- Painel "Comunicação Bacen 24h" dentro do `CaseWorkspace.tsx` com 3 estados:
  1. `draft` — rascunho gerado, aguardando revisão
  2. `submitted` — humano aprovou e enviou
  3. `expired` — passou 24h sem envio (alerta vermelho)
- Botão "Aprovar e enviar" + diálogo de confirmação (typed-name verification, padrão de ação irreversível)
- Endpoint preview `.md` (reuso direto de `bacenReport.ts` do CARD-012)

### Compliance LGPD
- Detector `is_pii_breach` (heurística + LLM classifier) — quando true, dispara também notificação ANPD
- Template ANPD `apps/web/src/components/demo/anpdReport.ts` (espelha `bacenReport.ts`)

---

## Não-escopo

- **Integração real com API SISBACEN/CSIRT-Bacen**: não há API pública estável hoje. Plugar adapter, deixar como integration-ready. Quando Bacen publicar, swap.
- **Notificação titulares de dados** (LGPD Art. 48 caput): fica para CARD-016 ou Sprint seguinte. ANPD primeiro.
- **Multi-tenant billing por uso regulatório**: fica para sprint comercial.
- **Auditoria SOC2 / ISO27001 cross-mapping**: candidato a CARD-017.

---

## Tarefas estimadas

| # | Tarefa | Estimativa |
|---|---|---|
| 1 | Curador: `consult-catalog compliance regulatory bacen email-send` | 15min |
| 2 | Schema Postgres `regulatory_communications` + migração | 0.5d |
| 3 | Endpoint backend CRUD + trigger automático | 2d |
| 4 | Hash-chain ledger (cadeia probatória) | 1d |
| 5 | Adapter envio e-mail + webhook | 1d |
| 6 | Detector PII breach + ANPD template | 1.5d |
| 7 | Componente `RegulatoryClock` + integração `CaseWorkspace` | 2d |
| 8 | Diálogo aprovação 1-clique + auth do aprovador | 1d |
| 9 | E2E tests + smoke público | 1d |
| 10 | Doc PT-BR `docs/pt-br/auto-bacen-24h.md` (incluindo limites: adapter SISBACEN é stub) | 0.5d |
| **Total** | | **~10-12d (~2 sprints)** |

---

## Critério de pronto

- [ ] Caso marcado relevante gera rascunho automaticamente em <30s
- [ ] Cronômetro 24h visível, contagem regressiva real, alerta vermelho ao cruzar 6h restantes
- [ ] Botão "Aprovar e enviar" exige typed-name verification antes de disparar
- [ ] E-mail enviado contém o `.md` (mesmo formato do CARD-012, agora com `caseId` real)
- [ ] Hash-chain registra: rascunho gerado, aprovador, timestamp, hash do envio anterior
- [ ] ANPD auto-disparada quando `is_pii_breach == true` (com gate humano separado)
- [ ] Smoke test público confirma fluxo end-to-end no demo
- [ ] Documentação explicitamente diz "adapter SISBACEN é stub — produção configura SMTP"

---

## Riscos identificados

- **Risco 1:** classificador "relevante" falha (FP gera comunicação Bacen indevida). Mitigação: humano sempre revisa antes de enviar; rascunho não é envio.
- **Risco 2:** SMTP enterprise da fintech bloqueia envio. Mitigação: adapter plugável + webhook fallback.
- **Risco 3:** sem API SISBACEN, o "envio" hoje é e-mail manual ao CSIRT. Mitigação: documentar explicitamente; quando Bacen publicar API, plug ready.
- **Risco 4:** vazamento de dados via e-mail. Mitigação: rascunho não inclui PII bruta (só agregados + IDs internos); template revisado por DPO antes do envio.

---

## Curador (Regra 11 step 0 — executar ANTES da primeira linha de código)

```bash
consult-catalog compliance
consult-catalog regulatory
consult-catalog email-send
consult-catalog hash-chain
consult-catalog ledger
```

Capabilities potencialmente reusáveis:
- `pdf-locale` (soma-id) — se PDF assinado for necessário no envio
- `pdf-pdfkit` (Payjarvis) — alternativa Node server-side
- E-mail send: provavelmente Zoho SMTP já configurado (ver `reference_zoho_smtp`)

---

## Dependências

- CARD-012 (rascunho `.md`) — entregue ✓ (`apps/web/src/components/demo/bacenReport.ts` é reusado direto)
- CARD-013 (benchmark FP) — não bloqueia, mas conviria ter números reais antes de pitch comercial
- CARD-015 (Mac Mini local LLM) — independente; este card funciona em qualquer modo (managed, self-host, sovereign)
