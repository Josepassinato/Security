# Benchmark PLD/FT — Quarry × IBM AML (público, reproduzível)

Roda o motor determinístico de PLD/FT do Quarry (`apps/web/src/lib/pldft/engine.ts`)
contra o dataset **IBM Transactions for Anti-Money Laundering** (ealtman2019, Kaggle),
que é **rotulado** (`Is Laundering`) e traz as **tipologias injetadas** (`*_Patterns.txt`).
Resultado: recall/precision **medidos contra dado de terceiro** — defensável em due diligence,
diferente de número auto-reportado em dataset próprio.

> O motor **não é modificado**. Este harness só importa `analyzePldFt()` e mede.

## Por que esse dataset

- É o único dataset AML público grande, com **grafo from→to**, timestamp real, formato de
  pagamento e **label de lavagem por transação** + arquivos de **tipologia** (fan-out, cycle,
  gather-scatter, etc). Casa com as regras de tipologia do motor.
- Tamanhos: `HI-Small` (~5M tx), `HI-Medium` (~31M), `HI-Large` (~180M). `HI` = razão de
  ilícito mais alta (mais sinal). Validamos no Small; Medium é o "scale run".

## O que ele NÃO cobre (honestidade)

O IBM AML não tem KYC, idade de conta, device nem listas de sanção/PEP. Logo **4 das 9 regras
não são exercitadas** aqui:

| Coberto por este benchmark (grafo transacional) | Só pelo gerador sintético `customizations/datasets/br-fintech-generator` |
|---|---|
| PLD-PIX-001 passagem · PLD-PIX-003 multi-vítima · PLD-STR-007 fracionamento · PLD-CRYPTO-009 · PLD-PIX-002 fan-out* | PLD-KYC-004 incompatibilidade econômica · PLD-KYC-005 conta nova · PLD-DEV-006 device reuse · PLD-LIST-008 sanções/PEP |

\* `PLD-PIX-002` é Pix-only no motor; o IBM não tem Pix. Por isso rodamos **dois modos**
(`honest` e `generalized`) — ver abaixo.

## Decisões de mapeamento (IBM → `PldTransaction`)

- **Entidade:** `customerId = Entity ID` (de `*_accounts.csv`) — agrupa contas sob o dono.
- **Direção:** cada linha IBM (From→To) vira **2 transações** (o pagador vê `out`, o recebedor `in`).
- **Moeda:** `Amount Paid` normalizado pra **USD** via tabela FX estática (~2022, em `adapter.ts`);
  thresholds BRL do motor convertidos a USD (÷ 5,2).
- **Rail:** Bitcoin→Crypto, Credit Card→Cartao, ACH/Wire→TED, Cheque/Cash→Outro.
- **Self-loop / Reinvestment** (From==To, mesma entidade): descartado (não é transferência entre partes).
- **Modos de fan-out:**
  - `honest` — rails reais; `PLD-PIX-002` (Pix-only) **não dispara** (mede a cegueira da regra).
  - `generalized` — ACH/Wire/Cheque→Pix **só no benchmark**, pra medir o ganho de generalizar a regra.

## Metodologia de score

- **Nível ENTIDADE (principal):** entidade *suja* = tem ≥1 tx lavagem; *flagada* = motor gerou ≥1 finding.
  - Recall = sujas pegas / sujas. Precision = flagadas que eram sujas / flagadas.
- **Por TIPOLOGIA:** dos anéis de cada tipo (Patterns.txt), quantos foram cobertos.
- **Por REGRA:** quantos findings cada regra gerou e quanta lavagem cobriu.
- **Nível TRANSAÇÃO (contexto):** precisão-tx é baixa por construção (um finding varre todas as
  txs da entidade) — não é a métrica de referência.
- Accuracy é **ignorada de propósito** (base ~0,1% positiva → accuracy seria enganosa).

## Reprodutibilidade

Pré-requisito: token Kaggle em `~/.kaggle/access_token` (formato novo `KGAT_…`, chmod 600).

```bash
# 1. baixar (fora do repo)
bash customizations/benchmarks/pldft_public/download.sh    # baixa HI-Small p/ /root/datasets/ibm-aml

# 2. rodar (a partir da raiz do repo; usa o tsx do projeto)
./node_modules/.bin/tsx customizations/benchmarks/pldft_public/run_benchmark.ts \
  /root/datasets/ibm-aml/HI-Small_Trans.csv \
  /root/datasets/ibm-aml/HI-Small_accounts.csv \
  /root/datasets/ibm-aml/HI-Small_Patterns.txt \
  /root/datasets/ibm-aml/runs/small-honest  honest

# variante generalized (mede o ganho de fan-out não-Pix)
#   … run_benchmark.ts … /root/datasets/ibm-aml/runs/small-generalized generalized
```

Saídas em `<outDir>/`: `report.md` (legível) + `metrics.json` (machine-readable) +
`prepared.tsv`/`sorted.tsv` (intermediários, descartáveis).

## Arquitetura (escala sem estourar RAM)

`prepare` (stream → projeta in/out → `prepared.tsv` keyed por entidade) →
`sort -k1,1` (em disco, não na RAM) →
`run` (stream por entidade, `analyzePldFt()` por entidade) →
`score`. Memória ≈ 1 entidade por vez → escala do Small ao Medium.

## Limitações conhecidas

- FX estática (~2022), não histórica por-data.
- `HI-Small` é amostra robusta mas é **um** dataset sintético (IBM); recall/precision aqui ≠
  produção real (que depende do mix de tipologias e thresholds calibrados ao cliente).
- Thresholds do motor são tunados pra BRL/fintech BR; aqui rodam em USD-equivalente fixo.
