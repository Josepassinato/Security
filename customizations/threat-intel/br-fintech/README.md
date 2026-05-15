# BR-Fintech Threat Intelligence Pack

Catálogo de padrões de ataque (TTPs) observados contra fintechs e bancos
brasileiros, construído a partir de fontes públicas verificáveis.

Este pacote alimenta o Quarry: cada pattern é o seed para detecções,
hunts, dashboards de risco e playbooks de resposta.

---

## Princípio inegociável

**Todo pattern aqui catalogado tem pelo menos uma fonte pública com URL real.**
Sem fonte = sem entrada. Honestidade > volume.

Quando uma fonte estiver atrás de paywall ou exigir login, marcamos
`access_note: paywall` ou `access_note: login required` para o revisor
saber.

Se um padrão for plausível mas a sessão de pesquisa não rendeu fonte
sólida, ele entra na seção **Candidatos** mais abaixo (não em `patterns/`).

---

## Estrutura do diretório

```
customizations/threat-intel/br-fintech/
├── README.md            (este arquivo)
├── index.yaml           (lista mestre de todos os patterns)
├── schema.yaml          (JSON Schema validando cada pattern)
└── patterns/
    ├── PIX-001-money-mule.yaml
    ├── PIX-002-golpe-pix-errado.yaml
    ├── PIX-003-pix-agendado-cancelado.yaml
    ├── VSH-001-falsa-central.yaml
    ├── SEN-001-whatsapp-clonado.yaml
    ├── ATO-001-sim-swap.yaml
    ├── BOL-001-boleto-adulterado.yaml
    ├── QR-001-qr-sticker-swap.yaml
    ├── EWL-001-ewallet-card-provisioning.yaml
    ├── MAL-001-gopix-trojan.yaml
    └── MAL-002-mao-fantasma-rat.yaml
```

---

## Convenção de IDs

| Prefixo | Categoria                      |
|---------|--------------------------------|
| `PIX`   | Fraudes específicas de PIX     |
| `ATO`   | Account Takeover               |
| `BOL`   | Fraudes de Boleto              |
| `QR`    | Fraudes de QR Code             |
| `VSH`   | Vishing / Voice phishing       |
| `SEN`   | Engenharia Social genérica     |
| `EWL`   | E-Wallet (Apple/Google Pay)    |
| `MAL`   | Malware bancário               |
| `OFI`   | Open Finance abuse (reservado) |

Formato: `PREFIXO-NNN` (três dígitos zero-padded, ex.: `PIX-001`).

---

## Schema de cada pattern

Cada `.yaml` em `patterns/` segue `schema.yaml` (JSON Schema Draft 2020-12).
Campos obrigatórios:

- `id` — formato `[A-Z]{2,4}-[0-9]{3}`
- `name`
- `category`
- `severity` — `low` | `medium` | `high` | `critical`
- `description` — em português, com nota explicando por que é BR-específico
- `sources` — pelo menos 1 URL real, com publisher + date + title
- `br_specific` — boolean (true = variante distinta de TTP internacional)
- `quarry_status` — `documented` | `rule_drafted` | `rule_active` | `deprecated`

Campos opcionais mas recomendados:

- `mitre_techniques` — array de `{id, name}` (formato MITRE ATT&CK)
- `data_sources_required` — telemetria/logs necessários para detecção
- `indicators` — heurísticas com thresholds
- `related_patterns` — IDs de patterns que costumam aparecer juntos
- `notes` — notas livres para revisores

Para validar:

```bash
# Exemplo usando ajv (npm)
ajv compile -s <(yq -o=json '.' schema.yaml)
ajv validate -s <(yq -o=json '.' schema.yaml) -d <(yq -o=json '.' patterns/PIX-001-money-mule.yaml)
```

---

## Patterns nesta versão (v0.1.0 — seed inicial)

