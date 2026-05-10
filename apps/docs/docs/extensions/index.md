---
id: extensions-overview
title: AiSOC Osquery Extension
sidebar_label: Overview
sidebar_position: 1
---

# AiSOC Osquery Extension

The AiSOC osquery extension (`aisoc-extension`) is a Go-based osquery external
extension that adds five **virtual tables** to every enrolled node.  These
tables bridge real-time server-side intelligence (pending actions, active
alerts, ATT&CK baselines) into the osquery SQL runtime on the host.

## Architecture

```
AiSOC API  ──────────────────────────────────────────────
           GET /api/v1/extensions/pending-actions
           GET /api/v1/extensions/alert-cache
           GET /api/v1/extensions/persistence-baseline
                         │
                    host-scoped JWT
                         │
               aisoc-extension (Go process)
                         │
             ┌───────────┼───────────────────┐
             │           │                   │
  aisoc_pending_actions  aisoc_alert_cache  aisoc_attck_persistence
  aisoc_kernel_modules_verified
  aisoc_browser_extensions
             │
         osquery process (via Unix socket)
```

The extension authenticates to the AiSOC API using a **host-scoped token**
bound to the node's `host_identifier`.  The token requires the
`extensions:read` scope and is provisioned automatically during TLS enrolment.

## Virtual tables

| Table | Description |
|---|---|
| [`aisoc_pending_actions`](tables-reference.md#aisoc_pending_actions) | Actions queued by the server that the extension must execute on the host |
| [`aisoc_alert_cache`](tables-reference.md#aisoc_alert_cache) | Recent alerts for this host cached locally for correlation |
| [`aisoc_attck_persistence`](tables-reference.md#aisoc_attck_persistence) | ATT&CK persistence baseline deltas sourced from the API |
| [`aisoc_kernel_modules_verified`](tables-reference.md#aisoc_kernel_modules_verified) | Loaded kernel modules annotated with LKRG/Sigma verification status |
| [`aisoc_browser_extensions`](tables-reference.md#aisoc_browser_extensions) | Installed browser extensions with risk scoring |

## Quick start

```bash
# Install
curl -fsSL https://releases.tryaisoc.com/extension/install.sh | bash

# Verify
osqueryi "SELECT * FROM aisoc_pending_actions LIMIT 5;"
```

See [Installation](install.md) for detailed setup instructions.

## API reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/extensions/pending-actions` | Pending actions for a host |
| `GET` | `/api/v1/extensions/alert-cache` | Recent alerts for a host |
| `GET` | `/api/v1/extensions/persistence-baseline` | ATT&CK persistence baseline |

Authentication requires `Authorization: Bearer <host-scoped-token>` with the
`extensions:read` permission.  See [Security Model](security-model.md).
