"""Evidence Pack HTTP API — CARD-016 framework exposure.

Exposes the evidence-pack pipeline over HTTP so the admin UI, the
Swagger explorer, and (eventually) the customer API can drive a pack
end-to-end without poking the Python internals.

Endpoints
---------

* ``GET  /api/v1/evidence-packs``                 list discovered packs
* ``GET  /api/v1/evidence-packs/{pack_id}``       single pack metadata
* ``POST /api/v1/evidence-packs/{pack_id}/compile`` run compiler, return JSON bundle
* ``GET  /api/v1/evidence-packs/{pack_id}/preview.html`` render HTML (browser-viewable)

This build wires the compiler to a ``MockRuntime`` — the production
runtime that hits the Investigation Ledger / Sigma corpus / config
state lands in the next card. The HTML preview shows the auditor view
with the mock-seal warning banner enabled.

Pack discovery
~~~~~~~~~~~~~~

By default we look at ``customizations/compliance/evidence-packs/``
relative to the repo root. Operators can override with the env var
``QUARRY_EVIDENCE_PACKS_DIR`` (absolute path).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.evidence_pack.compiler import (
    EvidenceBundle,
    EvidenceCompiler,
    MockRuntime,
)
from app.evidence_pack.parser import (
    EvidencePackError,
    load_packs_in_directory,
)
from app.evidence_pack.renderer import render_evidence_html
from app.evidence_pack.schema import EvidencePack
from app.evidence_pack.signer import MockSigner
from app.evidence_pack.tsa import MockTsaClient


router = APIRouter(prefix="/evidence-packs", tags=["evidence-packs"])


# ---------------------------------------------------------------------------
# Pack discovery
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    # /repo/services/api/app/api/v1/endpoints/evidence_packs.py
    #         6       5   4   3  2    1         0
    # parents[6] == repo root (verified: ``parents[5]`` is ``services``).
    return Path(__file__).resolve().parents[6]


def _packs_dir() -> Path:
    override = os.getenv("QUARRY_EVIDENCE_PACKS_DIR")
    if override:
        return Path(override)
    return _repo_root() / "customizations" / "compliance" / "evidence-packs"


@lru_cache(maxsize=1)
def _load_catalog() -> dict[str, EvidencePack]:
    """Load + cache the catalog. Tests can call ``_load_catalog.cache_clear()``."""
    base = _packs_dir()
    if not base.is_dir():
        return {}
    result = load_packs_in_directory(base)
    # We deliberately do NOT raise on per-file errors here — the caller
    # gets the working catalog and a separate /errors endpoint could
    # surface bad packs later. For the MVP, silently skip; production
    # CI fails the lint earlier.
    return {p.meta.pack_id: p for p in result.packs}


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class PackSummary(BaseModel):
    """Listing entry."""

    pack_id: str
    regulation_code: str
    article: str
    title: str
    reporting_period: str
    output_format: str


class PackListResponse(BaseModel):
    packs: list[PackSummary]
    count: int


class BundleResponse(BaseModel):
    """JSON envelope returned by /compile.

    Bytes-valued fields (TSA token, signature) are hex-encoded so the
    response is JSON-clean.
    """

    pack_id: str
    generated_at: str
    window_start: str
    window_end: str
    data: dict[str, Any]
    data_digest_hex: str
    timestamp: dict[str, Any]
    signature: dict[str, Any]
    hash_chain_entry_hash_hex: str | None
    prev_chain_entry_hash_hex: str | None
    mock_seal: bool = Field(
        description=(
            "True when the bundle was sealed with MockTsaClient or "
            "MockSigner. Production verification must refuse mock seals."
        )
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_compiler() -> EvidenceCompiler:
    """Build a compiler with the runtime the deployment configures.

    For this build we always use ``MockRuntime``; the real
    ``PostgresRuntime`` lands when the ledger migration is in.
    """
    return EvidenceCompiler(
        runtime=MockRuntime(),
        tsa=MockTsaClient(),
        signer=MockSigner(),
    )


def _bundle_to_response(bundle: EvidenceBundle) -> BundleResponse:
    from app.evidence_pack.signer import is_mock_signature
    from app.evidence_pack.tsa import is_mock_token

    mock_seal = is_mock_token(bundle.timestamp.token_der) or is_mock_signature(
        bundle.signature.signature_der
    )

    return BundleResponse(
        pack_id=bundle.pack_id,
        generated_at=bundle.generated_at.isoformat(),
        window_start=bundle.window_start.isoformat(),
        window_end=bundle.window_end.isoformat(),
        data=bundle.data,
        data_digest_hex=bundle.data_digest_hex,
        timestamp={
            "tsa_name": bundle.timestamp.tsa_name,
            "stamped_at": bundle.timestamp.stamped_at.isoformat(),
            "token_der_hex": bundle.timestamp.token_der.hex(),
            "digest_hex": bundle.timestamp.digest_hex,
        },
        signature={
            "signer_subject": bundle.signature.signer_subject,
            "signed_at": bundle.signature.signed_at.isoformat(),
            "digest_algorithm": bundle.signature.digest_algorithm,
            "digest_hex": bundle.signature.digest_hex,
            "signature_der_hex": bundle.signature.signature_der.hex(),
        },
        hash_chain_entry_hash_hex=bundle.hash_chain_entry_hash_hex,
        prev_chain_entry_hash_hex=bundle.prev_chain_entry_hash_hex,
        mock_seal=mock_seal,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=PackListResponse,
    summary="List discovered evidence packs",
)
async def list_packs() -> PackListResponse:
    """Return every YAML pack found under the configured directory."""
    catalog = _load_catalog()
    summaries = [
        PackSummary(
            pack_id=p.meta.pack_id,
            regulation_code=p.meta.regulation_code,
            article=p.meta.article,
            title=p.meta.title,
            reporting_period=p.reporting_period.value,
            output_format=p.output_format.value,
        )
        for p in catalog.values()
    ]
    summaries.sort(key=lambda s: (s.regulation_code, s.article, s.pack_id))
    return PackListResponse(packs=summaries, count=len(summaries))


@router.get(
    "/{pack_id}",
    response_model=PackSummary,
    summary="Get a single evidence pack's metadata",
)
async def get_pack(pack_id: str) -> PackSummary:
    catalog = _load_catalog()
    pack = catalog.get(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"unknown pack_id: {pack_id}")
    return PackSummary(
        pack_id=pack.meta.pack_id,
        regulation_code=pack.meta.regulation_code,
        article=pack.meta.article,
        title=pack.meta.title,
        reporting_period=pack.reporting_period.value,
        output_format=pack.output_format.value,
    )


@router.post(
    "/{pack_id}/compile",
    response_model=BundleResponse,
    summary="Compile a pack against the runtime and return a sealed bundle",
)
async def compile_pack(pack_id: str) -> BundleResponse:
    catalog = _load_catalog()
    pack = catalog.get(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"unknown pack_id: {pack_id}")
    try:
        compiler = _make_compiler()
        bundle = compiler.compile(pack)
    except EvidencePackError as exc:  # pragma: no cover
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _bundle_to_response(bundle)


@router.get(
    "/{pack_id}/preview.html",
    response_class=HTMLResponse,
    summary="Render the compiled pack as a self-contained HTML preview",
)
async def preview_pack_html(pack_id: str) -> HTMLResponse:
    catalog = _load_catalog()
    pack = catalog.get(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"unknown pack_id: {pack_id}")
    compiler = _make_compiler()
    bundle = compiler.compile(pack)
    html_doc = render_evidence_html(pack=pack, bundle=bundle)
    return HTMLResponse(content=html_doc)
