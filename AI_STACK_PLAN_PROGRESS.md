# AI Stack & Data Integration Plan — Progress Tracker

Tracking progress against the `ai-stack-data-integration-plan_e90071ca.plan.md`
spec (also attached as `uploads/ai-stack-data-integration-plan_e90071ca.plan-L1-L332-0.md`).

**Plan file is read-only — never edit it. Update this tracker instead.**

---

## How to resume after a session restart

1. Re-open `/Users/beenu/Desktop/Quarry` in your editor.
2. Read this file top-to-bottom.
3. Re-create the todo list from the snapshot in the
   "Live todo snapshot" section below — keep the same `id`s.
4. Resume from the section marked **"Resume here"** at the bottom.
5. Workspace rule: continue without stopping until every todo is done.

---

## Workstream status

| WS | Title                              | Status      | Anchor |
|----|------------------------------------|-------------|--------|
| 1  | Repo + plan alignment              | DONE        | pre-session |
| 2  | Click-and-connect OAuth            | DONE        | pre-session |
| 3  | Catalog expansion (P0 batch)       | DONE        | 14 connectors landed + manifests + docs |
| 4  | Capability taxonomy                | DONE        | enum + per-instance scoping + `/agents/tools` |
| 5  | Self-healing                       | DONE        | OAuth refresh + backfill + freshness SLO + UI badges |
| 6  | Universal capture                  | DONE        | `/v1/inbox/*` in `services/ingest` + tokens panel |
| 7  | Tenant lake API                    | DONE        | endpoints + rewriter + rate limiter + 69/69 tests |
| 8  | Bidirectional ITSM                 | DONE        | push_case + `/v1/inbox/itsm` + fan-out service + 113/113 tests |
| 9  | Docs + Sonali                      | DONE        | `api-coverage.md` + `itsm-as-source-of-truth.md` + `sonali-consultation-questions.md` + sidebars + SYSTEM_DESIGN §12 |

---

## GitHub hygiene workstream (in flight)

User asked for:
1. GitHub fully updated (docs/architecture in sync with code).
2. Code-scanning alerts at https://github.com/Josepassinato/quarry/security/code-scanning fixed.
3. Contributor graph showing only `beenu` (no automation accounts, no `Quarry Bot`).
4. **Author identity for all commits: `Beenu Arora <beenu@cyble.com>`** — no
   co-author trailers, no automation addresses, no `users.noreply.github.com`.

### Status

| ID                         | Task                                                                         | Status      |
|----------------------------|------------------------------------------------------------------------------|-------------|
| gh-1                       | Audit current git state, branches, identities                                | DONE        |
| gh-4                       | Secret scan with gitleaks + triage false positives                           | DONE (`.gitleaksignore` committed) |
| gh-2                       | Pull live code-scanning alerts and triage                                    | DONE (47 alerts triaged) |
| gh-6                       | Fix code-scanning issues (critical/high first)                               | DONE for SSRF + log-injection in `cases.py` + `fusion.py`; remaining notes (unused imports, bind-all, weak hash) triaged as benign |
| gh-5                       | Sync docs/architecture so GitHub matches current state                       | DONE (`docs/architecture/SYSTEM_DESIGN.md` §12 added; topology + service table updated) |
| gh-commit-pre-rewrite      | Commit fixes + tracker with `Beenu Arora <beenu@cyble.com>`, no co-authors   | DONE        |
| gh-3a..gh-3e               | History-rewrite plan (filter-repo + force-push)                              | DONE (3 passes; verified clean; CI workflows patched) |
| gh-prs                     | Close 19 dependabot PRs; comment on #37 for K4R7IK to rebase                 | DONE        |
| gh-7                       | Verify code-scanning alerts cleared after push                               | DONE (0 open high/medium/error alerts; 3 false positives dismissed with rationales) |
| gh-7a                      | Add `safe_log_value` helper + apply to 19 `py/log-injection` sites           | DONE        |
| gh-7b                      | Fix `py/url-redirection` in `oauth.py` (whitelist + URL reconstruction)      | DONE        |
| gh-7c                      | Fix/dismiss 3 `py/incomplete-url-substring-sanitization` alerts              | DONE        |
| gh-7d                      | Dismiss CodeQL false positives with rationales                               | DONE        |
| gh-7e                      | Clean up note-level alerts (unused imports/vars, empty except)               | DONE        |
| tryaisoc-cj                | Customer journey review of tryaisoc.com — find and fix bugs                  | DONE        |

### Co-author trailer issue (resolved at the local layer)

A shell harness was injecting an unwanted `Co-authored-by:` trailer into
every commit message at shell-invocation time, even though local git config
is clean (`user.name=Beenu Arora`, `user.email=beenu@cyble.com`, no
`commit.template`, no active hooks, no mailmap).

Workaround applied: after each commit, run

