-- Migration 047: PLD/FT operational module.
--
-- Persists transaction-import analysis, generated dossiers, human case
-- decisions, and tenant-level threshold calibration for the Brazilian
-- fintech PLD/FT module.

CREATE TABLE IF NOT EXISTS pld_ft_thresholds (
    tenant_id UUID PRIMARY KEY,
    thresholds JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pld_ft_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    institution TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'json',
    payload_hash TEXT NOT NULL,
    transaction_count INTEGER NOT NULL DEFAULT 0,
    dossier JSONB NOT NULL,
    risk_score INTEGER NOT NULL DEFAULT 0,
    severity TEXT NOT NULL DEFAULT 'low',
    case_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pld_ft_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    import_id UUID REFERENCES pld_ft_imports(id) ON DELETE SET NULL,
    dossier_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'novo',
    institution TEXT NOT NULL,
    risk_score INTEGER NOT NULL DEFAULT 0,
    severity TEXT NOT NULL DEFAULT 'low',
    dossier JSONB NOT NULL,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, dossier_id)
);

CREATE TABLE IF NOT EXISTS pld_ft_case_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    case_id UUID NOT NULL REFERENCES pld_ft_cases(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    analyst TEXT NOT NULL DEFAULT '',
    decided_by UUID,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pld_ft_imports_tenant_created
    ON pld_ft_imports (tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pld_ft_cases_tenant_status_created
    ON pld_ft_cases (tenant_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pld_ft_cases_tenant_risk
    ON pld_ft_cases (tenant_id, risk_score DESC);

CREATE INDEX IF NOT EXISTS idx_pld_ft_case_decisions_tenant_case
    ON pld_ft_case_decisions (tenant_id, case_id, decided_at DESC);
