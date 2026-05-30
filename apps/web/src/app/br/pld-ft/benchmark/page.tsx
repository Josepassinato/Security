import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { runSyntheticBenchmark } from '@/lib/pldft/scenarios';

export const metadata: Metadata = {
  title: { absolute: 'Benchmark Sintético PLD/FT | Quarry' },
  description: 'Benchmark sintético do motor PLD/FT Quarry com cenários de conta laranja, fluxo limpo, PEP, fracionamento e sanção simulada.',
  alternates: { canonical: '/br/pld-ft/benchmark' },
};

function badge(ok: boolean) {
  return ok ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100' : 'border-red-500/30 bg-red-500/10 text-red-100';
}

export default function PldFtBenchmarkPage() {
  const rows = runSyntheticBenchmark();
  const pass = rows.filter((row) => row.matchedExpectation).length;

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="border-b border-white/10 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <Link href="/br/pld-ft/lab" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
            <ArrowLeft className="h-4 w-4" />
            Voltar para laboratório
          </Link>
          <h1 className="mt-6 text-4xl font-semibold tracking-tight text-white">Benchmark sintético PLD/FT</h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
            Validação inicial com cenários controlados. Isto não substitui teste com dados históricos reais, mas prova que o engine responde de forma previsível.
          </p>
        </div>
      </section>
      <section className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Cenários</p>
              <p className="mt-2 text-4xl font-semibold text-white">{rows.length}</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Expectativas batidas</p>
              <p className="mt-2 text-4xl font-semibold text-white">{pass}/{rows.length}</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Próximo passo</p>
              <p className="mt-2 text-sm leading-6 text-slate-300">Rodar o mesmo harness com dataset anonimizado de fintech real.</p>
            </div>
          </div>

          <div className="mt-6 overflow-hidden rounded-3xl border border-white/10 bg-white/[0.04]">
            <table className="w-full border-collapse text-left text-sm">
              <thead className="bg-white/[0.06] text-xs uppercase tracking-[0.16em] text-slate-400">
                <tr>
                  <th className="px-5 py-4">Cenário</th>
                  <th className="px-5 py-4">Esperado</th>
                  <th className="px-5 py-4">Detectado</th>
                  <th className="px-5 py-4">Score</th>
                  <th className="px-5 py-4">Achados</th>
                  <th className="px-5 py-4">Top regra</th>
                  <th className="px-5 py-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.scenarioId} className="border-t border-white/10">
                    <td className="px-5 py-4 font-semibold text-white">{row.name}</td>
                    <td className="px-5 py-4 text-slate-300">{row.expectedSeverity}</td>
                    <td className="px-5 py-4 text-slate-300">{row.actualSeverity}</td>
                    <td className="px-5 py-4 text-slate-300">{row.riskScore}/100</td>
                    <td className="px-5 py-4 text-slate-300">{row.findings}</td>
                    <td className="px-5 py-4 text-slate-300">{row.topRule}</td>
                    <td className="px-5 py-4">
                      <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${badge(row.matchedExpectation)}`}>
                        {row.matchedExpectation ? 'ok' : 'rever'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </main>
  );
}
