-- 051_screening_decisions_identity_fields.sql
--
-- §1 (Identification & Scope) completeness for the screening dossier, plus the
-- name-only screening decision.
--
-- Changes (all additive / idempotent — 050 is the canonical base):
--   1. counterparty_id becomes NULLABLE. A screening can legitimately run on a
--      name alone (no document at decision time); the dossier template renders
--      "Screening por nome — sem documento" for that case. Forcing NOT NULL
--      would push callers to invent a sentinel, which is worse for evidence.
--   2. counterparty_jurisdiction — §1 asks "qual jurisdição"; ambiguity here is
--      the first thing an examiner distrusts.
--   3. screening_trigger — §1 asks "qual transação ou onboarding gerou o
--      screening" (e.g. 'onboarding', 'transaction:<ref>', 'rescreen').
--
-- Both new columns are evidence-bearing identity fields, so the ledger writer
-- folds them into the hash chain (screening-decisions-v1 field set extended
-- pre-release; no shipped chain to break — migration 050 not yet applied to
-- production). They are nullable so existing/legacy rows stay valid.

BEGIN;

ALTER TABLE screening_decisions
    ALTER COLUMN counterparty_id DROP NOT NULL;

ALTER TABLE screening_decisions
    ADD COLUMN IF NOT EXISTS counterparty_jurisdiction TEXT,
    ADD COLUMN IF NOT EXISTS screening_trigger         TEXT;

COMMIT;
