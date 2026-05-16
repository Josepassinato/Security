# Criando detections BR fintech no Quarry

Este guia documenta o fluxo usado no CARD-007 para criar regras Sigma especificas de fintech brasileira.

## Onde criar

Use sempre customizations/detections/sigma/br-fintech/.

Nao coloque regras verticais brasileiras dentro de detections/, porque esse diretorio pertence ao codigo herdado e ao corpus de deteccoes upstream.

## Fluxo recomendado

1. Escolha um pattern em customizations/threat-intel/br-fintech/patterns/.
2. Defina a fonte de dados: pix_gateway, auth_service, open_finance, sysmon, android, banking_app ou equivalente.
3. Escreva uma regra Sigma com selecao especifica, filtro de falso positivo e campos de investigacao.
4. Inclua tags vertical.fintech_br, quarry.pattern.ID e quarry.severity.level.
5. Rode validacao com pysigma.
6. Quando o runtime Quarry estiver ativo, importe via Detection-as-Code API e confirme exibicao no Detection Catalog.

## Status do CARD-007

O repositorio contem 40 regras Sigma BR fintech distribuidas entre Pix, tomada de conta, fraude de pagamento, malware bancario e Open Finance. A etapa estatica esta concluida. As etapas de importacao via API, validacao na UI e teste contra dataset dependem do Quarry rodando e do dataset sintetico do CARD-009.
