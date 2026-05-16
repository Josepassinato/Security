# CARD-009 - Dataset Sintetico Brasileiro

Gerador deterministico do dataset FinPlay Pagamentos, uma fintech ficticia de Sao Paulo com 50.000 clientes sinteticos.

## Arquivos

- generator.py: gera clientes e eventos JSONL.
- validate_dataset.py: valida contagens, JSONL e cenarios injetados.
- import_to_ingest.py: envia JSONL para o endpoint HTTP /v1/ingest/batch quando o Quarry estiver rodando.
- output/: dataset gerado localmente.

## Volumes gerados

- 100.000 transacoes Pix legitimas
- 500 transacoes Pix fraudulentas
- 50.000 logins de mobile banking
- 200 tentativas de account takeover
- 10.000 acessos Open Finance
- 30 anomalias Open Finance
- 5.000 criacoes de boleto
- 50 boletos fraudulentos
- 120 eventos de suporte para hunts operacionais

Total: 165.900 eventos, alem de 50.000 clientes sinteticos em CSV. Os 120 eventos adicionais sao evidencias de suporte para hunts de acesso privilegiado, exfiltracao, AML cripto e falsa central.

## Cenarios injetados

- SCN-001-money-mule-ring: money mule ring com 20 contas.
- SCN-002-sim-swap-high-value: SIM swap em conta high-value.
- SCN-003-open-finance-scraping: scraping anomalo Open Finance.
- SCN-004-boleto-fraud-campaign: campanha de boleto fraudulento.

## Uso

Gerar:

python3 customizations/datasets/br-fintech-generator/generator.py

Validar:

python3 customizations/datasets/br-fintech-generator/validate_dataset.py

Dry-run de importacao:

python3 customizations/datasets/br-fintech-generator/import_to_ingest.py --dry-run

Importar quando o Quarry estiver rodando:

python3 customizations/datasets/br-fintech-generator/import_to_ingest.py --ingest-url http://localhost:8001/v1/ingest/batch

## Restricoes

Todo dado e sintetico. A persona FinPlay Pagamentos e ficticia. CPFs, nomes, contas, chaves Pix, documentos, bancos, IPs e logs sao gerados por seed e nao representam clientes reais.
