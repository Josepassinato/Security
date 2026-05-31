"""Operational PLD/FT endpoints.

This surface persists the deterministic PLD/FT lab into Postgres so the
Brazilian fintech-compliance product can move from demo analysis to an
auditable workflow: import -> deterministic dossier -> case -> human decision.
"""

from __future__ import annotations

import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.api.v1.deps import AuthUser, DBSession
from app.services.pld_ft_engine import DEFAULT_THRESHOLDS, analyze_pld_ft, payload_hash

router = APIRouter(prefix="/pld-ft", tags=["pld-ft"])


RULE_CATALOG: list[dict[str, Any]] = [
    {
        "id": "PLD-PIX-001",
        "title": "Conta de passagem: entrada seguida de saída rápida",
        "type": "transactional",
        "severity": "critical",
        "input": "Transações Pix com direção, horário, valor e cliente.",
        "output": "Achado com transações de entrada/saída, valor em escopo e recomendação.",
    },
    {
        "id": "PLD-PIX-002",
        "title": "Fan-out Pix para múltiplos favorecidos",
        "type": "transactional",
        "severity": "high",
        "input": "Saídas Pix agrupadas por cliente e favorecido.",
        "output": "Quantidade de favorecidos, volume total e transações relacionadas.",
    },
    {
        "id": "PLD-PIX-003",
        "title": "Agregação de múltiplos remetentes e repasse posterior",
        "type": "network",
        "severity": "critical",
        "input": "Entradas e saídas por cliente, com remetentes distintos.",
        "output": "Sinal de centralização/dispersão com grafo de entidades.",
    },
    {
        "id": "PLD-KYC-004",
        "title": "Movimentação incompatível com perfil econômico declarado",
        "type": "kyc",
        "severity": "high",
        "input": "KYC de renda/faturamento declarado e volume transacional.",
        "output": "Múltiplo entre declarado e movimentado, com recomendação de diligência.",
    },
    {
        "id": "PLD-KYC-005",
        "title": "Conta nova com primeira saída relevante",
        "type": "kyc",
        "severity": "high",
        "input": "Idade da conta e primeiras saídas.",
        "output": "Sinal de risco de onboarding e necessidade de revisão reforçada.",
    },
    {
        "id": "PLD-DEV-006",
        "title": "Dispositivo reutilizado por múltiplas contas",
        "type": "device",
        "severity": "critical",
        "input": "Device ID por transação e cliente.",
        "output": "Cluster de contas ligadas ao mesmo dispositivo.",
    },
    {
        "id": "PLD-STR-007",
        "title": "Fracionamento recorrente abaixo de faixa sensível",
        "type": "transactional",
        "severity": "high",
        "input": "Sequência de transações por cliente e faixa de valor.",
        "output": "Contagem, volume agregado e transações fracionadas.",
    },
    {
        "id": "PLD-LIST-008",
        "title": "Exposição de cadastro a lista, PEP ou sinal externo de risco",
        "type": "screening",
        "severity": "critical",
        "input": "Flags cadastrais de sanções, PEP, mídia adversa e atividade de risco.",
        "output": "Achado de diligência reforçada com evidência cadastral.",
    },
    {
        "id": "PLD-CRYPTO-009",
        "title": "Adjacência cripto após entrada de recursos",
        "type": "network",
        "severity": "high",
        "input": "Entradas recentes e saídas para trilha cripto/P2P.",
        "output": "Volume cripto/P2P e entradas relacionadas.",
    },
]


class AnalyzeRequest(BaseModel):
    institution: str | None = None
    sourceType: str = Field(default="json", max_length=40)
    customers: list[dict[str, Any]] = Field(default_factory=list)
    transactions: list[dict[str, Any]] = Field(default_factory=list)
    thresholds: dict[str, Any] = Field(default_factory=dict)
    generatedAt: str | None = None


class SaveCaseRequest(BaseModel):
    dossier: dict[str, Any]
    importId: uuid.UUID | None = None
    status: str = Field(default="novo", max_length=40)


class DecisionRequest(BaseModel):
    status: str = Field(..., min_length=2, max_length=40)
    note: str = Field(default="", max_length=4000)
    analyst: str | None = Field(default=None, max_length=160)


class ThresholdsRequest(BaseModel):
    thresholds: dict[str, Any] = Field(default_factory=dict)


class RuleSimulationRequest(BaseModel):
    thresholds: dict[str, Any] = Field(default_factory=dict)
    payload: AnalyzeRequest | None = None


class RuleVersionRequest(BaseModel):
    versionName: str = Field(..., min_length=2, max_length=120)
    thresholds: dict[str, Any] = Field(default_factory=dict)
    rationale: str = Field(default="", max_length=4000)


class RuleVersionDecisionRequest(BaseModel):
    note: str = Field(default="", max_length=2000)


class WorkflowRequest(BaseModel):
    assignee: str | None = Field(default=None, max_length=160)
    priority: str | None = Field(default=None, max_length=40)
    slaDueAt: str | None = None
    status: str | None = Field(default=None, max_length=40)
    note: str | None = Field(default=None, max_length=2000)


class CommentRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=4000)
    author: str | None = Field(default=None, max_length=160)


class AttachmentRequest(BaseModel):
    fileName: str = Field(..., min_length=1, max_length=240)
    contentType: str = Field(default="", max_length=120)
    fileSize: int = Field(default=0, ge=0)
    description: str = Field(default="", max_length=1000)
    storageUrl: str = Field(default="", max_length=1000)


class IngestionJobRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    sourceType: str = Field(default="api", max_length=40)
    intervalSeconds: int = Field(default=300, ge=30, le=86400)
    autoCaseMinScore: int = Field(default=65, ge=0, le=100)
    config: dict[str, Any] = Field(default_factory=dict)


class StreamIngestionRequest(AnalyzeRequest):
    autoCaseMinScore: int = Field(default=65, ge=0, le=100)
    openCase: bool = True


class RegulatoryExportRequest(BaseModel):
    exportType: str = Field(default="coaf_internal", max_length=80)
    approvalNote: str = Field(default="", max_length=4000)


def _row_value(row: Any, key: str, default: Any = None) -> Any:
    try:
        return getattr(row, key)
    except AttributeError:
        try:
            return row._mapping.get(key, default)
        except AttributeError:
            return default


