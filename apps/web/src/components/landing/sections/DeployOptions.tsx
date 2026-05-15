'use client';

/**
 * "Run AiSOC where your data is allowed to live" — `deploy` section
 * from §6.10 of the brief.
 *
 * Three deploy-path cards in a 3-up grid (single column below `md`).
 *
 *   1. Managed (waitlist) — host on app.aisoc.dev.
 *   2. Self-host (recommended) — Render / Docker / Fly.io / Helm /
 *      AWS Terraform. The middle card is highlighted via `ShineBorder`.
 *   3. Sovereign / air-gap — `AISOC_AIRGAPPED=true`, Ollama sidecar.
 *
 * Each card exposes the same four-line stat strip (Time to live / LLM /
 * Residency / Body) so a buyer can scan horizontally without
 * re-orienting per card.
 */

import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, Cloud, Lock, Server } from 'lucide-react';
import type { ComponentType, SVGProps } from 'react';
import { ShineBorder } from '@/components/magicui/ShineBorder';
import { cn } from '@/lib/utils';

interface DeployOption {
  id: 'managed' | 'self-host' | 'sovereign';
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  title: string;
  recommended?: boolean;
  timeToLive: string;
  llm: string;
  residency: string;
  body: string;
  cta: { label: string; href: string };
}

const OPTIONS: ReadonlyArray<DeployOption> = [
  {
    id: 'managed',
    icon: Cloud,
    title: 'Managed',
    timeToLive: 'Same day — once seats open',
    llm: 'Cloud APIs · BYO endpoint',
    residency: 'EU · US · India',
    body:
      'We host it. You log in. SOC 2 and GDPR are on the roadmap. Join the waitlist for early access.',
    cta: { label: 'Join the waitlist', href: '/waitlist' },
  },
  {
    id: 'self-host',
    icon: Server,
    title: 'Self-host',
    recommended: true,
    timeToLive: 'Five minutes (warm Docker)',
    llm: 'Cloud APIs · local Ollama · BYO',
    residency: 'Operator-defined',
    body:
      'Render one-click, Docker Compose, Fly.io, Helm, AWS Terraform — pick any. The slim demo stack ships pre-seeded with a LockBit case mid-investigation.',
    cta: { label: 'Self-host on GitHub', href: 'https://github.com/beenuar/AiSOC' },
  },
  {
    id: 'sovereign',
    icon: Lock,
    title: 'Sovereign / air-gap',
    timeToLive: 'An afternoon',
    llm: 'Local Ollama · BYO LiteLLM',
    residency: 'Operator-defined',
    body:
      'Set AISOC_AIRGAPPED=true and the platform refuses every outbound call. The Ollama sidecar ships a pinned local model so the demo seed runs end-to-end with zero external calls.',
    cta: { label: 'Read the air-gap guide', href: '/sovereign' },
  },
];

function OptionCard({
  option,
  index,
  reduced,
}: {
  option: DeployOption;
  index: number;
  reduced: boolean | null;
}) {
  const Icon = option.icon;
  return (
    <motion.li
      initial={reduced ? false : { opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-15%' }}
      transition={{
        duration: 0.55,
        ease: [0.16, 1, 0.3, 1],
        delay: index * 0.08,
      }}
      className={cn(
        'relative flex flex-col gap-4 rounded-2xl border border-surface-border bg-surface-card/70 p-6 backdrop-blur-sm',
        option.recommended &&
          'shadow-[0_24px_64px_-24px_rgba(59,130,246,0.45)]',
      )}
    >
      {option.recommended && <ShineBorder duration={14} borderWidth={1} />}
      <div className="relative flex items-center justify-between gap-3">
        <span
          aria-hidden="true"
          className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500/20 to-landing-accent-violet/20 text-brand-300 ring-1 ring-inset ring-brand-500/30"
        >
          <Icon className="h-5 w-5" />
        </span>
        {option.recommended && (
          <span className="inline-flex items-center rounded-full bg-brand-500/15 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-brand-300 ring-1 ring-inset ring-brand-500/40">
            Recommended
          </span>
        )}
      </div>
      <h3 className="relative text-xl font-bold tracking-tight text-fg-primary">
        {option.title}
      </h3>
      <dl className="relative space-y-2 text-xs">
        <div className="flex items-baseline justify-between gap-2 border-b border-surface-border pb-2">
          <dt className="font-semibold uppercase tracking-[0.12em] text-fg-subtle">
            Time to live
          </dt>
          <dd className="text-right text-fg-primary">{option.timeToLive}</dd>
        </div>
        <div className="flex items-baseline justify-between gap-2 border-b border-surface-border pb-2">
          <dt className="font-semibold uppercase tracking-[0.12em] text-fg-subtle">
            LLM
          </dt>
          <dd className="text-right text-fg-primary">{option.llm}</dd>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <dt className="font-semibold uppercase tracking-[0.12em] text-fg-subtle">
            Residency
          </dt>
          <dd className="text-right text-fg-primary">{option.residency}</dd>
        </div>
      </dl>
      <p className="relative text-sm leading-relaxed text-fg-secondary">
        {option.body}
      </p>
      <Link
        href={option.cta.href}
        className={cn(
          'group relative mt-auto inline-flex h-10 items-center justify-center gap-1 rounded-md px-4 text-sm font-semibold transition-shadow duration-200 ease-landing-out-quart focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base',
          option.recommended
            ? 'bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-[0_1px_0_rgba(255,255,255,0.18)_inset] hover:shadow-[0_12px_32px_-12px_rgba(59,130,246,0.65)]'
            : 'border border-surface-border bg-surface-raised/60 text-fg-primary hover:border-brand-500/40',
        )}
      >
        {option.cta.label}
        <ArrowRight
          className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5 motion-reduce:transition-none motion-reduce:group-hover:translate-x-0"
          aria-hidden="true"
        />
      </Link>
    </motion.li>
  );
}

export function DeployOptions() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section
      id="deploy"
      aria-labelledby="deploy-heading"
      className="relative py-20 sm:py-24 lg:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-400">
            Run AiSOC where your data is allowed to live
          </p>
          <h2
            id="deploy-heading"
            className="mt-3 text-3xl font-bold tracking-tight text-fg-primary sm:text-4xl lg:text-[40px] lg:leading-[1.15] lg:tracking-[-0.015em]"
          >
            Three deploy paths. Same code.
          </h2>
        </div>

        <ul className="mt-12 grid gap-4 sm:gap-6 md:grid-cols-3 lg:mt-16 lg:gap-8">
          {OPTIONS.map((option, idx) => (
            <OptionCard
              key={option.id}
              option={option}
              index={idx}
              reduced={prefersReducedMotion}
            />
          ))}
        </ul>
      </div>
    </section>
  );
}
