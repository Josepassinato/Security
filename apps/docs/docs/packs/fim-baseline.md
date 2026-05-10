---
id: pack-fim-baseline
title: "Pack: AiSOC FIM Baseline"
sidebar_label: FIM Baseline
sidebar_position: 3
---

# Pack: AiSOC FIM Baseline

**Pack ID:** `aisoc-fim-baseline`  
**Version:** 1.0.0  
**Platforms:** Linux, macOS

## Description

Monitors critical system configuration and credential files for unauthorized
modifications. Covers `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`, and SSH
`authorized_keys` files. Aligns with MITRE ATT&CK
[T1098](https://attack.mitre.org/techniques/T1098/) (Account Manipulation) and
[T1078](https://attack.mitre.org/techniques/T1078/) (Valid Accounts).

## Monitored paths

| Category | Paths |
|---|---|
| `etc` | `/etc/passwd`, `/etc/shadow`, `/etc/group`, `/etc/gshadow` |
| `sudoers` | `/etc/sudoers`, `/etc/sudoers.d/**` |
| `ssh` | `~/.ssh/authorized_keys`, `/etc/ssh/sshd_config` |

## Queries

### `passwd_changes`
Detects writes to `/etc/passwd`, `/etc/shadow`, `/etc/group`, and
`/etc/gshadow`.

- **Interval:** 30 s
- **Severity:** High
- **MITRE:** T1098, T1078

### `sudoers_changes`
Detects modifications to `/etc/sudoers` and `/etc/sudoers.d/`.

- **Interval:** 30 s
- **Severity:** High
- **MITRE:** T1548.003

### `ssh_authorized_keys`
Detects writes to user `authorized_keys` files.

- **Interval:** 60 s
- **Severity:** High
- **MITRE:** T1098.004

## Assigning this pack

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pack_id": "aisoc-fim-baseline"}' \
  https://api.tryaisoc.com/api/v1/packs/assign
```

## Related detections

- `det-endpoint-297` — FIM: Critical system file modified
- `det-endpoint-298` — FIM: SSH authorized_keys changed
- `det-endpoint-299` — FIM: Sudoers file modified
- `det-endpoint-300` — FIM: New SUID/SGID binary
