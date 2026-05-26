import type { Metadata } from 'next';
import Link from 'next/link';
import {
  ArrowRight,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  LockKeyhole,
  ShieldCheck,
} from 'lucide-react';

export const metadata: Metadata = {
  title: 'Quarry — ISO/IEC 27001 readiness',
  description:
    'Quarry ISO/IEC 27001 readiness program: ISMS scope, risk management, evidence register, audit trail, secure development, and operational controls.',
};

const READINESS_STEPS = [
  {
    title: 'Escopo do SGSI',
    body: 'Desenvolvimento, operação, suporte e entrega comercial do Quarry, incluindo código, produção, acessos, fornecedores, evidências e resposta a incidentes.',
  },
  {
    title: 'Matriz de riscos',
    body: 'Riscos iniciais mapeados para VPS/root, segredos, deploys, backups, decisões de IA, fornecedores, vulnerabilidades e claims públicos.',
  },
  {
    title: 'Declaração de aplicabilidade',
    body: 'Controles organizacionais, pessoas, fornecedores, cloud, logging, backup, acesso, secure coding e governança de IA mapeados para evidências.',
  },
  {
    title: 'Biblioteca de evidências',
    body: 'Registro padronizado para access review, deploy, backup, restore, vulnerability management, incident response, supplier review e ledger do produto.',
  },
];

const CONTROL_AREAS = [
  'Access reviews',
  'Secure development',
  'Change management',
  'Backup and restore',
  'Incident response',
  'Supplier risk',
  'Vulnerability management',
  'AI decision logging',
  'AuditChain evidence',
  'Public claims control',
];

export default function Iso27001ReadinessPage() {
  return (
    <main className="min-h-screen bg-surface-base text-fg-primary">
      <section className="border-b border-surface-border px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm font-medium text-fg-secondary hover:text-fg-primary"
          >
            ← Voltar para Quarry
          </Link>

          <div className="mt-10 grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-brand-300">
                <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
                ISO/IEC 27001 readiness
              </p>
              <h1 className="mt-6 max-w-4xl text-4xl font-semibold leading-tight tracking-tight text-fg-primary sm:text-5xl">
                Quarry está sendo preparado para certificação ISO/IEC 27001.
              </h1>
              <p className="mt-6 max-w-2xl text-base leading-relaxed text-fg-secondary sm:text-lg">
                O objetivo é certificar o Sistema de Gestão de Segurança da Informação usado no
                desenvolvimento, operação e suporte do Quarry. A primeira etapa já estrutura escopo,
                riscos, controles, evidências e governança de IA auditável.
              </p>
              <p className="mt-4 max-w-2xl rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-sm leading-relaxed text-amber-100">
                Status: programa de prontidão. Esta página não declara que a 12Brain ou o Quarry já
                possuem certificação ISO/IEC 27001 emitida por certificadora.
              </p>
            </div>

            <div className="rounded-2xl border border-surface-border bg-surface-raised/40 p-6">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-fg-muted">
                Escopo recomendado
              </p>
              <p className="mt-3 text-sm leading-relaxed text-fg-secondary">
                SGSI para desenvolvimento, operação, suporte e entrega comercial do Quarry,
                incluindo infraestrutura, código, acessos, fornecedores, evidências, resposta a
                incidentes e auditoria das decisões dos agentes.
              </p>
              <div className="mt-6 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg border border-surface-border bg-surface-base/60 p-4">
                  <p className="text-2xl font-semibold text-fg-primary">90 dias</p>
                  <p className="mt-1 text-xs text-fg-muted">primeira janela de preparação</p>
                </div>
                <div className="rounded-lg border border-surface-border bg-surface-base/60 p-4">
                  <p className="text-2xl font-semibold text-fg-primary">12</p>
                  <p className="mt-1 text-xs text-fg-muted">políticas mínimas mapeadas</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-4 md:grid-cols-2">
            {READINESS_STEPS.map((step) => (
              <article
                key={step.title}
                className="rounded-xl border border-surface-border bg-surface-raised/35 p-6"
              >
                <ClipboardCheck className="h-6 w-6 text-brand-300" aria-hidden="true" />
                <h2 className="mt-4 text-lg font-semibold text-fg-primary">{step.title}</h2>
                <p className="mt-2 text-sm leading-relaxed text-fg-secondary">{step.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-surface-border px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-brand-300">
              Evidência antes de promessa
            </p>
            <h2 className="mt-4 text-3xl font-semibold leading-tight text-fg-primary">
              O diferencial do Quarry ajuda a própria certificação.
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-fg-secondary sm:text-base">
              Threat Ledger, AuditChain, logs de agentes e registros de decisão viram evidência
              operacional. Isso reduz a distância entre discurso comercial e prova auditável.
            </p>
          </div>

          <div className="grid gap-2 sm:grid-cols-2">
            {CONTROL_AREAS.map((area) => (
              <div
                key={area}
                className="flex items-center gap-2 rounded-lg border border-surface-border bg-surface-base/60 px-4 py-3 text-sm text-fg-secondary"
              >
                <CheckCircle2 className="h-4 w-4 shrink-0 text-brand-300" aria-hidden="true" />
                {area}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-surface-border px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl rounded-2xl border border-brand-500/30 bg-brand-500/5 p-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-500/15 text-brand-300">
                  <LockKeyhole className="h-5 w-5" aria-hidden="true" />
                </span>
                <h2 className="text-2xl font-semibold text-fg-primary">
                  Próximo passo: operar controles e coletar evidências.
                </h2>
              </div>
              <p className="mt-4 max-w-3xl text-sm leading-relaxed text-fg-secondary sm:text-base">
                A certificação real vem depois de operação, auditoria interna, revisão da direção e
                auditoria externa por certificadora. O pacote inicial cria o caminho para chegar lá
                sem depender de improviso.
              </p>
            </div>
            <Link
              href="/compliance/iso27001"
              className="inline-flex items-center justify-center gap-2 rounded-md bg-brand-600 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-500"
            >
              Ver dashboard ISO
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
