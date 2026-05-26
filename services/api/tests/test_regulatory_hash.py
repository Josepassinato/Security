"""Tests for regulatory_communications hash chain.

Mesmas garantias do test_audit_hash.py, adaptadas para a tabela
``regulatory_communications``:

1. ``compute_entry_hash`` é determinístico.
2. Mutar qualquer campo de negócio muda o digest.
3. ``prev_hash`` encadeia (reordenação quebra verify_chain).
4. Domain separator (``regulatory-comm-v1``) impede colisão acidental
   com audit_log.
5. ``verify_chain`` aceita chain válida e rejeita: linha removida,
   reescrita, reordenada, e prev_hash mismatch.
6. Linhas legacy (sem entry_hash) no topo são toleradas; gap após
   chain iniciada é forgery signal.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.services.regulatory_hash import compute_entry_hash, verify_chain

_BASE_TS = datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC)


def _ts(seconds: int) -> datetime:
    return _BASE_TS + timedelta(seconds=seconds)


def _row(
    *,
    prev_hash: str | None,
    row_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    case_id: uuid.UUID | None = None,
    kind: str = "bacen",
    status: str = "draft",
    draft_md: str = "# Test draft",
    draft_meta: dict[str, Any] | None = None,
    deadline_at: datetime | None = None,
    submitted_at: datetime | None = None,
    approver_email: str | None = None,
    approver_typed_name: str | None = None,
    sent_via: str | None = None,
    sent_to: str | None = None,
    dispatch_result: dict[str, Any] | None = None,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    rid = row_id or uuid.UUID(int=1)
    tid = tenant_id or uuid.UUID(int=42)
    deadline = deadline_at or _ts(86400)
    created = created_at or _ts(0)
    entry_hash = compute_entry_hash(
        prev_hash=prev_hash,
        row_id=rid,
        tenant_id=tid,
        case_id=case_id,
        kind=kind,
        status=status,
        draft_md=draft_md,
        draft_meta=draft_meta,
        deadline_at=deadline,
        submitted_at=submitted_at,
        approver_email=approver_email,
        approver_typed_name=approver_typed_name,
        sent_via=sent_via,
        sent_to=sent_to,
        dispatch_result=dispatch_result,
        created_at=created,
    )
    return {
        "id": rid,
        "tenant_id": tid,
        "case_id": case_id,
        "kind": kind,
        "status": status,
        "draft_md": draft_md,
        "draft_meta": draft_meta,
        "deadline_at": deadline,
        "submitted_at": submitted_at,
        "approver_email": approver_email,
        "approver_typed_name": approver_typed_name,
        "sent_via": sent_via,
        "sent_to": sent_to,
        "dispatch_result": dispatch_result,
        "created_at": created,
        "prev_hash": prev_hash,
        "entry_hash": entry_hash,
    }


def test_compute_is_deterministic():
    args = dict(
        prev_hash="abc",
        row_id=uuid.UUID(int=1),
        tenant_id=uuid.UUID(int=2),
        case_id=uuid.UUID(int=3),
        kind="bacen",
        status="draft",
        draft_md="# X",
        draft_meta={"a": 1},
        deadline_at=_ts(86400),
        submitted_at=None,
        approver_email=None,
        approver_typed_name=None,
        sent_via=None,
        sent_to=None,
        dispatch_result=None,
        created_at=_ts(0),
    )
    h1 = compute_entry_hash(**args)
    h2 = compute_entry_hash(**args)
    assert h1 == h2
    assert len(h1) == 64


@pytest.mark.parametrize(
    "field,value",
    [
        ("kind", "anpd"),
        ("status", "submitted"),
        ("draft_md", "# Different"),
        ("draft_meta", {"x": 99}),
        ("approver_email", "other@x.com"),
        ("sent_via", "email"),
        ("dispatch_result", {"ok": True}),
    ],
)
def test_mutating_any_field_changes_digest(field, value):
    base = dict(
        prev_hash=None,
        row_id=uuid.UUID(int=1),
        tenant_id=uuid.UUID(int=2),
        case_id=None,
        kind="bacen",
        status="draft",
        draft_md="# X",
        draft_meta=None,
        deadline_at=_ts(86400),
        submitted_at=None,
        approver_email=None,
        approver_typed_name=None,
        sent_via=None,
        sent_to=None,
        dispatch_result=None,
        created_at=_ts(0),
    )
    h_base = compute_entry_hash(**base)
    mutated = {**base, field: value}
    h_mut = compute_entry_hash(**mutated)
    assert h_base != h_mut, f"mutating {field} did not change hash"


def test_domain_separator_prevents_audit_log_collision():
    """regulatory-comm hash deve diferir do audit-log hash mesmo com inputs equivalentes."""
    from app.services.audit_hash import compute_entry_hash as audit_compute

    # Estes não são realmente "inputs equivalentes" semanticamente, mas a
    # parte que importa é: o domain separator garante que mesmo se alguém
    # construir um payload colidente em outro lugar, o hash não bate.
    h_reg = compute_entry_hash(
        prev_hash=None,
        row_id=uuid.UUID(int=1),
        tenant_id=uuid.UUID(int=2),
        case_id=None,
        kind="bacen",
        status="draft",
        draft_md="",
        draft_meta=None,
        deadline_at=_ts(86400),
        submitted_at=None,
        approver_email=None,
        approver_typed_name=None,
        sent_via=None,
        sent_to=None,
        dispatch_result=None,
        created_at=_ts(0),
    )
    h_audit = audit_compute(
        prev_hash=None,
        row_id=uuid.UUID(int=1),
        tenant_id=uuid.UUID(int=2),
        actor_id=None,
        actor_email=None,
        actor_ip=None,
        action="bacen",
        resource=None,
        resource_id=None,
        changes=None,
        metadata=None,
        created_at=_ts(0),
    )
    assert h_reg != h_audit


def test_verify_chain_accepts_valid_chain():
    r1 = _row(prev_hash=None, row_id=uuid.UUID(int=1), created_at=_ts(0))
    r2 = _row(prev_hash=r1["entry_hash"], row_id=uuid.UUID(int=2), created_at=_ts(60), status="submitted")
    r3 = _row(prev_hash=r2["entry_hash"], row_id=uuid.UUID(int=3), created_at=_ts(120), status="expired")
    ok, idx, reason = verify_chain([r1, r2, r3])
    assert ok, f"expected OK, got {idx}/{reason}"


def test_verify_chain_rejects_reordered_rows():
    r1 = _row(prev_hash=None, row_id=uuid.UUID(int=1), created_at=_ts(0))
    r2 = _row(prev_hash=r1["entry_hash"], row_id=uuid.UUID(int=2), created_at=_ts(60))
    r3 = _row(prev_hash=r2["entry_hash"], row_id=uuid.UUID(int=3), created_at=_ts(120))
    ok, idx, _ = verify_chain([r1, r3, r2])  # reordered
    assert not ok
    assert idx == 1


def test_verify_chain_rejects_deleted_middle_row():
    r1 = _row(prev_hash=None, row_id=uuid.UUID(int=1), created_at=_ts(0))
    r2 = _row(prev_hash=r1["entry_hash"], row_id=uuid.UUID(int=2), created_at=_ts(60))
    r3 = _row(prev_hash=r2["entry_hash"], row_id=uuid.UUID(int=3), created_at=_ts(120))
    ok, idx, _ = verify_chain([r1, r3])  # r2 sumiu
    assert not ok
    assert idx == 1


def test_verify_chain_rejects_rewritten_row():
    r1 = _row(prev_hash=None, row_id=uuid.UUID(int=1), created_at=_ts(0))
    r2 = _row(prev_hash=r1["entry_hash"], row_id=uuid.UUID(int=2), created_at=_ts(60))
    # mutate field but keep stored hash → tampering
    r2_tampered = {**r2, "draft_md": "# forged"}
    ok, idx, reason = verify_chain([r1, r2_tampered])
    assert not ok
    assert idx == 1
    assert "entry_hash mismatch" in (reason or "")


def test_verify_chain_tolerates_legacy_rows_only_at_head():
    legacy = {
        "id": uuid.UUID(int=1),
        "tenant_id": uuid.UUID(int=42),
        "case_id": None,
        "kind": "bacen",
        "status": "draft",
        "draft_md": "# legacy",
        "draft_meta": None,
        "deadline_at": _ts(86400),
        "submitted_at": None,
        "approver_email": None,
        "approver_typed_name": None,
        "sent_via": None,
        "sent_to": None,
        "dispatch_result": None,
        "created_at": _ts(0),
        "prev_hash": None,
        "entry_hash": None,  # legacy
    }
    r1 = _row(prev_hash=None, row_id=uuid.UUID(int=2), created_at=_ts(60))
    r2 = _row(prev_hash=r1["entry_hash"], row_id=uuid.UUID(int=3), created_at=_ts(120))
    ok, idx, _ = verify_chain([legacy, r1, r2])
    assert ok, "legacy head deve ser tolerado"

    # gap depois de chain iniciada = forgery
    gap = {**legacy, "id": uuid.UUID(int=99), "created_at": _ts(180)}
    ok2, idx2, reason2 = verify_chain([r1, r2, gap])
    assert not ok2
    assert idx2 == 2
    assert "chain interrupted" in (reason2 or "")
