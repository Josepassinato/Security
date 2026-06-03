'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, CheckCircle2, ShieldCheck } from 'lucide-react';

type IntakeResponse = {
  intake: {
    id: string;
    companyName: string;
    offerPriceBrl: number;
    listPriceBrl: number;
    riskTier: string;
    riskScore: number;
    commercialPath: 'free_triage' | 'paid_diagnostic';
    trialEndsAt?: string | null;
    triageNotes: string[];
    paymentMode: 'external_checkout' | 'proposal';
    checkoutUrl: string | null;
    onboardingPath: string;
  };
  next: {
    message: string;
    checkoutUrl: string | null;
    onboardingUrl: string;
    paymentMode: 'external_checkout' | 'proposal';
  };
};

const fintechModels = [
  'Conta digital / IP',
  'BaaS / Banking as a Service',
  'Gateway Pix / pagamentos',
  'Credito / SCD / SEP',
  'Adquirencia / subadquirencia',
  'Crypto / ativos digitais',
  'Cambio / remessas',
  'Outro modelo financeiro',
];

const transactionRanges = [
  'Ate 10 mil transacoes/mes',
  '10 mil a 100 mil transacoes/mes',
  '100 mil a 500 mil transacoes/mes',
  'Acima de 500 mil transacoes/mes',
];

const volumeRanges = [
  'Ate R$ 5 milhoes/mes',
  'R$ 5 mi a R$ 50 mi/mes',
  'R$ 50 mi a R$ 250 mi/mes',
  'Acima de R$ 250 mi/mes',
];

function formatBrl(value: number) {
  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0,
  });
}

