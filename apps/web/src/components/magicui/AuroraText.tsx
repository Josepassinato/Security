// Source: https://magicui.design/docs/components/aurora-text
// Licensed under MIT. Vendored implementation. Renders inline text with
// a slow-shifting aurora gradient (brand-500 → violet → brand-700) so
// the hero H1's accent phrase ("ten minutes" in the content doc) draws
// the eye without competing with the surrounding white text.
'use client';

import { useReducedMotion } from 'framer-motion';
import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface AuroraTextProps {
  children: ReactNode;
  className?: string;
}

export function AuroraText({ children, className }: AuroraTextProps) {
  const prefersReducedMotion = useReducedMotion();
  return (
    <span
      className={cn(
        'inline-block bg-gradient-to-r from-brand-300 via-landing-accent-violet to-brand-500 bg-clip-text text-transparent',
        !prefersReducedMotion && 'animate-aurora-shift [background-size:200%_100%]',
        className,
      )}
    >
      {children}
    </span>
  );
}
