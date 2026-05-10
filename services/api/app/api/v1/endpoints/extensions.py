"""Extensions API endpoints.

Serves data consumed by the AiSOC osquery extension (aisoc.ext) running on
enrolled hosts.  The extension calls these three read-only endpoints to
populate its virtual tables inside osqueryi.

Endpoints
---------
GET /v1/extensions/pending-actions?host_identifier=...
    → rows for ``aisoc_pending_actions`` virtual table

GET /v1/extensions/alert-cache?host_identifier=...&since=...
    → rows for ``aisoc_alert_cache`` virtual table (last 24 h by default)

GET /v1/extensions/persistence-baseline?host_identifier=...
    → trusted persistence items for ``aisoc_attck_persistence`` baseline
      comparison

Auth
----
Requests must carry a Bearer token validated by ``require_permission``.
Host-scoped tokens issued to enrolled agents are accepted; they must carry
at least the ``extensions:read`` permission.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AuthUser, DBSession, require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extensions", tags=["extensions"])

# Convenience alias — host-scoped token with extensions:read
ExtUser = Annotated[AuthUser, Depends(require_permission("extensions:read"))]


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class PendingAction(BaseModel):
    """One row for the ``aisoc_pending_actions`` virtual table."""

    action_id: uuid.UUID
    case_id: str | None = None
    action_type: str
    target: str
    requested_by: str
    requested_at: datetime
    expires_at: datetime | None = None
    description: str = ""


class PendingActionsResponse(BaseModel):
    host_identifier: str
    actions: list[PendingAction] = Field(default_factory=list)


class AlertCacheEntry(BaseModel):
    """One row for the ``aisoc_alert_cache`` virtual table."""

    alert_id: uuid.UUID
    rule_id: str
    severity: str
    fired_at: datetime
    summary: str
    case_id: str | None = None


class AlertCacheResponse(BaseModel):
    host_identifier: str
    since: datetime
    alerts: list[AlertCacheEntry] = Field(default_factory=list)


class PersistenceBaselineEntry(BaseModel):
    """One trusted-persistence item for ``aisoc_attck_persistence``."""

    item_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    # "crontab" | "systemd" | "launchd" | "registry_run" | ...
    persistence_type: str
    identifier: str  # key / path / service name
    description: str = ""
    mitre_technique: str = ""  # e.g. "T1053.003"
    is_trusted: bool = True


class PersistenceBaselineResponse(BaseModel):
    host_identifier: str
    baseline: list[PersistenceBaselineEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal query helpers
# ---------------------------------------------------------------------------


async def _get_pending_actions_for_host(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    host_identifier: str,
) -> list[dict]:
    """Return pending HITL approval rows for a specific host.

    Queries ``agent_approvals`` (responder module) filtered to ``pending``
    status with a target matching ``host_identifier``.  Returns an empty list
    when the table does not yet exist.
    """
    try:
        result = await db.execute(
            text(
                """
                SELECT
                    id                                      AS action_id,
                    case_id,
                    COALESCE(action->>'type', 'unknown')    AS action_type,
                    COALESCE(action->>'target', :hid)       AS target,
                    requested_by,
                    created_at                              AS requested_at,
                    expires_at,
                    COALESCE(summary, '')                   AS description
                FROM agent_approvals
                WHERE tenant_id = :tid
                  AND status    = 'pending'
                  AND (
                        action->>'host_identifier' = :hid
                     OR action->>'target'          = :hid
                  )
                ORDER BY created_at DESC
                LIMIT 100
                """
            ),
            {"tid": str(tenant_id), "hid": host_identifier},
        )
        return [dict(r) for r in result.mappings().all()]
    except Exception:
        logger.debug(
            "agent_approvals table unavailable; returning empty action list",
            exc_info=True,
        )
        return []


async def _get_alert_cache_for_host(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    host_identifier: str,
    since: datetime,
) -> list[dict]:
    """Return recent alerts linked to ``host_identifier``.

    Searches the ``alerts`` table by ``context`` JSONB keys
    ``host_identifier`` or ``hostname``.
    """
    try:
        result = await db.execute(
            text(
                """
                SELECT
                    id          AS alert_id,
                    COALESCE(
                        context->>'rule_id',
                        rule_id::text,
                        'unknown'
                    )           AS rule_id,
                    severity,
                    created_at  AS fired_at,
                    COALESCE(title, summary, name, '') AS summary,
                    case_id
                FROM alerts
                WHERE tenant_id = :tid
                  AND created_at >= :since
                  AND (
                        context->>'host_identifier' = :hid
                     OR context->>'hostname'        = :hid
                  )
                ORDER BY created_at DESC
                LIMIT 200
                """
            ),
            {
                "tid": str(tenant_id),
                "hid": host_identifier,
                "since": since.isoformat(),
            },
        )
        return [dict(r) for r in result.mappings().all()]
    except Exception:
        logger.debug(
            "alerts table query failed; returning empty alert cache",
            exc_info=True,
        )
        return []


async def _get_persistence_baseline(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    host_identifier: str,
) -> list[dict]:
    """Return trusted persistence items for the given host.

    Queries ``persistence_baselines`` (created lazily by an operator).
    Tenant-global rows (``host_identifier IS NULL``) apply to all hosts.
    Returns empty list when the table is absent.
    """
    try:
        result = await db.execute(
            text(
                """
                SELECT
                    id                                AS item_id,
                    persistence_type,
                    identifier,
                    COALESCE(description, '')         AS description,
                    COALESCE(mitre_technique, '')     AS mitre_technique,
                    COALESCE(is_trusted, true)        AS is_trusted
                FROM persistence_baselines
                WHERE tenant_id  = :tid
                  AND (host_identifier = :hid OR host_identifier IS NULL)
                ORDER BY persistence_type, identifier
                """
            ),
            {"tid": str(tenant_id), "hid": host_identifier},
        )
        return [dict(r) for r in result.mappings().all()]
    except Exception:
        logger.debug(
            "persistence_baselines table unavailable; returning empty baseline",
            exc_info=True,
        )
        return []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/pending-actions",
    response_model=PendingActionsResponse,
    summary="List pending HITL actions for a host",
    description=(
        "Returns rows consumed by the ``aisoc_pending_actions`` osquery virtual "
        "table.  The extension polls this endpoint on each table scan so operators "
        "can run ``SELECT * FROM aisoc_pending_actions`` inside osqueryi to see "
        "queued Human-in-the-Loop approvals."
    ),
)
async def list_pending_actions(
    host_identifier: str = Query(
        ...,
        description="osquery host_identifier of the requesting host",
    ),
    user: Annotated[AuthUser, Depends(require_permission("extensions:read"))],
    db: DBSession,
) -> PendingActionsResponse:
    rows = await _get_pending_actions_for_host(
        db=db,
        tenant_id=user.tenant_id,
        host_identifier=host_identifier,
    )

    actions: list[PendingAction] = []
    for row in rows:
        try:
            actions.append(
                PendingAction(
                    action_id=row["action_id"],
                    case_id=row.get("case_id"),
                    action_type=row.get("action_type") or "unknown",
                    target=row.get("target") or host_identifier,
                    requested_by=row.get("requested_by") or "system",
                    requested_at=row["requested_at"],
                    expires_at=row.get("expires_at"),
                    description=row.get("description") or "",
                )
            )
        except Exception:
            logger.warning("Skipping malformed pending action row: %s", row)

    return PendingActionsResponse(host_identifier=host_identifier, actions=actions)


@router.get(
    "/alert-cache",
    response_model=AlertCacheResponse,
    summary="Retrieve recent alerts for a host",
    description=(
        "Returns rows consumed by the ``aisoc_alert_cache`` osquery virtual "
        "table.  Defaults to the last 24 hours unless ``since`` is provided.  "
        "Useful for offline forensics when the SOC console is unreachable."
    ),
)
async def get_alert_cache(
    host_identifier: str = Query(
        ...,
        description="osquery host_identifier of the requesting host",
    ),
    since: datetime | None = Query(
        default=None,
        description=(
            "ISO-8601 timestamp; return alerts fired after this moment. "
            "Defaults to 24 hours ago."
        ),
    ),
    user: Annotated[AuthUser, Depends(require_permission("extensions:read"))],
    db: DBSession,
) -> AlertCacheResponse:
    effective_since: datetime = since or (datetime.now(UTC) - timedelta(hours=24))

    rows = await _get_alert_cache_for_host(
        db=db,
        tenant_id=user.tenant_id,
        host_identifier=host_identifier,
        since=effective_since,
    )

    alerts: list[AlertCacheEntry] = []
    for row in rows:
        try:
            alerts.append(
                AlertCacheEntry(
                    alert_id=row["alert_id"],
                    rule_id=row.get("rule_id") or "unknown",
                    severity=row.get("severity") or "info",
                    fired_at=row["fired_at"],
                    summary=row.get("summary") or "",
                    case_id=row.get("case_id"),
                )
            )
        except Exception:
            logger.warning("Skipping malformed alert cache row: %s", row)

    return AlertCacheResponse(
        host_identifier=host_identifier,
        since=effective_since,
        alerts=alerts,
    )


@router.get(
    "/persistence-baseline",
    response_model=PersistenceBaselineResponse,
    summary="Retrieve trusted persistence baseline for a host",
    description=(
        "Returns trusted persistence entries consumed by the "
        "``aisoc_attck_persistence`` virtual table.  The extension compares "
        "live persistence data (crontab, systemd units, launchd, registry Run "
        "keys) against this baseline and flags deviations as potential ATT&CK "
        "T1053 / T1543 activity.  Tenant-global entries (no host_identifier) "
        "apply to all enrolled hosts."
    ),
)
async def get_persistence_baseline(
    host_identifier: str = Query(
        ...,
        description="osquery host_identifier of the requesting host",
    ),
    user: Annotated[AuthUser, Depends(require_permission("extensions:read"))],
    db: DBSession,
) -> PersistenceBaselineResponse:
    rows = await _get_persistence_baseline(
        db=db,
        tenant_id=user.tenant_id,
        host_identifier=host_identifier,
    )

    baseline: list[PersistenceBaselineEntry] = []
    for row in rows:
        try:
            baseline.append(
                PersistenceBaselineEntry(
                    item_id=row.get("item_id") or uuid.uuid4(),
                    persistence_type=row.get("persistence_type") or "unknown",
                    identifier=row.get("identifier") or "",
                    description=row.get("description") or "",
                    mitre_technique=row.get("mitre_technique") or "",
                    is_trusted=bool(row.get("is_trusted", True)),
                )
            )
        except Exception:
            logger.warning("Skipping malformed baseline row: %s", row)

    return PersistenceBaselineResponse(
        host_identifier=host_identifier,
        baseline=baseline,
    )
