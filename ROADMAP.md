# AiSOC Roadmap

This document captures the planned direction for AiSOC across major versions. All v4 deliverables and items deferred beyond v4 are listed here.

## v4.0 — Shipped

### AI multi-agent investigator
- [x] Orchestrator (LangGraph state machine) in `services/agents/app/investigator/`
- [x] ReconAgent, ForensicAgent, ResponderAgent (dry-run with analyst approval)
- [x] ReportWriterAgent — streaming markdown + branded PDF
- [x] Investigation & Report tabs in Case Workspace UI
- [x] Eval harness: 20 synthetic incidents, ≥80% MITRE-tactic accuracy CI gate

### Visual SOAR studio
- [x] React Flow playbook editor with full node palette (Trigger, Condition, Action, Loop, Parallel, Human Approval, Wait, Notify)
- [x] DAG playbook engine with retries, idempotency, blast-radius checks
- [x] `playbook.schema.json` (JSON Schema 2020-12) for portability and CI linting
- [x] Detection-as-Code: `detections/` directory with Sigma + AiSOC YAML, GitHub Action deploy-on-merge
- [x] 12 starter playbook templates
- [x] Community playbook marketplace (static index v4.0; publishing flow v4.1)

### Plugin platform, public API, SDKs, docs
- [x] Plugin SDK in Python (`packages/plugin-sdk-py/`) and Go (`packages/plugin-sdk-go/`)
- [x] `plugin.yaml` manifest spec (connector | enricher | responder | detection | widget)
- [x] Plugin loader with OCI image support (`oras pull`) in api/actions/enrichment/connectors
- [x] Public REST API v1 at `/api/v1`, OpenAPI 3.1 at `docs/openapi.yaml`
- [x] GraphQL gateway (Strawberry) proxying REST
- [x] Scoped API tokens (`cases:read`, `playbooks:run`, `plugins:install`)
- [x] Auto-generated client SDKs: `@aisoc/sdk` (TypeScript), `aisoc-sdk` (Python/PyPI), `github.com/beenuar/aisoc/sdk-go`
- [x] Docusaurus docs site at `docs/site/`, deployed to GitHub Pages
- [x] Demo Lab: `pnpm aisoc:lab` one-command full-stack + Conti-style ransomware scenario
- [x] 4 reference plugins: Okta connector, YARA enricher, Slack quarantine responder, MTTR sparkline widget

### Cross-cutting
- [x] OpenTelemetry traces: agents → actions → api → realtime (Jaeger/Tempo)
- [x] API token scopes (foundation for SSO)
- [x] MIGRATION.md for v3 → v4 upgrade path

---

## v4.1 — Shipped

- [x] Plugin publishing flow (signed community submissions, Ed25519 verification, review endpoints)
- [x] Plugin marketplace UI v2 (ratings, install counts, verified badges, category filter, sort)
- [x] Detection catalog: browse and install community Sigma rules via UI
- [x] Playbook community submissions and curation
- [x] `aisoc-cli` — developer CLI for scaffold, validate, publish plugins and detections

---

## v5.0 — Shipped

### Identity & Access
- [x] SAML 2.0 + OIDC authentication (Okta, Azure AD, Google Workspace)
- [x] Multi-tenant row-level security (Postgres RLS + SQLAlchemy middleware)
- [x] Granular RBAC with data-class and tenant scopes (`require_permission()` dependency)
- [x] Full analyst audit log (append-only `audit_log` table + middleware + UI)

### Compliance
- [x] SOC 2 Type II evidence collection dashboard + PDF export
- [x] ISO 27001 control mapping
- [x] NIST CSF / NIST 800-53 control coverage heatmap
- [x] PCI-DSS, HIPAA, DORA module
- [x] MTTD / MTTR / MTTC SLA tracking per tenant

### High Availability & Operations
- [x] HA Helm chart with PodDisruptionBudgets and HorizontalPodAutoscalers
- [x] Backup / restore CLI (`scripts/backup.sh`, `scripts/restore.sh`)
- [x] Multi-region active-active topology guide (`docs/operations/multi-region.md`)
- [x] Operator runbook generation from OTel traces (`scripts/generate_runbook.py`)

---

## v5.1 — Shipped

