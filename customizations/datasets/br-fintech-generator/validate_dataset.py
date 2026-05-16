#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

EXPECTED = {
    "pix_legitimate": 100000,
    "pix_fraudulent": 500,
    "auth_logins": 50000,
    "account_takeover_attempts": 200,
    "open_finance_accesses": 10000,
    "open_finance_anomalies": 30,
    "boleto_creations": 5000,
    "boleto_fraudulent": 50,
}
REQUIRED_SCENARIOS = {
    "SCN-001-money-mule-ring",
    "SCN-002-sim-swap-high-value",
    "SCN-003-open-finance-scraping",
    "SCN-004-boleto-fraud-campaign",
}

def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON in {path}:{line_no}: {exc}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="customizations/datasets/br-fintech-generator/output")
    args = parser.parse_args()
    root = Path(args.dir)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Missing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    errors: list[str] = []
    seen_scenarios: set[str] = set()
    for key, expected in EXPECTED.items():
        file_info = manifest["files"].get(key)
        if not file_info:
            errors.append(f"manifest missing file entry {key}")
            continue
        path = Path(file_info["path"])
        if not path.exists():
            errors.append(f"missing file {path}")
            continue
        count = 0
        for event in iter_jsonl(path):
            count += 1
            for required in ["event_id", "timestamp", "event_kind", "event_type", "tenant_id", "synthetic", "fintech"]:
                if required not in event:
                    errors.append(f"{path}: event missing {required}")
                    break
            if event.get("synthetic") is not True:
                errors.append(f"{path}: non synthetic event {event.get('event_id')}")
            if event.get("scenario_id"):
                seen_scenarios.add(event["scenario_id"])
        if count != expected:
            errors.append(f"{key}: expected {expected}, got {count}")
    if manifest.get("files", {}).get("customers", {}).get("records") != 50000:
        errors.append("customers.csv must contain 50000 customers")
    missing = REQUIRED_SCENARIOS - seen_scenarios
    if missing:
        errors.append(f"missing scenarios: {sorted(missing)}")
    if errors:
        print("FAIL")
        for err in errors[:80]:
            print("-", err)
        return 1
    print(json.dumps({"status": "ok", "validated_files": len(EXPECTED), "scenarios": sorted(seen_scenarios)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
