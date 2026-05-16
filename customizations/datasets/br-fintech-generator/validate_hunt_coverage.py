#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

EXPECTED_HUNTS = {
    "HUNT-PIX-001": "fraude organizada Pix",
    "HUNT-MULE-001": "money mule network",
    "HUNT-ATO-001": "account takeover",
    "HUNT-SIM-001": "SIM swap",
    "HUNT-OFI-001": "Open Finance scraping",
    "HUNT-BOL-001": "boleto fraud",
    "HUNT-VSH-001": "falsa central/phishing",
    "HUNT-PRIV-001": "privileged access",
    "HUNT-EXFIL-001": "data exfiltration",
    "HUNT-AML-001": "crypto AML",
}

def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="customizations/datasets/br-fintech-generator/output")
    args = parser.parse_args()
    root = Path(args.dir)
    coverage = Counter()
    for event in read_jsonl(root / "pix_fraudulent.jsonl"):
        scenario = event.get("scenario_id")
        label = event.get("fraud_label")
        if scenario == "SCN-001-money-mule-ring":
            coverage["HUNT-PIX-001"] += 1
            coverage["HUNT-MULE-001"] += 1
        if scenario == "SCN-002-sim-swap-high-value":
            coverage["HUNT-ATO-001"] += 1
            coverage["HUNT-SIM-001"] += 1
        if label == "social_engineering_pix":
            coverage["HUNT-VSH-001"] += 1
    for event in read_jsonl(root / "account_takeover_attempts.jsonl"):
        if event.get("scenario_id") == "SCN-002-sim-swap-high-value":
            coverage["HUNT-ATO-001"] += 1
            coverage["HUNT-SIM-001"] += 1
    for event in read_jsonl(root / "open_finance_anomalies.jsonl"):
        if event.get("scenario_id") == "SCN-003-open-finance-scraping":
            coverage["HUNT-OFI-001"] += 1
    for event in read_jsonl(root / "boleto_fraudulent.jsonl"):
        if event.get("scenario_id") == "SCN-004-boleto-fraud-campaign":
            coverage["HUNT-BOL-001"] += 1
    support_path = root / "supporting_hunt_evidence.jsonl"
    if support_path.exists():
        for event in read_jsonl(support_path):
            for hunt_id in event.get("related_hunts", []):
                coverage[hunt_id] += 1
    missing = [hunt for hunt in EXPECTED_HUNTS if coverage[hunt] <= 0]
    result = {hunt: {"name": EXPECTED_HUNTS[hunt], "matching_events": coverage[hunt]} for hunt in EXPECTED_HUNTS}
    if missing:
        print(json.dumps({"status": "fail", "missing": missing, "coverage": result}, indent=2, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "ok", "coverage": result}, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
