'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  Download,
  FileCheck2,
  Gauge,
  LockKeyhole,
  Pause,
  Play,
  RefreshCw,
  ShieldCheck,
  Siren,
  WalletCards,
} from 'lucide-react';

type Severity = 'normal' | 'review' | 'high' | 'critical';

interface Transaction {
  id: string;
  at: string;
  customer: string;
  rail: 'Pix' | 'TED' | 'Boleto' | 'Open Finance';
  amount: string;
  destination: string;
  risk: number;
  status: 'Aprovada' | 'Em revisão' | 'Bloqueio sugerido' | 'Bloqueada';
  severity: Severity;
  reason: string;
}

interface Phase {
  label: string;
  description: string;
}

const PHASES: Phase[] = [
  {
    label: '1. Operação iniciada',
    description: 'A financeira FinPlay começa o dia com Pix, TED, boletos e acessos Open Finance entrando no Quarry.',
  },
  {
    label: '2. Fiscalização em tempo real',
    description: 'O Quarry normaliza eventos, calcula risco por entidade e separa transação comum de comportamento anômalo.',
  },
  {
    label: '3. Padrão detectado',
    description: 'Contas novas, SIM swap, repasses fracionados e scraping de Open Finance entram no mesmo grafo de ataque.',
  },
  {
    label: '4. Caso aberto',
    description: 'O agente abre um caso auditável, preserva evidências e recomenda bloqueio controlado com revisão humana.',
  },
  {
    label: '5. Relatórios emitidos',
    description: 'O sistema gera relatório executivo, relatório técnico e rascunho de comunicação Bacen/ANPD quando aplicável.',
  },
];

const TRANSACTIONS: Transaction[] = [
  {
    id: 'TX-884120',
    at: '09:02:11',
    customer: 'Cliente PJ 3812',
    rail: 'Pix',
    amount: 'R$ 8.420,00',
    destination: 'Fornecedor recorrente',
    risk: 12,
    status: 'Aprovada',
    severity: 'normal',
    reason: 'Perfil conhecido, destino recorrente e dispositivo confiável.',
  },
  {
    id: 'TX-884121',
    at: '09:04:37',
    customer: 'Cliente PF 8841',
    rail: 'Open Finance',
    amount: 'Consulta saldo',
    destination: 'App ofx-ghost',
    risk: 63,
    status: 'Em revisão',
    severity: 'review',
    reason: 'Consentimento recém-criado consultando múltiplas contas em janela curta.',
  },
  {
    id: 'TX-884122',
    at: '09:06:02',
    customer: 'Cliente PF 8841',
    rail: 'Pix',
    amount: 'R$ 48.900,00',
    destination: 'Conta nova 0291',
    risk: 86,
    status: 'Bloqueio sugerido',
    severity: 'high',
    reason: 'Primeiro Pix alto após troca de dispositivo e falha biométrica.',
  },
  {
    id: 'TX-884123',
    at: '09:07:18',
    customer: 'Conta nova 0291',
    rail: 'Pix',
    amount: 'R$ 16.300,00',
    destination: 'Conta laranja 7710',
    risk: 94,
    status: 'Bloqueada',
    severity: 'critical',
    reason: 'Fracionamento em cadeia para recebedor final já correlacionado.',
  },
  {
    id: 'TX-884124',
    at: '09:08:04',
    customer: 'Conta nova 0291',
    rail: 'Pix',
    amount: 'R$ 15.980,00',
    destination: 'Conta laranja 5532',
    risk: 96,
    status: 'Bloqueada',
    severity: 'critical',
    reason: 'Mesmo device virtualizado, ASN suspeito e repetição de janela temporal.',
  },
  {
    id: 'TX-884125',
    at: '09:09:41',
    customer: 'Cliente PJ 1102',
    rail: 'TED',
    amount: 'R$ 22.100,00',
    destination: 'Folha de pagamento',
    risk: 18,
    status: 'Aprovada',
    severity: 'normal',
    reason: 'Valor compatível com histórico e favorecido validado.',
  },
  {
    id: 'TX-884126',
    at: '09:11:22',
    customer: 'Conta laranja 5532',
    rail: 'Boleto',
    amount: 'R$ 4.900,00',
    destination: 'Beneficiário recém-criado',
    risk: 88,
    status: 'Bloqueio sugerido',
    severity: 'high',
    reason: 'Boleto criado após Pix suspeito para testar rota de saída.',
  },
  {
    id: 'TX-884127',
    at: '09:12:09',
    customer: 'Cliente PF 8841',
    rail: 'Pix',
    amount: 'R$ 51.200,00',
    destination: 'Conta nova 1840',
    risk: 97,
    status: 'Bloqueada',
    severity: 'critical',
    reason: 'Segundo Pix alto após SIM swap, fora do padrão e ligado ao mesmo grafo.',
  },
];

