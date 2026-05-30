"""Deterministic PLD/FT analysis engine.

The engine intentionally avoids LLM calls. It produces explainable findings
from transaction/KYC inputs so compliance teams can audit exactly why a case
was opened and later calibrate thresholds with specialists.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from typing import Any

DEFAULT_THRESHOLDS: dict[str, float | int] = {
    "passThroughMinAmount": 3000,
    "passThroughWindowMinutes": 90,
    "passThroughRatio": 0.8,
    "outboundFanoutMinCounterparties": 3,
    "outboundFanoutMinTotal": 12000,
    "multiVictimMinSenders": 4,
    "multiVictimMinInboundTotal": 8000,
    "multiVictimOutboundRatio": 0.65,
    "economicMismatchMinAmount": 15000,
    "economicMismatchMultiplier": 4,
    "economicMismatchCriticalMultiplier": 8,
    "newAccountMaxAgeDays": 20,
    "newAccountLargeSendMinAmount": 5000,
    "deviceReuseMinCustomers": 3,
    "structuringMinTransactions": 5,
    "structuringMinSingleAmount": 1000,
    "structuringMaxSingleAmount": 10000,
    "structuringMinTotal": 25000,
    "cryptoAdjacencyMinAmount": 3000,
    "cryptoAdjacencyInboundRatio": 0.7,
}


def payload_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _amount(tx: dict[str, Any]) -> float:
    try:
        return max(0.0, float(tx.get("amount") or 0))
    except (TypeError, ValueError):
        return 0.0


def _time(tx: dict[str, Any]) -> float:
    value = str(tx.get("timestamp") or "")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _sum(transactions: list[dict[str, Any]]) -> float:
    return sum(_amount(tx) for tx in transactions)


def _brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _severity(score: int) -> str:
    if score >= 85:
        return "critical"
    if score >= 65:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _thresholds(payload: dict[str, Any], saved: dict[str, Any] | None = None) -> dict[str, Any]:
    thresholds = dict(DEFAULT_THRESHOLDS)
    thresholds.update(saved or {})
    thresholds.update(payload.get("thresholds") or {})
    return thresholds


def _customers(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("customerId")): item for item in payload.get("customers") or [] if item.get("customerId")}


def _by_customer(transactions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for tx in transactions:
        groups[str(tx.get("customerId") or tx.get("accountId") or "unknown")].append(tx)
    return groups


def _finding(
    *,
    rule_id: str,
    title: str,
    severity: str,
    score: int,
    entity_id: str,
    entity_type: str,
    rationale: str,
    evidence: list[str],
    transactions: list[dict[str, Any]],
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "ruleId": rule_id,
        "title": title,
        "severity": severity,
        "score": score,
        "entityId": entity_id,
        "entityType": entity_type,
        "rationale": rationale,
        "evidence": evidence,
        "transactionIds": [str(tx.get("id")) for tx in transactions if tx.get("id")],
        "amountInScope": _sum(transactions),
        "recommendedAction": recommended_action,
    }


def _add(findings: list[dict[str, Any]], finding: dict[str, Any]) -> None:
    key = (finding["ruleId"], finding["entityId"], tuple(sorted(finding["transactionIds"])))
    for item in findings:
        if (item["ruleId"], item["entityId"], tuple(sorted(item["transactionIds"]))) == key:
            return
    findings.append(finding)


def _detect_pass_through(transactions: list[dict[str, Any]], findings: list[dict[str, Any]], t: dict[str, Any]) -> None:
    for customer_id, txs in _by_customer(transactions).items():
        inbound = sorted([tx for tx in txs if tx.get("direction") == "in"], key=_time)
        outbound = sorted([tx for tx in txs if tx.get("direction") == "out"], key=_time)
        for tx_in in inbound:
            start = _time(tx_in)
            close_out = [
                tx
                for tx in outbound
                if 0 <= (_time(tx) - start) / 60 <= float(t["passThroughWindowMinutes"])
            ]
            out_total = _sum(close_out)
            if _amount(tx_in) >= float(t["passThroughMinAmount"]) and out_total >= _amount(tx_in) * float(t["passThroughRatio"]):
                _add(
                    findings,
                    _finding(
                        rule_id="PLD-PIX-001",
                        title="Conta de passagem: entrada seguida de saída rápida",
                        severity="critical",
                        score=92,
                        entity_id=customer_id,
                        entity_type="customer",
                        rationale="Entrada relevante seguida de repasse de parcela substancial em janela curta.",
                        evidence=[
                            f"Entrada {tx_in.get('id')} de {_brl(_amount(tx_in))}.",
                            f"Saídas próximas somam {_brl(out_total)}.",
                            f"Parâmetro: {round(float(t['passThroughRatio']) * 100)}% em até {t['passThroughWindowMinutes']} minutos.",
                        ],
                        transactions=[tx_in, *close_out],
                        recommended_action="Abrir caso PLD/FT, revisar origem dos recursos e avaliar bloqueio preventivo conforme política interna.",
                    ),
                )


def _detect_fanout(transactions: list[dict[str, Any]], findings: list[dict[str, Any]], t: dict[str, Any]) -> None:
    for customer_id, txs in _by_customer(transactions).items():
        outbound = [tx for tx in txs if tx.get("direction") == "out" and tx.get("rail") == "Pix"]
        counterparties = {str(tx.get("counterpartyId")) for tx in outbound}
        total = _sum(outbound)
        if len(counterparties) >= int(t["outboundFanoutMinCounterparties"]) and total >= float(t["outboundFanoutMinTotal"]):
            _add(
                findings,
                _finding(
                    rule_id="PLD-PIX-002",
                    title="Fan-out Pix para múltiplos favorecidos",
                    severity="high",
                    score=76,
                    entity_id=customer_id,
                    entity_type="customer",
                    rationale="Múltiplas saídas Pix para favorecidos distintos sugerem dispersão de recursos.",
                    evidence=[f"{len(counterparties)} favorecidos distintos.", f"Volume de saída: {_brl(total)}."],
                    transactions=outbound,
                    recommended_action="Validar vínculo econômico dos favorecidos e recorrência histórica.",
                ),
            )


def _detect_multi_victim(transactions: list[dict[str, Any]], findings: list[dict[str, Any]], t: dict[str, Any]) -> None:
    for customer_id, txs in _by_customer(transactions).items():
        inbound = [tx for tx in txs if tx.get("direction") == "in"]
        senders = {str(tx.get("counterpartyId")) for tx in inbound}
        inbound_total = _sum(inbound)
        outbound_total = _sum([tx for tx in txs if tx.get("direction") == "out"])
        if (
            len(senders) >= int(t["multiVictimMinSenders"])
            and inbound_total >= float(t["multiVictimMinInboundTotal"])
            and outbound_total >= inbound_total * float(t["multiVictimOutboundRatio"])
        ):
            _add(
                findings,
                _finding(
                    rule_id="PLD-PIX-003",
                    title="Agregação de múltiplos remetentes e repasse posterior",
                    severity="critical",
                    score=88,
                    entity_id=customer_id,
                    entity_type="customer",
                    rationale="Recebimentos de vários remetentes com repasse posterior relevante.",
                    evidence=[f"{len(senders)} remetentes distintos.", f"Entradas {_brl(inbound_total)}; saídas {_brl(outbound_total)}."],
                    transactions=txs,
                    recommended_action="Checar origem/finalidade e possíveis contestações/MED.",
                ),
            )


def _detect_kyc(transactions: list[dict[str, Any]], customers: dict[str, dict[str, Any]], findings: list[dict[str, Any]], t: dict[str, Any]) -> None:
    for customer_id, txs in _by_customer(transactions).items():
        profile = customers.get(customer_id) or {}
        declared = float(profile.get("declaredMonthlyRevenue") or profile.get("declaredMonthlyIncome") or 0)
        moved = _sum(txs)
        if declared and moved >= float(t["economicMismatchMinAmount"]) and moved / declared >= float(t["economicMismatchMultiplier"]):
            multiplier = moved / declared
            sev = "critical" if multiplier >= float(t["economicMismatchCriticalMultiplier"]) else "high"
            _add(
                findings,
                _finding(
                    rule_id="PLD-KYC-004",
                    title="Movimentação incompatível com perfil econômico declarado",
                    severity=sev,
                    score=90 if sev == "critical" else 72,
                    entity_id=customer_id,
                    entity_type="customer",
                    rationale="Volume movimentado excede múltiplos relevantes da renda/faturamento declarado.",
                    evidence=[f"Declarado: {_brl(declared)}.", f"Movimentado: {_brl(moved)} ({multiplier:.1f}x)."],
                    transactions=txs,
                    recommended_action="Atualizar KYC e solicitar comprovação de atividade econômica.",
                ),
            )
        if int(profile.get("accountAgeDays") or 999) <= int(t["newAccountMaxAgeDays"]):
            outbound = sorted([tx for tx in txs if tx.get("direction") == "out"], key=_time)
            first_large = next((tx for tx in outbound if _amount(tx) >= float(t["newAccountLargeSendMinAmount"])), None)
            if first_large:
                _add(
                    findings,
                    _finding(
                        rule_id="PLD-KYC-005",
                        title="Conta nova com primeira saída relevante",
                        severity="high",
                        score=70,
                        entity_id=customer_id,
                        entity_type="customer",
                        rationale="Conta recém-aberta realizando saída relevante antes de formar histórico.",
                        evidence=[f"Idade da conta: {profile.get('accountAgeDays', 0)} dia(s).", f"Saída: {_brl(_amount(first_large))}."],
                        transactions=[first_large],
                        recommended_action="Aplicar diligência reforçada de onboarding, device, IP e origem dos fundos.",
                    ),
                )


def _detect_device_reuse(transactions: list[dict[str, Any]], findings: list[dict[str, Any]], t: dict[str, Any]) -> None:
    devices: dict[str, set[str]] = defaultdict(set)
    for tx in transactions:
        if tx.get("deviceId"):
            devices[str(tx["deviceId"])].add(str(tx.get("customerId")))
    for device_id, customers in devices.items():
        if len(customers) >= int(t["deviceReuseMinCustomers"]):
            related = [tx for tx in transactions if str(tx.get("deviceId")) == device_id]
            _add(
                findings,
                _finding(
                    rule_id="PLD-DEV-006",
                    title="Dispositivo reutilizado por múltiplas contas",
                    severity="critical",
                    score=87,
                    entity_id=device_id,
                    entity_type="device",
                    rationale="Mesmo device aparece em múltiplos clientes, sinal de rede operacional.",
                    evidence=[f"Device {device_id} aparece em {len(customers)} clientes.", f"Volume relacionado: {_brl(_sum(related))}."],
                    transactions=related,
                    recommended_action="Correlacionar KYC, IP, geolocalização e documentos das contas ligadas.",
                ),
            )


def _detect_structuring(transactions: list[dict[str, Any]], findings: list[dict[str, Any]], t: dict[str, Any]) -> None:
    for customer_id, txs in _by_customer(transactions).items():
        outbound = [
            tx
            for tx in txs
            if tx.get("direction") == "out"
            and float(t["structuringMinSingleAmount"]) <= _amount(tx) < float(t["structuringMaxSingleAmount"])
        ]
        total = _sum(outbound)
        if len(outbound) >= int(t["structuringMinTransactions"]) and total >= float(t["structuringMinTotal"]):
            _add(
                findings,
                _finding(
                    rule_id="PLD-STR-007",
                    title="Fracionamento recorrente abaixo de faixa sensível",
                    severity="high",
                    score=74,
                    entity_id=customer_id,
                    entity_type="customer",
                    rationale="Sequência de transações menores pode indicar estruturação.",
                    evidence=[f"{len(outbound)} saídas em faixa sensível.", f"Total fracionado: {_brl(total)}."],
                    transactions=outbound,
                    recommended_action="Avaliar padrão agregado, favorecidos e justificativa econômica.",
                ),
            )


def _detect_lists(transactions: list[dict[str, Any]], customers: dict[str, dict[str, Any]], findings: list[dict[str, Any]]) -> None:
    for customer_id, txs in _by_customer(transactions).items():
        profile = customers.get(customer_id) or {}
        flags = [
            name
            for field, name in [
                ("sanctionsHit", "sanções/lista restritiva"),
                ("pep", "PEP"),
                ("adverseMedia", "mídia adversa"),
                ("highRiskActivity", "atividade de alto risco"),
            ]
            if profile.get(field)
        ]
        if flags:
            sanctions = bool(profile.get("sanctionsHit"))
            _add(
                findings,
                _finding(
                    rule_id="PLD-LIST-008",
                    title="Exposição de cadastro a lista, PEP ou sinal externo de risco",
                    severity="critical" if sanctions else "high",
                    score=95 if sanctions else 78,
                    entity_id=customer_id,
                    entity_type="customer",
                    rationale="Cadastro possui flags externas/cadastrais que exigem diligência reforçada.",
                    evidence=[f"Flags: {', '.join(flags)}.", f"Movimentação relacionada: {_brl(_sum(txs))}."],
                    transactions=txs,
                    recommended_action="Executar enhanced due diligence e preservar evidência da fonte.",
                ),
            )


def _detect_crypto(transactions: list[dict[str, Any]], findings: list[dict[str, Any]], t: dict[str, Any]) -> None:
    for customer_id, txs in _by_customer(transactions).items():
        crypto_out = [
            tx
            for tx in txs
            if tx.get("direction") == "out"
            and (tx.get("rail") == "Crypto" or "crypto" in [str(tag).lower() for tag in tx.get("tags") or []])
        ]
        inbound = [tx for tx in txs if tx.get("direction") == "in"]
        crypto_total = _sum(crypto_out)
        inbound_total = _sum(inbound)
        if crypto_total >= float(t["cryptoAdjacencyMinAmount"]) and inbound_total >= crypto_total * float(t["cryptoAdjacencyInboundRatio"]):
            _add(
                findings,
                _finding(
                    rule_id="PLD-CRYPTO-009",
                    title="Adjacência cripto após entrada de recursos",
                    severity="high",
                    score=79,
                    entity_id=customer_id,
                    entity_type="customer",
                    rationale="Saída para trilha cripto/P2P após entradas recentes aumenta opacidade.",
                    evidence=[f"Saídas cripto/P2P: {_brl(crypto_total)}.", f"Entradas relacionadas: {_brl(inbound_total)}."],
                    transactions=[*crypto_out, *inbound],
                    recommended_action="Checar exchange/beneficiário, origem dos fundos e política interna cripto/P2P.",
                ),
            )


def _network(transactions: list[dict[str, Any]], findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    risk: dict[str, int] = defaultdict(int)
    tx_map = {str(tx.get("id")): tx for tx in transactions}
    for finding in findings:
        risk[str(finding["entityId"])] = max(risk[str(finding["entityId"])], int(finding["score"]))
        for tx_id in finding["transactionIds"]:
            tx = tx_map.get(str(tx_id))
            if not tx:
                continue
            for key in ("customerId", "accountId", "counterpartyId", "deviceId"):
                if tx.get(key):
                    risk[str(tx[key])] = max(risk[str(tx[key])], int(finding["score"]))
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    for tx in transactions:
        for node_id, label, kind in [
            (tx.get("customerId"), tx.get("customerId"), "customer"),
            (tx.get("accountId"), tx.get("accountId"), "account"),
            (tx.get("counterpartyId"), tx.get("counterpartyName") or tx.get("counterpartyId"), "counterparty"),
            (tx.get("deviceId"), tx.get("deviceId"), "device"),
        ]:
            if node_id:
                nodes[str(node_id)] = {"id": str(node_id), "label": str(label), "type": kind, "risk": risk[str(node_id)]}
        src = str(tx.get("counterpartyId") if tx.get("direction") == "in" else tx.get("accountId"))
        dst = str(tx.get("accountId") if tx.get("direction") == "in" else tx.get("counterpartyId"))
        key = f"{src}->{dst}:{tx.get('rail')}"
        if key not in edges:
            edges[key] = {"from": src, "to": dst, "label": str(tx.get("rail") or "Outro"), "amount": 0, "transactionIds": []}
        edges[key]["amount"] += _amount(tx)
        edges[key]["transactionIds"].append(str(tx.get("id")))
    return {
        "nodes": sorted(nodes.values(), key=lambda item: item["risk"], reverse=True)[:24],
        "edges": sorted(edges.values(), key=lambda item: item["amount"], reverse=True)[:32],
    }


def analyze_pld_ft(payload: dict[str, Any], saved_thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    transactions = sorted(payload.get("transactions") or [], key=_time)
    customers = _customers(payload)
    thresholds = _thresholds(payload, saved_thresholds)
    findings: list[dict[str, Any]] = []

    _detect_pass_through(transactions, findings, thresholds)
    _detect_fanout(transactions, findings, thresholds)
    _detect_multi_victim(transactions, findings, thresholds)
    _detect_kyc(transactions, customers, findings, thresholds)
    _detect_device_reuse(transactions, findings, thresholds)
    _detect_structuring(transactions, findings, thresholds)
    _detect_lists(transactions, customers, findings)
    _detect_crypto(transactions, findings, thresholds)

    findings.sort(key=lambda item: (item["score"], item["amountInScope"]), reverse=True)
    risk_score = min(100, round(sum(item["score"] * (0.45 if index == 0 else 0.12) for index, item in enumerate(findings))))
    finding_tx_ids = {tx_id for item in findings for tx_id in item["transactionIds"]}
    suspicious_amount = _sum([tx for tx in transactions if str(tx.get("id")) in finding_tx_ids])
    generated_at = payload.get("generatedAt") or datetime.utcnow().isoformat() + "Z"
    dossier_id = "PLD-" + hashlib.sha1((generated_at + payload_hash(payload)).encode("utf-8")).hexdigest()[:12].upper()

    if findings:
        top = "; ".join(item["title"] for item in findings[:3])
        summary = (
            f"O Quarry identificou {len(findings)} achado(s) compatíveis com risco PLD/FT em "
            f"{len(transactions)} transações. Score consolidado {risk_score}/100 ({_severity(risk_score)}), "
            f"com {_brl(suspicious_amount)} em escopo suspeito. Principais sinais: {top}."
        )
    else:
        summary = (
            "Nenhum padrão crítico foi identificado no conjunto analisado. O resultado não elimina risco; "
            "indica apenas que as regras determinísticas desta execução não encontraram sinal suficiente."
        )

    return {
        "id": dossier_id,
        "institution": payload.get("institution") or "Instituição financeira",
        "generatedAt": generated_at,
        "riskScore": risk_score,
        "severity": _severity(risk_score),
        "totalTransactions": len(transactions),
        "totalAmount": _sum(transactions),
        "suspiciousAmount": suspicious_amount,
        "findings": findings,
        "network": _network(transactions, findings),
        "executiveSummary": summary,
        "analystChecklist": [
            "Validar KYC, renda/faturamento e substância econômica das entidades com maior score.",
            "Conferir vínculo declarado entre cliente, favorecidos, dispositivos e contrapartes.",
            "Preservar evidências originais, timestamps, fontes e hashes antes de contato externo.",
            "Registrar decisão humana: falso positivo, monitoramento, bloqueio preventivo, escalado ou encerrado.",
            "Submeter casos críticos ao responsável PLD/FT e jurídico antes de qualquer comunicação externa.",
        ],
        "auditTrail": [
            "Entrada normalizada no schema Quarry PLD/FT Event v1.",
            "Regras determinísticas executadas sem LLM para cálculo de score.",
            "Achados classificados por severidade, valor em escopo e evidência transacional.",
            "Grafo de entidades criado a partir de cliente, conta, favorecido e dispositivo.",
            "Dossiê gerado com revisão humana obrigatória.",
        ],
        "disclaimer": (
            "Este dossiê não declara crime, culpa ou ilegalidade. Ele identifica padrões compatíveis "
            "com risco PLD/FT/fraude e organiza evidências para revisão humana, jurídica e regulatória."
        ),
    }
