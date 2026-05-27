"""Pydantic models for the Evidence Pack DSL.

Schema design principles:

* **Strict, not lax** — extra fields are rejected. A typo in a pack
  is far worse than rejection at load time; a fiscalização that
  receives an evidence artifact built from a malformed pack creates
  legal exposure.
* **Polymorphic by query type** — each evidence step declares its
  type and its own params block. The compiler dispatches on type;
  this keeps the YAML readable and keeps the executor extensible.
* **Reporting period as a unit, not a free string** — fiscalizações
  ask for evidence covering "last 90 days" or "since the last
  inspection". Encoding the period as data, not prose, lets the
  compiler render the date window consistently across packs.
"""
from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class QueryType(str, Enum):
    """The kinds of evidence the compiler knows how to collect.

    Each value maps to an executor in ``evidence_pack.compiler``.
    """

    SIGMA_RULES_ACTIVE = "sigma_rules_active"
    """Set of detection rules currently armed (provenance + last fired)."""

    INVESTIGATIONS = "investigations"
    """Investigation Ledger rows matching a filter."""

    LEDGER_EXPORT = "ledger_export"
    """A schema-typed export of the Investigation Ledger over a window."""

    CONFIG_STATE = "config_state"
    """A snapshot of relevant config (LLM target, air-gap flag, BYOK status)."""

    DETECTIONS_FIRED = "detections_fired"
    """Counts and exemplars of fired detection rules over the period."""

    CONTROLS_MAPPING = "controls_mapping"
    """Cross-walk from the pack's regulation to ISO 27001 / NIST CSF
    controls — handy for clients also pursuing those certifications."""


class ReportingPeriod(str, Enum):
    """Reporting window the auditor will reference."""

    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    LAST_180_DAYS = "180d"
    LAST_365_DAYS = "365d"
    SINCE_LAST_INSPECTION = "since_last_inspection"
    POINT_IN_TIME = "point_in_time"


class OutputFormat(str, Enum):
    """Artifact shape the compiler renders."""

    BCB_RFI_V1 = "BCB_RFI_v1"
    """Bacen Request-For-Information response, PDF + JSON envelope."""

    ANPD_INCIDENT_48H = "ANPD_incident_48h"
    """ANPD-format incident report under LGPD Art. 48."""

    BCB_24H_INCIDENT = "BCB_24h_incident"
    """24-hour cyber incident report under Comunicado Bacen 44.323/2024."""

    OPEN_FINANCE_FAPI_EVIDENCE = "open_finance_fapi_evidence"
    """Evidence envelope for Open Finance FAPI 2.0 security obligations."""

    GENERIC_AUDITOR_PDF = "generic_auditor_pdf"
    """Free-form auditor PDF — used during pack development."""


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class EvidencePackMeta(BaseModel):
    """Top-level identification of the obligation this pack covers."""

    model_config = ConfigDict(extra="forbid")

    pack_id: Annotated[str, Field(pattern=r"^[a-z0-9-]+$")] = Field(
        description="Internal slug, kebab-case (e.g. 'bcb-85-2021-art-6')."
    )
    regulation_code: str = Field(
        description=(
            "Stable regulation identifier — e.g. 'BCB-85-2021', "
            "'CMN-4893-2021', 'BCB-COMUNICADO-44323-2024'. "
            "Numbers must be verifiable on bcb.gov.br; counsel reviews "
            "the value before a pack lands in main."
        )
    )
    article: str = Field(
        description=(
            "Article reference within the regulation — e.g. 'Art. 6º', "
            "'Art. 12', 'Cap. III, Art. 7º, III'. Free-form so we can "
            "encode both Civil-Law and CMN drafting conventions."
        )
    )
    sub_item: str | None = Field(
        default=None,
        description="Optional inciso / paragraph identifier (e.g. 'II', '§ 2º').",
    )
    title: str = Field(min_length=8)
    requirement: str = Field(
        min_length=20,
        description=(
            "Plain-language paraphrase of what the regulation demands. "
            "This is what the auditor will read first in the artifact."
        ),
    )

    @field_validator("regulation_code")
    @classmethod
    def _no_invented_codes(cls, v: str) -> str:
        # Belt-and-suspenders: we don't want a pack to ship referencing
        # a regulation we can't cite. The list below is the explicitly
        # verified set as of 2026-05; counsel adds entries here when a
        # new resolution is mapped.
        known = {
            "BCB-85-2021",
            "CMN-4893-2021",
            "BCB-COMUNICADO-44323-2024",
            "BCB-CONJUNTA-1",
            "BCB-CONJUNTA-2",
            "BCB-CONJUNTA-3",
            "BCB-CONJUNTA-4",
            "LGPD-13709-2018",
            "ANPD-CD-15",
        }
        if v not in known:
            raise ValueError(
                f"regulation_code {v!r} is not in the verified registry. "
                f"Add it to evidence_pack.schema._no_invented_codes "
                f"only after counsel confirms the regulation exists."
            )
        return v


