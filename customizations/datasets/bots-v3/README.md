# BOTS v3 no Quarry

Este diretório contém o pipeline local para usar o dataset Splunk BOTS v3 como demo enterprise do Quarry. O corpus bruto fica fora do Git em `datasets/bots-v3/`.

## Fonte

- Repositório: <https://github.com/splunk/botsv3>
- Download: <https://botsdataset.s3.amazonaws.com/botsv3/botsv3_data_set.tgz>
- MD5 esperado: `d7ccca99a01cff070dff3c139cdc10eb`
- Licença: CC0-1.0, conforme o repositório upstream

O BOTS v3 é distribuído em formato Splunk pré-indexado. Por isso, o parser lê `rawdata/journal.gz`, extrai registros imprimíveis e normaliza eventos JSON e AWS VPC Flow para JSONL do Quarry.

## Layout local

```text
datasets/bots-v3/
  archives/botsv3_data_set.tgz
  extracted/botsv3_data_set/
  normalized/botsv3_events.jsonl.gz
  manifest/manifest.json
```

## Parser

```bash
python3 customizations/datasets/bots-v3/parse_botsv3.py
```

Saída esperada no ambiente atual:

```json
{
  "status": "ok",
  "events_total": 524580,
  "md5_ok": true
}
```

Teste rápido:

```bash
python3 customizations/datasets/bots-v3/parse_botsv3.py \
  --limit 1000 \
  --output datasets/bots-v3/normalized/sample_botsv3_events.jsonl.gz \
  --manifest datasets/bots-v3/manifest/sample_manifest.json
```

## Importação para ingest

Dry-run, sem chamar o serviço:

```bash
python3 customizations/datasets/bots-v3/import_to_ingest.py --dry-run --limit 1000
```

Importação real, quando o `services/ingest` estiver ativo e isolado:

```bash
python3 customizations/datasets/bots-v3/import_to_ingest.py \
  --ingest-url http://localhost:8080/v1/ingest/batch \
  --batch-size 500
```

O payload enviado segue o contrato do ingest:

```json
{
  "connector_id": "bots-v3-wayne-demo",
  "connector_type": "bots-v3",
  "source_format": "botsv3_normalized_json",
  "events": []
}
```

## Validação da demo Wayne Enterprises

```bash
python3 customizations/datasets/bots-v3/validate_botsv3.py
```

A validação gera artefatos locais em `datasets/bots-v3/normalized/`:

- `wayne_ransomware_timeline.json`
- `attack_graph.json`
- `mitre_heatmap.json`
- `federated_search_sample.json`
- `investigation_ledger_sample.jsonl`

O cenário de hunt fica em `customizations/hunts/bots-v3/wayne-ransomware-exfiltration.yaml` e usa a pergunta:

```text
Investigar possível ransomware deployment com exfiltração prévia
```

## Observação operacional

O parser e a validação funcionam offline. A ingestão Kafka, a busca federada real e o Investigation Ledger vivo dependem do runtime Quarry estar ativo. Em ambiente compartilhado, use `--dry-run` até o stack estar isolado.
