-- 046_investigation_events_hash_chain.sql
--
-- Add tamper-evident hash-chaining to the investigation_events table —
-- CARD-016 Item 1 (Bacen Evidence Engine).
--
-- Why
-- ===
-- Migration 008 set up ``investigation_events`` as append-only via the
-- ``trg_inv_events_immutable`` trigger plus tenant isolation via RLS.
-- That defends against in-flight UPDATE/DELETE. It does NOT defend
-- against a privileged operator (or stolen DB credentials) issuing a
-- DROP/RECREATE / TRUNCATE and forging a replacement history that
-- still satisfies the trigger.
--
-- For the Bacen Evidence Engine that gap is unacceptable: the whole
-- pitch is that every agent decision is defensible in a fiscalização.
-- A hash chain closes the gap. Each row carries:
--
--   * prev_hash   — the entry_hash of the previous event for the same
--                   (tenant_id, run_id) pair, or NULL for the first.
--   * entry_hash  — SHA-256 over a canonical serialization of the
--                   row's evidence-bearing fields, mixed with prev_hash.
--
-- Verification walks the chain per (tenant_id, run_id) and proves no
-- row was deleted, reordered, or rewritten. The trigger-enforced
-- immutability still applies; the chain catches the cases the trigger
-- cannot (whole-table reset, point-in-time PITR with selective drops,
-- physical row tampering at the heap level, etc).
--
-- This mirrors the pattern 043_audit_log_hash_chain.sql established
-- for audit_log; the two chains are independent (different scope) and
-- can be verified side by side during an inspection.
--
-- Backwards compatibility
-- =======================
-- Both columns are nullable + the ALTERs are idempotent, so existing
-- deployments can adopt the chain without a backfill flag day:
--
--   * Existing rows stay with NULL prev_hash + NULL entry_hash.
--   * The writer (services/agents/app/investigator/ledger.py) is
--     updated separately to populate the hashes on every NEW insert,
--     using ``app.evidence_pack.merkle.hash_entry``.
--   * Chain verification walks only the rows that carry hashes; a
--     later card may backfill historic rows once the schema is stable.

BEGIN;

ALTER TABLE investigation_events
    ADD COLUMN IF NOT EXISTS prev_hash  VARCHAR(64),
    ADD COLUMN IF NOT EXISTS entry_hash VARCHAR(64);

-- Index supports the "latest hashed entry per (tenant, run)" lookup
-- the chain writer performs on every insert.
CREATE INDEX IF NOT EXISTS idx_inv_events_chain_tail
    ON investigation_events(tenant_id, run_id, seq DESC)
    WHERE entry_hash IS NOT NULL;

-- Index supports offline chain verification — a verifier walks rows
-- ordered by seq and confirms every link.
CREATE INDEX IF NOT EXISTS idx_inv_events_entry_hash
    ON investigation_events(entry_hash)
    WHERE entry_hash IS NOT NULL;

COMMIT;
