-- 050_screening_decisions.sql
--
-- Sanctions Screening Evidence Ledger — Phase 1 of the AML Evidence Layer.
--
-- Regra-mãe (product owner, signed 2026-06-26):
--   "O produto não decide, ele prova. Toda decisão de match vem de uma engine
--    de screening reconhecida e fica atribuída a ela."
--
-- This table is the IMMUTABLE LEDGER ("livro-razão") of sanctions-screening
-- decisions. It is deliberately SEPARATE from pld_ft_cases, which is the
-- mutable workbench ("caderno de trabalho"): a case changes status many times;
-- the screening decisions that built it never change. A screening_decision
-- references its case (case_id), never the other way around.
--
-- Attribution model (signed decision, 2026-06-26):
--   We separate "who matched the name" from "who witnessed the list version":
--     * matching_engine    — who produced the match (e.g. complyadvantage)
--     * list_of_record     — the versioned source that witnesses the list
--                            (e.g. opensanctions, or the public OFAC file)
--     * list_dataset       — dataset id of record (e.g. us_ofac_sdn)
--     * list_version       — the dataset version/release of record
--     * list_release_date  — publication date of that version (UTC)
--   Independence of the version-witness from the matching vendor is MORE
--   defensible in an OFAC exam, not less.
--
-- Immutability is enforced three ways (defence-in-depth, mirroring
-- 004_audit_log.sql + 046_investigation_events_hash_chain.sql):
--   1. Trigger denies UPDATE/DELETE on the normal SQL path.
--   2. Hash chain (prev_hash/entry_hash) catches what the trigger cannot
--      (whole-table reset, PITR forgery, heap tampering) — verified offline.
--   3. RLS FORCE keeps tenants isolated.
-- A disposition change is a NEW chained record, never an UPDATE.
--
-- Retention: 5 years minimum (OFAC/FinCEN), immutable the whole period.
-- All timestamps stored UTC (TIMESTAMPTZ); rendered in the examiner's tz.

BEGIN;

CREATE TABLE IF NOT EXISTS screening_decisions (
    id                      UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id               UUID         NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Reference to the mutable working case. RESTRICT, not CASCADE/SET NULL:
    -- the ledger protects itself — a case cannot be deleted while screening
    -- decisions reference it, and an immutable row is never orphaned by a
    -- SET NULL (which the immutability trigger would block anyway).
    case_id                 UUID         REFERENCES pld_ft_cases(id) ON DELETE RESTRICT,

    -- Counterparty (raw as received + normalized form used for matching).
    counterparty_name       TEXT         NOT NULL,
    counterparty_normalized TEXT         NOT NULL,
    counterparty_id         TEXT         NOT NULL,
    counterparty_id_type    TEXT         NOT NULL,

    -- Attribution: who matched vs. who witnesses the list version.
    matching_engine         TEXT         NOT NULL,
    list_of_record          TEXT         NOT NULL,
    list_source             TEXT         NOT NULL,
    list_dataset            TEXT         NOT NULL,
    list_version            TEXT         NOT NULL,
    list_release_date       TIMESTAMPTZ  NOT NULL,

    -- Scoring: raw engine payload is sacred (proof of what the engine said);
    -- match_score is DERIVED by a versioned, isolated rule. Storing the raw
    -- lets us re-derive a new ruler without re-screening.
    engine_raw_result       JSONB        NOT NULL,
    match_score             INTEGER      NOT NULL,
    scoring_rule_version    TEXT         NOT NULL,

    -- Decision + disposition.
    decision                TEXT         NOT NULL,
    disposition             TEXT         NOT NULL,

    -- Human-in-the-loop: null reviewer == automatic (must be visible).
    -- rationale required when a human is in the loop.
    human_reviewer          TEXT,
    rationale               TEXT         NOT NULL DEFAULT '',

    -- When the screening happened (engine), and when the row was written.
    screened_at             TIMESTAMPTZ  NOT NULL,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT now(),

    -- Tamper-evident hash chain (nullable for genesis / legacy tolerance).
    prev_hash               VARCHAR(64),
    entry_hash              VARCHAR(64),

    CONSTRAINT chk_screening_match_score_range
        CHECK (match_score BETWEEN 0 AND 100),

    CONSTRAINT chk_screening_id_type
        CHECK (counterparty_id_type IN ('CPF','CNPJ','PASSPORT','WALLET','OTHER')),

    CONSTRAINT chk_screening_list_source
        CHECK (list_source IN ('OFAC_SDN','OFAC_CONSOLIDATED','UN','EU','PEP','ADVERSE_MEDIA')),

    CONSTRAINT chk_screening_decision
        CHECK (decision IN ('NO_MATCH','POTENTIAL_MATCH','TRUE_MATCH','ESCALATED')),

    CONSTRAINT chk_screening_disposition
        CHECK (disposition IN ('CLEARED_FALSE_POSITIVE','BLOCKED','REPORTED','PENDING')),

    -- Override rationale: a human review must carry a written rationale.
    CONSTRAINT chk_screening_override_rationale
        CHECK (human_reviewer IS NULL OR length(btrim(rationale)) > 0),

    -- HITL: a POTENTIAL_MATCH never auto-resolves. If it is resolved
    -- (disposition <> PENDING) it MUST carry a human reviewer + rationale.
    CONSTRAINT chk_screening_potential_match_hitl
        CHECK (
            decision <> 'POTENTIAL_MATCH'
            OR disposition = 'PENDING'
            OR (human_reviewer IS NOT NULL AND length(btrim(rationale)) > 0)
        )
);

