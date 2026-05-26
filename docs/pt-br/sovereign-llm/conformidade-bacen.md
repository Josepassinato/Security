# Sovereign LLM — Conformidade Bacen e LGPD

> **Status:** versão técnica · validação jurídica pendente
> **Última revisão:** 2026-05-26
> **Owner:** Quarry / 12Brain Solutions
>
> Este documento mapeia, **por modalidade de deployment**, como o
> Sovereign LLM da Quarry atende os principais dispositivos
> regulatórios brasileiros aplicáveis a fintechs licenciadas pelo
> Bacen. **Não constitui parecer jurídico.** Para uso defensivo em
> auditoria, RFI Bacen ou comunicação ANPD, o DPO da fintech deve
> revalidar cada item contra a sua estrutura operacional específica.
>
> **Princípio editorial:** se uma célula deste documento não pode ser
> defendida com citação específica de artigo/parágrafo do regulamento
> correspondente, ela está marcada como "*interpretação técnica, sem
> jurisprudência*". Conforme [`AGENTS.md`](../../../AGENTS.md), nada
> aqui é vendido como conformidade atestada — é o mapeamento que o DPO
> usa como ponto de partida.

---

## 1. Escopo regulatório coberto

Esta análise cobre as cinco fontes que mais aparecem em auditoria de
fintech BR licenciada (SCD, SEP, Conta de Pagamento, PSTI, Payment
Initiator, emissora de CCB):

| # | Diploma | Vinculação |
|---|---|---|
| 1 | **Res. BCB 85/2021** — Política de Segurança Cibernética para IFs e demais entes regulados | Obrigatória para qualquer ente Bacen-licenciado |
| 2 | **Res. CMN 4.893/2021** — Diretrizes de segurança cibernética e contratação de processamento e armazenamento de dados | Complementa 85/2021 para o lado CMN |
| 3 | **LGPD (Lei 13.709/2018)** — em especial Arts. 33, 46, 48 e 50 | Tratamento de dados pessoais de portadores/clientes |
| 4 | **Comunicado Bacen 44.323/2024** — incidentes de segurança cibernética: notificação em 24h | Operacional, vincula via 85/2021 |
| 5 | **Resoluções Conjuntas BCB/CMN 1, 2, 3, 4** — Open Finance / Open Insurance security framework | Para fintechs que operam Open Finance (qualquer tipo de TPP) |

ANPD: tratada como autoridade aplicável para LGPD. Os comunicados ANPD
sobre incidente em 48 horas são tratados como derivados do Art. 48 da
LGPD.

---

## 2. Tabela de mapeamento por modalidade

> **Convenção:** ✅ atende diretamente · 🟡 atende com cláusula
> contratual ou DPO override · ❌ não atende.

### 2.1 Res. BCB 85/2021 — Política de Segurança Cibernética

| Artigo / inciso | Exigência | Modalidade A — Mac Mini físico | Modalidade B — Hostinger BR | Modalidade B — Hetzner DE (fallback) | Modalidade C — Cloud BYOK |
|---|---|---|---|---|---|
| Art. 2º, § 1º | Política de segurança cibernética compatível com porte e perfil de risco | ✅ Quarry fornece controles, fintech homologa | ✅ idem | 🟡 idem + cláusula transfer LGPD | ✅ idem |
| Art. 3º | Princípios mínimos: confidencialidade, integridade, disponibilidade | ✅ dado em hardware da fintech | ✅ dado em datacenter BR | 🟡 dado em DC offshore — cláusula | ✅ via provider DPA |
| Art. 4º, II | Monitoramento de eventos em tempo real | ✅ ledger local + agentes | ✅ idem | ✅ idem | ✅ idem |
| Art. 6º | Plano de ação e resposta a incidentes documentado | ✅ Quarry fornece template | ✅ idem | ✅ idem | ✅ idem |
| Art. 7º | Testes e auditorias periódicos | ✅ ledger imutável | ✅ idem | ✅ idem | ✅ idem |
| **Art. 12** | **Contratação de serviços de processamento e armazenamento de dados** — comunicação prévia ao Bacen | 🟡 Mac Mini fica sob CNPJ da fintech, contrato 12Brain ainda exige comunicação | 🟡 VPS sob CNPJ da fintech (Hostinger) — comunicação aplicável | 🔴 **Comunicação prévia obrigatória** + DPA + cláusulas Art. 12 | 🟡 contrato BYOK direto cliente↔provider |
| **Art. 15** | **Vedações específicas para serviços contratados no exterior** | ✅ não aplicável (nacional/perímetro) | ✅ não aplicável (Hostinger BR) | 🔴 **Hetzner DE = exterior; sujeito a Art. 15** | 🟡 OpenAI / Anthropic = exterior |

