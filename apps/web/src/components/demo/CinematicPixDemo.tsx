'use client';

import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock3,
  DollarSign,
  Download,
  FileText,
  GitBranch,
  Landmark,
  Pause,
  Play,
  RefreshCcw,
  Scale,
  ShieldAlert,
  Sparkles,
  Zap,
} from 'lucide-react';
import {
  DEMO_PHASES,
  HERO_BRIEF,
  REGULATORY_ARTIFACTS,
  TOTAL_SECONDS,
  getDemoState,
  type DemoFinding,
  type DemoGraphEdge,
  type DemoGraphNode,
} from './cinematicScenario';
import { buildBacenCommunication, buildBacenFilename } from './bacenReport';

const BRL = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
});

const USD = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
});

const SIX_HOURS_MS = 6 * 60 * 60 * 1000;

function severityTone(severity: DemoFinding['severity']) {
  if (severity === 'critical') return 'border-red-500/50 bg-red-950/35 text-red-100';
  if (severity === 'high') return 'border-orange-500/50 bg-orange-950/30 text-orange-100';
  return 'border-yellow-500/40 bg-yellow-950/25 text-yellow-100';
}

function graphNodeTone(tone: DemoGraphNode['tone']) {
  if (tone === 'account') return 'border-sky-400 bg-sky-500 text-sky-950';
  if (tone === 'device') return 'border-cyan-300 bg-cyan-400 text-cyan-950';
  if (tone === 'pix') return 'border-emerald-300 bg-emerald-400 text-emerald-950';
  if (tone === 'merchant') return 'border-amber-300 bg-amber-400 text-amber-950';
  return 'border-red-300 bg-red-400 text-red-950';
}

function GraphEdge({
  edge,
  nodes,
}: {
  edge: DemoGraphEdge;
  nodes: DemoGraphNode[];
}) {
  const from = nodes.find((node) => node.id === edge.from);
  const to = nodes.find((node) => node.id === edge.to);
  if (!from || !to) return null;
  const x1 = from.x;
  const y1 = from.y;
  const x2 = to.x;
  const y2 = to.y;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const length = Math.sqrt(dx * dx + dy * dy);
  const angle = (Math.atan2(dy, dx) * 180) / Math.PI;

  return (
    <div
      className="absolute h-px origin-left bg-emerald-300/70 shadow-[0_0_12px_rgba(110,231,183,0.8)] transition-all duration-700"
      style={{
        left: `${x1}%`,
        top: `${y1}%`,
        width: `${length}%`,
        transform: `rotate(${angle}deg)`,
      }}
    >
      <span className="absolute left-1/2 top-1 -translate-x-1/2 rounded bg-slate-950/85 px-1.5 py-0.5 text-[10px] text-emerald-100 ring-1 ring-emerald-400/20">
        {edge.label}
      </span>
    </div>
  );
}

function MetricCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="rounded-md border border-slate-700 bg-slate-950/55 p-3">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-xl font-semibold text-white">{value}</div>
      <div className="mt-0.5 text-xs text-slate-400">{sub}</div>
    </div>
  );
}

