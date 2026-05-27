"""Merkle hash chain helpers — VENDORED from services/api.

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
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

GENESIS_PREV_HASH = b"\x00" * 32


def build_investigation_event_chain_payload(
    *,
    seq: int,
    ts,  # datetime
    kind: str,
    agent: str,
    summary: str,
    payload: dict | None,
    input_hash: str | None,
    output_hash: str | None,
    duration_ms: int,
) -> dict:
    """Canonical field set hashed for ``investigation_events`` rows.

    Used by BOTH the writer (services/agents/app/investigator/ledger.py)
    and the verifier (services/api/app/api/v1/endpoints/investigations.py
    /verify-chain). The two must agree byte-for-byte on what goes into
    each row's hash, otherwise the verifier will see a "broken" chain
    where the writer recorded a valid one.

    KEEP THIS STABLE across versions. Adding/removing/reordering keys
    here invalidates every historic hash; an auditor verifying a chain
    written before the change sees an immediate diff and the artifact
    loses its defensibility. If you must evolve this, version the
    schema (``schema_version`` field) so the verifier can dispatch on
    the row's stored version.
    """
    return {
        "seq": seq,
        "ts": ts.isoformat(),
        "kind": kind,
        "agent": agent,
        "summary": summary[:8000],
        "payload": payload or {},
        "input_hash": input_hash,
        "output_hash": output_hash,
        "duration_ms": duration_ms,
    }


@dataclass(frozen=True)
class HashChainEntry:
    """Result of hashing one ledger row into the chain."""

    prev_hash_hex: str
    """Hex of the previous row's ``entry_hash``. 64 chars."""

    entry_hash_hex: str
    """Hex of THIS row's hash. 64 chars."""

    canonical_payload: bytes
    """The exact bytes that were hashed. Stored alongside for auditor
    re-verification — if we change canonicalisation later, the auditor
    can still recompute against the bytes we originally signed."""


# ---------------------------------------------------------------------------
# Canonicalisation
# ---------------------------------------------------------------------------


def canonical_json(payload: dict[str, Any]) -> bytes:
    """Stable JSON serialisation suitable for hashing.

    Sorted keys, no extra whitespace, UTF-8 encoded.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def hash_entry(
    *,
    prev_entry_hash: bytes | str | None,
    row: dict[str, Any],
) -> HashChainEntry:
    """Compute the next chain entry.

    Args:
        prev_entry_hash: 32 raw bytes, 64-char hex string, or ``None``
            (genesis). The genesis row gets a zero-filled 32-byte prev.
        row: The ledger row's payload as a dict. Must be JSON-serialisable.

    Returns:
        :class:`HashChainEntry` with the prev hash, the new entry hash
        (both as hex), and the canonical bytes that were hashed.
    """
    prev = _normalise_prev(prev_entry_hash)
    payload = canonical_json(row)
    h = hashlib.sha256()
    h.update(prev)
    h.update(payload)
    entry_hash = h.digest()
    return HashChainEntry(
        prev_hash_hex=prev.hex(),
        entry_hash_hex=entry_hash.hex(),
        canonical_payload=payload,
    )


def verify_chain(entries: list[dict[str, Any]]) -> tuple[bool, int | None]:
    """Walk a chain of ledger rows and confirm every link.

    Each ``entry`` in ``entries`` is the materialised ledger row,
    including the stored ``prev_hash`` and ``entry_hash`` columns.

    Args:
        entries: Ledger rows in insertion order. Each row must include
            the keys ``prev_hash``, ``entry_hash``, and ``payload``.

    Returns:
        ``(True, None)`` when every entry hashes to its stored
        ``entry_hash`` AND the stored ``prev_hash`` matches the previous
        entry's ``entry_hash``.

        ``(False, idx)`` when verification fails — ``idx`` points at
        the row that breaks the chain. The caller is responsible for
        surfacing that to the operator.
    """
    expected_prev: bytes = GENESIS_PREV_HASH
    for idx, entry in enumerate(entries):
        stored_prev = _normalise_prev(entry["prev_hash"])
        if stored_prev != expected_prev:
            return False, idx
        recomputed = hash_entry(
            prev_entry_hash=expected_prev,
            row=entry["payload"],
        )
        if recomputed.entry_hash_hex != entry["entry_hash"]:
            return False, idx
        expected_prev = bytes.fromhex(entry["entry_hash"])
    return True, None


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _normalise_prev(prev: bytes | str | None) -> bytes:
    if prev is None:
        return GENESIS_PREV_HASH
    if isinstance(prev, bytes):
        if len(prev) != 32:
            raise ValueError(f"prev_entry_hash must be 32 bytes, got {len(prev)}")
        return prev
    if isinstance(prev, str):
        if len(prev) != 64:
            raise ValueError(
                f"prev_entry_hash hex must be 64 chars, got {len(prev)}"
            )
        return bytes.fromhex(prev)
    raise TypeError(f"unsupported prev_entry_hash type: {type(prev).__name__}")
