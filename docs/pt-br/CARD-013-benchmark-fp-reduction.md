# CARD-013 — Benchmark de redução de falso-positivo (auto-triage)

**Para:** José Passinato
**Por:** Claude (planejado em 2026-05-24)
**Status:** 🟡 PROPOSTO — aguardando alocação de sprint
**Razão:** o pitch atual cita ">80% de redução de falso-positivo" sem benchmark interno. Em due diligence técnica de fintech, esse número fura na primeira pergunta ("qual dataset? qual baseline? métrica de fechamento errado?"). Sem evidência reproduzível o claim vira hype e queima reputação. Com evidência vira diferencial defensável.

---

## Objetivo

Produzir um benchmark reproduzível, versionado e publicável de `auto_triage_agent` rodando contra o dataset BR FinPlay já existente (`customizations/datasets/br-fintech-generator/`), com 3 métricas centrais:

1. **Auto-close rate** — % de alertas que o auto-triage fecha sem chegar ao humano
2. **False-close rate** — % desses fechados que eram verdadeiros positivos (erro perigoso)
3. **Latência p50/p95** — tempo do ingest ao fechamento

Resultado publicado em `/br#benchmark` + slide de pitch.

---

## Por que importa

- **Pitch deck (CARD-012 follow-up + slides comerciais)** hoje cita "80%" sem fonte. Vira número crível.
- **Substituí ângulo "MSSP R$ 80-300k"** por dado comparável: "auto-triage fecha X% dos alertas sem humano, contra Y% dos MSSP tradicionais".
- **Quem perde com 80% sem benchmark:** todo prospect que tem CTO técnico (que é todo prospect que importa).

---

## Escopo

- Script Python reproduzível em `customizations/benchmarks/auto-triage-br-fintech/`
- Rodar contra geração canônica do FinPlay (~500 alertas, mix high/low fidelity)
- Comparar baseline (regras estáticas) vs auto-triage agêntico
- Gerar relatório `.md` versionado por commit + CSV com cada amostra
- Publicar resumo em `/br#benchmark` (componente novo)
- Documentar em `docs/pt-br/benchmark-auto-triage.md` o método (pra revisor externo refazer)

---

## Não-escopo

- Não medir outros agentes (investigation, attack-path, enrichment) — fica para CARDs futuros
- Não rodar contra dataset real de cliente — só sintético FinPlay
- Não automatizar em CI (rodada manual versionada por commit; CI fica para depois)

---

## Tarefas estimadas

| # | Tarefa | Estimativa |
|---|---|---|
| 1 | Curador: `consult-catalog benchmark eval` antes de codar | 10min |
| 2 | Definir esquema de ground-truth no FinPlay generator (label TP/FP) | 0.5d |
| 3 | Script benchmark Python `run_auto_triage_benchmark.py` | 1d |
| 4 | Baseline regra-estática (replicar lógica pré-IA) para comparação | 0.5d |
| 5 | Componente `apps/web/src/components/landing/br/BenchmarkBR.tsx` | 0.5d |
| 6 | Doc reproduzibilidade `docs/pt-br/benchmark-auto-triage.md` | 0.5d |
| 7 | Test deploy + smoke público | 0.5d |
| **Total** | | **~3.5d** |

---

## Critério de pronto

- [ ] Script benchmark roda standalone via `pnpm benchmark:auto-triage` ou comando python equivalente
- [ ] Resultado versionado em `customizations/benchmarks/runs/YYYY-MM-DD-<hash>.json`
- [ ] Seção `/br#benchmark` mostra número real + link para metodologia
- [ ] Pitch deck (`docs/pt-br/pitch-deck.md`) atualizado para citar número real
- [ ] Memória `project-quarry-positioning` atualizada (remove placeholder de 80%)

---

## Riscos identificados

- **Risco 1:** auto-triage agêntico medido pode ficar abaixo dos 80% prometidos. Mitigação: publicar número honesto + ajustar pitch. Número honesto credible > número alto sem fonte.
- **Risco 2:** dataset FinPlay sintético não reflete distribuição real fintech BR. Mitigação: documentar explicitamente que é sintético; convidar 1º prospect a rodar contra dataset deles em piloto.

---

## Curador (Regra 11 step 0 — executar ANTES da primeira linha de código)

```bash
consult-catalog benchmark
consult-catalog eval
consult-catalog metrics
```

Capabilities prováveis em outros projetos: nenhuma identificada hoje (gap real do framework — quando construído, propor entrada no INDEX.md).

---

## Dependências

- CARD-012 (Comunicação Bacen 24h) — já entregue ✓
- Dataset FinPlay generator existente em `customizations/datasets/br-fintech-generator/`
- Auto-triage agente existente em `services/agents/app/agents/auto_triage_agent.py`