def _row_to_case(row: Any, decisions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    dossier = dict(_row_value(row, "dossier", {}) or {})
    return {
        "id": str(_row_value(row, "id")),
        "status": _row_value(row, "status"),
        "importId": str(_row_value(row, "import_id")) if _row_value(row, "import_id") else None,
        "dossier": dossier,
        "dossierId": _row_value(row, "dossier_id"),
        "institution": _row_value(row, "institution"),
        "riskScore": _row_value(row, "risk_score"),
        "severity": _row_value(row, "severity"),
        "assignee": _row_value(row, "assignee"),
        "priority": _row_value(row, "priority", "normal"),
        "slaDueAt": _row_value(row, "sla_due_at").isoformat() if _row_value(row, "sla_due_at") else None,
        "closedAt": _row_value(row, "closed_at").isoformat() if _row_value(row, "closed_at") else None,
        "reopenedAt": _row_value(row, "reopened_at").isoformat() if _row_value(row, "reopened_at") else None,
        "workflow": _row_value(row, "workflow", {}) or {},
        "createdAt": _row_value(row, "created_at").isoformat() if _row_value(row, "created_at") else None,
        "updatedAt": _row_value(row, "updated_at").isoformat() if _row_value(row, "updated_at") else None,
        "decisions": decisions or [],
    }


def _brl(value: Any) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _html_escape(value: Any) -> str:
    return (
        str(value if value is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


PLD_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "read": {"admin", "analyst", "soc_analyst", "compliance_officer", "pld_compliance_officer", "auditor", "viewer"},
    "write": {"admin", "analyst", "soc_analyst", "compliance_officer", "pld_compliance_officer"},
    "approve": {"admin", "compliance_officer", "pld_compliance_officer"},
    "audit": {"admin", "compliance_officer", "pld_compliance_officer", "auditor"},
}


def _require_pld_role(user: AuthUser, permission: str) -> None:
    allowed = PLD_ROLE_PERMISSIONS.get(permission, set())
    role = str(getattr(user, "role", "") or "").lower()
    if role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"PLD/FT role denied: {permission}",
        )


def _canonical_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def _emit_pld_audit(
    db: DBSession,
    user: AuthUser,
    *,
    action: str,
    resource: str,
    resource_id: str = "",
    details: dict[str, Any] | None = None,
) -> None:
    prev = (
        await db.execute(
            text(
                """
                SELECT entry_hash
                FROM pld_ft_audit_log
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """
            ).bindparams(tenant_id=user.tenant_id)
        )
    ).fetchone()
    payload = {
        "tenant_id": str(user.tenant_id),
        "actor_id": str(user.user_id),
        "actor_email": user.email,
        "actor_role": getattr(user, "role", ""),
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "details": details or {},
        "prev_hash": prev.entry_hash if prev else None,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    entry_hash = _canonical_hash(payload)
    await db.execute(
        text(
            """
            INSERT INTO pld_ft_audit_log (
                tenant_id, actor_id, actor_email, actor_role, action, resource,
                resource_id, details, prev_hash, entry_hash, created_at
            )
            VALUES (
                :tenant_id, :actor_id, :actor_email, :actor_role, :action, :resource,
                :resource_id, CAST(:details AS jsonb), :prev_hash, :entry_hash, CAST(:created_at AS timestamptz)
            )
            """
        ).bindparams(
            tenant_id=user.tenant_id,
            actor_id=user.user_id,
            actor_email=user.email,
            actor_role=getattr(user, "role", ""),
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=json.dumps(details or {}, ensure_ascii=False),
            prev_hash=payload["prev_hash"],
            entry_hash=entry_hash,
            created_at=payload["created_at"],
        )
    )


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _month_window(month: str | None) -> tuple[datetime, datetime, str]:
    if month:
        try:
            start = datetime.strptime(month, "%Y-%m")
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="month must be YYYY-MM") from exc
    else:
        now = datetime.utcnow()
        start = datetime(now.year, now.month, 1)
    if start.month == 12:
        end = datetime(start.year + 1, 1, 1)
    else:
        end = datetime(start.year, start.month + 1, 1)
    return start, end, start.strftime("%Y-%m")


def _row_to_ingestion_job(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "name": row.name,
        "sourceType": row.source_type,
        "status": row.status,
        "intervalSeconds": row.interval_seconds,
        "autoCaseMinScore": row.auto_case_min_score,
        "config": row.config or {},
        "lastRunAt": row.last_run_at.isoformat() if row.last_run_at else None,
        "nextRunAt": row.next_run_at.isoformat() if row.next_run_at else None,
        "lastResult": row.last_result or {},
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
    }


def _row_to_regulatory_export(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "caseId": str(row.case_id),
        "exportType": row.export_type,
        "status": row.status,
        "structuredPayload": row.structured_payload or {},
        "approvalNote": row.approval_note,
        "approvedAt": row.approved_at.isoformat() if row.approved_at else None,
        "exportedAt": row.exported_at.isoformat() if row.exported_at else None,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
    }


def _regulatory_payload_from_case(case: dict[str, Any], export_type: str) -> dict[str, Any]:
    dossier = case.get("dossier") or {}
    findings = dossier.get("findings") or []
    transactions: set[str] = set()
    entities: set[str] = set()
    for finding in findings:
        entities.add(str(finding.get("entityId") or ""))
        for tx_id in finding.get("transactionIds") or []:
            transactions.add(str(tx_id))
    return {
        "schema": "quarry.pld_ft.regulatory_export.v1",
        "exportType": export_type,
        "humanApprovalRequired": True,
        "approvalStatus": "pending_approval",
        "caseId": case.get("id"),
        "dossierId": case.get("dossierId"),
        "institution": case.get("institution") or dossier.get("institution"),
        "status": case.get("status"),
        "riskScore": case.get("riskScore"),
        "severity": case.get("severity"),
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "summary": dossier.get("executiveSummary"),
        "totalAmount": dossier.get("totalAmount"),
        "suspiciousAmount": dossier.get("suspiciousAmount"),
        "involvedEntities": sorted(entity for entity in entities if entity),
        "transactionIds": sorted(transactions),
        "findings": [
            {
                "ruleId": finding.get("ruleId"),
                "title": finding.get("title"),
                "score": finding.get("score"),
                "severity": finding.get("severity"),
                "entityType": finding.get("entityType"),
                "entityId": finding.get("entityId"),
                "amountInScope": finding.get("amountInScope"),
                "evidence": finding.get("evidence") or [],
                "recommendedAction": finding.get("recommendedAction"),
            }
            for finding in findings
        ],
        "humanDecisions": case.get("decisions") or [],
        "guardrails": [
            "Exportacao estruturada nao e enviada automaticamente ao regulador.",
            "Compliance officer deve aprovar o conteudo antes do uso externo.",
            "O arquivo preserva evidencias, hipoteses e limites de interpretacao; nao declara crime ou culpa.",
        ],
    }


async def _persist_analysis(
    payload: AnalyzeRequest,
    db: DBSession,
    user: AuthUser,
    *,
    source_type: str | None = None,
    open_case: bool = False,
    auto_case_min_score: int = 65,
    audit_action: str | None = None,
    audit_resource_id: str = "",
) -> dict[str, Any]:
    body = payload.model_dump()
    if source_type:
        body["sourceType"] = source_type
    saved = await _saved_thresholds(db, user)
    dossier = analyze_pld_ft(body, saved_thresholds=saved)
    p_hash = payload_hash(body)
    tx_count = len(body.get("transactions") or [])

    import_row = (
        await db.execute(
            text(
                """
                INSERT INTO pld_ft_imports (
                    tenant_id, user_id, institution, source_type, payload_hash,
                    transaction_count, dossier, risk_score, severity
                )
                VALUES (
                    :tenant_id, :user_id, :institution, :source_type, :payload_hash,
                    :transaction_count, CAST(:dossier AS jsonb), :risk_score, :severity
                )
                RETURNING id, created_at
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                institution=dossier.get("institution"),
                source_type=body.get("sourceType") or payload.sourceType,
                payload_hash=p_hash,
                transaction_count=tx_count,
                dossier=json.dumps(dossier, ensure_ascii=False),
                risk_score=dossier.get("riskScore"),
                severity=dossier.get("severity"),
            )
        )
    ).fetchone()

    created_case: dict[str, Any] | None = None
    if open_case and int(dossier.get("riskScore") or 0) >= auto_case_min_score:
        dossier_id = str(dossier.get("id") or "")
        case_row = (
            await db.execute(
                text(
                    """
                    INSERT INTO pld_ft_cases (
                        tenant_id, import_id, dossier_id, status, institution,
                        risk_score, severity, dossier, created_by, updated_at
                    )
                    VALUES (
                        :tenant_id, :import_id, :dossier_id, 'novo', :institution,
                        :risk_score, :severity, CAST(:dossier AS jsonb), :user_id, now()
                    )
                    ON CONFLICT (tenant_id, dossier_id)
                    DO UPDATE SET
                        import_id = COALESCE(EXCLUDED.import_id, pld_ft_cases.import_id),
                        institution = EXCLUDED.institution,
                        risk_score = EXCLUDED.risk_score,
                        severity = EXCLUDED.severity,
                        dossier = EXCLUDED.dossier,
                        updated_at = now()
                    RETURNING *
                    """
                ).bindparams(
                    tenant_id=user.tenant_id,
                    import_id=import_row.id,
                    dossier_id=dossier_id,
                    institution=dossier.get("institution"),
                    risk_score=dossier.get("riskScore"),
                    severity=dossier.get("severity"),
                    dossier=json.dumps(dossier, ensure_ascii=False),
                    user_id=user.user_id,
                )
            )
        ).fetchone()
        await db.execute(
            text(
                """
                UPDATE pld_ft_imports
                SET case_ids = (
                    SELECT jsonb_agg(DISTINCT value)
                    FROM jsonb_array_elements(case_ids || jsonb_build_array(:case_id_text)) AS value
                )
                WHERE tenant_id = :tenant_id AND id = :import_id
                """
            ).bindparams(tenant_id=user.tenant_id, import_id=import_row.id, case_id_text=str(case_row.id))
        )
        created_case = _row_to_case(case_row, [])

    if audit_action:
        await _emit_pld_audit(
            db,
            user,
            action=audit_action,
            resource="pld_ft_import",
            resource_id=audit_resource_id or str(import_row.id),
            details={
                "importId": str(import_row.id),
                "payloadHash": p_hash,
                "transactionCount": tx_count,
                "riskScore": dossier.get("riskScore"),
                "severity": dossier.get("severity"),
                "createdCaseId": created_case.get("id") if created_case else None,
            },
        )

    await db.commit()
    if created_case:
        await _recompute_customer_risk(db, user)

    return {
        "mode": "backend",
        "importId": str(import_row.id),
        "createdAt": import_row.created_at.isoformat() if import_row.created_at else datetime.utcnow().isoformat(),
        "payloadHash": p_hash,
        "transactionCount": tx_count,
        "dossier": dossier,
        "createdCase": created_case,
    }


def _case_report_html(case: dict[str, Any]) -> str:
    dossier = case["dossier"]
    decisions = case.get("decisions") or []
    findings = dossier.get("findings") or []
    ai_analyst = dossier.get("aiAnalyst") or {}
    narrative = ai_analyst.get("caseNarrative") or {}
    hypotheses = ai_analyst.get("hypotheses") or []
    critic = ai_analyst.get("critic") or {}
    coaf = ai_analyst.get("coafDraft") or {}
    checklist = dossier.get("analystChecklist") or []
    audit = dossier.get("auditTrail") or []
    generated_at = datetime.utcnow().isoformat() + "Z"

    findings_html = "".join(
        f"""
        <article class="card">
          <p class="eyebrow">{_html_escape(finding.get("ruleId"))}</p>
          <h3>{_html_escape(finding.get("title"))}</h3>
          <p>{_html_escape(finding.get("rationale"))}</p>
          <p><strong>Entidade:</strong> {_html_escape(finding.get("entityType"))} {_html_escape(finding.get("entityId"))}</p>
          <p><strong>Score:</strong> {_html_escape(finding.get("score"))}/100 · <strong>Severidade:</strong> {_html_escape(finding.get("severity"))}</p>
          <p><strong>Valor em escopo:</strong> {_brl(finding.get("amountInScope"))}</p>
          <p><strong>Transações:</strong> {_html_escape(", ".join(finding.get("transactionIds") or []))}</p>
          <ul>{"".join(f"<li>{_html_escape(item)}</li>" for item in finding.get("evidence") or [])}</ul>
          <p class="action"><strong>Ação recomendada:</strong> {_html_escape(finding.get("recommendedAction"))}</p>
        </article>
        """
        for finding in findings
    )
    decisions_html = (
        "".join(
            f"""
            <article class="card">
              <p><strong>{_html_escape(decision.get("status"))}</strong> por {_html_escape(decision.get("analyst"))}</p>
              <p class="muted">{_html_escape(decision.get("decidedAt"))}</p>
              <p>{_html_escape(decision.get("note") or "Sem nota.")}</p>
            </article>
            """
            for decision in decisions
        )
        or "<p class='muted'>Nenhuma decisão humana registrada.</p>"
    )
    hypotheses_html = (
        "".join(
            f"""
            <article class="card">
              <p class="eyebrow">Hipótese · confiança {_html_escape(item.get("confidence"))}</p>
              <h3>{_html_escape(item.get("title"))}</h3>
              <p>{_html_escape(item.get("basis"))}</p>
              <p><strong>Contraponto:</strong> {_html_escape(item.get("alternateExplanation"))}</p>
              <p><strong>Evidências:</strong> {_html_escape(", ".join(item.get("evidenceIds") or []))}</p>
              <ul>{"".join(f"<li>{_html_escape(step)}</li>" for step in item.get("nextSteps") or [])}</ul>
            </article>
            """
            for item in hypotheses
        )
        or "<p class='muted'>Nenhuma hipótese prioritária disponível.</p>"
    )
    return f"""
    <!doctype html>
    <html lang="pt-BR">
      <head>
        <meta charset="utf-8" />
        <title>Relatório PLD/FT {_html_escape(case.get("id"))}</title>
        <style>
          @page {{ size: A4; margin: 22mm 18mm; }}
          body {{ font-family: Inter, Arial, sans-serif; color: #111827; line-height: 1.55; }}
          h1 {{ font-size: 26px; margin: 0 0 6px; }}
          h2 {{ font-size: 18px; margin: 26px 0 10px; border-bottom: 1px solid #d1d5db; padding-bottom: 6px; }}
          h3 {{ font-size: 15px; margin: 4px 0 8px; }}
          .muted {{ color: #4b5563; font-size: 12px; }}
          .eyebrow {{ color: #1d4ed8; font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
          .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 18px 0; }}
          .kpi, .card {{ border: 1px solid #d1d5db; border-radius: 10px; padding: 12px; break-inside: avoid; }}
          .kpi strong {{ display: block; font-size: 12px; color: #4b5563; }}
          .kpi span {{ display: block; font-size: 17px; font-weight: 800; margin-top: 5px; }}
          .action {{ background: #eff6ff; border-left: 4px solid #2563eb; padding: 8px; }}
          li {{ margin-bottom: 4px; }}
          footer {{ margin-top: 26px; border-top: 1px solid #d1d5db; padding-top: 10px; }}
        </style>
      </head>
      <body>
        <p class="muted">Quarry PLD/FT · Relatório oficial para revisão humana · gerado em {_html_escape(generated_at)}</p>
        <h1>Relatório PLD/FT - {_html_escape(dossier.get("id"))}</h1>
        <p><strong>Instituição:</strong> {_html_escape(dossier.get("institution"))}</p>
        <p><strong>Status operacional:</strong> {_html_escape(case.get("status"))}</p>
        <p>{_html_escape(dossier.get("executiveSummary"))}</p>

        <div class="kpis">
          <div class="kpi"><strong>Score</strong><span>{_html_escape(dossier.get("riskScore"))}/100</span></div>
          <div class="kpi"><strong>Severidade</strong><span>{_html_escape(dossier.get("severity"))}</span></div>
          <div class="kpi"><strong>Volume total</strong><span>{_brl(dossier.get("totalAmount"))}</span></div>
          <div class="kpi"><strong>Achados</strong><span>{len(findings)}</span></div>
        </div>

        <h2>Achados explicáveis</h2>
        {findings_html or "<p class='muted'>Nenhum achado registrado.</p>"}

        <h2>Analista IA auditável</h2>
        <article class="card">
          <p>{_html_escape(narrative.get("summary"))}</p>
          <p class="action"><strong>Recomendação operacional:</strong> {_html_escape(narrative.get("recommendedDecision"))}</p>
          <p><strong>Preparar minuta COAF:</strong> {_html_escape("sim" if coaf.get("shouldPrepare") else "não")} · {_html_escape(coaf.get("rationale"))}</p>
        </article>
        {hypotheses_html}

        <h2>Crítico de evidências</h2>
        <article class="card">
          <p><strong>Veredito:</strong> {_html_escape(critic.get("verdict"))}</p>
          <p><strong>Lacunas:</strong></p>
          <ul>{"".join(f"<li>{_html_escape(item)}</li>" for item in critic.get("gaps") or [])}</ul>
          <p><strong>Afirmações bloqueadas:</strong></p>
          <ul>{"".join(f"<li>{_html_escape(item)}</li>" for item in critic.get("unsupportedClaims") or [])}</ul>
        </article>

        <h2>Decisões humanas</h2>
        {decisions_html}

        <h2>Checklist do analista</h2>
        <ul>{"".join(f"<li>{_html_escape(item)}</li>" for item in checklist)}</ul>

        <h2>Trilha de auditoria</h2>
        <ol>{"".join(f"<li>{_html_escape(item)}</li>" for item in audit)}</ol>

        <footer>
          <p><strong>Observação legal:</strong> {_html_escape(dossier.get("disclaimer"))}</p>
          <p class="muted">Este relatório preserva critérios determinísticos, evidências e decisão humana. Ele não declara crime, culpa ou ilegalidade.</p>
        </footer>
      </body>
    </html>
    """


def _executive_report_html(report: dict[str, Any]) -> str:
    kpis = report.get("kpis") or {}
    top_customers = report.get("topCustomers") or []
    top_rules = report.get("topRules") or []
    return f"""
    <!doctype html>
    <html lang="pt-BR">
      <head>
        <meta charset="utf-8" />
        <title>Relatório Executivo PLD/FT</title>
        <style>
          @page {{ size: A4; margin: 20mm 18mm; }}
          body {{ font-family: Inter, Arial, sans-serif; color: #111827; line-height: 1.55; }}
          h1 {{ font-size: 26px; margin: 0 0 8px; }}
          h2 {{ margin-top: 24px; font-size: 18px; border-bottom: 1px solid #d1d5db; padding-bottom: 6px; }}
          .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
          .card {{ border: 1px solid #d1d5db; border-radius: 10px; padding: 12px; break-inside: avoid; }}
          .muted {{ color: #4b5563; font-size: 12px; }}
          table {{ width: 100%; border-collapse: collapse; }}
          td, th {{ border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; font-size: 12px; }}
        </style>
      </head>
      <body>
        <p class="muted">Quarry PLD/FT · Comitê de PLD/FT · {_html_escape(report.get("generatedAt"))}</p>
        <h1>Relatório Executivo PLD/FT</h1>
        <p>{_html_escape(report.get("executiveSummary"))}</p>
        <div class="grid">
          <div class="card"><strong>Casos</strong><br />{_html_escape(kpis.get("totalCases"))}</div>
          <div class="card"><strong>Abertos</strong><br />{_html_escape(kpis.get("openCases"))}</div>
          <div class="card"><strong>Críticos</strong><br />{_html_escape(kpis.get("criticalCases"))}</div>
          <div class="card"><strong>SLA vencido</strong><br />{_html_escape(kpis.get("overdueCases"))}</div>
        </div>
        <h2>Clientes de maior risco contínuo</h2>
        <table>
          <tr><th>Cliente</th><th>Score</th><th>Severidade</th><th>Casos</th><th>Volume</th></tr>
          {"".join(f"<tr><td>{_html_escape(item.get('customerId'))}</td><td>{_html_escape(item.get('riskScore'))}</td><td>{_html_escape(item.get('severity'))}</td><td>{_html_escape(item.get('totalCases'))}</td><td>{_brl(item.get('totalAmount'))}</td></tr>" for item in top_customers)}
        </table>
        <h2>Regras mais acionadas</h2>
        <table>
          <tr><th>Regra</th><th>Ocorrências</th></tr>
          {"".join(f"<tr><td>{_html_escape(item.get('ruleId'))}</td><td>{_html_escape(item.get('count'))}</td></tr>" for item in top_rules)}
        </table>
        <h2>Recomendações para diretoria/comitê</h2>
        <ul>{"".join(f"<li>{_html_escape(item)}</li>" for item in report.get("committeeRecommendations") or [])}</ul>
      </body>
    </html>
    """


async def _saved_thresholds(db: DBSession, user: AuthUser) -> dict[str, Any]:
    row = (
        await db.execute(
            text("SELECT thresholds FROM pld_ft_thresholds WHERE tenant_id = :tenant_id").bindparams(
                tenant_id=user.tenant_id
            )
        )
    ).fetchone()
    return dict(row.thresholds or {}) if row else {}


async def _case_decisions(db: DBSession, user: AuthUser, case_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                """
                SELECT id, status, note, analyst, decided_at
                FROM pld_ft_case_decisions
                WHERE tenant_id = :tenant_id AND case_id = :case_id
                ORDER BY decided_at DESC
                """
            ).bindparams(tenant_id=user.tenant_id, case_id=case_id)
        )
    ).fetchall()
    return [
        {
            "id": str(row.id),
            "status": row.status,
            "note": row.note,
            "analyst": row.analyst,
            "decidedAt": row.decided_at.isoformat() if row.decided_at else None,
        }
        for row in rows
    ]


async def _get_case_or_404(case_id: uuid.UUID, db: DBSession, user: AuthUser) -> dict[str, Any]:
    row = (
        await db.execute(
            text("SELECT * FROM pld_ft_cases WHERE tenant_id = :tenant_id AND id = :id").bindparams(
                tenant_id=user.tenant_id,
                id=case_id,
            )
        )
    ).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PLD/FT case not found")
    decisions = await _case_decisions(db, user, case_id)
    return _row_to_case(row, decisions)


def _case_customer_ids(case: dict[str, Any]) -> set[str]:
    dossier = case.get("dossier") or {}
    ids = {
        str(item.get("entityId"))
        for item in dossier.get("findings") or []
        if item.get("entityId") and item.get("entityType") == "customer"
    }
    for node in (dossier.get("network") or {}).get("nodes") or []:
        if node.get("type") == "customer" and node.get("id"):
            ids.add(str(node["id"]))
    return ids


def _risk_severity(score: int) -> str:
    if score >= 85:
        return "critical"
    if score >= 65:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


async def _recompute_customer_risk(db: DBSession, user: AuthUser) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                """
                SELECT *
                FROM pld_ft_cases
                WHERE tenant_id = :tenant_id
                ORDER BY updated_at DESC, created_at DESC
                """
            ).bindparams(tenant_id=user.tenant_id)
        )
    ).fetchall()
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        case = _row_to_case(row, [])
        for customer_id in _case_customer_ids(case):
            item = grouped.setdefault(
                customer_id,
                {
                    "customerId": customer_id,
                    "riskScore": 0,
                    "totalCases": 0,
                    "openCases": 0,
                    "escalatedCases": 0,
                    "falsePositiveCases": 0,
                    "totalAmount": 0.0,
                    "rules": {},
                    "evidence": [],
                    "lastCaseAt": None,
                },
            )
            status_value = str(case.get("status") or "")
            case_score = int(case.get("riskScore") or 0)
            if status_value == "falso_positivo":
                case_score = max(0, round(case_score * 0.25))
                item["falsePositiveCases"] += 1
            elif status_value == "escalado":
                case_score = min(100, case_score + 8)
                item["escalatedCases"] += 1
            if status_value not in {"encerrado", "falso_positivo"}:
                item["openCases"] += 1
            item["riskScore"] = max(int(item["riskScore"]), case_score)
            item["totalCases"] += 1
            item["totalAmount"] += float((case.get("dossier") or {}).get("suspiciousAmount") or 0)
            item["lastCaseAt"] = item["lastCaseAt"] or case.get("updatedAt") or case.get("createdAt")
            for finding in (case.get("dossier") or {}).get("findings") or []:
                rule_id = str(finding.get("ruleId") or "unknown")
                item["rules"][rule_id] = int(item["rules"].get(rule_id, 0)) + 1
            item["evidence"].append(
                {
                    "caseId": case["id"],
                    "dossierId": case.get("dossierId"),
                    "status": status_value,
                    "riskScore": case.get("riskScore"),
                    "severity": case.get("severity"),
                }
            )

    result: list[dict[str, Any]] = []
    await db.execute(text("DELETE FROM pld_ft_customer_risk WHERE tenant_id = :tenant_id").bindparams(tenant_id=user.tenant_id))
    for item in grouped.values():
        top_rules = [
            {"ruleId": rule, "count": count}
            for rule, count in sorted(item["rules"].items(), key=lambda pair: pair[1], reverse=True)[:6]
        ]
        score = min(100, int(item["riskScore"]) + min(10, max(0, int(item["openCases"]) - 1) * 3))
        severity = _risk_severity(score)
        await db.execute(
            text(
                """
                INSERT INTO pld_ft_customer_risk (
                    tenant_id, customer_id, risk_score, severity, total_cases, open_cases,
                    escalated_cases, false_positive_cases, total_amount, top_rules, evidence,
                    last_case_at, updated_at
                )
                VALUES (
                    :tenant_id, :customer_id, :risk_score, :severity, :total_cases, :open_cases,
                    :escalated_cases, :false_positive_cases, :total_amount, CAST(:top_rules AS jsonb),
                    CAST(:evidence AS jsonb), CAST(:last_case_at AS timestamptz), now()
                )
                ON CONFLICT (tenant_id, customer_id)
                DO UPDATE SET
                    risk_score = EXCLUDED.risk_score,
                    severity = EXCLUDED.severity,
                    total_cases = EXCLUDED.total_cases,
                    open_cases = EXCLUDED.open_cases,
                    escalated_cases = EXCLUDED.escalated_cases,
                    false_positive_cases = EXCLUDED.false_positive_cases,
                    total_amount = EXCLUDED.total_amount,
                    top_rules = EXCLUDED.top_rules,
                    evidence = EXCLUDED.evidence,
                    last_case_at = EXCLUDED.last_case_at,
                    updated_at = now()
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                customer_id=item["customerId"],
                risk_score=score,
                severity=severity,
                total_cases=item["totalCases"],
                open_cases=item["openCases"],
                escalated_cases=item["escalatedCases"],
                false_positive_cases=item["falsePositiveCases"],
                total_amount=item["totalAmount"],
                top_rules=json.dumps(top_rules, ensure_ascii=False),
                evidence=json.dumps(item["evidence"][:10], ensure_ascii=False),
                last_case_at=item["lastCaseAt"],
            )
        )
        result.append(
            {
                **{key: value for key, value in item.items() if key not in {"rules"}},
                "riskScore": score,
                "severity": severity,
                "topRules": top_rules,
            }
        )
    await db.commit()
    return sorted(result, key=lambda item: item["riskScore"], reverse=True)


async def _case_comments(db: DBSession, user: AuthUser, case_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                """
                SELECT id, body, author, created_at
                FROM pld_ft_case_comments
                WHERE tenant_id = :tenant_id AND case_id = :case_id
                ORDER BY created_at DESC
                """
            ).bindparams(tenant_id=user.tenant_id, case_id=case_id)
        )
    ).fetchall()
    return [
        {
            "id": str(row.id),
            "body": row.body,
            "author": row.author,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


async def _case_attachments(db: DBSession, user: AuthUser, case_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            text(
                """
                SELECT id, file_name, content_type, file_size, description, storage_url, created_at
                FROM pld_ft_case_attachments
                WHERE tenant_id = :tenant_id AND case_id = :case_id
                ORDER BY created_at DESC
                """
            ).bindparams(tenant_id=user.tenant_id, case_id=case_id)
        )
    ).fetchall()
    return [
        {
            "id": str(row.id),
            "fileName": row.file_name,
            "contentType": row.content_type,
            "fileSize": row.file_size,
            "description": row.description,
            "storageUrl": row.storage_url,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


def _rules_from_case(case: dict[str, Any]) -> set[str]:
    dossier = case.get("dossier") or {}
    return {str(item.get("ruleId")) for item in dossier.get("findings") or [] if item.get("ruleId")}


def _entities_from_case(case: dict[str, Any]) -> set[str]:
    dossier = case.get("dossier") or {}
    return {str(item.get("entityId")) for item in dossier.get("findings") or [] if item.get("entityId")}


async def _decision_memory(db: DBSession, user: AuthUser, case: dict[str, Any]) -> list[dict[str, Any]]:
    current_rules = _rules_from_case(case)
    current_entities = _entities_from_case(case)
    rows = (
        await db.execute(
            text(
                """
                SELECT *
                FROM pld_ft_cases
                WHERE tenant_id = :tenant_id AND id <> :id
                ORDER BY updated_at DESC, created_at DESC
                LIMIT 80
                """
            ).bindparams(tenant_id=user.tenant_id, id=uuid.UUID(case["id"]))
        )
    ).fetchall()
    memories: list[dict[str, Any]] = []
    for row in rows:
        candidate = _row_to_case(row, await _case_decisions(db, user, row.id))
        candidate_rules = _rules_from_case(candidate)
        candidate_entities = _entities_from_case(candidate)
        rule_overlap = sorted(current_rules & candidate_rules)
        entity_overlap = sorted(current_entities & candidate_entities)
        severity_match = candidate.get("severity") == case.get("severity")
        score = (len(rule_overlap) * 35) + (len(entity_overlap) * 20) + (15 if severity_match else 0)
        if score <= 0:
            continue
        memories.append(
            {
                "caseId": candidate["id"],
                "dossierId": candidate["dossierId"],
                "status": candidate["status"],
                "riskScore": candidate["riskScore"],
                "severity": candidate["severity"],
                "similarityScore": min(100, score),
                "overlapRules": rule_overlap,
                "overlapEntities": entity_overlap,
                "lastDecision": (candidate.get("decisions") or [{}])[0],
            }
        )
    return sorted(memories, key=lambda item: item["similarityScore"], reverse=True)[:8]


@router.get("/rules")
async def list_rules() -> dict[str, Any]:
    return {
        "rules": RULE_CATALOG,
        "thresholds": DEFAULT_THRESHOLDS,
        "mode": "deterministic",
    }


@router.get("/thresholds")
async def get_thresholds(db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "read")
    saved = await _saved_thresholds(db, user)
    return {"thresholds": {**DEFAULT_THRESHOLDS, **saved}, "defaults": DEFAULT_THRESHOLDS}


@router.put("/thresholds")
async def save_thresholds(payload: ThresholdsRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "approve")
    await db.execute(
        text(
            """
            INSERT INTO pld_ft_thresholds (tenant_id, thresholds, updated_by, updated_at)
            VALUES (:tenant_id, CAST(:thresholds AS jsonb), :user_id, now())
            ON CONFLICT (tenant_id)
            DO UPDATE SET thresholds = EXCLUDED.thresholds, updated_by = EXCLUDED.updated_by, updated_at = now()
            """
        ).bindparams(
            tenant_id=user.tenant_id,
            thresholds=json.dumps(payload.thresholds, ensure_ascii=False),
            user_id=user.user_id,
        )
    )
    await _emit_pld_audit(
        db,
        user,
        action="thresholds.updated",
        resource="pld_ft_thresholds",
        details={"keys": sorted(payload.thresholds.keys())},
    )
    await db.commit()
    return {"thresholds": {**DEFAULT_THRESHOLDS, **payload.thresholds}, "saved": True}


@router.post("/rule-simulations")
async def simulate_rules(payload: RuleSimulationRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "read")
    saved = await _saved_thresholds(db, user)
    proposed = {**saved, **payload.thresholds}
    if payload.payload:
        body = payload.payload.model_dump()
        baseline = analyze_pld_ft(body, saved_thresholds=saved)
        simulated = analyze_pld_ft(body, saved_thresholds=proposed)
        baseline_rules = {item["ruleId"] for item in baseline.get("findings") or []}
        simulated_rules = {item["ruleId"] for item in simulated.get("findings") or []}
        return {
            "mode": "payload",
            "baseline": {
                "riskScore": baseline["riskScore"],
                "severity": baseline["severity"],
                "findingCount": len(baseline.get("findings") or []),
                "rules": sorted(baseline_rules),
            },
            "simulated": {
                "riskScore": simulated["riskScore"],
                "severity": simulated["severity"],
                "findingCount": len(simulated.get("findings") or []),
                "rules": sorted(simulated_rules),
            },
            "delta": {
                "riskScore": int(simulated["riskScore"]) - int(baseline["riskScore"]),
                "findingCount": len(simulated.get("findings") or []) - len(baseline.get("findings") or []),
                "addedRules": sorted(simulated_rules - baseline_rules),
                "removedRules": sorted(baseline_rules - simulated_rules),
            },
            "recommendation": (
                "Mudança reduz alertas neste lote; validar se não remove tipologias críticas."
                if len(simulated.get("findings") or []) < len(baseline.get("findings") or [])
                else "Mudança aumenta sensibilidade; monitorar falso positivo antes de aprovar."
            ),
        }

    rows = (
        await db.execute(
            text(
                """
                SELECT status, risk_score, severity
                FROM pld_ft_cases
                WHERE tenant_id = :tenant_id
                """
            ).bindparams(tenant_id=user.tenant_id)
        )
    ).fetchall()
    strictness_delta = 0.0
    for key, value in payload.thresholds.items():
        default_value = float(DEFAULT_THRESHOLDS.get(key, saved.get(key, value)) or 1)
        try:
            strictness_delta += (float(value) - default_value) / max(default_value, 1)
        except (TypeError, ValueError):
            continue
    false_positive_count = sum(1 for row in rows if row.status == "falso_positivo")
    open_count = sum(1 for row in rows if row.status not in {"encerrado", "falso_positivo"})
    pressure = round((false_positive_count / max(len(rows), 1)) * 100, 1)
    return {
        "mode": "historical_estimate",
        "sampleSize": len(rows),
        "openCases": open_count,
        "falsePositiveCases": false_positive_count,
        "falsePositivePressure": pressure,
        "strictnessDelta": round(strictness_delta, 3),
        "estimatedImpact": (
            "Pode reduzir falso positivo, mas exige teste em lote real antes de aprovação."
            if strictness_delta > 0
            else "Pode aumentar captura de risco, com chance de mais falso positivo."
        ),
        "nextStep": "Crie uma versão de regra, submeta para aprovação e registre a justificativa do compliance officer.",
    }


@router.get("/rule-versions")
async def list_rule_versions(db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "read")
    rows = (
        await db.execute(
            text(
                """
                SELECT id, version_name, thresholds, status, rationale, submitted_at, approved_at, rejected_at, created_at, updated_at
                FROM pld_ft_rule_versions
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT 100
                """
            ).bindparams(tenant_id=user.tenant_id)
        )
    ).fetchall()
    return {
        "versions": [
            {
                "id": str(row.id),
                "versionName": row.version_name,
                "thresholds": row.thresholds or {},
                "status": row.status,
                "rationale": row.rationale,
                "submittedAt": row.submitted_at.isoformat() if row.submitted_at else None,
                "approvedAt": row.approved_at.isoformat() if row.approved_at else None,
                "rejectedAt": row.rejected_at.isoformat() if row.rejected_at else None,
                "createdAt": row.created_at.isoformat() if row.created_at else None,
                "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
            }
            for row in rows
        ]
    }


@router.post("/rule-versions", status_code=status.HTTP_201_CREATED)
async def create_rule_version(payload: RuleVersionRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "write")
    row = (
        await db.execute(
            text(
                """
                INSERT INTO pld_ft_rule_versions (tenant_id, version_name, thresholds, rationale, created_by)
                VALUES (:tenant_id, :version_name, CAST(:thresholds AS jsonb), :rationale, :user_id)
                ON CONFLICT (tenant_id, version_name)
                DO UPDATE SET thresholds = EXCLUDED.thresholds, rationale = EXCLUDED.rationale, status = 'draft', updated_at = now()
                RETURNING id, version_name, thresholds, status, rationale, created_at, updated_at
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                version_name=payload.versionName,
                thresholds=json.dumps(payload.thresholds, ensure_ascii=False),
                rationale=payload.rationale,
                user_id=user.user_id,
            )
        )
    ).fetchone()
    await _emit_pld_audit(
        db,
        user,
        action="rule_version.created",
        resource="pld_ft_rule_version",
        resource_id=str(row.id),
        details={"versionName": row.version_name, "status": row.status},
    )
    await db.commit()
    return {
        "id": str(row.id),
        "versionName": row.version_name,
        "thresholds": row.thresholds or {},
        "status": row.status,
        "rationale": row.rationale,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.patch("/rule-versions/{version_id}/{action}")
async def decide_rule_version(
    version_id: uuid.UUID,
    action: str,
    payload: RuleVersionDecisionRequest,
    db: DBSession,
    user: AuthUser,
) -> dict[str, Any]:
    _require_pld_role(user, "approve" if action in {"approve", "reject"} else "write")
    if action not in {"submit", "approve", "reject"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid rule version action")
    status_value = {"submit": "pending_approval", "approve": "approved", "reject": "rejected"}[action]
    timestamp_column = {"submit": "submitted_at", "approve": "approved_at", "reject": "rejected_at"}[action]
    row = (
        await db.execute(
            text(
                f"""
                UPDATE pld_ft_rule_versions
                SET status = :status, {timestamp_column} = now(), approved_by = CASE WHEN :action = 'approve' THEN :user_id ELSE approved_by END, updated_at = now()
                WHERE tenant_id = :tenant_id AND id = :id
                RETURNING id, version_name, thresholds, status, rationale, submitted_at, approved_at, rejected_at
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                id=version_id,
                status=status_value,
                action=action,
                user_id=user.user_id,
            )
        )
    ).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule version not found")
    if action == "approve":
        await db.execute(
            text(
                """
                INSERT INTO pld_ft_thresholds (tenant_id, thresholds, updated_by, updated_at)
                VALUES (:tenant_id, CAST(:thresholds AS jsonb), :user_id, now())
                ON CONFLICT (tenant_id)
                DO UPDATE SET thresholds = EXCLUDED.thresholds, updated_by = EXCLUDED.updated_by, updated_at = now()
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                thresholds=json.dumps(row.thresholds or {}, ensure_ascii=False),
                user_id=user.user_id,
            )
        )
    await _emit_pld_audit(
        db,
        user,
        action=f"rule_version.{action}",
        resource="pld_ft_rule_version",
        resource_id=str(row.id),
        details={"status": status_value, "note": payload.note},
    )
    await db.commit()
    return {
        "id": str(row.id),
        "versionName": row.version_name,
        "thresholds": row.thresholds or {},
        "status": row.status,
        "rationale": row.rationale,
        "submittedAt": row.submitted_at.isoformat() if row.submitted_at else None,
        "approvedAt": row.approved_at.isoformat() if row.approved_at else None,
        "rejectedAt": row.rejected_at.isoformat() if row.rejected_at else None,
        "note": payload.note,
    }


@router.post("/analyze", status_code=status.HTTP_201_CREATED)
async def analyze(payload: AnalyzeRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "write")
    body = payload.model_dump()
    saved = await _saved_thresholds(db, user)
    dossier = analyze_pld_ft(body, saved_thresholds=saved)
    p_hash = payload_hash(body)
    tx_count = len(body.get("transactions") or [])

    row = (
        await db.execute(
            text(
                """
                INSERT INTO pld_ft_imports (
                    tenant_id, user_id, institution, source_type, payload_hash,
                    transaction_count, dossier, risk_score, severity
                )
                VALUES (
                    :tenant_id, :user_id, :institution, :source_type, :payload_hash,
                    :transaction_count, CAST(:dossier AS jsonb), :risk_score, :severity
                )
                RETURNING id, created_at
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                institution=dossier.get("institution"),
                source_type=payload.sourceType,
                payload_hash=p_hash,
                transaction_count=tx_count,
                dossier=json.dumps(dossier, ensure_ascii=False),
                risk_score=dossier.get("riskScore"),
                severity=dossier.get("severity"),
            )
        )
    ).fetchone()
    await db.commit()

    return {
        "mode": "backend",
        "importId": str(row.id),
        "createdAt": row.created_at.isoformat() if row.created_at else datetime.utcnow().isoformat(),
        "payloadHash": p_hash,
        "transactionCount": tx_count,
        "dossier": dossier,
    }


@router.post("/cases", status_code=status.HTTP_201_CREATED)
async def save_case(payload: SaveCaseRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "write")
    dossier_id = str(payload.dossier.get("id") or "")
    if not dossier_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="dossier.id is required")

    row = (
        await db.execute(
            text(
                """
                INSERT INTO pld_ft_cases (
                    tenant_id, import_id, dossier_id, status, institution,
                    risk_score, severity, dossier, created_by, updated_at
                )
                VALUES (
                    :tenant_id, :import_id, :dossier_id, :status, :institution,
                    :risk_score, :severity, CAST(:dossier AS jsonb), :user_id, now()
                )
                ON CONFLICT (tenant_id, dossier_id)
                DO UPDATE SET
                    import_id = COALESCE(EXCLUDED.import_id, pld_ft_cases.import_id),
                    status = EXCLUDED.status,
                    institution = EXCLUDED.institution,
                    risk_score = EXCLUDED.risk_score,
                    severity = EXCLUDED.severity,
                    dossier = EXCLUDED.dossier,
                    updated_at = now()
                RETURNING *
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                import_id=payload.importId,
                dossier_id=dossier_id,
                status=payload.status,
                institution=payload.dossier.get("institution"),
                risk_score=payload.dossier.get("riskScore"),
                severity=payload.dossier.get("severity"),
                dossier=json.dumps(payload.dossier, ensure_ascii=False),
                user_id=user.user_id,
            )
        )
    ).fetchone()

    if payload.importId:
        await db.execute(
            text(
                """
                UPDATE pld_ft_imports
                SET case_ids = (
                    SELECT jsonb_agg(DISTINCT value)
                    FROM jsonb_array_elements(case_ids || jsonb_build_array(:case_id_text)) AS value
                )
                WHERE tenant_id = :tenant_id AND id = :import_id
                """
            ).bindparams(tenant_id=user.tenant_id, import_id=payload.importId, case_id_text=str(row.id))
        )
    await _emit_pld_audit(
        db,
        user,
        action="case.saved",
        resource="pld_ft_case",
        resource_id=str(row.id),
        details={"dossierId": dossier_id, "status": payload.status, "riskScore": payload.dossier.get("riskScore")},
    )
    await db.commit()
    await _recompute_customer_risk(db, user)

    decisions = await _case_decisions(db, user, row.id)
    return _row_to_case(row, decisions)


@router.get("/cases")
async def list_cases(
    db: DBSession,
    user: AuthUser,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=250),
) -> dict[str, Any]:
    _require_pld_role(user, "read")
    params: dict[str, Any] = {"tenant_id": user.tenant_id, "limit": limit}
    where = "tenant_id = :tenant_id"
    if status_filter:
        where += " AND status = :status"
        params["status"] = status_filter

    rows = (
        await db.execute(
            text(
                f"""
                SELECT *
                FROM pld_ft_cases
                WHERE {where}
                ORDER BY updated_at DESC, created_at DESC
                LIMIT :limit
                """
            ).bindparams(**params)
        )
    ).fetchall()

    cases: list[dict[str, Any]] = []
    for row in rows:
        decisions = await _case_decisions(db, user, row.id)
        cases.append(_row_to_case(row, decisions))
    return {"cases": cases}


@router.get("/customer-risk")
async def list_customer_risk(db: DBSession, user: AuthUser, limit: int = Query(default=50, ge=1, le=250)) -> dict[str, Any]:
    _require_pld_role(user, "read")
    rows = (
        await db.execute(
            text(
                """
                SELECT customer_id, risk_score, severity, total_cases, open_cases, escalated_cases,
                       false_positive_cases, total_amount, top_rules, evidence, last_case_at, updated_at
                FROM pld_ft_customer_risk
                WHERE tenant_id = :tenant_id
                ORDER BY risk_score DESC, updated_at DESC
                LIMIT :limit
                """
            ).bindparams(tenant_id=user.tenant_id, limit=limit)
        )
    ).fetchall()
    if not rows:
        await _recompute_customer_risk(db, user)
        rows = (
            await db.execute(
                text(
                    """
                    SELECT customer_id, risk_score, severity, total_cases, open_cases, escalated_cases,
                           false_positive_cases, total_amount, top_rules, evidence, last_case_at, updated_at
                    FROM pld_ft_customer_risk
                    WHERE tenant_id = :tenant_id
                    ORDER BY risk_score DESC, updated_at DESC
                    LIMIT :limit
                    """
                ).bindparams(tenant_id=user.tenant_id, limit=limit)
            )
        ).fetchall()
    return {
        "customers": [
            {
                "customerId": row.customer_id,
                "riskScore": row.risk_score,
                "severity": row.severity,
                "totalCases": row.total_cases,
                "openCases": row.open_cases,
                "escalatedCases": row.escalated_cases,
                "falsePositiveCases": row.false_positive_cases,
                "totalAmount": float(row.total_amount or 0),
                "topRules": row.top_rules or [],
                "evidence": row.evidence or [],
                "lastCaseAt": row.last_case_at.isoformat() if row.last_case_at else None,
                "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
            }
            for row in rows
        ]
    }


@router.post("/customer-risk/recompute")
async def recompute_customer_risk(db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "write")
    customers = await _recompute_customer_risk(db, user)
    await _emit_pld_audit(
        db,
        user,
        action="customer_risk.recomputed",
        resource="pld_ft_customer_risk",
        details={"count": len(customers)},
    )
    await db.commit()
    return {"customers": customers, "count": len(customers)}


@router.get("/cases/{case_id}/report.pdf")
async def case_report_pdf(case_id: uuid.UUID, db: DBSession, user: AuthUser) -> Response:
    _require_pld_role(user, "read")
    case = await _get_case_or_404(case_id, db, user)
    html = _case_report_html(case)
    try:
        from weasyprint import HTML  # type: ignore

        pdf = HTML(string=html).write_pdf()
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"content-disposition": f'attachment; filename="quarry-pldft-{case["dossierId"]}.pdf"'},
        )
    except Exception:
        return Response(
            content=html,
            media_type="text/html; charset=utf-8",
            headers={"content-disposition": f'attachment; filename="quarry-pldft-{case["dossierId"]}.html"'},
        )


@router.get("/cases/{case_id}/ai-analyst")
async def case_ai_analyst(case_id: uuid.UUID, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "read")
    case = await _get_case_or_404(case_id, db, user)
    dossier = case.get("dossier") or {}
    ai_analyst = dossier.get("aiAnalyst") or {}
    memories = await _decision_memory(db, user, case)
    return {
        "caseId": case["id"],
        "dossierId": case["dossierId"],
        "aiAnalyst": ai_analyst,
        "decisionMemory": memories,
        "operatorBrief": {
            "headline": "Revisar evidências, lacunas e casos semelhantes antes da decisão.",
            "recommendedAction": (ai_analyst.get("caseNarrative") or {}).get("recommendedDecision"),
            "memoryInsight": (
                f"{len(memories)} caso(s) semelhante(s) encontrados na memória institucional."
                if memories
                else "Ainda não há casos semelhantes decididos para comparar."
            ),
            "guardrail": "A IA organiza hipóteses e evidências; a decisão final permanece humana e auditável.",
        },
    }


@router.patch("/cases/{case_id}/workflow")
async def update_case_workflow(case_id: uuid.UUID, payload: WorkflowRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "write")
    await _get_case_or_404(case_id, db, user)
    status_value = payload.status
    workflow_patch = {
        "lastWorkflowNote": payload.note,
        "lastWorkflowUpdateBy": user.email,
        "lastWorkflowUpdateAt": datetime.utcnow().isoformat() + "Z",
    }
    row = (
        await db.execute(
            text(
                """
                UPDATE pld_ft_cases
                SET
                    assignee = COALESCE(:assignee, assignee),
                    priority = COALESCE(:priority, priority),
                    sla_due_at = COALESCE(CAST(:sla_due_at AS timestamptz), sla_due_at),
                    status = COALESCE(:status, status),
                    closed_at = CASE WHEN :status = 'encerrado' THEN now() ELSE closed_at END,
                    reopened_at = CASE WHEN :status IN ('novo', 'em_revisao', 'escalado') AND closed_at IS NOT NULL THEN now() ELSE reopened_at END,
                    workflow = workflow || CAST(:workflow_patch AS jsonb),
                    updated_at = now()
                WHERE tenant_id = :tenant_id AND id = :id
                RETURNING *
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                id=case_id,
                assignee=payload.assignee,
                priority=payload.priority,
                sla_due_at=payload.slaDueAt,
                status=status_value,
                workflow_patch=json.dumps(workflow_patch, ensure_ascii=False),
            )
        )
    ).fetchone()
    if payload.note:
        await db.execute(
            text(
                """
                INSERT INTO pld_ft_case_comments (tenant_id, case_id, body, author, created_by)
                VALUES (:tenant_id, :case_id, :body, :author, :user_id)
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                case_id=case_id,
                body=payload.note,
                author=user.email,
                user_id=user.user_id,
            )
        )
    await _emit_pld_audit(
        db,
        user,
        action="case.workflow_updated",
        resource="pld_ft_case",
        resource_id=str(case_id),
        details=payload.model_dump(exclude_none=True),
    )
    await db.commit()
    await _recompute_customer_risk(db, user)
    return _row_to_case(row, await _case_decisions(db, user, case_id))


@router.get("/cases/{case_id}/comments")
async def list_case_comments(case_id: uuid.UUID, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "read")
    await _get_case_or_404(case_id, db, user)
    return {"comments": await _case_comments(db, user, case_id)}


@router.post("/cases/{case_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_case_comment(case_id: uuid.UUID, payload: CommentRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "write")
    await _get_case_or_404(case_id, db, user)
    await db.execute(
        text(
            """
            INSERT INTO pld_ft_case_comments (tenant_id, case_id, body, author, created_by)
            VALUES (:tenant_id, :case_id, :body, :author, :user_id)
            """
        ).bindparams(
            tenant_id=user.tenant_id,
            case_id=case_id,
            body=payload.body,
            author=payload.author or user.email,
            user_id=user.user_id,
        )
    )
    await _emit_pld_audit(
        db,
        user,
        action="case.comment_created",
        resource="pld_ft_case",
        resource_id=str(case_id),
        details={"author": payload.author or user.email, "bodyLength": len(payload.body)},
    )
    await db.commit()
    return {"comments": await _case_comments(db, user, case_id)}


@router.get("/cases/{case_id}/attachments")
async def list_case_attachments(case_id: uuid.UUID, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "read")
    await _get_case_or_404(case_id, db, user)
    return {"attachments": await _case_attachments(db, user, case_id)}


@router.post("/cases/{case_id}/attachments", status_code=status.HTTP_201_CREATED)
async def create_case_attachment(case_id: uuid.UUID, payload: AttachmentRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "write")
    await _get_case_or_404(case_id, db, user)
    await db.execute(
        text(
            """
            INSERT INTO pld_ft_case_attachments (
                tenant_id, case_id, file_name, content_type, file_size, description, storage_url, uploaded_by
            )
            VALUES (
                :tenant_id, :case_id, :file_name, :content_type, :file_size, :description, :storage_url, :user_id
            )
            """
        ).bindparams(
            tenant_id=user.tenant_id,
            case_id=case_id,
            file_name=payload.fileName,
            content_type=payload.contentType,
            file_size=payload.fileSize,
            description=payload.description,
            storage_url=payload.storageUrl,
            user_id=user.user_id,
        )
    )
    await _emit_pld_audit(
        db,
        user,
        action="case.attachment_created",
        resource="pld_ft_case",
        resource_id=str(case_id),
        details={"fileName": payload.fileName, "contentType": payload.contentType, "fileSize": payload.fileSize},
    )
    await db.commit()
    return {"attachments": await _case_attachments(db, user, case_id)}


@router.patch("/cases/{case_id}/decision")
async def decide_case(case_id: uuid.UUID, payload: DecisionRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "write")
    await _get_case_or_404(case_id, db, user)

    analyst = payload.analyst or user.email
    await db.execute(
        text(
            """
            INSERT INTO pld_ft_case_decisions (tenant_id, case_id, status, note, analyst, decided_by)
            VALUES (:tenant_id, :case_id, :status, :note, :analyst, :user_id)
            """
        ).bindparams(
            tenant_id=user.tenant_id,
            case_id=case_id,
            status=payload.status,
            note=payload.note,
            analyst=analyst,
            user_id=user.user_id,
        )
    )
    row = (
        await db.execute(
            text(
                """
                UPDATE pld_ft_cases
                SET status = :status, updated_at = now()
                WHERE tenant_id = :tenant_id AND id = :id
                RETURNING *
                """
            ).bindparams(tenant_id=user.tenant_id, id=case_id, status=payload.status)
        )
    ).fetchone()
    await _emit_pld_audit(
        db,
        user,
        action="case.decision_recorded",
        resource="pld_ft_case",
        resource_id=str(case_id),
        details={"status": payload.status, "analyst": analyst, "noteLength": len(payload.note or "")},
    )
    await db.commit()
    await _recompute_customer_risk(db, user)

    decisions = await _case_decisions(db, user, case_id)
    return _row_to_case(row, decisions)


async def _executive_report(db: DBSession, user: AuthUser) -> dict[str, Any]:
    await _recompute_customer_risk(db, user)
    case_rows = (
        await db.execute(
            text(
                """
                SELECT status, severity, risk_score, sla_due_at, dossier
                FROM pld_ft_cases
                WHERE tenant_id = :tenant_id
                """
            ).bindparams(tenant_id=user.tenant_id)
        )
    ).fetchall()
    customer_rows = (
        await db.execute(
            text(
                """
                SELECT customer_id, risk_score, severity, total_cases, open_cases, total_amount, top_rules
                FROM pld_ft_customer_risk
                WHERE tenant_id = :tenant_id
                ORDER BY risk_score DESC
                LIMIT 10
                """
            ).bindparams(tenant_id=user.tenant_id)
        )
    ).fetchall()
    version_rows = (
        await db.execute(
            text(
                """
                SELECT status, count(*) AS count
                FROM pld_ft_rule_versions
                WHERE tenant_id = :tenant_id
                GROUP BY status
                """
            ).bindparams(tenant_id=user.tenant_id)
        )
    ).fetchall()
    now = datetime.utcnow()
    open_statuses = {"novo", "em_revisao", "escalado"}
    total_cases = len(case_rows)
    open_cases = sum(1 for row in case_rows if row.status in open_statuses)
    critical_cases = sum(1 for row in case_rows if row.severity == "critical")
    escalated_cases = sum(1 for row in case_rows if row.status == "escalado")
    false_positive_cases = sum(1 for row in case_rows if row.status == "falso_positivo")
    overdue_cases = sum(1 for row in case_rows if row.sla_due_at and row.sla_due_at.replace(tzinfo=None) < now and row.status in open_statuses)
    rules: dict[str, int] = {}
    for row in case_rows:
        for finding in (row.dossier or {}).get("findings") or []:
            rule_id = str(finding.get("ruleId") or "unknown")
            rules[rule_id] = rules.get(rule_id, 0) + 1
    top_rules = [{"ruleId": rule, "count": count} for rule, count in sorted(rules.items(), key=lambda pair: pair[1], reverse=True)[:8]]
    top_customers = [
        {
            "customerId": row.customer_id,
            "riskScore": row.risk_score,
            "severity": row.severity,
            "totalCases": row.total_cases,
            "openCases": row.open_cases,
            "totalAmount": float(row.total_amount or 0),
            "topRules": row.top_rules or [],
        }
        for row in customer_rows
    ]
    recommendations = [
        "Priorizar revisão dos clientes com score contínuo crítico e casos em SLA vencido.",
        "Submeter alterações de thresholds via versão formal e aprovação do compliance officer.",
        "Revisar regras com maior incidência em falso positivo antes de ampliar sensibilidade.",
    ]
    if critical_cases:
        recommendations.insert(0, "Realizar comitê sobre casos críticos e avaliar necessidade de comunicação regulatória.")
    return {
        "generatedAt": now.isoformat() + "Z",
        "executiveSummary": (
            f"O ambiente possui {total_cases} caso(s) PLD/FT, {open_cases} aberto(s), "
            f"{critical_cases} crítico(s) e {overdue_cases} com SLA vencido."
        ),
        "kpis": {
            "totalCases": total_cases,
            "openCases": open_cases,
            "criticalCases": critical_cases,
            "escalatedCases": escalated_cases,
            "falsePositiveCases": false_positive_cases,
            "overdueCases": overdue_cases,
        },
        "topRules": top_rules,
        "topCustomers": top_customers,
        "ruleVersionStatus": {row.status: row.count for row in version_rows},
        "committeeRecommendations": recommendations,
    }


@router.get("/executive-report")
async def executive_report(db: DBSession, user: AuthUser) -> dict[str, Any]:
    return await _executive_report(db, user)


@router.get("/executive-report.pdf")
async def executive_report_pdf(db: DBSession, user: AuthUser) -> Response:
    _require_pld_role(user, "read")
    report = await _executive_report(db, user)
    html = _executive_report_html(report)
    try:
        from weasyprint import HTML  # type: ignore

        pdf = HTML(string=html).write_pdf()
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"content-disposition": 'attachment; filename="quarry-pldft-relatorio-executivo.pdf"'},
        )
    except Exception:
        return Response(
            content=html,
            media_type="text/html; charset=utf-8",
            headers={"content-disposition": 'attachment; filename="quarry-pldft-relatorio-executivo.html"'},
        )


@router.get("/monthly-metrics")
async def monthly_metrics(db: DBSession, user: AuthUser, month: str | None = Query(default=None)) -> dict[str, Any]:
    _require_pld_role(user, "read")
    start, end, label = _month_window(month)
    rows = (
        await db.execute(
            text(
                """
                SELECT status, severity, risk_score, sla_due_at, dossier, created_at, updated_at
                FROM pld_ft_cases
                WHERE tenant_id = :tenant_id
                  AND created_at >= :start
                  AND created_at < :end
                """
            ).bindparams(tenant_id=user.tenant_id, start=start, end=end)
        )
    ).fetchall()
    import_rows = (
        await db.execute(
            text(
                """
                SELECT count(*) AS total
                FROM pld_ft_imports
                WHERE tenant_id = :tenant_id
                  AND created_at >= :start
                  AND created_at < :end
                """
            ).bindparams(tenant_id=user.tenant_id, start=start, end=end)
        )
    ).fetchone()
    open_statuses = {"novo", "em_revisao", "escalado"}
    now = datetime.utcnow()
    rules: dict[str, dict[str, int]] = {}
    for row in rows:
        for finding in (row.dossier or {}).get("findings") or []:
            rule_id = str(finding.get("ruleId") or "unknown")
            item = rules.setdefault(rule_id, {"count": 0, "falsePositive": 0})
            item["count"] += 1
            if row.status == "falso_positivo":
                item["falsePositive"] += 1
    noisy_rules = [
        {
            "ruleId": rule_id,
            "count": values["count"],
            "falsePositive": values["falsePositive"],
            "noiseScore": round((values["falsePositive"] / max(values["count"], 1)) * 100, 1),
        }
        for rule_id, values in sorted(rules.items(), key=lambda pair: (pair[1]["falsePositive"], pair[1]["count"]), reverse=True)[:8]
    ]
    total_cases = len(rows)
    archived = sum(1 for row in rows if row.status in {"encerrado", "falso_positivo"})
    escalated = sum(1 for row in rows if row.status == "escalado")
    overdue = sum(1 for row in rows if row.sla_due_at and row.sla_due_at.replace(tzinfo=None) < now and row.status in open_statuses)
    with_sla = sum(1 for row in rows if row.sla_due_at)
    return {
        "month": label,
        "period": {"start": start.isoformat() + "Z", "end": end.isoformat() + "Z"},
        "kpis": {
            "alerts": int(import_rows.total or 0) if import_rows else 0,
            "cases": total_cases,
            "archived": archived,
            "escalated": escalated,
            "slaTracked": with_sla,
            "slaOverdue": overdue,
            "slaComplianceRate": round(((with_sla - overdue) / max(with_sla, 1)) * 100, 1),
            "criticalCases": sum(1 for row in rows if row.severity == "critical"),
            "averageRiskScore": round(sum(int(row.risk_score or 0) for row in rows) / max(total_cases, 1), 1),
        },
        "noisyRules": noisy_rules,
        "recommendations": [
            "Atacar regras com ruido acima de 30% antes de ampliar sensibilidade.",
            "Revisar casos escalados e SLA vencido no comite PLD/FT mensal.",
            "Conferir se alertas sem caso aberto exigem calibragem do limiar de criacao automatica.",
        ],
    }


@router.get("/audit-log")
async def audit_log(db: DBSession, user: AuthUser, limit: int = Query(default=100, ge=1, le=500)) -> dict[str, Any]:
    _require_pld_role(user, "audit")
    rows = (
        await db.execute(
            text(
                """
                SELECT id, actor_email, actor_role, action, resource, resource_id,
                       details, prev_hash, entry_hash, created_at
                FROM pld_ft_audit_log
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC, id DESC
                LIMIT :limit
                """
            ).bindparams(tenant_id=user.tenant_id, limit=limit)
        )
    ).fetchall()
    ordered = list(reversed(rows))
    chain_ok = True
    previous_hash: str | None = ordered[0].prev_hash if ordered else None
    for row in ordered:
        if row.prev_hash != previous_hash:
            chain_ok = False
            break
        previous_hash = row.entry_hash
    return {
        "chainVerifiedForWindow": chain_ok,
        "entries": [
            {
                "id": str(row.id),
                "actorEmail": row.actor_email,
                "actorRole": row.actor_role,
                "action": row.action,
                "resource": row.resource,
                "resourceId": row.resource_id,
                "details": row.details or {},
                "prevHash": row.prev_hash,
                "entryHash": row.entry_hash,
                "createdAt": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
    }


@router.post("/ingest-stream", status_code=status.HTTP_201_CREATED)
async def ingest_stream(payload: StreamIngestionRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "write")
    analyze_payload = AnalyzeRequest(**payload.model_dump(exclude={"autoCaseMinScore", "openCase"}))
    return await _persist_analysis(
        analyze_payload,
        db,
        user,
        source_type=payload.sourceType or "stream",
        open_case=payload.openCase,
        auto_case_min_score=payload.autoCaseMinScore,
        audit_action="ingestion.stream_processed",
    )


@router.get("/ingestion-jobs")
async def list_ingestion_jobs(db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "read")
    rows = (
        await db.execute(
            text(
                """
                SELECT *
                FROM pld_ft_ingestion_jobs
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT 100
                """
            ).bindparams(tenant_id=user.tenant_id)
        )
    ).fetchall()
    return {"jobs": [_row_to_ingestion_job(row) for row in rows]}


@router.post("/ingestion-jobs", status_code=status.HTTP_201_CREATED)
async def create_ingestion_job(payload: IngestionJobRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "write")
    next_run_at = datetime.utcnow() + timedelta(seconds=payload.intervalSeconds)
    row = (
        await db.execute(
            text(
                """
                INSERT INTO pld_ft_ingestion_jobs (
                    tenant_id, name, source_type, interval_seconds, auto_case_min_score,
                    config, created_by, next_run_at
                )
                VALUES (
                    :tenant_id, :name, :source_type, :interval_seconds, :auto_case_min_score,
                    CAST(:config AS jsonb), :user_id, :next_run_at
                )
                RETURNING *
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                name=payload.name,
                source_type=payload.sourceType,
                interval_seconds=payload.intervalSeconds,
                auto_case_min_score=payload.autoCaseMinScore,
                config=json.dumps(payload.config, ensure_ascii=False),
                user_id=user.user_id,
                next_run_at=next_run_at,
            )
        )
    ).fetchone()
    await _emit_pld_audit(
        db,
        user,
        action="ingestion_job.created",
        resource="pld_ft_ingestion_job",
        resource_id=str(row.id),
        details={"name": row.name, "intervalSeconds": row.interval_seconds},
    )
    await db.commit()
    return _row_to_ingestion_job(row)


async def _run_ingestion_job(job_id: uuid.UUID, db: DBSession, user: AuthUser) -> dict[str, Any]:
    row = (
        await db.execute(
            text("SELECT * FROM pld_ft_ingestion_jobs WHERE tenant_id = :tenant_id AND id = :id").bindparams(
                tenant_id=user.tenant_id,
                id=job_id,
            )
        )
    ).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found")
    config = row.config or {}
    sample_payload = config.get("samplePayload") or config.get("payload")
    if not sample_payload:
        result = {
            "status": "skipped",
            "reason": "Configure config.samplePayload para o MVP de ingestao recorrente.",
            "ranAt": datetime.utcnow().isoformat() + "Z",
        }
    else:
        analyze_payload = AnalyzeRequest(**{**sample_payload, "sourceType": row.source_type})
        analysis = await _persist_analysis(
            analyze_payload,
            db,
            user,
            source_type=row.source_type,
            open_case=True,
            auto_case_min_score=int(row.auto_case_min_score or 65),
            audit_action="ingestion_job.executed",
            audit_resource_id=str(row.id),
        )
        result = {
            "status": "processed",
            "importId": analysis["importId"],
            "createdCaseId": (analysis.get("createdCase") or {}).get("id"),
            "riskScore": analysis["dossier"].get("riskScore"),
            "severity": analysis["dossier"].get("severity"),
            "ranAt": datetime.utcnow().isoformat() + "Z",
        }
    next_run_at = datetime.utcnow() + timedelta(seconds=int(row.interval_seconds or 300))
    updated = (
        await db.execute(
            text(
                """
                UPDATE pld_ft_ingestion_jobs
                SET last_run_at = now(),
                    next_run_at = :next_run_at,
                    last_result = CAST(:last_result AS jsonb),
                    updated_at = now()
                WHERE tenant_id = :tenant_id AND id = :id
                RETURNING *
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                id=job_id,
                next_run_at=next_run_at,
                last_result=json.dumps(result, ensure_ascii=False),
            )
        )
    ).fetchone()
    await _emit_pld_audit(
        db,
        user,
        action="ingestion_job.run_recorded",
        resource="pld_ft_ingestion_job",
        resource_id=str(job_id),
        details=result,
    )
    await db.commit()
    return {"job": _row_to_ingestion_job(updated), "result": result}


@router.post("/ingestion-jobs/{job_id}/run")
async def run_ingestion_job(job_id: uuid.UUID, db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "write")
    return await _run_ingestion_job(job_id, db, user)


@router.post("/ingestion-jobs/run-due")
async def run_due_ingestion_jobs(db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "write")
    rows = (
        await db.execute(
            text(
                """
                SELECT id
                FROM pld_ft_ingestion_jobs
                WHERE tenant_id = :tenant_id
                  AND status = 'active'
                  AND (next_run_at IS NULL OR next_run_at <= now())
                ORDER BY next_run_at NULLS FIRST, created_at
                LIMIT 20
                """
            ).bindparams(tenant_id=user.tenant_id)
        )
    ).fetchall()
    results = [await _run_ingestion_job(row.id, db, user) for row in rows]
    return {"count": len(results), "results": results}


@router.post("/cases/{case_id}/regulatory-exports", status_code=status.HTTP_201_CREATED)
async def create_regulatory_export(
    case_id: uuid.UUID,
    payload: RegulatoryExportRequest,
    db: DBSession,
    user: AuthUser,
) -> dict[str, Any]:
    _require_pld_role(user, "write")
    case = await _get_case_or_404(case_id, db, user)
    structured = _regulatory_payload_from_case(case, payload.exportType)
    row = (
        await db.execute(
            text(
                """
                INSERT INTO pld_ft_regulatory_exports (
                    tenant_id, case_id, export_type, status, structured_payload,
                    approval_note, created_by
                )
                VALUES (
                    :tenant_id, :case_id, :export_type, 'pending_approval',
                    CAST(:structured_payload AS jsonb), :approval_note, :user_id
                )
                RETURNING *
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                case_id=case_id,
                export_type=payload.exportType,
                structured_payload=json.dumps(structured, ensure_ascii=False, default=_json_default),
                approval_note=payload.approvalNote,
                user_id=user.user_id,
            )
        )
    ).fetchone()
    await _emit_pld_audit(
        db,
        user,
        action="regulatory_export.created",
        resource="pld_ft_regulatory_export",
        resource_id=str(row.id),
        details={"caseId": str(case_id), "exportType": payload.exportType, "status": row.status},
    )
    await db.commit()
    return _row_to_regulatory_export(row)


@router.get("/regulatory-exports")
async def list_regulatory_exports(db: DBSession, user: AuthUser) -> dict[str, Any]:
    _require_pld_role(user, "read")
    rows = (
        await db.execute(
            text(
                """
                SELECT *
                FROM pld_ft_regulatory_exports
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT 100
                """
            ).bindparams(tenant_id=user.tenant_id)
        )
    ).fetchall()
    return {"exports": [_row_to_regulatory_export(row) for row in rows]}


@router.patch("/regulatory-exports/{export_id}/approve")
async def approve_regulatory_export(
    export_id: uuid.UUID,
    payload: RegulatoryExportRequest,
    db: DBSession,
    user: AuthUser,
) -> dict[str, Any]:
    _require_pld_role(user, "approve")
    row = (
        await db.execute(
            text(
                """
                UPDATE pld_ft_regulatory_exports
                SET status = 'approved',
                    approval_note = :approval_note,
                    approved_by = :user_id,
                    approved_at = now(),
                    updated_at = now()
                WHERE tenant_id = :tenant_id AND id = :id
                RETURNING *
                """
            ).bindparams(
                tenant_id=user.tenant_id,
                id=export_id,
                approval_note=payload.approvalNote,
                user_id=user.user_id,
            )
        )
    ).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulatory export not found")
    await _emit_pld_audit(
        db,
        user,
        action="regulatory_export.approved",
        resource="pld_ft_regulatory_export",
        resource_id=str(row.id),
        details={"caseId": str(row.case_id), "approvalNote": payload.approvalNote},
    )
    await db.commit()
    return _row_to_regulatory_export(row)


@router.get("/regulatory-exports/{export_id}.json")
async def download_regulatory_export_json(export_id: uuid.UUID, db: DBSession, user: AuthUser) -> Response:
    _require_pld_role(user, "read")
    row = (
        await db.execute(
            text(
                """
                SELECT *
                FROM pld_ft_regulatory_exports
                WHERE tenant_id = :tenant_id AND id = :id
                """
            ).bindparams(tenant_id=user.tenant_id, id=export_id)
        )
    ).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulatory export not found")
    if row.status not in {"approved", "exported"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Regulatory export requires compliance officer approval before download",
        )
    if row.status == "approved":
        await db.execute(
            text(
                """
                UPDATE pld_ft_regulatory_exports
                SET status = 'exported', exported_at = now(), updated_at = now()
                WHERE tenant_id = :tenant_id AND id = :id
                """
            ).bindparams(tenant_id=user.tenant_id, id=export_id)
        )
        await _emit_pld_audit(
            db,
            user,
            action="regulatory_export.downloaded",
            resource="pld_ft_regulatory_export",
            resource_id=str(row.id),
            details={"caseId": str(row.case_id)},
        )
        await db.commit()
    content = json.dumps(row.structured_payload or {}, ensure_ascii=False, indent=2, default=_json_default)
    return Response(
        content=content,
        media_type="application/json; charset=utf-8",
        headers={"content-disposition": f'attachment; filename="quarry-pldft-export-{row.id}.json"'},
    )


@router.get("/benchmark")
async def benchmark(db: DBSession, user: AuthUser) -> dict[str, Any]:
    """Run a small deterministic benchmark with explicit scenarios.

    This is not a model-performance claim. It is a regression harness exposed to
    the UI so the operator can see whether core rule classes still trigger.
    """
    scenarios = [
        {
            "id": "pass-through",
            "name": "Conta de passagem Pix",
            "expectedRules": ["PLD-PIX-001"],
            "payload": {
                "institution": "Banco de Teste",
                "customers": [{"customerId": "C-001", "declaredMonthlyIncome": 2500, "accountAgeDays": 12}],
                "transactions": [
                    {
                        "id": "T-001",
                        "customerId": "C-001",
                        "accountId": "A-001",
                        "counterpartyId": "SRC-001",
                        "direction": "in",
                        "rail": "Pix",
                        "amount": 12000,
                        "timestamp": "2026-05-30T10:00:00Z",
                    },
                    {
                        "id": "T-002",
                        "customerId": "C-001",
                        "accountId": "A-001",
                        "counterpartyId": "DST-001",
                        "direction": "out",
                        "rail": "Pix",
                        "amount": 10800,
                        "timestamp": "2026-05-30T10:35:00Z",
                    },
                ],
            },
        },
        {
            "id": "clean",
            "name": "Baixo risco transacional",
            "expectedRules": [],
            "payload": {
                "institution": "Banco de Teste",
                "customers": [{"customerId": "C-LOW", "declaredMonthlyIncome": 9000, "accountAgeDays": 900}],
                "transactions": [
                    {
                        "id": "T-LOW",
                        "customerId": "C-LOW",
                        "accountId": "A-LOW",
                        "counterpartyId": "MERCHANT-1",
                        "direction": "out",
                        "rail": "Pix",
                        "amount": 180,
                        "timestamp": "2026-05-30T11:00:00Z",
                    }
                ],
            },
        },
    ]
    thresholds = await _saved_thresholds(db, user)
    results: list[dict[str, Any]] = []
    for scenario in scenarios:
        dossier = analyze_pld_ft(scenario["payload"], saved_thresholds=thresholds)
        found_rules = [item["ruleId"] for item in dossier["findings"]]
        expected = scenario["expectedRules"]
        results.append(
            {
                "id": scenario["id"],
                "name": scenario["name"],
                "expectedRules": expected,
                "foundRules": found_rules,
                "passed": all(rule in found_rules for rule in expected) and (bool(expected) or not found_rules),
                "riskScore": dossier["riskScore"],
                "severity": dossier["severity"],
            }
        )
    return {"results": results, "passed": all(item["passed"] for item in results)}
