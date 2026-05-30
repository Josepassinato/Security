'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  ArrowLeft,
  Briefcase,
  CheckCircle2,
  Download,
  FileJson,
  FileText,
  Network,
  RotateCcw,
  ShieldAlert,
  Upload,
} from 'lucide-react';
import {
  analyzePldFt,
  defaultPldThresholds,
  pldDossierToMarkdown,
  type PldDossier,
  type PldInput,
  type PldThresholds,
} from '@/lib/pldft/engine';
import { analyzePldFtBackend, savePldCaseBackend, savePldThresholdsBackend } from '@/lib/pldft/api';
import { savePldCase } from '@/lib/pldft/cases';
import { parsePldCsv, pldCsvTemplate } from '@/lib/pldft/importers';
import type { PldIntegration } from '@/lib/pldft/integrations';
import { samplePldInput } from '@/lib/pldft/sample';
import { pldScenarios } from '@/lib/pldft/scenarios';

const BRL = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 2,
});

function severityClass(severity: string): string {
  if (severity === 'critical') return 'border-red-500/40 bg-red-500/10 text-red-100';
  if (severity === 'high') return 'border-orange-500/40 bg-orange-500/10 text-orange-100';
  if (severity === 'medium') return 'border-amber-500/40 bg-amber-500/10 text-amber-100';
  return 'border-emerald-500/40 bg-emerald-500/10 text-emerald-100';
}

