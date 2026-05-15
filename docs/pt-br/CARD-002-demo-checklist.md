# CARD-002 — Checklist offline da demo AiSOC

**Para:** José Passinato
**Por:** Claude (preparado em 2026-05-15)
**Razão:** o VPS de produção (76.13.109.151) não atende o pré-requisito de 8 GB de RAM livre — a stack do AiSOC subiria com risco de OOM kill nos 60+ processos PM2 já em produção. Por isso a validação funcional foi delegada para outra máquina.

---

## Onde executar

Recomendado **um destes**:

- **Notebook pessoal** com Docker Desktop, ≥16 GB RAM total (8 GB livres confortáveis), ≥30 GB disco livre
- **VPS dedicado temporário** (ex: Hostinger KVM 4, AWS t3.xlarge, GCP e2-standard-4) — pode-se destruir após validação
- **Codespace do GitHub** (com `quarry` privado) na máquina com mais recursos do Codespace

❌ **NÃO** rodar no VPS de produção 76.13.109.151.

---

## Passo 1 — preparar a máquina

```bash
# Verificar pré-requisitos
docker --version              # ≥24.x
docker compose version        # ≥2.20
pnpm --version                # ≥8
free -h                       # ≥8GB available
df -h .                       # ≥30GB livre

# Clonar Quarry
git clone git@github.com:Josepassinato/quarry.git
cd quarry
```

> ⚠️ Note: o repositório clonado é Quarry (privado, sob Josepassinato), não o AiSOC upstream. O conteúdo é idêntico ao AiSOC no commit `28ce9f6b` por enquanto, mas evita expor que estamos avaliando.

---

## Passo 2 — subir a demo "one-shot"

Conforme [README.AISOC.md](../../README.AISOC.md) — seção "One-shot demo":

```bash
# Configurar .env mínimo
cp .env.example .env
# Editar .env e setar pelo menos:
#   OPENAI_API_KEY=sk-...           (para embeddings da MITRE ATT&CK no Qdrant)
#   AISOC_LLM_PROVIDER=openai       (ou anthropic — Anthropic exige adaptação)

# Subir demo (compose com 13 serviços + seed automático)
pnpm aisoc:demo
# alternativa direta:  docker compose -f docker-compose.demo.yml up -d
```

**Cronometrar:** capturar `time` do comando acima até a UI ficar acessível.

**Esperado:**
- Imagens AiSOC vêm de `ghcr.io/beenuar/aisoc-*:latest` (pull pode demorar 3-5 min)
- Kafka + Zookeeper + Postgres + Redis sobem primeiro
- Seed roda automaticamente após API estar healthy
- UI: `http://localhost:3000`
- API docs: `http://localhost:8088/docs`

---

## Passo 3 — validações funcionais

### 3.1 Login na UI
- Abrir `http://localhost:3000`
- Credenciais default (verificar `.env.example` ou docs upstream — geralmente `admin@aisoc.local` / `aisoc-dev`)
- ✅ Captura: screenshot da home logada → `screenshots/01-home.png`

### 3.2 Investigação pré-seeded
- Navegar para Cases (ou Alerts)
- Abrir um case seeded
- Verificar: timeline, evidências, decisões do agente
- ✅ Captura: `screenshots/02-case-detail.png`

### 3.3 Hunt manual
- Hunts → criar hunt nova ou rodar uma existente
- Esperar conclusão (pode ser instantâneo no demo seeded)
- ✅ Captura: `screenshots/03-hunt-result.png`

### 3.4 Investigation Ledger
- No detalhe de uma investigação, abrir Ledger / Decision Log
- Verificar: prompt, resposta LLM, tools chamadas, evidências citadas, custo/tokens
- ✅ Captura: `screenshots/04-ledger.png`

### 3.5 MCP server com Claude Code
```bash
# Em outra aba do terminal
cd services/mcp
pnpm install
pnpm build
# Configurar Claude Code MCP:
# Adicionar em ~/.config/claude-code/mcp.json:
{
  "mcpServers": {
    "aisoc": {
      "command": "node",
      "args": ["/path/to/quarry/services/mcp/dist/index.js", "serve"],
      "env": {
        "AISOC_API_URL": "http://localhost:8088",
        "AISOC_API_KEY": "<from .env>"
      }
    }
  }
}
# Reiniciar Claude Code; perguntar: "list aisoc alerts"
```

- ✅ Captura: `screenshots/05-mcp-claude.png`

---

## Passo 4 — medir recursos

Capturar em texto/screenshot:

### 4.1 Idle (após boot completo, sem hunt rodando)
```bash
docker stats --no-stream | tee idle-stats.txt
free -h | tee idle-mem.txt
df -h . | tee idle-disk.txt
```

### 4.2 Durante hunt
```bash
# Em uma aba: rodar hunt na UI
# Em outra aba durante a execução:
docker stats --no-stream | tee hunt-stats.txt
free -h | tee hunt-mem.txt
```

### 4.3 Tempo de boot
```bash
# Repetir do zero:
docker compose -f docker-compose.demo.yml down -v
time docker compose -f docker-compose.demo.yml up -d
# Aguardar UI responder em http://localhost:3000:
time bash -c 'until curl -fs http://localhost:3000 > /dev/null; do sleep 2; done'
```

---

## Passo 5 — relatório

Preencher o template em `docs/pt-br/CARD-002-demo-report.template.md` (a ser criado quando você voltar com dados). Estrutura:

1. Tempo total de setup (clone + pull images + boot até UI)
2. Issues encontrados + workarounds
3. Recursos consumidos (RAM idle/hunt, CPU peak, disk)
4. Screenshots em `screenshots/` (5+ imagens)
5. Avaliação subjetiva da demo (1-10) com justificativa
6. **Veredito final:** GO confirmado (mantém ADR-001) ou rebaixar para CAUTION

---

## Passo 6 — cleanup

```bash
# Parar serviços (preserva imagens)
docker compose -f docker-compose.demo.yml down
# Ou se quiser tudo apagado incluindo volumes:
docker compose -f docker-compose.demo.yml down -v

# Liberar imagens (opcional, libera ~5-8GB):
docker image prune -a
```

---

## Critérios pra rebaixar para CAUTION (mantenha ADR-001 GO em outro caso)

- ❌ Demo não sobe (falha em pull de imagens, erro irrecuperável de seed) → rebaixar
- ❌ UI não funciona em browser moderno → rebaixar
- ❌ Investigation Ledger vazio ou inconsistente → rebaixar
- ❌ MCP server não responde → CAUTION (não bloqueia, mas é diferencial chave)
- ❌ Consumo de recursos absurdo (>16GB RAM em idle) → CAUTION
- ❌ Bugs visíveis na UI que afetam tarefa primária (case investigation) → CAUTION
- ✅ Demo cinematográfica como prometido + recursos razoáveis + Ledger funcional + MCP funcional → GO confirmado

---

## Quando trazer os resultados

Quando completar, me envia:

1. O conteúdo de `screenshots/` (paste no chat ou path acessível)
2. As métricas em texto (idle-stats.txt, hunt-stats.txt, tempos)
3. Issues encontrados (lista corrida)
4. Seu veredito subjetivo de 1-10

Eu compilo o `aisoc-demo-report.md` final e adiciono ao Quarry.
