# CARD-015 — Sovereign LLM (Mac Mini físico OU VPS Llama dedicada — modalidades opcionais)

**Para:** José Passinato
**Por:** Claude (planejado em 2026-05-24)
**Status:** 🟡 PROPOSTO — aguardando alocação de sprint
**Razão:** o air-gap mode atual (`docker-compose.airgap.yml` + Ollama llama3.2:3b) é tecnicamente um modo, mas o modelo 3B é fraco demais para investigação séria. Para sustentar o pitch "Zero exfiltration" de forma honesta e barata, o produto precisa de **modalidades opcionais documentadas** que o cliente escolhe conforme seu perfil de soberania:

- **Modalidade A** — Mac Mini M-series físico **dentro da própria fintech** (soberania física + lógica máxima, R$ ~18k CAPEX)
- **Modalidade B** — VPS dedicada hospedando Llama via Ollama/vLLM (soberania lógica, OPEX ~R$ 800-3.500/mês, sem hardware na fintech)
- **Modalidade C (default existente)** — BYOK cloud LLM (OpenAI/Anthropic/Gemini) via `llm_resolver.py`

**Estas modalidades A e B são opcionais** — não substituem o managed/self-host atual. Quem não precisa de soberania máxima continua no BYOK cloud. Quem precisa, escolhe Mac Mini (fintech grande com sala-cofre) ou VPS dedicada (fintech menor sem espaço físico).

Isso é o que diferencia Quarry de **qualquer** SOC global no mercado BR fintech regulada.

---

## Objetivo

Documentar, validar e empacotar **duas modalidades opcionais de deploy "Quarry Sovereign LLM"** que o cliente escolhe conforme seu perfil:

### Modalidade A — Sovereign Appliance (Mac Mini físico na fintech)
Mac Mini M-series rodando dentro do datacenter/sala-cofre da fintech, hospedando MLX/Ollama, conectado ao Quarry web apenas para UI. Nenhum byte sai do perímetro físico.

### Modalidade B — Sovereign VPS (Llama em VPS dedicada do cliente)
VPS dedicada (Hostinger, Hetzner, OCI, dedicada BR, etc.) hospedando Llama via Ollama ou vLLM, sob conta do próprio cliente, isolada por VPC. Quarry web conecta via VPN privada. Sem hardware físico na fintech.

### Modalidade C (default existente — não muda)
BYOK cloud LLM (OpenAI/Anthropic/Gemini) via `llm_resolver.py`. Para quem não precisa de soberania máxima.

---

**Entregas comuns às modalidades A e B:**
1. **Hardware/host reference** documentado por modalidade
2. **Stack instalada** (MLX no Mac; Ollama+vLLM no Linux VPS — recomendação baseada em benchmark por modalidade)
3. **Modelo recomendado** (Qwen 2.5 14B Instruct ou Llama 3.1 8B/70B — escolha por modalidade e por benchmark)
4. **Setup scripts**:
   - `scripts/sovereign-appliance/install-mac.sh` (Modalidade A)
   - `scripts/sovereign-appliance/install-vps-linux.sh` (Modalidade B)
5. **Documento de conformidade Bacen** explicando como cada setup atende Res. BCB 85/2021 (PSC) + LGPD (com diferenças de soberania física vs lógica)
6. **Página `/br/sovereign-llm`** na landing — pitch comercial com seletor das 3 modalidades (A/B/C)
7. **Linha de produto comercial**: SKUs separados "Sovereign Appliance" e "Sovereign VPS" com pricing + SLA

---

## Por que importa (extremamente alto)

- **Resolve o paradoxo central** do positioning: "SOC econômico + zero exfiltration" só é viável com hardware barato local
- **Vira moat físico**: nenhum SOC global (Cyble, Mandiant, CrowdStrike) entrega isso — todos exigem cloud
- **Bacen-compliant by design**: dados de PII e queries forenses **nunca saem do perímetro físico da instituição** — Res. BCB 85/2021 Art. 3 (PSC) atendida sem interpretação criativa
- **Custo absurdamente competitivo**:
  - Mac Mini M4 Pro 64GB ~ R$ 18k one-time
  - vs cloud GPU AWS p4d.24xlarge: ~R$ 600k/ano
  - vs Splunk + MSSP: R$ 80-300k/mês
- **Pitch killer**: "leva um Mac Mini pra cofre da sua fintech, conecta na rede interna, Quarry roda em cima — nenhum byte sai daí"

---

## Modelos de referência por modalidade

### Modalidade A — Mac Mini Sovereign Appliance (soberania física máxima)

