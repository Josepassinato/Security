---
id: extensions-tables-reference
title: Virtual Tables Reference
sidebar_label: Tables Reference
sidebar_position: 3
---

# Virtual Tables Reference

All five virtual tables are available immediately after the extension starts.
They are read-only (`SELECT`-only) and return fresh data on each query.

---

## `aisoc_pending_actions` {#aisoc_pending_actions}

Actions queued by the AiSOC server that the extension should execute on the
host.  Polled from `GET /api/v1/extensions/pending-actions` every 60 seconds.

| Column | Type | Description |
|---|---|---|
| `action_id` | `TEXT` | Unique action identifier (UUID) |
| `action_type` | `TEXT` | Type of action, e.g. `isolate`, `kill_process`, `collect_artifact` |
| `payload` | `TEXT` | JSON-encoded action parameters |
| `created_at` | `TEXT` | ISO-8601 timestamp when the action was queued |

### Example

```sql
SELECT action_id, action_type, json_extract(payload, '$.pid') AS pid
FROM aisoc_pending_actions
WHERE action_type = 'kill_process';
```

---

## `aisoc_alert_cache` {#aisoc_alert_cache}

Recent alerts for this host, cached locally to enable correlated detection
without round-trips.  Polled from `GET /api/v1/extensions/alert-cache` every
5 minutes.

| Column | Type | Description |
|---|---|---|
| `alert_id` | `TEXT` | Alert UUID |
| `rule_id` | `TEXT` | Detection rule identifier |
| `severity` | `TEXT` | `info`, `low`, `medium`, or `high` |
| `title` | `TEXT` | Human-readable alert title |
| `fired_at` | `TEXT` | ISO-8601 timestamp |

### Example

```sql
SELECT severity, title, fired_at
FROM aisoc_alert_cache
WHERE severity IN ('high', 'medium')
ORDER BY fired_at DESC
LIMIT 10;
```

---

## `aisoc_attck_persistence` {#aisoc_attck_persistence}

ATT&CK persistence baseline deltas — entries that exist on the host but are
not in the approved baseline stored on the server.  Polled from
`GET /api/v1/extensions/persistence-baseline` every 5 minutes.

| Column | Type | Description |
|---|---|---|
| `technique_id` | `TEXT` | MITRE ATT&CK technique ID, e.g. `T1053.003` |
| `technique_name` | `TEXT` | Human-readable technique name |
| `evidence` | `TEXT` | JSON evidence fragment (command line, path, user) |
| `risk_score` | `INTEGER` | 0–100 risk score |
| `observed_at` | `TEXT` | ISO-8601 timestamp |

### Example

```sql
SELECT technique_id, technique_name, risk_score
FROM aisoc_attck_persistence
WHERE risk_score > 50
ORDER BY risk_score DESC;
```

---

## `aisoc_kernel_modules_verified` {#aisoc_kernel_modules_verified}

Loaded kernel modules annotated with verification status from LKRG/Sigma
allowlist lookups.  Data is computed locally by joining `kernel_modules` with
the extension's allowlist database.

| Column | Type | Description |
|---|---|---|
| `name` | `TEXT` | Module name |
| `size` | `INTEGER` | Module size in bytes |
| `used_by` | `TEXT` | Dependent modules |
| `status` | `TEXT` | `verified`, `unknown`, or `suspicious` |
| `sha256` | `TEXT` | SHA-256 of the module file |

### Example

```sql
SELECT name, status, sha256
FROM aisoc_kernel_modules_verified
WHERE status != 'verified';
```

---

## `aisoc_browser_extensions` {#aisoc_browser_extensions}

Installed browser extensions across Chrome, Firefox, and Edge with risk
scoring derived from the AiSOC threat intelligence feed.

| Column | Type | Description |
|---|---|---|
| `browser` | `TEXT` | `chrome`, `firefox`, or `edge` |
| `extension_id` | `TEXT` | Browser-specific extension identifier |
| `name` | `TEXT` | Display name |
| `version` | `TEXT` | Extension version |
| `permissions` | `TEXT` | JSON array of requested permissions |
| `risk_score` | `INTEGER` | 0–100 risk score |
| `username` | `TEXT` | Local OS user who has the extension installed |

### Example

```sql
SELECT username, browser, name, risk_score
FROM aisoc_browser_extensions
WHERE risk_score > 70
ORDER BY risk_score DESC;
```
