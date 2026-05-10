---
id: pack-fim-credentials
title: "Pack: AiSOC FIM Credentials"
sidebar_label: FIM Credentials
sidebar_position: 4
---

# Pack: AiSOC FIM Credentials

**Pack ID:** `aisoc-fim-credentials`  
**Version:** 1.0.0  
**Platforms:** Linux, macOS

## Description

Watches credential and cryptographic key material paths for tampering or
exfiltration. Monitors private keys, certificate stores, cloud-provider
credentials, and password managers. Aligns with MITRE ATT&CK
[T1552](https://attack.mitre.org/techniques/T1552/) (Unsecured Credentials) and
[T1555](https://attack.mitre.org/techniques/T1555/) (Credentials from Password
Stores).

## Monitored paths

| Category | Paths |
|---|---|
| `ssh_keys` | `~/.ssh/id_*`, `~/.ssh/*.pem` |
| `aws_creds` | `~/.aws/credentials`, `~/.aws/config` |
| `gcp_creds` | `~/.config/gcloud/credentials.db` |
| `gpg` | `~/.gnupg/%%` |
| `ssl_certs` | `/etc/ssl/private/%%`, `/etc/pki/%%` |

## Queries

### `private_key_access`
Detects reads or writes to SSH private key files.

- **Interval:** 60 s
- **Severity:** High
- **MITRE:** T1552.004

### `cloud_credential_access`
Detects writes to AWS, GCP, or Azure credential files.

- **Interval:** 60 s
- **Severity:** High
- **MITRE:** T1552.001

### `ssl_private_key_access`
Detects writes to `/etc/ssl/private/` or `/etc/pki/`.

- **Interval:** 60 s
- **Severity:** High
- **MITRE:** T1552

## Assigning this pack

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pack_id": "aisoc-fim-credentials"}' \
  https://api.tryaisoc.com/api/v1/packs/assign
```
