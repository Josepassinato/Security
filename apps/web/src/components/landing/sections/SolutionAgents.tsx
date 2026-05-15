'use client';

/**
 * "Four agents, one workflow" — `solution` section from §6.4 of the
 * brief. The most animation-heavy piece on the page; everything in it
 * is built to flatten gracefully under `prefers-reduced-motion`.
 *
 * Layout (desktop ≥ 1024 px):
 *
 *   ┌────────┐    ┌────────┐    ┌────────┐    ┌─────────┐
 *   │ Detect │ →  │ Triage │ →  │  Hunt  │ →  │ Respond │
 *   └────────┘    └────────┘    └────────┘    └─────────┘
 *
 * The arrows are three `AnimatedBeam` instances anchored on real DOM
 * refs (the card edges) so the curve auto-recomputes on resize. Each
 * beam fires a brand-tinted comet on a 3 s loop with a 700 ms phase
 * shift so the four-agent narrative reads as a *pipeline*, not four
 * independent boxes.
 *
 * Mobile (< 1024 px): cards stack vertically and the beams are
 * suppressed (the comet only renders when the layout is horizontal —
 * the curvature math doesn't translate cleanly to a column layout).
 */

import { motion, useReducedMotion } from 'framer-motion';
import { ScanSearch, Sparkles, Telescope, ShieldCheck } from 'lucide-react';
import {
  type ComponentType,
  type SVGProps,
  useRef,
  useState,
  useEffect,
} from 'react';
import { AnimatedBeam } from '@/components/magicui/AnimatedBeam';
import { cn } from '@/lib/utils';

interface Agent {
  id: 'detect' | 'triage' | 'hunt' | 'respond';
  label: string;
  job: string;
  capabilities: string;
  runsOn: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  accent: string;
}

const AGENTS: ReadonlyArray<Agent> = [
  {
    id: 'detect',
    label: 'Detect',
    job: 'Fuse raw signals into incidents.',
    capabilities: 'fusion · entity-risk (RBA) · native detections',
    runsOn: 'Deterministic · no LLM required',
    icon: ScanSearch,
    accent: 'from-brand-400/20 to-brand-700/20 ring-brand-400/30 text-brand-200',
  },
  {
    id: 'triage',
    label: 'Triage',
    job: 'Decide what matters and how urgent.',
    capabilities:
      'LLM auto-triage · phishing · identity · cloud · insider',
    runsOn: 'OpenAI · Anthropic · Azure · Bedrock · Ollama · BYO endpoint',
    icon: Sparkles,
    accent:
      'from-landing-accent-violet/20 to-brand-500/20 ring-landing-accent-violet/30 text-landing-accent-violet',
  },
  {
    id: 'hunt',
    label: 'Hunt',
    job: 'Ask new questions across the data.',
    capabilities: 'NL → ES|QL · KQL · SPL · scheduled YAML hunts',
    runsOn: 'Cloud LLM or local model',
    icon: Telescope,
    accent:
      'from-brand-500/20 to-brand-300/20 ring-brand-300/30 text-brand-300',
  },
  {
    id: 'respond',
    label: 'Respond',
    job: 'Plan containment, gate execution, approve via ChatOps.',
    capabilities: 'response planner · SOAR exec · approvals',
    runsOn: 'L0–L4 maturity dial, dry-run by default',
    icon: ShieldCheck,
    accent:
      'from-landing-accent-ember/20 to-brand-500/20 ring-landing-accent-ember/30 text-landing-accent-ember',
  },
];

