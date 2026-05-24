# Quarry — Pitch Deck

> Maio 2026 · em validação técnica
> Audiência: fintechs Seed/Series A, banco custodiante, investidor anjo BR
> Tempo de leitura: 6 min · Tempo de apresentação: 10–12 min
> Estrutura: 10 slides, separados por `---`. Compatível com Marp, Slidev e reveal.js.

---

<!-- slide 1 — capa -->

# Quarry

### SOC econômico para fintechs brasileiras que precisam *passar pela inspeção do Bacen* sem queimar o caixa de Series Seed.

Increase Trainer Inc. · maio 2026 · acesso por convite

---

<!-- slide 2 — problema -->

## 01 — o problema

Toda fintech regulada no Brasil é obrigada — por Res. BCB 85/2021, IN BCB 314 e LGPD — a ter cibersegurança documentada, registrada e auditável.

Só que as três alternativas hoje são todas ruins pra quem está começando:

| opção | custo mensal | problema real |
|---|---|---|
| MSSP enterprise (Splunk + 24×7) | R$ 80k – 300k | oversold pra fintech Seed; contrato 24m |
| SOC interno (squad + ferramentas) | R$ 180k – 420k | contratação demora 6 meses; risco de burnout |
| Sem SOC formal | R$ 0 | risco Bacen; bloqueio Pix; banco custodiante recusa |

**O paradoxo:** quem mais precisa atender a regra é quem menos pode pagar pra atender.

---

<!-- slide 3 — solução -->

## 02 — a solução

Um SaaS de SOC com **agentes IA** (Detect · Triage · Hunt · Respond) que entrega exatamente o que o regulador exige — e nada além disso.

Cinco artefatos sempre prontos:

1. **Política de Segurança Cibernética** (Res. BCB 85, Art. 3 e 4)
2. **Registro de incidentes relevantes** (Art. 8)
3. **Comunicação ao Bacen em até 24h** (Art. 9)
4. **Plano de continuidade testado** (IN BCB 314)
5. **Notificação de incidente com dado pessoal** (LGPD Art. 48)

Não competimos com Splunk. Competimos com a planilha que ninguém preenche depois.

---

<!-- slide 4 — demo / prova -->

## 03 — a prova

Investigação cinematográfica de fraude Pix organizada, dataset sintético FinPlay Pagamentos:

- **R$ 1,84 milhão** atravessam 20 contas-laranja
- **SIM swap** antecede 37 Pix de cliente high-value
- **Scraping Open Finance Bacen** seleciona vítimas com saldo alto
- **Boleto falso** fecha a rota de cash-out

Tempo total: **4 min 30 s.**
Custo médio de uma investigação completa pela IA: **R$ 27,40.**
Comparável a um analista sênior: ~18 horas · R$ ~2.250.

→ `quarry.12brain.org/demo-cinematografica` (acesso por convite)

---

<!-- slide 5 — como funciona -->

## 04 — como funciona

Quatro agentes especializados orquestrados via LangGraph, todos com ledger imutável:

```
brief recebido ──► hipóteses priorizadas ──► consultas em paralelo
                                                 │
       grafo de ataque ◄── evidências correlacionadas
                │
                ▼
       relatório regulatório · cadeia probatória · 24h Bacen
```

Cada chamada de modelo, cada query, cada decisão fica arquivada.
Auditor externo refaz a investigação do zero, com os mesmos dados.

Self-host disponível (motor MIT herdado de upstream curado) — opção pra fintech que exige soberania de dado.

---

<!-- slide 6 — mercado -->

## 05 — mercado

| Recorte | Estimativa |
|---|---|
| Fintechs registradas no Brasil (Distrito 2025) | ≈ 1.500 |
| Reguladas direta ou indiretamente pelo Bacen | ≈ 480 |
| Em estágio Seed / Series A com obrigação de PSC | ≈ 220 |
| ICP inicial Quarry (fintechs sem SOC interno hoje) | ≈ 110 |

