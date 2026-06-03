'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, CheckCircle2, FileUp, Loader2, ShieldCheck } from 'lucide-react';

type Intake = {
  id: string;
  companyName: string;
  contactName: string;
  email: string;
  status: string;
  riskTier: string;
  riskScore: number;
  checklist: Record<string, boolean>;
  uploads: Array<{
    id: string;
    purpose: string;
    originalName: string;
    size: number;
    uploadedAt: string;
  }>;
};

const checklistItems = [
  ['contexto_operacional', 'Contexto operacional', 'Produto financeiro, canais, Pix, BaaS/core, tipos de cliente e regioes atendidas.'],
  ['politica_pldft', 'Politica PLD/FT', 'Politica vigente, manuais internos e processo de revisao/aprovacao.'],
  ['matriz_risco', 'Matriz de risco', 'Matriz KYC/KYB, produtos, canais, geografia, PEP, sancoes e perfil economico.'],
  ['amostra_transacoes', 'Amostra anonimizada', '30 a 90 dias de transacoes com IDs internos, valores, datas, canal e origem/destino.'],
  ['base_clientes', 'Base de clientes', 'Clientes/contas com tipo, perfil declarado, data de abertura e status KYC/KYB.'],
  ['regras_monitoramento', 'Regras atuais', 'Regras, thresholds, alertas, falso positivo e historico de decisoes.'],
  ['responsavel_compliance', 'Responsavel de compliance', 'Nome do responsavel, aprovadores, comite e fluxo de decisao.'],
  ['agenda_devolutiva', 'Agenda de devolutiva', 'Janela para reuniao executiva e entrega do relatorio final.'],
] as const;

const uploadPurposes = [
  ['politica_pldft', 'Politica PLD/FT'],
  ['matriz_risco', 'Matriz de risco'],
  ['transacoes_csv', 'CSV/JSON de transacoes'],
  ['clientes_csv', 'Base de clientes'],
  ['regras_atuais', 'Regras atuais'],
  ['outro', 'Outro documento'],
];

