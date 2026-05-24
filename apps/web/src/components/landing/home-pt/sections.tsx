'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ArrowRight, Menu, X, Shield, Cpu, FileCheck2, Mail, Building2 } from 'lucide-react';
import { GithubMark } from '@/components/landing/sections/icons';
import { cn } from '@/lib/utils';

const NAV = [
  { label: 'Produto', href: '#produto' },
  { label: 'Para quem é', href: '#para-quem' },
  { label: 'Fintechs BR', href: '/br' },
  { label: 'Open-source', href: '/opensource' },
  { label: 'Demo', href: '/demo-cinematografica' },
];

export function HomeNav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    if (typeof document === 'undefined') return;
    document.body.style.overflow = open ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  return (
    <header
      className={cn(
        'fixed inset-x-0 top-0 z-50 transition-[background-color,border-color,backdrop-filter] duration-200',
        scrolled
          ? 'border-b border-surface-border bg-surface-base/85 backdrop-blur-md'
          : 'border-b border-transparent bg-transparent',
      )}
    >
      <nav aria-label="Primary" className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link href="/" aria-label="12Brain Solutions — início" className="flex items-center gap-2 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300">
          <span aria-hidden="true" className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-brand-400 to-brand-700 text-[10px] font-bold text-white shadow-[inset_0_0_0_1px_rgba(255,255,255,0.18)]">
            12B
          </span>
          <span className="text-base font-semibold tracking-tight text-fg-primary">
            12Brain<span className="text-fg-muted"> / Quarry</span>
          </span>
        </Link>

        <ul className="hidden items-center gap-1 lg:flex">
          {NAV.map((link) => (
            <li key={link.href}>
              <Link href={link.href} className="rounded-md px-3 py-2 text-sm font-medium text-fg-secondary transition-colors hover:text-fg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300">
                {link.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="hidden items-center gap-2 lg:flex">
          <a href="https://github.com/beenuar/Quarry" target="_blank" rel="noreferrer" aria-label="GitHub do Quarry" className="inline-flex items-center gap-2 rounded-md border border-surface-border bg-surface-raised/60 px-3 py-1.5 text-sm font-medium text-fg-secondary transition-colors hover:border-brand-500/40 hover:text-fg-primary">
            <GithubMark className="h-3.5 w-3.5" />
            <span>GitHub</span>
          </a>
          <Link href="#contato" className="group inline-flex items-center gap-1 rounded-md bg-gradient-to-br from-brand-500 to-brand-700 px-4 py-1.5 text-sm font-semibold text-white shadow-[0_1px_0_rgba(255,255,255,0.18)_inset] transition-shadow hover:shadow-[0_8px_24px_-8px_rgba(59,130,246,0.55)]">
            Falar com a 12Brain
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
          </Link>
        </div>

        <button type="button" onClick={() => setOpen(v => !v)} aria-expanded={open} aria-controls="home-pt-mobile-nav" aria-label={open ? 'Fechar menu' : 'Abrir menu'} className="inline-flex h-11 w-11 items-center justify-center rounded-md border border-surface-border bg-surface-raised/60 text-fg-secondary lg:hidden">
          {open ? <X className="h-4 w-4" aria-hidden="true" /> : <Menu className="h-4 w-4" aria-hidden="true" />}
        </button>
      </nav>

      <div id="home-pt-mobile-nav" className={cn('lg:hidden overflow-hidden border-t border-surface-border bg-surface-base/95 backdrop-blur-md transition-[max-height,opacity] duration-200', open ? 'max-h-[60vh] opacity-100' : 'max-h-0 opacity-0')}>
        <ul className="space-y-1 px-4 py-3">
          {NAV.map((link) => (
            <li key={link.href}>
              <Link href={link.href} onClick={() => setOpen(false)} className="block rounded-md px-3 py-3 text-sm font-medium text-fg-secondary hover:bg-surface-hover hover:text-fg-primary">
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
        <div className="px-4 pb-4">
          <Link href="#contato" onClick={() => setOpen(false)} className="block rounded-md bg-gradient-to-br from-brand-500 to-brand-700 px-3 py-3 text-center text-sm font-semibold text-white">
            Falar com a 12Brain
          </Link>
        </div>
      </div>
    </header>
  );
}

export function HeroEmpresa() {
  return (
    <section className="relative isolate overflow-hidden pt-32 pb-24 sm:pt-40 sm:pb-32">
      <div aria-hidden="true" className="absolute inset-0 -z-10">
        <div className="absolute inset-x-0 top-0 h-[120%] bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,rgba(59,130,246,0.18),transparent_70%)]" />
        <div className="absolute inset-x-0 top-1/3 h-px bg-gradient-to-r from-transparent via-surface-border to-transparent" />
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-surface-border bg-surface-raised/40 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-fg-secondary">
          <Building2 className="h-3 w-3" aria-hidden="true" />
          12Brain Solutions LLC · Coconut Creek, FL
        </p>
        <h1 className="max-w-4xl text-4xl font-semibold leading-[1.05] tracking-tight text-fg-primary sm:text-5xl lg:text-6xl">
          Infraestrutura de segurança econômica para{' '}
          <span className="bg-gradient-to-br from-brand-300 to-brand-500 bg-clip-text text-transparent">
            fintechs que crescem rápido
          </span>
          .
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-relaxed text-fg-secondary sm:text-xl">
          A 12Brain é a casa do <strong className="font-semibold text-fg-primary">Quarry</strong> — um SOC agêntico open-source que faz BACEN não tirar o sono de fintechs Seed/Série A. Sem MSSP de R$&nbsp;30 mil/mês, sem auditoria improvisada.
        </p>

        <div className="mt-10 flex flex-wrap items-center gap-3">
          <Link href="#produto" className="group inline-flex items-center gap-2 rounded-md bg-gradient-to-br from-brand-500 to-brand-700 px-5 py-3 text-sm font-semibold text-white shadow-[0_1px_0_rgba(255,255,255,0.18)_inset] transition-shadow hover:shadow-[0_8px_24px_-8px_rgba(59,130,246,0.55)]">
            Conhecer o Quarry
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
          </Link>
          <Link href="/demo-cinematografica" className="inline-flex items-center gap-2 rounded-md border border-surface-border bg-surface-raised/60 px-5 py-3 text-sm font-medium text-fg-primary hover:border-brand-500/40">
            Ver demo Pix →
          </Link>
          <Link href="/br" className="inline-flex items-center gap-2 rounded-md px-3 py-3 text-sm font-medium text-fg-secondary hover:text-fg-primary">
            Sou fintech BR
          </Link>
        </div>
      </div>
    </section>
  );
}

export function QuemSomos() {
  const stats = [
    { num: '13', label: 'produtos no portfólio 12Brain', sub: 'todos em produção' },
    { num: '2021', label: 'fundada em Coconut Creek, FL', sub: 'pelo José E. C. Passinato' },
    { num: 'MIT', label: 'licença do produto principal', sub: 'sem fork privado' },
  ];

  return (
    <section id="empresa" className="relative border-t border-surface-border py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-brand-300">01 — A empresa</p>
        <div className="mt-6 grid gap-12 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <h2 className="text-3xl font-semibold leading-tight text-fg-primary sm:text-4xl">
              Construímos software que <em className="font-medium text-brand-300 not-italic">resolve coisa cara</em> de um jeito barato.
            </h2>
            <div className="mt-6 space-y-5 text-base leading-relaxed text-fg-secondary sm:text-lg">
              <p>
                A 12Brain Solutions é uma operação enxuta sediada em Coconut Creek, Flórida, focada em produtos onde regulação encontra IA. Não somos consultoria. Não somos integradora. Construímos software próprio, lançamos em produção, e cobramos por valor entregue — não por hora.
              </p>
              <p>
                O Quarry é o produto principal do portfólio: um Security Operations Center agêntico, MIT-licensed, que substitui MSSPs caros para fintechs brasileiras em estágio Seed e Série A. Nasceu de um fork técnico do AiSOC, foi rebrandado, traduzido pro contexto BACEN, e endurecido para passar IN BCB 314 e Resolução BCB 85/2021 sem time de 12 pessoas.
              </p>
              <p>
                Outros produtos do portfólio (PayJarvis, Luna, Osprey, SOMA-ID) seguem a mesma tese: infra cara virou commodity barata quando você não carrega o legado.
              </p>
            </div>
          </div>

          <div className="lg:col-span-5">
            <dl className="grid grid-cols-1 gap-px overflow-hidden rounded-lg border border-surface-border bg-surface-border">
              {stats.map((s) => (
                <div key={s.label} className="bg-surface-base p-6">
                  <dt className="text-4xl font-semibold tracking-tight text-fg-primary sm:text-5xl">{s.num}</dt>
                  <dd className="mt-2 text-sm font-medium text-fg-primary">{s.label}</dd>
                  <dd className="text-sm text-fg-muted">{s.sub}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>
    </section>
  );
}

export function ProdutoQuarry() {
  const features = [
    { icon: Cpu, title: '4 agentes especializados', body: 'Detect, Triage, Hunt, Respond — cada um com gates de auto-consistência testados a cada PR.' },
    { icon: Shield, title: '69 conectores nativos', body: 'EDR, SIEM, cloud, IAM, SaaS, VCS, network. Schema OCSF normalizado. Cofre Fernet AES-128.' },
    { icon: FileCheck2, title: 'Air-gap num único flag', body: 'QUARRY_AIRGAPPED=true desliga toda chamada externa. Ollama local roda no cluster.' },
  ];

  return (
    <section id="produto" className="relative border-t border-surface-border py-20 sm:py-28">
      <div aria-hidden="true" className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand-500/40 to-transparent" />
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-brand-300">02 — O produto</p>
        <div className="mt-6 grid items-end gap-8 lg:grid-cols-2">
          <h2 className="text-3xl font-semibold leading-tight text-fg-primary sm:text-4xl">
            Quarry. Um SOC agêntico que <em className="font-medium text-brand-300 not-italic">cabe no caixa</em> de uma fintech Seed.
          </h2>
          <p className="text-base leading-relaxed text-fg-secondary sm:text-lg">
            Quatro agentes de IA cuidam de detecção, triagem, hunt e resposta. Sessenta e nove conectores ligam suas fontes em minutos. Um benchmark público de 200 incidentes mostra o que ele acerta e o que ele erra. Tudo MIT, hospedável em qualquer Docker.
          </p>
        </div>

        <ul className="mt-14 grid gap-px overflow-hidden rounded-xl border border-surface-border bg-surface-border sm:grid-cols-3">
          {features.map((f) => (
            <li key={f.title} className="bg-surface-base p-6 sm:p-8">
              <f.icon className="h-6 w-6 text-brand-300" aria-hidden="true" />
              <h3 className="mt-4 text-base font-semibold text-fg-primary">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-fg-secondary">{f.body}</p>
            </li>
          ))}
        </ul>

        <div className="mt-10">
          <Link href="/opensource" className="group inline-flex items-center gap-2 text-sm font-medium text-brand-300 hover:text-brand-300/80">
            Documentação técnica completa, license MIT, GitHub
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </section>
  );
}

export function ParaQuemE() {
  const personas = [
    {
      head: 'Fintech Seed/Série A no Brasil',
      body: 'Você tem 18-60 colaboradores, processa Pix, e precisa passar IN BCB 314 e Res. BCB 85/2021 sem contratar SOC enterprise. O Quarry foi feito pra esse caso.',
      cta: { label: 'Ver landing fintech BR', href: '/br' },
    },
    {
      head: 'Time de engenharia enxuto global',
      body: 'Cinco devs, infra no AWS/GCP, sem time de segurança dedicado. Quer self-host MIT, sem vendor lock-in, com benchmark público e código auditável.',
      cta: { label: 'Documentação OSS', href: '/opensource' },
    },
    {
      head: 'Quem cansou de MSSP',
      body: 'Você paga R$ 20-40 mil/mês pra um MSSP que manda PDF mensal, demora 2 dias pra responder incidente, e nunca tem evidência arquivada quando o BACEN pede.',
      cta: { label: 'Comparativo de custo', href: '#stat' },
    },
  ];

  return (
    <section id="para-quem" className="relative border-t border-surface-border py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-brand-300">03 — Para quem é</p>
        <h2 className="mt-6 max-w-3xl text-3xl font-semibold leading-tight text-fg-primary sm:text-4xl">
          Três perfis. O mesmo problema: <em className="font-medium text-brand-300 not-italic">segurança regulada custa caro demais</em>.
        </h2>

        <div className="mt-14 grid gap-6 lg:grid-cols-3">
          {personas.map((p) => (
            <article key={p.head} className="group relative flex flex-col rounded-xl border border-surface-border bg-surface-raised/40 p-6 transition-colors hover:border-brand-500/40 sm:p-7">
              <h3 className="text-lg font-semibold text-fg-primary">{p.head}</h3>
              <p className="mt-3 flex-1 text-sm leading-relaxed text-fg-secondary">{p.body}</p>
              <Link href={p.cta.href} className="mt-6 inline-flex items-center gap-1 text-sm font-medium text-brand-300 hover:text-brand-300/80">
                {p.cta.label}
                <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
              </Link>
            </article>
          ))}
        </div>

        <div className="mt-16 rounded-xl border border-surface-border bg-surface-raised/30 p-6 sm:p-8">
          <p className="text-xs font-medium uppercase tracking-[0.22em] text-fg-muted">Para quem não é</p>
          <p className="mt-3 text-base leading-relaxed text-fg-secondary sm:text-lg">
            Banco grande, big tech, governo, ou quem precisa de SOC com SLA contratual 24/7 com pessoas dedicadas. O Quarry assume que seu time é enxuto e a IA cobre o que pessoas custariam demais. Se você tem orçamento pra três turnos humanos, contrate um MSSP enterprise — não é o que entregamos.
          </p>
        </div>
      </div>
    </section>
  );
}

export function StatGigante() {
  return (
    <section id="stat" className="relative border-t border-surface-border py-24 sm:py-32">
      <div aria-hidden="true" className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand-500/40 to-transparent" />
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid items-center gap-12 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <p className="text-xs font-medium uppercase tracking-[0.22em] text-brand-300">04 — Em números</p>
            <p className="mt-6 text-[88px] font-semibold leading-none tracking-tight text-fg-primary sm:text-[120px] lg:text-[160px]">
              R$&nbsp;27,40
            </p>
            <p className="mt-4 text-base text-fg-secondary sm:text-lg">
              por alerta auditado, com cadeia probatória arquivada e relatório pronto pra BACEN.
            </p>
          </div>
          <div className="space-y-6 lg:col-span-5">
            <div className="rounded-lg border border-surface-border bg-surface-raised/40 p-6">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-fg-muted">Referência de mercado</p>
              <p className="mt-2 text-base text-fg-secondary">
                MSSP brasileiro típico para fintech Seed cobra entre R$&nbsp;18 mil e R$&nbsp;42 mil/mês, sem entregar evidência arquivada por incidente. Custo por alerta auditado varia de <strong className="text-fg-primary">R$&nbsp;180</strong> a <strong className="text-fg-primary">R$&nbsp;620</strong>.
              </p>
            </div>
            <div className="rounded-lg border border-brand-500/30 bg-brand-500/5 p-6">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-brand-300">Quarry self-host</p>
              <p className="mt-2 text-base text-fg-secondary">
                Mesmo trabalho, com infra própria + um agente humano part-time pra revisar. Cadeia probatória e timestamp de comunicação ao BACEN saem do produto, não de planilha.
              </p>
            </div>
            <p className="text-xs text-fg-muted">
              Benchmark interno, jan-abr 2026. Volume médio 240 alertas/mês em fintech Seed simulada. Inclui infra cloud + revisor humano. <Link href="/opensource#benchmark" className="underline decoration-fg-muted/40 underline-offset-2 hover:text-fg-secondary">Metodologia →</Link>
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export function CaminhoDuplo() {
  return (
    <section className="relative border-t border-surface-border py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-brand-300">05 — Por onde começar</p>
        <h2 className="mt-6 max-w-3xl text-3xl font-semibold leading-tight text-fg-primary sm:text-4xl">
          Dois caminhos. Sem fricção, sem reunião comercial.
        </h2>

        <div className="mt-14 grid gap-6 lg:grid-cols-2">
          <Link href="/br" className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-surface-border bg-surface-raised/40 p-8 transition-all hover:border-brand-500/40 hover:bg-surface-raised/60 sm:p-10">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-brand-300">Caminho A</p>
              <h3 className="mt-3 text-2xl font-semibold text-fg-primary sm:text-3xl">Sou fintech brasileira</h3>
              <p className="mt-4 text-sm leading-relaxed text-fg-secondary sm:text-base">
                Checklist BACEN 85, comparativo de custo MSSP, casos de Pix com cadeia probatória. Landing dedicada com a tese econômica completa.
              </p>
            </div>
            <span className="mt-8 inline-flex items-center gap-2 text-sm font-medium text-brand-300 group-hover:text-brand-300/80">
              Abrir landing fintechs BR
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
            </span>
          </Link>

          <Link href="/opensource" className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-surface-border bg-surface-raised/40 p-8 transition-all hover:border-brand-500/40 hover:bg-surface-raised/60 sm:p-10">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-brand-300">Caminho B</p>
              <h3 className="mt-3 text-2xl font-semibold text-fg-primary sm:text-3xl">Quero auto-hospedar</h3>
              <p className="mt-4 text-sm leading-relaxed text-fg-secondary sm:text-base">
                Documentação técnica completa, license MIT, 69 conectores, benchmark de 200 incidentes, deploy em Docker/Render/Fly/Helm. Sem cadastro.
              </p>
            </div>
            <span className="mt-8 inline-flex items-center gap-2 text-sm font-medium text-brand-300 group-hover:text-brand-300/80">
              Abrir documentação OSS
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
            </span>
          </Link>
        </div>
      </div>
    </section>
  );
}

export function DemoBanner() {
  return (
    <section className="relative border-t border-surface-border py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-2xl border border-surface-border bg-gradient-to-br from-surface-raised/60 via-surface-raised/30 to-brand-500/5 p-8 sm:p-12">
          <div aria-hidden="true" className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-brand-500/10 blur-3xl" />
          <p className="text-xs font-medium uppercase tracking-[0.22em] text-brand-300">06 — Ver funcionando</p>
          <div className="mt-6 grid items-end gap-8 lg:grid-cols-2">
            <div>
              <h2 className="text-3xl font-semibold leading-tight text-fg-primary sm:text-4xl">
                Demo cinematográfica: fraude em Pix detectada, contida e <em className="font-medium text-brand-300 not-italic">documentada</em> em 4 minutos.
              </h2>
              <p className="mt-4 max-w-xl text-base leading-relaxed text-fg-secondary sm:text-lg">
                Cenário sintético, dados reais de mercado. Mostra o overlay regulatório Bacen ao vivo: Res. BCB 85 Art. 3/4/8/9, IN BCB 314, e LGPD Art. 48/50 sendo acionados em tempo real.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3 lg:justify-end">
              <Link href="/demo-cinematografica" className="group inline-flex items-center gap-2 rounded-md bg-gradient-to-br from-brand-500 to-brand-700 px-6 py-3 text-sm font-semibold text-white shadow-[0_1px_0_rgba(255,255,255,0.18)_inset] transition-shadow hover:shadow-[0_8px_24px_-8px_rgba(59,130,246,0.55)]">
                Abrir demo →
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

const FAQ_ITEMS = [
  {
    q: 'O Quarry é gratuito?',
    a: 'O produto é MIT-licensed e self-hostable sem cobrança. Você cobre infra (cloud + LLM provider). Quem prefere não operar pode entrar na lista de espera do tier gerenciado pela 12Brain — anúncio em 2026.',
  },
  {
    q: 'Roda no meu cloud, ou só no de vocês?',
    a: 'Roda onde você quiser: AWS, GCP, Azure, on-prem, Docker num laptop. Air-gap completo num único flag. A 12Brain não toca nos seus dados em deploy self-host.',
  },
  {
    q: 'Quem mantém o código?',
    a: 'A 12Brain Solutions LLC mantém o fork principal. Repositório principal: github.com/beenuar/Quarry. Roadmap público, RFC processado em issues, releases tagueadas semanalmente.',
  },
  {
    q: 'E se a 12Brain sumir?',
    a: 'O código continua MIT. Você forka, contrata qualquer dev de Python pra manter, e segue. Não há SaaS proprietário, não há lock-in de dados, não há feature por trás de paywall.',
  },
  {
    q: 'Como entro em contato comercial?',
    a: 'Resposta abaixo, no formulário. Não temos call centre. Toda conversa comercial começa por e-mail ou GitHub Discussion — escala melhor pra time enxuto e pra você.',
  },
];

export function FaqHome() {
  return (
    <section id="faq" className="relative border-t border-surface-border py-20 sm:py-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-brand-300">07 — Perguntas comerciais</p>
        <h2 className="mt-6 max-w-3xl text-3xl font-semibold leading-tight text-fg-primary sm:text-4xl">
          O que decide compra. Sem rodeio.
        </h2>

        <dl className="mt-12 divide-y divide-surface-border border-y border-surface-border">
          {FAQ_ITEMS.map((item) => (
            <details key={item.q} className="group py-6">
              <summary className="flex cursor-pointer items-center justify-between gap-6 text-base font-medium text-fg-primary marker:hidden [&::-webkit-details-marker]:hidden sm:text-lg">
                <span>{item.q}</span>
                <span aria-hidden="true" className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-surface-border text-fg-muted transition-transform group-open:rotate-45">
                  +
                </span>
              </summary>
              <p className="mt-4 max-w-3xl text-sm leading-relaxed text-fg-secondary sm:text-base">{item.a}</p>
            </details>
          ))}
        </dl>
      </div>
    </section>
  );
}

export function FooterHome() {
  return (
    <footer id="contato" className="relative border-t border-surface-border bg-surface-raised/30 py-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <div className="flex items-center gap-2">
              <span aria-hidden="true" className="inline-flex h-9 w-9 items-center justify-center rounded-md bg-gradient-to-br from-brand-400 to-brand-700 text-[11px] font-bold text-white shadow-[inset_0_0_0_1px_rgba(255,255,255,0.18)]">
                12B
              </span>
              <p className="text-base font-semibold tracking-tight text-fg-primary">12Brain Solutions LLC</p>
            </div>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-fg-secondary">
              Coconut Creek, Flórida — EUA. Operação enxuta, produto na frente, regulação no centro. O Quarry é o produto principal; o resto do portfólio compartilha a mesma tese.
            </p>
            <a href="mailto:contato@12brain.org" className="mt-6 inline-flex items-center gap-2 rounded-md border border-surface-border bg-surface-base/60 px-4 py-2.5 text-sm font-medium text-fg-primary hover:border-brand-500/40">
              <Mail className="h-3.5 w-3.5" aria-hidden="true" />
              contato@12brain.org
            </a>
          </div>

          <div className="grid grid-cols-2 gap-8 sm:grid-cols-3 lg:col-span-7">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-fg-muted">Quarry</p>
              <ul className="mt-4 space-y-2 text-sm text-fg-secondary">
                <li><Link href="#produto" className="hover:text-fg-primary">O produto</Link></li>
                <li><Link href="/br" className="hover:text-fg-primary">Fintechs BR</Link></li>
                <li><Link href="/opensource" className="hover:text-fg-primary">Open-source</Link></li>
                <li><Link href="/demo-cinematografica" className="hover:text-fg-primary">Demo Pix</Link></li>
              </ul>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-fg-muted">Empresa</p>
              <ul className="mt-4 space-y-2 text-sm text-fg-secondary">
                <li><Link href="#empresa" className="hover:text-fg-primary">Sobre a 12Brain</Link></li>
                <li><Link href="#faq" className="hover:text-fg-primary">Perguntas</Link></li>
                <li><a href="mailto:contato@12brain.org" className="hover:text-fg-primary">Contato</a></li>
              </ul>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-fg-muted">Código</p>
              <ul className="mt-4 space-y-2 text-sm text-fg-secondary">
                <li><a href="https://github.com/beenuar/Quarry" target="_blank" rel="noreferrer" className="hover:text-fg-primary">GitHub</a></li>
                <li><a href="https://github.com/beenuar/Quarry/releases" target="_blank" rel="noreferrer" className="hover:text-fg-primary">Releases</a></li>
                <li><Link href="/opensource#benchmark" className="hover:text-fg-primary">Benchmark</Link></li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-14 flex flex-wrap items-center justify-between gap-3 border-t border-surface-border pt-6 text-xs text-fg-muted">
          <p>© {new Date().getFullYear()} 12Brain Solutions LLC. Todos os direitos reservados.</p>
          <p>Quarry é MIT-licensed. Marca registrada da 12Brain Solutions LLC.</p>
        </div>
      </div>
    </footer>
  );
}
