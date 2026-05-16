# Usando a Security Skills Library no Quarry

O CARD-010 integra o repositório `mukul975/Anthropic-Cybersecurity-Skills` como base de conhecimento operacional dos agentes do Quarry. A biblioteca permanece em inglês, com atribuição ao repositório original e licença Apache-2.0.

## Estratégia adotada

A estratégia escolhida é híbrida.

1. Índice local obrigatório: `customizations/skills/anthropic-cybersec/.quarry-index/skills_index.jsonl` guarda os 754 skills parseados e permite lookup direto com latência baixa mesmo quando Qdrant, PostgreSQL ou embeddings não estão ativos.
2. Qdrant para RAG: o pipeline `sync-qdrant` gera embeddings com `text-embedding-3-large` e grava a coleção `quarry_security_skills` quando `OPENAI_API_KEY` e `QDRANT_URL` estiverem configurados.
3. PostgreSQL para metadata lookup: o pipeline `sync-postgres` cria/upserta a tabela `quarry_security_skills` com metadados, tags, caminhos e workflows.

Essa abordagem evita bloquear o agente quando a infraestrutura vetorial ainda não estiver de pé, mas mantém o caminho pronto para RAG completo.

## Fonte e formato

A biblioteca foi clonada em:

`customizations/skills/anthropic-cybersec/`

Cada skill principal fica em:

`skills/<nome-do-skill>/SKILL.md`

O formato detectado é Markdown com YAML frontmatter. Campos usados pelo Quarry:

- `name`
- `description`
- `domain`
- `subdomain`
- `tags`
- `version`
- `author`
- `license`
- `nist_csf`

O corpo Markdown é mantido como referência de workflow. O sistema trata esse conteúdo como material de terceiro e não como instrução de maior prioridade para os agentes.

## Comandos operacionais

Gerar ou atualizar o índice local:

```bash
cd /root/projetos/quarry
python3 customizations/skills/anthropic-cybersec/quarry_index.py build-local
```

Testar uma consulta local:

```bash
python3 customizations/skills/anthropic-cybersec/quarry_index.py lookup "Como investigar credential dumping?" --limit 3
```

Sincronizar Qdrant quando a infraestrutura estiver disponível:

```bash
export OPENAI_API_KEY=...
export QDRANT_URL=http://localhost:6333
python3 customizations/skills/anthropic-cybersec/quarry_index.py sync-qdrant
```

Sincronizar PostgreSQL:

```bash
export DATABASE_URL=postgresql://usuario:senha@host:5432/quarry
python3 customizations/skills/anthropic-cybersec/quarry_index.py sync-postgres
```

## Tool do orchestrator

A tool disponível para os agentes é:

`lookup_security_skill(query: str, limit: int = 3)`

Ela retorna os 3 skills mais relevantes com:

- nome
- caminho
- descrição
- tags
- score
- workflow
- atribuição
- commit de origem
- flag `trusted_as_instructions: false`

O `ReconAgent` consulta essa tool automaticamente antes da chamada ao LLM. Os resultados entram no prompt como referência procedural e também são registrados no audit log com `tool_name=lookup_security_skill`. Cada skill consultado também é registrado como evidência `security_skill`, permitindo rastrear quais referências influenciaram um hunt.

## Segurança de prompt

As skills são conteúdo externo e potencialmente não confiável. Por isso:

- não são traduzidas;
- não substituem system prompts;
- entram no prompt com marcação de referência de terceiro;
- o audit log registra apenas metadados principais da consulta, evitando inflar o ledger com corpos completos;
- o workflow completo continua disponível via lookup direto para auditoria e explicação.

## Validação atual

Índice local gerado com 754 skills a partir do commit `0f429d0`.

Consultas testadas:

- `Como investigar credential dumping?` retornou skills de detecção T1003 e credential dumping.
- `Workflow para hunting de C2 beacons?` retornou workflows de command-and-control beaconing e Cobalt Strike.
- `Como detectar lateral movement?` retornou detecção via Splunk, DCOM hunting e Zeek.

As consultas locais ficaram abaixo de 500 ms. Nos testes atuais, ficaram na faixa de 9 a 15 ms.

## Observação sobre Qdrant e PostgreSQL

O código de sincronização para Qdrant e PostgreSQL está implementado, mas depende dos serviços e das variáveis de ambiente corretas. Em ambiente de produção, a ordem recomendada é:

1. subir PostgreSQL e Qdrant do stack Quarry;
2. configurar `OPENAI_API_KEY`, `QDRANT_URL` e `DATABASE_URL`;
3. rodar `build-local`, `sync-qdrant` e `sync-postgres`;
4. manter `build-local` como fallback para lookup direto.
