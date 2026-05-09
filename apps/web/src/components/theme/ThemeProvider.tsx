'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { THEME_STORAGE_KEY } from './themeScript';

export type ThemePreference = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

type ThemeContextValue = {
  /** What the user actually chose (light / dark / system). */
  preference: ThemePreference;
  /** What's currently painted (system → resolved against `prefers-color-scheme`). */
  resolved: ResolvedTheme;
  setPreference: (next: ThemePreference) => void;
  toggle: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

const SYSTEM_QUERY = '(prefers-color-scheme: light)';

function readStoredPreference(): ThemePreference {
  if (typeof window === 'undefined') return 'dark';
  try {
    const value = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (value === 'light' || value === 'dark' || value === 'system') return value;
  } catch {
    // localStorage can throw on iOS private mode etc; fall back silently.
  }
  return 'dark';
}

function resolvePreference(preference: ThemePreference): ResolvedTheme {
  if (preference !== 'system') return preference;
  if (typeof window === 'undefined') return 'dark';
  return window.matchMedia(SYSTEM_QUERY).matches ? 'light' : 'dark';
}

function applyTheme(preference: ThemePreference, resolved: ResolvedTheme) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  root.setAttribute('data-theme', resolved);
  root.setAttribute('data-theme-preference', preference);
  root.style.colorScheme = resolved;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  // Initialised with the same default the bootstrap script uses so that the
  // first React render matches the DOM the script wrote → no hydration
  // mismatch. The effect below corrects it from localStorage on mount.
  const [preference, setPreferenceState] = useState<ThemePreference>('dark');
  const [resolved, setResolved] = useState<ResolvedTheme>('dark');

  // Mount: pick up whatever the bootstrap script already wrote so the React
  // tree agrees with the DOM. We deliberately do NOT call `applyTheme()` here
  // — the bootstrap script already did that, and re-applying would be a
  // no-op write that just churns React.
  useEffect(() => {
    const stored = readStoredPreference();
    const next = resolvePreference(stored);
    setPreferenceState(stored);
    setResolved(next);
  }, []);

  // Track OS-level preference changes while the user is on `system`.
  useEffect(() => {
    if (preference !== 'system') return;
    if (typeof window === 'undefined') return;

    const media = window.matchMedia(SYSTEM_QUERY);
    const handle = (event: MediaQueryListEvent) => {
      const next: ResolvedTheme = event.matches ? 'light' : 'dark';
      setResolved(next);
      applyTheme('system', next);
    };
    media.addEventListener('change', handle);
    return () => media.removeEventListener('change', handle);
  }, [preference]);

  const setPreference = useCallback((next: ThemePreference) => {
    const nextResolved = resolvePreference(next);
    setPreferenceState(next);
    setResolved(nextResolved);
    applyTheme(next, nextResolved);
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, next);
    } catch {
      // private mode / quota — accept that the choice doesn't persist.
    }
  }, []);

  const toggle = useCallback(() => {
    // Toggle cycles dark → light → system → dark so users can discover the
    // OS-following option without an extra UI affordance.
    setPreference(
      preference === 'dark' ? 'light' : preference === 'light' ? 'system' : 'dark',
    );
  }, [preference, setPreference]);

  const value = useMemo<ThemeContextValue>(
    () => ({ preference, resolved, setPreference, toggle }),
    [preference, resolved, setPreference, toggle],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useTheme() must be used inside <ThemeProvider>');
  }
  return ctx;
}
