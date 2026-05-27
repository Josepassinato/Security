"""Evidence Pack compiler — turns a Pack + runtime state into a bundle.

The compiler is the choreographer of the four layers:

  1. Pack DSL (schema.py / parser.py)         — what to collect
  2. Runtime executor (this module)            — collect it
  3. Renderer (renderer.py)                    — make a PDF
  4. Chain + TSA + signature (merkle/tsa/signer) — seal it

In production the *runtime executor* hits real subsystems (Postgres
ledger, Sigma corpus, config service). For tests + early dev we ship
a :class:`MockRuntime` that returns deterministic stubs, so the whole
chain is verifiable without standing up infra.

The compiler stays small on purpose. Each query type has a tiny
executor function; adding a new ``QueryType`` is: extend the enum,
add a params model, add a runtime method, register here. That's it.
"""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from app.evidence_pack.merkle import canonical_json, hash_entry
from app.evidence_pack.schema import (
    EvidencePack,
    EvidenceQueryStep,
    QueryType,
    ReportingPeriod,
)
from app.evidence_pack.signer import (
    ArtifactSigner,
    MockSigner,
    SignatureResult,
)
from app.evidence_pack.tsa import (
    MockTsaClient,
    TimestampResponse,
    TsaClient,
)


# ---------------------------------------------------------------------------
# Runtime interface
# ---------------------------------------------------------------------------


