"""Tests for the Evidence Pack HTML / PDF renderer.

We don't try to render PDFs in CI by default (WeasyPrint needs the
Cairo/Pango native stack that the test container may not provide).
The HTML path is fully tested; the PDF path is tested behind a skip
guard that runs only when the native stack is present.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.evidence_pack.compiler import (  # noqa: E402
    MockRuntime,
    make_dev_compiler,
)
from app.evidence_pack.parser import load_pack  # noqa: E402
from app.evidence_pack.renderer import (  # noqa: E402
    WeasyPrintUnavailableError,
    render_evidence_html,
    render_evidence_pdf,
)


# ── helpers ────────────────────────────────────────────────────────────────


def _build_bundle():
    repo_root = _API_ROOT.parents[1]
    pack_path = (
        repo_root
        / "customizations"
        / "compliance"
        / "evidence-packs"
        / "bcb-85-2021-art-6.yaml"
    )
    pack = load_pack(pack_path)
    compiler = make_dev_compiler(
        runtime=MockRuntime(
            config={
                "incident_response.plan_version": "v3.2",
                "incident_response.last_review_date": "2026-01-15",
                "incident_response.approved_by": "DPO + CTO",
                "incident_response.training_completion_rate": 0.94,
            },
            ledger_rows=[{"id": i} for i in range(7)],
            controls_xwalk={"ISO-27001": ["A.5.24"], "NIST-CSF": ["RS.RP-1"]},
        )
    )
    bundle = compiler.compile(pack)
    return pack, bundle


# ── HTML ───────────────────────────────────────────────────────────────────


def test_html_renders_full_document():
    pack, bundle = _build_bundle()
    html = render_evidence_html(pack=pack, bundle=bundle)

    assert html.startswith("<!DOCTYPE html>")
    assert html.rstrip().endswith("</html>")
    # Pack identity in document
    assert "BCB-85-2021" in html
    assert "Art. 6º" in html
    # Pack title visible
    assert "Plano de resposta a incidentes" in html
    # Sealing section present
    assert "Cadeia Merkle" in html
    assert bundle.data_digest_hex in html
    assert bundle.hash_chain_entry_hash_hex in html


def test_html_includes_every_query_step_label():
    pack, bundle = _build_bundle()
    html = render_evidence_html(pack=pack, bundle=bundle)
    for step in pack.evidence_queries:
        assert step.label in html, f"missing step label in HTML: {step.label}"


def test_html_warns_when_seal_is_mock():
    """A mock TSA + mock signer must surface the warning banner —
    refusing to ship a mock-sealed artifact as if it were real is the
    whole point of the production verification gate."""
    pack, bundle = _build_bundle()
    html = render_evidence_html(pack=pack, bundle=bundle)
    assert "mock" in html.lower()
    assert "fiscalização" in html.lower() or "fiscaliza" in html.lower()


def test_html_escapes_pack_fields_safely():
    """Defensive — pack content reaches the auditor PDF, so HTML
    metachars must be escaped even though the schema disallows most
    weird inputs at validation time."""
    pack, bundle = _build_bundle()
    # Manually mutate a label to include a <script> tag and re-check.
    pack.evidence_queries[0].label = "<script>alert('x')</script>"
    bundle_data = dict(bundle.data)
    bundle_data["<script>alert('x')</script>"] = bundle_data.pop(
        next(iter(bundle.data.keys()))
    )
    # We can't easily mutate the frozen bundle dataclass; just render
    # the modified pack with the original bundle and confirm the label
    # is escaped on its way out.
    html = render_evidence_html(pack=pack, bundle=bundle)
    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html


def test_html_includes_cross_references_when_present():
    pack, bundle = _build_bundle()
    assert pack.cross_references, "fixture pack should ship cross-refs"
    html = render_evidence_html(pack=pack, bundle=bundle)
    for ref in pack.cross_references:
        # Cross-refs contain hyphens etc.; check a stable substring.
        first_word = ref.split(" ")[0]
        assert first_word in html


# ── PDF (skipped when native stack missing) ────────────────────────────────


def _weasyprint_native_available() -> bool:
    try:
        import weasyprint  # noqa: F401 PLC0415
        return True
    except (ImportError, OSError):
        return False


@pytest.mark.skipif(
    not _weasyprint_native_available(),
    reason="WeasyPrint native stack (Cairo/Pango/GLib) not installed",
)
def test_pdf_renders_to_bytes():
    pack, bundle = _build_bundle()
    pdf = render_evidence_pdf(pack=pack, bundle=bundle)
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF-"), "output is not a valid PDF (missing %PDF- header)"
    assert len(pdf) > 1000  # arbitrary lower bound — sanity, not exact size


def test_pdf_raises_friendly_error_when_weasyprint_absent(monkeypatch):
    """Simulate a no-WeasyPrint environment and confirm the wrapper
    raises WeasyPrintUnavailableError (not a bare ImportError)."""
    if _weasyprint_native_available():
        # Hide the module so the import path fails.
        import sys as _sys
        monkeypatch.setitem(_sys.modules, "weasyprint", None)
    pack, bundle = _build_bundle()
    with pytest.raises(WeasyPrintUnavailableError):
        render_evidence_pdf(pack=pack, bundle=bundle)
