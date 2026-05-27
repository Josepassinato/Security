'use client';

/**
 * Evidence Packs admin panel — CARD-016.
 *
 * Read-only operator surface over the framework that lives in
 * services/api/app/evidence_pack/. Lists every pack discovered on the
 * server, lets the operator compile one against the runtime, and opens
 * the rendered preview in a new tab.
 *
 * Production-verification gate: any bundle whose seal is mock (i.e.
 * MockTsaClient / MockSigner) shows a clear warning. Operators must
 * not send mock-sealed PDFs to a fiscalização.
 *
 * Pairs with:
 *   • services/api/app/api/v1/endpoints/evidence_packs.py
 *   • customizations/compliance/evidence-packs/*.yaml
 */

import { useState } from 'react';
import useSWR from 'swr';

// ── Types (mirror the FastAPI response models) ──────────────────────────────

interface PackSummary {
  pack_id: string;
  regulation_code: string;
  article: string;
  title: string;
  reporting_period: string;
  output_format: string;
}

interface PackListResponse {
  packs: PackSummary[];
  count: number;
}

interface BundleTimestamp {
  tsa_name: string;
  stamped_at: string;
  token_der_hex: string;
  digest_hex: string;
}

interface BundleSignature {
  signer_subject: string;
  signed_at: string;
  digest_algorithm: string;
  digest_hex: string;
  signature_der_hex: string;
}

interface BundleResponse {
  pack_id: string;
  generated_at: string;
  window_start: string;
  window_end: string;
  data: Record<string, unknown>;
  data_digest_hex: string;
  timestamp: BundleTimestamp;
  signature: BundleSignature;
  hash_chain_entry_hash_hex: string | null;
  prev_chain_entry_hash_hex: string | null;
  mock_seal: boolean;
}

// ── Fetchers ────────────────────────────────────────────────────────────────

async function fetchPacks(): Promise<PackListResponse> {
  const resp = await fetch('/api/v1/evidence-packs', { credentials: 'include' });
  if (!resp.ok) throw new Error(`evidence-packs list: HTTP ${resp.status}`);
  return resp.json();
}

async function compilePack(packId: string): Promise<BundleResponse> {
  const resp = await fetch(
    `/api/v1/evidence-packs/${encodeURIComponent(packId)}/compile`,
    { method: 'POST', credentials: 'include' },
  );
  if (!resp.ok) throw new Error(`compile ${packId}: HTTP ${resp.status}`);
  return resp.json();
}

function previewUrl(packId: string): string {
  return `/api/v1/evidence-packs/${encodeURIComponent(packId)}/preview.html`;
}