class EvidenceRuntime(ABC):
    """Thin port for the subsystems each query type consults.

    Implementations:
      * :class:`MockRuntime` — tests + early dev, returns canned data.
      * (future) ``PostgresRuntime`` — hits the real ledger + sigma + config.
    """

    @abstractmethod
    def sigma_rules_active(self, rule_ids: list[str]) -> list[dict[str, Any]]: ...

    @abstractmethod
    def investigations(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        pattern_prefix: str | None,
        severity_in: list[str] | None,
        closed: bool | None,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    def ledger_export(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        schema_version: str,
        include_redacted_pii: bool,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def config_state(self, keys: list[str]) -> dict[str, Any]: ...

    @abstractmethod
    def detections_fired(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        rule_categories: list[str] | None,
        min_severity: str | None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def controls_mapping(self, frameworks: list[str]) -> dict[str, list[str]]: ...


# ---------------------------------------------------------------------------
# Mock runtime (tests + dev)
# ---------------------------------------------------------------------------


@dataclass
class MockRuntime(EvidenceRuntime):
    """Deterministic canned-data runtime.

    Each method returns plausible-shaped data so the compiler + renderer
    + chain can be exercised end-to-end. Production code MUST NOT use
    this for real fiscalização output — gate downstream on
    ``isinstance(runtime, MockRuntime)``.
    """

    sigma_active: list[dict[str, Any]] = field(default_factory=list)
    investigations_rows: list[dict[str, Any]] = field(default_factory=list)
    ledger_rows: list[dict[str, Any]] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    detections_summary: dict[str, Any] | None = None
    controls_xwalk: dict[str, list[str]] = field(default_factory=dict)

    def sigma_rules_active(self, rule_ids: list[str]) -> list[dict[str, Any]]:
        if self.sigma_active:
            return [r for r in self.sigma_active if r.get("id") in rule_ids]
        return [
            {"id": rid, "enabled": True, "last_fired_at": None, "version": "v1"}
            for rid in rule_ids
        ]

    def investigations(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        pattern_prefix: str | None,
        severity_in: list[str] | None,
        closed: bool | None,
    ) -> list[dict[str, Any]]:
        rows = list(self.investigations_rows)
        if pattern_prefix is not None:
            rows = [r for r in rows if r.get("pattern", "").startswith(pattern_prefix)]
        if severity_in is not None:
            rows = [r for r in rows if r.get("severity") in severity_in]
        if closed is not None:
            rows = [r for r in rows if r.get("closed") is closed]
        return rows

    def ledger_export(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        schema_version: str,
        include_redacted_pii: bool,
    ) -> dict[str, Any]:
        return {
            "schema_version": schema_version,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "include_redacted_pii": include_redacted_pii,
            "entries_count": len(self.ledger_rows),
            "entries": self.ledger_rows,
        }

    def config_state(self, keys: list[str]) -> dict[str, Any]:
        # Return only the requested keys, defaulting missing ones to None
        # so the auditor PDF can show "not configured" explicitly.
        return {k: self.config.get(k) for k in keys}

    def detections_fired(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        rule_categories: list[str] | None,
        min_severity: str | None,
    ) -> dict[str, Any]:
        if self.detections_summary is not None:
            return self.detections_summary
        return {
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "total": 0,
            "by_severity": {},
            "exemplars": [],
        }

    def controls_mapping(self, frameworks: list[str]) -> dict[str, list[str]]:
        return {f: self.controls_xwalk.get(f, []) for f in frameworks}


# ---------------------------------------------------------------------------
# Bundle types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceBundle:
    """The output of compiling a pack against the runtime + sealing.

    * ``data`` is the structured evidence collected per step.
    * ``data_digest_hex`` is the SHA-256 of the canonical-JSON
      serialisation of ``data`` — what TSA stamped and signer signed.
    * ``timestamp`` and ``signature`` come from the TSA + signer.
    * ``hash_chain_entry`` is the merkle-chain receipt linking THIS
      bundle to the previous one the compiler produced (if any).
    """

    pack_id: str
    generated_at: datetime
    window_start: datetime
    window_end: datetime

    data: dict[str, Any]
    data_digest_hex: str

    timestamp: TimestampResponse
    signature: SignatureResult
    hash_chain_entry_hash_hex: str | None
    prev_chain_entry_hash_hex: str | None


# ---------------------------------------------------------------------------
# Compiler
# ---------------------------------------------------------------------------


@dataclass
class EvidenceCompiler:
    """Run a pack against a runtime; return a sealed evidence bundle."""

    runtime: EvidenceRuntime
    tsa: TsaClient
    signer: ArtifactSigner
    now_provider: Any = field(default=None)
    """Optional ``() -> datetime`` for deterministic tests. Defaults to
    ``datetime.now(timezone.utc)``."""

    def __post_init__(self) -> None:
        if self.now_provider is None:
            self.now_provider = lambda: datetime.now(timezone.utc)

    # -- Public entrypoints -------------------------------------------------

    def compile(
        self,
        pack: EvidencePack,
        *,
        prev_chain_entry_hash_hex: str | None = None,
    ) -> EvidenceBundle:
        """Materialise the pack into a sealed bundle.

        Args:
            pack: A validated :class:`EvidencePack`.
            prev_chain_entry_hash_hex: Previous bundle's chain hash for
                merkle linkage. ``None`` for the first bundle ever.

        Returns:
            :class:`EvidenceBundle`.
        """
        window_start, window_end = self._resolve_window(pack.reporting_period)

        data: dict[str, Any] = {}
        for step in pack.evidence_queries:
            data[step.label] = self._execute_step(
                step, window_start=window_start, window_end=window_end
            )

        canonical = canonical_json(
            {
                "pack_id": pack.meta.pack_id,
                "regulation_code": pack.meta.regulation_code,
                "article": pack.meta.article,
                "schema_version": pack.schema_version,
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "data": data,
            }
        )
        data_digest = hashlib.sha256(canonical).digest()

        ts = self.tsa.stamp_digest(data_digest)
        sig = self.signer.sign_digest(data_digest)

        # Chain linkage — the bundle hash binds in order: data_digest,
        # TSA token, signature. The auditor recomputes this from the
        # three artifacts and confirms it matches the chain entry.
        chain = hash_entry(
            prev_entry_hash=prev_chain_entry_hash_hex,
            row={
                "data_digest": data_digest.hex(),
                "tsa_token_b64": ts.token_der.hex(),
                "signature_der_b64": sig.signature_der.hex(),
            },
        )

        return EvidenceBundle(
            pack_id=pack.meta.pack_id,
            generated_at=self.now_provider(),
            window_start=window_start,
            window_end=window_end,
            data=data,
            data_digest_hex=data_digest.hex(),
            timestamp=ts,
            signature=sig,
            hash_chain_entry_hash_hex=chain.entry_hash_hex,
            prev_chain_entry_hash_hex=chain.prev_hash_hex,
        )

    # -- Step dispatch ------------------------------------------------------

    def _execute_step(
        self,
        step: EvidenceQueryStep,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> Any:
        match step.type:
            case QueryType.SIGMA_RULES_ACTIVE:
                return self.runtime.sigma_rules_active(step.params["rule_ids"])
            case QueryType.INVESTIGATIONS:
                return self.runtime.investigations(
                    window_start=window_start,
                    window_end=window_end,
                    pattern_prefix=step.params.get("pattern_prefix"),
                    severity_in=step.params.get("severity_in"),
                    closed=step.params.get("closed"),
                )
            case QueryType.LEDGER_EXPORT:
                return self.runtime.ledger_export(
                    window_start=window_start,
                    window_end=window_end,
                    schema_version=step.params["schema_version"],
                    include_redacted_pii=step.params.get(
                        "include_redacted_pii", False
                    ),
                )
            case QueryType.CONFIG_STATE:
                return self.runtime.config_state(step.params["keys"])
            case QueryType.DETECTIONS_FIRED:
                return self.runtime.detections_fired(
                    window_start=window_start,
                    window_end=window_end,
                    rule_categories=step.params.get("rule_categories"),
                    min_severity=step.params.get("min_severity"),
                )
            case QueryType.CONTROLS_MAPPING:
                return self.runtime.controls_mapping(step.params["frameworks"])
            case _:  # pragma: no cover — schema guards this
                raise NotImplementedError(f"unsupported query type: {step.type}")

    # -- Window resolution --------------------------------------------------

    def _resolve_window(
        self, period: ReportingPeriod
    ) -> tuple[datetime, datetime]:
        end = self.now_provider()
        deltas: dict[ReportingPeriod, timedelta] = {
            ReportingPeriod.LAST_30_DAYS: timedelta(days=30),
            ReportingPeriod.LAST_90_DAYS: timedelta(days=90),
            ReportingPeriod.LAST_180_DAYS: timedelta(days=180),
            ReportingPeriod.LAST_365_DAYS: timedelta(days=365),
        }
        if period in deltas:
            return end - deltas[period], end
        if period == ReportingPeriod.POINT_IN_TIME:
            return end, end
        # SINCE_LAST_INSPECTION — falls back to 365d in this build; the
        # production runtime will resolve the actual last-inspection
        # date from a per-tenant config table.
        return end - timedelta(days=365), end


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def make_dev_compiler(runtime: EvidenceRuntime | None = None) -> EvidenceCompiler:
    """Build a compiler wired with the mock TSA + mock signer.

    Useful for tests and the first end-to-end demo. Production callers
    construct :class:`EvidenceCompiler` directly with the real TSA and
    signer instances.
    """
    return EvidenceCompiler(
        runtime=runtime or MockRuntime(),
        tsa=MockTsaClient(),
        signer=MockSigner(),
    )
