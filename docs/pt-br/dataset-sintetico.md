# Dataset sintetico brasileiro - CARD-009

Este documento descreve o dataset sintetico FinPlay Pagamentos criado para demos e desenvolvimento do Quarry no mercado brasileiro.

## Persona ficticia

- Nome: FinPlay Pagamentos
- Localizacao: Sao Paulo, SP
- Clientes ativos sinteticos: 50.000
- Produtos: conta digital, cartao e Pix
- Natureza: empresa totalmente ficticia; nenhum dado real foi usado ou anonimizado.

## Localizacao dos arquivos

Gerador:
customizations/datasets/br-fintech-generator/

Output gerado:
customizations/datasets/br-fintech-generator/output/

Arquivos principais:

- customers.csv: 50.000 clientes sinteticos
- pix_legitimate.jsonl: 100.000 transacoes Pix legitimas
- pix_fraudulent.jsonl: 500 transacoes Pix fraudulentas
- auth_logins.jsonl: 50.000 logins mobile banking
- account_takeover_attempts.jsonl: 200 tentativas de account takeover
- open_finance_accesses.jsonl: 10.000 acessos Open Finance
- open_finance_anomalies.jsonl: 30 anomalias Open Finance
- boleto_creations.jsonl: 5.000 criacoes de boleto
- boleto_fraudulent.jsonl: 50 boletos fraudulentos
- supporting_hunt_evidence.jsonl: 120 evidencias de suporte para hunts operacionais
- manifest.json: contagens, hashes, cenarios e metadados

Total de eventos JSONL: 165.900.

## Schemas simulados

Pix usa um SPI simplificado com end_to_end_id, tx_id, settlement_method, initiation_type, payer, payee, amount_brl, status, device_id, ASN e rotulo de fraude.

Auth usa logs OAuth2 + biometria com grant_type, client_id, scope, biometria, device_id, user_agent, geo, MFA, outcome e risk_signal.

Open Finance usa formato inspirado no ecossistema Bacen/Open Finance Brasil: consent_id, TPP, status de certificado, escopos, endpoint, ASN de origem, volume em janela e risk_signal.

Boleto usa JSON estruturado com boleto_id, linha_digitavel_hash, beneficiario esperado, beneficiario pago, mismatch e valor.

Eventos de suporte incluem admin_audit, data_access, crypto-ledger e support-fraud para cobrir hunts que nao cabem nos quatro fluxos transacionais principais.

## Cenarios injetados

SCN-001-money-mule-ring:
Money mule ring com 20 contas novas, recebimento Pix de multiplas origens e dispersao para destino comum. Alimenta HUNT-PIX-001 e HUNT-MULE-001.

SCN-002-sim-swap-high-value:
SIM swap em conta high-value com sinais de novo device, MFA suspeito, impossible travel e Pix de alto valor. Alimenta HUNT-SIM-001 e HUNT-ATO-001.

SCN-003-open-finance-scraping:
TPP/AISP com consumo anomalo de API, escopo maximo, ASN divergente, certificado revogado ou consentimento revogado ainda usado. Alimenta HUNT-OFI-001.

SCN-004-boleto-fraud-campaign:
Campanha de boleto adulterado com divergencia de beneficiario, novo favorecido e valores suspeitos. Alimenta HUNT-BOL-001.

Evidencias de suporte:
Cobrem HUNT-VSH-001, HUNT-PRIV-001, HUNT-EXFIL-001 e HUNT-AML-001.

## Comandos

Gerar dataset:
python3 customizations/datasets/br-fintech-generator/generator.py

Validar dataset:
python3 customizations/datasets/br-fintech-generator/validate_dataset.py

Validar cobertura das hunts:
python3 customizations/datasets/br-fintech-generator/validate_hunt_coverage.py

Dry-run de importacao:
python3 customizations/datasets/br-fintech-generator/import_to_ingest.py --dry-run

Importacao real quando o runtime Quarry estiver ativo:
python3 customizations/datasets/br-fintech-generator/import_to_ingest.py --ingest-url http://localhost:8001/v1/ingest/batch

## Status de ingestao

A importacao real depende do Quarry runtime com ingest service ativo. Nesta VPS compartilhada a stack completa ainda nao deve ser subida antes do corte do MVP, conforme CARD-002 e docs/SKILL.md. Por isso o CARD-009 entrega o importador pronto e validado em dry-run. Quando a stack estiver ativa, o mesmo script envia os lotes para /v1/ingest/batch com X-Tenant-ID.

## Resultado da validacao local

validate_dataset.py confirmou as contagens obrigatorias, JSONL valido e presenca dos quatro cenarios principais.

validate_hunt_coverage.py confirmou eventos correspondentes para os 10 templates do CARD-008:

- HUNT-PIX-001: 360 eventos
- HUNT-MULE-001: 360 eventos
- HUNT-ATO-001: 280 eventos
- HUNT-SIM-001: 280 eventos
- HUNT-OFI-001: 30 eventos
- HUNT-BOL-001: 50 eventos
- HUNT-VSH-001: 150 eventos
- HUNT-PRIV-001: 30 eventos
- HUNT-EXFIL-001: 30 eventos
- HUNT-AML-001: 30 eventos

## Garantias

Todo dado e sintetico. CPFs, nomes, contas, chaves Pix, documentos, IPs, TPPs e eventos sao gerados por seed. A FinPlay Pagamentos nao representa instituicao real.
