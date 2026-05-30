import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export const metadata: Metadata = {
  title: { absolute: 'Prontidão PLD/FT | Quarry' },
  description: 'Relatório de prontidão do módulo Quarry PLD/FT, separando o que está pronto, pendente de integração e pendente de validação especialista.',
  alternates: { canonical: '/br/pld-ft/readiness' },
};

const sections = [
  {
    title: 'Pronto em código',
    items: [
      'Engine determinístico de regras PLD/FT.',
      'Upload JSON/CSV e template transacional.',
      'Score explicável com evidências e transações citáveis.',
      'Dossiê exportável em Markdown e PDF via impressão.',
      'Fila local de casos com status e decisão humana.',
      'Matriz de regras e benchmark sintético.',
      'Painel de integrações pendentes.',
    ],
  },
  {
    title: 'Depende de integração',
    items: [
      'Webhook/API Pix e Core Banking.',
      'Base KYC/cadastral real.',
      'Device fingerprint, IP e geolocalização.',
      'Listas PEP, sanções, mídia adversa e fontes reputacionais.',
      'Persistência servidor-side em banco multi-tenant.',
      'Fila corporativa/GRC/SIEM para operação real.',
    ],
  },
  {
    title: 'Depende de especialista',
    items: [
      'Thresholds por produto e porte da fintech.',
      'Pesos de score e severidade.',
      'Política de bloqueio preventivo.',
      'Critérios de falso positivo aceitável.',
      'Quando escalar para jurídico/PLD.',
      'Quando comunicar regulador ou autoridade competente.',
    ],
  },
  {
    title: 'Depende de validação jurídica',
    items: [
      'Linguagem comercial e contratual.',
      'Procedimento de comunicação externa.',
      'Retenção de evidências e dados pessoais.',
      'Base legal LGPD e segregação de acesso.',
      'Limites do uso de IA e revisão humana obrigatória.',
    ],
  },
];

export default function PldFtReadinessPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="border-b border-white/10 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <Link href="/br/pld-ft/lab" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
            <ArrowLeft className="h-4 w-4" />
            Voltar para laboratório
          </Link>
          <h1 className="mt-6 text-4xl font-semibold tracking-tight text-white">Relatório de prontidão PLD/FT</h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
            Separação objetiva entre capacidade construída, integrações faltantes e validações necessárias antes de vender como controle de produção.
          </p>
        </div>
      </section>
      <section className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-4 md:grid-cols-2">
          {sections.map((section) => (
            <article key={section.title} className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
              <h2 className="text-2xl font-semibold text-white">{section.title}</h2>
              <ul className="mt-5 grid gap-3">
                {section.items.map((item) => (
                  <li key={item} className="rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-sm leading-6 text-slate-300">
                    {item}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
