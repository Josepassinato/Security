---
id: extensions-security-model
title: Extension Security Model
sidebar_label: Security Model
sidebar_position: 4
---

# Extension Security Model

## Host-scoped tokens

The AiSOC extension authenticates to the API using a **host-scoped JWT** — a
short-lived token that is:

- Bound to a single `host_identifier` (cannot be reused on another node)
- Scoped to the `extensions:read` permission only
- Issued by the AiSOC API during TLS enrolment
- Valid for 24 hours and automatically refreshed by the extension

This design limits blast radius: a compromised token on one node cannot be used
to access data for other nodes or to perform write operations.

## Token lifecycle

```
1. Node enrols via TLS (POST /api/v1/enroll)
         │
2. AiSOC API issues host-scoped token
   (stored in /etc/osquery/aisoc-extension.env)
         │
3. Extension starts → validates token (GET /api/v1/me)
         │
4. Every 23 hours → token auto-refresh
   (POST /api/v1/extensions/refresh-token)
         │
5. If node is decommissioned → token revoked
   (all subsequent API calls return 401)
```

## API permission model

| Permission | Grants |
|---|---|
| `extensions:read` | Read pending-actions, alert-cache, persistence-baseline |

The `extensions:read` scope is separate from tenant admin scopes.  It is the
minimum privilege needed for the extension to function and does not grant access
to the management API.

## Network security

- All traffic uses TLS 1.2+ to `api.tryaisoc.com`
- Certificate pinning is enforced in the extension binary
- The extension never accepts inbound connections; it only makes outbound HTTPS
  calls to the AiSOC API

## Local security

- The extension binary is owned by `root:root` with mode `0755`
- The env file (`aisoc-extension.env`) is owned by `root:root` with mode `0600`
- The token stored in the env file is the only secret; there are no additional
  credentials or keys

## Token revocation

To revoke a host-scoped token immediately (e.g. on node decommission):

```bash
curl -X DELETE -H "Authorization: Bearer $TENANT_TOKEN" \
  "https://api.tryaisoc.com/api/v1/nodes/<host_identifier>/extension-token"
```

After revocation, the extension on that node will receive `401 Unauthorized`
and cease polling.

## Threat model

| Threat | Mitigation |
|---|---|
| Token theft from disk | Tokens are host-scoped and short-lived (24 h) |
| MITM attack on API calls | Certificate pinning + TLS 1.2+ |
| Privilege escalation via extension | Extension only reads data; no write/exec API |
| Malicious osquery query | Virtual tables return pre-fetched data; no arbitrary SQL to the API |
| Supply chain attack on binary | SHA-256 pinning in the install script; releases are GPG-signed |
