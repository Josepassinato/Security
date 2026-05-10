---
sidebar_position: 3
---

# Architecture

## High-Level Data Flow

```
External Sources
  (EDR · SIEM · Cloud · Identity · Network · Threat Intel)
        │
        ▼ connectors
   Kafka spine  ◄── Honeytokens (deception events)
        │
   ┌────┼──────────────────────────────────┐
   ▼    ▼                                  ▼
Fusion  UEBA                           Detections
(ML)  (baseline)                  (Sigma·YARA·KQL·EQL)
   │    │                                  │
   └────┴──────────────────────────────────┘
                      │
              PostgreSQL · ClickHouse · OpenSearch
              Qdrant (vectors) · Neo4j (graph) · Redis
                      │
               FastAPI Core API (port 8000)
                      │
            ┌─────────┼──────────┬─────────────┐
            ▼         ▼          ▼             ▼
         Next.js   Agents   Realtime         MCP
        (port 3000) (8001)  (8086, WS+Push)  (TS, stdio)
                       │
                Investigation Ledger
              (every prompt/tool/step,
               replayable per case)
```

Key structural pieces include the **Investigation Ledger** (every
agent prompt, response, evidence citation, and tool call is logged step-by-
step against a case and replayable in the UI), the **Ambient Copilot**
(context-aware next-action surface across alerts, cases, rules, and
playbooks), the **Responder PWA** (passkey-only mobile route at
`/responder/*` with VAPID Web Push), the **public eval harness** (one
real measurement plus three substrate self-consistency gates, run in CI),
the **MCP server** (`@aisoc/mcp`, exposes 11 tools to Claude / Cursor /
Continue / Cody), and the **click-and-connect connector platform** (next
section).

Additional capabilities introduced in 2026 H2:

- **Detection-as-Code (DAC)** — propose → review → eval-gate → promote lifecycle for detection rules, with eval results gating promotion.
- **Detection confidence** — each fused alert carries a derived confidence label (`high / medium / low`) with an ordered evidence chain.
- **Detection drift monitoring** — scheduled ATT&CK coverage snapshots with delta tracking.
- **Hunt-as-Code** — YAML hunt definitions in `hunts/` with hypothesis-driven indicator matching and APScheduler-driven continuous execution.
- **Risk-Based Alerting (RBA)** — time-decayed entity risk scoring that promotes high-risk entities to incidents.
- **Federated search** — translate a single query into SPL, KQL, and ES|QL and fan out to connected SIEMs.
- **ChatOps verification** — HMAC-signed Slack/Teams interactive prompts for human-in-the-loop response actions.
- **AI-vs-AI adversary eval** — deterministic attacker-LLM mutator for testing detection resilience.

### v1.5 — market-driven additions (2026-05-07)

The v1.5 release ships from a review of G2, Gartner Peer Insights, and customer feedback on AI SOC / SIEM / SOAR platforms. It adds five new agents, eight new console pages, four new API surfaces, and ten new connectors:

- **Autonomous alert triage agents** — `services/agents/app/agents/auto_triage_agent.py` plus four sibling agents (phishing, identity, cloud, insider-threat) classify each alert as `true_positive` / `false_positive` / `benign` with a confidence score. Low-confidence noise auto-closes; the rest is escalated. Surfaced via `/api/v1/agents/triage`.
- **Conversational investigation chat** — multi-turn copilot at `/investigate` that anchors on a case and reads its evidence, ledger, and entity graph for grounded follow-up Q&A. Component: `apps/web/src/components/copilot/InvestigationChat.tsx`.
- **MITRE ATT&CK coverage advisor** — `/coverage-advisor` ranks technique gaps by adversary prevalence and recommends rules to close them.
- **Shift handoff dashboard** — `/shifts` shows outgoing/incoming analysts the active cases, in-flight investigations, and queued approvals on one screen. Endpoints in `services/api/app/api/v1/endpoints/shifts.py`.
- **EASM (External Attack Surface Management)** — `/easm` discovers assets, exposed services, and certificate-expiry risks for everything the org points at the public internet.
- **MSSP executive dashboard** — `/mssp` rolls up KPIs, cross-tenant alert volumes, and per-customer SLA posture into a multi-tenant pane.
- **Alert noise-tuning dashboard** — `/noise-tuning` surfaces per-rule false-positive rate, suppression candidates, and one-click tuning.
- **Team analytics & gamification** — `/analytics/team` ships analyst leaderboard, MTTR per analyst, dispositions accuracy, and shift workload balance.
- **STIX 2.1 / TAXII 2.1 publishing** — `services/api/app/api/v1/endpoints/stix_taxii.py` pushes the tenant's IOCs and threat-actor profiles to upstream / community feeds.
- **Automated compliance evidence** — `services/api/app/api/v1/endpoints/compliance.py` collects point-in-time evidence for SOC 2 / ISO 27001 / NIST CSF / PCI-DSS / HIPAA / DORA.
- **AI-generated incident reports** — one-click "Export Report" on every case generates a PDF incident report from the Investigation Ledger.
- **Air-gap deployment configuration** — `services/api/app/api/v1/endpoints/deployment.py` exposes air-gap mode toggles for tenants that disallow external feeds.
- **Ten new connectors** — SentinelOne, Cortex XDR, Wiz, Snyk, Zscaler, Proofpoint, ServiceNow, Jira, 1Password, Duo Security; the catalog is now 26 connectors. See [Connectors](./connectors/).

## Connector polling and credential vault

```
Browser (Add connector wizard)
    │
    │ POST /api/v1/connectors  { type, auth_config, connector_config }
    ▼
services/api  ─── CredentialVault.encrypt() ───▶ vault:v1:<base64>
    │
    │ INSERT INTO connectors(auth_config_encrypted, ...)
    ▼
PostgreSQL  ◄────────────────────────────────────────────────────┐
    │                                                            │
    │ every 30s reload                                            │
    ▼                                                             │
services/connectors                                               │
   ConnectorScheduler (APScheduler, in-process)                   │
       │                                                          │
       │  per-instance job @ poll_interval_seconds (default 300s) │
       ▼                                                          │
   _poll_one(instance)                                            │
       │                                                          │
       │ 1. CredentialVault.decrypt() ── reads same key as API ──┘
       │ 2. construct connector class from registry
       │ 3. await connector.fetch_alerts(since_seconds=300)
       │ 4. [connector.normalize(e) for e in raw_events]
       │ 5. await ingest_client.push_events(tenant_id, normalized)
       │ 6. record_poll_success(events_added, elapsed_ms)
       ▼
services/ingest  POST /v1/ingest/batch  X-Tenant-ID: <uuid>
       │
       ▼
   Kafka spine ──▶ Fusion · UEBA · Detections (existing pipeline)
```

The `services/api` service holds the **encrypt** authority for the vault
and is the only writer to `connectors.auth_config_encrypted`.
`services/connectors` ships a vendored read-path `decrypt_dict()` that
pairs to the same `AISOC_CREDENTIAL_KEY` so the scheduler can decrypt
per-poll without owning the write path. Key rotation is supported via
`MultiFernet` and the `AISOC_CREDENTIAL_KEY_ROTATION_FROM` env var; the
[Operations: Credentials](./operations/credentials) page documents the
full rotation procedure, threat model, and hosted-OAuth roadmap.

The wizard's `Test connection` button skips the vault entirely — it
forwards the raw form values to a stateless `POST /connectors/{id}/test`
endpoint on the connectors microservice, which constructs the connector
in memory and calls `test_connection()`. Bad credentials never touch the
database.

## osquery Fleet Integration

AiSOC ships a first-class osquery integration with three layers:

### osquery-tls service (`services/osquery-tls/`)