| Componente | Especificação | Custo (BRL ~mai/2026) |
|---|---|---|
| **Hardware** | Mac Mini M4 Pro, 14-core CPU, 20-core GPU, 64GB unified memory, 1TB SSD | ~R$ 18.000 CAPEX one-time |
| **OS** | macOS Sonoma 14+ (LTS até 2027) | incluso |
| **Runtime LLM** | MLX (nativo Apple Silicon, mais rápido que Ollama em M-series) | open-source |
| **Modelo primário** | Qwen 2.5 14B Instruct Q4 (~10GB) | open-source |
| **Modelo fallback** | Llama 3.1 8B (auto-triage de baixa latência) | open-source |
| **Network** | Tailscale point-to-point para Quarry web | gratuito até 100 dev |
| **Backup** | Time Machine para NAS interno | incluso |

Throughput estimado: Qwen 14B Q4 em M4 Pro ~30 tok/s; auto-triage ~7s; investigação completa ~3min. Sustenta ~500 alertas/dia.

### Modalidade B — VPS Llama Dedicada (soberania lógica, sem hardware na fintech)

Três níveis de hospedagem, dimensionados por volume:

| Tier | VPS recomendado | Modelo | Custo BRL/mês |
|---|---|---|---|
| **Light** | Hostinger KVM 8 (8 vCPU, 32GB RAM, 400GB NVMe) | Llama 3.1 8B Q4 via Ollama | ~R$ 320 |
| **Standard** | Hetzner AX42 (Ryzen 7 PRO, 64GB DDR5, 2x512GB NVMe) | Qwen 2.5 14B Q4 via Ollama | ~R$ 800 |
| **Pro** | Hetzner GEX130 (Ryzen 9 + RTX 4000 SFF Ada 20GB) ou OCI GPU A10 | Llama 3.3 70B Q4 via vLLM | ~R$ 2.800-3.500 |

**Stack comum Modalidade B:**
- OS: Ubuntu 24.04 LTS (hardenizado, fail2ban, ufw, unattended-upgrades)
- Runtime: Ollama (CPU/RAM) ou vLLM (GPU)
- Inferência: HTTP local exposto APENAS na VPN para Quarry web
- VPN: WireGuard ou Tailscale; zero porta pública
- Logs: ledger imutável local + opcional shipping para Quarry web (sem PII)
- Auditoria: cliente roda a VPS na própria conta cloud — recibos/logs do provedor servem como evidência de soberania

**Diferenças A vs B (para o pitch comercial):**

| Critério | Modalidade A (Mac Mini) | Modalidade B (VPS) |
|---|---|---|
| Soberania **física** | ✅ máxima (hardware no perímetro físico) | ⚠️ não — VPS em datacenter terceiro |
| Soberania **lógica** | ✅ máxima | ✅ máxima (conta cloud do cliente, VPC isolada) |
| Custo entrada | R$ 18k CAPEX único | R$ 320-3.500 OPEX/mês |
| Tempo setup | 2h (entrega + instalação) | <1h (provisão + script) |
| Manutenção | Equipe TI fintech + parceiro Apple | Sysadmin Linux ou managed pelo Quarry |
| Bacen-fit | PSC "controle físico exclusivo" (mais forte) | PSC "controle lógico exclusivo + isolamento cloud" (suficiente para Seed/A) |
| Quando recomendar | Fintech com sala-cofre, IPO/M&A em vista, PII alto valor | Fintech Seed/A sem espaço físico, preferência OPEX |

Cliente escolhe a modalidade no onboarding. **Pode migrar A↔B sem reinstalar Quarry** (só troca target no `llm_resolver`).

---

## Escopo

### Documentação técnica
- `docs/pt-br/sovereign-llm/hardware-reference-mac.md` — Modalidade A: modelo Mac Mini, custo, fornecedores BR
- `docs/pt-br/sovereign-llm/vps-reference-linux.md` — Modalidade B: tiers Light/Standard/Pro, provedores recomendados (Hostinger, Hetzner, OCI)
- `docs/pt-br/sovereign-llm/setup-mac-mini.md` — passo-a-passo Modalidade A
- `docs/pt-br/sovereign-llm/setup-vps-linux.md` — passo-a-passo Modalidade B
- `docs/pt-br/sovereign-llm/conformidade-bacen.md` — mapeamento Res. BCB 85/2021 + LGPD, com diferenças A vs B explicitadas
- `docs/pt-br/sovereign-llm/benchmark.md` — throughput por modalidade × modelo × hardware
- `docs/pt-br/sovereign-llm/escolha-modalidade.md` — guia para o cliente escolher A, B ou C (default)

