# Fronteira entre GitHub, VPS e artefatos

Este projeto usa tres camadas. A regra e simples: o GitHub guarda o codigo e a
historia tecnica; a VPS guarda a operacao viva; artefatos grandes ficam fora do
Git normal.

## 1. GitHub: fonte do codigo

O repositorio privado e o lugar certo para:

- codigo-fonte;
- telas, APIs, agentes e servicos;
- Dockerfiles e `docker-compose`;
- documentacao, runbooks e ADRs;
- testes e scripts;
- geradores de dataset;
- manifests, checksums e metadados pequenos;
- templates, prompts e configuracoes sem segredo.

O GitHub nao deve receber `.env`, senhas, chaves privadas, bancos, backups,
`node_modules`, builds, caches ou datasets brutos grandes.

## 2. VPS: casa montada e funcionando

A VPS e o ambiente operacional. Ela guarda aquilo que faz o produto rodar:

- containers e processos supervisionados;
- volumes Docker;
- banco de dados e filas;
- `.env` real e configuracoes sensiveis;
- datasets gerados ou importados;
- arquivos temporarios de build/deploy;
- logs e backups locais;
- Nginx, SSL e configuracao do dominio publico.

Para o Quarry atual, a referencia operacional e:

- projeto: `/root/projetos/quarry`;
- dominio: `https://quarry.12brain.org`;
- app web local: `127.0.0.1:3014`;
- API local: `127.0.0.1:8014`;
- compose publico: `docker-compose.demo.yml`;
- env publico local: `.env.quarry-public.local`.

Esses itens podem ser auditados na VPS, mas nao devem ser empurrados para o
GitHub quando forem segredos, dados gerados ou estado runtime.

## 3. Artefatos grandes

Arquivos grandes devem seguir esta politica:

- menos de 50 MB: pode ficar no Git, se fizer sentido como codigo/documentacao;
- 50 MB a 100 MB: avaliar Git LFS;
- acima de 100 MB: nunca commitar no Git normal;
- datasets brutos: preferir storage externo, DVC ou backup da VPS;
- videos, PDFs, PPTX e binarios de entrega: usar Git LFS quando versionados.

O arquivo `.gitattributes` ja prepara o repo para Git LFS em binarios comuns.
Isso vale para novos arquivos ou futuras alteracoes. Nao foi feita reescrita de
historico para converter arquivos ja enviados.

## Fluxo recomendado para revisao externa

1. Adicionar o revisor ao repositorio privado com acesso temporario.
2. Enviar o `REVIEW_GUIDE.md` como ponto de partida.
3. Compartilhar a demo publica e credenciais temporarias por canal separado.
4. Manter datasets brutos fora do GitHub; se necessario, entregar por storage
   controlado ou permitir geracao local.
5. Receber achados via Pull Request comments ou GitHub Issues.
6. Remover o acesso do revisor ao fim do trabalho.
7. Rotacionar qualquer credencial que tenha sido usada no processo.

## Quando separar em outro repositorio

Separar repositorio so vale quando houver produto independente ou ciclo de vida
proprio. Tamanho, sozinho, nao e bom motivo.

Possiveis repositorios futuros:

- `quarry-connectors`, se conectores virarem pacote separado;
- `quarry-infra`, se a operacao crescer com ambientes multiplos;
- `quarry-dataset-manifests`, se datasets tiverem ciclo proprio com DVC;
- `quarry-pitch`, se materiais comerciais precisarem controle de acesso
  diferente do codigo.

Enquanto o produto ainda esta em validacao, o monorepo principal continua sendo
a melhor opcao.

