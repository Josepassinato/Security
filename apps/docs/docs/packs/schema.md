---
id: packs-schema
title: Pack YAML Schema
sidebar_label: YAML Schema
sidebar_position: 2
---

# Pack YAML Schema

All osquery pack definitions live in `packs/*.yaml` at the repository root.
The loader validates every file against the schema below at startup.

## Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | ✅ | Unique identifier, e.g. `aisoc-fim-baseline` |
| `name` | `string` | ✅ | Human-readable name |
| `version` | `string` | ✅ | Semantic version, e.g. `1.0.0` |
| `platforms` | `string[]` | ✅ | One or more of `linux`, `darwin`, `windows` |
| `description` | `string` | ✅ | Short description of the pack's purpose |
| `discovery` | `string[]` | | Optional osquery discovery queries |
| `queries` | `Query[]` | ✅ | One or more query definitions (see below) |
| `file_paths` | `FilePath[]` | | Optional FIM path categories |

## Query fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | ✅ | Query name (must be unique within the pack) |
| `sql` | `string` | ✅ | The osquery SQL statement |
| `interval` | `integer` | ✅ | Polling interval in seconds |
| `severity` | `string` | | One of `info`, `low`, `medium`, `high` |
| `mitre` | `string[]` | | MITRE ATT&CK technique IDs, e.g. `["T1053.003"]` |
| `references` | `string[]` | | Supporting URLs |

## FilePath fields (FIM only)

| Field | Type | Required | Description |
|---|---|---|---|
| `category` | `string` | ✅ | Logical category name, e.g. `etc` |
| `paths` | `string[]` | ✅ | Glob patterns to monitor |

## Example

```yaml
id: aisoc-fim-baseline
name: AiSOC FIM Baseline
version: 1.0.0
platforms:
  - linux
  - darwin
description: Monitor creation, modification, and deletion of critical system files.

file_paths:
  - category: etc
    paths:
      - /etc/%%
  - category: binaries
    paths:
      - /usr/bin/%%
      - /usr/sbin/%%

queries:
  - name: file_events_etc
    sql: |
      SELECT action, target_path, inode, sha256, username
      FROM file_events
      WHERE category = 'etc';
    interval: 30
    severity: medium
    mitre:
      - T1565.001
```

## Authoring guidelines

- Keep `id` lowercase, hyphenated, and prefixed with `aisoc-`.
- Prefer `interval` values that are multiples of 30 s for alignment.
- Tag every query with the most specific MITRE technique where applicable.
- Run `pnpm marketplace:sync` after adding a pack to keep the marketplace
  manifest in sync.
