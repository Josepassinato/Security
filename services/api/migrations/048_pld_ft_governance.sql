-- Migration 048: PLD/FT governance, continuous risk and case workflow.

ALTER TABLE pld_ft_cases
    ADD COLUMN IF NOT EXISTS assignee TEXT,
    ADD COLUMN IF NOT EXISTS priority TEXT NOT NULL DEFAULT 'normal',
    ADD COLUMN IF NOT EXISTS sla_due_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS reopened_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS workflow JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS pld_ft_customer_risk (
    tenant_id UUID NOT NULL,
    customer_id TEXT NOT NULL,
    risk_score INTEGER NOT NULL DEFAULT 0,
    severity TEXT NOT NULL DEFAULT 'low',
    total_cases INTEGER NOT NULL DEFAULT 0,
    open_cases INTEGER NOT NULL DEFAULT 0,
    escalated_cases INTEGER NOT NULL DEFAULT 0,
    false_positive_cases INTEGER NOT NULL DEFAULT 0,
    total_amount NUMERIC NOT NULL DEFAULT 0,
    top_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    last_case_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, customer_id)
);

CREATE TABLE IF NOT EXISTS pld_ft_rule_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    version_name TEXT NOT NULL,
    thresholds JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'draft',
    rationale TEXT NOT NULL DEFAULT '',
    created_by UUID,
    submitted_at TIMESTAMPTZ,
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    rejected_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, version_name)
);

CREATE TABLE IF NOT EXISTS pld_ft_case_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    case_id UUID NOT NULL REFERENCES pld_ft_cases(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pld_ft_case_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    case_id UUID NOT NULL REFERENCES pld_ft_cases(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT '',
    file_size INTEGER NOT NULL DEFAULT 0,
    description TEXT NOT NULL DEFAULT '',
    storage_url TEXT NOT NULL DEFAULT '',
    uploaded_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pld_ft_customer_risk_tenant_score
    ON pld_ft_customer_risk (tenant_id, risk_score DESC);

CREATE INDEX IF NOT EXISTS idx_pld_ft_rule_versions_tenant_status
    ON pld_ft_rule_versions (tenant_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pld_ft_case_comments_case_created
    ON pld_ft_case_comments (tenant_id, case_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pld_ft_case_attachments_case_created
    ON pld_ft_case_attachments (tenant_id, case_id, created_at DESC);