function download(filename: string, content: string, type = 'text/plain;charset=utf-8') {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function parseJsonPayload(text: string): PldInput {
  const parsed = JSON.parse(text) as PldInput;
  if (!Array.isArray(parsed.transactions)) {
    throw new Error('O JSON precisa conter uma lista "transactions".');
  }
  return parsed;
}

function printDossier(dossier: PldDossier) {
  const html = `
    <html>
      <head>
        <title>${dossier.id}</title>
        <style>
          body{font-family:Inter,Arial,sans-serif;color:#111827;padding:32px;line-height:1.55}
          h1{font-size:28px;margin:0 0 8px}
          h2{margin-top:28px;border-bottom:1px solid #ddd;padding-bottom:6px}
          .kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:20px 0}
          .card{border:1px solid #ddd;border-radius:12px;padding:14px;margin:10px 0}
          .small{font-size:12px;color:#4b5563}
          li{margin-bottom:6px}
        </style>
      </head>
      <body>
        <p class="small">Quarry PLD/FT - documento para revisão humana</p>
        <h1>Dossiê ${dossier.id}</h1>
        <p><strong>Instituição:</strong> ${dossier.institution}</p>
        <p>${dossier.executiveSummary}</p>
        <div class="kpi">
          <div class="card"><strong>Score</strong><br/>${dossier.riskScore}/100</div>
          <div class="card"><strong>Severidade</strong><br/>${dossier.severity}</div>
          <div class="card"><strong>Volume total</strong><br/>${BRL.format(dossier.totalAmount)}</div>
          <div class="card"><strong>Achados</strong><br/>${dossier.findings.length}</div>
        </div>
        <h2>Achados</h2>
        ${dossier.findings.map((finding) => `
          <div class="card">
            <h3>${finding.ruleId} - ${finding.title}</h3>
            <p>${finding.rationale}</p>
            <p><strong>Valor em escopo:</strong> ${BRL.format(finding.amountInScope)}</p>
            <p><strong>Transações:</strong> ${finding.transactionIds.join(', ')}</p>
            <ul>${finding.evidence.map((item) => `<li>${item}</li>`).join('')}</ul>
            <p><strong>Ação recomendada:</strong> ${finding.recommendedAction}</p>
          </div>
        `).join('')}
        <h2>Checklist humano</h2>
        <ul>${dossier.analystChecklist.map((item) => `<li>${item}</li>`).join('')}</ul>
        <h2>Trilha de auditoria</h2>
        <ul>${dossier.auditTrail.map((item) => `<li>${item}</li>`).join('')}</ul>
        <h2>Observação legal</h2>
        <p>${dossier.disclaimer}</p>
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

function withThreshold(input: PldInput, key: keyof PldThresholds, value: number): PldInput {
  return {
    ...input,
    thresholds: {
      ...input.thresholds,
      [key]: value,
    },
  };
}

function KpiCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
      {sub && <p className="mt-1 text-xs leading-5 text-slate-400">{sub}</p>}
    </div>
  );
}

function DossierView({ dossier }: { dossier: PldDossier }) {
  return (
    <div className="grid gap-6">
      <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-200">
              Dossiê {dossier.id}
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white">
              Score {dossier.riskScore}/100 · {dossier.severity}
            </h2>
            <p className="mt-3 max-w-4xl text-sm leading-7 text-slate-300">{dossier.executiveSummary}</p>
          </div>
          <span className={`inline-flex rounded-full border px-4 py-2 text-sm font-semibold ${severityClass(dossier.severity)}`}>
            {dossier.severity.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <KpiCard label="Transações" value={dossier.totalTransactions} />
        <KpiCard label="Volume total" value={BRL.format(dossier.totalAmount)} />
        <KpiCard label="Volume em escopo" value={BRL.format(dossier.suspiciousAmount)} />
        <KpiCard label="Achados" value={dossier.findings.length} />
      </div>

      <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
        <div className="flex items-center gap-3">
          <ShieldAlert className="h-5 w-5 text-red-300" aria-hidden="true" />
          <h3 className="text-xl font-semibold text-white">Achados explicáveis</h3>
        </div>
        <div className="mt-5 grid gap-4">
          {dossier.findings.map((finding) => (
            <article key={`${finding.ruleId}-${finding.entityId}`} className="rounded-2xl border border-white/10 bg-slate-950/70 p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{finding.ruleId}</p>
                  <h4 className="mt-1 text-lg font-semibold text-white">{finding.title}</h4>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{finding.rationale}</p>
                </div>
                <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${severityClass(finding.severity)}`}>
                  {finding.score}/100
                </span>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-[0.8fr_1.2fr]">
                <div className="rounded-xl bg-white/[0.04] p-4 text-sm text-slate-300">
                  <p><strong className="text-white">Entidade:</strong> {finding.entityType} {finding.entityId}</p>
                  <p className="mt-2"><strong className="text-white">Valor:</strong> {BRL.format(finding.amountInScope)}</p>
                  <p className="mt-2"><strong className="text-white">Transações:</strong> {finding.transactionIds.join(', ')}</p>
                </div>
                <div className="rounded-xl bg-white/[0.04] p-4 text-sm leading-6 text-slate-300">
                  <strong className="text-white">Evidências:</strong>
                  <ul className="mt-2 list-disc space-y-1 pl-5">
                    {finding.evidence.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </div>
              </div>
              <p className="mt-4 rounded-xl border border-blue-500/20 bg-blue-500/10 p-4 text-sm leading-6 text-blue-100">
                <strong>Ação recomendada:</strong> {finding.recommendedAction}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
          <div className="flex items-center gap-3">
            <Network className="h-5 w-5 text-blue-200" aria-hidden="true" />
            <h3 className="text-xl font-semibold text-white">Rede de entidades</h3>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {dossier.network.nodes.slice(0, 10).map((node) => (
              <div key={node.id} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                <p className="text-sm font-semibold text-white">{node.label}</p>
                <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">{node.type}</p>
                <div className="mt-3 h-2 rounded-full bg-slate-800">
                  <div className="h-2 rounded-full bg-gradient-to-r from-amber-400 to-red-500" style={{ width: `${Math.min(node.risk, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
          <h3 className="text-xl font-semibold text-white">Checklist humano</h3>
          <div className="mt-5 grid gap-3">
            {dossier.analystChecklist.map((item) => (
              <div key={item} className="flex gap-3 rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-sm leading-6 text-slate-300">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" aria-hidden="true" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
        <h3 className="text-xl font-semibold text-white">Trilha de auditoria</h3>
        <ol className="mt-5 grid gap-3">
          {dossier.auditTrail.map((item, index) => (
            <li key={item} className="grid grid-cols-[2.5rem_1fr] gap-3 rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-sm leading-6 text-slate-300">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-xs font-bold text-slate-950">{index + 1}</span>
              <span className="self-center">{item}</span>
            </li>
          ))}
        </ol>
        <p className="mt-5 rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm leading-6 text-amber-100">
          {dossier.disclaimer}
        </p>
      </section>
    </div>
  );
}

const integrationChecklist: PldIntegration[] = [
  {
    id: 'pix-core',
    name: 'Pix / Core Banking',
    status: 'pending',
    envKeys: ['QUARRY_PLD_PIX_WEBHOOK_SECRET', 'QUARRY_PLD_CORE_BANKING_URL'],
    purpose: 'Receber eventos transacionais reais em tempo real ou lote diário.',
    nextStep: 'Conectar webhook/API da fintech e mapear para o schema PldTransaction.',
  },
  {
    id: 'kyc',
    name: 'KYC / Cadastro',
    status: 'pending',
    envKeys: ['QUARRY_PLD_KYC_URL'],
    purpose: 'Comparar movimentação contra renda, faturamento, CNAE, idade da conta e dados cadastrais.',
    nextStep: 'Conectar base cadastral ou provedor KYC.',
  },
  {
    id: 'sanctions-pep',
    name: 'Sanções / PEP / mídia adversa',
    status: 'pending',
    envKeys: ['OFAC_API_KEY', 'QUARRY_PLD_PEP_URL', 'QUARRY_PLD_ADVERSE_MEDIA_URL'],
    purpose: 'Enriquecer risco com listas externas e sinais reputacionais.',
    nextStep: 'Definir provedor, política de atualização e validação jurídica.',
  },
  {
    id: 'case-management',
    name: 'Fila de casos / GRC',
    status: 'pending',
    envKeys: ['QUARRY_PLD_CASE_WEBHOOK_URL'],
    purpose: 'Mandar casos críticos para revisão humana, decisão e trilha de auditoria.',
    nextStep: 'Conectar webhook ou GRC interno.',
  },
];

export function PldFtLab() {
  const [input, setInput] = useState<PldInput>(samplePldInput);
  const [text, setText] = useState(() => JSON.stringify(samplePldInput, null, 2));
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [backendDossier, setBackendDossier] = useState<PldDossier | null>(null);
  const [backendImportId, setBackendImportId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const localDossier = useMemo(() => analyzePldFt(input), [input]);
  const dossier = backendDossier || localDossier;
  const thresholds = { ...defaultPldThresholds, ...(input.thresholds || {}) };

  async function runFromText() {
    try {
      const parsed = parseJsonPayload(text);
      setInput(parsed);
      setBackendDossier(null);
      setBackendImportId(null);
      setIsAnalyzing(true);
      const result = await analyzePldFtBackend(parsed);
      setBackendDossier(result.dossier);
      setBackendImportId(result.importId);
      setError(null);
      setNotice(`Análise ${result.dossier.id} gravada no Postgres. Hash ${result.payloadHash.slice(0, 12)}...`);
    } catch (err) {
      try {
        const parsed = parseJsonPayload(text);
        setInput(parsed);
        setError(null);
        setNotice('API indisponível ou recusou a análise. Resultado calculado localmente e ainda pode ser exportado.');
      } catch (parseErr) {
        setError(parseErr instanceof Error ? parseErr.message : 'Não foi possível ler o JSON.');
      }
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function onFile(file?: File) {
    if (!file) return;
    try {
      const payload = await file.text();
      const parsed = file.name.toLowerCase().endsWith('.csv')
        ? parsePldCsv(payload, input.institution || 'Instituição financeira')
        : parseJsonPayload(payload);
      setText(JSON.stringify(parsed, null, 2));
      setInput(parsed);
      setBackendDossier(null);
      setBackendImportId(null);
      setError(null);
      setNotice(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Arquivo inválido.');
    }
  }

  function loadScenario(id: string) {
    const scenario = pldScenarios.find((item) => item.id === id);
    if (!scenario) return;
    setInput(scenario.input);
    setText(JSON.stringify(scenario.input, null, 2));
    setBackendDossier(null);
    setBackendImportId(null);
    setError(null);
    setNotice(`Cenário carregado: ${scenario.name}`);
  }

  async function updateThreshold(key: keyof PldThresholds, value: number) {
    const next = withThreshold(input, key, value);
    setInput(next);
    setText(JSON.stringify(next, null, 2));
    setBackendDossier(null);
    setBackendImportId(null);
    try {
      await savePldThresholdsBackend(next.thresholds || {});
      setNotice('Threshold salvo na API. A próxima análise usará a calibração persistida.');
    } catch {
      setNotice('Threshold ajustado localmente. A API não confirmou persistência agora.');
    }
  }

  async function saveCurrentCase() {
    try {
      await savePldCaseBackend(dossier, backendImportId);
      setNotice(`Caso ${dossier.id} salvo no Postgres para revisão humana.`);
    } catch {
      savePldCase(dossier);
      setNotice(`API indisponível. Caso ${dossier.id} salvo localmente neste navegador.`);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="border-b border-white/10 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <Link href="/br/pld-ft" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Voltar para PLD/FT
          </Link>
          <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_0.85fr] lg:items-end">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-blue-100">
                <ShieldAlert className="h-3.5 w-3.5" aria-hidden="true" />
                Laboratório PLD/FT operacional
              </p>
              <h1 className="mt-5 max-w-4xl text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
                Analise transações, gere score explicável e baixe o dossiê auditável.
              </h1>
              <p className="mt-5 max-w-3xl text-base leading-8 text-slate-300">
                Este módulo executa regras determinísticas sobre transações, KYC e sinais externos.
                A IA pode resumir depois, mas o cálculo de risco e as evidências não dependem de opinião.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link href="/br/pld-ft/cases" className="rounded-xl border border-white/10 px-4 py-3 text-sm font-semibold text-slate-200 hover:bg-white/[0.06]">
                  Fila de casos
                </Link>
                <Link href="/br/pld-ft/rules" className="rounded-xl border border-white/10 px-4 py-3 text-sm font-semibold text-slate-200 hover:bg-white/[0.06]">
                  Matriz de regras
                </Link>
                <Link href="/br/pld-ft/benchmark" className="rounded-xl border border-white/10 px-4 py-3 text-sm font-semibold text-slate-200 hover:bg-white/[0.06]">
                  Benchmark
                </Link>
                <Link href="/br/pld-ft/readiness" className="rounded-xl border border-white/10 px-4 py-3 text-sm font-semibold text-slate-200 hover:bg-white/[0.06]">
                  Prontidão
                </Link>
              </div>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
              <p className="flex items-center gap-2 text-sm font-semibold text-white">
                <AlertTriangle className="h-4 w-4 text-amber-300" aria-hidden="true" />
                Próxima etapa para produção
              </p>
              <p className="mt-3 text-sm leading-6 text-slate-300">
                Conectar Pix/Core Banking/KYC reais, listas PEP/sanções/adverse media e calibrar thresholds
                com casos históricos validados por especialistas.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[0.82fr_1.18fr]">
          <aside className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 lg:sticky lg:top-6 lg:self-start">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Entrada</p>
                <h2 className="mt-1 text-xl font-semibold text-white">JSON de análise</h2>
              </div>
              <FileJson className="h-5 w-5 text-blue-200" aria-hidden="true" />
            </div>
            <textarea
              value={text}
              onChange={(event) => setText(event.target.value)}
              className="mt-4 min-h-[360px] w-full resize-y rounded-2xl border border-white/10 bg-slate-950 p-4 font-mono text-xs leading-5 text-slate-200 outline-none focus:border-blue-400"
              spellCheck={false}
            />
            {error && <p className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-100">{error}</p>}
            {notice && <p className="mt-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-100">{notice}</p>}
            <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/70 p-4">
              <p className="text-sm font-semibold text-white">Cenários prontos</p>
              <select
                onChange={(event) => loadScenario(event.target.value)}
                defaultValue=""
                className="mt-3 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-white"
              >
                <option value="" disabled>Escolha um cenário</option>
                {pldScenarios.map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>{scenario.name}</option>
                ))}
              </select>
            </div>
            <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/70 p-4">
              <p className="text-sm font-semibold text-white">Calibração rápida</p>
              <div className="mt-3 grid gap-3">
                {([
                  ['passThroughWindowMinutes', 'Janela conta de passagem (min)'],
                  ['passThroughRatio', 'Percentual de repasse'],
                  ['economicMismatchMultiplier', 'Multiplicador renda/faturamento'],
                  ['deviceReuseMinCustomers', 'Clientes por device'],
                  ['structuringMinTransactions', 'Qtd. fracionamento'],
                ] as [keyof PldThresholds, string][]).map(([key, label]) => (
                  <label key={key} className="grid gap-1 text-xs text-slate-400">
                    {label}
                    <input
                      type="number"
                      step={key === 'passThroughRatio' ? '0.05' : '1'}
                      value={thresholds[key]}
                      onChange={(event) => updateThreshold(key, Number(event.target.value))}
                      className="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-white"
                    />
                  </label>
                ))}
              </div>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <button
                type="button"
                onClick={runFromText}
                disabled={isAnalyzing}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-500 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-400"
              >
                <ShieldAlert className="h-4 w-4" aria-hidden="true" />
                {isAnalyzing ? 'Analisando...' : 'Analisar'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setInput(samplePldInput);
                  setText(JSON.stringify(samplePldInput, null, 2));
                  setBackendDossier(null);
                  setBackendImportId(null);
                  setError(null);
                }}
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 px-4 py-3 text-sm font-semibold text-slate-200 hover:bg-white/[0.06]"
              >
                <RotateCcw className="h-4 w-4" aria-hidden="true" />
                Restaurar exemplo
              </button>
            </div>
            <label className="mt-3 flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-white/20 px-4 py-3 text-sm font-semibold text-slate-300 hover:bg-white/[0.06]">
              <Upload className="h-4 w-4" aria-hidden="true" />
              Upload JSON ou CSV
              <input type="file" accept="application/json,.json,text/csv,.csv" className="hidden" onChange={(event) => onFile(event.target.files?.[0])} />
            </label>
            <button
              type="button"
              onClick={() => download('quarry-pldft-template.csv', pldCsvTemplate, 'text/csv;charset=utf-8')}
              className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-white/10 px-4 py-3 text-sm font-semibold text-slate-200 hover:bg-white/[0.06]"
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              Baixar template CSV
            </button>
            <button
              type="button"
              onClick={() => download(`${dossier.id}.md`, pldDossierToMarkdown(dossier), 'text/markdown;charset=utf-8')}
              className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-950 hover:bg-slate-200"
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              Baixar dossiê
            </button>
            <button
              type="button"
              onClick={() => printDossier(dossier)}
              className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-white/10 px-4 py-3 text-sm font-semibold text-slate-200 hover:bg-white/[0.06]"
            >
              <FileText className="h-4 w-4" aria-hidden="true" />
              PDF / imprimir
            </button>
            <button
              type="button"
              onClick={saveCurrentCase}
              className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-400"
            >
              <Briefcase className="h-4 w-4" aria-hidden="true" />
              Salvar na fila
            </button>
          </aside>

          <div className="grid gap-6">
            <section className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                Contrato de produção
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Conectores necessários para piloto real</h2>
              <div className="mt-5 grid gap-3 md:grid-cols-2">
                {integrationChecklist.map((item) => (
                  <div key={item.id} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-white">{item.name}</p>
                        <p className="mt-2 text-sm leading-6 text-slate-300">{item.purpose}</p>
                      </div>
                      <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-100">
                        pendente
                      </span>
                    </div>
                    <p className="mt-3 text-xs leading-5 text-slate-500">{item.nextStep}</p>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-xs leading-5 text-slate-500">
                A API de status está em <code>/api/pld-ft/integrations</code>. Quando as variáveis de ambiente forem configuradas,
                ela passa a reportar os conectores como conectados.
              </p>
            </section>
            <DossierView dossier={dossier} />
          </div>
        </div>
      </section>
    </main>
  );
}