const LEDGER = [
  'Evento normalizado no schema Quarry Financial Event v1.',
  'Score de risco calculado por entidade: cliente, dispositivo, chave Pix e destino.',
  'Hipótese criada: cash-out por contas-laranja após SIM swap.',
  'Grafo correlacionou 8 transações, 5 contas, 2 dispositivos e 1 app Open Finance.',
  'Ação recomendada: bloqueio preventivo + revisão humana antes de comunicação externa.',
  'Relatórios gerados com evidência, linha do tempo e controles BACEN/LGPD acionados.',
];

const REPORTS = [
  {
    title: 'Relatório executivo',
    filename: 'finplay-relatorio-executivo.md',
    body: 'Resumo para diretoria: R$ 132.380,00 sob risco, 3 transações bloqueadas e 1 caso crítico aberto.',
  },
  {
    title: 'Relatório técnico',
    filename: 'finplay-relatorio-tecnico.md',
    body: 'Linha do tempo, IOCs, contas correlacionadas, device fingerprint, queries e racional do agente.',
  },
  {
    title: 'Rascunho Bacen 24h',
    filename: 'finplay-comunicacao-bacen-24h.md',
    body: 'Comunicação assistida por IA com natureza do incidente, impacto, medidas adotadas e prazo regulatório.',
  },
  {
    title: 'Anexo LGPD/ANPD',
    filename: 'finplay-anexo-lgpd-anpd.md',
    body: 'Checklist para avaliar dado pessoal envolvido, titulares afetados e necessidade de notificação.',
  },
];

function severityClass(severity: Severity): string {
  if (severity === 'critical') return 'border-red-500/40 bg-red-500/10 text-red-100';
  if (severity === 'high') return 'border-orange-500/40 bg-orange-500/10 text-orange-100';
  if (severity === 'review') return 'border-amber-500/40 bg-amber-500/10 text-amber-100';
  return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100';
}

