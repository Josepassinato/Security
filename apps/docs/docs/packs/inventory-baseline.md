---
id: pack-inventory-baseline
title: "Pack: AiSOC Inventory Baseline"
sidebar_label: Inventory Baseline
sidebar_position: 7
---

# Pack: AiSOC Inventory Baseline

**Pack ID:** `aisoc-inventory-baseline`  
**Version:** 1.0.0  
**Platforms:** Linux, macOS, Windows

## Description

Collects hardware, software, and network inventory data from every enrolled
node. Designed for asset discovery, compliance baselining, and change
detection. Results flow into the AiSOC CMDB and are searchable from the
Investigation workspace.

## Queries

### `system_info`
CPU, memory, UUID, and OS version.

- **Interval:** 86400 s (once per day)
- **Severity:** Info

### `installed_packages`
All installed packages (RPM/DEB/macOS packages).

- **Interval:** 86400 s
- **Severity:** Info

### `listening_ports`
All TCP/UDP listening sockets with owning process.

- **Interval:** 3600 s
- **Severity:** Low

### `interface_addresses`
All network interface IP addresses.

- **Interval:** 3600 s
- **Severity:** Info

### `users`
All local user accounts.

- **Interval:** 86400 s
- **Severity:** Low

## Assigning this pack

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pack_id": "aisoc-inventory-baseline"}' \
  https://api.tryaisoc.com/api/v1/packs/assign
```
