"""Tamper-evident hash chain for regulatory_communications.

Mesma semântica de ``app.services.audit_hash`` (sha256 + canonical JSON
+ domain separator + chain per tenant), mas:

* O conjunto de campos hasheados é o da tabela
  ``regulatory_communications`` (ver migração 045).
* A chain é por ``(tenant_id, kind)`` em vez de por ``tenant_id`` —
  Bacen e ANPD têm reguladores distintos e o auditor de cada um quer
  ver a cronologia daquela jurisdição específica.
* O domain separator é ``regulatory-comm-v1`` pra impedir reuso
  acidental do payload em outro contexto de hash.

Verificação é stateless: dado um array de linhas ordenado por
``created_at``, ``verify_chain`` replica o cálculo e retorna a primeira
violação encontrada. Pode rodar em CSV exportado, sem acesso ao banco.

Adicionar campo é mudança quebrante de chain (rows antigos não
verificam mais). Se isso for necessário, criar ``regulatory-comm-v2`` e
migrar com flag day documentado.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

_DOMAIN_SEPARATOR = b"\x1fregulatory-comm-v1\x1f"


def _canonicalise(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _canonicalise(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_canonicalise(v) for v in value]
    return str(value)


def compute_entry_hash(
    *,
    prev_hash: str | None,
    row_id: uuid.UUID | str,
    tenant_id: uuid.UUID | str,
    case_id: uuid.UUID | str | None,
    kind: str,
    status: str,
    draft_md: str,
    draft_meta: dict | None,
    deadline_at: datetime,
    submitted_at: datetime | None,
    approver_email: str | None,
    approver_typed_name: str | None,
    sent_via: str | None,
    sent_to: str | None,
    dispatch_result: dict | None,
    created_at: datetime,
) -> str:
    body = {
        "id": _canonicalise(row_id),
        "tenant_id": _canonicalise(tenant_id),
        "case_id": _canonicalise(case_id),
        "kind": kind,
        "status": status,
        # draft_md is hashed in full — it IS the artifact being attested
        "draft_md": draft_md,
        "draft_meta": _canonicalise(draft_meta),
        "deadline_at": _canonicalise(deadline_at),
        "submitted_at": _canonicalise(submitted_at),
        "approver_email": approver_email,
        "approver_typed_name": approver_typed_name,
        "sent_via": sent_via,
        "sent_to": sent_to,
        "dispatch_result": _canonicalise(dispatch_result),
        "created_at": _canonicalise(created_at),
    }
    serialised = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    h = hashlib.sha256()
    h.update((prev_hash or "").encode("utf-8"))
    h.update(_DOMAIN_SEPARATOR)
    h.update(serialised.encode("utf-8"))
    return h.hexdigest()


def verify_chain(
    rows: list[dict[str, Any]],
) -> tuple[bool, int | None, str | None]:
    """Replay ``rows`` (oldest → newest, same tenant + kind) and verify.

    Returns ``(True, None, None)`` on success, or ``(False, index, reason)``.
    Rows without ``entry_hash`` are treated as legacy and skipped — once
    a chain has started for that (tenant, kind), every subsequent row
    must carry one.
    """
    prev_hash: str | None = None
    started = False
    for idx, row in enumerate(rows):
        stored = row.get("entry_hash")
        if stored is None:
            if started:
                return False, idx, "chain interrupted: entry_hash missing"
            continue
        started = True

        recorded_prev = row.get("prev_hash")
        if recorded_prev != prev_hash:
            return False, idx, "prev_hash mismatch"

        computed = compute_entry_hash(
            prev_hash=prev_hash,
            row_id=row["id"],
            tenant_id=row["tenant_id"],
            case_id=row.get("case_id"),
            kind=row["kind"],
            status=row["status"],
            draft_md=row["draft_md"],
            draft_meta=row.get("draft_meta"),
            deadline_at=row["deadline_at"],
            submitted_at=row.get("submitted_at"),
            approver_email=row.get("approver_email"),
            approver_typed_name=row.get("approver_typed_name"),
            sent_via=row.get("sent_via"),
            sent_to=row.get("sent_to"),
            dispatch_result=row.get("dispatch_result"),
            created_at=row["created_at"],
        )
        if computed != stored:
            return False, idx, "entry_hash mismatch"
        prev_hash = computed
    return True, None, None


__all__ = ["compute_entry_hash", "verify_chain"]
