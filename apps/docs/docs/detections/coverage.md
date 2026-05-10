---
title: Detection Coverage
description: |
  AiSOC v1.0 ships a curated set of MITRE ATT&CK-mapped
  detections covering the eight buyer-prioritised threat
  families. This page is generated from the on-disk corpus
  via ``scripts/curate_detections.py`` — it is the source
  of truth for what we promise in v1.0.
sidebar_position: 2
---

# Detection Coverage

Generated: `2026-05-10T14:50:52Z`

## Headline numbers

- **Curated v1.0 detections**: `411` (target: ≥ 300)
- **Total rules considered**: `1011` (quality floor: 0.55)
- **Unique MITRE techniques covered**: `113`

## Coverage by buyer family

| Family | Count | Target | Covered |
|---|---|---|---|
| **Ransomware** | 46 | ≥ 25 | ✅ |
| **Credential Access** | 83 | ≥ 25 | ✅ |
| **Lateral Movement** | 32 | ≥ 25 | ✅ |
| **Data Exfiltration** | 41 | ≥ 25 | ✅ |
| **Cloud** | 100 | ≥ 25 | ✅ |
| **Identity** | 100 | ≥ 25 | ✅ |
| **Supply Chain** | 36 | ≥ 25 | ✅ |
| **Kubernetes / Containers** | 73 | ≥ 25 | ✅ |

## Distribution

### By tier

- `imported`: 41
- `native`: 370

### By severity

- `critical`: 99
- `high`: 206
- `low`: 6
- `medium`: 100

### By category

- `application`: 29
- `cloud`: 162
- `data-exfil`: 20
- `endpoint`: 112
- `identity`: 76
- `network`: 12

## How to audit

The curated rule IDs are listed in [`marketplace/curated.json`](https://github.com/aisoc-platform/aisoc/blob/main/marketplace/curated.json) under each family. Every entry has a `path` field pointing at the on-disk YAML. Run `pnpm marketplace:curate --check` in CI to enforce drift; run `python3 scripts/curate_detections.py` locally to regenerate.