function downloadUrl(packId: string): string {
  return `/api/v1/evidence-packs/${encodeURIComponent(packId)}/download.pdf`;
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function shortHash(hex: string | null | undefined, head = 10, tail = 6): string {
  if (!hex) return '—';
  if (hex.length <= head + tail + 1) return hex;
  return `${hex.slice(0, head)}…${hex.slice(-tail)}`;
}

function formatPeriod(period: string): string {
  const map: Record<string, string> = {
    '30d': 'last 30 days',
    '90d': 'last 90 days',
    '180d': 'last 180 days',
    '365d': 'last year',
    point_in_time: 'point in time',
    since_last_inspection: 'since last inspection',
  };
  return map[period] ?? period;
}

// ── Component ───────────────────────────────────────────────────────────────

export function EvidencePacksView() {
  const { data, error, isLoading, mutate } = useSWR<PackListResponse>(
    '/api/v1/evidence-packs',
    fetchPacks,
    { revalidateOnFocus: false },
  );

  const [compiling, setCompiling] = useState<string | null>(null);
  const [compileError, setCompileError] = useState<string | null>(null);
  const [bundle, setBundle] = useState<BundleResponse | null>(null);

  const handleCompile = async (packId: string) => {
    setCompiling(packId);
    setCompileError(null);
    setBundle(null);
    try {
      const result = await compilePack(packId);
      setBundle(result);
    } catch (e) {
      setCompileError(String(e));
    } finally {
      setCompiling(null);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-medium tracking-tight">Evidence Packs</h1>
        <p className="text-sm text-muted-foreground">
          Bacen Evidence Engine — packs available on this deployment. Read-only;
          the compiled bundle is sealed with the TSA + signer configured on the
          server (mock by default until SafeWeb + e-CNPJ credentials are wired).
        </p>
      </header>

      {/* Pack list */}
      {isLoading && (
        <div className="rounded border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
          loading…
        </div>
      )}

      {error && (
        <div className="rounded border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          Failed to load packs: {String(error)}
        </div>
      )}

      {data && data.packs.length === 0 && (
        <div className="rounded border border-border bg-muted/20 p-4 text-sm text-muted-foreground">
          No packs found in <code className="font-mono">customizations/compliance/evidence-packs/</code>.
        </div>
      )}

      {data && data.packs.length > 0 && (
        <section className="rounded border border-border">
          <table className="w-full text-sm">
            <thead className="bg-muted/30 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-3">Pack</th>
                <th className="px-4 py-3">Regulation</th>
                <th className="px-4 py-3">Period</th>
                <th className="px-4 py-3">Output</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data.packs.map((p) => (
                <tr key={p.pack_id} className="hover:bg-muted/20">
                  <td className="px-4 py-3">
                    <div className="font-medium">{p.title}</div>
                    <div className="font-mono text-xs text-muted-foreground">{p.pack_id}</div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {p.regulation_code}
                    <div className="text-muted-foreground">{p.article}</div>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {formatPeriod(p.reporting_period)}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{p.output_format}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => handleCompile(p.pack_id)}
                        disabled={compiling === p.pack_id}
                        className="rounded border border-border px-3 py-1.5 text-xs hover:bg-accent disabled:opacity-50"
                      >
                        {compiling === p.pack_id ? 'compiling…' : 'compile'}
                      </button>
                      <a
                        href={previewUrl(p.pack_id)}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded border border-border px-3 py-1.5 text-xs hover:bg-accent"
                      >
                        preview ↗
                      </a>
                      <a
                        href={downloadUrl(p.pack_id)}
                        className="rounded border border-border px-3 py-1.5 text-xs hover:bg-accent"
                        title="download as PDF (requires WeasyPrint on the server)"
                      >
                        PDF ↓
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* Compile result */}
      {compileError && (
        <div className="rounded border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          {compileError}
        </div>
      )}

      {bundle && (
        <section
          className={
            bundle.mock_seal
              ? 'rounded border border-amber-500/40 bg-amber-500/5 p-5'
              : 'rounded border border-emerald-500/40 bg-emerald-500/5 p-5'
          }
        >
          <div className="flex items-baseline justify-between gap-4">
            <div>
              <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                last compiled bundle
              </p>
              <p className="mt-1 text-lg font-medium">{bundle.pack_id}</p>
            </div>
            {bundle.mock_seal && (
              <span className="rounded bg-amber-500/15 px-2 py-0.5 text-xs font-medium text-amber-700">
                MOCK SEAL — dev only
              </span>
            )}
          </div>

          <dl className="mt-5 grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
            <div>
              <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                data digest (SHA-256)
              </dt>
              <dd className="mt-1 font-mono">{shortHash(bundle.data_digest_hex, 14, 8)}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                timestamp
              </dt>
              <dd className="mt-1">
                {bundle.timestamp.tsa_name}
                <div className="font-mono text-xs text-muted-foreground">
                  {new Date(bundle.timestamp.stamped_at).toLocaleString()}
                </div>
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                signer
              </dt>
              <dd className="mt-1 text-xs">{bundle.signature.signer_subject}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                chain link
              </dt>
              <dd className="mt-1 font-mono text-xs">
                {shortHash(bundle.prev_chain_entry_hash_hex, 8, 4)} →{' '}
                {shortHash(bundle.hash_chain_entry_hash_hex, 8, 4)}
              </dd>
            </div>
          </dl>

          <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-border/60 pt-4">
            <a
              href={previewUrl(bundle.pack_id)}
              target="_blank"
              rel="noreferrer"
              className="rounded border border-border bg-background px-3 py-1.5 text-xs hover:bg-accent"
            >
              open preview ↗
            </a>
            <a
              href={downloadUrl(bundle.pack_id)}
              className="rounded border border-border bg-background px-3 py-1.5 text-xs hover:bg-accent"
              title="download as PDF (requires WeasyPrint on the server)"
            >
              download PDF ↓
            </a>
            <button
              type="button"
              onClick={() => void mutate()}
              className="rounded border border-border bg-background px-3 py-1.5 text-xs hover:bg-accent"
            >
              refresh catalog
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
