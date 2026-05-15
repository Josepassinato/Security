'use client';

/**
 * "MIT all the way down" — `open-source` section from §6.11 of the brief.
 *
 * Single-column band split into two halves on `≥md`:
 *
 *   - Left: eyebrow + H2 + sub-head + primary/secondary CTAs.
 *   - Right: a "repo card" rendered as a stylised README header with a
 *     `BorderBeam` and a `bash` snippet underneath. Three commands —
 *     the same `git clone … pnpm quarry:demo` shorthand the
 *     `landing-page-content.md` doc specifies.
 *
 * No live GitHub API call for the star count; it is intentionally
 * static here. A follow-up workflow will fill in the real value from
 * `github.repos.get`.
 */

import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, GitBranch, Star, Terminal } from 'lucide-react';
import { BorderBeam } from '@/components/magicui/BorderBeam';
import { GithubMark } from './icons';

const REPO_URL = 'https://github.com/beenuar/Quarry';
const CONTRIBUTING_URL = 'https://github.com/beenuar/Quarry/blob/main/CONTRIBUTING.md';
const SNIPPET = `git clone https://github.com/beenuar/Quarry.git
cd Quarry
pnpm quarry:demo`;

export function OpenSourceMoment() {
  const prefersReducedMotion = useReducedMotion();
  const fadeIn = (delay = 0) =>
    prefersReducedMotion
      ? false
      : ({
          initial: { opacity: 0, y: 16 },
          whileInView: { opacity: 1, y: 0 },
          viewport: { once: true, margin: '-15%' as const },
          transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1], delay },
        } as const);

  return (
    <section
      id="open-source"
      aria-labelledby="open-source-heading"
      className="relative py-20 sm:py-24 lg:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid items-center gap-12 lg:grid-cols-[1.05fr_1fr] lg:gap-16">
          <motion.div {...(fadeIn(0) || {})}>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-400">
              MIT all the way down
            </p>
            <h2
              id="open-source-heading"
              className="mt-3 text-3xl font-bold tracking-tight text-fg-primary sm:text-4xl lg:text-[40px] lg:leading-[1.15] lg:tracking-[-0.015em]"
            >
              Every detection rule public. Every benchmark reproducible.
            </h2>
            <p className="mt-4 max-w-xl text-base leading-relaxed text-fg-secondary">
              Fork the agent, fork the rules, fork the harness. We measure
              ourselves on the same metrics we publish, and we ship the
              dataset that produced them. There is no private fork.
            </p>
            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Link
                href={REPO_URL}
                rel="noreferrer"
                target="_blank"
                className="group inline-flex h-10 items-center gap-2 rounded-md bg-gradient-to-br from-brand-500 to-brand-700 px-4 text-sm font-semibold text-white shadow-[0_1px_0_rgba(255,255,255,0.18)_inset] transition-shadow duration-200 ease-landing-out-quart hover:shadow-[0_12px_32px_-12px_rgba(59,130,246,0.65)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base"
              >
                <Star className="h-4 w-4" aria-hidden="true" />
                Star on GitHub
                <ArrowRight
                  className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5 motion-reduce:transition-none motion-reduce:group-hover:translate-x-0"
                  aria-hidden="true"
                />
              </Link>
              <Link
                href={CONTRIBUTING_URL}
                rel="noreferrer"
                target="_blank"
                className="inline-flex h-10 items-center gap-2 rounded-md border border-surface-border bg-surface-raised/60 px-4 text-sm font-semibold text-fg-primary transition-colors duration-200 hover:border-brand-500/40 hover:text-brand-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base"
              >
                <GitBranch className="h-4 w-4" aria-hidden="true" />
                Read CONTRIBUTING.md
              </Link>
            </div>
          </motion.div>

          <motion.div {...(fadeIn(0.12) || {})} className="relative">
            <div className="relative overflow-hidden rounded-2xl border border-surface-border bg-surface-card/80 backdrop-blur-sm">
              <BorderBeam size={160} duration={14} colorFrom="#3b82f6" colorTo="#8b5cf6" />
              <div className="flex items-center gap-2 border-b border-surface-border bg-surface-raised/70 px-4 py-3 text-xs text-fg-muted">
                <span className="flex gap-1.5" aria-hidden="true">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/70" />
                </span>
                <span className="ml-2 font-mono">github.com/beenuar/Quarry</span>
              </div>
              <div className="space-y-4 p-6">
                <div className="flex items-start gap-3">
                  <span
                    aria-hidden="true"
                    className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-fg-primary/10 text-fg-primary"
                  >
                    <GithubMark className="h-5 w-5" />
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-fg-primary">
                      beenuar / Quarry
                    </p>
                    <p className="text-xs text-fg-muted">
                      <span aria-label="GitHub stars">★ 2.3k</span> · MIT · TypeScript / Python / Go
                    </p>
                  </div>
                </div>
                <p className="text-sm leading-relaxed text-fg-secondary">
                  Clone, demo, and inspect a live case in three commands:
                </p>
                <pre className="overflow-x-auto rounded-lg border border-surface-border bg-surface-raised/60 p-4 text-xs leading-relaxed text-fg-secondary">
                  <code className="block whitespace-pre font-mono">
                    <span className="select-none text-fg-muted">$ </span>
                    <span className="text-brand-300">git clone</span>{' '}
                    <span className="text-fg-primary">https://github.com/beenuar/Quarry.git</span>
                    {'\n'}
                    <span className="select-none text-fg-muted">$ </span>
                    <span className="text-brand-300">cd</span>{' '}
                    <span className="text-fg-primary">Quarry</span>
                    {'\n'}
                    <span className="select-none text-fg-muted">$ </span>
                    <span className="text-brand-300">pnpm</span>{' '}
                    <span className="text-fg-primary">quarry:demo</span>
                  </code>
                </pre>
                <div className="flex items-center gap-2 text-xs text-fg-muted">
                  <Terminal className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Boots a pre-seeded case in under a minute.</span>
                </div>
                {/* Hidden plaintext copy for screen readers / clipboard tools */}
                <span className="sr-only">{SNIPPET}</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
