"""Pack resolver: maps a tenant to their osquery schedule config.

PR4 stub — returns a minimal baseline schedule so enrolled nodes get a
valid (non-empty) config response immediately.  The full implementation
(curated packs, YAML pack format, pack_assignment table) is delivered
in PR5.
"""
from __future__ import annotations

from app.core.config import settings


_BASELINE_QUERIES: dict[str, dict] = {
    "system_info": {
        "query": "SELECT * FROM system_info;",
        "interval": settings.default_interval_seconds,
        "snapshot": True,
    },
    "os_version": {
        "query": "SELECT * FROM os_version;",
        "interval": settings.default_interval_seconds,
        "snapshot": True,
    },
    "listening_ports": {
        "query": "SELECT pid, port, protocol, address FROM listening_ports WHERE port < 32768;",
        "interval": settings.default_interval_seconds,
    },
    "logged_in_users": {
        "query": "SELECT * FROM logged_in_users;",
        "interval": 60,
    },
}


def resolve_config(tenant_id: str) -> dict:
    """Return the osquery TLS config JSON for the given tenant.

    The config object must match the osquery TLS config response schema:
    https://osquery.readthedocs.io/en/stable/deployment/remote/#config-retrieval
    """
    return {
        "schedule": _BASELINE_QUERIES,
        "options": {
            "host_identifier": "hostname",
            "schedule_splay_percent": 10,
        },
    }
