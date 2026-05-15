'use client';

/**
 * "See it work" — `demo` section from §6.5 of the brief.
 *
 * Renders a stylised mock of the Investigation Ledger panel as it
 * appears in the console mid-investigation (INC-RT-001 / LockBit 3.0,
 * step 14 of 32). This is intentionally a mock — not a real Cytoscape
 * embed — so the section can be statically rendered, parses no JSON at
 * load, and adds zero JS to the landing route's First Load bundle.
 *
 * The actual live demo lives at `/dashboard` (per the existing
 * onboarding-first surface). When/if the buyer-facing tour wants the
 * real Cytoscape mount, swap this component for a `next/dynamic` lazy
 * import of `RealtimeGraph` gated behind an `IntersectionObserver`, per
 * §12 of the brief.
 *
 * Animation: ledger rows fade-in-up with 60 ms stagger when the panel
 * enters the viewport; the cursor blinks at 1 Hz on the active step
 * with a single CSS `step-end` animation; `BorderBeam` traces the
 * panel chrome on a 14 s loop. All three respect `prefers-reduced-motion`.
 */

import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, Clock, Cpu, Database } from 'lucide-react';
import { BorderBeam } from '@/components/magicui/BorderBeam';
import { cn } from '@/lib/utils';

interface LedgerStep {
  step: number;
  agent: 'Detect' | 'Triage' | 'Hunt' | 'Respond';
  action: string;
  result: string;
  state: 'complete' | 'active' | 'queued';
}

const STEPS: ReadonlyArray<LedgerStep> = [
  {
    step: 11,
    agent: 'Detect',
    action: 'fuse_signals(host=WS-RT-014)',
    result: '4 alerts → INC-RT-001',
    state: 'complete',
  },
  {
    step: 12,
    agent: 'Triage',
    action: 'classify(family="LockBit 3.0")',
    result: 'confidence 0.93',
    state: 'complete',
  },
  {
    step: 13,
    agent: 'Triage',
    action: 'enrich(user=oliver.tan, asset=WS-RT-014)',
    result: 'priv=admin · last login 03:21',
    state: 'complete',
  },
  {
    step: 14,
    agent: 'Hunt',
    action: 'kql("SecurityEvent EventID=4688 …")',
    result: '38 process events · 7 lateral',
    state: 'active',
  },
  {
    step: 15,
    agent: 'Respond',
    action: 'plan(containment, dry_run=true)',
    result: 'pending L2 approval',
    state: 'queued',
  },
];

const AGENT_COLOR: Record<LedgerStep['agent'], string> = {
  Detect: 'text-brand-300 bg-brand-500/10 ring-brand-500/30',
  Triage:
    'text-landing-accent-violet bg-landing-accent-violet/10 ring-landing-accent-violet/30',
  Hunt: 'text-brand-300 bg-brand-500/15 ring-brand-300/30',
  Respond:
    'text-landing-accent-ember bg-landing-accent-ember/10 ring-landing-accent-ember/30',
};

const STATE_DOT: Record<LedgerStep['state'], string> = {
  complete: 'bg-status-live',
  active: 'bg-brand-400 animate-pulse',
  queued: 'bg-status-idle',
};