| ID       | Nome                                         | Severidade | BR-específico |
|----------|----------------------------------------------|------------|---------------|
| PIX-001  | Money Mule via Conta Digital Nova            | high       | sim           |
| PIX-002  | Golpe do PIX Errado (Falso Estorno)          | high       | sim           |
| PIX-003  | PIX Agendado com Cancelamento Pré-Liquidação | medium     | sim           |
| VSH-001  | Falsa Central de Atendimento (Vishing+Spoof) | critical   | sim           |
| SEN-001  | WhatsApp Clonado para Golpe Familiar PIX     | critical   | sim           |
| ATO-001  | Account Takeover via SIM Swap                | critical   | não           |
| BOL-001  | Boleto Adulterado (Bolware / Reboleto)       | high       | sim           |
| QR-001   | QR Code Sticker Swap em Estabelecimento      | medium     | sim           |
| EWL-001  | Cartão em E-Wallet (Apple/Google Pay)        | high       | não           |
| MAL-001  | GoPix Trojan (clipboard PIX)                 | critical   | sim           |
| MAL-002  | Golpe da Mão Fantasma (RATs)                 | critical   | sim           |

> **Nota:** PIX-001 aparece como `mule_network` em sua categoria principal,
> mas está fortemente relacionado a PIX (combo via fluxo de saída).

Total: 11 patterns documentados (versão do índice traz contagem detalhada
por severidade e categoria em `index.yaml`).

---

## Candidatos — patterns para próximas sessões

Padrões que aparecem em literatura/casos mas onde a pesquisa inicial não
rendeu fonte adequada (URL pública, com publisher e data clara). Próximas
sessões devem investigar e elevar a `patterns/` se encontrarem fonte.

