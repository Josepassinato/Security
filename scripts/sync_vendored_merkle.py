#!/usr/bin/env python3
"""Drift guard for the vendored ``merkle.py`` between API and agents.

The Investigation Ledger Merkle chain is written by the agents service
and verified by the API service. Both sides MUST agree byte-for-byte on
the canonical JSON serialisation and the SHA-256 hashing — if they
drift the verifier will report every chain as broken even when the
data is intact.

The pattern mirrors ``scripts/sync_vendored_narrative.py`` (referenced
in AGENTS.md): the canonical implementation lives in the API service,
the agents service keeps a verbatim copy under
``services/agents/app/security/merkle.py`` with a vendored header.

Usage::

    python3 scripts/sync_vendored_merkle.py            # check only (CI mode)
    python3 scripts/sync_vendored_merkle.py --write    # overwrite the vendored copy

CI mode exits non-zero on drift so a PR that changes one side without
the other cannot land.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CANONICAL = REPO / "services" / "api" / "app" / "evidence_pack" / "merkle.py"
VENDORED = REPO / "services" / "agents" / "app" / "security" / "merkle.py"


VENDOR_HEADER = '''"""Merkle hash chain helpers — VENDORED from services/api.

The canonical implementation lives at
``services/api/app/evidence_pack/merkle.py``. We vendor the pure
helpers here so the agents service can hash + chain rows on the
INSERT path without importing from ``services.api`` (separate
service, separate venv, separate deploy unit).

Mirror the credential_vault / sovereign_healthcheck pattern: keep
the two copies byte-identical (modulo this header). If you change
the canonicalisation or the digest algorithm, you MUST update both
sides in lockstep — the agents service writes, the API service
verifies, and they have to agree on what "this row's hash" means.

Stay-in-sync helper (THIS FILE):
    scripts/sync_vendored_merkle.py — diff the two files and fail
    CI on drift. Run with ``--write`` to overwrite the vendored
    copy from the canonical source.
"""
'''


def _strip_module_docstring(src: str) -> str:
    """Return ``src`` with the leading triple-quoted module docstring removed."""
    first = src.find('"""')
    if first == -1:
        return src
    end = src.find('"""', first + 3)
    if end == -1:
        return src
    return src[end + 3 :]


def _vendored_body() -> str:
    """The body the vendored file SHOULD contain (header + canonical body)."""
    canonical_src = CANONICAL.read_text(encoding="utf-8")
    body = _strip_module_docstring(canonical_src)
    return VENDOR_HEADER + body.lstrip()


def check() -> int:
    """Return 0 if vendored == expected, 1 if drift detected."""
    if not CANONICAL.is_file():
        print(f"FAIL: canonical missing at {CANONICAL}", file=sys.stderr)
        return 2
    if not VENDORED.is_file():
        print(f"FAIL: vendored missing at {VENDORED}", file=sys.stderr)
        return 2
    expected = _vendored_body()
    actual = VENDORED.read_text(encoding="utf-8")
    if actual == expected:
        print(f"OK: {VENDORED.relative_to(REPO)} matches canonical")
        return 0
    # Locate the first divergence — useful in CI logs.
    for i, (a, b) in enumerate(zip(actual, expected)):
        if a != b:
            head = actual[max(0, i - 40) : i + 40]
            print(
                f"FAIL: drift at byte {i} (showing 80-char window):\n{head!r}",
                file=sys.stderr,
            )
            break
    else:
        # One file is a prefix of the other — length mismatch.
        print(
            f"FAIL: length mismatch (vendored={len(actual)} expected={len(expected)})",
            file=sys.stderr,
        )
    print(
        f"\nRun `python3 {Path(__file__).relative_to(REPO)} --write` to refresh "
        f"the vendored copy from {CANONICAL.relative_to(REPO)}.",
        file=sys.stderr,
    )
    return 1


def write() -> int:
    """Overwrite the vendored file with header + canonical body. Returns 0."""
    expected = _vendored_body()
    VENDORED.write_text(expected, encoding="utf-8")
    print(f"wrote {VENDORED.relative_to(REPO)} ({len(expected)} bytes)")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="overwrite the vendored copy from the canonical source",
    )
    args = parser.parse_args(argv)
    if args.write:
        return write()
    return check()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
