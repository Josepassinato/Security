import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowRight, CheckCircle2, FileText, ShieldAlert, ShieldCheck, Workflow } from 'lucide-react';
import { DiagnosticIntakeForm } from '@/components/pldft/DiagnosticIntakeForm';

export const metadata: Metadata = {
  title: { absolute: 'Diagnóstico PLD/FT para fintechs | Quarry' },
  description:
    'Produto de entrada do Quarry para fintechs brasileiras: avaliação de exposição a fraude, lavagem de dinheiro e uso por organizações criminosas, com relatório executivo e plano de implantação.',
  alternates: { canonical: '/diagnostico-pld-ft' },
};

const deliverables = [
  'Reunião remota de contexto com responsáveis da fintech.',
  'Checklist PLD/FT, fraude, KYC/KYB, Pix, sanções e governança.',
  'Análise de amostra anonimizada de transações e clientes.',
  'Score de maturidade, principais lacunas e regras prioritárias.',
  'Relatório executivo para diretoria, compliance e jurídico.',
  'Plano de piloto de 60 dias com integrações e controles recomendados.',
];

const path = [
  ['Cadastro', 'A fintech informa modelo, volume, responsável e dor principal.'],
  ['Compra ou proposta', 'Checkout externo quando configurado; proposta comercial quando o pagamento ainda for assistido.'],
  ['Onboarding técnico', 'Checklist, documentos e amostras anonimizadas antes de qualquer API real.'],
  ['Diagnóstico', 'Quarry roda regras, score, evidências, lacunas e hipóteses revisáveis.'],
  ['Implantação', 'Se fizer sentido, conecta core/BaaS/Pix e abre monitoramento contínuo.'],
];

const checklist = [
  'Política PLD/FT e matriz de risco.',
  'Amostra CSV/JSON de transações.',
  'Base de clientes anonimizada.',
  'Regras e alertas atuais.',
  'Fluxo de decisão e responsáveis.',
  'Agenda para devolutiva executiva.',
];