ACV de partida: R$ 2,4k – 9,8k/mês (a fechar).
SOM realista 12 meses: 6–12 clientes pagantes.
Vetores adicionais não-ICP: BaaS, gateway Pix indireto, exchanges cripto.

*Números do funil ainda não validados em campo — primeiras conversas começam em junho.*

---

<!-- slide 7 — diferencial -->

## 06 — onde nos encaixamos

| Categoria | Concorrente típico | O que Quarry faz diferente |
|---|---|---|
| MSSP enterprise | Tempest, ISH, Cyble | preço 10–30× menor; foca nos artefatos do regulador |
| SIEM/SOAR puro | Splunk, Sentinel | já vem com playbook BR; não cobra licença por GB |
| Antifraude transacional | ClearSale, Konduto | *complementar*, não substituto — Quarry investiga depois |
| SOC interno DIY | n/a | sem contratar squad; agentes IA + ledger |
| EDR/XDR | CrowdStrike, S1 | escopo menor de propósito; foco é Bacen, não endpoint |

Quarry é **propositalmente abaixo** do escopo enterprise. A categoria que estamos criando: *compliance-grade SOC para fintech early-stage*.

---

<!-- slide 8 — para quem não é -->

## 07 — para quem isso não é

Mais honesto deixar claro:

- **Banco grande, conglomerado, IF S1/S2** — Quarry substitui mal um MSSP enterprise.
- **Fintech que precisa de antifraude tempo real** — bloquear o Pix antes do envio é outro produto.
- **Quem quer "AI-powered cyber" pra pitch deck** — o relógio do produto é o do regulador, não o do fundo.
- **Quem ainda não decidiu se vai operar regulado no Brasil** — depende de saber qual regime se aplica.

Disqualifier é parte da estratégia. Vender pra cliente errado é prejuízo composto.

---

<!-- slide 9 — onde estamos -->

## 08 — onde estamos hoje

**Construído:**
- Motor agentic completo (Detect/Triage/Hunt/Respond) — funcionando.
- 6.998 detections, 62 playbook packs, 69 connectors herdados.
- Demo cinematográfica fintech BR no ar com basic auth.
- Landing `/br` com posicionamento + checklist BACEN + comparativo.
- 5 datasets sintéticos BR (FinPlay, BOTS v3 BR, scraping Open Finance).
- Cadeia probatória + ledger imutável + replayable runs.

**Falta:**
- Primeiro cliente pagante.
- Pricing publicado (substituir "a definir" por número real).
- Entidade BR ou contrato cross-border padronizado.
- Provas sociais (logo, depoimento, métrica de inspeção real).
- SOC2 Type II evidência ativa (já mapeado, não auditado).

**Próximos 90 dias:** 3 fintechs em piloto pago, 1 estudo de caso público, pricing fixo.

---

<!-- slide 10 — pedido -->

## 09 — o pedido

Três coisas concretas, na ordem de quem está na sala:

**Se você é fintech Seed/A regulada:**
piloto de 90 dias com preço fixo, sem contrato longo. Saída clean.

**Se você é banco custodiante / BaaS aggregator:**
indicação de fintechs no seu portfólio que ainda não fecharam o item de PSC.
Você reduz risco de carteira, nós validamos com clientes alinhados.

**Se você é investidor BR de cibersegurança / fintech:**
ainda não estamos abrindo round. Vale conhecer agora pra entrar na próxima
janela com contexto, não com cold deck.

contato: **contato@quarry.dev**

---

<!-- slide bônus — referência -->

## referências

- Site fintech BR: `https://quarry.12brain.org/br`
- Demo cinematográfica: `https://quarry.12brain.org/demo-cinematografica`
- Comparativo de custo: `/br#custo`
- Disqualifier explícito: `/br#para-quem-nao-e`
- Owner legal: Increase Trainer Inc. (Coconut Creek, FL)
- Regimes citados: Res. BCB 85/2021, IN BCB 314, LGPD Art. 48 e 50

*Quarry · 2026 · uma operação da Increase Trainer Inc.*
