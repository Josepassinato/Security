'use client';

/**
 * PackHealthWidget
 * ================
 * Dashboard widget showing how many osquery packs are assigned to this tenant
 * and providing a quick-action link to the packs management page.
 *
 * Data is fetched via the packs API using SWR with a 5-minute refresh interval
 * since pack assignments change infrequently.
 */

import React from 'react';
import useSWR from 'swr';
import Link from 'next/link';
import { packsApi, type PackSummaryItem, type AssignedPackItem } from '@/lib/api';

// ─── SWR fetchers ────────────────────────────────────────────────────────────

function usePackHealth() {
  const catalog = useSWR<PackSummaryItem[]>(
    'packs-catalog',
    () => packsApi.list(),
    { refreshInterval: 5 * 60_000 },
  );

  const assigned = useSWR<AssignedPackItem[]>(
    'packs-assigned',
    () => packsApi.listAssigned(),
    { refreshInterval: 5 * 60_000 },
  );

  return {
    catalog: catalog.data ?? [],
    assigned: assigned.data ?? [],
    isLoading: catalog.isLoading || assigned.isLoading,
    error: catalog.error || assigned.error,
  };
}

// ─── Component ───────────────────────────────────────────────────────────────

export function PackHealthWidget() {
  const { catalog, assigned, isLoading, error } = usePackHealth();

  const assignedIds = new Set(assigned.map((a) => a.pack_id));
  const hasFim = assigned.some((a) => a.pack_id.includes('fim'));

  return (
    <div className="rounded-xl border border-gray-700/60 bg-gray-800/40 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg" aria-hidden>📦</span>
          <h2 className="text-sm font-semibold text-gray-100">Osquery Packs</h2>
        </div>
        <Link
          href="/packs"
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
          prefetch={false}
        >
          Manage →
        </Link>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-2 animate-pulse">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-6 bg-gray-700/40 rounded" />
          ))}
        </div>
      )}

      {/* Error */}
      {!isLoading && error && (
        <p className="text-xs text-red-400">Failed to load pack status.</p>
      )}

      {/* Content */}
      {!isLoading && !error && (
        <div className="space-y-3">
          {/* Summary counts */}
          <div className="flex gap-4">
            <div className="flex-1 text-center">
              <p className="text-2xl font-bold text-white">{assigned.length}</p>
              <p className="text-xs text-gray-400">Assigned</p>
            </div>
            <div className="flex-1 text-center">
              <p className="text-2xl font-bold text-white">{catalog.length}</p>
              <p className="text-xs text-gray-400">Available</p>
            </div>
            <div className="flex-1 text-center">
              <p className="text-2xl font-bold text-white">
                {catalog.length - assigned.length}
              </p>
              <p className="text-xs text-gray-400">Unassigned</p>
            </div>
          </div>

          {/* FIM status badge */}
          <div className="flex items-center gap-2 rounded-lg bg-gray-700/30 px-3 py-2">
            <span
              className={`inline-block h-2 w-2 rounded-full flex-shrink-0 ${
                hasFim ? 'bg-emerald-400' : 'bg-red-400'
              }`}
              aria-hidden
            />
            <span className="text-xs text-gray-300">
              FIM pack{' '}
              <span className={hasFim ? 'text-emerald-400' : 'text-red-400'}>
                {hasFim ? 'active' : 'not assigned'}
              </span>
            </span>
          </div>

          {/* Pack list (first 4) */}
          {catalog.length > 0 && (
            <ul className="space-y-1">
              {catalog.slice(0, 4).map((pack) => {
                const isAssigned = assignedIds.has(pack.id);
                return (
                  <li
                    key={pack.id}
                    className="flex items-center justify-between text-xs text-gray-300"
                  >
                    <span className="truncate max-w-[150px]" title={pack.name}>
                      {pack.name}
                    </span>
                    <span
                      className={`ml-2 flex-shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium ${
                        isAssigned
                          ? 'bg-emerald-900/50 text-emerald-400'
                          : 'bg-gray-700/50 text-gray-500'
                      }`}
                    >
                      {isAssigned ? 'on' : 'off'}
                    </span>
                  </li>
                );
              })}
              {catalog.length > 4 && (
                <li className="text-xs text-gray-500 pt-0.5">
                  +{catalog.length - 4} more
                </li>
              )}
            </ul>
          )}

          {catalog.length === 0 && (
            <p className="text-xs text-gray-500 text-center py-2">
              No packs available.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
