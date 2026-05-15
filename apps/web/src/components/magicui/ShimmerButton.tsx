// Source: https://magicui.design/docs/components/shimmer-button
// Licensed under MIT. Vendored implementation. A brand-tinted button that
// loops a soft sheen across its surface on hover only — never on mount —
// so the conversion target never competes with the H1 reveal for
// attention. Reduces to a solid brand-500 button under
// `prefers-reduced-motion`.
'use client';

import type { ButtonHTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

type ShimmerButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  shimmerColor?: string;
  shimmerDuration?: string;
};

export const ShimmerButton = forwardRef<HTMLButtonElement, ShimmerButtonProps>(
  function ShimmerButton(
    {
      children,
      className,
      shimmerColor = 'rgba(147,197,253,0.65)',
      shimmerDuration = '2.5s',
      ...rest
    },
    ref,
  ) {
    return (
      <button
        ref={ref}
        className={cn(
          'group/shimmer relative inline-flex h-11 cursor-pointer items-center justify-center overflow-hidden rounded-md bg-gradient-to-br from-brand-500 to-brand-700 px-6 text-sm font-semibold text-white shadow-[0_0_0_1px_rgba(59,130,246,0.35)] transition-shadow duration-200 ease-landing-in-out-quad',
          'hover:shadow-[0_8px_24px_-8px_rgba(59,130,246,0.55)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base',
          'motion-reduce:hover:shadow-none',
          className,
        )}
        style={
          {
            '--shimmer-color': shimmerColor,
            '--shimmer-duration': shimmerDuration,
          } as React.CSSProperties
        }
        {...rest}
      >
        <span
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -translate-x-full bg-[linear-gradient(110deg,transparent_0%,var(--shimmer-color)_50%,transparent_100%)] opacity-0 transition-opacity duration-200 ease-out group-hover/shimmer:opacity-100 group-hover/shimmer:[animation:shimmer-pass_var(--shimmer-duration)_linear_infinite] motion-reduce:hidden"
        />
        <span className="relative z-10 flex items-center gap-2">{children}</span>
      </button>
    );
  },
);

// Keyframe lives here so a host page that imports the button gets the
// animation without needing to load it from globals.css separately. This
// is the one keyframe we keep co-located with its consumer — every other
// landing-page keyframe is in globals.css.
if (typeof document !== 'undefined' && !document.getElementById('shimmer-button-keyframe')) {
  const style = document.createElement('style');
  style.id = 'shimmer-button-keyframe';
  style.textContent = `@keyframes shimmer-pass { from { transform: translateX(-120%); } to { transform: translateX(120%); } }`;
  document.head.appendChild(style);
}
