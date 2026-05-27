"""Unit tests for the Investigation Ledger chain writer — CARD-016 Item 1.

What's covered here:
  • The vendored ``merkle`` helper is byte-stable with the canonical
    serialisation in the API copy (so chains written by agents verify
    on the API side).
  • ``_build_chain_payload`` returns the deterministic field set that
    feeds into the entry_hash. Any reorder / addition here breaks
    existing historic hashes — the test pins the shape.
  • ``_lookup_chain_tail`` issues the expected SQL with the expected
    parameters.
  • ``record_event`` computes a chain link end-to-end and passes both
    ``prev_hash`` and ``entry_hash`` to the INSERT.
  • Chain-compute failure degrades gracefully to NULL hashes (Regra
    Zero — best-effort logging, never lose a row).

Real Postgres apply + multi-writer concurrency lives in
``services/agents/tests/integration/`` — out of scope here.
"""
from __future__ import annotations

import sys
import types
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_AGENTS_ROOT = Path(__file__).resolve().parents[1]
if str(_AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENTS_ROOT))


# ── Load ledger.py via importlib bypassing app.investigator.__init__ ─────
#
# The package __init__ eagerly imports the LangGraph orchestrator (which in
# turn pulls langgraph, langchain, opentelemetry, etc). For these focused
# unit tests we want ledger.py and nothing else. importlib.util lets us
# load a module by file path without running the parent package's __init__.

import importlib.util  # noqa: E402

_LEDGER_PATH = _AGENTS_ROOT / "app" / "investigator" / "ledger.py"


