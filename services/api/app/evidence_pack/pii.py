"""PII redaction / pseudonimization for evidence-pack exports.

Per Parecer Jurídico Nº 012/2026 § VI, ANPD prefers pseudonimização
determinística over irreversible masking ("***" patterns):

  - Determinism enables forensic correlation across exports
  - Auditability: a DPO holding the salt can de-pseudonimize on demand
  - Minimization: regulators see categories of data, not raw values

We implement HMAC-SHA256 with a per-tenant salt. The salt rotates by
tenant policy; the key-mapping (salt → original value lookup) is
held outside this module — in a vault accessible only to the DPO.

Three export modes are exposed via :class:`ExportLevel`:

  - ``INTERNAL_FORENSICS``    — raw PII, never leaves the tenant
  - ``REGULATORY_SUBMISSION`` — pseudonimized PII, goes to ANPD/BACEN
  - ``EXECUTIVE_SUMMARY``     — counts only, suitable for boards

The pseudonimization shape is ``{kind}_{hex16}``:

  >>> pseudonimize("12345678900", salt=b"t1", kind="cpf")
  'cpf_a1b2c3d4e5f60718'

where ``hex16`` is the first 16 hex chars of HMAC-SHA256(salt, value).
"""
from __future__ import annotations

import hashlib
import hmac
import re
from enum import Enum
from typing import Any


class ExportLevel(str, Enum):
    """How much PII the export carries.

    Maps to the three-tier model the advisor recommended. Compilers
    and runtimes branch on this; renderers display it in the seal
    grid so a reader instantly knows what they are looking at.
    """

    INTERNAL_FORENSICS = "internal_forensics"
    """PII integral. Internal investigations only — never sent
    outside the controller tenant."""

    REGULATORY_SUBMISSION = "regulatory_submission"
    """PII pseudonimizada via HMAC-SHA256 + salt. Default for ANPD/
    BACEN notifications."""

    EXECUTIVE_SUMMARY = "executive_summary"
    """PII removed entirely; only aggregates and counts. For board
    reporting, sales decks, partner reviews."""


# Field-name patterns the redactor recognizes as PII. The shape is
# intentionally permissive — production runtimes operating on the
# real ledger should layer schema-aware redaction on top.

_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "cpf": re.compile(r"(^|_|\.)(cpf)(\b|_|$)", re.IGNORECASE),
    "cnpj": re.compile(r"(^|_|\.)(cnpj)(\b|_|$)", re.IGNORECASE),
    "email": re.compile(r"(^|_|\.)(email|e_mail)(\b|_|$)", re.IGNORECASE),
    "phone": re.compile(r"(^|_|\.)(phone|telefone)(\b|_|$)", re.IGNORECASE),
    "rg": re.compile(r"(^|_|\.)(rg)(\b|_|$)", re.IGNORECASE),
}


def _kind_for(key: str) -> str | None:
    """Return the PII kind for a field name, or None if not PII."""
    for kind, pattern in _PII_PATTERNS.items():
        if pattern.search(key):
            return kind
    return None


def pseudonimize(value: str, *, salt: bytes, kind: str) -> str:
    """Pseudonimize a single string value deterministically.

    Args:
        value: The raw PII value (CPF, email, phone, etc).
        salt: Per-tenant salt; SHOULD be at least 32 bytes of entropy.
        kind: PII kind prefix (cpf, email, phone, cnpj, rg, ...).

    Returns:
        ``{kind}_{hex16}`` — 16 hex chars are ~64 bits, far more than
        enough to avoid collisions within a tenant.

    Raises:
        ValueError: salt is empty or shorter than 16 bytes (would
            severely weaken the HMAC).
    """
    if len(salt) < 16:
        raise ValueError("PII pseudonimization salt must be >= 16 bytes")
    digest = hmac.new(salt, value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{kind}_{digest[:16]}"


def redact_row(
    row: dict[str, Any],
    *,
    level: ExportLevel,
    salt: bytes,
) -> dict[str, Any]:
    """Apply the level's redaction policy to a single dict row.

    The function operates one level deep — sufficient for the ledger
    row shapes ``MockRuntime`` returns. Nested PII inside JSON blobs
    must be redacted before write-time; we do NOT recursively crawl
    arbitrary structures.
    """
    if level is ExportLevel.INTERNAL_FORENSICS:
        return row

    out: dict[str, Any] = {}
    for key, val in row.items():
        kind = _kind_for(key)
        if kind is None:
            out[key] = val
            continue

        if level is ExportLevel.EXECUTIVE_SUMMARY:
            # Strip the value; keep the key so downstream consumers
            # can still count "rows with email" etc.
            out[key] = "[redacted]"
            continue

        # REGULATORY_SUBMISSION: pseudonimize.
        if isinstance(val, str) and val:
            out[key] = pseudonimize(val, salt=salt, kind=kind)
        elif val is None or val == "":
            out[key] = val
        else:
            # Numeric / other — coerce to string for pseudonimization.
            out[key] = pseudonimize(str(val), salt=salt, kind=kind)
    return out


def redact_rows(
    rows: list[dict[str, Any]],
    *,
    level: ExportLevel,
    salt: bytes,
) -> list[dict[str, Any]]:
    """Vectorized helper over :func:`redact_row`."""
    return [redact_row(r, level=level, salt=salt) for r in rows]


__all__ = [
    "ExportLevel",
    "pseudonimize",
    "redact_row",
    "redact_rows",
]
