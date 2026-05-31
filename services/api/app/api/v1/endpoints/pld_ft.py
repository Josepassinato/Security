"""Operational PLD/FT endpoints.

This surface persists the deterministic PLD/FT lab into Postgres so the
Brazilian fintech-compliance product can move from demo analysis to an
auditable workflow: import -> deterministic dossier -> case -> human decision.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
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


def _row_to_case(row: Any, decisions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    dossier = dict(row.dossier or {})
    return {
        "id": str(row.id),
        "status": row.status,
        "importId": str(row.import_id) if row.import_id else None,
        "dossier": dossier,
        "dossierId": row.dossier_id,
        "institution": row.institution,
        "riskScore": row.risk_score,
        "severity": row.severity,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
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
    saved = await _saved_thresholds(db, user)
    return {"thresholds": {**DEFAULT_THRESHOLDS, **saved}, "defaults": DEFAULT_THRESHOLDS}


@router.put("/thresholds")
async def save_thresholds(payload: ThresholdsRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
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
    await db.commit()
    return {"thresholds": {**DEFAULT_THRESHOLDS, **payload.thresholds}, "saved": True}


@router.post("/analyze", status_code=status.HTTP_201_CREATED)
async def analyze(payload: AnalyzeRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
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
    await db.commit()

    decisions = await _case_decisions(db, user, row.id)
    return _row_to_case(row, decisions)


@router.get("/cases")
async def list_cases(
    db: DBSession,
    user: AuthUser,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=250),
) -> dict[str, Any]:
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


@router.get("/cases/{case_id}/report.pdf")
async def case_report_pdf(case_id: uuid.UUID, db: DBSession, user: AuthUser) -> Response:
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


@router.patch("/cases/{case_id}/decision")
async def decide_case(case_id: uuid.UUID, payload: DecisionRequest, db: DBSession, user: AuthUser) -> dict[str, Any]:
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
    await db.commit()

    decisions = await _case_decisions(db, user, case_id)
    return _row_to_case(row, decisions)


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
