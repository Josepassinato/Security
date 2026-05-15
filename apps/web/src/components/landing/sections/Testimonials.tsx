'use client';

/**
 * "From the people running it" — `testimonials` section from §6.12 of
 * the brief.
 *
 * Empty-state surface: there are no published case studies yet, so we
 * ship the honest version rather than fabricated quotes. Per the
 * content doc, once `apps/web/content/customers/*.mdx` has at least
 * two real studies the carousel below replaces this block — but
 * unverified social proof is worse than no social proof.
 *
 *   - Eyebrow + H2 from the content doc.
 *   - Centered card: H3 ("Be the first reference team."), body,
 *     CTA ("Become a reference partner").
 *   - Decorative `Meteors` layer behind the card adds gentle motion
 *     without implying a non-existent customer base.
 */

import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, ShieldCheck } from 'lucide-react';
import { Meteors } from '@/components/magicui/Meteors';

export function Testimonials() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section
      id="testimonials"
      aria-labelledby="testimonials-heading"
      className="relative py-20 sm:py-24 lg:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-400">
            From the people running it
          </p>
          <h2
            id="testimonials-heading"
            className="mt-3 text-3xl font-bold tracking-tight text-fg-primary sm:text-4xl lg:text-[40px] lg:leading-[1.15] lg:tracking-[-0.015em]"
          >
            What teams say after their first month.
          </h2>
        </div>

        <motion.div
          initial={prefersReducedMotion ? false : { opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-15%' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="relative mx-auto mt-12 max-w-2xl overflow-hidden rounded-2xl border border-surface-border bg-surface-card/80 p-8 backdrop-blur-sm sm:p-10 lg:mt-16"
        >
          {!prefersReducedMotion && (
            <Meteors number={14} className="opacity-50" />
          )}
          <div className="relative flex flex-col items-center text-center">
            <span
              aria-hidden="true"
              className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500/20 to-landing-accent-violet/20 text-brand-300 ring-1 ring-inset ring-brand-500/30"
            >
              <ShieldCheck className="h-6 w-6" />
            </span>
            <h3 className="mt-5 text-xl font-bold text-fg-primary sm:text-2xl">
              Be the first reference team.
            </h3>
            <p className="mt-3 max-w-xl text-base leading-relaxed text-fg-secondary">
              We are onboarding reference partners through Q2 2026. If your
              team ships AiSOC into production, we will publish your case
              study under your byline, with the before/after metrics you
              choose.
            </p>
            <Link
              href="/partners"
              className="group mt-6 inline-flex h-10 items-center gap-2 rounded-md bg-gradient-to-br from-brand-500 to-brand-700 px-4 text-sm font-semibold text-white shadow-[0_1px_0_rgba(255,255,255,0.18)_inset] transition-shadow duration-200 ease-landing-out-quart hover:shadow-[0_12px_32px_-12px_rgba(59,130,246,0.65)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base"
            >
              Become a reference partner
              <ArrowRight
                className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5 motion-reduce:transition-none motion-reduce:group-hover:translate-x-0"
                aria-hidden="true"
              />
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