```bash
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f \
  --msg-filter "sed '/^Co-authored-by: /d' \
                | awk 'NF{p=1} p' \
                | awk 'BEGIN{n=0} {lines[n++]=\$0} END{e=n-1; while(e>=0 && lines[e]==\"\") e--; for(i=0;i<=e;i++) print lines[i]}'" \
  HEAD~N..HEAD
```

…where `N` is the number of recent commits with the trailer. The two AwK
passes strip leading and trailing blank lines so the rewritten commit message
is byte-clean.

Verification command:

```bash
git log --format='%h %an <%ae>%n%(trailers:only=true)' -n 5
```

---

## WS7 — Tenant lake API (shipped)

### What landed

- `services/api/pyproject.toml` — `sqlglot>=23.0.0,<27.0.0` + `clickhouse-driver`.
- `services/api/app/db/clickhouse.py` — async ClickHouse client wrapper:
  `get_clickhouse_client`, `close_clickhouse`, `execute_lake_query`,
  `fetch_lake_schema`. Exceptions: `LakeQueryNotConfiguredError`,
  `LakeQueryTimeoutError`, `LakeQueryError`. Returns `LakeQueryResult` dataclass.
- `services/api/app/services/lake_sql.py` — sqlglot rewriter:
  - `rewrite_for_tenant(sql, tenant_id, *, max_limit, allowlist)` →
    `RewriteResult(sql, referenced_tables, applied_limit)`.
  - SELECT-only allowlist; rejects DML/DDL/`KILL`/table-valued functions.
  - Recursive `tenant_id` predicate injection via `optimizer.scope`.
  - Empty-projection `SELECT` rejection (treats bare `SELECT` as syntax error).
  - **Subtle bug fixed**: `_direct_tables` previously read `select.args.get("from_")`;
    sqlglot stores the FROM clause under the dict key `"from"` (the Python attr
    is `from_`, but `args[]` uses the YAML-style key). All FROMs were silently
    skipped before the fix → no predicate injection, empty `referenced_tables`.
  - **Forbidden roots**: `(exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter,
    exp.Create, exp.TruncateTable, exp.Command, exp.Kill)`.
- `services/api/app/services/lake_rate_limit.py` — per-tenant in-memory token
  bucket. `LakeRateLimiter.acquire(tenant_id, cost=1.0)` → `RateLimitDecision`
  with `to_headers()` for `X-RateLimit-*` + `Retry-After`. Uses
  `time.monotonic` for refill clock; `_TokenBucket.last_refill` is a
  `field(default_factory=time.monotonic)` — see "Test gotcha" below.
- `services/api/app/api/v1/endpoints/lake.py` — `POST /api/v1/lake/sql` and
  `GET /api/v1/lake/schema`. Uses `AuthUser`, `DBSession`,
  `require_permission("lake:query"|"lake:read_schema")`. Helpers:
  `_acquire_or_429`, `_scrub_sql_for_log`, `_audit_query_attempt`.
  Pydantic models: `LakeQueryRequest`, `LakeQueryResponse`, `LakeColumnInfo`,
  `LakeTableInfo`, `LakeSchemaResponse`.
- `services/api/migrations/034_lake_permissions.sql` — registers
  `lake:query` + `lake:read_schema` in `role_permissions`.
- `services/mcp/src/tools/lake.ts` — `aisoc_lake_query` + `aisoc_lake_schema`
  MCP tools (typed surface, prompt-injection guards, calls API endpoints).
- `services/mcp/tests/lake.test.ts` — comprehensive tests for both tools
  (Zod schemas, multi-statement guard, forbidden tables, response shape).

### Tests — done

- `services/api/tests/test_lake_sql.py` — **44/44 passing**.
- `services/api/tests/test_lake_rate_limit.py` — **25/25 passing**.

### Test gotcha — `LakeRateLimiter` + `time.monotonic`

`_TokenBucket.last_refill` is set via `field(default_factory=time.monotonic)`,
which captures the **real** clock at bucket-creation time. If a test patches
`app.services.lake_rate_limit.time.monotonic` *after* the bucket has been
created, `_refill` computes `elapsed = patched_now - real_creation_now`,
which is hugely negative and gets clamped to 0 → no tokens refill.

Workaround already used in `test_lake_rate_limit.py`:

```python
async def _seed_bucket(limiter, tenant, *, at_time):
    """Force-create the tenant's bucket and align last_refill with the patched clock."""
    await limiter.acquire(tenant, cost=0.0)
    bucket = limiter._buckets[tenant]
    bucket.last_refill = at_time
```

Apply the same pattern when writing endpoint tests that depend on rate-limit
timing.

---

## Security fixes (gh-6)

### `services/api/app/api/v1/endpoints/fusion.py`

- Added `_SAFE_PATH_RE = re.compile(r"^/[A-Za-z0-9_\-./%]*$")` and
  `_validate_proxy_path(path)` that rejects `..`, protocol-relative `//host/...`,
  and any character outside the allowlist.
