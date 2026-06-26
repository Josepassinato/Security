"""SQLAlchemy ORM model for the sanctions screening evidence ledger (Phase 1).

``screening_decisions`` is the IMMUTABLE ledger of sanctions-screening
decisions — the "livro-razão". It is intentionally separate from
``pld_ft_cases`` (the mutable "caderno de trabalho"): a case changes status
many times; the decisions that built it never change. A decision references
its case via ``case_id``, never the reverse.

The canonical schema lives in
``services/api/migrations/050_screening_decisions.sql`` — it adds the
immutability trigger, RLS, CHECK constraints and indexes that this ORM
definition cannot express. Dev environments auto-create the table via
``Base.metadata.create_all``; the SQL migration layers the guardrails on top.

Attribution is split (signed product decision, 2026-06-26): ``matching_engine``
is who produced the match; ``list_of_record`` + ``list_dataset`` +
``list_version`` + ``list_release_date`` are the versioned source that
*witnesses* which list build the name was run against. ``engine_raw_result``
holds the untouched engine payload (sacred); ``match_score`` is derived by a
versioned rule (``scoring_rule_version``).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ScreeningDecision(Base):
    """One immutable, hash-chained sanctions-screening decision."""

    __tablename__ = "screening_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pld_ft_cases.id", ondelete="RESTRICT")
    )

    # Counterparty
    counterparty_name: Mapped[str] = mapped_column(Text, nullable=False)
    counterparty_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    counterparty_id: Mapped[str] = mapped_column(Text, nullable=False)
    counterparty_id_type: Mapped[str] = mapped_column(Text, nullable=False)

    # Attribution: who matched vs. who witnesses the list version
    matching_engine: Mapped[str] = mapped_column(Text, nullable=False)
    list_of_record: Mapped[str] = mapped_column(Text, nullable=False)
    list_source: Mapped[str] = mapped_column(Text, nullable=False)
    list_dataset: Mapped[str] = mapped_column(Text, nullable=False)
    list_version: Mapped[str] = mapped_column(Text, nullable=False)
    list_release_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    # Scoring: raw engine payload (sacred) + derived score (versioned ruler)
    engine_raw_result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    match_score: Mapped[int] = mapped_column(Integer, nullable=False)
    scoring_rule_version: Mapped[str] = mapped_column(Text, nullable=False)

    # Decision + disposition
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    disposition: Mapped[str] = mapped_column(Text, nullable=False)

    # Human-in-the-loop (null reviewer == automatic; rationale required on override)
    human_reviewer: Mapped[str | None] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text, nullable=False, server_default="")

    # Timestamps (UTC)
    screened_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Tamper-evident hash chain
    prev_hash: Mapped[str | None] = mapped_column(String(64))
    entry_hash: Mapped[str | None] = mapped_column(String(64))

    __table_args__ = (
        CheckConstraint("match_score BETWEEN 0 AND 100", name="chk_screening_match_score_range"),
        CheckConstraint(
            "counterparty_id_type IN ('CPF','CNPJ','PASSPORT','WALLET','OTHER')",
            name="chk_screening_id_type",
        ),
        CheckConstraint(
            "list_source IN ('OFAC_SDN','OFAC_CONSOLIDATED','UN','EU','PEP','ADVERSE_MEDIA')",
            name="chk_screening_list_source",
        ),
        CheckConstraint(
            "decision IN ('NO_MATCH','POTENTIAL_MATCH','TRUE_MATCH','ESCALATED')",
            name="chk_screening_decision",
        ),
        CheckConstraint(
            "disposition IN ('CLEARED_FALSE_POSITIVE','BLOCKED','REPORTED','PENDING')",
            name="chk_screening_disposition",
        ),
        CheckConstraint(
            "human_reviewer IS NULL OR length(btrim(rationale)) > 0",
            name="chk_screening_override_rationale",
        ),
        CheckConstraint(
            "decision <> 'POTENTIAL_MATCH' OR disposition = 'PENDING' "
            "OR (human_reviewer IS NOT NULL AND length(btrim(rationale)) > 0)",
            name="chk_screening_potential_match_hitl",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<ScreeningDecision {self.id} {self.counterparty_normalized!r} "
            f"{self.decision}/{self.disposition} via {self.matching_engine}>"
        )