-- ── Indexes ──────────────────────────────────────────────────────────────────
-- Chain tail lookup per tenant (writer reads the latest hashed entry).
CREATE INDEX IF NOT EXISTS idx_screening_chain_tail
    ON screening_decisions (tenant_id, created_at DESC, id DESC)
    WHERE entry_hash IS NOT NULL;
-- Offline chain verification.
CREATE INDEX IF NOT EXISTS idx_screening_entry_hash
    ON screening_decisions (entry_hash)
    WHERE entry_hash IS NOT NULL;
-- Counterparty re-screening / lookup.
CREATE INDEX IF NOT EXISTS idx_screening_counterparty_id
    ON screening_decisions (tenant_id, counterparty_id_type, counterparty_id);
CREATE INDEX IF NOT EXISTS idx_screening_counterparty_norm
    ON screening_decisions (tenant_id, counterparty_normalized);
-- Case link.
CREATE INDEX IF NOT EXISTS idx_screening_case
    ON screening_decisions (tenant_id, case_id)
    WHERE case_id IS NOT NULL;
-- "Which list version did we run against" / re-screen on list update.
CREATE INDEX IF NOT EXISTS idx_screening_list_version
    ON screening_decisions (tenant_id, list_dataset, list_release_date DESC);
-- Decision/disposition filtering (review queue, reporting).
CREATE INDEX IF NOT EXISTS idx_screening_decision_disposition
    ON screening_decisions (tenant_id, decision, disposition, created_at DESC);

-- ── Immutability: deny UPDATE and DELETE via trigger ─────────────────────────
CREATE OR REPLACE FUNCTION screening_decisions_immutable()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'screening_decisions rows are immutable (attempted %)', TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS trg_screening_decisions_immutable ON screening_decisions;
CREATE TRIGGER trg_screening_decisions_immutable
    BEFORE UPDATE OR DELETE ON screening_decisions
    FOR EACH ROW EXECUTE FUNCTION screening_decisions_immutable();

-- ── RLS: each tenant sees only its own rows ──────────────────────────────────
ALTER TABLE screening_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE screening_decisions FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS screening_tenant ON screening_decisions;
CREATE POLICY screening_tenant ON screening_decisions
    USING (tenant_id = current_tenant_id() OR current_tenant_id() IS NULL);

COMMIT;