export default function DiagnosticoPldFtPage() {
  return (
    <main data-theme="light" className="min-h-screen bg-[#f7f4ef] text-[#17140f]">
      <section className="border-b border-[#ddd4c6] px-5 pb-16 pt-10 sm:px-8 lg:pb-20">
        <nav className="mx-auto flex max-w-6xl items-center justify-between gap-4 py-4">
          <Link href="/" className="text-sm font-semibold text-[#514839] no-underline hover:text-[#17140f]">
            Quarry
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link href="/br/pld-ft" className="text-[#514839] no-underline hover:text-[#17140f]">
              PLD/FT
            </Link>
            <Link href="/demo-financeira" className="text-[#514839] no-underline hover:text-[#17140f]">
              Simulação
            </Link>
          </div>
        </nav>

        <div className="mx-auto grid max-w-6xl gap-10 pt-14 lg:grid-cols-[1.05fr_0.95fr] lg:items-start">
          <div>
            <p className="mb-5 text-xs font-bold uppercase tracking-[0.24em] text-[#916f3b]">
              Produto de entrada · Diagnóstico PLD/FT
            </p>
            <h1 className="max-w-4xl text-4xl font-semibold leading-[1.02] tracking-tight text-[#17140f] sm:text-6xl">
              Queremos avaliar se sua fintech pode estar vulnerável a fraude, lavagem e contas de passagem.
            </h1>
            <p className="mt-6 max-w-3xl text-lg leading-8 text-[#4d4639]">
              O diagnóstico Quarry foi desenhado para fintechs brasileiras que usam Pix,
              conta digital, BaaS, crédito, adquirência, cripto ou pagamentos e precisam
              provar que conseguem detectar movimentações anormais com evidência defensável.
            </p>
            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-[#d8cdb9] bg-white p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-[#916f3b]">Preço cheio</p>
                <p className="mt-2 text-2xl font-semibold line-through">R$ 60.000</p>
              </div>
              <div className="rounded-2xl border border-[#17140f] bg-[#17140f] p-4 text-white">
                <p className="text-xs uppercase tracking-[0.16em] text-[#d8b56d]">Oferta inicial</p>
                <p className="mt-2 text-2xl font-semibold">R$ 18.000</p>
              </div>
              <div className="rounded-2xl border border-[#d8cdb9] bg-white p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-[#916f3b]">Entrega</p>
                <p className="mt-2 text-2xl font-semibold">Remota</p>
              </div>
            </div>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <a
                href="#cadastro"
                className="inline-flex items-center justify-center gap-2 rounded-full bg-[#17140f] px-6 py-3 text-sm font-semibold text-white no-underline transition hover:bg-[#2a241b]"
              >
                Começar cadastro
                <ArrowRight className="h-4 w-4" />
              </a>
              <Link
                href="/br/pld-ft/readiness"
                className="inline-flex items-center justify-center rounded-full border border-[#17140f] bg-white px-6 py-3 text-sm font-semibold text-[#17140f] no-underline transition hover:bg-[#f0e8d8]"
              >
                Ver prontidão técnica
              </Link>
            </div>
          </div>

          <DiagnosticIntakeForm />
        </div>
      </section>

      <section className="border-b border-[#ddd4c6] bg-[#17140f] px-5 py-16 text-[#f7f4ef] sm:px-8">
        <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-[#d8b56d]">
              Por que isso compra atenção
            </p>
            <h2 className="mt-4 text-4xl font-semibold leading-tight">
              A fintech não precisa começar integrando tudo. Ela precisa primeiro saber onde está exposta.
            </h2>
            <p className="mt-5 text-base leading-7 text-[#d8d0c0]">
              O diagnóstico reduz a barreira comercial: entra como avaliação, gera evidência,
              mostra lacunas e cria o caminho para o monitoramento recorrente.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {deliverables.map((item) => (
              <div key={item} className="rounded-2xl border border-white/10 bg-white/[0.06] p-4 text-sm leading-6 text-[#f7f4ef]">
                <CheckCircle2 className="mb-3 h-5 w-5 text-[#d8b56d]" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-[#ddd4c6] px-5 py-16 sm:px-8">
        <div className="mx-auto max-w-6xl">
          <div className="max-w-3xl">
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-[#916f3b]">
              Fluxo de aquisição
            </p>
            <h2 className="mt-4 text-4xl font-semibold text-[#17140f]">
              Cadastro, aquisição e primeiro uso em uma jornada controlada.
            </h2>
          </div>
          <div className="mt-8 grid gap-4 md:grid-cols-5">
            {path.map(([title, body], index) => (
              <div key={title} className="rounded-3xl border border-[#d8cdb9] bg-white p-5">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-[#17140f] text-sm font-semibold text-white">
                  {index + 1}
                </div>
                <h3 className="font-semibold text-[#17140f]">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-[#514839]">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="cadastro" className="px-5 py-16 sm:px-8">
        <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[0.85fr_1.15fr]">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-[#916f3b]">
              O que a fintech prepara
            </p>
            <h2 className="mt-4 text-4xl font-semibold text-[#17140f]">
              Onboarding sem fricção, mas com responsabilidade.
            </h2>
            <p className="mt-5 text-base leading-7 text-[#514839]">
              Após o cadastro, o sistema libera um workspace para checklist e uploads.
              O diagnóstico começa com dados anonimizados e documentos, antes de qualquer
              integração com produção.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {checklist.map((item) => (
              <div key={item} className="rounded-2xl border border-[#d8cdb9] bg-white p-4 text-sm leading-6 text-[#514839]">
                <FileText className="mb-3 h-5 w-5 text-[#916f3b]" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-[#ddd4c6] bg-white px-5 py-12 sm:px-8">
        <div className="mx-auto grid max-w-6xl gap-4 md:grid-cols-3">
          {[
            [ShieldAlert, 'Controle agressivo de risco', 'Posicionamento forte contra fraude, lavagem e uso por organizações criminosas.'],
            [Workflow, 'Produto que vira implantação', 'O diagnóstico vira backlog técnico para monitoramento mensal e gestão de casos.'],
            [ShieldCheck, 'Humano no ponto certo', 'O sistema organiza evidência; decisões sensíveis continuam com compliance e jurídico.'],
          ].map(([Icon, title, body]) => {
            const TypedIcon = Icon as typeof ShieldCheck;
            return (
              <div key={String(title)} className="rounded-3xl border border-[#d8cdb9] bg-[#fffaf1] p-6">
                <TypedIcon className="h-6 w-6 text-[#916f3b]" />
                <h3 className="mt-4 text-xl font-semibold text-[#17140f]">{title as string}</h3>
                <p className="mt-3 text-sm leading-6 text-[#514839]">{body as string}</p>
              </div>
            );
          })}
        </div>
      </section>
    </main>
  );
}
