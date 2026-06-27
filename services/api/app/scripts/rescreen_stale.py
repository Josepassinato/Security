"""Re-screen counterparties stuck on an older sanctions-list build (Phase 3 cron).

Run daily (or on a list-update webhook). For each tenant, asks OpenSanctions for
the current build of the dataset and re-screens every counterparty whose latest
decision used an older build — appending fresh, attributed, chained records.

    OPENSANCTIONS_API_KEY=... python -m app.scripts.rescreen_stale
    OPENSANCTIONS_API_KEY=... python -m app.scripts.rescreen_stale --tenant <uuid>

Exit 0 always (idempotent maintenance job); prints a per-tenant summary.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.screening_decision import ScreeningDecision
from app.screening.opensanctions_client import OpenSanctionsClient
from app.screening.rescreen import rescreen_tenant

logger = logging.getLogger("rescreen_stale")
logging.basicConfig(level=logging.INFO, format="%(message)s")


async def _run(dsn: str, tenant: str | None, dataset: str, threshold: int) -> int:
    key = os.getenv("OPENSANCTIONS_API_KEY")
    if not key:
        logger.error("OPENSANCTIONS_API_KEY not set — cannot re-screen")
        return 2
    client = OpenSanctionsClient(key)
    engine = create_async_engine(dsn)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as db:
            if tenant:
                tenants = [tenant]
            else:
                result = await db.execute(select(ScreeningDecision.tenant_id).distinct())
                tenants = [row[0] for row in result]
            for tid in tenants:
                summary = await rescreen_tenant(db, client, tenant_id=tid, list_dataset=dataset, threshold=threshold)
                logger.info(
                    "tenant %s: build=%s counterparties=%d stale=%d rescreened=%d",
                    tid,
                    summary["current_version"],
                    summary["counterparties"],
                    summary["stale"],
                    summary["rescreened"],
                )
    finally:
        await engine.dispose()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Re-screen stale counterparties against the current list build.")
    parser.add_argument("--tenant", help="Only this tenant_id (UUID). Default: all.")
    parser.add_argument("--dataset", default="us_ofac_sdn")
    parser.add_argument("--threshold", type=int, default=85)
    parser.add_argument("--dsn", default=str(settings.DATABASE_URL))
    args = parser.parse_args(argv)
    return asyncio.run(_run(args.dsn, args.tenant, args.dataset, args.threshold))


if __name__ == "__main__":
    sys.exit(main())