export function CinematicPixDemo() {
  const searchParams = useSearchParams();
  const speed = searchParams.get('speed') === 'fast' ? 18 : 1;
  const autoRecord = searchParams.get('record') === '1';
  const [elapsed, setElapsed] = useState(0);
  const [running, setRunning] = useState(true);
  const state = useMemo(() => getDemoState(elapsed), [elapsed]);

  useEffect(() => {
    if (!running) return;
    const id = window.setInterval(() => {
      setElapsed((current) => Math.min(TOTAL_SECONDS, current + speed));
    }, 1000);
    return () => window.clearInterval(id);
  }, [running, speed]);

  useEffect(() => {
    if (elapsed >= TOTAL_SECONDS) setRunning(false);
  }, [elapsed]);

  useEffect(() => {
    const id = window.setInterval(() => {
      setElapsed(0);
      setRunning(true);
    }, SIX_HOURS_MS);
    return () => window.clearInterval(id);
  }, []);

  return (
    <main
      data-demo-ready={state.reportReady ? 'true' : 'false'}
      className="min-h-screen bg-slate-950 px-4 py-5 text-slate-100 sm:px-6 lg:px-8"
    >
      <div className="mx-auto max-w-[1440px] space-y-5">
        <section className="grid gap-4 lg:grid-cols-[1.55fr_0.9fr]">
          <div className="rounded-md border border-emerald-500/30 bg-slate-900/80 p-5 shadow-[0_0_40px_-24px_rgba(52,211,153,0.75)]">
            <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-200">
                <ShieldAlert className="h-3.5 w-3.5" />
                Demo hero
              </span>
              <span className="rounded-full border border-slate-700 px-2.5 py-1 text-xs text-slate-300">
                Dataset sintético FinPlay Pagamentos
              </span>
              {autoRecord ? (
                <span className="rounded-full border border-red-400/40 bg-red-500/10 px-2.5 py-1 text-xs text-red-200">
                  gravação
                </span>
              ) : null}
            </div>
            <h1 className="mt-4 text-3xl font-semibold tracking-tight text-white lg:text-4xl">
              Investigação de fraude Pix organizada
            </h1>
            <p className="mt-3 max-w-4xl text-base leading-7 text-slate-200">
              {HERO_BRIEF}
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              <MetricCard
                label="Transações analisadas"
                value={state.metrics.transactionsScanned.toLocaleString('pt-BR')}
                sub="Pix legítimos e suspeitos"
              />
              <MetricCard
                label="Valor correlacionado"
                value={BRL.format(state.metrics.pixValueBrl)}
                sub="rota de cash-out mapeada"
              />
              <MetricCard
                label="Contas conectadas"
                value={state.metrics.accountsCorrelated.toLocaleString('pt-BR')}
                sub="clientes, recebedores e dispositivos"
              />
            </div>
          </div>

          <div className="rounded-md border border-slate-700 bg-slate-900/85 p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Execução ao vivo
                </div>
                <div className="mt-1 text-3xl font-semibold text-white">{state.metrics.elapsedLabel}</div>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setRunning((current) => !current)}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-700 bg-slate-950 text-slate-200 hover:border-emerald-400 hover:text-emerald-200"
                  aria-label={running ? 'Pausar demo' : 'Retomar demo'}
                >
                  {running ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setElapsed(0);
                    setRunning(true);
                  }}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-700 bg-slate-950 text-slate-200 hover:border-emerald-400 hover:text-emerald-200"
                  aria-label="Reiniciar demo"
                >
                  <RefreshCcw className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="mt-5">
              <div className="mb-2 flex items-center justify-between text-xs text-slate-400">
                <span>{state.activePhase.theatre}</span>
                <span>{Math.round(state.overallProgress * 100)}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-emerald-400 transition-all duration-700"
                  style={{ width: `${state.overallProgress * 100}%` }}
                />
              </div>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-2">
              <MetricCard label="Custo IA" value={USD.format(state.metrics.costUsd)} sub="tokens + orquestração" />
              <MetricCard label="Analista humano" value={USD.format(state.metrics.humanCostUsd)} sub={`${state.metrics.hoursSaved.toFixed(1)}h economizadas`} />
            </div>
          </div>
        </section>

        {state.activeRegulatoryArtifact ? (
          <section
            data-testid="regulatory-overlay"
            className="rounded-md border border-amber-500/40 bg-gradient-to-br from-amber-950/40 to-slate-900/70 p-5 shadow-[0_0_36px_-20px_rgba(217,119,6,0.6)]"
          >
            <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/40 bg-amber-500/15 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-amber-100">
                    <Landmark className="h-3.5 w-3.5" />
                    Regulação ativa
                  </span>
                  <span className="rounded-full border border-amber-500/30 px-2.5 py-1 font-mono text-[11px] text-amber-200">
                    {state.activeRegulatoryArtifact.norma}
                  </span>
                </div>
                <h2 className="mt-3 text-xl font-semibold text-amber-50 lg:text-2xl">
                  {state.activeRegulatoryArtifact.titulo}
                </h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-amber-100/85">
                  {state.activeRegulatoryArtifact.detalhe}
                </p>
              </div>

              <div className="rounded-md border border-amber-500/25 bg-slate-950/60 p-4">
                <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-amber-200/80">
                  <Scale className="h-3.5 w-3.5" />
                  Artefatos satisfeitos
                </div>
                <ul className="mt-3 space-y-2">
                  {REGULATORY_ARTIFACTS.map((artifact) => {
                    const triggered = state.visibleRegulatoryArtifacts.some(
                      (a) => a.id === artifact.id,
                    );
                    const isActive = state.activeRegulatoryArtifact?.id === artifact.id;
                    return (
                      <li
                        key={artifact.id}
                        className={[
                          'flex items-center gap-2 text-[12px] transition-colors',
                          triggered
                            ? isActive
                              ? 'text-amber-100'
                              : 'text-amber-200/70'
                            : 'text-slate-600',
                        ].join(' ')}
                      >
                        <CheckCircle2
                          className={[
                            'h-3.5 w-3.5',
                            triggered ? 'text-emerald-300' : 'text-slate-700',
                          ].join(' ')}
                        />
                        <span className="font-mono text-[11px] uppercase tracking-wide">
                          {artifact.norma.split('·')[0].trim()}
                        </span>
                        <span className="truncate">{artifact.titulo}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </div>
          </section>
        ) : null}

        <section className="rounded-md border border-slate-700 bg-slate-900/70 p-4">
          <div className="grid gap-2 md:grid-cols-7">
            {DEMO_PHASES.map((phase) => {
              const done = elapsed >= phase.endsAt;
              const active = phase.id === state.activePhase.id;
              return (
                <div
                  key={phase.id}
                  className={[
                    'rounded-md border p-3 transition-all duration-500',
                    active
                      ? 'border-emerald-400 bg-emerald-500/10 text-emerald-100'
                      : done
                        ? 'border-slate-700 bg-slate-950/60 text-slate-300'
                        : 'border-slate-800 bg-slate-950/35 text-slate-500',
                  ].join(' ')}
                >
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide">
                    {done ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Clock3 className="h-3.5 w-3.5" />}
                    {phase.label}
                  </div>
                  <div className="mt-1 text-[11px] text-slate-400">
                    {phase.startsAt}s → {phase.endsAt}s
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.9fr_1fr_0.9fr]">
          <div className="space-y-5">
            <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <Sparkles className="h-4 w-4 text-emerald-300" />
                Hipóteses priorizadas
              </div>
              <div className="mt-4 space-y-3">
                {state.visibleHypotheses.map((hypothesis) => (
                  <div
                    key={hypothesis.id}
                    className="rounded-md border border-slate-700 bg-slate-950/55 p-3 transition-all duration-500 animate-in fade-in slide-in-from-bottom-2"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="font-medium text-slate-100">{hypothesis.title}</div>
                      <div className="rounded bg-emerald-500/15 px-2 py-0.5 text-xs font-semibold text-emerald-200">
                        {Math.round(hypothesis.confidence * 100)}%
                      </div>
                    </div>
                    <p className="mt-1 text-sm leading-5 text-slate-400">{hypothesis.detail}</p>
                    <div className="mt-2 text-xs text-slate-500">{hypothesis.tactic}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <Zap className="h-4 w-4 text-cyan-300" />
                Consultas em execução
              </div>
              <div className="mt-4 space-y-3">
                {state.activeQueries.map((query) => (
                  <div key={query.id} className="rounded-md border border-slate-700 bg-slate-950/55 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-medium text-slate-100">{query.source}</div>
                        <div className="mt-1 font-mono text-[11px] text-slate-500">{query.query}</div>
                      </div>
                      <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
                        {query.status}
                      </span>
                    </div>
                    <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-800">
                      <div
                        className="h-full rounded-full bg-cyan-300 transition-all duration-700"
                        style={{ width: `${query.progress * 100}%` }}
                      />
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      {Math.round(query.progress * query.rows).toLocaleString('pt-BR')} linhas
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-5">
            <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <GitBranch className="h-4 w-4 text-emerald-300" />
                Attack graph
              </div>
              <div className="relative mt-4 h-[420px] overflow-hidden rounded-md border border-slate-800 bg-slate-950">
                {state.visibleGraphEdges.map((edge) => (
                  <GraphEdge key={`${edge.from}-${edge.to}`} edge={edge} nodes={state.visibleGraphNodes} />
                ))}
                {state.visibleGraphNodes.map((node) => (
                  <div
                    key={node.id}
                    className={`absolute max-w-[120px] -translate-x-1/2 -translate-y-1/2 rounded-md border px-2 py-1.5 text-center text-xs font-semibold shadow-lg transition-all duration-700 ${graphNodeTone(node.tone)}`}
                    style={{ left: `${node.x}%`, top: `${node.y}%` }}
                  >
                    {node.label}
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <BarChart3 className="h-4 w-4 text-amber-300" />
                MITRE heatmap em tempo real
              </div>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {state.visibleMitreCells.map((cell) => (
                  <div
                    key={cell.technique}
                    className="rounded-md border border-amber-400/30 bg-amber-500/10 p-3 transition-all duration-500"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-xs font-semibold uppercase tracking-wide text-amber-200">
                        {cell.tactic}
                      </span>
                      <span className="font-mono text-xs text-amber-100">{cell.technique}</span>
                    </div>
                    <div className="mt-1 text-sm text-slate-200">{cell.label}</div>
                    <div className="mt-2 flex gap-1">
                      {[1, 2, 3].map((level) => (
                        <span
                          key={level}
                          className={`h-1.5 flex-1 rounded-full ${level <= cell.intensity ? 'bg-amber-300' : 'bg-slate-800'}`}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-5">
            <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <AlertTriangle className="h-4 w-4 text-orange-300" />
                Findings
              </div>
              <div className="mt-4 space-y-3">
                {state.visibleFindings.map((finding) => (
                  <div
                    key={finding.id}
                    className={`rounded-md border p-3 transition-all duration-500 animate-in fade-in zoom-in-95 ${severityTone(finding.severity)}`}
                  >
                    <div className="text-xs font-semibold uppercase tracking-wide opacity-80">
                      {finding.severity}
                    </div>
                    <div className="mt-1 font-semibold">{finding.title}</div>
                    <p className="mt-1 text-sm leading-5 opacity-85">{finding.description}</p>
                    <div className="mt-2 rounded bg-black/20 px-2 py-1 text-xs">{finding.evidence}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <DollarSign className="h-4 w-4 text-emerald-300" />
                Cost vs Human Analyst
              </div>
              <div className="mt-4 space-y-3">
                <MetricCard label="Tempo decorrido" value={state.metrics.elapsedLabel} sub="demo end-to-end" />
                <MetricCard label="Custo IA" value={USD.format(state.metrics.costUsd)} sub="atualizado em tempo real" />
                <MetricCard label="Custo humano estimado" value={USD.format(state.metrics.humanCostUsd)} sub={`${state.metrics.hoursSaved.toFixed(1)} horas poupadas`} />
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-md border border-slate-700 bg-slate-900/80 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <FileText className="h-4 w-4 text-cyan-300" />
              Final reveal: relatório completo
            </div>
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${state.reportReady ? 'bg-emerald-500/15 text-emerald-200' : 'bg-slate-800 text-slate-400'}`}>
              {state.reportReady ? '8-12 páginas prontas' : 'montando relatório'}
            </span>
          </div>
          {state.reportReady ? (
            <div
              data-testid="bacen-report-download"
              className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-md border border-amber-500/30 bg-amber-500/5 p-4"
            >
              <div className="flex items-start gap-3 text-amber-100">
                <Landmark className="h-5 w-5 flex-shrink-0 text-amber-300" />
                <div>
                  <div className="text-sm font-semibold text-amber-50">
                    Comunicação imediata Bacen (24h) — rascunho pronto
                  </div>
                  <div className="mt-1 text-xs text-amber-200/80">
                    Conforme Res. BCB 85/2021 Art. 9 · revisão humana obrigatória antes do envio
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  const now = new Date();
                  const md = buildBacenCommunication({ state, now });
                  const filename = buildBacenFilename(now);
                  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
                  const url = URL.createObjectURL(blob);
                  const link = document.createElement('a');
                  link.href = url;
                  link.download = filename;
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                  URL.revokeObjectURL(url);
                }}
                className="inline-flex items-center gap-2 rounded-md bg-amber-400 px-4 py-2 text-sm font-semibold text-amber-950 transition hover:bg-amber-300"
              >
                <Download className="h-4 w-4" />
                Baixar comunicação (.md)
              </button>
            </div>
          ) : null}
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            {state.reportPages.map((page) => (
              <div key={page.page} className="min-h-[150px] rounded-md border border-slate-700 bg-slate-950/55 p-3">
                <div className="text-xs font-semibold uppercase tracking-wide text-cyan-300">
                  página {page.page}
                </div>
                <div className="mt-1 font-semibold text-slate-100">{page.title}</div>
                <ul className="mt-3 space-y-1.5 text-sm text-slate-400">
                  {page.bullets.map((bullet) => (
                    <li key={bullet} className="flex gap-2">
                      <span className="mt-2 h-1 w-1 flex-shrink-0 rounded-full bg-cyan-300" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
