// Source: https://magicui.design/docs/components/meteors
// Licensed under MIT. Vendored implementation. Renders a configurable
// number of meteor streaks across the parent. Each meteor uses the
// shared `animate-meteor` keyframe in `globals.css`; the JS layer only
// computes initial start positions and a per-meteor delay. Hidden under
// `prefers-reduced-motion`.
'use client';

import { useReducedMotion } from 'framer-motion';
import { useMemo } from 'react';
import { cn } from '@/lib/utils';

interface MeteorsProps {
  /** Number of meteors to render. Default 18 — pre-trimmed for the perf budget. */
  number?: number;
  className?: string;
}

export function Meteors({ number = 18, className }: MeteorsProps) {
  const prefersReducedMotion = useReducedMotion();
  const meteors = useMemo(
    () =>
      Array.from({ length: number }, (_, idx) => ({
        id: idx,
        top: `${Math.floor(Math.random() * 100)}%`,
        left: `${Math.floor(Math.random() * 100)}%`,
        delay: `${Math.random() * 4}s`,
        duration: `${4 + Math.random() * 6}s`,
      })),
    [number],
  );

  if (prefersReducedMotion) return null;

  return (
    <div className={cn('pointer-events-none absolute inset-0 overflow-hidden', className)}>
      {meteors.map(({ id, top, left, delay, duration }) => (
        <span
          key={id}
          aria-hidden="true"
          className="absolute h-0.5 w-0.5 rotate-[215deg] animate-meteor rounded-full bg-slate-200 shadow-[0_0_0_1px_rgba(255,255,255,0.1)] before:absolute before:top-1/2 before:h-px before:w-12 before:-translate-y-1/2 before:bg-gradient-to-r before:from-slate-100 before:to-transparent before:content-['']"
          style={{ top, left, animationDelay: delay, animationDuration: duration }}
        />
      ))}
    </div>
  );
}
