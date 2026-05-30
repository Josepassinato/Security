from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.pld_ft import (
    AnalyzeRequest,
    SaveCaseRequest,
    _case_report_html,
    analyze,
    list_rules,
    save_case,
)


class _Result:
    def __init__(self, row=None) -> None:
        self._row = row

    def fetchone(self):
        return self._row


class _FakeDb:
    def __init__(self) -> None:
        self.executed = []
        self.committed = False

    async def execute(self, statement):
        sql = str(statement)
        self.executed.append(sql)
        if "FROM pld_ft_thresholds" in sql:
            return _Result(None)
        if "INSERT INTO pld_ft_imports" in sql:
            return _Result(SimpleNamespace(id=uuid.uuid4(), created_at=datetime.now(UTC)))
        return _Result(None)

    async def commit(self):
        self.committed = True


def _user() -> SimpleNamespace:
    return SimpleNamespace(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role="analyst",
        email="analyst@example.com",
    )


def _payload() -> AnalyzeRequest:
    return AnalyzeRequest(
        institution="Banco Teste",
        customers=[{"customerId": "C1", "declaredMonthlyIncome": 2000, "accountAgeDays": 5}],
        transactions=[
            {
                "id": "T1",
                "timestamp": "2026-05-30T10:00:00Z",
                "accountId": "A1",
                "customerId": "C1",
                "direction": "in",
                "rail": "Pix",
                "amount": 12000,
                "counterpartyId": "SRC",
            },
            {
                "id": "T2",
                "timestamp": "2026-05-30T10:20:00Z",
                "accountId": "A1",
                "customerId": "C1",
                "direction": "out",
                "rail": "Pix",
                "amount": 11000,
                "counterpartyId": "DST",
            },
        ],
    )


@pytest.mark.asyncio
async def test_list_rules_returns_deterministic_catalog():
    payload = await list_rules()
    assert payload["mode"] == "deterministic"
    assert len(payload["rules"]) >= 9
    assert "passThroughMinAmount" in payload["thresholds"]


@pytest.mark.asyncio
async def test_analyze_persists_import_and_returns_dossier():
    db = _FakeDb()
    response = await analyze(_payload(), db, _user())

    assert response["mode"] == "backend"
    assert response["transactionCount"] == 2
    assert response["dossier"]["findings"][0]["ruleId"] == "PLD-PIX-001"
    assert response["payloadHash"]
    assert db.committed is True
    assert any("INSERT INTO pld_ft_imports" in sql for sql in db.executed)


@pytest.mark.asyncio
async def test_save_case_requires_dossier_id():
    with pytest.raises(HTTPException) as exc:
        await save_case(SaveCaseRequest(dossier={}), _FakeDb(), _user())
    assert exc.value.status_code == 422
    assert "dossier.id" in exc.value.detail


def test_case_report_html_escapes_content_and_includes_decision():
    case = {
        "id": "case-1",
        "status": "em_revisao",
        "dossierId": "PLD-TEST",
        "dossier": {
            "id": "PLD-TEST",
            "institution": "<Banco>",
            "riskScore": 92,
            "severity": "critical",
            "totalAmount": 12000,
            "executiveSummary": "Resumo <script>",
            "findings": [
                {
                    "ruleId": "PLD-PIX-001",
                    "title": "Conta de passagem",
                    "rationale": "Entrada e saída rápida",
                    "entityType": "customer",
                    "entityId": "C1",
                    "score": 92,
                    "severity": "critical",
                    "amountInScope": 12000,
                    "transactionIds": ["T1", "T2"],
                    "evidence": ["Entrada relevante"],
                    "recommendedAction": "Revisar",
                }
            ],
            "analystChecklist": ["Validar KYC"],
            "auditTrail": ["Regras determinísticas executadas"],
            "disclaimer": "Não declara crime.",
        },
        "decisions": [{"status": "em_revisao", "analyst": "QA", "decidedAt": "2026-05-30", "note": "Ok"}],
    }

    html = _case_report_html(case)
    assert "&lt;Banco&gt;" in html
    assert "Resumo &lt;script&gt;" in html
    assert "PLD-PIX-001" in html
    assert "QA" in html
