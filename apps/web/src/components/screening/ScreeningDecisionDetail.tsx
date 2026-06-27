'use client';

/**
 * AML screening — Decision detail + disposition (page 2).
 *
 * Shows one decision (GET /api/v1/screening/{id}) with its frozen list-build
 * carimbo and a link to the per-case dossier, then lets a reviewer record a
 * human disposition via POST /api/v1/screening/{id}/review.
 *
 * The disposition is APPEND-ONLY: submitting records a NEW chained decision
 * (reviewer + rationale required) — it never edits the original. On success we
 * revalidate the review queue.
 */

import { useState } from 'react';
import useSWR, { mutate } from 'swr';

interface Decision {
  id: string;
  counterparty_name: string;
  decision: string;
  disposition: string;
  match_score: number;
  matching_engine: string;
  list_of_record: string;
  list_dataset: string;
  list_version: string;
  list_release_date: string;
  screened_at: string;
  entry_hash: string | null;
}

const QUEUE_KEY = '/api/v1/screening?status=pending_review';

const DISPOSITIONS: { value: string; label: string }[] = [
  { value: 'CLEARED_FALSE_POSITIVE', label: 'Falso positivo — liberar' },
  { value: 'BLOCKED', label: 'Bloquear' },
  { value: 'REPORTED', label: 'Reportar (COAF/autoridade)' },
];

async function fetchDecision(url: string): Promise<Decision> {
  const resp = await fetch(url, { credentials: 'include' });
  if (!resp.ok) throw new Error(`decision: HTTP ${resp.status}`);
  return resp.json();
}

function fmt(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? String(iso) : d.toISOString().replace('T', ' ').slice(0, 16) + ' UTC';
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 border-b border-border py-2 text-sm last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right">{children}</span>
    </div>
  );
}

export function ScreeningDecisionDetail({ id }: { id: string }) {
  const { data, error, isLoading } = useSWR<Decision>(`/api/v1/screening/${id}`, fetchDecision, {
    revalidateOnFocus: false,
  });

  const [disposition, setDisposition] = useState('CLEARED_FALSE_POSITIVE');
  const [rationale, setRationale] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState<Decision | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setSubmitError(null);
    try {
      const resp = await fetch(`/api/v1/screening/${id}/review`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ disposition, rationale }),
      });
      if (!resp.ok) throw new Error(`review: HTTP ${resp.status} — ${await resp.text()}`);
      const created: Decision = await resp.json();
      setDone(created);
      void mutate(QUEUE_KEY);
    } catch (err) {
      setSubmitError(String(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (isLoading) {
    return <div className="rounded border border-border bg-muted/30 p-4 text-sm text-muted-foreground">carregando…</div>;
  }
  if (error || !data) {
    return (
      <div className="rounded border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
        Falha ao carregar a decisão: {String(error)}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <header className="space-y-1">
        <a href="/compliance/screening" className="text-xs text-muted-foreground hover:underline">
          ← fila de revisão
        </a>
        <h1 className="text-2xl font-medium tracking-tight">{data.counterparty_name}</h1>
        <p className="text-sm text-muted-foreground">
          {data.decision} · disposição atual: {data.disposition}
        </p>
      </header>

      <section className="rounded border border-border p-4">
        <Row label="Score (0–100)">
          <span className="font-mono tabular-nums">{data.match_score}</span>
        </Row>
        <Row label="Engine de matching">
          <span className="font-mono text-xs">{data.matching_engine}</span>
        </Row>
        <Row label="Lista (fonte-de-registro)">
          <span className="font-mono text-xs">
            {data.list_dataset} · {data.list_of_record}
          </span>
        </Row>
        <Row label="Build da lista">
          <span className="font-mono text-xs">{data.list_version}</span>
        </Row>
        <Row label="Publicação do build">
          <span className="text-xs">{fmt(data.list_release_date)}</span>
        </Row>
        <Row label="Screenado (UTC)">
          <span className="text-xs">{fmt(data.screened_at)}</span>
        </Row>
        <Row label="Hash da decisão">
          <code className="font-mono text-xs text-muted-foreground">{data.entry_hash ?? '—'}</code>
        </Row>
        <div className="pt-3">
          <a
            href={`/api/v1/screening/${id}/dossier.html`}
            target="_blank"
            rel="noreferrer"
            className="rounded border border-border px-3 py-1.5 text-xs hover:bg-accent"
          >
            ver dossiê ↗
          </a>
        </div>
      </section>

      {done ? (
        <section className="rounded border border-border bg-muted/20 p-4 text-sm">
          <p className="font-medium">Disposição registrada.</p>
          <p className="mt-1 text-muted-foreground">
            Novo registro encadeado: <code className="font-mono text-xs">{done.disposition}</code> ·
            hash <code className="font-mono text-xs">{(done.entry_hash ?? '').slice(0, 12)}…</code>. O
            registro original permanece imutável.
          </p>
          <a href="/compliance/screening" className="mt-3 inline-block text-xs hover:underline">
            ← voltar à fila
          </a>
        </section>
      ) : (
        <form onSubmit={submit} className="space-y-4 rounded border border-border p-4">
          <h2 className="text-sm font-medium">Registrar disposição</h2>
          <div className="space-y-2">
            <label className="block text-xs text-muted-foreground" htmlFor="disposition">
              Disposição
            </label>
            <select
              id="disposition"
              value={disposition}
              onChange={(e) => setDisposition(e.target.value)}
              className="w-full rounded border border-border bg-background px-3 py-2 text-sm"
            >
              {DISPOSITIONS.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="block text-xs text-muted-foreground" htmlFor="rationale">
              Fundamentação (obrigatória — vai pro livro-razão)
            </label>
            <textarea
              id="rationale"
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              rows={4}
              minLength={3}
              required
              placeholder="ex.: alias fraco, data de nascimento distinta, documento não confere…"
              className="w-full rounded border border-border bg-background px-3 py-2 text-sm"
            />
          </div>
          {submitError && (
            <div className="rounded border border-destructive/40 bg-destructive/5 p-3 text-xs text-destructive">
              {submitError}
            </div>
          )}
          <button
            type="submit"
            disabled={submitting || rationale.trim().length < 3}
            className="rounded border border-border px-4 py-2 text-sm hover:bg-accent disabled:opacity-50"
          >
            {submitting ? 'registrando…' : 'registrar disposição'}
          </button>
          <p className="text-xs text-muted-foreground">
            Append-only: grava um registro novo encadeado por hash. Nunca altera o original.
          </p>
        </form>
      )}
    </div>
  );
}