def _load_ledger_module():
    # Pre-create the parent packages as empty modules so `from app.security`
    # imports inside ledger.py resolve correctly. The app.security package
    # has no offending side effects so the real one loads cleanly.
    if "app" not in sys.modules:
        app_pkg = types.ModuleType("app")
        app_pkg.__path__ = [str(_AGENTS_ROOT / "app")]
        sys.modules["app"] = app_pkg
    if "app.investigator" not in sys.modules:
        inv_pkg = types.ModuleType("app.investigator")
        inv_pkg.__path__ = [str(_AGENTS_ROOT / "app" / "investigator")]
        sys.modules["app.investigator"] = inv_pkg
    spec = importlib.util.spec_from_file_location(
        "app.investigator.ledger", _LEDGER_PATH
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["app.investigator.ledger"] = mod
    spec.loader.exec_module(mod)
    return mod


ledger = _load_ledger_module()


# ── Vendored merkle stays in sync with the canonical API copy ──────────────


def test_vendored_merkle_matches_api_canonical():
    """Both files must be byte-identical except for the vendored
    header. If they diverge, chains written by the agents service
    won't verify on the API side."""
    agents_path = _AGENTS_ROOT / "app" / "security" / "merkle.py"
    api_path = (
        _AGENTS_ROOT.parents[1] / "services" / "api" / "app" / "evidence_pack" / "merkle.py"
    )
    assert agents_path.is_file()
    assert api_path.is_file()
    # Strip the leading docstring on both sides and compare bodies.
    a = agents_path.read_text(encoding="utf-8")
    b = api_path.read_text(encoding="utf-8")

    def _strip_module_docstring(src: str) -> str:
        # The module docstring is the first triple-quoted block.
        first = src.find('"""')
        assert first != -1
        end = src.find('"""', first + 3)
        return src[end + 3 :]

    assert _strip_module_docstring(a) == _strip_module_docstring(b), (
        "vendored merkle has drifted from the API canonical copy — "
        "update both in lockstep (planned: scripts/sync_vendored_merkle.py)."
    )


# ── Chain payload shape (the field set that gets hashed) ───────────────────


def test_build_chain_payload_pins_the_field_set():
    from app.investigator import ledger

    ts = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
    out = ledger._build_chain_payload(
        seq=7,
        ts=ts,
        kind="llm_call",
        agent="recon",
        summary="resumo curto",
        payload={"prompt": "x"},
        input_hash="ih",
        output_hash="oh",
        duration_ms=42,
    )
    assert set(out.keys()) == {
        "seq", "ts", "kind", "agent", "summary",
        "payload", "input_hash", "output_hash", "duration_ms",
    }, (
        "the chain payload field set is part of the canonical "
        "definition of an event hash. Adding or removing keys here "
        "invalidates every historic chain entry — review carefully."
    )
    assert out["ts"] == ts.isoformat()
    assert out["payload"] == {"prompt": "x"}


def test_build_chain_payload_truncates_summary_to_8000_chars():
    from app.investigator import ledger

    long = "a" * 12000
    out = ledger._build_chain_payload(
        seq=1, ts=datetime.utcnow(), kind="x", agent="y",
        summary=long, payload=None, input_hash=None, output_hash=None,
        duration_ms=0,
    )
    assert len(out["summary"]) == 8000


def test_build_chain_payload_handles_none_payload():
    from app.investigator import ledger

    out = ledger._build_chain_payload(
        seq=1, ts=datetime.utcnow(), kind="x", agent="y",
        summary="s", payload=None, input_hash=None, output_hash=None,
        duration_ms=0,
    )
    assert out["payload"] == {}


# ── Chain tail lookup (the SQL that finds the previous entry) ──────────────


@pytest.mark.asyncio
async def test_lookup_chain_tail_issues_expected_sql():
    from app.investigator import ledger

    tenant_id = uuid.uuid4()
    run_id = uuid.uuid4()
    fake_conn = MagicMock()
    fake_conn.fetchrow = AsyncMock(return_value=None)

    result = await ledger._lookup_chain_tail(
        fake_conn, tenant_id=tenant_id, run_id=run_id
    )
    assert result is None
    sql_arg = fake_conn.fetchrow.call_args.args[0]
    assert "investigation_events" in sql_arg
    assert "entry_hash IS NOT NULL" in sql_arg
    assert "ORDER BY seq DESC" in sql_arg
    assert fake_conn.fetchrow.call_args.args[1:] == (tenant_id, run_id)


@pytest.mark.asyncio
async def test_lookup_chain_tail_returns_entry_hash_when_present():
    from app.investigator import ledger

    fake_conn = MagicMock()
    fake_conn.fetchrow = AsyncMock(return_value={"entry_hash": "deadbeef" * 8})
    result = await ledger._lookup_chain_tail(
        fake_conn, tenant_id=uuid.uuid4(), run_id=uuid.uuid4()
    )
    assert result == "deadbeef" * 8


# ── record_event end-to-end (mocked pool) ──────────────────────────────────


@pytest.mark.asyncio
async def test_record_event_computes_chain_and_writes_both_hashes():
    """Build a fake pool/conn, call record_event, confirm the INSERT
    parameters include both prev_hash and entry_hash with the right
    shape (64-char hex)."""
    from app.investigator import ledger

    tenant_id = uuid.uuid4()
    run_id = uuid.uuid4()

    fake_conn = MagicMock()
    fake_conn.fetchrow = AsyncMock(return_value=None)  # genesis
    fake_conn.execute = AsyncMock(return_value="INSERT 0 1")

    class _Acquire:
        async def __aenter__(self):
            return fake_conn

        async def __aexit__(self, *a):
            return None

    fake_pool = MagicMock()
    fake_pool.acquire = MagicMock(return_value=_Acquire())

    with patch.object(ledger, "get_pool", AsyncMock(return_value=fake_pool)):
        with patch.object(ledger, "_set_rls_context", AsyncMock(return_value=None)):
            event_id = await ledger.record_event(
                run_id=run_id,
                tenant_id=tenant_id,
                seq=1,
                kind="llm_call",
                agent="recon",
                summary="primeira chamada",
                payload={"prompt": "x"},
            )

    assert isinstance(event_id, uuid.UUID)
    insert_args = fake_conn.execute.call_args.args
    sql, params = insert_args[0], insert_args[1:]
    assert "prev_hash, entry_hash" in sql
    # Params order from the INSERT statement:
    # 0:event_id, 1:run_id, 2:tenant_id, 3:seq, 4:ts, 5:kind, 6:agent,
    # 7:summary, 8:payload_json, 9:input_hash, 10:output_hash,
    # 11:duration_ms, 12:prev_hash, 13:entry_hash
    prev_hash, entry_hash = params[12], params[13]
    # Genesis row → prev_hash is NULL in the DB (matches the nullable
    # column in migration 046). The verifier treats NULL as genesis
    # and normalises it to the all-zero 32-byte sentinel before
    # walking the chain — see app/security/merkle.py::_normalise_prev.
    assert prev_hash is None
    assert isinstance(entry_hash, str) and len(entry_hash) == 64


@pytest.mark.asyncio
async def test_record_event_chains_two_consecutive_rows():
    """Confirm row 2 carries prev_hash = entry_hash of row 1."""
    from app.investigator import ledger
    from app.security.merkle import hash_entry

    tenant_id = uuid.uuid4()
    run_id = uuid.uuid4()

    # First call: genesis (lookup returns None).
    # Second call: lookup returns the hash from first call.
    captured: list[tuple] = []

    fake_conn = MagicMock()

    async def _fetchrow(sql, *params):
        if captured:
            return {"entry_hash": captured[-1][13]}  # last entry_hash
        return None

    async def _execute(sql, *params):
        captured.append(params)
        return "INSERT 0 1"

    fake_conn.fetchrow = AsyncMock(side_effect=_fetchrow)
    fake_conn.execute = AsyncMock(side_effect=_execute)

    class _Acquire:
        async def __aenter__(self):
            return fake_conn

        async def __aexit__(self, *a):
            return None

    fake_pool = MagicMock()
    fake_pool.acquire = MagicMock(return_value=_Acquire())

    with patch.object(ledger, "get_pool", AsyncMock(return_value=fake_pool)):
        with patch.object(ledger, "_set_rls_context", AsyncMock(return_value=None)):
            await ledger.record_event(
                run_id=run_id, tenant_id=tenant_id, seq=1,
                kind="llm_call", agent="recon", summary="row 1",
            )
            await ledger.record_event(
                run_id=run_id, tenant_id=tenant_id, seq=2,
                kind="llm_call", agent="recon", summary="row 2",
            )

    assert len(captured) == 2
    row1_entry = captured[0][13]
    row2_prev = captured[1][12]
    assert row1_entry == row2_prev, (
        "row 2's prev_hash must equal row 1's entry_hash"
    )


@pytest.mark.asyncio
async def test_record_event_degrades_to_null_hashes_on_chain_failure():
    """If chain compute raises for any reason, the row still inserts
    with NULL hashes. Logging is best-effort; we never lose the row."""
    from app.investigator import ledger

    fake_conn = MagicMock()
    fake_conn.fetchrow = AsyncMock(side_effect=RuntimeError("db went away"))
    fake_conn.execute = AsyncMock(return_value="INSERT 0 1")

    class _Acquire:
        async def __aenter__(self):
            return fake_conn

        async def __aexit__(self, *a):
            return None

    fake_pool = MagicMock()
    fake_pool.acquire = MagicMock(return_value=_Acquire())

    with patch.object(ledger, "get_pool", AsyncMock(return_value=fake_pool)):
        with patch.object(ledger, "_set_rls_context", AsyncMock(return_value=None)):
            eid = await ledger.record_event(
                run_id=uuid.uuid4(), tenant_id=uuid.uuid4(), seq=1,
                kind="llm_call", agent="recon", summary="x",
            )

    assert eid is not None  # row still inserted
    params = fake_conn.execute.call_args.args[1:]
    assert params[12] is None  # prev_hash
    assert params[13] is None  # entry_hash
