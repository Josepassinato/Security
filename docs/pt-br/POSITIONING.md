# Quarry — Positioning

> Documento-âncora. Toda decisão de produto, copy, sales e roadmap pergunta:
> *"isso confirma ou contradiz o que está escrito aqui?"*
>
> **Última revisão:** 2026-05-26 — José Passinato + Claude
> **Cadência:** revisar trimestralmente. Versionar mudanças no `CHANGELOG.md`.
> **Formato:** April Dunford ([Obviously Awesome](https://www.aprildunford.com/obviously-awesome)).

---

## 1. Para quem é

**ICP (Ideal Customer Profile) — recortado, não genérico:**

- Fintech brasileira **licenciada/autorizada pelo Bacen**
  (SCD, SEP, Conta de Pagamento, PSTI, Payment Initiator, Sociedade de Crédito Direto, emissora de CCB)
- **50–300 funcionários** (Seed a Série A)
- **Sem CISO sênior interno** (geralmente CTO acumula segurança)
- Budget total de segurança **R$ 20–80k/mês**
- **Tem dor regulatória ativa** — auditor independente, próxima fiscalização Bacen, ou cláusula contratual de Open Finance
- **Sensibilidade alta a soberania de dados** (LGPD + Res. BCB 85/2021 PSC)

### Gates de qualificação (yes/no)

| Pergunta | Sim → ICP | Não → fora |
|---|---|---|
| É Bacen-licensed? | ✅ | ❌ — sem dor regulatória específica |
| Tem 50–300 funcionários? | ✅ | ❌ — Nubank/Inter constroem; Bradesco compra Splunk |
| Tem CISO sênior dedicado? | ❌ | ❌ — vai construir interno |
| O CTO/CISO já avaliou Splunk e desistiu pelo preço? | ✅ | ⚠️ avaliar |
| Dado de PII/transação **não pode** sair do Brasil? | ✅ | ⚠️ avaliar |

**Recusar ativamente:** Tier-1 banks, fintechs >300 pessoas, empresas globais sem operação BR significativa, qualquer prospect sem licença Bacen.

---

## 2. Contra quem somos (categoria de competição declarada)

**Categoria escolhida:** *Sovereign Detection & Response platform para fintech BR regulada.*

Não é SIEM. Não é SOAR. Não é XDR. É a **camada de detecção forense soberana** específica para fintech BR sob Bacen.

| Quem | Como nos ataca | Como ganhamos |
|---|---|---|
| **Splunk, Datadog, CrowdStrike** | Brand global, deep integrations, dinheiro infinito | Preço + soberania física (eles obrigam cloud global) + Bacen-native que eles ignoram |
| **Mandiant, Tempest, Cipher** | Consultoria + serviço | Produto autônomo + auditável + preço previsível |
| **Stark AI, Idwall AI** | Mesmo comprador, automação de compliance docs | Surface diferente — detecção/resposta, não doc analysis. Adjacência, não competição |
| **Wazuh + DIY internal SOC** | Open-source grátis | Curadoria de detecções BR-específicas + LLM forense + Bacen mapping + suporte |
| **Falcon Charlotte AI, Dropzone, Anvilogic** | AI-native, $100M+ funding | Local + sovereign deployment que eles não oferecem + auditabilidade citacional |

**Categoria que NÃO somos:** SIEM genérico, doc-AI, conformidade-como-serviço, GRC, MSSP.

---

## 3. O wedge (3 pilares de moat — não-copiáveis em <24 meses)

### Pilar 1 — Sovereign deployment
LLM rodando **dentro do perímetro físico do cliente**: Mac Mini na sala-cofre OU VPS dedicada do cliente. Nenhum byte de PII ou query forense sai pra cloud global.

- Nenhum SOC global oferece (modelo de negócio incompatível)
- Nenhum BaaS vai construir (não é o core deles)
- Atende Res. BCB 85/2021 PSC + LGPD **sem interpretação criativa**

### Pilar 2 — Citation-validated reasoning
Cada alerta, recomendação e veredito tem **trace forense citável**: fonte primária, regra acionada, raciocínio do agente, confiança numérica.

- Vs Stark AI / Charlotte AI: black-box
- Vs SIEM tradicional: "veio do log X" (não-defensável)
- Defensável em CVM, Bacen, MP, CGU
- Auditor LGPD consegue inspecionar a lógica

### Pilar 3 — Bacen-native + LGPD-native
Mapeamento direto com:
- Res. BCB 85/2021 (PSC + monitoramento contínuo)
- Res. CMN 4.893/2021 (segurança cibernética)
- Open Finance security framework
- ANPD comunicação 24h
- LGPD Art. 46 (medidas técnicas)

- Global player ignora especificidades BR
- SOC local (Tempest, Cipher) vende consultoria, não mapeamento de produto

---

## 4. A prova (assets defensáveis hoje)

| Asset | Localização | Status | Cadência |
|---|---|---|---|
| **Benchmark auto-triage BR** | `/br#benchmark` | Vivo | Atualizar mensal vs Splunk/Datadog/Falcon |
| **Sandbox executável** | `docker-compose.demo.yml` | Vivo | Manter PR pública passando |
| **Sovereign Mac Mini demo** | CARD-015 Fase 2 | Em validação | Vídeo público após validação |
| **Sovereign VPS install** | `scripts/sovereign-appliance/install-vps-linux.sh` | Sandbox | Validar em Hetzner AX42 |
| **ISO 27001 readiness pack** | `docs/.../iso27001/` | Publicado | Versão semestral |
| **Bacen conformidade doc** | `docs/pt-br/sovereign-llm/conformidade-bacen.md` | Pendente | CARD-015 Fase 1 |
| **Eval before/after público** | `EVAL_BEFORE_AFTER.md` | Vivo | Atualizar com cada modelo novo |

---

## 5. Métrica única (12 meses)

**Norte definitivo:** **3-5 fintechs BR Bacen-licensed pagantes em produção** até 2027-05-26.

- ≥1 com Sovereign deployment validado (Mac Mini OU VPS)
- ≥1 com Bacen como compelling event (fiscalização, RFI)
- ARR mínimo R$ 20k/mês por cliente
- NRR ≥110% em 12m

**Se chegarmos lá:** o sandwich (BaaS-vertical + global-SOC + AI-native) não nos alcança no ICP.
**Se não chegarmos:** revisar este documento. Não revisar antes — disciplina vence taste.

### Anti-métricas (rejeitar como sucesso)

- Stars no GitHub ⛔
- Downloads do docker-compose ⛔
- MQLs sem licença Bacen ⛔
- Pageviews na landing ⛔
- Deals com Tier-1 bank ⛔ (mesmo se aparecer)

---

## 6. Regras de recusa

Para preservar o positioning, **recusar ativamente** os seguintes deals/oportunidades — mesmo se aparecerem:

1. **Tier-1 banks** (BB, Itaú, Bradesco, Santander, Caixa) — vão comprar Splunk, e o ciclo de vendas mata o time
2. **Big-tech fintechs** (Nubank, Inter, PicPay, Mercado Pago) — constroem interno e te trocam em 18 meses
3. **Empresas não-financeiras** ("vocês também não fazem SOC pra e-commerce?") — perde foco regulatório
4. **Empresas sem operação BR** — fora do mercado-alvo, perde mapeamento Bacen
5. **Pedidos de "SIEM completo"** — não somos isso; redirecionar para Wazuh ou Datadog
6. **Pedidos de compliance docs AI** — Stark AI / Idwall já fazem; nosso surface é detecção
7. **Empresas que pedem "MSSP gerenciado 24/7"** — produto, não serviço; redirecionar para Tempest/Cipher
8. **Investidores que pedem TAM global** — TAM nosso é fintech BR regulada, ~R$ 300M/ano. Honestidade > vaidade

**Regra geral:** se o deal não confirmar pelo menos 2 dos 3 pilares (sovereign + citation + Bacen-native), recusar.

---

## 7. Como usar este documento

### Antes de mergear PR

- A feature/copy/mudança **confirma ou contradiz** algum dos 3 pilares?
- Atende o ICP definido na seção 1?
- Resiste à "regra do BaaS amanhã" — se Stark Infra anunciar isso amanhã, ainda temos moat?

### Antes de aceitar um deal

- Cliente passa nos 5 gates da seção 1?
- Cliente está em alguma das 8 categorias de recusa?
- Vale a pena pelo learning, mesmo fora de ICP? (raramente)

### Antes de mudar este documento

- Quem propõe a mudança escreve justificativa em PR
- Revisão obrigatória: José + 1 advisor externo
- Atualizar `CHANGELOG.md` com diff e razão

---

## 8. Anti-tagline (o que NÃO somos)

- ❌ "AI-powered SOC platform"
- ❌ "Revolutionize your security"
- ❌ "End-to-end cyber observability"
- ❌ "Modern SIEM"
- ❌ "Compliance copilot"

## Tagline canônica (a usar em hero, meta, README)

> **Quarry — O SOC soberano para fintech BR regulada.**
> Detecção e resposta com LLM rodando dentro do seu perímetro físico, raciocínio forense citável, mapeamento direto com Res. BCB 85/2021 e LGPD.
> Para fintech Bacen-licensed que precisa provar pra auditor, sem mandar dado pra cloud global, sem o budget do Splunk.

---

*Fim do documento. Curto de propósito. Brevidade é disciplina.*
