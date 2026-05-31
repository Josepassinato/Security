-- Migration 049: PLD/FT operational maturity.
--
-- Adds monthly metrics support, recurring/near-real-time ingestion control,
-- PLD-specific hash-chained audit log, and structured regulatory exports that
-- require human approval before export.

CREATE TABLE IF NOT EXISTS pld_ft_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    actor_id UUID,
    actor_email TEXT NOT NULL DEFAULT '',
    actor_role TEXT NOT NULL DEFAULT '',
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    resource_id TEXT NOT NULL DEFAULT '',
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    prev_hash TEXT,
    entry_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pld_ft_ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'api',
    status TEXT NOT NULL DEFAULT 'active',
    interval_seconds INTEGER NOT NULL DEFAULT 300,
    auto_case_min_score INTEGER NOT NULL DEFAULT 65,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    last_result JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pld_ft_regulatory_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    case_id UUID NOT NULL REFERENCES pld_ft_cases(id) ON DELETE CASCADE,
    export_type TEXT NOT NULL DEFAULT 'coaf_internal',
    status TEXT NOT NULL DEFAULT 'draft',
    structured_payload JSONB NOT NULL,
    approval_note TEXT NOT NULL DEFAULT '',
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    exported_at TIMESTAMPTZ,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pld_ft_audit_tenant_created
    ON pld_ft_audit_log (tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pld_ft_audit_tenant_hash
    ON pld_ft_audit_log (tenant_id, created_at DESC)
    WHERE entry_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_pld_ft_ingestion_jobs_due
    ON pld_ft_ingestion_jobs (tenant_id, status, next_run_at);

CREATE INDEX IF NOT EXISTS idx_pld_ft_reg_exports_case_status
    ON pld_ft_regulatory_exports (tenant_id, case_id, status, created_at DESC);
