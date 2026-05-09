'use client';

import { SWRConfig } from 'swr';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { CommandPalette } from './CommandPalette';
import { CopilotDock } from '@/components/copilot/CopilotDock';
import { DemoBanner } from '@/components/demo/DemoBanner';
import { DemoAutoLogin } from '@/components/demo/DemoAutoLogin';
import { ClientOnly } from '@/components/util/ClientOnly';
import { isDemoMode } from '@/lib/demoMode';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  // In demo mode the banner adds 36px (h-9) to the top, so push the main
  // content down to keep the TopBar from sliding underneath it.
  const demo = isDemoMode();
  const topPadClass = demo ? 'pt-[100px]' : 'pt-16';

  return (
    // SWR v2 disables `revalidateOnMount` by default whenever `fallbackData`
    // is provided. Most views in the console pass `fallbackData: MOCK_*` so
    // that the page renders instantly with placeholder data, but the side
    // effect was that the real fetcher never ran — every page silently froze
    // on its mocks (e.g. /cases showed seeded `case-1000` rows even though
    // /api/v1/cases worked). Forcing both flags here makes mocks act as a
    // first-paint placeholder and the live fetch always run on mount.
    <SWRConfig value={{ revalidateOnMount: true, revalidateIfStale: true }}>
      {/*
        Silently grants demo visitors a real JWT so SWR fetchers send a
        bearer and views like /cases swap their `fallbackData` mocks for
        live rows. Must sit *inside* SWRConfig so its post-login
        `mutate(() => true)` reaches every key in the same SWR cache.
        No-ops outside demo mode.
      */}
      <DemoAutoLogin />
      <div className="min-h-screen bg-surface-base">
        <DemoBanner />
        <Sidebar />
        <div className="md:ml-60">
          <TopBar demoOffset={demo} />
          <main className={`${topPadClass} min-h-screen`}>
            <div className="p-6">{children}</div>
          </main>
        </div>
        {/*
          Floating Copilot launcher and global command palette both rely on
          Framer Motion, which serializes inline `transform` styles differently
          on server vs client and triggers a hydration mismatch (React #418).
          Wrapping them in ClientOnly defers their entire render to after mount
          so SSR ships nothing for these subtrees.
        */}
        <ClientOnly>
          <CopilotDock />
        </ClientOnly>
        <ClientOnly>
          <CommandPalette />
        </ClientOnly>
      </div>
    </SWRConfig>
  );
}
