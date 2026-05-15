import type { Config } from 'tailwindcss';

/*
 * The `surface.*` and `fg.*` palettes below resolve at runtime via CSS
 * variables defined in `src/app/globals.css`. That layer is what powers
 * the WS-F1 light theme: when `<html data-theme="light">` is set, the
 * variables flip and any `bg-surface-card`, `text-fg-primary`, etc. class
 * automatically follows — no per-component branching required.
 *
 * `brand.*`, `severity.*`, and `status.*` are deliberately theme-agnostic
 * (a "high"-severity alert should look the same in both themes).
 *
 * Migration playbook for un-themed surfaces lives in
 * `apps/docs/docs/operations/theming.md`.
 */
const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    '../../packages/ui/src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Primary brand — used for CTAs, links, and active state. Aligned with the
        // logo gradient (sky-400 → blue-700) so the marketing site and console feel
        // like one product.
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // Surface ramp — themeable. Resolves to dark hex values on
        // `[data-theme="dark"]` and slate-tinted whites on
        // `[data-theme="light"]`.
        surface: {
          base: 'var(--surface-base)',
          raised: 'var(--surface-raised)',
          card: 'var(--surface-card)',
          hover: 'var(--surface-hover)',
          subtle: 'var(--surface-subtle)',
          border: 'var(--surface-border)',
          divider: 'var(--surface-divider)',
        },
        // Foreground ramp — themeable. `fg-primary` is the highest-contrast
        // token, `fg-subtle` is the lowest. Use these instead of raw
        // `text-white` / `text-gray-*` on chrome so the text inverts in
        // light mode.
        fg: {
          primary: 'var(--fg-primary)',
          secondary: 'var(--fg-secondary)',
          muted: 'var(--fg-muted)',
          subtle: 'var(--fg-subtle)',
          inverse: 'var(--fg-inverse)',
        },
        // Severity scale shared by alerts, cases, dashboard, and detection rules.
        // Wired to the same hex values used in `getAlertSeverityColor()` so a
        // background-class swap stays consistent with text/badge colors.
        severity: {
          critical: '#ef4444',
          high: '#f97316',
          medium: '#eab308',
          low: '#3b82f6',
          info: '#22c55e',
        },
        // Connection / health status — used by LiveFeedPanel, connector cards, etc.
        status: {
          live: '#22c55e',
          warn: '#f59e0b',
          dead: '#ef4444',
          idle: '#64748b',
        },
        // Marketing-landing accents (T6.5). Strictly additive — these live in
        // a `landing.*` namespace so they cannot collide with the console
        // palette and only appear on `apps/web/src/components/landing/`
        // surfaces. Mirrors `docs/design/landing-page-design-tokens.md` §2.3.
        landing: {
          accent: {
            ember: '#f97316',
            violet: '#8b5cf6',
          },
        },
      },
      backgroundImage: {
        // Three brand-tinted gradients used by the landing page only. Resolve
        // to CSS variables defined in `globals.css` so a future light-mode
        // landing variant can flip the stops without touching components.
        'landing-grad-hero': 'var(--landing-grad-hero)',
        'landing-grad-pillars': 'var(--landing-grad-pillars)',
        'landing-grad-cta': 'var(--landing-grad-cta)',
      },
      transitionTimingFunction: {
        // Easing tokens from `docs/design/landing-page-design-tokens.md` §7.1.
        'landing-out-expo': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'landing-out-quart': 'cubic-bezier(0.25, 1, 0.5, 1)',
        'landing-in-out-quad': 'cubic-bezier(0.45, 0, 0.55, 1)',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
