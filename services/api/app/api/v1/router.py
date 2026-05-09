"""API v1 router aggregating all endpoint modules."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    airgap,
    alerts,
    api_keys,
    approvals,
    assets,
    audit,
    auth,
    autonomy_policy,
    cases,
    community,
    compliance,
    connectors,
    deployment,
    detection_compat,
    detection_loop,
    detection_proposals,
    detection_rules,
    easm,
    feedback,
    federated,
    fusion,
    hunts,
    identity_timeline,
    inbox,
    inbox_itsm,
    knowledge_base,
    lake,
    nl_detection,
    nl_query,
    oauth,
    graph,
    identity_graph,
    insider_threat,
    investigations,
    marketplace,
    metrics,
    mssp,
    oncall,
    passkeys,
    phishing,
    playbooks,
    plugins,
    posture,
    push,
    rbac,
    remediation,
    reports,
    shifts,
    sla,
    stix_taxii,
    tenants,
    threat_intel,
    translation,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(api_keys.router)
api_router.include_router(alerts.router)
api_router.include_router(cases.router)
api_router.include_router(connectors.router)
# Hosted OAuth one-click for connectors (Workstream 2 of AI Stack plan).
# /oauth/start mints a state nonce + 302 to the provider; /oauth/callback
# swaps the code, encrypts tokens via the credential vault, and lands the
# operator back on /onboarding.
api_router.include_router(oauth.router)
api_router.include_router(tenants.router)
api_router.include_router(detection_rules.router)
# Frontend-shape facade: /api/v1/detection/rules + /api/v1/detection/test
api_router.include_router(detection_compat.router)
api_router.include_router(detection_proposals.router)
api_router.include_router(federated.router)
api_router.include_router(graph.router)
api_router.include_router(playbooks.router)
api_router.include_router(plugins.router)
api_router.include_router(community.router)
api_router.include_router(marketplace.router)
api_router.include_router(rbac.router)
api_router.include_router(audit.router)
api_router.include_router(compliance.router)
api_router.include_router(metrics.router)
api_router.include_router(sla.router)
api_router.include_router(investigations.router)

# Mobile responder PWA (Phase 4B)
api_router.include_router(push.router)
api_router.include_router(oncall.router)
api_router.include_router(approvals.router)
api_router.include_router(passkeys.router)

# Wave 3 — operational maturity
api_router.include_router(assets.router)
api_router.include_router(mssp.router)
api_router.include_router(insider_threat.router)
api_router.include_router(remediation.router)

# Analyst feedback loop
api_router.include_router(feedback.router)

# Configurable autonomy guardrails — three-tier per-action confidence (Tier 1.3)
api_router.include_router(autonomy_policy.router)

# NL detection authoring (Tier 2)
api_router.include_router(nl_detection.router)

# Closed-loop detection engineering: FP → LLM Sigma draft → DAC proposal (Tier 2)
api_router.include_router(detection_loop.router)

# Natural-language query → ES|QL / SPL / KQL translation + execution (Tier 2)
api_router.include_router(nl_query.router)

# Identity-centric investigation timeline (Tier 2)
api_router.include_router(identity_timeline.router)

# Cross-platform detection rule translation: Sigma↔SPL↔KQL↔UDM↔ES|QL (Tier 2)
api_router.include_router(translation.router)

# Hypothesis-driven hunt workbench (Tier 2)
api_router.include_router(hunts.router)

# Email-security + phishing-triage workflow (Tier 3)
api_router.include_router(phishing.router)

# Knowledge-base + RAG over org docs/runbooks (Tier 3)
api_router.include_router(knowledge_base.router)

# Wave 4 — advanced capabilities
api_router.include_router(threat_intel.router)
api_router.include_router(posture.router)
api_router.include_router(easm.router)
api_router.include_router(identity_graph.router)
api_router.include_router(reports.router)

# Air-gap status snapshot for operators — Tier 3.1 (air-gapped certification)
api_router.include_router(airgap.router)

# STIX/TAXII threat intelligence publishing (Tier 4)
api_router.include_router(stix_taxii.router)

# Shift handoff and SOC analyst scheduling
api_router.include_router(shifts.router)

# Deployment configuration and air-gap bundle management
api_router.include_router(deployment.router)

# Fusion gateway: proxies to services/fusion when FUSION_URL is set, otherwise
# returns graceful empty payloads so the analyst console renders cleanly.
api_router.include_router(fusion.router)

# Agent-facing tool surface (Workstream 4 of AI Stack plan).
# /agents/tools returns the tenant-scoped, downscope-filtered list of
# (connector instance × capability) pairs the agent layer is allowed to
# invoke. Read-only — actual invocation lives in the agents service.
api_router.include_router(agents.router)

# Universal capture push paths (Workstream 6 of AI Stack plan).
# /inbox/templates + /inbox/tokens manage the per-tenant rotatable inbox
# URLs the wizard's "Push (any vendor)" card hands out. Vendor traffic
# itself terminates at services/ingest, which resolves the token to a
# tenant + template_id and reuses the existing OCSF normalizer.
api_router.include_router(inbox.router)

# Bidirectional ITSM webhook receiver (Workstream 8 of AI Stack plan).
# /inbox/itsm/{tenant_token}/{connector_instance_id} accepts inbound
# Jira / ServiceNow webhooks, resolves the external ticket back to its
# AiSOC case via case_external_refs, and mirrors the status onto
# aisoc_cases. This is the *inbound* counterpart to case_fanout (which
# handles outbound AiSOC → ITSM projection) and is what makes the
# operator's existing ITSM the source of truth for case status.
api_router.include_router(inbox_itsm.router)

# Tenant lake API (Workstream 7 of AI Stack plan).
# /lake/sql executes a tenant-scoped SELECT against the warm tier
# (ClickHouse) after passing through the SQL rewriter, which enforces a
# table allowlist, injects tenant_id predicates, clamps LIMIT, and
# rejects DML/DDL/table-valued functions. /lake/schema returns the
# allowlisted table catalog so operators (and LLM agents) can author
# queries without column-name guesswork.
api_router.include_router(lake.router)
