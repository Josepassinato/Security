---
id: pack-attck-defense-evasion
title: "Pack: AiSOC ATT&CK Defense Evasion"
sidebar_label: ATT&CK Defense Evasion
sidebar_position: 6
---

# Pack: AiSOC ATT&CK Defense Evasion

**Pack ID:** `aisoc-attck-defense-evasion`  
**Version:** 1.0.0  
**Platforms:** Linux, macOS

## Description

Detects indicators of defense-evasion activity including rootkit installation,
audit-log tampering, binary masquerading, and `LD_PRELOAD` hijacking. Aligns
with MITRE ATT&CK [TA0005](https://attack.mitre.org/tactics/TA0005/) (Defense
Evasion).

## Covered techniques

| Technique | ID | Description |
|---|---|---|
| Rootkit | T1014 | Hidden kernel modules and processes |
| Indicator Removal | T1070 | Log file deletion/truncation |
| Hijack Execution Flow | T1574.006 | `LD_PRELOAD` / dynamic linker abuse |
| Masquerading | T1036 | Processes named to mimic system daemons |

## Queries

### `hidden_files`
Detects files hidden using `...` or unusual dotfile patterns in sensitive dirs.

- **Interval:** 3600 s
- **Severity:** High
- **MITRE:** T1014

### `ld_preload`
Reads `/etc/ld.so.preload` and per-process `LD_PRELOAD` env.

- **Interval:** 1800 s
- **Severity:** High
- **MITRE:** T1574.006

### `cleared_logs`
Detects recently truncated or deleted log files under `/var/log/`.

- **Interval:** 900 s
- **Severity:** High
- **MITRE:** T1070.002

## Assigning this pack

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pack_id": "aisoc-attck-defense-evasion"}' \
  https://api.tryaisoc.com/api/v1/packs/assign
```