A FastAPI service that implements the full [osquery TLS protocol](https://osquery.readthedocs.io/en/stable/deployment/remote/) (enrolment, configuration, log ingestion, distributed queries) with multi-tenant isolation. All osquery nodes enrol using the standard `--tls_enroll_secret` / `--enroll_secret_path` flag pair.

```
osquery agent (fleet host)
    │  TLS 1.3, mutual auth
    ├─▶  POST /api/v1/osquery/enroll         — returns node_key, host-scoped JWT
    ├─▶  POST /api/v1/osquery/config         — returns compiled pack + FIM config
    ├─▶  POST /api/v1/osquery/log            — ingests result + status logs
    └─▶  POST /api/v1/osquery/distributed/*  — live query fan-out (read/write)
                    │
                    ▼  normalised events
               services/ingest ──▶ Kafka spine ──▶ Detections / Fusion
```

### osquery pack catalog (`packs/`)

Five curated YAML packs ship in the repo root's `packs/` directory. Each pack is validated on load against a Pydantic schema and cached in memory by the pack loader service.

| Pack ID | Purpose | Tables |
|---|---|---|
| `aisoc-fim-baseline` | File-integrity monitoring for critical paths | `file_events` |
| `aisoc-fim-credentials` | Credential file changes (`/etc/passwd`, SSH keys, sudoers) | `file_events` |
| `aisoc-attck-persistence` | MITRE T1547 — startup items, cron, systemd units | `startup_items`, `cron_tab`, `systemd_units` |
| `aisoc-attck-defense-evasion` | MITRE T1562 — log clearing, module unload, AV disablement | `process_events`, `kernel_modules` |
| `aisoc-inventory-baseline` | Hardware/software inventory baseline | `system_info`, `os_version`, `programs` |

Pack assignment (which packs run on which tenants) is stored in Postgres. The osquery-tls service compiles assigned packs into the canonical osquery config response at enrolment time, with optional FleetDM-compatible or raw-osquery JSON render formats.

### AiSOC osquery extension (`services/osquery-extensions/`)

A standalone Go binary that loads into osquery as a [thrift extension](https://osquery.readthedocs.io/en/stable/development/osquery-sdk/). It exposes five virtual tables that let analysts query AiSOC state directly from osquery SQL:

| Table | Description | Auth |
|---|---|---|
| `aisoc_pending_actions` | HITL response actions queued for this host | host-scoped JWT |
| `aisoc_alert_cache` | Alerts fired against this host (last 24 h) | host-scoped JWT |
| `aisoc_attck_persistence` | Approved persistence baseline (T1547 diff) | host-scoped JWT |
| `aisoc_kernel_modules_verified` | Loaded kernel modules with signing status (Linux) | local only |
| `aisoc_browser_extensions` | Installed browser extensions per user profile | local only |

The extension authenticates via **host-scoped JWTs** issued at TLS enrolment. Each token is bound to a single `host_identifier`, scoped to `extensions:read`, and valid for 24 hours with automatic refresh. See [Extension Security Model](./extensions/security-model.md) for the full threat model.

The extension is distributed as a pre-built binary for Linux (amd64/arm64), macOS (amd64/arm64), and Windows (amd64). CI builds release artifacts on `ext-v*` tags with cosign keyless signing. See [Extension Install](./extensions/install.md).

## Monorepo Layout

```
AiSOC/
├── apps/
│   ├── web/                # Next.js 14 React frontend (incl. Responder PWA)
│   └── docs/               # This Docusaurus site
├── services/
│   ├── api/                # FastAPI gateway              (port 8000)
│   ├── agents/             # LangGraph investigator       (port 8001)
│   ├── realtime/           # Node/TS WebSocket + Web Push (port 8086)
│   ├── ingest/             # Go OCSF normaliser           (port 8081)
│   ├── enrichment/         # Go enrichment fan-out        (port 8080)
│   ├── fusion/             # Fusion + ML scoring          (port 8003)
│   ├── actions/            # Action executor              (port 8002)
│   ├── threatintel/        # TAXII / MISP / OTX / KEV     (port 8005)
│   ├── ueba/               # User behavior analytics      (port 8007)
│   ├── honeytokens/        # Deception platform           (port 8008)
│   ├── purple-team/        # Adversary emulation          (port 8006)
│   ├── connectors/         # Connector polling + credential vault
│   ├── osquery-tls/        # osquery TLS server (enrol, config, log, distributed)
│   ├── osquery-extensions/ # Go extension binary (5 virtual tables)
│   ├── demo-producer/      # Synthetic event generator for demos
│   └── mcp/                # Model Context Protocol server (TypeScript)
├── packages/
│   ├── plugin-sdk-py/      # Python plugin SDK
│   ├── plugin-sdk-go/      # Go plugin SDK
│   ├── sdk-py/             # Python client SDK
│   ├── sdk-ts/             # TypeScript client SDK
│   └── sdk-go/             # Go models / client helpers
├── packs/                  # Curated osquery packs (YAML, 5 first-party)
├── infra/
│   ├── helm/aisoc/         # Helm chart (Kubernetes, HA-ready)
│   ├── terraform/          # Terraform modules
│   ├── coolify/            # One-click deploy on Coolify
│   ├── fly/                # Fly.io demo deployments
│   ├── railway/            # Railway templates
│   └── render/             # render.yaml blueprint
├── detections/             # 300+ detection rules (osquery/Sigma/YARA/KQL, YAML)
├── hunts/                  # Hunt-as-Code YAML definitions (hypothesis + indicators)
├── playbooks/              # 50+ SOAR playbooks (YAML)
├── plugins/                # 15 first-party plugins (Go + Python)
├── marketplace/            # Marketplace index (index.json)
├── docs/                   # OpenAPI spec (openapi.yaml)
├── docker-compose.yml      # Full development stack
├── docker-compose.demo.yml # Slim profile for `pnpm aisoc:demo`
└── scripts/                # Utilities (seed, eval harness, build, validate)
```

## Service Responsibilities

| Service | Port | Language | Responsibility |
|---------|------|----------|----------------|
| `api` | 8000 | Python (FastAPI) | REST gateway, auth, RBAC, RLS, audit log, **Investigation Ledger**, Ambient Copilot, marketplace, approvals, on-call, passkeys, push subscriptions, **Detection Proposals** (DAC lifecycle), **Federated Search** fan-out, SLA tracking, **Shifts** handoff, **STIX/TAXII** publishing, **Compliance evidence** collection, **Deployment / air-gap** configuration |
| `agents` | 8001 | Python (LangGraph) | Orchestrator + recon + forensic + responder + report-writer agents, **autonomous triage agent** + phishing / identity / cloud / insider-threat sub-agents, **conversational investigation chat**, playbook engine, ledger writes, **Hunt-as-Code** engine + scheduler |
| `realtime` | 8086 | TypeScript (Node.js) | WebSocket streaming of agent steps; **VAPID Web Push** delivery for the Responder PWA |
| `ingest` | 8081 | Go | OCSF normalisation, Bloom-filter dedup, Kafka publish |
| `enrichment` | 8080 | Go | Enrichment fan-out (IP, domain, hash, email, user) |
| `fusion` | 8003 | Python | ML scoring (LightGBM + Isolation Forest), correlation, **alert confidence scoring**, **entity risk / RBA** |
| `actions` | 8002 | Python | Plugin action executor, blast-radius gating, **ChatOps verification** (HMAC-signed Slack/Teams prompts) |
| `threatintel` | 8005 | Python | TAXII 2.1 / MISP / OTX / KEV ingestion + triple storage |
| `ueba` | 8007 | Python | Welford baseline, Z-score scoring, anomaly stream |
| `honeytokens` | 8008 | Python | Token lifecycle, HMAC signing, webhook dispatch |
| `purple-team` | 8006 | Python | ART YAML parser, Caldera executor, ATT&CK heatmap, **detection drift snapshots** |
| `connectors` | — | Python | Connector polling (APScheduler), credential vault (`CredentialVault`), registry-based connector discovery |
| `demo-producer` | — | Python | Synthetic event generator for demos and evaluation |
| `mcp` | n/a | TypeScript | Model Context Protocol stdio server, 11 tools for IDE-side agents |
| `web` | 3000 | TypeScript (Next.js) | React console + Responder PWA route group, **benchmark scoreboard** |

## Storage Tier

| Store | Role |
|-------|------|
| PostgreSQL | Operational data, RLS-enforced multi-tenancy, audit log, **investigation ledger** |
| ClickHouse | Time-series analytics, compliance metrics |
| OpenSearch | Full-text search across alerts, logs, cases |
| Qdrant | Semantic vector search for RAG copilot + agent memory |
| Neo4j | Attack graph, entity relationships, blast-radius queries |
| Redis | Cache, rate-limiting, session store, push subscription cache |
| Kafka | Async event backbone |

## Investigation Ledger

Every agent action (LLM prompt, LLM response, tool call, evidence
citation, decision branch) is appended to the `investigation_ledger`
table, scoped to a case and stamped with the agent identity, model,
prompt hash, and timestamp. The Case workspace renders this as a
scrubbable timeline so analysts can replay the agent's reasoning.

The schema is defined in
[`services/api/migrations/008_investigation_ledger.sql`](https://github.com/beenuar/AiSOC/blob/main/services/api/migrations/008_investigation_ledger.sql).
The agent-side writer lives in
[`services/agents/app/investigator/ledger.py`](https://github.com/beenuar/AiSOC/blob/main/services/agents/app/investigator/ledger.py),
and the UI consumer is
[`apps/web/src/components/cases/InvestigationLedger.tsx`](https://github.com/beenuar/AiSOC/blob/main/apps/web/src/components/cases/InvestigationLedger.tsx).

## Responder PWA

The Responder PWA is mounted under the Next.js route group
`apps/web/src/app/(responder)/`. It is **passkey-only** (no passwords),
shows the on-call rotation, lists pending approvals, supports VAPID
Web Push for high-severity alerts, and ships an offline shell.

The schema is defined in
[`009_responder_pwa.sql`](https://github.com/beenuar/AiSOC/blob/main/services/api/migrations/009_responder_pwa.sql).
The push pipeline lives in
[`services/realtime/src/push.ts`](https://github.com/beenuar/AiSOC/blob/main/services/realtime/src/push.ts).

## Enterprise Security Controls

- **Multi-tenancy** — PostgreSQL Row-Level Security on every table; `tenant_id` is derived from the JWT and cannot be spoofed.
- **RBAC** — `require_permission` FastAPI dependency; custom roles with fine-grained action permissions per resource type.
- **SAML 2.0 / OIDC** — Pluggable SSO with JIT user provisioning and group-to-role mapping.
- **WebAuthn / Passkeys** — Required for the Responder PWA; password-less by default.
- **Immutable Audit Log** — Postgres trigger + `SECURITY DEFINER` function prevents UPDATE/DELETE on `audit_log`.
- **Replayable agent decisions** — The Investigation Ledger is append-only and tenant-scoped.
- **OpenTelemetry** — All services emit traces, metrics, and structured logs to a configurable OTLP endpoint.
- **Backup & Restore** — `scripts/backup.sh` / `restore.sh` with AES-256-GCM encryption and SHA-256 manifest.
- **High-Availability Helm** — Multi-replica deployments, HPA, PDB, anti-affinity, and readiness probes.

## Plugin Extension Points

Plugins extend AiSOC at three key points:

- **Enrichers** — Add context to indicators (IP, domain, hash, email)
- **Actions** — Execute response steps (block IP, disable user, create ticket)
- **Connectors** — Ingest events from external sources (SIEM, EDR, cloud)
- **Widgets** — Render plugin-supplied React panels in the case workspace

See [Plugin Overview](./plugins/overview) for the full plugin lifecycle.
