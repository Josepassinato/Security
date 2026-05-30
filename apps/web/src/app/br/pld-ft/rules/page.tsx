import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { pldRuleCatalog } from '@/lib/pldft/rules';

export const metadata: Metadata = {
  title: { absolute: 'Matriz de Regras PLD/FT | Quarry' },
  description: 'Matriz técnica das regras determinísticas PLD/FT do Quarry, com inputs, condições e pontos para validação especialista.',
  alternates: { canonical: '/br/pld-ft/rules' },
};

export default function PldFtRulesPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="border-b border-white/10 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <Link href="/br/pld-ft/lab" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
            <ArrowLeft className="h-4 w-4" />
            Voltar para laboratório
          </Link>
          <h1 className="mt-6 text-4xl font-semibold tracking-tight text-white">Matriz de regras PLD/FT</h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
            Cada regra abaixo é determinística, versionável e pronta para validação de especialista. O objetivo é separar cálculo verificável de interpretação humana.
          </p>
        </div>
      </section>
      <section className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-4">
          {pldRuleCatalog.map((rule) => (
            <article key={rule.id} className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <div className="grid gap-5 lg:grid-cols-[0.85fr_1.15fr]">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-200">{rule.id}</p>
                  <h2 className="mt-2 text-2xl font-semibold text-white">{rule.title}</h2>
                  <p className="mt-3 text-sm leading-7 text-slate-300">{rule.objective}</p>
                  <p className="mt-4 rounded-2xl border border-blue-500/20 bg-blue-500/10 p-4 text-sm leading-6 text-blue-100">
                    <strong>Condição:</strong> {rule.deterministicCondition}
                  </p>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                    <p className="font-semibold text-white">Inputs necessários</p>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">
                      {rule.requiredInputs.map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                    <p className="font-semibold text-white">Falsos positivos comuns</p>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">
                      {rule.commonFalsePositives.map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                    <p className="font-semibold text-white">Ação recomendada</p>
                    <p className="mt-2 text-sm leading-6 text-slate-300">{rule.recommendedAction}</p>
                  </div>
                  <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4">
                    <p className="font-semibold text-amber-100">Validação especialista</p>
                    <p className="mt-2 text-sm leading-6 text-amber-100">{rule.specialistValidation}</p>
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