- `_proxy_get` validates the path before any `httpx.AsyncClient.get` and logs
  the *validated* path (kills the `py/log-injection` sink).
- `entity_risk_detail` now URL-encodes `entity_type` + `entity_value` via
  `urllib.parse.quote(safe="")` before composing the path.

### `services/api/app/api/v1/endpoints/cases.py`

- Same path validator pattern (`_SAFE_PROXY_PATH_RE`, `_validate_agents_path`),
  same `//` rejection.
- `case_investigation_run` URL-encodes `run_id` before proxying.
- `case_investigation_pdf` URL-encodes `run_id` and scrubs both `case_id` and
  `run_id` for the `Content-Disposition` filename via
  `_safe_filename_segment` (kills CR/LF/quote injection in headers).

### `.gitleaksignore`

Six triaged false positives, each with a comment:

- `detections/fixtures/positive/jwt-none-alg.json:jwt:2` — positive test fixture.
- `render.yaml:generic-api-key:70` and `:124` — env var **names**
  (`QUARRY_DISABLE_NEO4J=true`).
- `scripts/detection_specs_part3_application.py:generic-api-key:61` —
  detection rule literal `count_5min_per_ip_gt: 30`.
- `scripts/detection_specs_part2.py:jwt:1111` — positive sample for jwt-none-alg.
- `services/api/tests/test_security_defaults.py:generic-api-key:34` —
  pre-generated Fernet key for tests; production injects the real one via env.

---

## WS7 — Verification

```bash
cd services/api && source .venv/bin/activate
python -m pytest tests/test_lake_sql.py tests/test_lake_rate_limit.py -q
# 69 passed
```

`ws7-verify` (full pytest + MCP build) is still pending and tracked under the
post-rewrite block.

---

## WS8 — Bidirectional ITSM (shipped)

### What landed

- `services/connectors/app/connectors/base.py` — extended `BaseConnector` with
  abstract `push_case` and `push_status_change` methods, plus
  `Capability.PUSH_CASE` / `Capability.PUSH_STATUS` enum members.
- `services/connectors/app/connectors/jira_connector.py` —
  - `push_case`: creates Jira issue with ADF-formatted description, severity →
    priority mapping, summary truncation at 255 chars, `quarry-case-{id}` label
    for round-trip identification, returns `{external_id, external_url, vendor,
    external_status}`.
  - `push_status_change`: discovers transitions via
    `GET /rest/api/3/issue/{key}/transitions`, picks the matching transition by
    target status name, POSTs the transition; no-op when target status isn't
    exposed by the workflow.
  - Falls through to `push_case` when `external_ref is None` (first push).
- `services/connectors/app/connectors/servicenow.py` —
  - `push_case`: POSTs to `/api/now/table/incident`, sets
    `correlation_id="quarry:{case_id}"` for round-tripping Quarry case identity,
    severity → impact/urgency mapping, short_description truncation at 160 chars.
  - `push_status_change`: PATCHes `/api/now/table/incident/{sys_id}` with
    `state`; for `Resolved`/`Closed` adds `close_code` + `close_notes` (required
    by stock instances), otherwise omits them.
- `services/connectors/app/api/router.py` —
  - `POST /connectors/{connector_id}/push_case`
  - `POST /connectors/{connector_id}/push_status_change`
- `services/api/migrations/035_case_external_refs.sql` — `case_external_refs`
  table (one row per `(case_id, vendor)`) with `external_id`, `external_url`,
  `external_status`, `last_synced_at`, `sync_state`, plus indexes for
  inbound webhook lookup by `(vendor, external_id)`.
- `services/api/app/services/case_fanout.py` — projection layer:
  - `fanout_create_case(case_id, tenant_id)` — finds enabled ITSM connectors,
    decrypts auth via `CredentialVault`, POSTs to connectors service, persists
    `case_external_refs` row, returns `FanoutResult`.
  - `fanout_status_change(case_id, tenant_id, old_status, new_status)` —
    looks up existing refs, calls `push_status_change`, updates row.
  - `_serialize_case_for_push(case_row)` — accepts dict or SQLAlchemy `Row`
    (`._mapping`); the test suite uses dicts and the production path uses Rows.
- `services/api/app/api/v1/endpoints/cases.py` — `create_case` and `update_case`
  invoke fan-out after the response is committed (best-effort, errors logged
  not raised).
- `services/api/app/api/v1/endpoints/inbox_itsm.py` — public-surface inbound
  webhook (`POST /v1/inbox/itsm/{token}`) with:
  - HMAC-SHA256 verification via `X-Quarry-Signature` header.
  - Vendor-specific payload parsing (Jira `issue.key`/`fields.status.name`,
    ServiceNow `sys_id`/`state`).
  - `_map_inbound_status` collapsing vendor statuses → Quarry statuses.
  - `case_external_refs` lookup by `(vendor, external_id)`.
  - Idempotent Quarry case status updates (skips if already at target status).
