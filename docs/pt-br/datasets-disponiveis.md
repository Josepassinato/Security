# Datasets disponíveis

Este documento lista os datasets locais preparados para demos e validações do Quarry. Dados brutos grandes ficam fora do Git; somente geradores, parsers, hunts e documentação são versionados.

## FinPlay Pagamentos - fintech brasileira sintética

Persona fictícia criada para demonstrar operação de fintech brasileira com Pix, login mobile, Open Finance e boletos.

- Gerador: `customizations/datasets/br-fintech-generator/generator.py`
- Validação: `customizations/datasets/br-fintech-generator/validate_dataset.py`
- Documentação: `docs/pt-br/dataset-sintetico.md`
- Volume esperado: 165.900 eventos sintéticos e 50.000 clientes fictícios
- Cenários: money mule ring, SIM swap, scraping Open Finance e campanha de boleto fraudulento

Comandos principais:

```bash
python3 customizations/datasets/br-fintech-generator/generator.py
python3 customizations/datasets/br-fintech-generator/validate_dataset.py
python3 customizations/datasets/br-fintech-generator/import_to_ingest.py --dry-run
```

## Splunk BOTS v3 - Wayne Enterprises

Dataset enterprise público do Splunk BOTS v3, usado aqui como demo cinematográfica Wayne Enterprises.

- Fonte: <https://github.com/splunk/botsv3>
- Download: <https://botsdataset.s3.amazonaws.com/botsv3/botsv3_data_set.tgz>
- Licença: CC0-1.0
- MD5 esperado: `d7ccca99a01cff070dff3c139cdc10eb`
- Formato original: Splunk pré-indexado
- Local bruto local: `datasets/bots-v3/`, ignorado pelo Git
- Parser Quarry: `customizations/datasets/bots-v3/parse_botsv3.py`
- Importador: `customizations/datasets/bots-v3/import_to_ingest.py`
- Validador/demo: `customizations/datasets/bots-v3/validate_botsv3.py`
- Hunt brief: `customizations/hunts/bots-v3/wayne-ransomware-exfiltration.yaml`

Estado validado no ambiente atual:

```text
Arquivo baixado: datasets/bots-v3/archives/botsv3_data_set.tgz
MD5: d7ccca99a01cff070dff3c139cdc10eb
Eventos normalizados: 524.580
Eventos marcados no cenário Wayne ransomware/exfiltration: 498
```

### Como preparar

```bash
mkdir -p datasets/bots-v3/{archives,extracted,normalized,manifest}
curl -L https://botsdataset.s3.amazonaws.com/botsv3/botsv3_data_set.tgz \
  -o datasets/bots-v3/archives/botsv3_data_set.tgz
md5sum datasets/bots-v3/archives/botsv3_data_set.tgz
tar -xzf datasets/bots-v3/archives/botsv3_data_set.tgz -C datasets/bots-v3/extracted
python3 customizations/datasets/bots-v3/parse_botsv3.py
```

### Como validar a demo

```bash
python3 customizations/datasets/bots-v3/validate_botsv3.py
```

Artefatos gerados:

- `datasets/bots-v3/normalized/wayne_ransomware_timeline.json`
- `datasets/bots-v3/normalized/attack_graph.json`
- `datasets/bots-v3/normalized/mitre_heatmap.json`
- `datasets/bots-v3/normalized/federated_search_sample.json`
- `datasets/bots-v3/normalized/investigation_ledger_sample.jsonl`

### Como importar no Quarry

Dry-run:

```bash
python3 customizations/datasets/bots-v3/import_to_ingest.py --dry-run --limit 1000
```

Importação real quando `services/ingest` estiver ativo:

```bash
python3 customizations/datasets/bots-v3/import_to_ingest.py \
  --ingest-url http://localhost:8080/v1/ingest/batch \
  --batch-size 500
```

A importação real publica no ingest do Quarry, que encaminha para Kafka e permite busca federada/graph/ledger no runtime. Em ambiente compartilhado, validar primeiro em `--dry-run` para evitar carga acidental.
