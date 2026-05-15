# ADR-001: Fork condicional do AiSOC como base do Quarry

**Data:** 2026-05-15
**Status:** ACEITO (condicional, ver "Condições")
**Decisores:** José Passinato (founder), Claude (auditor técnico)
**Card relacionado:** CARD-001 (auditoria AiSOC)
**Documento de suporte:** [`/root/projetos/audits/aisoc-audit-report.md`](../aisoc-audit-report.md)

---

## Contexto

Quarry é um produto SaaS de segurança em planejamento (operado sob o domínio `securit.12brain.org`). Antes de iniciar implementação, surgiu a oportunidade de forkar o projeto open-source AiSOC (`github.com/beenuar/AiSOC`, MIT, criado 2026-05-02), que entrega arquitetura SOC end-to-end: orchestrator LangGraph, eval harness CI-gated, MCP server, 50+ connectors, detection corpus multi-source.

A decisão estratégica é: **forkar AiSOC** (parte de Day 1 com infraestrutura técnica madura) **ou construir do zero** (controle total, sem dependência narrativa de outro projeto).

## Decisão

**Forkar AiSOC** no commit observável em 2026-05-15 (latest commit `pushedAt: 2026-05-15T11:21:56Z`, ref será fixada no ato do fork em CARD-002).

A decisão é **condicional** às 10 restrições listadas abaixo.

## Justificativa

**Pró:**
1. AiSOC é tecnicamente sólido (score 7/10) com arquitetura, testes (213 arquivos) e CI (16 workflows) já em pé.
2. Licença raiz MIT — totalmente compatível com SaaS comercial closed-source.
3. Reproduzir o que existe demandaria 6-12 meses de equipe; fork = Day 1 produtivo.
4. Eval harness, Investigation Ledger e MCP server são diferenciais de produto raros no espaço.
5. Detection corpus já vem com provenance per-rule — sistema correto para atribuição legal.

**Contra (mitigados pelas condições):**
1. Projeto tem 13 dias de vida — imaturo como dependência.
2. Bus factor = 1 (92% commits por Beenu Arora / Cyble).
3. Mantido por funcionários da Cyble (empresa de threat intel comercial) — potencial conflito futuro.
4. Versionamento caótico (5 majors em 6 dias).
5. Stack pesado (20+ serviços compose) — operacionalmente custoso.

**Trade-off final:** os contras existem mas são endereçáveis por **fork independente + roadmap próprio**. Os prós são imediatos e dificilmente replicáveis sem custo significativo.

## Condições (não-negociáveis)

1. **Fixar SHA do upstream** no momento do fork. Nunca `git pull` automático.
2. **Rebrand completo** antes do primeiro deploy: remover toda referência a AiSOC/Cyble/tryaisoc.com.
3. **Cherry-pick manual** de features upstream — nunca merge passivo.
4. **Monorepo separado** (não submodule).
5. **Cortar stack para MVP**: manter api/agents/web/ingest/fusion/connectors/realtime/mcp. Adiar ueba/threatintel/honeytokens/purple-team/osquery-tls/slack-bot/teams-bot. Substituir Kafka+Zookeeper por Redpanda. Adiar Neo4j/Qdrant/OpenSearch.
6. **Reescrever `NOTICE.md`** a partir do provenance dos detections antes de qualquer demo público (obrigação legal DRL-1.1 + Apache-2.0).
7. **Gerar SBOM** (`cyclonedx-py` + `cyclonedx-node`) no momento do fork; versionar.
8. **`CHANGELOG.md` Quarry próprio** começando em "Forked from AiSOC commit `<sha>` on 2026-MM-DD".
9. **CI/CD próprio** — remover workflows que apontam para docs.tryaisoc.com / wet-eval / sync-marketplace.
10. **Roadmap independente** alinhado com clientes pagantes Quarry, não com narrative OSS upstream.

## Tratamento de licenças

- **MIT** raiz: ✅ sem ação além de manter copyright original (cláusula MIT) em NOTICE.
- **pysigma (LGPL-2.1)**: ✅ OK para SaaS hosted; ⚠️ se Quarry oferecer on-prem futuro, isolar pysigma em microserviço swapable.
- **DRL-1.1 (SigmaHQ rules)**: ✅ manter sistema de provenance; gerar NOTICE.md automatizado.
- **Apache-2.0 (MITRE CAR, Splunk Security Content, Chronicle)**: ✅ atribuição automática via provenance.
- Nenhuma dep GPL/AGPL/SSPL identificada na auditoria.

## Riscos aceitos

| Risco | Mitigação |
|---|---|
| Cyble lançar SaaS concorrente | Quarry diferencia desde Day 1 (target market BR, vertical específica, etc — definir em ADR-002) |
| Beenu Arora abandonar AiSOC | Fork independente; não dependemos da continuidade upstream |
| Quebra de API entre versões upstream | Cherry-pick manual; nunca pull passivo |
| pysigma LGPL se Quarry virar on-prem | Decisão revisitável; arquitetura prevê isolamento |
| Stack operacional pesado | Corte agressivo do MVP (condição 5) |

## Decisão revisitável em

**90 dias (2026-08-15)** — reavaliar se faz sentido pegar features upstream com mais regularidade, condicionado a:
- AiSOC consolidar 2-3 contribuidores externos significativos
- Versionamento estabilizar (1 major/trimestre, não 5/semana)
- Cyble publicamente endossar AiSOC (governança formal)

Até lá: **fork e isolar**.

## Próximos cards

- **CARD-002**: executar o fork (clone próprio, fixar SHA, rebrand básico, primeiro commit Quarry).
- **CARD-003**: corte do stack MVP (remover serviços não-essenciais, simplificar docker-compose).
- **CARD-004**: gerar NOTICE.md + SBOM inicial.
- **CARD-005**: definir roadmap Quarry independente (Quarry-vs-AiSOC differentiation).

## Referências

- Relatório de auditoria completo: [`/root/projetos/audits/aisoc-audit-report.md`](../aisoc-audit-report.md)
- Repositório AiSOC: `github.com/beenuar/AiSOC` (commit observável 2026-05-15T11:21:56Z)
- License upstream: MIT (`LICENSE`)
- Documento upstream inconsistente: `LICENSES.md` (afirma Apache-2.0 erroneamente) — reportar como issue se forkarmos