class SigmaRulesActiveParams(BaseModel):
    """Params for `type: sigma_rules_active`."""

    model_config = ConfigDict(extra="forbid")
    rule_ids: list[str] = Field(min_length=1)


class InvestigationsParams(BaseModel):
    """Params for `type: investigations`."""

    model_config = ConfigDict(extra="forbid")
    pattern_prefix: str | None = None
    severity_in: list[Literal["info", "low", "medium", "high", "critical"]] | None = None
    closed: bool | None = None


class LedgerExportParams(BaseModel):
    """Params for `type: ledger_export`."""

    model_config = ConfigDict(extra="forbid")
    schema_version: str = Field(pattern=r"^v\d+(\.\d+)*$")
    include_redacted_pii: bool = Field(
        default=False,
        description=(
            "When True, the ledger export includes PII columns "
            "(redacted/hashed). Required for some Bacen 24h incident "
            "reports; default False so dev packs cannot accidentally "
            "spill PII into auditor PDFs."
        ),
    )


class ConfigStateParams(BaseModel):
    """Params for `type: config_state`."""

    model_config = ConfigDict(extra="forbid")
    keys: list[str] = Field(min_length=1)


class DetectionsFiredParams(BaseModel):
    """Params for `type: detections_fired`."""

    model_config = ConfigDict(extra="forbid")
    rule_categories: list[str] | None = None
    min_severity: Literal["info", "low", "medium", "high", "critical"] | None = None


class ControlsMappingParams(BaseModel):
    """Params for `type: controls_mapping`."""

    model_config = ConfigDict(extra="forbid")
    frameworks: list[Literal["ISO-27001", "NIST-CSF", "PCI-DSS-4", "SOC-2"]] = Field(
        min_length=1
    )


# Polymorphic step ----------------------------------------------------------


class EvidenceQueryStep(BaseModel):
    """One step in the evidence-collection pipeline.

    The ``type`` discriminator picks which params model applies.
    """

    model_config = ConfigDict(extra="forbid")

    type: QueryType
    label: str = Field(
        min_length=4,
        description="Short label rendered in the auditor PDF for this step.",
    )
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator("params")
    @classmethod
    def _validate_params_for_type(cls, params: dict[str, Any], info: Any) -> dict[str, Any]:
        # Re-parse the params dict against the params model for the
        # declared type. This gives us strict per-type validation
        # without inventing a discriminated-union dance.
        type_value = info.data.get("type")
        if type_value is None:
            return params
        model_by_type: dict[QueryType, type[BaseModel]] = {
            QueryType.SIGMA_RULES_ACTIVE: SigmaRulesActiveParams,
            QueryType.INVESTIGATIONS: InvestigationsParams,
            QueryType.LEDGER_EXPORT: LedgerExportParams,
            QueryType.CONFIG_STATE: ConfigStateParams,
            QueryType.DETECTIONS_FIRED: DetectionsFiredParams,
            QueryType.CONTROLS_MAPPING: ControlsMappingParams,
        }
        model = model_by_type[type_value]
        # Validate; raises on extras or missing required fields.
        model.model_validate(params)
        return params


class EvidencePack(BaseModel):
    """Top-level pack: meta + ordered list of query steps + output spec."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["v1"] = Field(
        default="v1",
        description="DSL schema version. Bump when the pack format changes.",
    )
    meta: EvidencePackMeta
    reporting_period: ReportingPeriod
    output_format: OutputFormat
    evidence_queries: list[EvidenceQueryStep] = Field(min_length=1)
    narrative_template: str | None = Field(
        default=None,
        description=(
            "Optional Jinja2 narrative the compiler renders above the "
            "structured evidence. Use to explain the obligation in the "
            "DPO's voice; keep under ~300 words."
        ),
    )
    cross_references: list[str] = Field(
        default_factory=list,
        description=(
            "Optional list of related control IDs in other frameworks "
            "(ISO 27001 A.5.10, NIST CSF DE.CM-1, etc.). Used by the "
            "compiler to generate a cross-walk appendix when the client "
            "is also pursuing those certifications."
        ),
    )