function AgentCard({
  agent,
  index,
  innerRef,
}: {
  agent: Agent;
  index: number;
  innerRef: React.RefObject<HTMLDivElement | null>;
}) {
  const Icon = agent.icon;
  return (
    <motion.div
      ref={innerRef}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-15%' }}
      transition={{
        duration: 0.5,
        ease: [0.16, 1, 0.3, 1],
        delay: index * 0.08,
      }}
      className={cn(
        'group relative flex h-full flex-col gap-3 rounded-2xl border border-surface-border bg-surface-card/70 p-5 backdrop-blur-sm',
        'transition-transform duration-300 ease-landing-out-quart hover:-translate-y-1 hover:border-brand-500/40',
        'focus-within:-translate-y-1 focus-within:border-brand-500/40',
      )}
    >
      <div className="flex items-center gap-3">
        <span
          aria-hidden="true"
          className={cn(
            'inline-flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br ring-1 ring-inset',
            agent.accent,
          )}
        >
          <Icon className="h-4 w-4" />
        </span>
        <h3 className="text-base font-semibold tracking-tight text-fg-primary">
          {agent.label}
        </h3>
        <span
          aria-hidden="true"
          className="ml-auto inline-flex items-center justify-center rounded-md border border-surface-border bg-surface-raised/60 px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.12em] text-fg-subtle"
        >
          0{index + 1}
        </span>
      </div>
      <p className="text-sm font-medium leading-snug text-fg-primary">
        {agent.job}
      </p>
      <dl className="mt-auto space-y-2 text-xs">
        <div>
          <dt className="font-semibold uppercase tracking-[0.12em] text-fg-subtle">
            Capabilities
          </dt>
          <dd className="mt-1 leading-relaxed text-fg-secondary">
            {agent.capabilities}
          </dd>
        </div>
        <div>
          <dt className="font-semibold uppercase tracking-[0.12em] text-fg-subtle">
            Runs on
          </dt>
          <dd className="mt-1 leading-relaxed text-fg-muted">{agent.runsOn}</dd>
        </div>
      </dl>
    </motion.div>
  );
}

export function SolutionAgents() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const detectRef = useRef<HTMLDivElement | null>(null);
  const triageRef = useRef<HTMLDivElement | null>(null);
  const huntRef = useRef<HTMLDivElement | null>(null);
  const respondRef = useRef<HTMLDivElement | null>(null);
  const cardRefs = [detectRef, triageRef, huntRef, respondRef];
  const prefersReducedMotion = useReducedMotion();

  const [isHorizontal, setIsHorizontal] = useState(false);
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mq = window.matchMedia('(min-width: 1024px)');
    const onChange = () => setIsHorizontal(mq.matches);
    onChange();
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  return (
    <section
      id="solution"
      aria-labelledby="solution-heading"
      className="relative py-20 sm:py-24 lg:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-400">
            Four agents, one workflow
          </p>
          <h2
            id="solution-heading"
            className="mt-3 text-3xl font-bold tracking-tight text-fg-primary sm:text-4xl lg:text-[40px] lg:leading-[1.15] lg:tracking-[-0.015em]"
          >
            One agent for each stage of an incident.
          </h2>
          <p className="mt-4 text-base leading-relaxed text-fg-secondary sm:text-lg">
            AiSOC ships exactly four named agents — Detect, Triage, Hunt, and
            Respond. Each one has a fixed job, a published capability list,
            and a replayable audit trail. Sub-agents (phishing, identity,
            cloud, insider) are capabilities of Triage, never separate brands.
          </p>
        </div>

        <div
          ref={containerRef}
          className="relative mt-12 grid gap-4 sm:gap-6 lg:mt-16 lg:grid-cols-4"
        >
          {AGENTS.map((agent, i) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              index={i}
              innerRef={cardRefs[i]}
            />
          ))}

          {isHorizontal && !prefersReducedMotion && (
            <>
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={detectRef}
                toRef={triageRef}
                duration={3}
                delay={0}
                curvature={0}
              />
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={triageRef}
                toRef={huntRef}
                duration={3}
                delay={0.7}
                curvature={0}
                gradientStart="#8b5cf6"
                gradientStop="#3b82f6"
              />
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={huntRef}
                toRef={respondRef}
                duration={3}
                delay={1.4}
                curvature={0}
                gradientStart="#3b82f6"
                gradientStop="#f97316"
              />
            </>
          )}
        </div>
      </div>
    </section>
  );
}
