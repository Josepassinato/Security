# Demo Cinematografica

## Objetivo

A demo hero do Quarry apresenta uma investigacao de fraude Pix organizada em 3 a 5 minutos, usando somente dados sinteticos da fintech ficticia FinPlay Pagamentos. A rota principal e `/demo-cinematografica`.

## Narrativa

Brief pre-carregado:

> Investigar possivel fraude Pix organizada na FinPlay Pagamentos: 500 transacoes suspeitas em 30 dias, contas recem-criadas recebendo valores fracionados e repasses em cadeia para possiveis contas-laranja.

O fluxo mostra, em ordem:

1. Brief recebido em portugues.
2. Hipoteses priorizadas com confianca.
3. Queries com barras de progresso.
4. Findings em cards visuais.
5. Attack graph animado.
6. MITRE heatmap atualizado em tempo real.
7. Painel Cost vs Human Analyst.
8. Final reveal com relatorio de 10 paginas.

## Timing

O roteiro foi calibrado para estes marcos:

| Marco | Limite | Configurado |
| --- | ---: | ---: |
| Brief para primeira hipotese | <15s | 11s |
| Primeira hipotese para primeira query | <10s | 9s |
| Primeira query para primeiro finding | <30s | 29s |
| Primeiro finding para correlacao | <60s | 56s |
| Correlacao para relatorio | <90s | 85s |
| Total | 3-5 min | 4m30s |

Para gravacao ou ensaio rapido, use `?speed=fast&record=1`.

## Reset automatico

A tela reinicia automaticamente a cada 6 horas enquanto estiver aberta. O botao de reinicio manual tambem volta o roteiro para o inicio.

## Offline

A demo nao depende de API externa em runtime. O cenario, eventos agregados, findings, grafo, MITRE e relatorio estao embarcados no web app para funcionar mesmo se a internet cair durante o pitch.

## Testes

Executar:

```bash
pnpm --filter @quarry/web test -- cinematicScenario.test.ts
pnpm --filter @quarry/web type-check
```

O teste `cinematicScenario.test.ts` executa 10 checagens deterministicas do roteiro e valida os limites de timing do CARD-013.

## Videos de backup

Com o web app rodando em `http://127.0.0.1:3000`, grave as tres versoes:

```bash
pnpm demo:cinematic:record -- --base-url http://127.0.0.1:3000/demo-cinematografica --duration 28
```

Os arquivos sao gerados em `artifacts/demo-videos/`:

- `demo-cinematografica-executive.mp4`
- `demo-cinematografica-technical.mp4`
- `demo-cinematografica-backup.mp4`

## Checklist humano

Antes de pitch presencial, validar com 3 pessoas nao-tecnicas:

1. Se entenderam o problema em menos de 30 segundos.
2. Se perceberam valor economico no painel Cost vs Human Analyst.
3. Se o final reveal gerou confianca para uma conversa comercial.