1. **Open Finance — consentimento abusivo / phishing de fluxo de consent**
   Risco apontado por FEBRABAN ("desafio central é engenharia social para
   obter consentimentos fraudulentos"), mas FEBRABAN também afirma que
   "após cinco anos de Open Finance não há notícias significativas sobre
   golpes/fraudes/vazamento usando Open Finance". Sem incidente público
   concreto, fica como candidato (não como pattern ativo).
   - Buscar: relatos do Estruturador do Open Finance Brasil, BACEN,
     Demarest, casos disputados em Procon.

2. **Sinqia (heist de R$ 710 milhões / US$ 130M)** — Incidente noticiado
   pela Infosecurity Magazine. Atacantes tentaram desviar R$ 710M de dois
   clientes bancários da Sinqia. Falta detalhamento técnico público para
   um pattern reproduzível (CVE? credenciais? supply chain?). Vale uma
   sessão dedicada para tentar tirar TTP do que existir.

3. **Credential stuffing contra fintechs BR específicas** — TTP global
   bem documentado em relatórios HUMAN/F5/Fortinet, mas não foram
   encontradas reportagens públicas atribuindo um incidente concreto a
   uma fintech brasileira nomeada. Catalogar quando aparecer.

4. **Falso boleto de IPVA/IPTU/multa** — variante de BOL-001, com TTP
   específico de impersonar órgãos públicos. Provável fonte: SERPRO,
   Procons estaduais. Pendente.

5. **PIX por Aproximação (NFC) — abuso recém-lançado** — funcionalidade
   relativamente nova; padrões de abuso ainda em formação. Reserva-se ID
   `PIX-004` quando houver incidente público.

6. **Drop fraud em onboarding (uso de documentos vazados para abrir conta
   em nome de terceiro)** — relacionado a PIX-001 (mula) mas com vetor
   distinto (KYC bypass). Buscar: SERASA Experian, IDfy, Unico, casos
   públicos de fintechs brasileiras.

---

## Como contribuir

1. Encontre fonte pública: relatório FEBRABAN, comunicado BACEN, threat
   report da Tempest/Kaspersky/ISH, notícia de veículo conhecido.
2. Crie `patterns/<ID>-<slug>.yaml` seguindo `schema.yaml`.
3. Adicione entrada em `index.yaml`.
4. PR / commit local com link da fonte original como evidência.

**Padrão de qualidade:**
- Pelo menos 1 fonte com URL real (preferir 3+).
- Pelo menos 2 fontes independentes para `severity: critical`.
- Descrição em português, explicando por que é (ou não) BR-específico.
- Indicators acionáveis (com threshold concreto, não vagos).
- Map para MITRE ATT&CK quando possível.

**Não-objetivo:**
- Fabricar fontes ou inventar URLs.
- Listar TTPs sem evidência de uso real no Brasil.
- Inflar o catálogo com variantes triviais.

---

## Expansão futura (alvo: 30-50 patterns)

Roadmap não-vinculante para próximas releases:

- **v0.2** (+5-7 patterns): Open Finance abuse documentado, drop fraud
  KYC bypass, falso boleto IPVA/IPTU, vishing com IA (clonagem de voz),
  golpe do motoboy (cartão físico).
- **v0.3** (+8-10 patterns): variantes regionais (golpes em cooperativas
  Sicoob/Sicredi), fraudes em maquininhas (Stone/PagSeguro skimming),
  malwares mais recentes (PixRevolution detalhado separadamente,
  Coyote, Brookial, BlueShield).
- **v0.4** (+10+ patterns): cobertura defensiva — patterns de fraude
  contra a própria fintech (insider, BIN attack, refund abuse, chargeback
  fraud específico do mercado BR).

---

## Fontes-mãe consultadas nesta versão

Lista das fontes-pai (sites/organizações) acessadas via WebSearch.
URLs específicas vivem em cada `pattern.yaml`.

**Reguladores / autorreguladores:**
- Banco Central do Brasil — bcb.gov.br (MED, MED 2.0, Resolução 403/2024)
- FEBRABAN — portal.febraban.org.br (ranking dos 10 golpes em 2024)
- Senado Federal — senado.leg.br
- Polícia Civil de Sergipe — policiacivil.se.gov.br

**Threat Intelligence:**
- Kaspersky / Securelist — securelist.com, kaspersky.com.br (GoPix,
  Ghimob, TwMobo)
- ISH Tecnologia — ish.com.br (SIM swap)
- Clavis Segurança — clavis.com.br (SIM swap)
- CISO Advisor — cisoadvisor.com.br (RATs BR exportados)

**Imprensa especializada:**
- CNN Brasil, Agência Brasil, Poder360, Exame, Estado de Minas,
  Folha Vitória, O Antagonista, Correio Braziliense, IstoÉ, O Povo,
  Tecnoblog, Canaltech, TechTudo, MacMagazine, TudoCelular.

**Fintechs / bancos (educativos):**
- Banco do Brasil (blog), Nubank (blog), Bradesco (alerta via Mixvale),
  Mercado Pago (blog), SERASA Experian, BB Seguros.

**Defesa do consumidor:**
- IDEC — idec.org.br

**Reclamações públicas:**
- Reclame Aqui (utilizado como evidência circunstancial em EWL-001).

---

## Versionamento

- Cada pattern segue versionamento implícito pelo git log do repositório
  Quarry.
- `index.yaml` mantém a versão do catálogo em `# Versão do catálogo`.
- Mudanças breaking em `schema.yaml` exigem bump major do catálogo.

---

## Licença e ética

Conteúdo é informação pública agregada para fins de defesa cibernética.
Catálogo NÃO contém:

- IOCs de atacantes individuais identificáveis (sem doxxing).
- Detalhes operacionais que ajudem o atacante (sem how-to-cracker).
- Dados de vítimas concretas (sem PII).

Catálogo CONTÉM:

- TTPs em nível de comportamento.
- Indicators heurísticos.
- Mitigações estruturais (lado defensor).

Use ético: para detectar, responder e educar usuários. Não use para
fingerprintar pessoas físicas ou perfilar consumidores fora de contexto
de prevenção de fraude.
