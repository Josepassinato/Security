'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Database, Download, FileSliders, FileText, Gauge, History, RefreshCw, ShieldCheck } from 'lucide-react';
import {
  approvePldRegulatoryExportBackend,
  createPldIngestionJobBackend,
  createPldRegulatoryExportBackend,
  createPldRuleVersionBackend,
  decidePldRuleVersionBackend,
  downloadPldExecutiveReportBackend,
  downloadPldRegulatoryExportBackend,
  getPldExecutiveReportBackend,
  getPldMonthlyMetricsBackend,
  ingestPldStreamBackend,
  listPldAuditLogBackend,
  listPldCasesBackend,
  listPldCustomerRiskBackend,
  listPldIngestionJobsBackend,
  listPldRegulatoryExportsBackend,
  listPldRuleVersionsBackend,
  recomputePldCustomerRiskBackend,
  runPldIngestionJobBackend,
  type PldAuditEntry,
  type PldIngestionJob,
  type PldMonthlyMetrics,
  type PldRegulatoryExport,
  simulatePldRulesBackend,
  type PldCustomerRiskRecord,
  type PldExecutiveReport,
  type PldRuleSimulationResponse,
  type PldRuleVersion,
} from '@/lib/pldft/api';
import type { PldCaseRecord } from '@/lib/pldft/cases';
import type { PldThresholds } from '@/lib/pldft/engine';

const BRL = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

const SAMPLE_STREAM_PAYLOAD = {
  institution: 'Quarry Demo Bank',
  customers: [
    { customerId: 'C-STREAM-001', declaredMonthlyIncome: 4200, accountAgeDays: 8 },
    { customerId: 'C-STREAM-002', declaredMonthlyIncome: 9000, accountAgeDays: 640 },
  ],
  transactions: [
    {
      id: `TX-IN-${Date.now()}`,
      timestamp: new Date().toISOString(),
      accountId: 'ACC-STREAM-001',
      customerId: 'C-STREAM-001',
      direction: 'in',
      rail: 'Pix',
      amount: 18600,
      counterpartyId: 'SRC-ALTA-001',
      deviceId: 'DEV-STREAM-1',
    },
    {
      id: `TX-OUT-${Date.now()}`,
      timestamp: new Date(Date.now() + 20 * 60 * 1000).toISOString(),
      accountId: 'ACC-STREAM-001',
      customerId: 'C-STREAM-001',
      direction: 'out',
      rail: 'Pix',
      amount: 17250,
      counterpartyId: 'DST-ALTA-001',
      deviceId: 'DEV-STREAM-1',
    },
  ],
};

