#!/usr/bin/env python3
"""Push generated FinPlay JSONL files to Quarry ingest over HTTP.

Requires the Quarry ingest service to be running. This script is intentionally
not executed on the shared production VPS until the Quarry runtime is isolated.
"""
from __future__ import annotations
import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_TENANT = "00000000-0000-0000-0000-000000000001"

def batched(events, size: int):
    batch = []
    for event in events:
        batch.append(event)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch

def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def post_batch(url: str, tenant_id: str, connector_id: str, connector_type: str, events: list[dict], dry_run: bool) -> dict:
    if dry_run:
        return {"accepted": len(events), "rejected": 0, "dry_run": True}
    payload = json.dumps({
        "connector_id": connector_id,
        "connector_type": connector_type,
        "source_format": "finplay_synthetic_json",
        "events": events,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST", headers={"Content-Type": "application/json", "X-Tenant-ID": tenant_id})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {"accepted": len(events), "rejected": 0}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"ingest returned {exc.code}: {exc.read().decode('utf-8', 'replace')[:500]}") from exc

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="customizations/datasets/br-fintech-generator/output")
    parser.add_argument("--ingest-url", default="http://localhost:8001/v1/ingest/batch")
    parser.add_argument("--tenant-id", default=DEFAULT_TENANT)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(args.dir)
    manifest = json.loads((root / "manifest.json").read_text())
    results = {}
    for key, info in manifest["files"].items():
        if key == "customers":
            continue
        path = Path(info["path"])
        accepted = 0
        connector_type = key.replace("_", "-")
        for batch in batched(read_jsonl(path), args.batch_size):
            result = post_batch(args.ingest_url, args.tenant_id, f"finplay-{connector_type}", connector_type, batch, args.dry_run)
            accepted += int(result.get("accepted", len(batch)))
        results[key] = accepted
        print(f"{key}: {accepted}")
    print(json.dumps({"status": "ok", "dry_run": args.dry_run, "results": results}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
