#!/usr/bin/env python3
"""Generate the FinPlay Pagamentos synthetic BR fintech dataset.

The generator uses only deterministic synthetic data. It does not read or
transform any real customer, transaction, bank, phone, or Open Finance data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid5, NAMESPACE_URL

DATASET_VERSION = "2026.05-card009"
DEFAULT_SEED = 20260515
TENANT_ID = "00000000-0000-0000-0000-000000000001"
FINTECH = {
    "name": "FinPlay Pagamentos",
    "legal_name": "FinPlay Pagamentos S.A. (ficticia)",
    "city": "Sao Paulo",
    "state": "SP",
    "country": "BR",
    "products": ["conta_digital", "cartao", "pix"],
    "active_customers": 50000,
    "synthetic": True,
}
COUNTS = {
    "pix_legitimate": 100000,
    "pix_fraudulent": 500,
    "auth_logins": 50000,
    "account_takeover_attempts": 200,
    "open_finance_accesses": 10000,
    "open_finance_anomalies": 30,
    "boleto_creations": 5000,
    "boleto_fraudulent": 50,
    "supporting_hunt_evidence": 120,
}
FILES = {
    "pix_legitimate": "pix_legitimate.jsonl",
    "pix_fraudulent": "pix_fraudulent.jsonl",
    "auth_logins": "auth_logins.jsonl",
    "account_takeover_attempts": "account_takeover_attempts.jsonl",
    "open_finance_accesses": "open_finance_accesses.jsonl",
    "open_finance_anomalies": "open_finance_anomalies.jsonl",
    "boleto_creations": "boleto_creations.jsonl",
    "boleto_fraudulent": "boleto_fraudulent.jsonl",
    "supporting_hunt_evidence": "supporting_hunt_evidence.jsonl",
}
SCENARIOS = {
    "SCN-001-money-mule-ring": {
        "name": "Money mule ring com 20 contas",
        "related_hunts": ["HUNT-PIX-001", "HUNT-MULE-001"],
        "related_patterns": ["PIX-001", "SEN-001", "VSH-001"],
    },
    "SCN-002-sim-swap-high-value": {
        "name": "SIM swap em conta high-value",
        "related_hunts": ["HUNT-SIM-001", "HUNT-ATO-001"],
        "related_patterns": ["ATO-001"],
    },
    "SCN-003-open-finance-scraping": {
        "name": "Open Finance scraping anomalo",
        "related_hunts": ["HUNT-OFI-001"],
        "related_patterns": ["OFI-001"],
    },
    "SCN-004-boleto-fraud-campaign": {
        "name": "Boleto fraud campaign",
        "related_hunts": ["HUNT-BOL-001"],
        "related_patterns": ["BOL-001", "MAL-001"],
    },
}

FIRST_NAMES = ["Ana", "Bruno", "Carla", "Diego", "Eduarda", "Felipe", "Gabriela", "Henrique", "Isabela", "Joao", "Karen", "Lucas", "Mariana", "Nicolas", "Olivia", "Paulo", "Renata", "Sofia", "Tiago", "Valeria"]
LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Pereira", "Costa", "Rodrigues", "Almeida", "Nascimento", "Lima", "Gomes", "Ribeiro", "Martins", "Carvalho", "Araujo", "Melo"]
CITIES = ["Sao Paulo", "Guarulhos", "Osasco", "Campinas", "Santo Andre", "Sao Bernardo do Campo", "Sorocaba", "Ribeirao Preto", "Santos", "Barueri"]
BANKS = ["260", "336", "077", "237", "341", "001", "033", "104", "290", "380"]
TPPS = ["Mercado Integrado Open", "FinData AISP", "ContaFlux ITP", "Pagamentos Conecta", "CreditHub Brasil", "OpenBridge Finance"]
USER_AGENTS = ["FinPlayApp/6.8 iOS", "FinPlayApp/6.8 Android", "FinPlayApp/6.7 Android", "Mozilla/5.0 Mobile", "FinPlayWeb/3.2"]
ASNS = ["AS28573", "AS18881", "AS27699", "AS7738", "AS16735", "AS10429"]

@dataclass(frozen=True)
class Customer:
    customer_id: str
    account_id: str
    cpf: str
    name: str
    city: str
    risk_tier: str
    monthly_income_brl: int
    device_id: str
    phone_hash: str
    created_at: datetime

class Writer:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.file = path.open("w", encoding="utf-8")
        self.count = 0
        self.sha = hashlib.sha256()
    def write(self, event: dict[str, Any]) -> None:
        line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
        self.file.write(line)
        self.sha.update(line.encode("utf-8"))
        self.count += 1
    def close(self) -> dict[str, Any]:
        self.file.close()
        return {"path": str(self.path), "records": self.count, "sha256": self.sha.hexdigest(), "bytes": self.path.stat().st_size}

def event_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{uuid5(NAMESPACE_URL, '|'.join(map(str, parts)))}"

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def rand_dt(rng: random.Random, start: datetime, days: int = 30) -> datetime:
    return start + timedelta(seconds=rng.randint(0, days * 24 * 3600 - 1))

def cpf_like(n: int) -> str:
    raw = str(10000000000 + n).zfill(11)[-11:]
    return f"{raw[:3]}.{raw[3:6]}.{raw[6:9]}-{raw[9:]}"

def pix_key_for(customer_id: str) -> str:
    digest = hashlib.sha1(customer_id.encode()).hexdigest()[:32]
    return f"{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"

def make_customers(rng: random.Random, start: datetime, total: int = 50000) -> list[Customer]:
    customers: list[Customer] = []
    for i in range(total):
        cid = f"cus_{i+1:06d}"
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        risk = rng.choices(["low", "medium", "high"], weights=[82, 15, 3])[0]
        customers.append(Customer(
            customer_id=cid,
            account_id=f"acc_{i+1:06d}",
            cpf=cpf_like(i + 12345),
            name=f"{first} {last}",
            city=rng.choice(CITIES),
            risk_tier=risk,
            monthly_income_brl=rng.randint(1800, 42000 if risk == "high" else 16000),
            device_id=f"dev_{hashlib.sha1((cid + 'device').encode()).hexdigest()[:16]}",
            phone_hash=hashlib.sha256((cid + 'phone').encode()).hexdigest()[:20],
            created_at=start - timedelta(days=rng.randint(1, 900)),
        ))
    return customers

def base_event(kind: str, ts: datetime, connector: str, source: str, event_type: str, scenario: str | None = None) -> dict[str, Any]:
    event = {
        "dataset": "finplay_br_synthetic",
        "dataset_version": DATASET_VERSION,
        "tenant_id": TENANT_ID,
        "synthetic": True,
        "fintech": FINTECH,
        "event_kind": kind,
        "event_type": event_type,
        "timestamp": iso(ts),
        "connector_id": f"finplay-{connector}",
        "connector_type": connector,
        "source_format": source,
    }
    if scenario:
        event["scenario_id"] = scenario
        event["scenario_name"] = SCENARIOS[scenario]["name"]
    return event

def pix_event(rng: random.Random, ts: datetime, customer: Customer, amount: float, status: str = "settled", scenario: str | None = None, fraud_label: str | None = None, recipient_account: str | None = None) -> dict[str, Any]:
    recipient_bank = rng.choice(BANKS)
    recipient = recipient_account or f"ext_acc_{rng.randint(1, 90000):06d}"
    evt = base_event("pix", ts, "pix-gateway", "spi_simplified_json", "pix.transfer", scenario)
    evt.update({
        "event_id": event_id("pix", ts.timestamp(), customer.customer_id, amount, recipient),
        "spi": {
            "end_to_end_id": f"E{recipient_bank}{ts.strftime('%Y%m%d')}{rng.randint(10**20, 10**21-1)}",
            "tx_id": f"TX{rng.randint(10**8, 10**9-1)}",
            "settlement_method": "SPI",
            "initiation_type": rng.choice(["manual", "pix_key", "static_qr", "dynamic_qr"]),
            "purpose": rng.choice(["transfer", "purchase", "bill_payment", "refund"]),
        },
        "payer": {
            "customer_id": customer.customer_id,
            "account_id": customer.account_id,
            "cpf_hash": hashlib.sha256(customer.cpf.encode()).hexdigest()[:24],
            "city": customer.city,
            "risk_tier": customer.risk_tier,
            "pix_key": pix_key_for(customer.customer_id),
        },
        "payee": {
            "bank_code": recipient_bank,
            "account_id": recipient,
            "pix_key_hash": hashlib.sha256(recipient.encode()).hexdigest()[:24],
            "first_time_payee": rng.random() < (0.42 if scenario else 0.08),
        },
        "amount_brl": round(amount, 2),
        "status": status,
        "channel": rng.choice(["mobile", "web", "api"]),
        "device_id": customer.device_id,
        "ip_address": f"177.{rng.randint(10,250)}.{rng.randint(0,255)}.{rng.randint(1,254)}",
        "asn": rng.choice(ASNS),
        "fraud_label": fraud_label or "legitimate",
    })
    return evt

def auth_event(rng: random.Random, ts: datetime, customer: Customer, event_type: str = "auth.login_success", scenario: str | None = None, outcome: str = "success", risk_signal: str | None = None) -> dict[str, Any]:
    evt = base_event("auth", ts, "mobile-auth", "oauth2_biometric_json", event_type, scenario)
    evt.update({
        "event_id": event_id("auth", ts.timestamp(), customer.customer_id, event_type, risk_signal or "normal"),
        "customer_id": customer.customer_id,
        "account_id": customer.account_id,
        "oauth": {
            "grant_type": rng.choice(["authorization_code", "refresh_token", "device_code"]),
            "client_id": rng.choice(["finplay-mobile-ios", "finplay-mobile-android", "finplay-web"]),
            "scope": "openid profile account pix payments",
        },
        "biometric": {
            "used": rng.random() < 0.72,
            "method": rng.choice(["face", "fingerprint", "device_pin"]),
            "result": "passed" if outcome == "success" else "failed",
        },
        "device_id": customer.device_id if not risk_signal else f"dev_suspect_{rng.randint(1000,9999)}",
        "user_agent": rng.choice(USER_AGENTS),
        "ip_address": f"191.{rng.randint(10,250)}.{rng.randint(0,255)}.{rng.randint(1,254)}",
        "asn": rng.choice(ASNS if not risk_signal else ["AS9009", "AS20473", "AS14061"]),
        "geo_city": customer.city if not risk_signal else rng.choice(["Bogota", "Lisboa", "Miami", "Santiago"]),
        "outcome": outcome,
        "risk_signal": risk_signal or "baseline",
        "mfa_method": rng.choice(["push", "biometric", "totp", "sms"]),
    })
    return evt

def open_finance_event(rng: random.Random, ts: datetime, customer: Customer, scenario: str | None = None, risk_signal: str | None = None) -> dict[str, Any]:
    tpp = rng.choice(TPPS)
    max_scope = bool(risk_signal)
    evt = base_event("open_finance", ts, "open-finance", "bacen_open_finance_simplified_json", "open_finance.api_call", scenario)
    evt.update({
        "event_id": event_id("ofi", ts.timestamp(), customer.customer_id, tpp, risk_signal or "baseline"),
        "customer_id": customer.customer_id,
        "consent_id": f"cons_{hashlib.sha1((customer.customer_id + tpp).encode()).hexdigest()[:16]}",
        "tpp": {
            "name": tpp,
            "directory_status": "active" if risk_signal not in {"revoked_certificate_active_call"} else "suspended",
            "certificate_status": "valid" if risk_signal not in {"revoked_certificate_active_call"} else "revoked",
            "registered_asn": rng.choice(ASNS),
        },
        "scopes": ["accounts", "transactions", "balances", "payments"] if max_scope else rng.sample(["accounts", "transactions", "balances", "credit_cards"], k=rng.randint(1, 3)),
        "endpoint": rng.choice(["/open-banking/accounts/v1/accounts", "/open-banking/transactions/v1/transactions", "/open-banking/payments/v4/pix/payments"]),
        "http_status": 200,
        "source_asn": rng.choice(["AS9009", "AS20473"]) if risk_signal == "asn_mismatch" else rng.choice(ASNS),
        "calls_in_window_1h": rng.randint(1, 30) if not risk_signal else rng.randint(600, 1600),
        "risk_signal": risk_signal or "baseline",
    })
    return evt

def boleto_event(rng: random.Random, ts: datetime, customer: Customer, scenario: str | None = None, fraud_label: str | None = None) -> dict[str, Any]:
    evt = base_event("boleto", ts, "boleto-core", "structured_app_json", "boleto.created", scenario)
    expected_doc = f"{rng.randint(10_000_000,99_999_999)}/0001-{rng.randint(10,99)}"
    paid_doc = expected_doc if not fraud_label else f"{rng.randint(10_000_000,99_999_999)}/0001-{rng.randint(10,99)}"
    evt.update({
        "event_id": event_id("bol", ts.timestamp(), customer.customer_id, expected_doc, fraud_label or "legit"),
        "customer_id": customer.customer_id,
        "boleto_id": f"bol_{hashlib.sha1((customer.customer_id + str(ts.timestamp())).encode()).hexdigest()[:18]}",
        "linha_digitavel_hash": hashlib.sha256(f"{customer.customer_id}{ts.timestamp()}".encode()).hexdigest()[:32],
        "amount_brl": round(rng.uniform(65, 4500) if not fraud_label else rng.uniform(600, 12000), 2),
        "beneficiary_expected_document": expected_doc,
        "beneficiary_paid_document": paid_doc,
        "beneficiary_mismatch": bool(fraud_label),
        "first_time_beneficiary": bool(fraud_label) or rng.random() < 0.12,
        "channel": rng.choice(["mobile", "web"]),
        "fraud_label": fraud_label or "legitimate",
    })
    return evt

def support_event(rng: random.Random, ts: datetime, customer: Customer, support_type: str) -> dict[str, Any]:
    connector = {
        "privileged_access": "admin-audit",
        "data_exfiltration": "data-access",
        "crypto_aml": "crypto-ledger",
        "phishing_case": "support-fraud",
    }[support_type]
    evt = base_event("supporting_hunt_evidence", ts, connector, "structured_app_json", f"support.{support_type}")
    evt.update({
        "event_id": event_id("sup", ts.timestamp(), customer.customer_id, support_type),
        "customer_id": customer.customer_id,
        "account_id": customer.account_id,
        "support_type": support_type,
        "risk_signal": support_type,
        "amount_brl": round(rng.uniform(800, 95000), 2),
        "device_id": customer.device_id,
        "ip_address": f"189.{rng.randint(10,250)}.{rng.randint(0,255)}.{rng.randint(1,254)}",
        "related_hunts": {
            "privileged_access": ["HUNT-PRIV-001"],
            "data_exfiltration": ["HUNT-EXFIL-001"],
            "crypto_aml": ["HUNT-AML-001"],
            "phishing_case": ["HUNT-VSH-001"],
        }[support_type],
        "evidence": {
            "privileged_access": {"operator_id": f"ops_{rng.randint(10,99)}", "accounts_touched_count": rng.randint(25, 900), "ticket_id": None, "off_hours": True},
            "data_exfiltration": {"rows_returned": rng.randint(12000, 250000), "export_format": rng.choice(["csv", "parquet", "xlsx"]), "destination_classification": "non_allowlisted"},
            "crypto_aml": {"offramp_ratio_72h": round(rng.uniform(0.78, 0.98), 3), "cluster_accounts": rng.randint(5, 22), "pep_flag": rng.random() < 0.1},
            "phishing_case": {"ticket_keywords": ["falsa central", "estorno", "pix", "urgente"], "new_payee_after_contact": True},
        }[support_type],
    })
    return evt

def write_csv_customers(path: Path, customers: list[Customer]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["customer_id", "account_id", "cpf_synthetic", "name", "city", "risk_tier", "monthly_income_brl", "device_id", "created_at"])
        w.writeheader()
        for c in customers:
            w.writerow({
                "customer_id": c.customer_id,
                "account_id": c.account_id,
                "cpf_synthetic": c.cpf,
                "name": c.name,
                "city": c.city,
                "risk_tier": c.risk_tier,
                "monthly_income_brl": c.monthly_income_brl,
                "device_id": c.device_id,
                "created_at": iso(c.created_at),
            })

def generate(out_dir: Path, seed: int = DEFAULT_SEED, start: datetime | None = None, days: int = 30) -> dict[str, Any]:
    rng = random.Random(seed)
    start = start or datetime(2026, 4, 1, tzinfo=timezone.utc)
    out_dir.mkdir(parents=True, exist_ok=True)
    customers = make_customers(rng, start)
    write_csv_customers(out_dir / "customers.csv", customers)
    high_value = max(customers, key=lambda c: c.monthly_income_brl)
    mule_accounts = customers[:20]
    mule_destination = "ext_mule_operator_000001"
    open_finance_victims = customers[100:130]
    boleto_victims = customers[300:350]
    stats: dict[str, Any] = {"seed": seed, "start": iso(start), "days": days, "files": {}, "scenarios": {k: {**v, "events": 0} for k, v in SCENARIOS.items()}}
    writers = {k: Writer(out_dir / v) for k, v in FILES.items()}
    try:
        for _ in range(COUNTS["pix_legitimate"]):
            c = rng.choice(customers)
            amount = max(1.0, rng.lognormvariate(5.2, 0.85))
            writers["pix_legitimate"].write(pix_event(rng, rand_dt(rng, start, days), c, min(amount, 18000)))
        for i in range(COUNTS["pix_fraudulent"]):
            if i < 300:
                c = mule_accounts[i % len(mule_accounts)]
                ts = start + timedelta(days=7, minutes=i * 3)
                amount = rng.uniform(1400, 9800)
                scenario = "SCN-001-money-mule-ring"
                stats["scenarios"][scenario]["events"] += 1
                writers["pix_fraudulent"].write(pix_event(rng, ts, c, amount, scenario=scenario, fraud_label="money_mule_inbound_outbound", recipient_account=mule_destination))
            elif i < 380:
                ts = start + timedelta(days=14, minutes=i)
                scenario = "SCN-002-sim-swap-high-value"
                stats["scenarios"][scenario]["events"] += 1
                writers["pix_fraudulent"].write(pix_event(rng, ts, high_value, rng.uniform(6000, 25000), scenario=scenario, fraud_label="sim_swap_high_value_pix"))
            else:
                c = rng.choice(customers)
                scenario = "SCN-004-boleto-fraud-campaign" if i % 2 == 0 else "SCN-001-money-mule-ring"
                stats["scenarios"][scenario]["events"] += 1
                writers["pix_fraudulent"].write(pix_event(rng, rand_dt(rng, start, days), c, rng.uniform(500, 12000), scenario=scenario, fraud_label="social_engineering_pix"))
        for _ in range(COUNTS["auth_logins"]):
            writers["auth_logins"].write(auth_event(rng, rand_dt(rng, start, days), rng.choice(customers)))
        for i in range(COUNTS["account_takeover_attempts"]):
            c = high_value if i < 40 else rng.choice(customers)
            scenario = "SCN-002-sim-swap-high-value"
            stats["scenarios"][scenario]["events"] += 1
            ts = start + timedelta(days=14, minutes=i * 2)
            risk = rng.choice(["sim_swap_recent_iccid_change", "new_device_high_value", "impossible_travel", "sms_mfa_after_phone_change"])
            writers["account_takeover_attempts"].write(auth_event(rng, ts, c, event_type="auth.account_takeover_signal", scenario=scenario, outcome=rng.choice(["success", "blocked", "challenge_failed"]), risk_signal=risk))
        for _ in range(COUNTS["open_finance_accesses"]):
            writers["open_finance_accesses"].write(open_finance_event(rng, rand_dt(rng, start, days), rng.choice(customers)))
        risk_signals = ["max_scope_first_time_customer", "tpp_volume_burst", "asn_mismatch", "revoked_consent_used", "fast_high_value_payment", "revoked_certificate_active_call"]
        for i in range(COUNTS["open_finance_anomalies"]):
            scenario = "SCN-003-open-finance-scraping"
            stats["scenarios"][scenario]["events"] += 1
            writers["open_finance_anomalies"].write(open_finance_event(rng, start + timedelta(days=20, minutes=i * 5), open_finance_victims[i % len(open_finance_victims)], scenario=scenario, risk_signal=rng.choice(risk_signals)))
        for _ in range(COUNTS["boleto_creations"]):
            writers["boleto_creations"].write(boleto_event(rng, rand_dt(rng, start, days), rng.choice(customers)))
        for i in range(COUNTS["boleto_fraudulent"]):
            scenario = "SCN-004-boleto-fraud-campaign"
            stats["scenarios"][scenario]["events"] += 1
            writers["boleto_fraudulent"].write(boleto_event(rng, start + timedelta(days=23, minutes=i * 11), boleto_victims[i % len(boleto_victims)], scenario=scenario, fraud_label="beneficiary_mismatch_campaign"))
        support_types = ["privileged_access", "data_exfiltration", "crypto_aml", "phishing_case"]
        for i in range(COUNTS["supporting_hunt_evidence"]):
            support_type = support_types[i % len(support_types)]
            ts = start + timedelta(days=25 + (i % 5), minutes=i * 13)
            writers["supporting_hunt_evidence"].write(support_event(rng, ts, customers[(700 + i) % len(customers)], support_type))
    finally:
        for key, w in writers.items():
            stats["files"][key] = w.close()
    stats["files"]["customers"] = {"path": str(out_dir / "customers.csv"), "records": len(customers), "bytes": (out_dir / "customers.csv").stat().st_size, "sha256": hashlib.sha256((out_dir / "customers.csv").read_bytes()).hexdigest()}
    stats["expected_counts"] = COUNTS
    stats["fintech"] = FINTECH
    stats["total_events"] = sum(COUNTS.values())
    (out_dir / "manifest.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return stats

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic FinPlay BR fintech dataset")
    parser.add_argument("--out", default="customizations/datasets/br-fintech-generator/output", help="Output directory")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--start", default="2026-04-01T00:00:00Z")
    args = parser.parse_args()
    start = datetime.fromisoformat(args.start.replace("Z", "+00:00"))
    stats = generate(Path(args.out), seed=args.seed, start=start)
    print(json.dumps({"status": "ok", "out": args.out, "total_events": stats["total_events"], "files": {k: v["records"] for k, v in stats["files"].items()}}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
