"""Tests for the investigation_events hash-chain migration — CARD-016.

We don't spin up Postgres in the unit-test layer (that's the
integration-test job). What we DO assert here:

  * The migration file lives at the expected path with the expected
    sequence number (046).
  * It is wrapped in a BEGIN/COMMIT block (so the schema change is
    atomic on apply).
  * It only ADDS columns (no DROP, no NOT NULL on existing rows) —
    Regra Zero: never break what works.
  * It declares both ``prev_hash`` and ``entry_hash`` columns.
  * The two supporting indexes are partial (``WHERE entry_hash IS NOT NULL``)
    so we don't bloat the index over the unhashed historic rows.
  * The ORM model in ``app.models.investigation`` exposes the two new
    fields so SQLAlchemy stays in sync with the schema.

Production integration coverage (real Postgres apply + chain write)
lives in ``services/api/tests/integration/`` and runs against a
container — out of scope here.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


MIGRATION_PATH = (
    _API_ROOT / "migrations" / "046_investigation_events_hash_chain.sql"
)


# ── Migration file ────────────────────────────────────────────────────────


def test_migration_file_exists():
    assert MIGRATION_PATH.is_file(), (
        f"expected migration at {MIGRATION_PATH}; was the numbering changed?"
    )


def test_migration_is_atomic_begin_commit():
    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    assert "BEGIN;" in sql, "migration must be wrapped in a transaction"
    assert "COMMIT;" in sql, "migration must end with COMMIT;"
    # BEGIN must come before COMMIT.
    assert sql.index("BEGIN;") < sql.index("COMMIT;")


def test_migration_adds_both_chain_columns():
    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS prev_hash" in sql
    assert "ADD COLUMN IF NOT EXISTS entry_hash" in sql
    # Both must be VARCHAR(64) to hold a hex SHA-256 digest.
    assert "prev_hash  VARCHAR(64)" in sql or "prev_hash VARCHAR(64)" in sql
    assert "entry_hash VARCHAR(64)" in sql


def test_migration_uses_only_additive_alters():
    """Regra Zero: no destructive operations on the live ledger table."""
    # Strip line comments so the natural-language explanation cannot
    # trip on words like "NOT NULL" appearing in the rationale.
    raw = MIGRATION_PATH.read_text(encoding="utf-8")
    code_only_lines = [
        line for line in raw.splitlines() if not line.lstrip().startswith("--")
    ]
    sql = "\n".join(code_only_lines).upper()
    forbidden_substrings = [
        "DROP COLUMN",
        "DROP TABLE",
        "TRUNCATE",
        "SET NOT NULL",  # backfill required before this is safe
    ]
    for pattern in forbidden_substrings:
        assert pattern not in sql, (
            f"migration must not contain {pattern!r}; "
            f"that would risk breaking existing data."
        )
    # ALTER COLUMN ... TYPE is also forbidden but needs a regex
    # because the two tokens may be split across whitespace.
    assert not re.search(r"\bALTER COLUMN\b[^;]*\bTYPE\b", sql), (
        "migration must not change an existing column's TYPE"
    )


def test_migration_indexes_are_partial():
    """Partial indexes over `entry_hash IS NOT NULL` keep the index
    cheap for deployments with millions of pre-hash-chain rows."""
    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    # At least two CREATE INDEX statements expected.
    indexes = re.findall(
        r"CREATE INDEX IF NOT EXISTS\s+(\w+)[\s\S]+?WHERE entry_hash IS NOT NULL",
        sql,
        flags=re.IGNORECASE,
    )
    assert len(indexes) >= 2, (
        f"expected at least 2 partial indexes filtered on entry_hash; got {indexes}"
    )


def test_migration_does_not_modify_audit_log():
    """Sanity check — the audit_log chain has its own migration (043).
    This one only touches investigation_events.

    Allow ``audit_log`` to appear in line comments (the rationale
    references migration 043 as prior art) but forbid it in any DDL
    statement.
    """
    raw = MIGRATION_PATH.read_text(encoding="utf-8")
    code_only_lines = [
        line for line in raw.splitlines() if not line.lstrip().startswith("--")
    ]
    code = "\n".join(code_only_lines).lower()
    assert "audit_log" not in code, (
        "DDL must not touch audit_log; that table has its own migration."
    )


# ── ORM model ─────────────────────────────────────────────────────────────


def test_orm_exposes_prev_hash_and_entry_hash():
    # Importing the SQLAlchemy module pulls a lot of infra; we read the
    # source directly instead, which is enough to confirm the columns
    # are declared. This avoids needing a configured DATABASE_URL just
    # to validate the model file.
    model_path = _API_ROOT / "app" / "models" / "investigation.py"
    src = model_path.read_text(encoding="utf-8")
    # The two new declarations must appear inside InvestigationEvent
    # (heuristic: between the class line and the next class line).
    event_class_idx = src.index("class InvestigationEvent(")
    next_class_idx = src.index("class InvestigationArtifact(", event_class_idx)
    event_class_src = src[event_class_idx:next_class_idx]
    assert "prev_hash:" in event_class_src, (
        "InvestigationEvent must declare prev_hash for the Merkle chain"
    )
    assert "entry_hash:" in event_class_src, (
        "InvestigationEvent must declare entry_hash for the Merkle chain"
    )
    # Both columns must be VARCHAR(64) — same width as input_hash.
    assert "String(64)" in event_class_src
