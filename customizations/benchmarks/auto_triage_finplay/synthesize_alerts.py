#!/usr/bin/env python3
"""Sintetiza alertas SOC a partir dos eventos brutos do FinPlay BR.

O dataset FinPlay (`customizations/datasets/br-fintech-generator/output/`)
gera eventos crus de Pix, login, boleto, Open Finance. O auto-triage opera
sobre **alertas**, não eventos — alertas são o output de detectores que
processam streams de eventos e disparam quando vêem padrão suspeito.

Este módulo simula a camada de detecção: lê eventos FinPlay e produz
alertas balanceados com ground-truth label embutido, permitindo medir a
precisão do auto-triage offline (sem precisar rodar pipeline real).

Distribuição alvo (sample 100):
  - 60 true_positive: alertas reais (fraude Pix, SIM swap, scraping)
  - 30 false_positive: alertas que parecem ameaça mas são atividade
    legítima (varreduras agendadas, pen-test interno, software conhecido)
  - 10 benign: ruído informacional sem risco real

Determinístico (seed fixa) — runs são byte-stable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

DEFAULT_SEED = 20260524
DEFAULT_SAMPLE_SIZE = 100
DEFAULT_DIST = {"true_positive": 0.60, "false_positive": 0.30, "benign": 0.10}

FINPLAY_OUTPUT = Path(__file__).resolve().parents[2] / "datasets" / "br-fintech-generator" / "output"


@dataclass
class SynthAlert:
    alert_id: str
    rule_id: str
    severity: str  # critical|high|medium|low|info
    risk_score: float  # 0.0–1.0
    summary: str
    raw: dict[str, Any] = field(default_factory=dict)
    mitre_techniques: list[str] = field(default_factory=list)
    ground_truth: str = "true_positive"  # ground-truth label
    ground_truth_reason: str = ""


def _ah(*parts: str) -> str:
    """Stable short hash for alert IDs."""
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:12]


def _load_events(name: str) -> list[dict[str, Any]]:
    path = FINPLAY_OUTPUT / f"{name}.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _alert_pix_fraud(evt: dict[str, Any]) -> SynthAlert:
    amount = evt.get("amount_brl", 0)
    payee = evt.get("payee", {})
    payer = evt.get("payer", {})
    scn = evt.get("scenario_id", "SCN-unknown")
    return SynthAlert(
        alert_id=f"alt-{_ah('pix-fraud', evt['event_id'])}",
        rule_id="det-pix-001-money-mule-cashout",
        severity="critical" if amount > 3000 else "high",
        risk_score=0.92 if amount > 3000 else 0.78,
        summary=f"Pix de R$ {amount:.2f} para conta laranja recém-criada · cenário {scn}",
        raw={
            "event_kind": "pix.transfer",
            "amount_brl": amount,
            "payer_risk_tier": payer.get("risk_tier"),
            "payee_first_time": payee.get("first_time_payee"),
            "payee_bank_code": payee.get("bank_code"),
            "device_id": evt.get("device_id"),
            "ip_address": evt.get("ip_address"),
            "asn": evt.get("asn"),
            "fraud_label_internal": evt.get("fraud_label"),
        },
        mitre_techniques=["T1657", "T1071"],
        ground_truth="true_positive",
        ground_truth_reason=f"Ground-truth: pix_fraudulent {scn}",
    )


def _alert_ato_attempt(evt: dict[str, Any]) -> SynthAlert:
    scn = evt.get("scenario_id", "SCN-002-sim-swap-high-value")
    return SynthAlert(
        alert_id=f"alt-{_ah('ato', evt['event_id'])}",
        rule_id="det-auth-002-ato-sim-swap",
        severity="high",
        risk_score=0.86,
        summary=f"Account takeover candidato: biometria falha + SIM swap recente · {scn}",
        raw={
            "event_kind": "auth.account_takeover_signal",
            "biometric_result": evt.get("biometric", {}).get("result"),
            "device_id": evt.get("device_id"),
            "geo_city": evt.get("geo_city"),
            "ip_address": evt.get("ip_address"),
            "risk_signal": evt.get("risk_signal"),
            "outcome": evt.get("outcome"),
        },
        mitre_techniques=["T1111", "T1078"],
        ground_truth="true_positive",
        ground_truth_reason="Ground-truth: account_takeover_attempts",
    )


def _alert_openfinance_anomaly(evt: dict[str, Any]) -> SynthAlert:
    return SynthAlert(
        alert_id=f"alt-{_ah('ofx', evt['event_id'])}",
        rule_id="det-openfinance-003-scraping",
        severity="high",
        risk_score=0.81,
        summary="Scraping Open Finance massivo de um único consentimento — fingerprint conhecido",
        raw={
            "event_kind": "openfinance.access_anomaly",
            "app_id": evt.get("app_id", "ofx-ghost"),
            "customer_id": evt.get("customer_id"),
            "consent_id": evt.get("consent_id"),
            "ip_address": evt.get("ip_address"),
        },
        mitre_techniques=["T1213"],
        ground_truth="true_positive",
        ground_truth_reason="Ground-truth: open_finance_anomalies",
    )


def _alert_boleto_fraud(evt: dict[str, Any]) -> SynthAlert:
    return SynthAlert(
        alert_id=f"alt-{_ah('boleto', evt['event_id'])}",
        rule_id="det-boleto-001-beneficiary-mismatch",
        severity="high",
        risk_score=0.79,
        summary="Boleto com beneficiário divergente — primeiro pagamento ao CNPJ recém-aberto",
        raw={
            "event_kind": "boleto.created",
            "beneficiary_mismatch": evt.get("beneficiary_mismatch"),
            "first_time_beneficiary": evt.get("first_time_beneficiary"),
            "amount_brl": evt.get("amount_brl"),
        },
        mitre_techniques=["T1657"],
        ground_truth="true_positive",
        ground_truth_reason="Ground-truth: boleto_fraudulent",
    )


# --- False-positive synthesizers — alertas que parecem ameaça mas não são ---

_FP_TEMPLATES = [
    {
        "rule_id": "det-vuln-007-nmap-scan",
        "severity": "medium",
        "risk_score": 0.65,
        "summary": "Varredura nmap detectada na sub-rede 10.20.0.0/16",
        "raw": {
            "scan_type": "TCP SYN",
            "source": "scanner-internal-01",
            "ports_scanned": 65535,
            "scheduled": True,
            "owner": "blue-team-vulnerability-mgmt",
        },
        "mitre_techniques": ["T1046"],
        "reason": "Varredura interna agendada do time de vulnerability management.",
    },
    {
        "rule_id": "det-edr-014-pwsh-encoded",
        "severity": "high",
        "risk_score": 0.71,
        "summary": "PowerShell com -EncodedCommand executado em estação corporativa",
        "raw": {
            "host": "WIN-DEV-042",
            "user": "svc-deploy",
            "command_b64": "JABzAGUAcgB2AGkAYwBlAA==",
            "parent_process": "deploy-runner.exe",
            "signed_publisher": "FinPlay Pagamentos S.A.",
        },
        "mitre_techniques": ["T1059.001"],
        "reason": "Software de deploy assinado pela empresa — comportamento esperado.",
    },
    {
        "rule_id": "det-pentest-021-known-tool",
        "severity": "critical",
        "risk_score": 0.88,
        "summary": "Sliver C2 beacon detectado de host corporativo",
        "raw": {
            "host": "PENTEST-LAB-007",
            "engagement": "Q2-2026 internal pentest",
            "authorized_by": "ciso@finplay",
            "ticket": "SEC-2026-04-PENTEST",
        },
        "mitre_techniques": ["T1071.001"],
        "reason": "Pentest interno autorizado — ticket SEC-2026-04-PENTEST.",
    },
    {
        "rule_id": "det-pix-009-recurring-payment",
        "severity": "medium",
        "risk_score": 0.55,
        "summary": "Pix recorrente de valor exato disparou alerta de pattern fraud",
        "raw": {
            "customer_id": "cus_012345",
            "payee": "concessionaria-energia-rj",
            "amount_brl": 287.40,
            "monthly_recurring": True,
            "months_seen": 18,
        },
        "mitre_techniques": [],
        "reason": "Pagamento mensal recorrente para concessionária reconhecida há 18 meses.",
    },
    {
        "rule_id": "det-edr-019-script-from-temp",
        "severity": "high",
        "risk_score": 0.72,
        "summary": "Script executado de %TEMP% por usuário comum",
        "raw": {
            "host": "WIN-FIN-118",
            "user": "ana.silva",
            "script_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
            "publisher": "Microsoft Update Standalone Package",
            "signed_authenticode": True,
        },
        "mitre_techniques": ["T1059"],
        "reason": "Atualização Microsoft assinada (hash conhecido na allowlist).",
    },
]


# --- Benign synthesizers — informacional sem risco ---

_BENIGN_TEMPLATES = [
    {
        "rule_id": "det-info-001-mfa-enrollment",
        "severity": "info",
        "risk_score": 0.10,
        "summary": "Cliente concluiu enrollment de MFA via aplicativo",
        "raw": {"customer_id": "cus_077200", "mfa_method": "totp", "outcome": "enrolled"},
        "mitre_techniques": [],
        "reason": "Evento informacional de auditoria — comportamento esperado pós-cadastro.",
    },
    {
        "rule_id": "det-info-002-pix-key-rotated",
        "severity": "low",
        "risk_score": 0.18,
        "summary": "Chave Pix rotacionada por cliente via app",
        "raw": {"customer_id": "cus_004812", "key_type": "phone", "channel": "mobile"},
        "mitre_techniques": [],
        "reason": "Rotação manual de chave Pix — cliente exerceu controle previsto.",
    },
    {
        "rule_id": "det-info-003-tls-cert-renewed",
        "severity": "info",
        "risk_score": 0.05,
        "summary": "Certificado TLS renovado automaticamente pelo cert-manager",
        "raw": {"domain": "api.finplay.com.br", "issuer": "Let's Encrypt", "auto": True},
        "mitre_techniques": [],
        "reason": "Renovação automática de certificado — operacional rotineiro.",
    },
]


def _alert_from_template(template: dict[str, Any], idx: int, kind: str) -> SynthAlert:
    return SynthAlert(
        alert_id=f"alt-{_ah(kind, template['rule_id'], str(idx))}",
        rule_id=template["rule_id"],
        severity=template["severity"],
        risk_score=template["risk_score"],
        summary=template["summary"],
        raw=template["raw"],
        mitre_techniques=template.get("mitre_techniques", []),
        ground_truth=kind,
        ground_truth_reason=template["reason"],
    )


def synthesize(
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    seed: int = DEFAULT_SEED,
    distribution: dict[str, float] | None = None,
) -> list[SynthAlert]:
    """Build a balanced alert sample with deterministic ground-truth."""
    rng = random.Random(seed)
    dist = distribution or DEFAULT_DIST
    target_tp = int(round(sample_size * dist["true_positive"]))
    target_fp = int(round(sample_size * dist["false_positive"]))
    target_benign = sample_size - target_tp - target_fp

    pix_fraud = _load_events("pix_fraudulent")
    ato = _load_events("account_takeover_attempts")
    ofx = _load_events("open_finance_anomalies")
    boleto = _load_events("boleto_fraudulent")

    tp_pool: list[SynthAlert] = []
    tp_pool.extend(_alert_pix_fraud(e) for e in pix_fraud)
    tp_pool.extend(_alert_ato_attempt(e) for e in ato)
    tp_pool.extend(_alert_openfinance_anomaly(e) for e in ofx)
    tp_pool.extend(_alert_boleto_fraud(e) for e in boleto)
    rng.shuffle(tp_pool)
    tp_picked = tp_pool[:target_tp]

    fp_picked = [
        _alert_from_template(_FP_TEMPLATES[i % len(_FP_TEMPLATES)], i, "false_positive")
        for i in range(target_fp)
    ]
    benign_picked = [
        _alert_from_template(_BENIGN_TEMPLATES[i % len(_BENIGN_TEMPLATES)], i, "benign")
        for i in range(target_benign)
    ]

    all_alerts = tp_picked + fp_picked + benign_picked
    rng.shuffle(all_alerts)
    return all_alerts


def write_jsonl(alerts: list[SynthAlert], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for a in alerts:
            f.write(json.dumps(asdict(a), ensure_ascii=False) + "\n")


def main() -> int:
    p = argparse.ArgumentParser(description="Sintetiza alertas FinPlay BR com ground-truth.")
    p.add_argument("--size", type=int, default=DEFAULT_SAMPLE_SIZE)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--out", type=Path, default=Path("alerts.jsonl"))
    args = p.parse_args()

    alerts = synthesize(sample_size=args.size, seed=args.seed)
    write_jsonl(alerts, args.out)

    by_gt: dict[str, int] = {}
    for a in alerts:
        by_gt[a.ground_truth] = by_gt.get(a.ground_truth, 0) + 1

    print(f"Synthesized {len(alerts)} alerts → {args.out}")
    for k, v in sorted(by_gt.items()):
        print(f"  {k:>15}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
