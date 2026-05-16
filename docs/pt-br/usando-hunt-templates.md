# Usando hunt templates BR fintech

Este guia documenta os hunt templates criados no CARD-008.

## Onde ficam

customizations/hunts/br-fintech/

Cada arquivo YAML descreve uma investigacao reutilizavel para analistas Quarry em portugues brasileiro.

## Templates disponiveis

- fraude-organizada-pix-contas-novas.yaml
- account-takeover-ultimas-24h.yaml
- sim-swap-correlacionado.yaml
- money-mule-networks.yaml
- phishing-falsa-central-direcionado.yaml
- fraude-boleto-larga-escala.yaml
- open-finance-api-suspeita.yaml
- acessos-privilegiados-anomalos.yaml
- exfiltracao-dados-clientes.yaml
- lavagem-cripto-adjacente.yaml

## Como usar no produto

Quando a API Quarry estiver ativa, estes templates devem ser importados para a area de Threat Hunting e filtrados por vertical: fintech_br. O analista escolhe o template, revisa hipoteses, fontes de dados e workflow, e executa a hunt em modo demo ou producao.

## Contrato minimo do YAML

Cada template deve conter id, name, language, vertical, description, hypotheses, data_sources_required, mitre_techniques_expected, related_patterns, related_sigma_rules, workflow_steps, output_format, expected_runtime_minutes, analyst_skill_level e demo_safe.

## Status do CARD-008

O repositorio contem 10 templates, cobrindo os cenarios obrigatorios principais: fraude Pix, ATO, SIM swap, money mule, phishing/falsa central, boleto, Open Finance, acessos privilegiados, exfiltracao e cripto adjacente. A importacao via API e validacao visual na UI ficam para depois do runtime Quarry e do dataset sintetico do CARD-009.