export function DemoEmbed() {
  const prefersReducedMotion = useReducedMotion();
  const initial = prefersReducedMotion ? false : { opacity: 0, y: 12 };

  return (
    <section
      id="demo"
      aria-labelledby="demo-heading"
      className="relative py-20 sm:py-24 lg:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-400">
            See it work
          </p>
          <h2
            id="demo-heading"
            className="mt-3 text-3xl font-bold tracking-tight text-fg-primary sm:text-4xl lg:text-[40px] lg:leading-[1.15] lg:tracking-[-0.015em]"
          >
            Watch Quarry investigate a live ransomware incident.
          </h2>
          <p className="mt-4 text-base leading-relaxed text-fg-secondary sm:text-lg">
            INC-RT-001 is a LockBit 3.0 case that ships with every install.
            The ledger streams every prompt, tool call, and decision the
            agent made. Scrub the timeline, pause on any step, fork the
            rationale into a ticket.
          </p>
        </div>

        <motion.figure
          initial={initial}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-15%' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="relative mx-auto mt-12 max-w-5xl lg:mt-16"
        >
          <div className="relative overflow-hidden rounded-2xl border border-surface-border bg-surface-card/80 shadow-[0_30px_80px_-32px_rgba(15,23,42,0.8)] backdrop-blur-sm">
            <header className="flex items-center justify-between gap-3 border-b border-surface-border px-4 py-3 sm:px-6">
              <div className="flex items-center gap-2">
                <span
                  aria-hidden="true"
                  className="inline-flex h-2.5 w-2.5 rounded-full bg-severity-critical"
                />
                <span
                  aria-hidden="true"
                  className="inline-flex h-2.5 w-2.5 rounded-full bg-status-warn"
                />
                <span
                  aria-hidden="true"
                  className="inline-flex h-2.5 w-2.5 rounded-full bg-status-live"
                />
              </div>
              <p className="hidden text-xs font-mono text-fg-muted sm:block">
                quarry.dev/cases/INC-RT-001?tab=ledger
              </p>
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-fg-subtle">
                Live
              </p>
            </header>

            <div className="grid gap-0 md:grid-cols-[1fr_320px]">
              <div className="px-4 py-5 sm:px-6 sm:py-6">
                <div className="flex flex-wrap items-center gap-2 text-xs font-medium">
                  <span className="inline-flex items-center gap-2 rounded-full bg-severity-critical/10 px-2.5 py-1 text-severity-critical ring-1 ring-inset ring-severity-critical/30">
                    <span
                      aria-hidden="true"
                      className="inline-block h-1.5 w-1.5 rounded-full bg-severity-critical"
                    />
                    Critical
                  </span>
                  <span className="text-fg-muted">INC-RT-001</span>
                  <span className="text-fg-subtle">·</span>
                  <span className="text-fg-muted">LockBit 3.0</span>
                  <span className="text-fg-subtle">·</span>
                  <span className="text-fg-muted">step 14 of 32</span>
                </div>

                <ol className="mt-5 space-y-2 font-mono">
                  {STEPS.map((step, idx) => (
                    <motion.li
                      key={step.step}
                      initial={initial}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true, margin: '-15%' }}
                      transition={{
                        duration: 0.45,
                        ease: [0.16, 1, 0.3, 1],
                        delay: 0.15 + idx * 0.07,
                      }}
                      className={cn(
                        'flex items-start gap-3 rounded-lg px-3 py-2 text-[11.5px] leading-relaxed',
                        step.state === 'active' &&
                          'bg-brand-500/5 ring-1 ring-inset ring-brand-500/30',
                      )}
                    >
                      <span
                        aria-hidden="true"
                        className={cn(
                          'mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full',
                          STATE_DOT[step.state],
                        )}
                      />
                      <span className="w-8 shrink-0 text-fg-subtle">
                        #{step.step}
                      </span>
                      <span
                        className={cn(
                          'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] ring-1 ring-inset',
                          AGENT_COLOR[step.agent],
                        )}
                      >
                        {step.agent}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-fg-primary">
                          {step.action}
                          {step.state === 'active' && (
                            <span
                              aria-hidden="true"
                              className="ml-1 inline-block h-3 w-2 translate-y-0.5 bg-brand-400 motion-safe:animate-pulse motion-reduce:opacity-50"
                            />
                          )}
                        </p>
                        <p className="text-fg-muted">→ {step.result}</p>
                      </div>
                    </motion.li>
                  ))}
                </ol>
              </div>

              <aside className="border-t border-surface-border bg-surface-base/60 px-4 py-5 sm:px-6 sm:py-6 md:border-l md:border-t-0">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-fg-subtle">
                  Investigation summary
                </p>
                <dl className="mt-4 space-y-4 text-xs">
                  <div className="flex items-start gap-3">
                    <Clock
                      className="mt-0.5 h-3.5 w-3.5 text-brand-300"
                      aria-hidden="true"
                    />
                    <div>
                      <dt className="text-fg-subtle">Elapsed</dt>
                      <dd className="font-mono text-fg-primary">00:01:47</dd>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Cpu
                      className="mt-0.5 h-3.5 w-3.5 text-brand-300"
                      aria-hidden="true"
                    />
                    <div>
                      <dt className="text-fg-subtle">LLM spend</dt>
                      <dd className="font-mono text-fg-primary">$0.084</dd>
                      <dd className="text-fg-muted">claude-4-haiku · 14 calls</dd>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Database
                      className="mt-0.5 h-3.5 w-3.5 text-brand-300"
                      aria-hidden="true"
                    />
                    <div>
                      <dt className="text-fg-subtle">Touched</dt>
                      <dd className="font-mono text-fg-primary">4 hosts · 2 users</dd>
                      <dd className="text-fg-muted">38 process events</dd>
                    </div>
                  </div>
                </dl>
                <hr className="my-5 border-surface-border" />
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-fg-subtle">
                  Next planned action
                </p>
                <p className="mt-2 text-xs leading-relaxed text-fg-secondary">
                  Quarantine WS-RT-014 + force-rotate <span className="font-mono">oliver.tan</span> session.
                  L2 approval requested in <span className="font-mono">#soc-approvals</span>.
                </p>
              </aside>
            </div>
          </div>
          {!prefersReducedMotion && (
            <BorderBeam duration={14} size={220} colorFrom="#3b82f6" colorTo="#8b5cf6" />
          )}
          <figcaption className="sr-only">
            INC-RT-001 LockBit 3.0 investigation, paused on step 14 of 32 inside
            the Quarry ledger view.
          </figcaption>
        </motion.figure>

        <div className="mx-auto mt-10 flex max-w-3xl flex-col items-center justify-center gap-3 text-center sm:flex-row sm:gap-5">
          <Link
            href="https://github.com/beenuar/Quarry#5-minute-demo"
            className="group inline-flex h-11 items-center gap-2 rounded-md bg-gradient-to-br from-brand-500 to-brand-700 px-6 text-sm font-semibold text-white shadow-[0_1px_0_rgba(255,255,255,0.18)_inset] transition-shadow duration-200 ease-landing-out-quart hover:shadow-[0_12px_32px_-12px_rgba(59,130,246,0.65)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base"
          >
            Run this yourself in 5 minutes
            <ArrowRight
              className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5 motion-reduce:transition-none motion-reduce:group-hover:translate-x-0"
              aria-hidden="true"
            />
          </Link>
          <Link
            href="https://docs.quarry.dev/architecture"
            className="inline-flex items-center gap-1 text-sm font-medium text-fg-muted transition-colors duration-200 hover:text-fg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base"
          >
            Read the architecture
            <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </section>
  );
}
