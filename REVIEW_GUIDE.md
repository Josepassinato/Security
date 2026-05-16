# Quarry Review Guide

Este guia existe para uma revisao externa completa do produto sem expor
segredos, dados brutos ou acesso irrestrito a VPS.

## Escopo esperado da revisao

- Arquitetura do produto e separacao entre frontend, API, agentes, realtime e
  datasets.
- Qualidade do codigo, riscos de seguranca, dependencias e pontos de
  escalabilidade.
- Fluxo da demo cinematografica e clareza do produto para apresentacao.
- Integracao dos datasets sinteticos, hunts e investigation ledger.
- Runbooks, deploy, backups e riscos operacionais documentados.

## Como rodar localmente

1. Clone o repositorio privado.
2. Instale as dependencias com `pnpm install`.
3. Use `.env.example` como referencia. Nunca solicite ou commite `.env` real.
4. Rode os testes relevantes:

```bash
pnpm --filter @quarry/web test -- src/components/demo/cinematicScenario.test.ts
pnpm --filter @quarry/web build
```

5. Para validar o deploy vivo, use a URL publica fornecida pelo owner:
   `https://quarry.12brain.org`.

## O que nao esta no GitHub

Os itens abaixo ficam na VPS ou em armazenamento de artefatos, nao no GitHub:

- `.env` e qualquer segredo operacional.
- Bancos, volumes Docker e backups.
- Datasets brutos `.jsonl`/`.csv` gerados.
- Clones de datasets grandes, como BOTS v3.
- `node_modules`, builds, caches e outputs temporarios.

O codigo que gera, ingere ou documenta esses artefatos fica versionado no
GitHub. Os dados pesados devem ser restaurados por script, pelo gerador ou por
backup controlado.

## Como comentar a revisao

Preferir Pull Request ou GitHub Issues com uma issue por problema real:

- `security`: risco de seguranca ou segredo exposto.
- `architecture`: desenho, separacao de responsabilidades ou escalabilidade.
- `bug`: comportamento incorreto.
- `ux`: friccao na demo ou no painel.
- `ops`: deploy, backup, monitoramento ou runbook.

## Regras de seguranca para o revisor

- Nao pedir acesso root a VPS para revisao inicial.
- Nao pedir chaves de API em texto aberto.
- Nao commitar credenciais, tokens, dumps ou arquivos `.env`.
- Se encontrar segredo exposto, comunicar fora do GitHub antes de comentar o
  valor publicamente.
- Se precisar testar a VPS, solicitar usuario temporario limitado.

