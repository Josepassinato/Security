"""Bacen Evidence Pack DSL — CARD-016 core wedge.

A Pack maps one regulatory obligation (e.g. BCB 85/2021 Art. 6) to:

1. The evidence the system must collect to demonstrate compliance,
2. The expression of *how* to collect it (queries against ledger,
   investigations, sigma corpus, config state),
3. The auditor-facing artifact shape (PDF / JSON envelope).

The DSL is YAML; the schema enforced here is the public contract a
pack author writes against. Validation must be strict — silently
ignoring an unknown field would let a malformed pack ship to a
fiscalização.

This package is the *framework*. The *content* (the actual curated
packs validated by counsel) lives under `customizations/compliance/
evidence-packs/` and, in the closed-source split, will move to
`enterprise/` under a BSL licence.
"""
from app.evidence_pack.schema import (
    EvidencePack,
    EvidencePackMeta,
    EvidenceQueryStep,
    QueryType,
    ReportingPeriod,
)

__all__ = [
    "EvidencePack",
    "EvidencePackMeta",
    "EvidenceQueryStep",
    "QueryType",
    "ReportingPeriod",
]
