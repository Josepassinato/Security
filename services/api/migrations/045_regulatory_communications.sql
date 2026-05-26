-- 045_regulatory_communications.sql
--
-- Auto-comunicação Bacen 24h + ANPD (CARD-014).
--
-- Why
-- ───
-- A Resolução BCB 85/2021 Art. 9 obriga a fintech a comunicar incidentes
-- relevantes ao Bacen em até 24h. A LGPD Art. 48 §1º (cumulado com a IN
-- ANPD 03/2024) obriga notificação à ANPD em prazo razoável quando o
-- incidente envolve dado pessoal. Hoje o Quarry gera o rascunho .md no
-- demo (CARD-012); o que falta é o fluxo operacional dentro do Case
-- Workspace: cronômetro 24h, gate humano de 1-clique, envio efetivo via
-- canal configurável, e ledger imutável vinculando rascunho → decisão
-- humana → envio.
--
-- Esta tabela é o lastro probatório desse fluxo. Cada linha representa
-- um artefato regulatório (bacen | anpd) num determinado estado do seu
-- ciclo de vida. Hash chain reusa o algoritmo de
-- ``app.services.audit_hash`` adaptado pra esta tabela: cada inserção
-- ou transição de estado fecha sobre ``prev_hash`` da linha anterior do
-- mesmo tenant + mesmo ``kind``, encadeando a cronologia probatória
-- exigida pela LGPD Art. 50 (registro de operações).
--
-- Decisões deliberadas
-- ────────────────────
-- - ``status`` é texto enumerado em vez de ENUM nativo do PG porque a
--   trilha probatória trata transição como insert (nova linha), não
--   update da mesma linha. Isso mantém a tabela append-only por
--   convenção, consistente com ``audit_log``. Quem precisa do estado
--   "atual" lê a linha mais recente por ``(tenant_id, case_id, kind)``.
-- - ``deadline_at`` é calculado em momento de geração (created_at +
--   24h ou intervalo definido na config do tenant) e materializado pra
--   permitir índice rápido em "vencendo nas próximas 6h" sem
--   reaplicar lógica em SQL.
-- - ``approver_email`` espelha ``audit_log.actor_email``: o registro
--   sobrevive ao tombamento de usuários e mantém valor probatório
--   independente da tabela ``users``.
-- - ``sent_via`` distingue ``email`` / ``webhook`` / ``sisbacen`` /
--   ``manual``. ``sisbacen`` fica para quando o Bacen publicar API
--   pública; hoje é stub que retorna NotImplemented com mensagem clara.
-- - PII bruta NÃO é persistida em ``draft_md``. O detector
--   ``is_pii_breach`` opera sobre o caso, mas o template já cita
--   agregados e IDs internos. Isso é mitigation do Risco 4 do CARD-014.

BEGIN;

CREATE TABLE IF NOT EXISTS regulatory_communications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    case_id         UUID REFERENCES aisoc_cases(id) ON DELETE SET NULL,
    kind            VARCHAR(20) NOT NULL CHECK (kind IN ('bacen', 'anpd')),
    status          VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'submitted', 'expired', 'cancelled')),

    draft_md        TEXT NOT NULL,
    draft_meta      JSONB,

    deadline_at     TIMESTAMPTZ NOT NULL,
    submitted_at    TIMESTAMPTZ,
    expired_at      TIMESTAMPTZ,

    approver_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    approver_email  VARCHAR(255),
    approver_typed_name  VARCHAR(255),

    sent_via        VARCHAR(20) CHECK (sent_via IN ('email', 'webhook', 'sisbacen', 'manual')),
    sent_to         VARCHAR(500),
    dispatch_result JSONB,

    -- Hash chain (mesma semântica de audit_log.prev_hash/entry_hash).
    -- Chain é por (tenant_id, kind) — o relógio do Bacen e o relógio da
    -- ANPD são auditados em separado pelos reguladores distintos.
    prev_hash       VARCHAR(64),
    entry_hash      VARCHAR(64),

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata        JSONB
);

-- Permite localizar rapidamente "qual é a comunicação ativa pra este caso"
-- e "quais expiram nas próximas N horas".
CREATE INDEX IF NOT EXISTS idx_regcomm_tenant_case
    ON regulatory_communications (tenant_id, case_id, kind);

CREATE INDEX IF NOT EXISTS idx_regcomm_tenant_status_deadline
    ON regulatory_communications (tenant_id, status, deadline_at)
    WHERE status = 'draft';

CREATE INDEX IF NOT EXISTS idx_regcomm_tenant_kind_created
    ON regulatory_communications (tenant_id, kind, created_at DESC);

-- RLS — mesmo padrão das outras tabelas multi-tenant.
-- Política usa a função ``current_tenant_id()`` definida em 002_rls.sql.
ALTER TABLE regulatory_communications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS regulatory_communications_tenant_isolation
    ON regulatory_communications;

CREATE POLICY regulatory_communications_tenant_isolation
    ON regulatory_communications
    USING (tenant_id = current_tenant_id())
    WITH CHECK (tenant_id = current_tenant_id());

-- Append-only enforcement. As transições de estado (draft → submitted)
-- são inserções de novas linhas; updates só são permitidos pelo serviço
-- de dispatch via security-definer (pra gravar dispatch_result após
-- envio efetivo). Esta versão é permissiva no UPDATE pra simplificar o
-- MVP — quando a UI de approval entrar (próxima sessão), endurecer.
-- DELETE é sempre bloqueado.
CREATE OR REPLACE FUNCTION regulatory_communications_no_delete()
    RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'regulatory_communications is append-only — DELETE forbidden';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_regcomm_no_delete ON regulatory_communications;
CREATE TRIGGER trg_regcomm_no_delete
    BEFORE DELETE ON regulatory_communications
    FOR EACH ROW EXECUTE FUNCTION regulatory_communications_no_delete();

COMMIT;