function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function PldFtGovernance() {
  const [customers, setCustomers] = useState<PldCustomerRiskRecord[]>([]);
  const [versions, setVersions] = useState<PldRuleVersion[]>([]);
  const [cases, setCases] = useState<PldCaseRecord[]>([]);
  const [metrics, setMetrics] = useState<PldMonthlyMetrics | null>(null);
  const [jobs, setJobs] = useState<PldIngestionJob[]>([]);
  const [auditEntries, setAuditEntries] = useState<PldAuditEntry[]>([]);
  const [auditChainOk, setAuditChainOk] = useState<boolean | null>(null);
  const [regulatoryExports, setRegulatoryExports] = useState<PldRegulatoryExport[]>([]);
  const [report, setReport] = useState<PldExecutiveReport | null>(null);
  const [simulation, setSimulation] = useState<PldRuleSimulationResponse | null>(null);
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [versionName, setVersionName] = useState(`PLD-${new Date().toISOString().slice(0, 10)}`);
  const [thresholdKey, setThresholdKey] = useState<keyof PldThresholds>('passThroughMinAmount');
  const [thresholdValue, setThresholdValue] = useState('5000');
  const [rationale, setRationale] = useState('Ajuste proposto para reduzir falso positivo sem remover revisão humana.');
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const thresholdPatch = useMemo(() => ({ [thresholdKey]: Number(thresholdValue) || 0 }) as Partial<PldThresholds>, [thresholdKey, thresholdValue]);

  useEffect(() => {
    void refresh();
  }, []);

  async function refresh() {
    setLoading(true);
    try {
      const [risk, ruleVersions, executive] = await Promise.all([
        listPldCustomerRiskBackend(),
        listPldRuleVersionsBackend(),
        getPldExecutiveReportBackend(),
      ]);
      const [caseList, monthly, jobList, audit, exportsList] = await Promise.all([
        listPldCasesBackend(),
        getPldMonthlyMetricsBackend(),
        listPldIngestionJobsBackend(),
        listPldAuditLogBackend(),
        listPldRegulatoryExportsBackend(),
      ]);
      setCustomers(risk);
      setVersions(ruleVersions);
      setReport(executive);
      setCases(caseList);
      setSelectedCaseId((current) => current || caseList[0]?.id || '');
      setMetrics(monthly);
      setJobs(jobList);
      setAuditEntries(audit.entries);
      setAuditChainOk(audit.chainVerifiedForWindow);
      setRegulatoryExports(exportsList);
      setNotice(null);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Falha ao carregar governança PLD/FT.');
    } finally {
      setLoading(false);
    }
  }

  async function recomputeRisk() {
    const risk = await recomputePldCustomerRiskBackend();
    setCustomers(risk);
    setNotice('Score contínuo por cliente recalculado.');
  }

  async function simulate() {
    const result = await simulatePldRulesBackend(thresholdPatch);
    setSimulation(result);
    setNotice('Simulação de tuning executada.');
  }

  async function createVersion() {
    const created = await createPldRuleVersionBackend(versionName, thresholdPatch, rationale);
    setVersions((current) => [created, ...current.filter((item) => item.id !== created.id)]);
    setNotice('Versão de regra criada como rascunho.');
  }

  async function decide(versionId: string, action: 'submit' | 'approve' | 'reject') {
    const updated = await decidePldRuleVersionBackend(versionId, action, rationale);
    setVersions((current) => current.map((item) => item.id === versionId ? updated : item));
    setNotice(action === 'approve' ? 'Versão aprovada e thresholds ativados.' : 'Status da versão atualizado.');
    if (action === 'approve') await refresh();
  }

  async function downloadExecutivePdf() {
    const blob = await downloadPldExecutiveReportBackend();
    downloadBlob('quarry-pldft-relatorio-executivo.pdf', blob);
  }

  async function ingestStreamSample() {
    const result = await ingestPldStreamBackend(SAMPLE_STREAM_PAYLOAD, 65);
    setNotice(result.createdCase ? `Ingestao quase real processada e caso ${result.createdCase.id} aberto.` : 'Ingestao quase real processada sem abertura de caso.');
    await refresh();
  }

  async function createRecurringJob() {
    const created = await createPldIngestionJobBackend({
      name: `Stream PLD demo ${new Date().toISOString().slice(0, 16)}`,
      sourceType: 'api-stream',
      intervalSeconds: 300,
      autoCaseMinScore: 65,
      config: { samplePayload: SAMPLE_STREAM_PAYLOAD },
    });
    setJobs((current) => [created, ...current]);
    setNotice('Job recorrente criado. No MVP ele executa o payload autorizado em config.samplePayload.');
  }

  async function runJob(jobId: string) {
    const result = await runPldIngestionJobBackend(jobId);
    setNotice(`Job executado: ${String(result.result.status || 'processado')}.`);
    await refresh();
  }

  async function createRegulatoryExport() {
    if (!selectedCaseId) {
      setNotice('Selecione um caso antes de criar a exportacao regulatoria.');
      return;
    }
    const created = await createPldRegulatoryExportBackend(selectedCaseId, 'Rascunho estruturado criado para aprovacao humana.');
    setRegulatoryExports((current) => [created, ...current]);
    setNotice('Exportacao estruturada criada e aguardando aprovacao do compliance officer.');
  }

  async function approveExport(exportId: string) {
    const approved = await approvePldRegulatoryExportBackend(exportId, 'Aprovado para download regulatorio apos revisao humana.');
    setRegulatoryExports((current) => current.map((item) => (item.id === exportId ? approved : item)));
    setNotice('Exportacao aprovada para download.');
  }

  async function downloadExport(exportId: string) {
    const blob = await downloadPldRegulatoryExportBackend(exportId);
    downloadBlob(`quarry-pldft-export-${exportId}.json`, blob);
    await refresh();
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="border-b border-white/10 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <Link href="/br/pld-ft" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
            <ArrowLeft className="h-4 w-4" />
            Voltar para PLD/FT
          </Link>
          <div className="mt-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-200">Governança operacional</p>
              <h1 className="mt-2 text-4xl font-semibold tracking-tight text-white">Comitê PLD/FT e tuning auditável</h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
                Score contínuo por cliente, simulação de regras, versionamento com aprovação, workflow de casos e relatório executivo.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={refresh} className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-sm font-semibold text-slate-200">
                <RefreshCw className="h-4 w-4" />
                Atualizar
              </button>
              <button type="button" onClick={downloadExecutivePdf} className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-slate-950">
                <Download className="h-4 w-4" />
                PDF executivo
              </button>
            </div>
          </div>
          {notice && <p className="mt-4 rounded-2xl border border-blue-400/30 bg-blue-500/10 p-4 text-sm text-blue-100">{notice}</p>}
        </div>
      </section>

      <section className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-6">
          <section className="grid gap-4 md:grid-cols-5">
            {[
              ['Casos', report?.kpis.totalCases ?? 0],
              ['Abertos', report?.kpis.openCases ?? 0],
              ['Críticos', report?.kpis.criticalCases ?? 0],
              ['Escalados', report?.kpis.escalatedCases ?? 0],
              ['SLA vencido', report?.kpis.overdueCases ?? 0],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                <p className="text-xs uppercase tracking-[0.16em] text-slate-400">{label}</p>
                <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
              </div>
            ))}
          </section>

          <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <h2 className="text-xl font-semibold text-white">Métricas mensais PLD/FT</h2>
              <p className="mt-2 text-sm text-slate-400">Alertas, arquivamentos, escalonamentos, SLA e ruído por regra no mês {metrics?.month || 'atual'}.</p>
              <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
                {[
                  ['Alertas', metrics?.kpis.alerts ?? 0],
                  ['Arquivados', metrics?.kpis.archived ?? 0],
                  ['Escalados', metrics?.kpis.escalated ?? 0],
                  ['SLA', `${metrics?.kpis.slaComplianceRate ?? 0}%`],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                    <p className="text-xs uppercase tracking-[0.14em] text-slate-500">{label}</p>
                    <p className="mt-2 text-xl font-semibold text-white">{value}</p>
                  </div>
                ))}
              </div>
              <div className="mt-5 grid gap-2">
                {(metrics?.recommendations || []).map((item) => (
                  <p key={item} className="rounded-2xl border border-white/10 bg-slate-950/70 p-3 text-sm text-slate-300">{item}</p>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <h2 className="text-xl font-semibold text-white">Regras mais ruidosas</h2>
              <div className="mt-5 overflow-x-auto">
                <table className="w-full min-w-[520px] text-left text-sm">
                  <thead className="text-xs uppercase tracking-[0.14em] text-slate-500">
                    <tr>
                      <th className="py-2">Regra</th>
                      <th>Ocorrências</th>
                      <th>Falso positivo</th>
                      <th>Ruído</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(metrics?.noisyRules || []).map((rule) => (
                      <tr key={rule.ruleId} className="border-t border-white/10">
                        <td className="py-3 font-semibold text-white">{rule.ruleId}</td>
                        <td>{rule.count}</td>
                        <td>{rule.falsePositive}</td>
                        <td>{rule.noiseScore}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {metrics && metrics.noisyRules.length === 0 && <p className="py-6 text-sm text-slate-400">Ainda não há ruído calculado para o mês.</p>}
              </div>
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <h2 className="inline-flex items-center gap-2 text-xl font-semibold text-white">
                <Database className="h-5 w-5 text-cyan-200" />
                Ingestão recorrente e quase real
              </h2>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                O modo quase real recebe eventos, executa regras determinísticas e abre caso automaticamente acima do score mínimo.
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                <button type="button" onClick={ingestStreamSample} className="rounded-xl bg-cyan-500 px-4 py-3 text-sm font-semibold text-slate-950">Simular evento agora</button>
                <button type="button" onClick={createRecurringJob} className="rounded-xl border border-white/10 px-4 py-3 text-sm font-semibold text-slate-200">Criar job recorrente</button>
              </div>
              <div className="mt-5 grid gap-3">
                {jobs.map((job) => (
                  <article key={job.id} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                      <div>
                        <p className="font-semibold text-white">{job.name}</p>
                        <p className="mt-1 text-xs text-slate-400">{job.status} · {job.sourceType} · a cada {job.intervalSeconds}s · próximo {job.nextRunAt || 'sob demanda'}</p>
                        {job.lastResult?.status && <p className="mt-2 text-xs text-slate-500">Último resultado: {String(job.lastResult.status)}</p>}
                      </div>
                      <button type="button" onClick={() => runJob(job.id)} className="rounded-lg border border-white/10 px-3 py-2 text-xs font-semibold text-slate-200">Executar</button>
                    </div>
                  </article>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <h2 className="inline-flex items-center gap-2 text-xl font-semibold text-white">
                <History className="h-5 w-5 text-emerald-300" />
                RBAC e trilha hash PLD/FT
              </h2>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                Papéis suportados: analyst, compliance_officer, admin e auditor. Decisões sensíveis entram em cadeia hash dedicada.
              </p>
              <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                <p className="text-sm font-semibold text-white">Cadeia verificada na janela: {auditChainOk === null ? 'carregando' : auditChainOk ? 'sim' : 'não'}</p>
              </div>
              <div className="mt-5 max-h-80 space-y-3 overflow-auto pr-2">
                {auditEntries.slice(0, 10).map((entry) => (
                  <article key={entry.id} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-sm">
                    <p className="font-semibold text-white">{entry.action}</p>
                    <p className="mt-1 text-xs text-slate-400">{entry.actorEmail} · {entry.actorRole} · {entry.createdAt}</p>
                    <p className="mt-2 break-all text-xs text-slate-500">hash: {entry.entryHash}</p>
                  </article>
                ))}
                {auditEntries.length === 0 && <p className="text-sm text-slate-400">Nenhum evento auditável registrado ainda.</p>}
              </div>
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <div className="flex items-center justify-between gap-4">
                <h2 className="inline-flex items-center gap-2 text-xl font-semibold text-white">
                  <Gauge className="h-5 w-5 text-blue-200" />
                  Score contínuo por cliente
                </h2>
                <button type="button" onClick={recomputeRisk} className="rounded-xl border border-white/10 px-3 py-2 text-xs font-semibold text-slate-200">
                  Recalcular
                </button>
              </div>
              <div className="mt-5 overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead className="text-xs uppercase tracking-[0.14em] text-slate-500">
                    <tr>
                      <th className="py-2">Cliente</th>
                      <th>Score</th>
                      <th>Severidade</th>
                      <th>Casos</th>
                      <th>Abertos</th>
                      <th>Volume</th>
                      <th>Regras</th>
                    </tr>
                  </thead>
                  <tbody>
                    {customers.map((customer) => (
                      <tr key={customer.customerId} className="border-t border-white/10">
                        <td className="py-3 font-semibold text-white">{customer.customerId}</td>
                        <td>{customer.riskScore}/100</td>
                        <td>{customer.severity}</td>
                        <td>{customer.totalCases}</td>
                        <td>{customer.openCases}</td>
                        <td>{BRL.format(customer.totalAmount)}</td>
                        <td>{customer.topRules.map((rule) => `${rule.ruleId} (${rule.count})`).join(', ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!loading && customers.length === 0 && <p className="py-8 text-sm text-slate-400">Nenhum cliente com risco calculado.</p>}
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <h2 className="inline-flex items-center gap-2 text-xl font-semibold text-white">
                <FileSliders className="h-5 w-5 text-blue-200" />
                Simulação e tuning
              </h2>
              <div className="mt-5 grid gap-3">
                <select value={thresholdKey} onChange={(event) => setThresholdKey(event.target.value as keyof PldThresholds)} className="rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-white">
                  <option value="passThroughMinAmount">Valor mínimo conta de passagem</option>
                  <option value="passThroughWindowMinutes">Janela conta de passagem</option>
                  <option value="outboundFanoutMinTotal">Valor mínimo fan-out</option>
                  <option value="structuringMinTotal">Total mínimo fracionamento</option>
                  <option value="economicMismatchMultiplier">Multiplicador incompatibilidade econômica</option>
                </select>
                <input value={thresholdValue} onChange={(event) => setThresholdValue(event.target.value)} className="rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-white" />
                <textarea value={rationale} onChange={(event) => setRationale(event.target.value)} rows={3} className="rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-white" />
                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={simulate} className="rounded-xl bg-blue-500 px-4 py-3 text-sm font-semibold text-white">Simular</button>
                  <button type="button" onClick={createVersion} className="rounded-xl border border-white/10 px-4 py-3 text-sm font-semibold text-slate-200">Criar versão</button>
                </div>
              </div>
              {simulation && (
                <div className="mt-5 rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-sm leading-6 text-slate-300">
                  <p><strong className="text-white">Modo:</strong> {simulation.mode}</p>
                  <p><strong className="text-white">Pressão de falso positivo:</strong> {simulation.falsePositivePressure ?? 'n/a'}%</p>
                  <p>{simulation.estimatedImpact || simulation.recommendation}</p>
                  <p className="mt-2 text-slate-400">{simulation.nextStep}</p>
                </div>
              )}
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <h2 className="inline-flex items-center gap-2 text-xl font-semibold text-white">
                <ShieldCheck className="h-5 w-5 text-emerald-300" />
                Versões e aprovação do compliance officer
              </h2>
              <div className="mt-5 grid gap-3">
                <input value={versionName} onChange={(event) => setVersionName(event.target.value)} className="rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-white" />
                {versions.map((version) => (
                  <article key={version.id} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div>
                        <p className="font-semibold text-white">{version.versionName}</p>
                        <p className="mt-1 text-xs text-slate-400">{version.status} · {version.rationale}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button type="button" onClick={() => decide(version.id, 'submit')} className="rounded-lg border border-white/10 px-3 py-2 text-xs font-semibold">Submeter</button>
                        <button type="button" onClick={() => decide(version.id, 'approve')} className="rounded-lg bg-emerald-500 px-3 py-2 text-xs font-semibold text-white">Aprovar</button>
                        <button type="button" onClick={() => decide(version.id, 'reject')} className="rounded-lg border border-red-400/30 px-3 py-2 text-xs font-semibold text-red-100">Rejeitar</button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <h2 className="text-xl font-semibold text-white">Relatório executivo para diretoria/comitê</h2>
              <p className="mt-3 text-sm leading-7 text-slate-300">{report?.executiveSummary || 'Carregando relatório executivo...'}</p>
              <div className="mt-5 grid gap-3">
                {(report?.committeeRecommendations || []).map((item) => (
                  <div key={item} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-sm leading-6 text-slate-300">
                    {item}
                  </div>
                ))}
              </div>
              <div className="mt-5">
                <Link href="/br/pld-ft/cases" className="rounded-xl border border-white/10 px-4 py-3 text-sm font-semibold text-slate-200">
                  Abrir workflow de casos
                </Link>
              </div>
            </div>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <h2 className="inline-flex items-center gap-2 text-xl font-semibold text-white">
                  <FileText className="h-5 w-5 text-amber-200" />
                  Exportação regulatória estruturada
                </h2>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
                  Gera JSON estruturado para comunicação regulatória ou dossiê interno, mas bloqueia o download até aprovação humana.
                </p>
              </div>
              <div className="flex flex-col gap-2 sm:flex-row">
                <select value={selectedCaseId} onChange={(event) => setSelectedCaseId(event.target.value)} className="min-w-[280px] rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-white">
                  <option value="">Selecione um caso</option>
                  {cases.map((item) => (
                    <option key={item.id} value={item.id}>{item.dossierId || item.id} · {item.status}</option>
                  ))}
                </select>
                <button type="button" onClick={createRegulatoryExport} className="rounded-xl bg-amber-400 px-4 py-3 text-sm font-semibold text-slate-950">Criar exportação</button>
              </div>
            </div>
            <div className="mt-5 grid gap-3">
              {regulatoryExports.map((item) => (
                <article key={item.id} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <p className="font-semibold text-white">{item.exportType} · {item.status}</p>
                      <p className="mt-1 text-xs text-slate-400">Caso {item.caseId} · criado em {item.createdAt}</p>
                      <p className="mt-2 text-xs text-slate-500">{item.approvalNote || 'Aguardando nota de aprovação.'}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button type="button" onClick={() => approveExport(item.id)} className="rounded-lg bg-emerald-500 px-3 py-2 text-xs font-semibold text-white">Aprovar</button>
                      <button type="button" onClick={() => downloadExport(item.id)} className="rounded-lg border border-white/10 px-3 py-2 text-xs font-semibold text-slate-200">Baixar JSON</button>
                    </div>
                  </div>
                </article>
              ))}
              {regulatoryExports.length === 0 && <p className="text-sm text-slate-400">Nenhuma exportação regulatória criada ainda.</p>}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
