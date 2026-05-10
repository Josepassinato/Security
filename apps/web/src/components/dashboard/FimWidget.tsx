'use client';

/**
 * FimWidget
 * =========
 * Compact dashboard widget showing File Integrity Monitoring activity.
 * Displays top file-change events from the last 24 h and links to the
 * full FIM dashboard at /fim.
 *
 * Data is fetched via the osquery-api helper using SWR for auto-refresh.
 */

import React from 'react';
import useSWR from 'swr';
import Link from 'next/link';
import { getFimSummary } from '@/lib/osquery-api';

// ─── Action badge colours ────────────────────────────────────────────────────

const ACTION_DOT: Record<string, string> = {
  CREATED: 'bg-emerald-400',
  DELETED: 'bg-red-400',
  UPDATED: 'bg-amber-400',
  ATTRIBUTES_MODIFIED: 'bg-sky-400',
  MODIFIED: 'bg-amber-400',
  MOVED_FROM: 'bg-purple-400',
  MOVED_TO: 'bg-purple-400',
};

// ─── SWR fetcher ─────────────────────────────────────────────────────────────

const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000;

function useFimSummaryWidget() {
  const since = new Date(Date.now() - TWENTY_FOUR_HOURS).toISOString();
  return useSWR(
    ['fim-summary-widget', since],
    () => getFimSummary({ since }),
    { refreshInterval: 60_000 },
  );
}

// ─── Component ───────────────────────────────────────────────────────────────

export function FimWidget() {
  const { data, isLoading, error } = useFimSummaryWidget();

  return (
    <div className="rounded-xl border border-gray-700/60 bg-gray-800/40 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg" aria-hidden>🗂️</span>
          <h2 className="text-sm font-semibold text-gray-100">File Integrity (24 h)</h2>
        </div>
        <Link
          href="/fim"
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
          prefetch={false}
        >
          View all →
        </Link>
      </div>

      {/* Loading skeleton */}
      {isLoading && (
        <div className="space-y-2 animate-pulse">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-6 bg-gray-700/40 rounded" />
          ))}
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <p className="text-xs text-gray-500 italic">
          Unable to load FIM data — check osquery-tls connectivity.
        </p>
      )}

      {/* Data */}
      {data && !isLoading && (
        <>
          {/* KPI row */}
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="rounded-lg bg-gray-700/30 px-3 py-2 text-center">
              <div className="text-xl font-bold text-gray-100">
                {data.total_events.toLocaleString()}
              </div>
              <div className="text-[11px] text-gray-500">Total events</div>
            </div>
            <div className="rounded-lg bg-gray-700/30 px-3 py-2 text-center">
              <div className="text-xl font-bold text-gray-100">
                {data.active_nodes.toLocaleString()}
              </div>
              <div className="text-[11px] text-gray-500">Active nodes</div>
            </div>
          </div>

          {/* Action breakdown */}
          {data.by_action.length > 0 && (
            <div className="space-y-1 mb-3">
              {data.by_action.slice(0, 4).map(({ action, count }) => (
                <div key={action} className="flex items-center gap-2 text-xs">
                  <span
                    className={`inline-block h-2 w-2 flex-shrink-0 rounded-full ${ACTION_DOT[action] ?? 'bg-gray-400'}`}
                    aria-hidden
                  />
                  <span className="flex-1 truncate text-gray-300">{action}</span>
                  <span className="font-medium text-gray-200">{count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          )}

          {/* Top paths */}
          {data.top_paths.length > 0 && (
            <div>
              <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
                Top paths
              </div>
              <div className="space-y-0.5">
                {data.top_paths.slice(0, 3).map(({ target_path, count }) => (
                  <div key={target_path} className="flex items-center gap-1 text-xs">
                    <span className="flex-1 truncate font-mono text-gray-400 text-[11px]">
                      {target_path}
                    </span>
                    <span className="flex-shrink-0 font-medium text-gray-300">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {data.total_events === 0 && (
            <p className="text-xs text-gray-500 italic text-center py-2">
              No FIM events in the last 24 h.
            </p>
          )}
        </>
      )}
    </div>
  );
}