- `services/api/app/api/v1/endpoints/inbox.py` — `itsm-inbound` template added
  to `ALLOWED_TEMPLATE_IDS` and `_TEMPLATE_CATALOG`; `_build_inbox_url` now
  routes ITSM tokens through `OAUTH_PUBLIC_BASE_URL` to the API service.

### Tests — done

- `services/api/tests/test_inbox_itsm_endpoint.py` — **69/69 passing**.
  Covers HMAC verification, payload parsing for both vendors, status mapping,
  external-ref lookup, idempotency, missing-token / wrong-signature paths.
- `services/api/tests/test_case_fanout.py` — **21/21 passing**. Covers
  payload serialization, vault decryption, connector RPC happy path, missing
  external_id, unsupported capability, status-change with no refs, status-change
  with orphaned refs, transport errors.
- `services/connectors/tests/test_push_capabilities.py` — **23/23 passing**.
  Covers Jira `push_case` (payload shape, ADF, label, priority mapping, 255-char
  truncation, 4xx propagation), Jira `push_status_change` (no-ref fallthrough,
  unknown-status no-op, missing-transition no-op, transition discovery + POST,
  4xx on transition POST), ServiceNow `push_case` (correlation_id round-trip,
  short_description truncation at 160, 4xx propagation), ServiceNow
  `push_status_change` (no-ref fallthrough, unknown-status no-op, in-progress
  state-only PATCH, Resolved/Closed close_code+close_notes, 4xx propagation),
  capability declarations on both classes.

**Total WS8 test count: 113/113 passing.**

### Test gotcha — `respx` is not in the connectors test environment

`services/connectors/pyproject.toml` declares `respx` as a dev dep but the
local venv doesn't have it installed (collection errors out for
`test_azure_connectors.py`, `test_gcp_connectors.py`). For
`test_push_capabilities.py` we use `unittest.mock.patch` against
`httpx.AsyncClient` instead — same pattern as
`services/api/tests/test_case_fanout.py`. Helper `_build_response` mocks
`status_code`, `json()`, `text`, `request`, and `raise_for_status` so the
connector code under test sees a faithful `httpx.Response` substitute.

### Test gotcha — `_serialize_case_for_push` accepts dict or Row, not SimpleNamespace

`SimpleNamespace` is *not* iterable as key-value pairs, so
`dict(SimpleNamespace(...))` raises `TypeError`. The serializer goes through
`getattr(case_row, "_mapping", None)` then falls back to `dict(case_row)`,
which works for SQLAlchemy `Row` (production) and plain `dict` (tests). All
test fixtures in `test_case_fanout.py` use `_make_case_row()` returning a dict.

Reference plan §WS8.

---

## WS9 — Docs + Sonali (shipped)

### What landed

- `apps/docs/docs/connectors/api-coverage.md` — capability matrix for all
  42 connectors. Generated programmatically from `BaseConnector` subclasses
  by parsing `capabilities()` return tuples and `ConnectorSchema(...)`
  invocations directly out of source. Grouped by `category` (edr, siem,
  cloud, iam, saas, vcs, network) and includes columns for `OAuth (hosted)`
  and `Federated search`. Closes the "what works where" question Sonali
  flagged — no more reading source to know if a given connector can
  `PUSH_CASE` or only `PULL_ALERTS`.
- `apps/docs/docs/architecture/itsm-as-source-of-truth.md` — explains why
  Quarry is the canonical store for case state and ITSM systems are
  projections. Covers the outbound path (`case_fanout` → `push_case` /
  `push_status_change`), the inbound path (`POST /v1/inbox/itsm` with
  HMAC verification, `_JIRA_INBOUND_STATUS` / `_SNOW_INBOUND_STATUS`
  mapping, `case_external_refs` resolution), conflict resolution rules,
  and what is explicitly **not** synced (Jira priority, ServiceNow
  assignment_group, etc.). Includes a `mermaid` flowchart.
- `apps/docs/docs/operations/sonali-consultation-questions.md` — structured
  question set for CISO / Head of SecOps / IR Lead pre-deployment
  conversations. Covers outcomes, threat model, data sources, case
  lifecycle, agent autonomy, compliance, identity/access, ops, reporting.
  Designed to surface boundary disagreements early rather than discovering
  them mid-rollout.
- `apps/docs/sidebars.ts` — registered all three new pages. Added a new
  "Architecture" category (so `itsm-as-source-of-truth.md` has a home
  outside the Concepts bucket), and slotted the other two under their
  existing "Connectors" and "Operations" categories.
