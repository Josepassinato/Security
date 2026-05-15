'use client';

/**
 * "What makes Quarry different" — `pillars` section from §6.6 of the
 * brief. Four differentiation cards in a 2×2 grid above `md`, single
 * column below.
 *
 * Each card composes two Aceternity primitives:
 *   - `GlowingEffect` paints a soft conic halo that tracks the pointer
 *     when the card is hovered or focused.
 *   - `CardHoverEffect` swaps to a brand-tinted overlay on the same
 *     pointer event so the card reads as "active" without redrawing
 *     its body.
 *
 * Each card carries a stat strip (e.g. "6,998 public detection rules")
 * with `tnum`-enabled mono digits and a single CTA link that opens the
 * corresponding repo file.
 */

import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, GitGraph, ScrollText, Sparkles, Boxes } from 'lucide-react';
import type { ComponentType, SVGProps } from 'react';
import { GlowingEffect } from '@/components/aceternity/GlowingEffect';
import { cn } from '@/lib/utils';

interface Pillar {
  id: 'open-source' | 'graph-native' | 'agentic' | 'deploy';
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  title: string;
  body: string;
  stat: string;
  statLabel: string;
  href: string;
  linkLabel: string;
}

const PILLARS: ReadonlyArray<Pillar> = [
  {
    id: 'open-source',
    icon: ScrollText,
    title: 'Open source and transparent',
    body:
      'MIT-licensed agent, public detection corpus, reproducible benchmark — every claim on this page maps to a file in the repo.',
    stat: '6,998',
    statLabel: 'public detection rules',
    href: 'https://github.com/beenuar/Quarry/blob/main/LICENSE',
    linkLabel: 'Read the LICENSE',
  },
  {
    id: 'graph-native',
    icon: GitGraph,
    title: 'Graph-native at ingest',
    body:
      'The entity graph is written while events are normalised, not when an analyst clicks "show graph." Schema v1.0 is published.',
    stat: '17 + 14',
    statLabel: 'node labels · relationships',
    href: 'https://docs.quarry.dev/architecture/graph-schema',
    linkLabel: 'Read the graph schema',
  },
  {
    id: 'agentic',
    icon: Sparkles,
    title: 'Agentic and auditable',
    body:
      'Four named agents. Every prompt, tool call, and decision is logged. The LLM-input contract fails closed on malformed prompts.',
    stat: '4 / 100%',
    statLabel: 'agents · audited',
    href: 'https://docs.quarry.dev/architecture/agents',
    linkLabel: 'Read the agent contract',
  },
  {
    id: 'deploy',
    icon: Boxes,
    title: 'Deploy anywhere',
    body:
      'Render, Fly.io, Kubernetes, AWS, your air-gapped rack — same code path. BYOK LLM credentials in the encrypted vault.',
    stat: '6 + 1',
    statLabel: 'deploy targets · air-gap overlay',
    href: 'https://docs.quarry.dev/deployment',
    linkLabel: 'Read the deployment guide',
  },
];

function PillarCard({
  pillar,
  index,
  reduced,
}: {
  pillar: Pillar;
  index: number;
  reduced: boolean | null;
}) {
  const Icon = pillar.icon;
  return (
    <motion.li
      initial={reduced ? false : { opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-15%' }}
      transition={{
        duration: 0.55,
        ease: [0.16, 1, 0.3, 1],
        delay: index * 0.07,
      }}
      className="group relative"
    >
      <div className="relative h-full overflow-hidden rounded-2xl border border-surface-border bg-surface-card/70 p-6 backdrop-blur-sm transition-shadow duration-300 ease-landing-out-quart hover:shadow-[0_24px_64px_-32px_rgba(59,130,246,0.4)]">
        <GlowingEffect proximity={120} inactiveZone={0.35} />
        <div className="relative flex items-start gap-4">
          <span
            aria-hidden="true"
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500/20 to-landing-accent-violet/20 text-brand-300 ring-1 ring-inset ring-brand-500/30"
          >
            <Icon className="h-5 w-5" />
          </span>
          <div className="min-w-0">
            <h3 className="text-base font-semibold tracking-tight text-fg-primary sm:text-lg">
              {pillar.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-fg-secondary">
              {pillar.body}
            </p>
          </div>
        </div>
        <hr className="my-5 border-surface-border" />
        <div className="relative flex flex-wrap items-end justify-between gap-3">
          <div>
            <p
              className={cn(
                'font-mono text-2xl font-semibold tracking-tight text-fg-primary tabular-nums',
                'sm:text-3xl',
              )}
            >
              {pillar.stat}
            </p>
            <p className="text-xs text-fg-muted">{pillar.statLabel}</p>
          </div>
          <Link
            href={pillar.href}
            className="group/link inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold text-brand-300 transition-colors duration-200 hover:text-brand-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base"
          >
            {pillar.linkLabel}
            <ArrowRight
              className="h-3 w-3 transition-transform duration-200 group-hover/link:translate-x-0.5 motion-reduce:transition-none motion-reduce:group-hover/link:translate-x-0"
              aria-hidden="true"
            />
          </Link>
        </div>
      </div>
    </motion.li>
  );
}

export function Pillars() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section
      id="pillars"
      aria-labelledby="pillars-heading"
      className="relative py-20 sm:py-24 lg:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-400">
            What makes Quarry different
          </p>
          <h2
            id="pillars-heading"
            className="mt-3 text-3xl font-bold tracking-tight text-fg-primary sm:text-4xl lg:text-[40px] lg:leading-[1.15] lg:tracking-[-0.015em]"
          >
            Four promises we hold ourselves to.
          </h2>
        </div>

        <ul className="mt-12 grid gap-4 sm:gap-6 md:grid-cols-2 lg:mt-16">
          {PILLARS.map((pillar, idx) => (
            <PillarCard
              key={pillar.id}
              pillar={pillar}
              index={idx}
              reduced={prefersReducedMotion}
            />
          ))}
        </ul>
      </div>
    </section>
  );
}
