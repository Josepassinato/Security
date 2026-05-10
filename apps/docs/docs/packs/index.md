---
id: packs-overview
title: Osquery Packs
sidebar_label: Overview
sidebar_position: 1
---

# Osquery Packs

AiSOC ships a curated library of **osquery packs** — bundled query sets that
you can assign to your tenant's fleet with a single API call.  Packs combine
related queries that share a theme (FIM, ATT&CK persistence, inventory, …)
and are version-controlled alongside AiSOC's detection content.

## How packs work

```
packs/*.yaml  →  pack_loader  →  catalog (in-memory)
                                       │
                           POST /api/v1/packs/assign
                                       │
                                pack_assignment (Postgres)
                                       │
                           compiled osquery JSON config
                           returned by the TLS enrol endpoint
```

1. **Pack YAML files** live in `packs/` at the root of the repository.  Each
   file follows the [Pack YAML schema](schema.md).
2. The **pack loader** reads and validates all YAML files at startup and
   caches them in memory.
3. Tenants use the **pack catalog API** (`GET /api/v1/packs`) to browse
   available packs and the assignment API to opt-in or opt-out.
4. When an osquery node enrolls, the compiled pack configuration is injected
   into the node's schedule automatically.

## Available packs

| Pack | Purpose |
|---|---|
| [aisoc-fim-baseline](fim-baseline.md) | Monitor creation, modification, and deletion of critical files |
| [aisoc-fim-credentials](fim-credentials.md) | Watch credential and key material paths for tampering |
| [aisoc-attck-persistence](attck-persistence.md) | Detect ATT&CK persistence techniques (T1053, T1547, …) |
| [aisoc-attck-defense-evasion](attck-defense-evasion.md) | Detect defense-evasion indicators (rootkits, log clearing) |
| [aisoc-inventory-baseline](inventory-baseline.md) | Hardware, software, and network inventory queries |

## Quick start

```bash
# List available packs
curl -H "Authorization: Bearer $TOKEN" \
  https://api.tryaisoc.com/api/v1/packs

# Assign the FIM baseline pack to your tenant
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pack_id": "aisoc-fim-baseline"}' \
  https://api.tryaisoc.com/api/v1/packs/assign

# Verify the assignment
curl -H "Authorization: Bearer $TOKEN" \
  https://api.tryaisoc.com/api/v1/packs/assigned
```

## API reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/packs` | List all packs in the catalog |
| `GET` | `/api/v1/packs/{pack_id}` | Get a single pack's full detail |
| `GET` | `/api/v1/packs/{pack_id}/render` | Render pack in osctrl, fleetdm, or osquery-json format |
| `GET` | `/api/v1/packs/assigned` | List packs assigned to the current tenant |
| `POST` | `/api/v1/packs/assign` | Assign a pack to the current tenant |
| `DELETE` | `/api/v1/packs/unassign/{pack_id}` | Remove a pack assignment |

See the [Pack YAML schema](schema.md) for authoring your own packs.