### Software
- `scripts/sovereign-appliance/install-mac.sh` — Modalidade A: instala MLX, modelo, launchd service
- `scripts/sovereign-appliance/install-vps-linux.sh` — Modalidade B: instala Ollama/vLLM, modelo, systemd unit, WireGuard
- `scripts/sovereign-appliance/healthcheck.sh` — comum ambas modalidades
- Adapter LLM `services/agents/app/security/llm_resolver.py` aceita targets `sovereign-mac` e `sovereign-vps` apontando para endpoint privado
- Painel admin novo em `/settings/sovereign-llm` mostrando modalidade ativa + status + último healthcheck + token/s atual

### Comercial (landing + pitch)
- `apps/web/src/app/br/sovereign-llm/page.tsx` — landing PT-BR com seletor 3-modalidades (A/B/C)
- Componente `apps/web/src/components/landing/br/SovereignLlmBR.tsx`
- Atualizar `DeployOptions.tsx` para mostrar Sovereign LLM como família com 2 modalidades opcionais (A e B) + default (C)
- SKUs comerciais:
  - **Sovereign Appliance (A):** setup R$ 35-50k (inclui Mac Mini + instalação + treinamento TI) + assinatura Quarry web mensal
  - **Sovereign VPS (B):** setup R$ 8-15k (inclui provisão VPS + hardening + treinamento) + assinatura Quarry web mensal + VPS recorrente paga pelo cliente

---

## Não-escopo (este card)

- **Build do appliance pré-instalado** (vender Mac Mini com tudo pronto, lacrado). MVP é DIY com script; venda de appliance pronto fica para CARD-021 quando houver 3+ clientes pagantes na modalidade A.
- **Modelos quantizados próprios** (fine-tuned Quarry). Usar Qwen/Llama vanilla por enquanto.
- **Failover/HA entre múltiplos appliances**. MVP é single-node em cada modalidade — fintech Seed/A não tem volume que justifique HA.
- **Suporte Windows + GPU NVIDIA RTX consumer**. Modalidade B cobre Linux + GPU server-grade; Windows desktop não está no escopo.
- **Modalidade D — appliance híbrida** (Mac Mini + GPU externa eGPU via Thunderbolt). Caso de uso raro; futuro.
- **Substituir BYOK cloud (Modalidade C) como default**. C continua sendo o default — A e B são opcionais para quem precisa de soberania.

---

## Tarefas estimadas

### Fase 1 — Modalidade B (VPS Llama) primeiro — ~7d
> Mais barato validar (não exige compra de hardware), valida o adapter + pitch antes do CAPEX do Mac

| # | Tarefa | Estimativa |
|---|---|---|
| 1 | Curador: `consult-catalog llm-local ollama mlx vllm appliance` | 20min |
| 2 | Provisionar Hetzner AX42 (~R$ 800/mês) + Ubuntu 24.04 hardenizado | 0.5d |
| 3 | Script `install-vps-linux.sh` (Ollama + Qwen 14B + WireGuard + systemd) | 1.5d |
| 4 | Adapter LLM `sovereign-vps` no resolver + healthcheck | 1d |
| 5 | Painel admin `/settings/sovereign-llm` (modalidade ativa, tokens/s) | 1.5d |
| 6 | Benchmark Modalidade B vs Modalidade C (cloud BYOK) | 1d |
| 7 | Landing `/br/sovereign-llm` com seletor 3-modalidades (mostra A como "em validação") | 1.5d |

### Fase 2 — Modalidade A (Mac Mini) — ~6-7d + CAPEX
| # | Tarefa | Estimativa |
|---|---|---|
| 8 | Comprar 1 Mac Mini M4 Pro 64GB para validação | 1d (compra+entrega) |
| 9 | Script `install-mac.sh` (MLX + Qwen 14B + launchd + Tailscale) | 1.5d |
| 10 | Adapter LLM `sovereign-mac` no resolver | 0.5d |
| 11 | Benchmark MLX vs Ollama no M4 Pro com Qwen 14B + Llama 8B | 1.5d |
| 12 | Atualizar landing com modalidade A "disponível" + benchmark | 0.5d |
| 13 | Smoke E2E Mac Mini real → Quarry web via Tailscale | 1d |

### Fase 3 — Conformidade + comercial — ~3d
| # | Tarefa | Estimativa |
|---|---|---|
| 14 | Conformidade Bacen: rascunho doc + revisão jurídica externa (CAPEX jurídico R$ 5-10k) | 2d |
| 15 | Pitch deck atualizado (2 slides: A físico, B lógico) | 0.5d |
| 16 | Doc PT-BR completo `escolha-modalidade.md` para guiar prospect | 0.5d |

**Total: ~16-18d trabalho + ~R$ 18k CAPEX Mac Mini + ~R$ 800/mês VPS validação + ~R$ 5-10k advogado**

---