export function FinancialOpsSimulation() {
  const [tick, setTick] = useState(0);
  const [running, setRunning] = useState(true);

  useEffect(() => {
    if (!running) return undefined;
    const id = window.setInterval(() => {
      setTick((current) => Math.min(current + 1, 23));
    }, 1150);
    return () => window.clearInterval(id);
  }, [running]);

  const visibleTransactions = useMemo(() => {
    const count = Math.min(Math.max(tick - 1, 1), TRANSACTIONS.length);
    return TRANSACTIONS.slice(0, count);
  }, [tick]);

  const phase = PHASES[Math.min(Math.floor(tick / 5), PHASES.length - 1)];
  const riskAverage = Math.round(
    visibleTransactions.reduce((sum, tx) => sum + tx.risk, 0) / visibleTransactions.length,
  );
  const blocked = visibleTransactions.filter((tx) => tx.status === 'Bloqueada').length;
  const critical = visibleTransactions.filter((tx) => tx.severity === 'critical').length;
  const reportsReady = tick >= 20;
  const progress = Math.min(Math.round((tick / 23) * 100), 100);

  function downloadReport(report: (typeof REPORTS)[number]) {
    const content = [
      `# ${report.title}`,
      '',
      '**Instituição simulada:** FinPlay Pagamentos S.A.',
      '**Caso:** CASE-FINPLAY-PIX-001',
      '**Status:** emitido automaticamente pelo Quarry em ambiente demonstrativo.',
      '',
      '## Resumo',
      '',
      report.body,
      '',
      '## Evidências principais',
      '',
      '- R$ 132.380,00 em transações sob risco.',
      '- 8 transações analisadas na simulação operacional.',
      '- 3 transações bloqueadas preventivamente.',
      '- SIM swap, device novo, app Open Finance suspeito e contas-laranja correlacionadas.',
      '- Ledger preservando normalização, score, hipótese, grafo, ação e relatório.',
      '',
      '## Próximos passos',
      '',
      '1. Revisão humana do caso e das ações recomendadas.',
      '2. Validação de comunicação Bacen/ANPD conforme aplicabilidade regulatória.',
      '3. Preservação das evidências no Threat Ledger / AuditChain.',
      '',
      '_Documento demonstrativo gerado pelo Quarry._',
    ].join('\n');
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = report.filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="border-b border-slate-800 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Link href="/" className="text-sm text-slate-400 hover:text-white">
              ← Voltar para Quarry
            </Link>
            <p className="mt-8 inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-blue-200">
              <WalletCards className="h-3.5 w-3.5" aria-hidden="true" />
              Simulação completa · financeira em operação
            </p>
            <h1 className="mt-5 max-w-4xl text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
              FinPlay operando transações. Quarry fiscalizando em tempo real.
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-relaxed text-slate-300">
              Acompanhe do início ao fim: eventos financeiros entram, o motor calcula risco,
              detecta padrão de fraude, abre caso, preserva evidência e emite os relatórios de
              diretoria, técnico, Bacen e LGPD.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setRunning((value) => !value)}
              className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-100 hover:border-blue-500/50"
            >
              {running ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              {running ? 'Pausar' : 'Continuar'}
            </button>
            <button
              type="button"
              onClick={() => {
                setTick(0);
                setRunning(true);
              }}
              className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-100 hover:border-blue-500/50"
            >
              <RefreshCw className="h-4 w-4" />
              Reiniciar
            </button>
          </div>
        </div>
      </section>

      <section className="px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-4 lg:grid-cols-[0.95fr_1.4fr_0.95fr]">
          <aside className="space-y-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-slate-200">{phase.label}</p>
                <span className="rounded-full bg-blue-500/15 px-2 py-1 text-xs text-blue-200">
                  {progress}%
                </span>
              </div>
              <div className="mt-4 h-2 rounded-full bg-slate-800">
                <div
                  className="h-2 rounded-full bg-blue-500 transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="mt-4 text-sm leading-relaxed text-slate-400">{phase.description}</p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
              <Metric icon={Gauge} label="Risco médio" value={`${riskAverage}`} tone="blue" />
              <Metric icon={Siren} label="Críticos" value={`${critical}`} tone="red" />
              <Metric icon={LockKeyhole} label="Bloqueadas" value={`${blocked}`} tone="orange" />
              <Metric icon={Clock3} label="SLA Bacen" value={critical ? '24h' : 'N/A'} tone="emerald" />
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
              <p className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                <ShieldCheck className="h-4 w-4 text-blue-300" />
                Controles acionados
              </p>
              <ul className="mt-4 space-y-3 text-sm text-slate-300">
                <li className="flex gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />
                  Score por entidade e transação
                </li>
                <li className="flex gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />
                  Grafo Pix, device, conta e Open Finance
                </li>
                <li className="flex gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />
                  Ledger imutável das decisões
                </li>
                <li className="flex gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />
                  Evidência BACEN/LGPD preparada
                </li>
              </ul>
            </div>
          </aside>

          <section className="rounded-xl border border-slate-800 bg-slate-900/70">
            <div className="border-b border-slate-800 p-5">
              <p className="text-sm font-semibold text-slate-200">Esteira de transações</p>
              <p className="mt-1 text-sm text-slate-500">
                Transações fictícias para demonstrar fiscalização operacional.
              </p>
            </div>
            <div className="divide-y divide-slate-800">
              {visibleTransactions.map((tx) => (
                <article key={tx.id} className="grid gap-4 p-4 md:grid-cols-[1fr_auto]">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs text-slate-500">{tx.at}</span>
                      <span className="font-mono text-xs text-slate-400">{tx.id}</span>
                      <span className="rounded-full border border-slate-700 px-2 py-0.5 text-xs text-slate-300">
                        {tx.rail}
                      </span>
                      <span className={`rounded-full border px-2 py-0.5 text-xs ${severityClass(tx.severity)}`}>
                        risco {tx.risk}
                      </span>
                    </div>
                    <h2 className="mt-2 text-base font-semibold text-white">
                      {tx.customer} → {tx.destination}
                    </h2>
                    <p className="mt-1 text-sm text-slate-400">{tx.reason}</p>
                  </div>
                  <div className="md:text-right">
                    <p className="text-lg font-semibold text-white">{tx.amount}</p>
                    <p
                      className={
                        'mt-1 text-sm font-medium ' +
                        (tx.status === 'Bloqueada'
                          ? 'text-red-300'
                          : tx.status === 'Bloqueio sugerido'
                            ? 'text-orange-300'
                            : tx.status === 'Em revisão'
                              ? 'text-amber-300'
                              : 'text-emerald-300')
                      }
                    >
                      {tx.status}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <aside className="space-y-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
              <p className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                <AlertTriangle className="h-4 w-4 text-orange-300" />
                Caso aberto
              </p>
              <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-red-200">
                  CASE-FINPLAY-PIX-001
                </p>
                <h2 className="mt-2 text-base font-semibold text-white">
                  Cash-out Pix após SIM swap
                </h2>
                <p className="mt-2 text-sm leading-relaxed text-red-100/80">
                  Padrão provável de conta-laranja com repasse fracionado e uso indevido de Open
                  Finance para seleção de vítima.
                </p>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
              <p className="text-sm font-semibold text-slate-200">Investigation Ledger</p>
              <ol className="mt-4 space-y-3">
                {LEDGER.slice(0, Math.min(Math.max(tick - 2, 1), LEDGER.length)).map((item, idx) => (
                  <li key={item} className="flex gap-3 text-sm text-slate-300">
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-500/15 text-[11px] font-bold text-blue-200">
                      {idx + 1}
                    </span>
                    {item}
                  </li>
                ))}
              </ol>
            </div>
          </aside>
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl rounded-xl border border-slate-800 bg-slate-900/70 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                <FileCheck2 className="h-4 w-4 text-blue-300" />
                Emissão dos relatórios
              </p>
              <p className="mt-1 text-sm text-slate-500">
                Os documentos aparecem quando a simulação chega ao fim da investigação.
              </p>
            </div>
            <span
              className={
                'rounded-full px-3 py-1 text-xs font-semibold ' +
                (reportsReady ? 'bg-emerald-500/15 text-emerald-200' : 'bg-slate-800 text-slate-400')
              }
            >
              {reportsReady ? 'Relatórios prontos' : 'Coletando evidências'}
            </span>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {REPORTS.map((report, idx) => {
              const ready = reportsReady || tick > 16 + idx;
              return (
                <article
                  key={report.title}
                  className={
                    'rounded-lg border p-4 transition ' +
                    (ready
                      ? 'border-blue-500/30 bg-blue-500/10'
                      : 'border-slate-800 bg-slate-950/50 opacity-55')
                  }
                >
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-sm font-semibold text-white">{report.title}</h3>
                    {ready ? (
                      <Download className="h-4 w-4 text-blue-300" aria-hidden="true" />
                    ) : (
                      <Clock3 className="h-4 w-4 text-slate-500" aria-hidden="true" />
                    )}
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-slate-400">{report.body}</p>
                  <button
                    type="button"
                    disabled={!ready}
                    onClick={() => downloadReport(report)}
                    className={
                      'mt-4 inline-flex items-center gap-2 rounded-md px-3 py-2 text-xs font-semibold transition ' +
                      (ready
                        ? 'bg-blue-500 text-white hover:bg-blue-400'
                        : 'cursor-not-allowed bg-slate-800 text-slate-500')
                    }
                  >
                    <Download className="h-3.5 w-3.5" aria-hidden="true" />
                    Baixar .md
                  </button>
                </article>
              );
            })}
          </div>
        </div>
      </section>
    </main>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Gauge;
  label: string;
  value: string;
  tone: 'blue' | 'red' | 'orange' | 'emerald';
}) {
  const colors = {
    blue: 'border-blue-500/30 bg-blue-500/10 text-blue-200',
    red: 'border-red-500/30 bg-red-500/10 text-red-200',
    orange: 'border-orange-500/30 bg-orange-500/10 text-orange-200',
    emerald: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200',
  };

  return (
    <div className={`rounded-xl border p-4 ${colors[tone]}`}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-[0.16em] opacity-80">{label}</p>
        <Icon className="h-4 w-4" aria-hidden="true" />
      </div>
      <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
    </div>
  );
}