### UEBA
- [x] Per-user, per-host, per-service behavioral baselines (Welford's algorithm)
- [x] Anomaly risk scores feeding the fusion engine (z-score composite scoring)
- [x] Peer-group analysis and deviation scoring
- [x] Kafka integration: consumes `security.events`, publishes `ueba.anomalies`

### Deception / Honeytokens
- [x] Token generation (AWS keys, URLs, DNS, file, DB credentials, custom types)
- [x] First-touch alerting via HMAC-SHA256-signed webhooks
- [x] Honeytoken lifecycle management UI (create, revoke, delete, trigger history)

### Purple-Team / Continuous Validation
- [x] Atomic Red Team YAML loader and test sync API
- [x] Caldera adversary emulation REST client integration
- [x] ATT&CK coverage heatmap by tactic/technique with detection tracking
- [x] Tabletop incident simulator with findings management UI

---

## v6.0 — Shipped (2026-05-06)

### Wave 3 — Operational Maturity

- [x] MSSP / parent-tenant console — onboard child tenants, delegate cross-tenant actions, view rollup metrics
- [x] Asset inventory + vuln-to-alert correlation — asset CRUD, vulnerability findings, blast-radius context
- [x] Insider threat module — user risk profiles, behavioural indicators, peer-group deviation scoring
- [x] L0–L4 auto-remediation maturity tiers — per-tenant autonomy gate with audit log and per-action whitelist

### Wave 4 — Advanced Capabilities

- [x] Internal threat intelligence — IOC harvesting, threat actor profiles, STIX/TAXII feed subscriptions
- [x] Cloud security posture management (CSPM/KSPM) — posture findings, drift tracking, suppress/resolve workflows
- [x] Identity-centric correlation graph — identity node/edge graph, alert-to-identity linking, attack-path queries
- [x] Auto-generated board reports — report templates, scheduled PDF/HTML artefacts, email/webhook delivery

### Platform

- [x] Dashboard metrics API — aggregated KPI endpoint powering frontend dashboard tiles
- [x] Tailscale connector — audit log and policy-change events with cursor-based pagination
- [x] AWS GuardDuty credential-exfiltration Sigma detection rule

---

## v6.1 — Shipped (2026-05-07) — v1.5 market-driven feature expansion

A review of G2, Gartner Peer Insights, and customer feedback on AI SOC / SIEM /
SOAR platforms drove this release.

### New autonomous agents (`services/agents/app/agents/`)

- [x] Master autonomous triage agent (`auto_triage_agent.py`) — classifies each
      alert as `true_positive` / `false_positive` / `benign` with confidence
- [x] Phishing triage sub-agent (`phishing_agent.py`)
- [x] Identity reasoning sub-agent (`identity_agent.py`)
- [x] Cloud reasoning sub-agent (`cloud_agent.py`)
- [x] Insider-threat reasoning sub-agent (`insider_threat_agent.py`)
- [x] All five exposed via `POST /api/v1/agents/triage`

### New console pages (`apps/web/src/components/`)

- [x] `/investigate` — conversational, multi-turn investigation copilot
- [x] `/coverage-advisor` — MITRE ATT&CK gap ranking by adversary prevalence
- [x] `/shifts` — analyst shift-handoff dashboard
- [x] `/easm` — External Attack Surface Management
- [x] `/mssp` — MSSP executive dashboard
- [x] `/noise-tuning` — per-rule false-positive rate and one-click tuning
- [x] `/analytics/team` — analyst leaderboard, MTTR per analyst, dispositions accuracy

### New API surfaces (`services/api/app/api/v1/endpoints/`)

- [x] `shifts.py` — shift-handoff CRUD
- [x] `stix_taxii.py` — STIX 2.1 / TAXII 2.1 publishing
- [x] `compliance.py` — automated compliance evidence (SOC 2, ISO 27001, NIST CSF, PCI-DSS, HIPAA, DORA)
- [x] `deployment.py` — deployment / air-gap toggles

### New connectors (16 → 26)

- [x] SentinelOne (`sentinelone.py`)
- [x] Cortex XDR (`cortex_xdr.py`)
- [x] Wiz (`wiz.py`)
- [x] Snyk (`snyk.py`)
- [x] Zscaler (`zscaler.py`)
- [x] Proofpoint (`proofpoint.py`)
- [x] ServiceNow (`servicenow.py`)
- [x] Jira (`jira.py`)
- [x] 1Password (`1password.py`)
- [x] Duo Security (`duo_security.py`)

### Other

- [x] AI-generated incident reports — one-click "Export Report" generates PDF from the Investigation Ledger
- [x] Air-gap deployment configuration — per-tenant toggles disable external feeds

---

## v7.0 — Shipped ✅ (2026-05-10)

All items below were shipped as part of the v1.0 buyer-value plan.
Implemented and reviewed by Beenu Arora <beenu@cyble.com>.

- [x] WCAG AA full accessibility pass (axe-core CI gate — `apps/web/src/test/a11y.test.tsx`)
- [x] Light theme persisted in user profile (`ThemeProvider.tsx` + `PATCH /api/v1/users/me/preferences`)
- [x] Saved views and custom drag-drop dashboard widgets per analyst (`saved_views.py` + `DashboardView.tsx`)
- [x] AI-generated weekly executive digest — auto-emailed PDF (`digest_pdf.py` + `weekly_digest_task.py`)
- [x] Slack native bot for alert triage without opening the UI (`services/slack-bot/` — 61 tests)
- [x] Threat actor attribution engine v0 (`services/threatintel/app/actors/attribution.py`)
- [x] Air-gap / Ollama local-LLM mode (`docker-compose.airgap.yml` + `apps/docs/docs/operations/air-gapped.md`)
- [x] BYOK per-tenant LLM credentials UI + API (`llm_credentials.py` + `SettingsView.tsx`)
- [x] MSSP console — per-child-tenant KPI aggregation, SLA posture, parent_tenant_id hierarchy
- [x] Team analytics view — analyst MTTR, leaderboard, shift workload (`TeamAnalyticsView.tsx`)
- [x] Case auto-summary + PDF export (`case_summary.py` + `case_summary_html.py`)
- [x] Investigation timeline (replayable) (`InvestigationTimeline.tsx`)
- [x] Playbook gallery with 12 curated packs + GitHub PR integration for detection proposals
- [x] osquery pack management — YAML pack loader, 5 curated packs, tenant-aware resolver, pack catalog API, `?format=fleet|osquery` render modes
- [x] FIM pipeline — ingestion endpoint, event query / summary API, React FIM dashboard (table + summary card), 4 FIM detection rules (det-endpoint-281..284)
- [x] Custom osquery extension binary — 5 virtual tables (`aisoc_pending_actions`, `aisoc_alert_cache`, `aisoc_attck_persistence`, `aisoc_kernel_modules_verified`, `aisoc_browser_extensions`)
- [x] Extensions API endpoints (`/api/v1/osquery/extensions/*`) and cross-platform CI build matrix with cosign signing
- [ ] Mobile responder console (React Native) — triage and acknowledge from phone _(deferred to v8.0)_
- [ ] Plugin publishing marketplace v3 (commercial plugins, revenue sharing) _(deferred to v8.0)_

---

## v8.0 — Planned

- Mobile responder console (React Native) — triage and acknowledge from phone
- Plugin publishing marketplace v3 (commercial plugins, revenue sharing)
- MSSP RBAC enforcement on `/api/v1/actors/*` endpoints (threat attribution)
- Automated IOC sharing to community MISP instances via STIX/TAXII push
- NL→query: "show me failed logins from new ASNs last 24h" → ES|QL / KQL
- AI-generated threat intelligence briefings from public feeds
- Embedded red-team scoring (ATT&CK coverage %) as a live dashboard widget
- SLA breach predictor (ML model on historical MTTR data)
- Incident cost estimator (breach impact calculator)
- SOC-in-a-box one-click cloud deploy (Terraform module for AWS / GCP)
- osquery live-query response action — push ad-hoc queries to hosts via playbooks
- FleetDM connector (alternative/complement to osctrl)
- Wire `aisoc_pending_actions` / `aisoc_alert_cache` to live case/alert DB tables (replace stubs)
- osquery extension signing verification in CI (`cosign verify-blob` gate)

---

## Ideas Backlog (unscheduled)

- NL→query: "show me failed logins from new ASNs last 24h" → ES|QL / KQL
- AI-generated threat intelligence briefings from public feeds
- Automated IOC sharing to community MISP instances
- Embedded red-team scoring (ATT&CK coverage %) visible on dashboard
- "Explain this alert" button using LLM with enrichment context
- Incident cost estimator (breach impact calculator)
- SLA breach predictor (ML model on historical MTTR data)
