# Quarry — Branding Guidelines

**Última atualização:** 2026-05-15 (CARD-004 rebrand)

---

## Nome e tagline

- **Nome do produto:** Quarry
- **Owner legal:** Increase Trainer Inc.
- **Tagline EN:** Autonomous Threat Hunting for the Post-Mythos Era
- **Tagline PT-BR:** Caça Autônoma de Ameaças para a Era Pós-Mythos
- **Domínio (planejado):** `quarry.12brain.org`

### Origem do nome

"Quarry" tem dois sentidos em inglês: (1) presa caçada, (2) pedreira de onde se extrai material valioso. Ambos ressoam com SOC: presas hostis e extração de sinal de ameaça em grandes volumes de telemetria. Nome curto, registrável, sem conflito conhecido no espaço cybersecurity BR.

### O que "Era Pós-Mythos" significa

Referência interna ao aprendizado pós-Mythos sobre desenho adversarial de agentes IA: operadores podem ser hostis ou comprometidos, LLMs podem ser jailbroken, custo (tokens, API calls) é vetor de ataque. Auditoria não é feature, é restrição de design.

---

## Paleta de cores

### Primárias

| Token | Hex | Uso |
|---|---|---|
| `quarry-red` | `#8B0000` | acentos, alertas, branding mark |
| `quarry-charcoal` | `#1a1a1a` | fundos escuros, dark mode primary |
| `quarry-bone` | `#f7f4ef` | fundos claros, off-white (alinha com landing 12Brain anti-AI design) |
| `quarry-ink` | `#0a0a0a` | texto sobre claro |

### Secundárias

| Token | Hex | Uso |
|---|---|---|
| `quarry-rust` | `#a8482e` | hover de red, links visited |
| `quarry-gravel` | `#3a3a3a` | bordas, separadores dark |
| `quarry-ash` | `#9a9a9a` | texto secundário, metadata |

### Semantic colors (mantidos do upstream, ajustados)

| Token | Hex | Uso |
|---|---|---|
| `severity-high` | `#dc2626` | severidade alta |
| `severity-medium` | `#f59e0b` | severidade média |
| `severity-low` | `#3b82f6` | severidade baixa |
| `severity-info` | `#6b7280` | severidade info |

**Regra:** NÃO substituir `quarry-red` por `severity-high`. O vermelho do brand é mais escuro e é assinatura visual; severidade alta usa o vermelho mais claro (#dc2626) por legibilidade em contexto de dados.

---

## Tipografia

| Uso | Fonte | Notas |
|---|---|---|
| Headlines marketing | **Fraunces** (serif, variable) | Alinha com landing 12Brain (anti-AI design). Italic permitido em pull quotes. |
| Body marketing | **Inter** (sans, variable) | Tamanho conforto leitura longa. |
| UI dashboard | **Inter** | Tudo Inter no console autenticado — utilitário, não cinematográfico. |
| Code, logs, JSON | **JetBrains Mono** ou stack default monospace | Manter herdado do AiSOC. |

**Regra interna:** dashboards autenticados são utilitários (regra anti-AI design 12Brain), não precisam de serif. Marketing/landing/about pages SIM seguem o design Fraunces+Inter.

---

## Logo

- **Logo mark principal:** `apps/web/public/logo-mark.svg` (120×120, hexágono estilizado com Q-mineração)
- **Favicon:** `apps/web/public/favicon.svg` (32×32)
- **Placeholder atual.** Versão final será encomendada quando MVP estiver de pé.

---

## Voz e tom

- **Direto, sem fluff.** Sem "revolucione", "transforme", "AI-powered" (regra anti-AI design 12Brain).
- **Específico.** Quantificar quando possível: "reduz 87% dos alertas redundantes" > "menos ruído".
- **Honesto.** Limites conhecidos do produto declarados, não escondidos. Inclui seção "Para quem Quarry não é" (disqualifier).
- **Português brasileiro técnico** em conteúdo BR; inglês em código + commits + comunicação internacional.

---

## CTAs

- **Suaves**, sem exclamação. Estilo "ver a plataforma →", "começar piloto →", "ler caso de uso →".
- **Evitar:** "Comece agora!", "Experimente grátis!", "Revolucione seu SOC!".

---

## O que NÃO usar

- ❌ Emoji em headings
- ❌ Gradient emerald-teal-purple (anti-AI design)
- ❌ Avatares stock photo
- ❌ Grid 4-col simétrico de métricas redondas (95%, 99%, etc.)
- ❌ "How it works" 3-step com ícones circulares
- ❌ Frases "AI-powered", "revolucione", "transforme"

---

## Atribuição original (preservada)

- Logo do AiSOC original (`README.AISOC.md` linha 3) **não é usado** em Quarry. Quarry tem identidade visual própria.
- Atribuição obrigatória em `NOTICE.md` mantém crédito do código fonte ao AiSOC contributors.