- `docs/architecture/SYSTEM_DESIGN.md` — root-level architecture doc
  resynced with v2.1 reality. Topology diagram now shows `services/api`
  (inbox tokens + HMAC webhooks + CEF/HEC/DNS) and `services/connectors`
  (APScheduler poll + 42 connector classes + push_case/status) as
  parallel front doors feeding `services/ingest`. Service responsibilities
  table gained a `services/connectors` row and `services/api` was
  extended with "ITSM webhook inbox, case fan-out". A new §12 captures
  the v2.1 additions in narrative form with cross-links to the
  Docusaurus pages above.

### Cross-links from §12

- §12.1 → `apps/docs/docs/connectors/api-coverage.md`,
  `apps/docs/docs/operations/credentials.md`
- §12.4 → `apps/docs/docs/architecture/itsm-as-source-of-truth.md`
- §12.6 → `apps/docs/docs/plugins/python-sdk.md`,
  `apps/docs/docs/plugins/go-sdk.md`

Reference plan §WS9.

---

## Live todo snapshot (recreate via TodoWrite after restart)

```json
[
  {"id": "gh-1",                  "content": "Audit current git state, branches, identities in history, working tree", "status": "completed"},
  {"id": "gh-4",                  "content": "Secret scan working tree before any commit/push (gitleaks)", "status": "completed"},
  {"id": "gh-2",                  "content": "Pull live GitHub code-scanning alerts and triage by severity", "status": "completed"},
  {"id": "gh-6",                  "content": "Fix code-scanning issues with minimal diffs (critical/high first)", "status": "completed"},
  {"id": "ws7-tests",             "content": "WS7: lake endpoint unit tests (POST /lake/sql, GET /lake/schema, helpers)", "status": "completed"},
  {"id": "ws8-tests-inbox",       "content": "WS8: Inbox ITSM webhook tests (69 passing)", "status": "completed"},
  {"id": "ws8-tests-fanout",      "content": "WS8: Tests for case_fanout service (21 passing)", "status": "completed"},
  {"id": "ws8-tests-push",        "content": "WS8: Tests for jira/snow push_case/push_status_change methods (23 passing)", "status": "completed"},
  {"id": "tracker-update",        "content": "Update AI_STACK_PLAN_PROGRESS.md to reflect WS8 completion", "status": "completed"},
  {"id": "ws9-api-coverage",      "content": "WS9: write apps/docs/docs/connectors/api-coverage.md", "status": "completed"},
  {"id": "ws9-itsm-sot",          "content": "WS9: write apps/docs/docs/architecture/itsm-as-source-of-truth.md", "status": "completed"},
  {"id": "ws9-sonali",            "content": "WS9: write apps/docs/docs/operations/sonali-consultation-questions.md", "status": "completed"},
  {"id": "ws9-sidebar",           "content": "WS9: register new docs in apps/docs/sidebars.ts", "status": "completed"},
  {"id": "gh-5",                  "content": "Sync docs/architecture (WS3-WS8) so GitHub matches current state", "status": "completed"},
  {"id": "tracker-update-ws9",    "content": "Update AI_STACK_PLAN_PROGRESS.md to mark WS9 done", "status": "completed"},
  {"id": "gh-commit",             "content": "Commit all WS9 + tracker docs with Beenu Arora <beenu@cyble.com> identity (no co-author trailers)", "status": "completed"},
  {"id": "gh-3a",                 "content": "Backup current main to refs/heads/backup/pre-rewrite-2026-05-08 on origin", "status": "completed"},
  {"id": "gh-3b",                 "content": "Install git-filter-repo and build authors/message callbacks (strip non-human co-author trailers, canonicalize all to beenu@cyble.com)", "status": "completed"},
  {"id": "gh-3c",                 "content": "Run git-filter-repo on a fresh mirror; verify locally that all commits show Beenu Arora <beenu@cyble.com> and no Co-authored-by trailers remain", "status": "completed"},
  {"id": "gh-3d",                 "content": "Force-push rewritten main + tags + branches", "status": "completed"},
  {"id": "gh-3e",                 "content": "Verify GitHub contributors graph shows only beenu", "status": "completed"},
  {"id": "gh-prs",                "content": "Close 19 dependabot PRs with explanation; comment on #37 asking K4R7IK to rebase", "status": "completed"},
  {"id": "gh-7",                  "content": "Verify code-scanning alerts cleared after push; record any remaining (3 false positives dismissed; 0 open high/medium/error)", "status": "completed"},
  {"id": "gh-ci-identity",        "content": "Patch CI workflows so machine commits use Beenu Arora identity", "status": "completed"},
  {"id": "tryaisoc-cj",           "content": "Customer journey review of tryaisoc.com — find and fix bugs", "status": "completed"}
]
```

---

## Environment

- Repo: `/Users/beenu/Desktop/Quarry` (branch: `main`)
- Python venv: `services/api/.venv` → `python3.14`
- Activate: `cd services/api && source .venv/bin/activate`
- Test: `python -m pytest tests/test_lake_sql.py tests/test_lake_rate_limit.py -q`
  (currently **69 passed**; smoke check before resuming)
