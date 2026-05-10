"""Osquery pack catalog endpoints.

Provides a read-only catalog of available AiSOC osquery packs and a
per-tenant assignment API so operators can choose which packs are pushed
to their agents.

Endpoints
---------
GET  /v1/packs                         List all available packs (catalog)
GET  /v1/packs/{pack_id}               Get a single pack with render formats
GET  /v1/packs/{pack_id}/render        Render a pack in a target format
GET  /v1/packs/assigned                List packs assigned to the calling tenant
POST /v1/packs/assign                  Assign a pack to the calling tenant
DELETE /v1/packs/assign/{pack_id}      Remove a pack assignment
GET  /v1/packs/config                  Compile all assigned packs into one osquery config blob
"""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import AuthUser, DBSession
from app.services.pack_assignment import (
    assign_pack,
    compile_osquery_config,
    get_assigned_pack_ids,
    get_assigned_packs,
    unassign_pack,
)
from app.services.pack_loader import OsqueryPack, get_pack, list_packs

router = APIRouter(prefix="/packs", tags=["packs"])

# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

RenderFormat = Literal["osquery-json", "fleetdm", "osctrl"]


class PackSummary(BaseModel):
    id: str
    name: str
    version: str
    platforms: list[str]
    description: str
    query_count: int
    has_fim: bool


class PackDetail(BaseModel):
    id: str
    name: str
    version: str
    platforms: list[str]
    description: str
    discovery: list[str]
    queries: dict
    file_paths: dict
    query_count: int
    has_fim: bool
    rendered: Optional[dict] = Field(
        default=None, description="Rendered output in the requested format"
    )


class AssignRequest(BaseModel):
    pack_id: str = Field(..., description="ID of the pack to assign")


class AssignResponse(BaseModel):
    pack_id: str
    assigned: bool
    message: str


def _to_summary(pack: OsqueryPack) -> PackSummary:
    return PackSummary(
        id=pack.id,
        name=pack.name,
        version=pack.version,
        platforms=pack.platforms,
        description=pack.description,
        query_count=len(pack.queries),
        has_fim=bool(pack.file_paths),
    )


def _to_detail(pack: OsqueryPack, render_format: Optional[RenderFormat] = None) -> PackDetail:
    rendered: Optional[dict] = None
    if render_format == "osquery-json":
        rendered = pack.to_osquery_json()
    elif render_format == "fleetdm":
        rendered = pack.to_fleetdm_json()
    elif render_format == "osctrl":
        rendered = pack.to_osctrl_json()

    return PackDetail(
        id=pack.id,
        name=pack.name,
        version=pack.version,
        platforms=pack.platforms,
        description=pack.description,
        discovery=pack.discovery,
        queries={name: q.model_dump() for name, q in pack.queries.items()},
        file_paths=pack.file_paths,
        query_count=len(pack.queries),
        has_fim=bool(pack.file_paths),
        rendered=rendered,
    )


# ---------------------------------------------------------------------------
# Catalog endpoints (no DB needed — packs live on disk)
# ---------------------------------------------------------------------------


@router.get("", response_model=list[PackSummary])
async def list_pack_catalog(
    current_user: AuthUser,
    platform: Optional[str] = Query(None, description="Filter by platform: linux | darwin | windows"),
    has_fim: Optional[bool] = Query(None, description="Filter to packs with file_paths defined"),
) -> list[PackSummary]:
    """Return the full AiSOC pack catalog."""
    packs = list_packs()
    if platform:
        packs = [p for p in packs if platform in p.platforms]
    if has_fim is not None:
        packs = [p for p in packs if bool(p.file_paths) == has_fim]
    return [_to_summary(p) for p in packs]


@router.get("/assigned", response_model=list[PackSummary])
async def list_assigned_packs(
    current_user: AuthUser,
    session: DBSession,
) -> list[PackSummary]:
    """Return packs currently assigned to the calling tenant."""
    tenant_id = current_user.tenant_id
    packs = await get_assigned_packs(session, tenant_id)
    return [_to_summary(p) for p in packs]


@router.get("/config")
async def get_osquery_config(
    current_user: AuthUser,
    session: DBSession,
) -> dict:
    """Compile all packs assigned to the tenant into a single osquery config blob."""
    tenant_id = current_user.tenant_id
    packs = await get_assigned_packs(session, tenant_id)
    return compile_osquery_config(packs)


@router.post("/assign", response_model=AssignResponse)
async def assign_pack_to_tenant(
    body: AssignRequest,
    current_user: AuthUser,
    session: DBSession,
) -> AssignResponse:
    """Assign a pack to the calling tenant."""
    tenant_id = current_user.tenant_id
    ok = await assign_pack(session, tenant_id, body.pack_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Pack '{body.pack_id}' not found in catalog")
    return AssignResponse(
        pack_id=body.pack_id,
        assigned=True,
        message=f"Pack '{body.pack_id}' assigned to tenant '{tenant_id}'",
    )


@router.delete("/assign/{pack_id}", status_code=204)
async def unassign_pack_from_tenant(
    pack_id: str,
    current_user: AuthUser,
    session: DBSession,
) -> None:
    """Remove a pack assignment from the calling tenant."""
    tenant_id = current_user.tenant_id
    await unassign_pack(session, tenant_id, pack_id)


@router.get("/{pack_id}", response_model=PackDetail)
async def get_pack_detail(
    pack_id: str,
    current_user: AuthUser,
    format: Optional[RenderFormat] = Query(None, description="Render the pack in this format"),
) -> PackDetail:
    """Return full detail for a single pack, optionally rendered."""
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack '{pack_id}' not found")
    return _to_detail(pack, render_format=format)


@router.get("/{pack_id}/render")
async def render_pack(
    pack_id: str,
    current_user: AuthUser,
    format: RenderFormat = Query("osquery-json", description="Target render format"),
) -> dict:
    """Render a pack in the specified format without returning full metadata."""
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack '{pack_id}' not found")
    if format == "osquery-json":
        return pack.to_osquery_json()
    if format == "fleetdm":
        return pack.to_fleetdm_json()
    return pack.to_osctrl_json()
