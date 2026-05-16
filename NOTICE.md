# NOTICE — Atribuições e licenças de terceiros

Quarry é um produto da **Increase Trainer Inc.** baseado em fork independente do projeto open-source AiSOC. Este arquivo lista todas as atribuições obrigatórias por força das licenças do código e dos corpora de detecção herdados.

---

## 1. AiSOC (base do código)

- **Repositório upstream:** [github.com/beenuar/AiSOC](https://github.com/beenuar/AiSOC)
- **Commit forkado:** `28ce9f6bba8d997de04244be963ea3f2c38f0084`
- **Data do fork:** 2026-05-15
- **Licença:** MIT — Copyright (c) 2024-present AiSOC contributors
- **Texto da licença:** ver [`LICENSE`](LICENSE)
- **Cláusula MIT mantida:** "The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software." Esta nota preserva tal atribuição em Quarry.

---

## 2. Corpora de detecção redistribuídos (herdados do AiSOC)

O diretório [`detections/`](detections/) contém regras importadas de quatro corpora upstream. Cada regra carrega um bloco `provenance` documentando origem, ID original, SHA do commit upstream e licença.

### 2.1 SigmaHQ

- **Repositório:** [SigmaHQ/sigma](https://github.com/SigmaHQ/sigma)
- **Licença:** [Detection Rule License (DRL) 1.1](https://github.com/SigmaHQ/Detection-Rule-License)
- **Classificação:** Permissiva, redistribuição autorizada com atribuição preservada
- **Localização:** `detections/sigma-imports/`
- **Atribuição:** "Rule originally published by SigmaHQ under DRL-1.1. Provenance preserved per rule in the `provenance` block."

### 2.2 MITRE Cyber Analytics Repository (CAR)

- **Repositório:** [mitre-attack/car](https://github.com/mitre-attack/car)
- **Licença:** Apache-2.0
- **Localização:** `detections/car-imports/`

### 2.3 Splunk Security Content

- **Repositório:** [splunk/security_content](https://github.com/splunk/security_content)
- **Licença:** Apache-2.0
- **Localização:** `detections/splunk-imports/`

### 2.4 Chronicle Detection Rules

- **Repositório:** [chronicle/detection-rules](https://github.com/chronicle/detection-rules)
- **Licença:** Apache-2.0
- **Localização:** `detections/chronicle-imports/`

---

## 3. Biblioteca de skills de cibersegurança

### 3.1 Anthropic Cybersecurity Skills

- **Repositório:** [mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills)
- **Licença:** Apache-2.0
- **Localização:** `customizations/skills/anthropic-cybersec/`
- **Uso:** base de conhecimento operacional para lookup/RAG dos agentes Quarry
- **Atribuição:** mantida no clone original, no índice local `customizations/skills/anthropic-cybersec/.quarry-index/skills_index.jsonl` e na documentação `docs/pt-br/usando-skills-library.md`.

---

## 4. Datasets de demonstração

### 4.1 Splunk BOTS v3

- **Repositório:** [splunk/botsv3](https://github.com/splunk/botsv3)
- **Licença:** CC0-1.0, conforme `datasets/bots-v3/source/LICENSE`
- **Dataset:** `botsv3_data_set.tgz`, MD5 `d7ccca99a01cff070dff3c139cdc10eb`
- **Localização local:** `datasets/bots-v3/` fica fora do Git por tamanho; parser e importador ficam em `customizations/datasets/bots-v3/`.
- **Uso:** demo Wayne Enterprises para investigação de ransomware com exfiltração prévia.

---

## 5. Dependências Python notáveis

### 5.1 pysigma — LGPL-2.1

- **Pacote:** [`pysigma`](https://pypi.org/project/pysigma/) (e `pysigma-backend-opensearch`)
- **Licença:** GNU Lesser General Public License v2 (LGPL-2.1)
- **Uso:** linkagem dinâmica via `import` em Python (compatível com SaaS hosted closed-source)
- **Obrigação:** se Quarry for distribuído como binário/imagem que o cliente executa, o cliente deve poder substituir a versão de pysigma. Para SaaS cloud-hosted onde o cliente nunca recebe o binário, LGPL não gera obrigação de distribuição.

### 5.2 Demais dependências

Todas as outras dependências Python e Node são MIT, Apache-2.0 ou BSD. SBOM completo será gerado e versionado em card próximo.

---

## 6. Dependências Node notáveis

- Next.js (MIT), React (MIT), Tailwind CSS (MIT), framer-motion (MIT), Cytoscape (MIT), Zustand (MIT), recharts (MIT), Monaco Editor (MIT), `@modelcontextprotocol/sdk` (MIT)

Nenhuma incompatibilidade comercial detectada.

---

## 7. Marcas

- "AiSOC" é marca dos contribuidores do projeto AiSOC. Quarry usa "AiSOC" apenas em contexto de atribuição histórica ou referência técnica, não como identificação do produto.
- "MITRE", "MITRE ATT&CK", "ATT&CK" são marcas registradas de The MITRE Corporation.
- "Splunk", "Chronicle", "Google Cloud" são marcas dos seus respectivos donos.
- "Quarry" é o nome em uso pela Increase Trainer Inc. para este produto.

---

## 8. Como atualizar este arquivo

Sempre que um novo corpus de detecções ou uma dependência com licença não-permissiva for adicionada, este arquivo deve ser atualizado **antes** do merge. CI futuro vai validar atribuições automaticamente a partir dos blocos `provenance` em `detections/` e do SBOM.

---

_Última atualização: 2026-05-16._
