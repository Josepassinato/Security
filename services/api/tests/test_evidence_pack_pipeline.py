"""End-to-end + unit tests for the Evidence Pack pipeline (CARD-016 Item 1).

Coverage:
  • Merkle chain — single-entry, multi-entry, tamper detection.
  • Mock TSA — output shape, mock-detection guard.
  • Mock signer — output shape, mock-detection guard.
  • Compiler dispatch over the 6 query types.
  • End-to-end: load the BCB 85/2021 pack from disk, run compiler with
    mocked runtime, render a sealed bundle, verify the chain.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.evidence_pack.compiler import (  # noqa: E402
    EvidenceCompiler,
    MockRuntime,
    make_dev_compiler,
)
from app.evidence_pack.merkle import (  # noqa: E402
    GENESIS_PREV_HASH,
    canonical_json,
    hash_entry,
    verify_chain,
)
from app.evidence_pack.parser import load_pack  # noqa: E402
from app.evidence_pack.signer import (  # noqa: E402
    MockSigner,
    is_mock_signature,
)
from app.evidence_pack.tsa import (  # noqa: E402
    MockTsaClient,
    TsaError,
    is_mock_token,
)


# ── Merkle ─────────────────────────────────────────────────────────────────


def test_canonical_json_is_stable_across_key_order():
    a = canonical_json({"a": 1, "b": 2})
    b = canonical_json({"b": 2, "a": 1})
    assert a == b


def test_genesis_entry_uses_zero_prev():
    entry = hash_entry(prev_entry_hash=None, row={"k": "v"})
    assert entry.prev_hash_hex == GENESIS_PREV_HASH.hex()
    assert len(entry.entry_hash_hex) == 64


def test_chain_links_three_entries_correctly():
    e1 = hash_entry(prev_entry_hash=None, row={"step": 1})
    e2 = hash_entry(prev_entry_hash=e1.entry_hash_hex, row={"step": 2})
    e3 = hash_entry(prev_entry_hash=e2.entry_hash_hex, row={"step": 3})

    rows = [
        {"prev_hash": e1.prev_hash_hex, "entry_hash": e1.entry_hash_hex, "payload": {"step": 1}},
        {"prev_hash": e2.prev_hash_hex, "entry_hash": e2.entry_hash_hex, "payload": {"step": 2}},
        {"prev_hash": e3.prev_hash_hex, "entry_hash": e3.entry_hash_hex, "payload": {"step": 3}},
    ]
    ok, bad_idx = verify_chain(rows)
    assert ok is True
    assert bad_idx is None


def test_chain_detects_payload_tampering():
    e1 = hash_entry(prev_entry_hash=None, row={"step": 1})
    e2 = hash_entry(prev_entry_hash=e1.entry_hash_hex, row={"step": 2})

    rows = [
        {"prev_hash": e1.prev_hash_hex, "entry_hash": e1.entry_hash_hex, "payload": {"step": 1}},
        {
            "prev_hash": e2.prev_hash_hex,
            "entry_hash": e2.entry_hash_hex,
            "payload": {"step": 999},  # mutated after the fact
        },
    ]
    ok, bad_idx = verify_chain(rows)
    assert ok is False
    assert bad_idx == 1


def test_chain_detects_prev_hash_tampering():
    e1 = hash_entry(prev_entry_hash=None, row={"step": 1})
    e2 = hash_entry(prev_entry_hash=e1.entry_hash_hex, row={"step": 2})

    rows = [
        {"prev_hash": e1.prev_hash_hex, "entry_hash": e1.entry_hash_hex, "payload": {"step": 1}},
        {
            "prev_hash": "f" * 64,  # tampered link
            "entry_hash": e2.entry_hash_hex,
            "payload": {"step": 2},
        },
    ]
    ok, bad_idx = verify_chain(rows)
    assert ok is False
    assert bad_idx == 1


def test_invalid_prev_lengths_raise():
    with pytest.raises(ValueError):
        hash_entry(prev_entry_hash=b"\x00" * 16, row={})
    with pytest.raises(ValueError):
        hash_entry(prev_entry_hash="ab", row={})


# ── TSA mock ───────────────────────────────────────────────────────────────


def test_mock_tsa_emits_well_formed_response():
    tsa = MockTsaClient(now_provider=lambda: datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc))
    digest = hashlib.sha256(b"payload").digest()
    resp = tsa.stamp_digest(digest)
    assert resp.tsa_name.startswith("MockTSA")
    assert resp.digest_hex == digest.hex()
    assert is_mock_token(resp.token_der)
    assert resp.stamped_at.tzinfo is not None


def test_mock_tsa_rejects_bad_digest_length():
    tsa = MockTsaClient()
    with pytest.raises(TsaError):
        tsa.stamp_digest(b"\x00" * 31)


def test_mock_tsa_stamp_bytes_helper_hashes_first():
    tsa = MockTsaClient()
    resp = tsa.stamp_bytes(b"hello world")
    assert resp.digest_hex == hashlib.sha256(b"hello world").hexdigest()


def test_mock_tsa_refuses_empty_payload():
    tsa = MockTsaClient()
    with pytest.raises(TsaError):
        tsa.stamp_bytes(b"")


# ── Signer mock ────────────────────────────────────────────────────────────


def test_mock_signer_is_deterministic():
    s1 = MockSigner(now_provider=lambda: datetime(2026, 5, 26, 12, tzinfo=timezone.utc))
    s2 = MockSigner(now_provider=lambda: datetime(2026, 5, 26, 12, tzinfo=timezone.utc))
    digest = hashlib.sha256(b"payload").digest()
    a = s1.sign_digest(digest)
    b = s2.sign_digest(digest)
    assert a.signature_der == b.signature_der
    assert is_mock_signature(a.signature_der)


def test_mock_signer_emits_expected_subject():
    s = MockSigner()
    res = s.sign_bytes(b"hi")
    assert "MOCK SIGNER" in res.signer_subject


# ── Compiler dispatch ──────────────────────────────────────────────────────


def test_compiler_dispatches_each_query_type():
    """Synthesise a pack that exercises every QueryType, run compile."""
    # Build a synthetic pack via the dict surface — uses BCB-85-2021 code
    # so the regulation-allowlist guard accepts it.
    from app.evidence_pack.schema import EvidencePack

    pack = EvidencePack.model_validate(
        {
            "schema_version": "v1",
            "meta": {
                "pack_id": "test-all-step-types",
                "regulation_code": "BCB-85-2021",
                "article": "Art. 6",
                "title": "Test pack exercising every QueryType",
                "requirement": "Sanity check that the compiler runs each step kind.",
            },
            "reporting_period": "90d",
            "output_format": "generic_auditor_pdf",
            "evidence_queries": [
                {"type": "sigma_rules_active", "label": "sigma-active",
                 "params": {"rule_ids": ["PIX-001"]}},
                {"type": "investigations", "label": "open-cases",
                 "params": {"severity_in": ["high"]}},
                {"type": "ledger_export", "label": "ledger",
                 "params": {"schema_version": "v1"}},
                {"type": "config_state", "label": "config-snapshot",
                 "params": {"keys": ["incident_response.plan_version"]}},
                {"type": "detections_fired", "label": "fired",
                 "params": {"min_severity": "medium"}},
                {"type": "controls_mapping", "label": "xwalk",
                 "params": {"frameworks": ["ISO-27001"]}},
            ],
        }
    )

    compiler = make_dev_compiler()
    bundle = compiler.compile(pack)
    assert set(bundle.data.keys()) == {
        "sigma-active", "open-cases", "ledger", "config-snapshot", "fired", "xwalk",
    }
    assert len(bundle.data_digest_hex) == 64


def test_compiler_chains_bundles_in_order():
    pack = _load_bundled_pack()
    runtime = MockRuntime(
        ledger_rows=[{"id": 1, "decision": "block"}],
        config={"incident_response.plan_version": "v3.2"},
    )
    compiler = EvidenceCompiler(
        runtime=runtime, tsa=MockTsaClient(), signer=MockSigner()
    )
    b1 = compiler.compile(pack)
    b2 = compiler.compile(
        pack, prev_chain_entry_hash_hex=b1.hash_chain_entry_hash_hex
    )
    assert b1.prev_chain_entry_hash_hex == GENESIS_PREV_HASH.hex()
    assert b2.prev_chain_entry_hash_hex == b1.hash_chain_entry_hash_hex
    assert b2.hash_chain_entry_hash_hex != b1.hash_chain_entry_hash_hex


# ── End-to-end on the bundled pack ─────────────────────────────────────────


def _load_bundled_pack():
    repo_root = _API_ROOT.parents[1]
    pack_path = (
        repo_root
        / "customizations"
        / "compliance"
        / "evidence-packs"
        / "bcb-85-2021-art-6.yaml"
    )
    return load_pack(pack_path)


def test_end_to_end_bcb_85_art_6_pack_compiles_into_sealed_bundle():
    pack = _load_bundled_pack()
    runtime = MockRuntime(
        config={
            "incident_response.plan_version": "v3.2",
            "incident_response.last_review_date": "2026-01-15",
            "incident_response.approved_by": "DPO + CTO",
            "incident_response.training_completion_rate": 0.94,
        },
        ledger_rows=[{"id": i, "decision": "noop"} for i in range(12)],
        investigations_rows=[
            {"id": "INV-1", "severity": "high", "pattern": "PIX-001"},
            {"id": "INV-2", "severity": "medium", "pattern": "ATO-003"},
        ],
        detections_summary={
            "total": 47,
            "by_severity": {"medium": 30, "high": 12, "critical": 5},
            "exemplars": [],
        },
        controls_xwalk={
            "ISO-27001": ["A.5.24", "A.5.26"],
            "NIST-CSF": ["RS.RP-1", "RS.CO-1"],
        },
    )

    compiler = EvidenceCompiler(
        runtime=runtime,
        tsa=MockTsaClient(),
        signer=MockSigner(),
    )
    bundle = compiler.compile(pack)

    # Pack identity
    assert bundle.pack_id == "bcb-85-2021-art-6"

    # All 5 query steps produced output
    assert set(bundle.data.keys()) == {
        "Plano de resposta a incidentes vigente",
        "Detecções relevantes acionadas no período",
        "Investigações abertas e fechadas no período",
        "Trilha de auditoria — decisões dos agentes",
        "Cross-walk com frameworks de certificação",
    }
    # Ledger export carried real shape
    ledger = bundle.data["Trilha de auditoria — decisões dos agentes"]
    assert ledger["entries_count"] == 12
    assert ledger["include_redacted_pii"] is False

    # Sealing layer present
    assert len(bundle.data_digest_hex) == 64
    assert is_mock_token(bundle.timestamp.token_der)
    assert is_mock_signature(bundle.signature.signature_der)
    assert bundle.signature.digest_hex == bundle.data_digest_hex
    assert bundle.timestamp.digest_hex == bundle.data_digest_hex

    # Chain receipt covers data + tsa + signature
    assert len(bundle.hash_chain_entry_hash_hex) == 64
    assert bundle.prev_chain_entry_hash_hex == GENESIS_PREV_HASH.hex()