export function DiagnosticIntakeForm() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [response, setResponse] = useState<IntakeResponse | null>(null);

  const ctaLabel = useMemo(() => {
    if (!response) return 'Solicitar diagnostico';
    if (response.intake.commercialPath === 'free_triage') return 'Abrir triagem gratuita';
    return response.next.checkoutUrl ? 'Pagar diagnostico' : 'Abrir onboarding tecnico';
  }, [response]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError('');
    const form = new FormData(event.currentTarget);
    const submitter = (event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null;
    form.set('commercialPath', submitter?.value === 'free_triage' ? 'free_triage' : 'paid_diagnostic');
    const payload = Object.fromEntries(form.entries());

    try {
      const res = await fetch('/api/pld-ft/intake', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Erro ao criar cadastro.');
      setResponse(data);
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar cadastro.');
    } finally {
      setLoading(false);
    }
  }

  if (response) {
    const target = response.next.checkoutUrl || response.next.onboardingUrl;
    return (
      <div className="rounded-[2rem] border border-emerald-200 bg-white p-6 shadow-[0_24px_80px_rgba(25,60,40,0.12)]">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-emerald-100 p-3 text-emerald-800">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-700">
              Cadastro criado
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-[#17140f]">
              {response.intake.companyName} entrou na fila do diagnostico PLD/FT.
            </h2>
            <p className="mt-3 text-sm leading-6 text-[#514839]">{response.next.message}</p>
          </div>
        </div>

        <div className="mt-6 grid gap-3 rounded-2xl bg-[#f7f4ef] p-4 text-sm text-[#3a362e]">
          <div className="flex items-center justify-between gap-4">
            <span>{response.intake.commercialPath === 'free_triage' ? 'Triagem inicial' : 'Oferta de entrada'}</span>
            <strong>{response.intake.commercialPath === 'free_triage' ? 'Gratuita' : formatBrl(response.intake.offerPriceBrl)}</strong>
          </div>
          {response.intake.commercialPath === 'paid_diagnostic' && (
            <div className="flex items-center justify-between gap-4">
              <span>Preco cheio</span>
              <span className="line-through">{formatBrl(response.intake.listPriceBrl)}</span>
            </div>
          )}
          {response.intake.trialEndsAt && (
            <div className="flex items-center justify-between gap-4">
              <span>Validade</span>
              <strong>7 dias</strong>
            </div>
          )}
          <div className="flex items-center justify-between gap-4">
            <span>Triagem inicial</span>
            <strong>
              {response.intake.riskTier.toUpperCase()} · {response.intake.riskScore}/100
            </strong>
          </div>
        </div>

        <ul className="mt-5 grid gap-2 text-sm text-[#514839]">
          {response.intake.triageNotes.map((note) => (
            <li key={note} className="flex gap-2">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-700" />
              <span>{note}</span>
            </li>
          ))}
        </ul>

        <Link
          href={target}
          className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#17140f] px-6 py-4 text-sm font-semibold text-white no-underline transition hover:bg-[#2a241b]"
        >
          {ctaLabel}
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  return (
    <form
      onSubmit={submit}
      className="rounded-[2rem] border border-[#d8cdb9] bg-white p-5 shadow-[0_24px_80px_rgba(64,45,20,0.12)] sm:p-6"
    >
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#916f3b]">
          Comecar avaliacao
        </p>
        <h2 className="mt-2 text-2xl font-semibold text-[#17140f]">
          Cadastro da fintech
        </h2>
        <p className="mt-2 text-sm leading-6 text-[#514839]">
          O cadastro abre a triagem, gera o proximo passo comercial e libera o
          checklist tecnico para iniciar o diagnostico.
        </p>
      </div>

      <div className="mt-6 grid gap-4">
        <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
          Nome da fintech
          <input name="companyName" required className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]" />
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
            CNPJ
            <input name="cnpj" className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]" />
          </label>
          <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
            Site
            <input name="website" type="url" placeholder="https://" className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]" />
          </label>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
            Responsavel
            <input name="contactName" required className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]" />
          </label>
          <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
            Cargo
            <input name="contactRole" placeholder="Compliance Officer, CEO..." className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]" />
          </label>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
            E-mail corporativo
            <input name="email" type="email" required className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]" />
          </label>
          <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
            Telefone / WhatsApp
            <input name="phone" className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]" />
          </label>
        </div>
        <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
          Modelo da fintech
          <select name="fintechModel" required className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]">
            <option value="">Selecione</option>
            {fintechModels.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
            Transacoes mensais
            <select name="monthlyTransactions" className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]">
              <option value="">Nao informado</option>
              {transactionRanges.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
            Volume financeiro mensal
            <select name="monthlyVolume" className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]">
              <option value="">Nao informado</option>
              {volumeRanges.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
        </div>
        <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
          Controles atuais
          <textarea name="currentControls" rows={3} placeholder="Regras atuais, ferramentas, time, processo de decisao..." className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]" />
        </label>
        <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
          Principal preocupacao
          <textarea name="pain" rows={3} placeholder="Fraude Pix, conta de passagem, laranjas, falta de evidencia, auditoria..." className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]" />
        </label>
      </div>

      {error && <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      <div className="mt-6 grid gap-3">
        <button
          type="submit"
          name="commercialPath"
          value="free_triage"
          disabled={loading}
          className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-[#17140f] bg-white px-6 py-4 text-sm font-semibold text-[#17140f] transition hover:bg-[#f0e8d8] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? 'Criando cadastro...' : 'Fazer triagem gratuita'}
          <ArrowRight className="h-4 w-4" />
        </button>
        <button
          type="submit"
          name="commercialPath"
          value="paid_diagnostic"
          disabled={loading}
          className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#17140f] px-6 py-4 text-sm font-semibold text-white transition hover:bg-[#2a241b] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? 'Criando cadastro...' : 'Contratar diagnostico completo por R$ 18.000'}
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
      <p className="mt-3 text-xs leading-5 text-[#6c6252]">
        A triagem gratuita usa sandbox e informações declaradas. O diagnóstico pago entra em documentos,
        amostras anonimizadas e relatório executivo.
      </p>
    </form>
  );
}
