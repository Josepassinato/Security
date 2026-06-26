"""Verify the tamper-evident hash chain of ``screening_decisions``.

This is the F6 artifact: the independent verifier that turns every screening
decision from "claim" into "evidence". Anyone — an examiner, an auditor, an
incident responder — can run it against the live DB (or a CSV/JSON export) and
prove that no decision was deleted, reordered, or silently rewritten since it
was recorded.

Demo (the acceptance criterion):

    # 1. chain intact
    python -m app.scripts.verify_screening_chain --tenant <uuid>
    #    → ✓ tenant <uuid>: chain INTACT (N decisions)

    # 2. a privileged operator forges history (DISABLE TRIGGER + UPDATE)
    # 3. re-run → the verifier accuses the break and points at the row:
    #    ✗ tenant <uuid>: chain BROKEN at index K — entry_hash mismatch
    #      offending row id=<uuid> seq/created_at=<...>

Exit code is 0 when every tenant's chain verifies, 1 when any chain is broken —
so it drops cleanly into CI or a cron integrity check.

Why asyncpg + a jsonb codec: the writer computes ``entry_hash`` over the Python
dict form of ``engine_raw_result``. asyncpg returns JSONB as raw text by
default, which would canonicalise differently and report a false break. We
register a json.loads decoder so the verifier hashes the same shape the writer
sealed.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from collections import defaultdict
from typing import Any

import asyncpg

from app.core.config import settings
from app.scripts.run_migrations import _asyncpg_dsn
from app.services.screening_hash import verify_chain

logger = logging.getLogger("verify_screening_chain")
logging.basicConfig(level=logging.INFO, format="%(message)s")

_COLUMNS = (
    "id, tenant_id, case_id, counterparty_name, counterparty_normalized, "
    "counterparty_id, counterparty_id_type, counterparty_jurisdiction, "
    "screening_trigger, matching_engine, list_of_record, list_source, "
    "list_dataset, list_version, list_release_date, engine_raw_result, "
    "match_score, scoring_rule_version, decision, disposition, human_reviewer, "
    "rationale, screened_at, created_at, prev_hash, entry_hash"
)


async def _connect(dsn: str) -> asyncpg.Connection:
    bare_dsn, kwargs = _asyncpg_dsn(dsn)
    conn = await asyncpg.connect(bare_dsn, **kwargs)
    # Match the writer's hashed shape: JSONB → dict, not raw text.
    await conn.set_type_codec(
        "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )
    return conn


async def _run(dsn: str, tenant: str | None) -> int:
    conn = await _connect(dsn)
    try:
        where = "WHERE tenant_id = $1" if tenant else ""
        params: tuple[Any, ...] = (tenant,) if tenant else ()
        rows = await conn.fetch(
            f"SELECT {_COLUMNS} FROM screening_decisions {where} "
            f"ORDER BY tenant_id, created_at ASC, id ASC",
            *params,
        )
    finally:
        await conn.close()

    by_tenant: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_tenant[r["tenant_id"]].append(dict(r))

    if not by_tenant:
        logger.info("no screening_decisions found for the given scope")
        return 0

    broken = 0
    for tid, tenant_rows in by_tenant.items():
        ok, idx, reason = verify_chain(tenant_rows)
        if ok:
            logger.info("✓ tenant %s: chain INTACT (%d decisions)", tid, len(tenant_rows))
        else:
            broken += 1
            bad = tenant_rows[idx] if idx is not None and idx < len(tenant_rows) else None
            logger.error(
                "✗ tenant %s: chain BROKEN at index %s — %s", tid, idx, reason
            )
            if bad is not None:
                logger.error(
                    "  offending row id=%s created_at=%s counterparty=%r",
                    bad.get("id"), bad.get("created_at"), bad.get("counterparty_name"),
                )
    return 1 if broken else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify screening_decisions hash chain.")
    parser.add_argument("--tenant", help="Verify only this tenant_id (UUID). Default: all.")
    parser.add_argument(
        "--dsn",
        default=str(settings.DATABASE_URL),
        help="Postgres DSN. Default: settings.DATABASE_URL.",
    )
    args = parser.parse_args(argv)
    return asyncio.run(_run(args.dsn, args.tenant))


if __name__ == "__main__":
    sys.exit(main())
