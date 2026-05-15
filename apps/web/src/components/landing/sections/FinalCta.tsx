'use client';

/**
 * "Ship the SOC you wish you had." — `final-cta` section from §6.15.
 *
 * Closing CTA band over the `landing-grad-cta` gradient with a
 * `BackgroundBeams` mesh on top. Two CTAs (Try managed / Self-host on
 * GitHub) plus the microcopy from the content doc.
 */

import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { BackgroundBeams } from '@/components/aceternity/BackgroundBeams';
import { GithubMark } from './icons';

export function FinalCta() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section
      id="cta"
      aria-labelledby="cta-heading"
      className="relative isolate overflow-hidden py-24 sm:py-28 lg:py-32"
    >
      <div className="absolute inset-0 -z-10 bg-landing-grad-cta opacity-[0.18]" aria-hidden="true" />
      <div className="absolute inset-0 -z-10" aria-hidden="true">
        <BackgroundBeams />
      </div>

      <div className="mx-auto max-w-3xl px-4 text-center sm:px-6 lg:px-8">
        <motion.h2
          id="cta-heading"
          initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-15%' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="text-4xl font-bold tracking-tight text-fg-primary sm:text-5xl lg:text-[56px] lg:leading-[1.05] lg:tracking-[-0.02em]"
        >
          Ship the SOC you wish you had.
        </motion.h2>
        <motion.p
          initial={prefersReducedMotion ? false : { opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-15%' }}
          transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1], delay: 0.08 }}
          className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-fg-secondary sm:text-lg"
        >
          Either path lands you on a working SOC, not a blank dashboard.
        </motion.p>
        <motion.div
          initial={prefersReducedMotion ? false : { opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-15%' }}
          transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1], delay: 0.16 }}
          className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4"
        >
          <Link
            href="/waitlist"
            className="group inline-flex h-11 items-center justify-center gap-2 rounded-md bg-gradient-to-br from-brand-500 to-brand-700 px-6 text-sm font-semibold text-white shadow-[0_1px_0_rgba(255,255,255,0.18)_inset] transition-shadow duration-200 ease-landing-out-quart hover:shadow-[0_18px_44px_-12px_rgba(59,130,246,0.65)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base"
          >
            Try managed
            <ArrowRight
              className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5 motion-reduce:transition-none motion-reduce:group-hover:translate-x-0"
              aria-hidden="true"
            />
          </Link>
          <Link
            href="https://github.com/beenuar/AiSOC"
            rel="noreferrer"
            target="_blank"
            className="inline-flex h-11 items-center justify-center gap-2 rounded-md border border-surface-border bg-surface-card/80 px-6 text-sm font-semibold text-fg-primary backdrop-blur-sm transition-colors duration-200 hover:border-brand-500/40 hover:text-brand-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base"
          >
            <GithubMark className="h-4 w-4" />
            Self-host on GitHub
          </Link>
        </motion.div>
        <p className="mt-6 text-xs text-fg-muted">
          MIT-licensed · No credit card · Air-gap on a flag
        </p>
      </div>
    </section>
  );
}
