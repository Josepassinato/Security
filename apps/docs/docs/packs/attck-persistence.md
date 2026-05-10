---
id: pack-attck-persistence
title: "Pack: AiSOC ATT&CK Persistence"
sidebar_label: ATT&CK Persistence
sidebar_position: 5
---

# Pack: AiSOC ATT&CK Persistence

**Pack ID:** `aisoc-attck-persistence`  
**Version:** 1.0.0  
**Platforms:** Linux, macOS, Windows

## Description

Detects MITRE ATT&CK persistence techniques by querying osquery tables that
expose scheduled tasks, startup items, kernel modules, cron jobs, and login
items. Data from this pack also feeds the `aisoc_attck_persistence` virtual
table exposed by the AiSOC osquery extension.

## Covered techniques

| Technique | ID | Description |
|---|---|---|
| Scheduled Task/Job | T1053 | cron, at, systemd timers |
| Boot/Logon Autostart | T1547 | rc.local, login items, startup entries |
| Create or Modify System Process | T1543 | systemd unit files, launchd plists |
| Kernel Modules | T1547.006 | Loaded kernel modules (Linux) |
| Browser Extensions | T1176 | Installed browser extensions |

## Queries

### `cron_jobs`
Lists all cron jobs across users.

- **Interval:** 3600 s
- **Severity:** Medium
- **MITRE:** T1053.003

### `systemd_units`
Lists enabled systemd unit files.

- **Interval:** 3600 s
- **Severity:** Medium
- **MITRE:** T1543.002

### `kernel_modules`
Lists loaded kernel modules.

- **Interval:** 1800 s
- **Severity:** Medium
- **MITRE:** T1547.006

### `startup_items`
Lists macOS startup items.

- **Interval:** 3600 s
- **Severity:** Medium
- **MITRE:** T1547.011

### `browser_extensions`
Lists installed browser extensions.

- **Interval:** 3600 s
- **Severity:** Low
- **MITRE:** T1176

## Assigning this pack

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pack_id": "aisoc-attck-persistence"}' \
  https://api.tryaisoc.com/api/v1/packs/assign
```

## Virtual table integration

When the AiSOC osquery extension (`aisoc_attck_persistence`) is installed on a
node it polls `GET /api/v1/extensions/persistence-baseline` every 5 minutes to
build a local baseline and surfaces new entries as osquery rows.  See the
[Extensions documentation](../extensions/index.md) for details.
