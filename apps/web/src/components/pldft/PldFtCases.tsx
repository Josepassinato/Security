'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Download, FileText, Search, Trash2 } from 'lucide-react';
import {
  addPldCaseDecision,
  listPldCases,
  pldCaseStatusLabels,
  removePldCase,
  type PldCaseRecord,
  type PldCaseStatus,
} from '@/lib/pldft/cases';
import { addPldCaseDecisionBackend, downloadPldCaseReportBackend, listPldCasesBackend } from '@/lib/pldft/api';
import { pldDossierToMarkdown } from '@/lib/pldft/engine';

const BRL = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

function download(filename: string, content: string, type = 'text/plain;charset=utf-8') {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function printCase(record: PldCaseRecord) {
  const html = `
    <html>
      <head>
        <title>${record.id}</title>
        <style>
          body{font-family:Inter,Arial,sans-serif;color:#111827;padding:32px;line-height:1.55}
          h1{font-size:28px;margin:0 0 8px}
          h2{margin-top:28px;border-bottom:1px solid #ddd;padding-bottom:6px}
          .kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:20px 0}
          .card{border:1px solid #ddd;border-radius:12px;padding:14px}
          .small{font-size:12px;color:#4b5563}
          li{margin-bottom:6px}
        </style>
      </head>
      <body>
        <p class="small">Quarry PLD/FT - documento para revisão humana</p>
        <h1>Dossiê ${record.id}</h1>
        <p><strong>Status:</strong> ${pldCaseStatusLabels[record.status]}</p>
        <p>${record.dossier.executiveSummary}</p>
        <div class="kpi">
          <div class="card"><strong>Score</strong><br/>${record.dossier.riskScore}/100</div>
          <div class="card"><strong>Severidade</strong><br/>${record.dossier.severity}</div>
          <div class="card"><strong>Volume</strong><br/>${BRL.format(record.dossier.totalAmount)}</div>
          <div class="card"><strong>Achados</strong><br/>${record.dossier.findings.length}</div>
        </div>
        <h2>Achados</h2>
        ${record.dossier.findings.map((finding) => `
          <div class="card">
            <h3>${finding.ruleId} - ${finding.title}</h3>
            <p>${finding.rationale}</p>
            <p><strong>Valor em escopo:</strong> ${BRL.format(finding.amountInScope)}</p>
            <p><strong>Transações:</strong> ${finding.transactionIds.join(', ')}</p>
            <ul>${finding.evidence.map((item) => `<li>${item}</li>`).join('')}</ul>
          </div>
        `).join('')}
        <h2>Decisões humanas</h2>
        ${record.decisions.length ? record.decisions.map((decision) => `
          <div class="card">
            <p><strong>${pldCaseStatusLabels[decision.status]}</strong> por ${decision.analyst || 'analista'} em ${decision.decidedAt}</p>
            <p>${decision.note || 'Sem nota.'}</p>
          </div>
        `).join('') : '<p>Nenhuma decisão registrada.</p>'}
        <h2>Observação legal</h2>
        <p>${record.dossier.disclaimer}</p>
      </body>
    </html>
  `;
  const popup = window.open('', '_blank');
  if (!popup) return;
  popup.document.write(html);
  popup.document.close();
  popup.focus();
  popup.print();
}

export function PldFtCases() {
  const [records, setRecords] = useState<PldCaseRecord[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [status, setStatus] = useState<PldCaseStatus>('em_revisao');
  const [analyst, setAnalyst] = useState('Analista PLD');
  const [note, setNote] = useState('');
  const [source, setSource] = useState<'postgres' | 'local'>('local');
  const [notice, setNotice] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'todos' | PldCaseStatus>('todos');
  const [severityFilter, setSeverityFilter] = useState<'todas' | string>('todas');
  const [query, setQuery] = useState('');

  useEffect(() => {
    void refresh();
  }, []);

  const selected = useMemo(
    () => records.find((record) => record.id === selectedId) || null,
    [records, selectedId],
  );
  const filteredRecords = useMemo(() => {
    const term = query.trim().toLowerCase();
    return records.filter((record) => {
      const matchesStatus = statusFilter === 'todos' || record.status === statusFilter;
      const matchesSeverity = severityFilter === 'todas' || record.dossier.severity === severityFilter;
      const searchable = [
        record.id,
        record.dossier.id,
        record.dossier.institution,
        record.dossier.executiveSummary,
        ...(record.dossier.findings || []).map((finding) => `${finding.ruleId} ${finding.title} ${finding.entityId}`),
      ].join(' ').toLowerCase();
      return matchesStatus && matchesSeverity && (!term || searchable.includes(term));
    });
  }, [records, query, severityFilter, statusFilter]);

  async function refresh() {
    try {
      const items = await listPldCasesBackend();
      setRecords(items);
      setSelectedId((current) => current && items.some((item) => item.id === current) ? current : items[0]?.id || null);
      setSource('postgres');
      setNotice(null);
    } catch {
      const items = listPldCases();
      setRecords(items);
      setSelectedId((current) => current && items.some((item) => item.id === current) ? current : items[0]?.id || null);
      setSource('local');
      setNotice('API indisponível. Mostrando fila local deste navegador.');
    }
  }

  async function registerDecision() {
    if (!selected) return;
    if (source === 'postgres') {
      try {
        const updated = await addPldCaseDecisionBackend(selected.id, { status, analyst, note });
        setRecords((current) => current.map((record) => record.id === updated.id ? updated : record));
        setNote('');
        setNotice('Decisão registrada no Postgres com trilha de auditoria.');
        return;
      } catch {
        setNotice('Não foi possível registrar no Postgres. Tentando registrar localmente.');
      }
    }
    addPldCaseDecision(selected.id, { status, analyst, note });
    setNote('');
    await refresh();
  }

  function deleteCase(caseId: string) {
    removePldCase(caseId);
    const next = listPldCases();
    setRecords(next);
    setSelectedId(next[0]?.id || null);
    if (source === 'postgres') {
      setNotice('Remoção só é local nesta versão; casos do Postgres permanecem auditáveis.');
    }
  }

  async function downloadOfficialReport(record: PldCaseRecord) {
    if (source !== 'postgres') {
      printCase(record);
      return;
    }
    try {
      const blob = await downloadPldCaseReportBackend(record.id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${record.dossier.id || record.id}.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
      setNotice('Relatório oficial gerado pela API.');
    } catch {
      setNotice('Não foi possível baixar o PDF oficial. Abrindo versão de impressão local.');
      printCase(record);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="border-b border-white/10 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <Link href="/br/pld-ft/lab" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
            <ArrowLeft className="h-4 w-4" />
            Voltar para laboratório
          </Link>
          <h1 className="mt-6 text-4xl font-semibold tracking-tight text-white">Fila de casos PLD/FT</h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
            Registro de dossiês, decisão humana, status e trilha operacional. Quando a API estiver disponível,
            a fila é carregada do Postgres; em contingência, usa o armazenamento local do navegador.
          </p>
          {notice && (
            <p className="mt-4 rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100">
              {notice}
            </p>
          )}
        </div>
      </section>

      <section className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[0.78fr_1.22fr]">
          <aside className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Casos salvos</h2>
              <div className="flex items-center gap-2">
                <span className="rounded-full border border-white/10 px-3 py-1 text-xs font-semibold text-slate-300">
                  {source === 'postgres' ? 'Postgres' : 'Local'}
                </span>
                <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-950">{records.length}</span>
              </div>
            </div>
            <div className="mt-4 grid gap-3">
              <label className="relative block">
                <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-slate-500" aria-hidden="true" />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Buscar por instituição, regra, entidade..."
                  className="w-full rounded-xl border border-white/10 bg-slate-950 py-3 pl-9 pr-3 text-sm text-white placeholder:text-slate-500"
                />
              </label>
              <div className="grid grid-cols-2 gap-3">
                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value as 'todos' | PldCaseStatus)}
                  className="rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-white"
                >
                  <option value="todos">Todos status</option>
                  {Object.entries(pldCaseStatusLabels).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
                <select
                  value={severityFilter}
                  onChange={(event) => setSeverityFilter(event.target.value)}
                  className="rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-white"
                >
                  <option value="todas">Todas severidades</option>
                  <option value="critical">Crítica</option>
                  <option value="high">Alta</option>
                  <option value="medium">Média</option>
                  <option value="low">Baixa</option>
                </select>
              </div>
            </div>
            <div className="mt-4 grid gap-3">
              {records.length === 0 && (
                <div className="rounded-2xl border border-dashed border-white/20 p-5 text-sm leading-6 text-slate-400">
                  Nenhum caso salvo. Rode uma análise no laboratório e clique em “Salvar na fila”.
                </div>
              )}
              {records.length > 0 && filteredRecords.length === 0 && (
                <div className="rounded-2xl border border-dashed border-white/20 p-5 text-sm leading-6 text-slate-400">
                  Nenhum caso bate com os filtros atuais.
                </div>
              )}
              {filteredRecords.map((record) => (
                <button
                  type="button"
                  key={record.id}
                  onClick={() => setSelectedId(record.id)}
                  className={`rounded-2xl border p-4 text-left transition ${
                    record.id === selectedId ? 'border-blue-400 bg-blue-500/10' : 'border-white/10 bg-slate-950/70 hover:bg-white/[0.06]'
                  }`}
                >
                  <p className="text-sm font-semibold text-white">{record.id}</p>
                  <p className="mt-1 text-xs text-slate-400">{record.dossier.institution}</p>
                  <div className="mt-3 flex items-center justify-between gap-3 text-xs">
                    <span className="rounded-full border border-white/10 px-2 py-1 text-slate-300">{pldCaseStatusLabels[record.status]}</span>
                    <span className="font-semibold text-red-200">{record.dossier.riskScore}/100</span>
                  </div>
                </button>
              ))}
            </div>
          </aside>

          {selected ? (
            <div className="grid gap-6">
              <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-200">{selected.id}</p>
                    <h2 className="mt-2 text-3xl font-semibold text-white">
                      {selected.dossier.riskScore}/100 · {selected.dossier.severity}
                    </h2>
                    <p className="mt-3 text-sm leading-7 text-slate-300">{selected.dossier.executiveSummary}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => downloadOfficialReport(selected)}
                      className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-slate-950"
                    >
                      <Download className="h-4 w-4" />
                      PDF oficial
                    </button>
                    <button
                      type="button"
                      onClick={() => printCase(selected)}
                      className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-sm font-semibold text-slate-200"
                    >
                      <FileText className="h-4 w-4" />
                      Imprimir
                    </button>
                    <button
                      type="button"
                      onClick={() => download(`${selected.id}.md`, pldDossierToMarkdown(selected.dossier), 'text/markdown;charset=utf-8')}
                      className="rounded-xl border border-white/10 px-4 py-2 text-sm font-semibold text-slate-200"
                    >
                      Markdown
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteCase(selected.id)}
                      disabled={source === 'postgres'}
                      className="inline-flex items-center gap-2 rounded-xl border border-red-500/30 px-4 py-2 text-sm font-semibold text-red-100"
                    >
                      <Trash2 className="h-4 w-4" />
                      Remover
                    </button>
                  </div>
                </div>
              </section>

              <section className="grid gap-4 md:grid-cols-4">
                <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Status</p>
                  <p className="mt-2 text-xl font-semibold text-white">{pldCaseStatusLabels[selected.status]}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Volume</p>
                  <p className="mt-2 text-xl font-semibold text-white">{BRL.format(selected.dossier.totalAmount)}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Achados</p>
                  <p className="mt-2 text-xl font-semibold text-white">{selected.dossier.findings.length}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Decisões</p>
                  <p className="mt-2 text-xl font-semibold text-white">{selected.decisions.length}</p>
                </div>
              </section>

              <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
                <h3 className="text-xl font-semibold text-white">Registrar decisão humana</h3>
                <div className="mt-4 grid gap-3 md:grid-cols-[0.7fr_0.7fr_1.6fr_auto]">
                  <select value={status} onChange={(event) => setStatus(event.target.value as PldCaseStatus)} className="rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-white">
                    {Object.entries(pldCaseStatusLabels).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                  <input value={analyst} onChange={(event) => setAnalyst(event.target.value)} className="rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-white" />
                  <input value={note} onChange={(event) => setNote(event.target.value)} placeholder="Motivo, evidência adicional ou orientação" className="rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-white" />
                  <button type="button" onClick={registerDecision} className="rounded-xl bg-blue-500 px-4 py-3 text-sm font-semibold text-white">
                    Registrar
                  </button>
                </div>
              </section>

              <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
                <h3 className="text-xl font-semibold text-white">Histórico de decisões</h3>
                <div className="mt-4 grid gap-3">
                  {selected.decisions.length === 0 && <p className="text-sm text-slate-400">Ainda sem decisão humana registrada.</p>}
                  {selected.decisions.map((decision) => (
                    <div key={`${decision.decidedAt}-${decision.status}`} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                      <p className="text-sm font-semibold text-white">
                        {pldCaseStatusLabels[decision.status]} · {decision.analyst}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">{decision.decidedAt}</p>
                      <p className="mt-3 text-sm leading-6 text-slate-300">{decision.note || 'Sem nota.'}</p>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          ) : (
            <div className="rounded-3xl border border-dashed border-white/20 p-10 text-center text-slate-400">
              Selecione um caso para revisar.
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