- MCP: `cd services/mcp && pnpm install && pnpm test`
- Git identity (verified): `Beenu Arora <beenu@cyble.com>`

---

## tryaisoc-cj findings (closeout)

`tryaisoc-cj` is DONE. All nine plan workstreams (WS1-WS9), the
GitHub hygiene tail (`gh-1` … `gh-7`, `gh-ci-identity`), and the
customer-journey review of `https://tryaisoc.com` have shipped. The
history rewrite landed cleanly, contributors graph shows only
`beenu`, CodeQL is green (0 open high/medium/error alerts; 3 medium
false positives dismissed with rationale), and the public site is
verified clean on every canonical path the UI actually links to.

### Bugs found and fixed

P0 / P1 only. P2 polish was deferred — none was blocking a customer
journey.

| #  | Severity | URL                                              | Symptom                                                                     | Fix commit | Verified                |
| -- | -------- | ------------------------------------------------ | --------------------------------------------------------------------------- | ---------- | ----------------------- |
| 1  | P0       | `/cases/INC-001?tab=ledger`                      | "Ledger unavailable" — `GET /api/v1/investigations` 405                     | `a8f08c4`  | endpoint returns 200    |
| 2  | P0       | `/api/v1/marketplace`                            | 503 "marketplace/index.json not found" (file outside Docker build context)  | `8328870`  | endpoint returns 200    |
| 3  | P0       | API service boot                                 | FastAPI `AssertionError` on 204 route (`oauth.py` DELETE) crashed startup   | `8328870`  | `/health` returns 200   |
| 4  | P1       | Case workspace + Hunt view (demo mode)           | UI banner + toasts said "backend offline" when only writes are disabled     | `a8f08c4`  | copy reads correctly    |
| 5  | P1       | `sitemap.xml`                                    | `/signup` listed in sitemap but route is 404 (Quarry ships no signup)        | `a8f08c4`  | sitemap clean           |
| 6  | P1       | `/onboarding` "Run a detection" card             | Linked to `/detections` (plural) — 404. Correct path is `/detection`        | `d3240a7`  | card now links to 200   |
| 7  | P1       | `/onboarding` "Bring your own data" card         | Linked to in-app `/docs/operations/credentials` — 404 (docs are external)   | `d3240a7`  | links to GH Pages docs  |
| 8  | P1       | `NextStepCard` component                         | Used `next/link` for cross-origin docs URL; would break target=_blank       | `d3240a7`  | external `<a>` rendered |

### Fix commits

- `a8f08c4` — fix(web): customer-journey bugs — ledger routing, demo
  copy, /signup 404
- `8328870` — fix(api): unblock startup + bake marketplace/index.json
  into api build
- `d3240a7` — fix(web/onboarding): two 404s in NextStepCard footer

All three authored as `Beenu Arora <beenu@cyble.com>` with no
co-author trailers, deployed to `quarry-demo-web` and `quarry-demo-api`
on Fly, and verified live on `tryaisoc.com`.

### Post-deploy verification sweep

Probed every canonical sitemap route and every `/api/v1/*` endpoint
the UI actually calls. All return `200`.

Frontend (15 paths from `apps/web/src/app/sitemap.ts`):
`/`, `/benchmark`, `/connectors`, `/purple-team`, `/responder`,
`/why-open-source`, `/marketplace`, `/compliance`, `/hunt`,
`/copilot`, `/graph`, `/login`, `/detection`, `/threat-intel`,
`/sla` — all 200.

API endpoints the UI calls (7 paths, via `tryaisoc.com` rewrites):
`/api/v1/cases`, `/api/v1/investigations`, `/api/v1/connectors`,
`/api/v1/detection/rules`, `/api/v1/marketplace`,
`/api/v1/marketplace/installed`, `/api/v1/contextual/actions` —
all 200.

Direct API health (`api.tryaisoc.com` / Fly app domain):
`/health` — 200.

### Non-bugs (404s that are correct)

These paths return 404 because they are intentionally not part of the
product surface. Recorded here so a future review does not re-open
them:

- `/signup`, `/pricing`, `/about` — Quarry is open source and
  self-hosted; the only auth entry is `/login`, and the demo lands
  anonymously via the home-page CTA. The hero copy and the
  why-open-source page both state "No signup."
- `/docs`, `/docs-portal` — documentation is hosted separately on
  GitHub Pages and `docs.tryaisoc.com` (cloudflared tunnel to the
  Docusaurus app). The Next.js app deliberately does not serve
  `/docs/*`. All in-app links to docs now use absolute URLs to the
  external host.
- `/detections` (plural), `/runbooks`, `/agents`, `/admin/oauth`,
  `/investigations`, `/maintenance` — not listed in `sitemap.ts` and
  not linked from any UI component under `apps/web/src/`.
