---
id: dashboard-file-integrity
title: File Integrity Monitoring Dashboard
sidebar_label: File Integrity
sidebar_position: 10
---

# File Integrity Monitoring Dashboard

The **File Integrity Monitoring (FIM)** dashboard provides real-time visibility
into file creation, modification, and deletion events across your entire osquery
fleet.  It is available at two locations:

| Route | Description |
|---|---|
| `/fim` | Standalone FIM page with full event table and filters |
| `/dashboard/file-integrity` | Same view embedded in the dashboard section |

## Overview

The FIM dashboard displays data sourced from the osquery `file_events` table,
which is populated by the `aisoc-fim-baseline` and `aisoc-fim-credentials`
packs.

### Summary cards

At the top of the page, four summary cards give a quick health check:

| Card | Description |
|---|---|
| **Total events** | Count of `file_events` rows in the selected time range |
| **Active nodes** | Number of distinct nodes reporting FIM events |
| **By action** | Breakdown of `CREATED`, `MODIFIED`, and `DELETED` events |
| **Top paths** | Top 5 most-frequently modified file paths |

Cards refresh automatically every 60 seconds.

### Event table

The paginated event table lists individual `file_events` rows with columns:

| Column | Description |
|---|---|
| Time | Event timestamp |
| Host | `host_identifier` of the reporting node |
| Action | `CREATED`, `MODIFIED`, or `DELETED` |
| Path | `target_path` |
| User | `username` of the process that triggered the event |
| Hash | SHA-256 of the file at event time |

Click any row to open the full event detail panel, which shows all available
osquery columns and links to related alerts.

## Dashboard widget

The main dashboard (`/dashboard`) includes a compact **FIM + Pack Health**
widget row that shows:

- Last 24-hour FIM event totals
- Active node count
- Pack assignment status

Click **View full dashboard →** in the widget to navigate to `/dashboard/file-integrity`.

## Prerequisites

The FIM dashboard requires at least one osquery pack containing `file_events`
queries to be assigned to your tenant.  Assign the baseline pack:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pack_id": "aisoc-fim-baseline"}' \
  https://api.tryaisoc.com/api/v1/packs/assign
```

See [FIM Baseline pack](../packs/fim-baseline.md) for details.

## Alert integration

FIM events that match a detection rule automatically generate alerts.  The
following detection rules fire on FIM data:

| Rule | Trigger |
|---|---|
| `det-endpoint-297` | Critical system file modified (`/etc/passwd`, `/etc/shadow`, …) |
| `det-endpoint-298` | SSH `authorized_keys` changed |
| `det-endpoint-299` | Sudoers file modified |
| `det-endpoint-300` | New SUID/SGID binary appeared |

Alerts appear in the **Alerts** page and are linked back to the originating
`file_events` row in the FIM dashboard.