**Conclusão Bacen 85/2021:** Modalidades A e B (Hostinger BR) atendem
sem necessidade de comunicação ao Bacen sob Art. 12/15. Modalidades B
(Hetzner DE fallback) e C exigem comunicação prévia e cláusulas
específicas. **A escolha de Hostinger BR como canônico para
Modalidade B é, primariamente, uma decisão de conformidade Bacen — não
de preço.**

---

### 2.2 LGPD — Lei 13.709/2018

| Artigo | Exigência | Modalidade A | Modalidade B (Hostinger BR) | Modalidade B (Hetzner DE) | Modalidade C (Cloud BYOK) |
|---|---|---|---|---|---|
| Art. 6º, VII (segurança) | Medidas técnicas para proteger dados pessoais | ✅ air-gap físico | ✅ air-gap lógico VPN | 🟡 air-gap lógico VPN + DPA | 🟡 SLA do provider |
| Art. 33 | Transferência internacional de dados pessoais | ✅ não há transferência | ✅ idem | 🔴 **Hetzner DE = transferência; exige SCC ou decisão de adequação** | 🔴 OpenAI/Anthropic = transferência; SCC obrigatória |
| Art. 46 | Medidas técnicas e administrativas para proteger dados | ✅ documentadas no doc Quarry | ✅ idem | ✅ idem (com cláusula transfer) | 🟡 herda do provider |
| Art. 48 | Comunicação de incidente à ANPD | ✅ Quarry gera relatório auto | ✅ idem | ✅ idem | ✅ idem |
| Art. 50 | Boas práticas e governança (programa de governança) | ✅ ledger + audit trail | ✅ idem | ✅ idem | ✅ idem |

**Conclusão LGPD:** Modalidade A é a mais defensiva. Modalidade B
(Hostinger BR) atende sem necessidade de cláusula de transferência
internacional. Modalidades B (Hetzner DE) e C exigem **Cláusulas
Contratuais Padrão** (Art. 33, V LGPD) e DPA com o provider. Quarry
não fornece o instrumento jurídico — o DPO da fintech contrata sob seu
modelo de cláusulas.

---

### 2.3 Comunicado Bacen 44.323/2024 — Incidente em 24 horas

Comum a todas as modalidades: Quarry gera o relatório padronizado
(campos `incident_id`, `severity`, `affected_assets`, `containment`,
`root_cause`, `timeline`, `evidence_links`) em formato compatível com o
template do Comunicado. **Diferença prática entre modalidades:**

| Modalidade | Tempo médio até relatório pronto* | Justificativa |
|---|---|---|
| A | < 4 horas | Logs locais, sem latência de transferência |
| B (Hostinger BR) | < 4 horas | Logs em SP, latência mínima |
| B (Hetzner DE) | < 6 horas | Logs em DE — latência transferência + revisão DPA |
| C (Cloud BYOK) | < 6 horas | Depende de SLA de log retrieval do provider |

\* *Estimativa técnica de geração do relatório, não inclui revisão
jurídica do DPO antes do envio.*

---

### 2.4 Open Finance / Open Insurance security framework

Para fintechs que operam como **Iniciador de Pagamento (PIxx)**,
**Detentora de Conta (DCxx)**, **Transmissora (TPP)** ou
**Receptora (RPP)** sob Resoluções Conjuntas BCB/CMN 1-4:

| Requisito | Aplicável | Modalidades suportadas |
|---|---|---|
| Monitoramento contínuo dos consentimentos | Sim | Todas |
| Detecção de uso anômalo de consentimento (>10k consentimentos / TPP / 30s, etc.) | Sim | Todas — regra `open-finance` no Quarry |
| Trilha probatória de cada chamada FAPI 2.0 | Sim | Todas |
| Resposta automatizada de bloqueio de TPP suspeito | Sim | Todas |
| Tratamento de dados em território nacional preferencial | Recomendado em RFB BCB FAPI | A, B-Hostinger BR ✅ · B-Hetzner DE 🟡 · C 🟡 |

---

## 3. Pontos de atenção (o que esta doc NÃO substitui)

1. **Comunicação prévia Art. 12** — quando o ente Bacen contrata
   processamento por terceiro, é necessário comunicar previamente.
   Esta doc não é o instrumento dessa comunicação. O DPO da fintech
   prepara o ofício; Quarry fornece anexo técnico se solicitado.

2. **DPA / Standard Contractual Clauses** — Modalidade B (Hetzner DE)
   e Modalidade C exigem DPA + SCC executadas. Quarry não é parte
   dessa contratação (fintech ↔ provider direto). Quarry pode revisar
   o draft, mas a assinatura é do DPO.

3. **Aviso de incidente em 48h à ANPD** — Quarry gera o draft do
   comunicado. A decisão de enviar, e o envio formal, é do DPO. Não
   ativamos a comunicação sem ordem expressa.

4. **Audit trail imutável** — o `Investigation Ledger` do Quarry
   garante integridade criptográfica das entradas (hash chain), mas
   o **storage primário** ainda é o Postgres da fintech. Backup +
   imutabilidade off-cluster é responsabilidade da fintech.

5. **PCI-DSS** — fora deste escopo. Quarry não toca dado de cartão
   PAN-clear; quando aplicável, integramos via tokenização do
   provider (Stark Infra, Dock, BIN sponsor, etc.).

---

## 4. Recomendação canônica por perfil

| Perfil de fintech | Modalidade recomendada | Razão |
|---|---|---|
| SCD / SEP Seed-A, dado de CPF + transação | **B — Hostinger BR** | Soberania territorial real, custo previsível, atende Bacen sem comunicação Art. 12 do exterior |
| Fintech +R$ 1bi TPV/mês com sala-cofre | **A — Mac Mini físico** | Auditor exige perímetro físico verificável |
| Fintech sem operação Bacen formal, B2C apenas | **C — Cloud BYOK** | Não há gatilho regulatório que exija sovereign |
| Fintech regulada com requisito GPU pesado (Llama 70B) | **B — Hetzner DE com DPA** | Tier Pro local ainda em avaliação; aceitar transferência LGPD |

---

## 5. Próximos passos (lado Quarry)

- [ ] Revisão jurídica deste documento por advogado especializado em Bacen + LGPD
- [ ] Anexo técnico padronizado para Art. 12 (comunicação prévia)
- [ ] Template de DPA + SCC pré-aprovado para clientes que escolherem Hetzner DE
- [ ] Auditoria externa do ledger criptográfico (com publicação do parecer)
- [ ] Mapeamento adicional: Res. CMN 4.553/2017 (gestão de risco operacional) — relevante mas não aplicado aqui ainda

---

## 6. Referências

- [Res. BCB 85/2021](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Resolu%C3%A7%C3%A3o%20BCB&numero=85) — texto oficial
- [Res. CMN 4.893/2021](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Resolu%C3%A7%C3%A3o%20CMN&numero=4893) — texto oficial
- [Lei 13.709/2018 (LGPD)](http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/L13709.htm)
- [Comunicado Bacen 44.323/2024](https://www.bcb.gov.br/) — incidentes 24h
- [Open Finance Security Framework — Bacen](https://openfinancebrasil.org.br/seguranca-e-experiencia-do-usuario)
- ANPD: Comunicados de incidente em 48h — derivado LGPD Art. 48

---

*Este documento é versionado em Git. Mudanças regulatórias relevantes
(novas resoluções, comunicados Bacen, decisões ANPD) acionam revisão
trimestral.*