- `/api/v1/incidents`, `/api/v1/detections`, `/api/v1/runbooks`,
  `/api/v1/agents/runs`, `/api/v1/contextual/health`,
  `/api/v1/contextual/orgs`, `/api/v1/oauth/apps` — not implemented
  on the API service and not called by the UI. The real names are
  `/api/v1/cases`, `/api/v1/detection/rules`, and the contextual
  endpoints listed above.

### Outstanding non-blocker

`flyctl deploy` for `quarry-demo-web` returned a client-side timeout
warning ("the app is not listening on the expected address") on the
last roll-out, but the new image is live and all post-deploy probes
pass. Recorded here so a future deploy can investigate the listener
warning, but it is not gating the customer journey.

Workspace rule: do not stop until every todo is done. → done.

---

## Session — 2026-05-09 (buyer-value plan: A3, C1, H4)

Three workstreams from `aisoc_v1.0_—_buyer-value_plan_c8116970` shipped
or verified in this session.

### WS-A3 — One-click deploy

`render.yaml` was relocated from `infra/render/render.yaml` to the
repository root so Render's "Deploy to Render" button can resolve it
without a custom path. Updated `README.md` (new "Deploy in 60 seconds"
section + TOC entry), `infra/render/README.md` (relative path), and
`CHANGELOG.md`. Also updated the two `.gitleaksignore` entries that
pinned `infra/render/render.yaml:generic-api-key:70` /`:124` to point
at `render.yaml:generic-api-key:70` /`:124` (the line numbers track
content positions inside `envVars`, not absolute file lines, so they
remain valid post-move). One-click Docker Compose, Render, and Fly.io
buttons are now linked from the README.

### WS-C1 — 25 named playbooks

Verified complete. `playbooks/packs/v1/` contains 50+ playbook JSON
files covering ransomware, BEC, identity, cloud, lateral movement,
data-exfil, privilege escalation, and more. Each playbook conforms
to the schema enforced by `scripts/validate_playbooks.py` (CI gate
in `.github/workflows/validate-playbooks.yml`). The runtime in
`services/agents/app/playbook/store.py` loads `packs/v1/**` on
startup and merges with any user-defined playbooks in
`services/agents/data/playbooks/index.json` (user playbooks win).
No new authoring needed for v1.0 — the v1.0 floor of 25 was passed
and then some.

### WS-H4 — Air-gapped / local-LLM mode

Verified complete and shippable.

- `apps/docs/docs/operations/airgap.md` is comprehensive (allowlist,
  Ollama / vLLM / LiteLLM topology, demo-mode behaviour, audit log
  expectations, "deploy-time only" mutation policy) and is reachable
  from the Docusaurus sidebar at `Operations → Air-gapped deployment`
  via `apps/docs/sidebars.ts`.
- `services/api/app/api/v1/endpoints/llm_status.py` classifies
  providers as `openai | anthropic | azure-openai | local-ollama |
  local-vllm | local-litellm | custom` and exposes a redacted snapshot
  at `GET /api/v1/llm/status`. The Settings UI's "Deployment & AI"
  panel (`apps/web/src/components/settings/SettingsView.tsx`) reads
  both `/api/v1/airgap/status` and `/api/v1/llm/status` and renders
  read-only badges for "Air-gap engaged" + "AI calls route to: …".
  Mutations are deliberately deploy-time only.
- `services/agents/app/api/explain.py:_llm_allowed()` honours
  `QUARRY_AIRGAPPED`: with air-gap on and no `OPENAI_BASE_URL`, the
  outbound call is blocked; with a local proxy URL it is allowed.
- `docker-compose.demo.yml` ships zero outbound LLM calls by
  default (`OPENAI_API_KEY: ${OPENAI_API_KEY:-}` — empty unless the
  operator opts in).

### WS-H2 — BYOK per-tenant settings UI

Shipped. v1.0 buyer-value criteria required per-tenant BYOK; the
existing `CredentialVault` primitive already provided the
encryption story, so we landed the model, endpoints, agents-side
read path, and Settings UI in a single coherent change set.

Backend (services/api):

- `migrations/038_tenant_llm_credentials.sql` — new
  `tenant_llm_credentials` table keyed on `tenant_id`, with a
  `provider` `CHECK` constraint matching the four-tier ladder
  (`openai | anthropic | azure-openai | openai-compatible`),
  a vault-encrypted `api_key_vault` column, audit timestamps,
  and Row-Level Security policies bound to the
  `app.tenant_id` GUC.
- `app/models/llm_credential.py` — `TenantLlmCredential` ORM
  model registered in `app/models/__init__.py` so Alembic and
  the dependency-injected `DBSession` see it.
