#!/usr/bin/env python3
"""Push normalized BOTS v3 events to Quarry ingest.

The real ingest endpoint publishes into Kafka. Use --dry-run while the Quarry
runtime is not active or when validating batches on a shared VPS.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

DEFAULT_TENANT = "00000000-0000-0000-0000-000000000001"
DEFAULT_CONNECTOR_ID = "bots-v3-wayne-demo"
DEFAULT_CONNECTOR_TYPE = "bots-v3"
DEFAULT_SOURCE_FORMAT = "botsv3_normalized_json"
DEFAULT_INPUT = Path("datasets/bots-v3/normalized/botsv3_events.jsonl.gz")


def default_ingest_url() -> str:
    base = os.getenv("INGEST_SERVICE_URL", "http://localhost:8080").rstrip("/")
    return f"{base}/v1/ingest/batch"


def read_jsonl(path: Path, *, limit: int | None = None, skip: int = 0) -> Iterable[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    emitted = 0
    seen = 0
    with opener(path, "rt", encoding="utf-8") as fh:  # type: ignore[arg-type]
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            seen += 1
            if seen <= skip:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid JSON in {path}:{line_no}: {exc}") from exc
            emitted += 1
            if limit is not None and emitted >= limit:
                break


def batched(events: Iterable[dict], size: int) -> Iterable[list[dict]]:
    batch: list[dict] = []
    for event in events:
        batch.append(event)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def post_batch(
    *,
    url: str,
    tenant_id: str,
    connector_id: str,
    connector_type: str,
    source_format: str,
    events: list[dict],
    dry_run: bool,
) -> dict:
    if dry_run:
        return {"accepted": len(events), "rejected": 0, "dry_run": True}

    payload = json.dumps(
        {
            "connector_id": connector_id,
            "connector_type": connector_type,
            "source_format": source_format,
            "events": events,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "X-Tenant-ID": tenant_id},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {"accepted": len(events), "rejected": 0}
    except urllib.error.HTTPError as exc:
        preview = exc.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"ingest returned HTTP {exc.code}: {preview}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"ingest service unreachable at {url}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Import normalized BOTS v3 JSONL into Quarry ingest")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--ingest-url", default=default_ingest_url())
    parser.add_argument("--tenant-id", default=DEFAULT_TENANT)
    parser.add_argument("--connector-id", default=DEFAULT_CONNECTOR_ID)
    parser.add_argument("--connector-type", default=DEFAULT_CONNECTOR_TYPE)
    parser.add_argument("--source-format", default=DEFAULT_SOURCE_FORMAT)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--limit", type=int, default=0, help="Optional event limit for tests")
    parser.add_argument("--skip", type=int, default=0, help="Skip this many events before importing")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.batch_size < 1:
        raise SystemExit("--batch-size must be >= 1")
    if not args.input.exists():
        raise SystemExit(f"input file not found: {args.input}")

    accepted = 0
    rejected = 0
    batches = 0
    for batch in batched(read_jsonl(args.input, limit=args.limit or None, skip=args.skip), args.batch_size):
        result = post_batch(
            url=args.ingest_url,
            tenant_id=args.tenant_id,
            connector_id=args.connector_id,
            connector_type=args.connector_type,
            source_format=args.source_format,
            events=batch,
            dry_run=args.dry_run,
        )
        accepted += int(result.get("accepted", len(batch)))
        rejected += int(result.get("rejected", 0))
        batches += 1
        if batches % 100 == 0:
            print(json.dumps({"batches": batches, "accepted": accepted, "rejected": rejected}))

    print(
        json.dumps(
            {
                "status": "ok",
                "dry_run": args.dry_run,
                "input": str(args.input),
                "batches": batches,
                "skipped": args.skip,
                "accepted": accepted,
                "rejected": rejected,
                "connector_id": args.connector_id,
                "connector_type": args.connector_type,
                "source_format": args.source_format,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