function formatBytes(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

export function OnboardingWorkspace() {
  const params = useSearchParams();
  const id = params.get('id') || '';
  const [intake, setIntake] = useState<Intake | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const progress = useMemo(() => {
    if (!intake) return 0;
    const done = checklistItems.filter(([key]) => intake.checklist?.[key]).length;
    return Math.round((done / checklistItems.length) * 100);
  }, [intake]);

  useEffect(() => {
    async function load() {
      if (!id) {
        setLoading(false);
        setError('ID do cadastro nao informado.');
        return;
      }
      try {
        const res = await fetch(`/api/pld-ft/intake/${encodeURIComponent(id)}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Cadastro nao encontrado.');
        setIntake(data.intake);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro ao carregar onboarding.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  async function toggleItem(key: string) {
    if (!intake) return;
    setSaving(true);
    setMessage('');
    const checklist = { [key]: !intake.checklist?.[key] };
    try {
      const res = await fetch('/api/pld-ft/onboarding', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: intake.id, checklist }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Erro ao atualizar checklist.');
      setIntake(data.intake);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar checklist.');
    } finally {
      setSaving(false);
    }
  }

  async function upload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!intake) return;
    setUploading(true);
    setMessage('');
    setError('');
    const form = new FormData(event.currentTarget);
    form.set('id', intake.id);
    try {
      const res = await fetch('/api/pld-ft/onboarding', {
        method: 'POST',
        body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Erro ao enviar arquivo.');
      setIntake(data.intake);
      setMessage('Arquivo registrado no onboarding.');
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao enviar arquivo.');
    } finally {
      setUploading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-[#514839]">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Carregando onboarding...
      </div>
    );
  }

  if (!intake) {
    return (
      <div className="mx-auto max-w-3xl rounded-[2rem] border border-red-200 bg-white p-8 text-red-700">
        <p>{error || 'Cadastro nao encontrado.'}</p>
        <Link href="/diagnostico-pld-ft" className="mt-4 inline-flex text-sm font-semibold text-[#17140f]">
          Voltar para cadastro
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-5 py-28 sm:px-8">
      <Link href="/diagnostico-pld-ft" className="inline-flex items-center gap-2 text-sm font-semibold text-[#5b5142] no-underline hover:text-[#17140f]">
        <ArrowLeft className="h-4 w-4" />
        Voltar para diagnostico
      </Link>

      <div className="mt-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <aside className="rounded-[2rem] border border-[#d8cdb9] bg-[#fffaf1] p-6 shadow-[0_24px_80px_rgba(64,45,20,0.12)]">
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-[#916f3b]">
            Onboarding tecnico
          </p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight text-[#17140f]">
            {intake.companyName}
          </h1>
          <p className="mt-4 text-sm leading-6 text-[#514839]">
            Responsavel: <strong>{intake.contactName}</strong> · {intake.email}
          </p>
          <div className="mt-6 rounded-2xl bg-white p-4">
            <div className="flex items-center justify-between text-sm">
              <span>Progresso do checklist</span>
              <strong>{progress}%</strong>
            </div>
            <div className="mt-3 h-3 overflow-hidden rounded-full bg-[#eadff2]">
              <div className="h-full rounded-full bg-[#17140f]" style={{ width: `${progress}%` }} />
            </div>
          </div>
          <div className="mt-4 grid gap-3 rounded-2xl bg-white p-4 text-sm text-[#514839]">
            <div className="flex items-center justify-between gap-3">
              <span>Triagem de risco</span>
              <strong>{intake.riskTier.toUpperCase()} · {intake.riskScore}/100</strong>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span>Status</span>
              <strong>{intake.status.replace(/_/g, ' ')}</strong>
            </div>
          </div>
          <p className="mt-5 text-xs leading-5 text-[#6c6252]">
            Nesta etapa a fintech ainda nao precisa integrar API real. O time pode iniciar
            com documentos, CSV/JSON anonimizados e contexto operacional.
          </p>
        </aside>

        <section className="grid gap-6">
          <div className="rounded-[2rem] border border-[#d8cdb9] bg-white p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-2xl font-semibold text-[#17140f]">Checklist de prontidao</h2>
                <p className="mt-2 text-sm leading-6 text-[#514839]">
                  Marque o que ja foi entregue ou validado. Cada item vira parte da trilha operacional do diagnostico.
                </p>
              </div>
              {saving && <Loader2 className="h-5 w-5 animate-spin text-[#916f3b]" />}
            </div>
            <div className="mt-6 grid gap-3">
              {checklistItems.map(([key, title, body]) => {
                const checked = Boolean(intake.checklist?.[key]);
                return (
                  <button
                    key={key}
                    onClick={() => toggleItem(key)}
                    className={`grid gap-1 rounded-2xl border p-4 text-left transition ${
                      checked
                        ? 'border-emerald-200 bg-emerald-50'
                        : 'border-[#e3d9ca] bg-[#fffaf1] hover:border-[#17140f]'
                    }`}
                  >
                    <span className="flex items-center gap-2 font-semibold text-[#17140f]">
                      {checked ? <CheckCircle2 className="h-5 w-5 text-emerald-700" /> : <ShieldCheck className="h-5 w-5 text-[#916f3b]" />}
                      {title}
                    </span>
                    <span className="text-sm leading-6 text-[#514839]">{body}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="rounded-[2rem] border border-[#d8cdb9] bg-white p-6">
            <h2 className="text-2xl font-semibold text-[#17140f]">Upload de documentos e amostras</h2>
            <p className="mt-2 text-sm leading-6 text-[#514839]">
              Aceita PDF, CSV, JSON, XLSX ou documentos internos. Para o diagnostico inicial, prefira dados anonimizados.
            </p>
            <form onSubmit={upload} className="mt-5 grid gap-4 sm:grid-cols-[1fr_1.2fr_auto] sm:items-end">
              <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
                Tipo
                <select name="purpose" className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]">
                  {uploadPurposes.map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </label>
              <label className="grid gap-1 text-sm font-semibold text-[#2a241b]">
                Arquivo
                <input name="file" type="file" required className="rounded-xl border border-[#d8cdb9] bg-[#fffaf1] px-4 py-3 outline-none focus:border-[#17140f]" />
              </label>
              <button
                disabled={uploading}
                className="inline-flex items-center justify-center gap-2 rounded-full bg-[#17140f] px-5 py-3 text-sm font-semibold text-white disabled:opacity-60"
              >
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
                Enviar
              </button>
            </form>
            {message && <p className="mt-4 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p>}
            {error && <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
            <div className="mt-6 grid gap-3">
              {intake.uploads.length ? intake.uploads.map((uploadItem) => (
                <div key={uploadItem.id} className="rounded-2xl border border-[#e3d9ca] bg-[#fffaf1] p-4 text-sm text-[#514839]">
                  <strong className="text-[#17140f]">{uploadItem.originalName}</strong>
                  <div className="mt-1">
                    {uploadItem.purpose.replace(/_/g, ' ')} · {formatBytes(uploadItem.size)} · {new Date(uploadItem.uploadedAt).toLocaleString('pt-BR')}
                  </div>
                </div>
              )) : (
                <div className="rounded-2xl border border-dashed border-[#d8cdb9] bg-[#fffaf1] p-5 text-sm text-[#6c6252]">
                  Nenhum arquivo enviado ainda.
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
