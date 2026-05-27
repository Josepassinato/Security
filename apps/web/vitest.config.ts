import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';

// Smoke-test config for `apps/web`. We only need component-level rendering
// (jsdom) — no SSR, no Next.js server runtime. Anything that requires the
// full Next.js stack should live in an e2e suite (Playwright) instead.
export default defineConfig({
  // react() returns vite@7 Plugin types; vitest@2 expects vite@5 Plugin types.
  // Cast through unknown to bridge the version gap without changing the runtime.
  plugins: [react() as unknown as import('vitest/config').UserConfig['plugins']],
  // React 19 conditionally exports ``act`` only when NODE_ENV !== 'production'.
  // Vitest's default loader for the @vitejs/plugin-react pipeline can land on
  // the production CJS bundle in this monorepo, which makes ``React.act``
  // undefined and breaks @testing-library/react's act-compat shim. Pin the
  // define here so every test file sees the non-prod React surface.
  define: {
    'process.env.NODE_ENV': JSON.stringify('test'),
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    css: false,
    env: {
      NODE_ENV: 'test',
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
