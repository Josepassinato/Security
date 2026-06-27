'use client';

/**
 * AML screening — Review Queue (page 1).
 *
 * Read surface over GET /api/v1/screening?status=pending_review: the latest
 * decision per counterparty that is a POTENTIAL_MATCH still awaiting human
 * disposition. Examiner-grade table: who, the engine's score, and — the
 * product's spine — the exact sanctions-list BUILD the name was run against
 * (version + publication date), frozen on the decision.
 *
 * Pairs with:
 *   • services/api/app/api/v1/endpoints/screening.py
 * Disposition (clear/block/report) is the next page; here each row links to the
 * per-case dossier.
 */

import useSWR from 'swr';

// ── Types (mirror the FastAPI list response) ────────────────────────────────

interface ScreeningRow {
  id: string;
  counterparty_name: string;
  counterparty_id: string | null;
  counterparty_id_type: string;
  counterparty_jurisdiction: string | null;
  decision: string;
  disposition: string;
  match_score: number;
  matching_engine: string;
  list_of_record: string;
  list_source: string;
  list_dataset: string;
  list_version: string;
  list_release_date: string;
  screened_at: string;
  entry_hash: string | null;
}

async function fetchQueue(url: string): Promise<ScreeningRow[]> {
  const resp = await fetch(url, { credentials: 'include' });
  if (!resp.ok) throw new Error(`screening queue: HTTP ${resp.status}`);
  return resp.json();
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toISOString().replace('T', ' ').slice(0, 16) + ' UTC';
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toISOString().slice(0, 10);
}

// ── Component ───────────────────────────────────────────────────────────────

export function ScreeningReviewQueue() {
  const { data, error, isLoading } = useSWR<ScreeningRow[]>(
    '/api/v1/screening?status=pending_review',
    fetchQueue,
    { revalidateOnFocus: false },
  );

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-medium tracking-tight">Fila de Revisão — Screening</h1>
        <p className="text-sm text-muted-foreground">
          Matches potenciais aguardando disposição humana. Cada decisão carrega o
          <span className="font-medium"> build da lista</span> contra o qual o nome foi
          rodado — congelado no instante do screening, defensável em exame.
        </p>
      </header>

      {isLoading && (
        <div className="rounded border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
          carregando…
        </div>
      )}

      {error && (
        <div className="rounded border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          Falha ao carregar a fila: {String(error)}
        </div>
      )}

      {data && data.length === 0 && (
        <div className="rounded border border-border bg-muted/20 p-6 text-sm text-muted-foreground">
          Nenhum match potencial pendente. A carteira está limpa para revisão.
        </div>
      )}

      {data && data.length > 0 && (
        <section className="rounded border border-border">
          <table className="w-full text-sm">
            <thead className="bg-muted/30 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-3">Contraparte</th>
                <th className="px-4 py-3 text-right">Score</th>
                <th className="px-4 py-3">Build da lista</th>
                <th className="px-4 py-3">Screenado (UTC)</th>
                <th className="px-4 py-3 text-right">Ação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data.map((r) => (
                <tr key={r.id} className="hover:bg-muted/20">
                  <td className="px-4 py-3">
                    <div className="font-medium">{r.counterparty_name}</div>
                    <div className="font-mono text-xs text-muted-foreground">
                      {r.counterparty_id ? `${r.counterparty_id} (${r.counterparty_id_type})` : 'sem documento'}
                      {r.counterparty_jurisdiction ? ` · ${r.counterparty_jurisdiction}` : ''}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="font-mono font-medium tabular-nums">{r.match_score}</span>
                    <div className="text-xs text-muted-foreground">/ 100</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-mono text-xs">{r.list_source}</div>
                    <div className="font-mono text-xs text-muted-foreground">{r.list_version}</div>
                    <div className="text-xs text-muted-foreground">publicado {fmtDate(r.list_release_date)}</div>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">{fmtDateTime(r.screened_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <a
                      href={`/compliance/screening/${encodeURIComponent(r.id)}`}
                      className="rounded border border-border px-3 py-1.5 text-xs hover:bg-accent"
                    >
                      revisar →
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <p className="text-xs text-muted-foreground">
        Disposição (limpar / bloquear / reportar) é append-only — cada ação grava
        um registro novo encadeado, nunca altera o anterior. (Próxima página.)
      </p>
    </div>
  );
}
