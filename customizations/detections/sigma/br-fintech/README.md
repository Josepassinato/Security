# Regras Sigma BR Fintech

Este diretorio contem regras Sigma especificas do Quarry para operacao de fintech brasileira. As regras complementam o corpus herdado do projeto base e devem permanecer separadas em customizations/.

## Categorias

- pix-fraud: fraude Pix, contas mulas, falso estorno e dispersao de valores.
- account-takeover: SIM swap, WhatsApp clonado, MFA degradado e tomada de conta.
- payment-fraud: boleto adulterado, QR/Pix e divergencia de beneficiario.
- banking-malware: GoPix, mao fantasma, clipboard hijack e abuso de acessibilidade.
- open-finance: consentimentos, TPP/AISP, certificados e abuso de tokens Open Finance.

## Convencoes obrigatorias

Toda regra customizada deve conter status experimental, author Quarry - Increase Trainer Inc., tag vertical.fintech_br, tag quarry.pattern.ID e tag quarry.severity.level.

## Validacao local

Use pysigma para parsear todos os arquivos em customizations/detections/sigma/br-fintech antes de importar via API.

## Status

Este conjunto fecha o CARD-007 no nivel estatico: regras criadas e parseaveis. Importacao via API, exibicao no catalogo e teste com dataset dependem do runtime Quarry e do CARD-009.
