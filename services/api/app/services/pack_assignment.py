"""Pack assignment service.

Manages which osquery packs are assigned to which tenants.  Assignments are
persisted in a Postgres table ``pack_assignments`` (created by Alembic migration
``add_pack_assignments``) and cached in-process for fast read paths.

The service intentionally does **not** own the database session; callers pass an
``AsyncSession`` so the operation participates in the caller's transaction.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import Column, String, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pack_loader import OsqueryPack, get_pack, list_packs

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SQL helpers (raw text rather than ORM to avoid migration complexity)
# ---------------------------------------------------------------------------

_ENSURE_TABLE = text(
    """
    CREATE TABLE IF NOT EXISTS pack_assignments (
        tenant_id  TEXT NOT NULL,
        pack_id    TEXT NOT NULL,
        assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (tenant_id, pack_id)
    )
    """
)

_LIST_ASSIGNED = text(
    "SELECT pack_id FROM pack_assignments WHERE tenant_id = :tenant_id"
)

_ASSIGN = text(
    """
    INSERT INTO pack_assignments (tenant_id, pack_id)
    VALUES (:tenant_id, :pack_id)
    ON CONFLICT (tenant_id, pack_id) DO NOTHING
    """
)

_UNASSIGN = text(
    """
    DELETE FROM pack_assignments
    WHERE tenant_id = :tenant_id AND pack_id = :pack_id
    """
)


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def ensure_table(session: AsyncSession) -> None:
    """Create the pack_assignments table if it does not exist yet."""
    await session.execute(_ENSURE_TABLE)
    await session.commit()


async def get_assigned_pack_ids(
    session: AsyncSession, tenant_id: str
) -> list[str]:
    """Return all pack_ids assigned to *tenant_id*."""
    result = await session.execute(_LIST_ASSIGNED, {"tenant_id": tenant_id})
    return [row[0] for row in result.fetchall()]


async def get_assigned_packs(
    session: AsyncSession, tenant_id: str
) -> list[OsqueryPack]:
    """Return full :class:`OsqueryPack` objects assigned to *tenant_id*."""
    ids = await get_assigned_pack_ids(session, tenant_id)
    packs: list[OsqueryPack] = []
    for pid in ids:
        pack = get_pack(pid)
        if pack:
            packs.append(pack)
        else:
            logger.warning(
                "Pack %r assigned to tenant %r but YAML file not found", pid, tenant_id
            )
    return sorted(packs, key=lambda p: p.id)


async def assign_pack(
    session: AsyncSession, tenant_id: str, pack_id: str
) -> bool:
    """Assign *pack_id* to *tenant_id*.  Returns False if pack does not exist."""
    if get_pack(pack_id) is None:
        return False
    await session.execute(_ASSIGN, {"tenant_id": tenant_id, "pack_id": pack_id})
    return True


async def unassign_pack(
    session: AsyncSession, tenant_id: str, pack_id: str
) -> None:
    """Remove a pack assignment.  No-op if not assigned."""
    await session.execute(_UNASSIGN, {"tenant_id": tenant_id, "pack_id": pack_id})


def compile_osquery_config(packs: list[OsqueryPack]) -> dict:
    """Compile *packs* into a single osquery configuration JSON blob.

    The returned dict is suitable for serving directly to an osquery agent
    (``/config`` endpoint) or embedding in an osctrl / FleetDM push.
    """
    merged_packs: dict[str, dict] = {}
    merged_file_paths: dict[str, list[str]] = {}

    for pack in packs:
        merged_packs[pack.id] = pack.to_osquery_json()
        for group, paths in pack.file_paths.items():
            existing = merged_file_paths.setdefault(group, [])
            for p in paths:
                if p not in existing:
                    existing.append(p)

    config: dict = {"packs": merged_packs}
    if merged_file_paths:
        config["file_paths"] = merged_file_paths
    return config