- `app/api/v1/endpoints/llm_credentials.py` — `GET / PUT /
  DELETE /api/v1/llm/credentials` gated on `settings:read` /
  `settings:write` RBAC. Writes encrypt the API key with
  `CredentialVault` (`vault:v1:` prefix), enforce
  provider-specific invariants (`base_url` mandatory for
  `openai-compatible`, `api_key` mandatory on first write for
  hosted providers), and emit `audit.llm_credential.{created,
  updated,deleted}` records via `emit_audit`. Reads return a
  `LlmCredentialView` projection that *never* includes the
  plaintext key — only `has_api_key: bool`.
- `app/api/v1/endpoints/llm_status.py` — refactored to layer
  the tenant override over the env baseline and surface the
  resolved `source` (`tenant | environment | mixed | none`) so
  the Settings UI can explain provenance.
- `app/api/v1/router.py` — registered the new credentials
  router under `/api/v1/llm/credentials`.

Agents-side read path (services/agents):

- `app/security/credential_vault.py` — vendored read-path copy
  of the API service's vault. Differs only in that
  `get_vault()` returns `None` (instead of raising) when
  `QUARRY_CREDENTIAL_KEY` is missing, so explain stays
  resilient on operator boxes that have not migrated to BYOK
  yet.
- `app/security/llm_resolver.py` — `resolve_llm_config` is
  now the single source of truth for "what config does this
  request actually use?". It layers tenant rows over env vars,
  applies the same air-gap rule as `_llm_allowed`, and returns
  a deterministic fallback so the explain path can still log
  `allowed=False` reasons even when no key is configured. The
  ledger import is lazy so unit tests that mount only the
  explain router don't drag in LangGraph.
- `app/api/explain.py` — calls `resolve_llm_config(tenant_ref)`
  per request instead of reading env vars directly.

Frontend (apps/web):

- `src/components/settings/SettingsView.tsx` — new BYOK panel
  in the "Deployment & AI" section. Read-only by default;
  flips to write mode when the user has `settings:write`.
  Shows `provider`, `base_url`, `model`, `has_api_key`,
  `enabled`, `last_rotated_at`, and the resolved
  `source` from `/llm/status` so the buyer sees where each
  field came from.
- `src/lib/api.ts` — `getLlmCredential`, `putLlmCredential`,
  `deleteLlmCredential` typed clients.

Tests:

- `services/api/tests/test_llm_credentials_endpoint.py` —
  40 tests covering vault round-trip, the `_project` redactor,
  `LlmCredentialUpsert` validators, `_enforce_provider_invariants`,
  GET / PUT / DELETE happy paths, the rotation-only update
  case (`api_key=null` keeps the existing ciphertext), failure
  paths (provider transitions that violate invariants,
  duplicate-tenant `IntegrityError`), and audit emission.
- `services/agents/tests/test_llm_resolver.py` — 33 tests
  covering `_env_baseline` (OPENAI_*, LLM_*, QUARRY_LLM_MODEL
  precedence), `_airgap_blocks`, `_classify_source`,
  `_decrypt_vault_token` (vault disabled, round-trip, corrupt
  ciphertext), and `resolve_llm_config` end-to-end with a
  mocked `asyncpg` pool. Includes the BYOK-under-air-gap
  scenarios (private gateway allowed, OpenAI host blocked
  even with a valid tenant key) and the graceful-degradation
  paths (DB unreachable, ledger import unavailable, vault key
  missing, ciphertext decrypt fails).

All 73 tests pass.

Documentation:

- `apps/docs/docs/operations/credentials.md` — added a "Per-tenant
  LLM credentials (BYOK)" section explaining the
  `tenant_llm_credentials` table, the vault round-trip, and how
  the agents service decrypts at read time.
- `apps/docs/docs/operations/airgap.md` — clarified that BYOK
  to a private LiteLLM/Ollama/vLLM gateway works under
  `QUARRY_AIRGAPPED=true`, while BYOK pointing at
  `api.openai.com` is still blocked.
- `apps/docs/docs/operations/security.md` — added a pointer
  to the BYOK section so the security model document
  enumerates LLM keys alongside connector secrets.

Workspace rule: do not stop until every todo is done.

---

## v1.0 Buyer-Value Plan — COMPLETE (2026-05-10)

Author: Beenu Arora <beenu@cyble.com>
Released as: **v7.0.0** on `main` branch.

All workstreams from `aisoc_v1.0_—_buyer-value_plan_c8116970.plan.md` are
now shipped and verified. See `PROGRESS.md` for the full workstream table,
fix log, and documentation changes.

PR #43 (`feat/threatintel-attribution-v0-fixed`) was squash-merged into
`main` on 2026-05-10 (205 files changed, +16 524 / -1 961 lines).

CHANGELOG promoted to `[7.0.0] — 2026-05-10`.
ROADMAP v7.0 marked Shipped ✅; v8.0 Planned section added.
README version badge updated to `7.0.0`.

The AI Stack & Data Integration plan workstreams (this file) remain at
DONE status — no regressions introduced by the v7.0 buyer-value plan.
