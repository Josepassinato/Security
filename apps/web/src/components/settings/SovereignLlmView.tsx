'use client';

/**
 * Sovereign LLM status panel — CARD-015 Tarefa #5.
 *
 * Read-only observability for the sovereign deployment (Modalidade A —
 * Mac Mini in the cofre, Modalidade B — VPS Llama dedicated to the
 * customer). Shows the resolved mode, endpoint, configured model, and
 * a live healthcheck probe (latency + active model reported by the
 * runtime).
 *
 * Pairs with:
 *   • services/api/app/api/v1/endpoints/sovereign_llm.py
 *   • services/agents/app/security/sovereign_healthcheck.py
 *   • scripts/sovereign-appliance/install-vps-linux.sh
 *
 * No write surface here on purpose — the operator switches mode by
 * setting QUARRY_LLM_MODE at deploy time and re-rolling the pod.
 * That keeps a typo on the panel from accidentally re-routing the
 * production LLM call out to the public internet.
 */

import { useState } from 'react';
import useSWR from 'swr';

// ── Types (mirror the FastAPI response model in sovereign_llm.py) ───────────

type Mode = 'cloud-byok' | 'sovereign-vps' | 'sovereign-mac';
type Runtime = 'ollama' | 'vllm' | 'unknown';

interface Healthcheck {
  ok: boolean;
  runtime: Runtime;
  active_model: string | null;
  latency_ms: number;
  reason: string;
  checked_at: string;
}

interface SovereignLlmStatus {
  mode: Mode;
  active: boolean;
  endpoint: string | null;
  model: string | null;
  api_key_set: boolean;
  healthcheck: Healthcheck | null;
}

// ── Fetcher ─────────────────────────────────────────────────────────────────

async function fetchSovereignStatus(): Promise<SovereignLlmStatus> {
  const resp = await fetch('/api/v1/llm/sovereign/status', { credentials: 'include' });
  if (!resp.ok) {
    throw new Error(`sovereign status: HTTP ${resp.status}`);
  }
  return resp.json();
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function modeLabel(mode: Mode): string {
  switch (mode) {
    case 'sovereign-vps':
      return 'Sovereign — VPS Llama';
    case 'sovereign-mac':
      return 'Sovereign — Mac Mini';
    default:
      return 'Cloud BYOK';
  }
}

function modeDescription(mode: Mode): string {
  switch (mode) {
    case 'sovereign-vps':
      return 'LLM running on a dedicated VPS inside your perimeter, reachable over a private WireGuard tunnel.';
    case 'sovereign-mac':
      return 'LLM running on a Mac Mini physically installed in your cofre / on-prem rack.';
    default:
      return 'LLM calls routed to a public cloud provider (OpenAI, Anthropic, etc.) via BYOK credentials.';
  }
}

// ── Component ───────────────────────────────────────────────────────────────

export function SovereignLlmView() {
  const [probeNonce, setProbeNonce] = useState(0);
  const { data, error, isLoading, mutate } = useSWR<SovereignLlmStatus>(
    ['sovereign-llm-status', probeNonce],
    fetchSovereignStatus,
    { revalidateOnFocus: false },
  );

  const refresh = () => {
    setProbeNonce((n) => n + 1);
    void mutate();
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-medium tracking-tight">Sovereign LLM</h1>
        <p className="text-sm text-muted-foreground">
          Live status of the on-premise or dedicated-VPS LLM deployment (CARD-015).
          Read-only — switch modes via the <code>QUARRY_LLM_MODE</code> env var.
        </p>
      </header>

      {isLoading && (
        <div className="rounded border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
          probing…
        </div>
      )}

      {error && (
        <div className="rounded border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          Failed to load status: {String(error)}
        </div>
      )}

      {data && (
        <>
          {/* Mode banner */}
          <section
            className={
              data.active
                ? 'rounded border border-emerald-500/30 bg-emerald-500/5 p-5'
                : 'rounded border border-border bg-muted/20 p-5'
            }
          >
            <div className="flex items-baseline justify-between gap-4">
              <div>
                <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                  active mode
                </p>
                <p className="mt-1 text-lg font-medium">{modeLabel(data.mode)}</p>
              </div>
              <button
                type="button"
                onClick={refresh}
                className="rounded border border-border px-3 py-1.5 text-xs hover:bg-accent"
              >
                refresh probe
              </button>
            </div>
            <p className="mt-3 max-w-xl text-sm text-muted-foreground">
              {modeDescription(data.mode)}
            </p>
          </section>

          {/* Cloud-BYOK shortcut */}
          {!data.active && (
            <section className="rounded border border-border p-4 text-sm text-muted-foreground">
              The sovereign deployment is not engaged on this pod. For cloud-BYOK
              provider status, see the{' '}
              <a href="/settings" className="underline">
                Deployment &amp; AI
              </a>{' '}
              panel.
            </section>
          )}

          {/* Sovereign config + healthcheck */}
          {data.active && (
            <>
              <section className="rounded border border-border p-5">
                <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
                  Configuration
                </h2>
                <dl className="mt-4 grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                      endpoint
                    </dt>
                    <dd className="mt-1 font-mono text-sm">{data.endpoint}</dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                      configured model
                    </dt>
                    <dd className="mt-1 font-mono text-sm">{data.model}</dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                      auth
                    </dt>
                    <dd className="mt-1 text-sm">
                      {data.api_key_set ? 'bearer token set (vLLM proxy)' : 'open (Ollama default)'}
                    </dd>
                  </div>
                </dl>
              </section>

              {data.healthcheck && (
                <section
                  className={
                    data.healthcheck.ok
                      ? 'rounded border border-emerald-500/30 bg-emerald-500/5 p-5'
                      : 'rounded border border-destructive/40 bg-destructive/5 p-5'
                  }
                >
                  <div className="flex items-baseline justify-between">
                    <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
                      Live probe
                    </h2>
                    <span
                      className={
                        data.healthcheck.ok
                          ? 'rounded bg-emerald-500/15 px-2 py-0.5 text-xs font-medium text-emerald-700'
                          : 'rounded bg-destructive/15 px-2 py-0.5 text-xs font-medium text-destructive'
                      }
                    >
                      {data.healthcheck.ok ? 'up' : 'down'}
                    </span>
                  </div>

                  <dl className="mt-4 grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
                    <div>
                      <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                        runtime
                      </dt>
                      <dd className="mt-1 font-mono">{data.healthcheck.runtime}</dd>
                    </div>
                    <div>
                      <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                        active model
                      </dt>
                      <dd className="mt-1 font-mono">
                        {data.healthcheck.active_model ?? '—'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                        latency
                      </dt>
                      <dd className="mt-1 font-mono">{data.healthcheck.latency_ms} ms</dd>
                    </div>
                    <div>
                      <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                        checked
                      </dt>
                      <dd className="mt-1 font-mono text-xs">
                        {new Date(data.healthcheck.checked_at).toLocaleString()}
                      </dd>
                    </div>
                  </dl>

                  {data.healthcheck.reason && (
                    <p className="mt-4 rounded bg-background/60 p-3 text-xs text-muted-foreground">
                      {data.healthcheck.reason}
                    </p>
                  )}
                </section>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