## Critério de pronto

### Modalidade B (VPS Llama) — Fase 1
- [ ] VPS provisionada + Ollama + Qwen 14B Q4 rodando, exposto só em VPN
- [ ] Script `install-vps-linux.sh` executado por terceiro em <1h
- [ ] Adapter `sovereign-vps` no resolver responde, painel admin mostra status
- [ ] Benchmark publicado: Modalidade B vs Modalidade C (cloud BYOK)
- [ ] Landing `/br/sovereign-llm` no ar com seletor 3-modalidades

### Modalidade A (Mac Mini) — Fase 2
- [ ] Mac Mini real instalado, MLX + Qwen 14B, conectado via Tailscale
- [ ] Script `install-mac.sh` executado por terceiro em <2h
- [ ] Benchmark publicado: Modalidade A vs B vs C, lado a lado
- [ ] Landing atualizada com modalidade A "disponível" + foto/specs

### Comum — Fase 3
- [ ] Doc conformidade Bacen revisado por advogado externo
- [ ] Pitch deck contém 2 slides (A físico, B lógico) + comparativo de custo total vs MSSP
- [ ] SKUs comerciais publicados com pricing (A e B separados)
- [ ] Memória `project-quarry-positioning` atualizada: cita as 2 modalidades opcionais + default BYOK
- [ ] Onboarding flow do produto pergunta ao novo cliente: "qual modalidade LLM você quer?"

---

## Riscos identificados

- **Risco 1 (ambas modalidades):** Qwen 14B Q4 entrega qualidade inferior ao GPT-4/Claude em investigação complexa. Mitigação: benchmark CARD-013 mede; se fraco, fluxo híbrido — auto-triage local, investigação complexa pode escalar para BYOK cloud opcional (cliente decide caso a caso).
- **Risco 2 (Modalidade A):** Apple muda licença macOS proibindo uso enterprise headless. Mitigação: pouco provável; Modalidade B cobre o caso.
- **Risco 3 (Modalidade A):** Fintech rejeita Mac Mini por política "só Linux Server". Mitigação: oferecer Modalidade B sem fricção.
- **Risco 4 (ambas):** Throughput de 1 nó não escala para fintech com >5k alertas/dia. Mitigação: documentar limites; cliente escala horizontalmente (2 Mac Minis cluster MLX, ou VPS maior).
- **Risco 5 (Modalidade A):** Cliente compra Mac Mini, instala, e descobre que precisa de profissional Apple para manter. Mitigação: doc claro + parceria com 1 prestador Apple Authorized BR.
- **Risco 6 (Modalidade B):** VPS BR de menor qualidade (provedores nacionais low-cost) dá downtime alto e mata SLA do Quarry. Mitigação: recomendação canônica é Hetzner DE ou OCI BR; provedores não-recomendados marcados explicitamente como "use por conta e risco" na doc.
- **Risco 7 (Modalidade B):** Soberania "lógica" não satisfaz auditor Bacen que exige soberania "física". Mitigação: documento conformidade explicita esse limite; cliente que precisa de física vai para Modalidade A.
- **Risco 8 (comercial):** prospect fica confuso com 3 modalidades e desiste. Mitigação: `escolha-modalidade.md` faz fluxo decisório em 3 perguntas; onboarding pré-seleciona o recomendado por perfil.

---

## Curador (Regra 11 step 0 — executar ANTES da primeira linha de código)

```bash
consult-catalog llm-local
consult-catalog ollama
consult-catalog mlx
consult-catalog vllm
consult-catalog appliance
consult-catalog air-gap
consult-catalog vps-hardening
consult-catalog wireguard
```

Capabilities provavelmente reusáveis:
- `langgraph-workflow` (já no Quarry) — orquestrador existente segue funcionando com qualquer LLM target
- Nenhuma capability "sovereign-llm" no catálogo atual — é **gap real**. Quando construído, proposta forte de entradas novas no INDEX.md:
  - `llm-sovereign-mac` 🟢 (Modalidade A — Mac Mini + MLX)
  - `llm-sovereign-vps` 🟢 (Modalidade B — VPS Linux + Ollama/vLLM)
  - Provavelmente reusáveis por outros projetos 12Brain (Luna, Osprey, Payjarvis) que tenham clientes pedindo soberania.

---

## Dependências

- CARD-013 (benchmark FP) — independente, mas o benchmark do Mac Mini deve seguir mesma metodologia
- CARD-014 (Auto-Bacen real) — independente, funciona em qualquer LLM target
- **Capex:** R$ ~18k para comprar 1 Mac Mini de validação. Decisão financeira do José.
- **Jurídico:** ~R$ 5-10k para advogado externo revisar doc de conformidade Bacen
