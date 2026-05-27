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

Stay-in-sync helper (planned, mirror of
``scripts/sync_vendored_narrative.py``):
    scripts/sync_vendored_merkle.py — diff the two files and fail
    CI on drift. Not yet implemented; for the MVP, change both
    files in the same PR.

────────────────────────────────────────────────────────────────────

The current ledger is append-only Postgres. Item 1 of CARD-016 raises
it to *evidence-grade*: every row gets a ``prev_hash`` and an
``entry_hash`` so a fiscalização can prove the chain has not been
tampered with after the fact.

This module is **pure**: it does not touch Postgres. The caller passes
in the previous-row hash and the current row's stable serialisation;
we compute the next ``entry_hash`` and return it. The migration that
adds the columns and the trigger that calls these helpers live with
the ledger module (services/agents/app/investigator/ledger.py), not
here — keeping the math testable in isolation.

Algorithm
---------

* Serialise the row to a **canonical JSON** form (sorted keys, no
  whitespace, ``ensure_ascii=False``). This is what gets hashed; not
  Python ``str()`` (which is unstable across versions) and not Postgres
  ``ROW()`` (which depends on column order at write time).
* ``entry_hash = SHA-256(prev_hash || canonical_row_bytes)``.
* The genesis row uses ``prev_hash = b"\\x00" * 32``.
* All hashes are 32-byte hex strings (64 chars) in storage; we use the
  raw bytes form internally for the concatenation.

Why SHA-256 (and not SHA-3 or BLAKE3): SHA-256 is what RFC 3161
(ICP-Brasil TSA) signs, what Bacen's own published verification tools
expect, and what every Big-4 audit team knows how to verify.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

GENESIS_PREV_HASH = b"\x00" * 32


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
