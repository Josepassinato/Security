"""Pack loader service.

Reads AiSOC-flavored osquery pack YAML files from the ``packs/`` directory at
the repository root, validates them against the ``OsqueryPack`` Pydantic schema,
and caches the results in memory with mtime-based invalidation so repeated API
calls are cheap.

The loader is intentionally read-only; assignment of packs to tenants is handled
by :mod:`app.services.pack_assignment`.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

PACKS_DIR = Path(__file__).resolve().parents[5] / "packs"


class QueryDef(BaseModel):
    sql: str
    interval: int = Field(ge=1, default=60)
    severity: str = Field(default="info", pattern=r"^(info|low|medium|high)$")
    description: str = ""
    mitre: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class OsqueryPack(BaseModel):
    id: str
    name: str
    version: str = "1.0.0"
    platforms: list[str] = Field(default_factory=lambda: ["linux", "darwin"])
    description: str = ""
    discovery: list[str] = Field(default_factory=list)
    queries: dict[str, QueryDef] = Field(default_factory=dict)
    file_paths: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("platforms", mode="before")
    @classmethod
    def _coerce_platforms(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [v]
        return v  # type: ignore[return-value]

    def to_osquery_json(self) -> dict:
        """Compile pack to canonical osquery JSON shape."""
        schedule: dict[str, dict] = {}
        for qname, qdef in self.queries.items():
            schedule[qname] = {
                "query": qdef.sql.strip(),
                "interval": qdef.interval,
                "description": qdef.description,
            }
        return {
            "queries": schedule,
            "discovery": self.discovery,
            "platform": ",".join(self.platforms) if self.platforms else None,
            "version": self.version,
        }

    def to_fleetdm_json(self) -> dict:
        """Render in FleetDM pack format."""
        queries: list[dict] = []
        for qname, qdef in self.queries.items():
            queries.append(
                {
                    "name": qname,
                    "query": qdef.sql.strip(),
                    "interval": qdef.interval,
                    "description": qdef.description,
                    "platform": ",".join(self.platforms),
                }
            )
        return {"name": self.id, "queries": queries}

    def to_osctrl_json(self) -> dict:
        """Render in osctrl schedule format (compatible with osctrl packs API)."""
        schedule: dict[str, dict] = {}
        for qname, qdef in self.queries.items():
            schedule[qname] = {
                "query": qdef.sql.strip(),
                "interval": qdef.interval,
                "description": qdef.description,
                "platform": ",".join(self.platforms),
                "version": "",
                "shard": 0,
            }
        return {"schedule": schedule, "discovery": self.discovery}


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class _PackCache:
    """In-memory pack cache with mtime-based invalidation."""

    def __init__(self) -> None:
        self._packs: dict[str, OsqueryPack] = {}
        self._mtimes: dict[str, float] = {}
        self._loaded_at: float = 0.0
        self._ttl: float = 30.0  # refresh every 30 s

    def _pack_path(self, pack_id: str) -> Path:
        return PACKS_DIR / f"{pack_id}.yaml"

    def _load_file(self, path: Path) -> Optional[OsqueryPack]:
        try:
            raw = yaml.safe_load(path.read_text())
            return OsqueryPack.model_validate(raw)
        except Exception as exc:
            logger.warning("Failed to load pack %s: %s", path.name, exc)
            return None

    def _needs_refresh(self) -> bool:
        return (time.monotonic() - self._loaded_at) > self._ttl

    def load_all(self) -> dict[str, OsqueryPack]:
        if not self._needs_refresh():
            return self._packs

        if not PACKS_DIR.exists():
            logger.warning("Packs directory not found: %s", PACKS_DIR)
            return {}

        fresh: dict[str, OsqueryPack] = {}
        for path in PACKS_DIR.glob("*.yaml"):
            mtime = path.stat().st_mtime
            pack_id = path.stem
            cached_mtime = self._mtimes.get(pack_id)
            if cached_mtime == mtime and pack_id in self._packs:
                fresh[pack_id] = self._packs[pack_id]
                continue
            pack = self._load_file(path)
            if pack:
                fresh[pack.id] = pack
                self._mtimes[pack.id] = mtime

        self._packs = fresh
        self._loaded_at = time.monotonic()
        return self._packs

    def get(self, pack_id: str) -> Optional[OsqueryPack]:
        packs = self.load_all()
        return packs.get(pack_id)


_cache = _PackCache()


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def list_packs() -> list[OsqueryPack]:
    """Return all loaded packs sorted by id."""
    return sorted(_cache.load_all().values(), key=lambda p: p.id)


def get_pack(pack_id: str) -> Optional[OsqueryPack]:
    """Return a single pack by id, or None if not found."""
    return _cache.get(pack_id)
