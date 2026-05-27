/**
 * Tests for EvidencePacksView — CARD-016 admin panel.
 *
 * Verifies the UI surface that operators see when working with sealed
 * Bacen Evidence Packs. The mock-seal warning is the most important
 * assertion: per Parecer Jurídico Nº 012/2026 § II.5, a reader must
 * never confuse a mock-sealed bundle for a real one.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// ─── SWR mock (keyed cache, matches the project convention) ────────────────

const swrData = vi.hoisted(() => new Map<string, unknown>());
const swrErrors = vi.hoisted(() => new Map<string, unknown>());
const swrLoadingKeys = vi.hoisted(() => new Set<string>());
const swrMutate = vi.hoisted(() => vi.fn());

vi.mock('swr', () => ({
  __esModule: true,
  default: (key: unknown) => {
    const k = typeof key === 'string' ? key : JSON.stringify(key);
    return {
      data: swrData.get(k),
      error: swrErrors.get(k),
      isLoading: swrLoadingKeys.has(k),
      mutate: swrMutate,
    };
  },
}));

// ─── Fetch mock for the compile POST ───────────────────────────────────────

const fetchMock = vi.fn();

beforeEach(() => {
  swrData.clear();
  swrErrors.clear();
  swrLoadingKeys.clear();
  swrMutate.mockReset();
  fetchMock.mockReset();
  // @ts-expect-error — global stub
  global.fetch = fetchMock;
});

// Component imports MUST come after the mocks above.
import { EvidencePacksView } from './EvidencePacksView';

// ─── Test fixtures ─────────────────────────────────────────────────────────

const PACKS_KEY = '/api/v1/evidence-packs';

const SAMPLE_LIST = {
  count: 2,
  packs: [
    {
      pack_id: 'bcb-85-2021-art-6',
      regulation_code: 'BCB-85-2021',
      article: 'Art. 6º',
      title: 'Plano de resposta a incidentes',
      reporting_period: '90d',
      output_format: 'BCB_RFI_v1',
    },
    {
      pack_id: 'lgpd-art-48-anpd-res-15-2024',
      regulation_code: 'LGPD-13709-2018',
      article: 'Art. 48 c/c Res. CD/ANPD 15/2024',
      title: 'Comunicação de incidente à ANPD',
      reporting_period: 'point_in_time',
      output_format: 'ANPD_incident_res_15_2024',
    },
  ],
};

function fakeBundle(overrides: Record<string, unknown> = {}) {
  return {
    pack_id: 'bcb-85-2021-art-6',
    generated_at: '2026-05-27T03:19:29Z',
    window_start: '2026-02-26T03:19:29Z',
    window_end: '2026-05-27T03:19:29Z',
    data: {},
    data_digest_hex: 'a'.repeat(64),
    timestamp: {
      tsa_name: 'MockTSA (dev only)',
      stamped_at: '2026-05-27T03:19:29Z',
      token_der_hex: 'deadbeef',
      digest_hex: 'a'.repeat(64),
    },
    signature: {
      signer_subject: 'CN=MOCK SIGNER (dev only), O=Quarry, C=BR',
      signed_at: '2026-05-27T03:19:29Z',
      digest_algorithm: 'SHA-256',
      digest_hex: 'a'.repeat(64),
      signature_der_hex: 'cafebabe',
    },
    hash_chain_entry_hash_hex: 'b'.repeat(64),
    prev_chain_entry_hash_hex: '0'.repeat(64),
    mock_seal: true,
    ...overrides,
  };
}

// ─── Tests ─────────────────────────────────────────────────────────────────

describe('EvidencePacksView', () => {
  it('renders the loading state while the catalog fetch is in flight', () => {
    swrLoadingKeys.add(PACKS_KEY);
    render(<EvidencePacksView />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('renders the empty state when no packs are discovered', () => {
    swrData.set(PACKS_KEY, { count: 0, packs: [] });
    render(<EvidencePacksView />);
    expect(screen.getByText(/no packs found/i)).toBeInTheDocument();
  });

  it('lists every discovered pack with regulation + article + period', () => {
    swrData.set(PACKS_KEY, SAMPLE_LIST);
    render(<EvidencePacksView />);

    // Both pack titles render
    expect(screen.getByText('Plano de resposta a incidentes')).toBeInTheDocument();
    expect(
      screen.getByText('Comunicação de incidente à ANPD'),
    ).toBeInTheDocument();

    // Pack IDs render in mono
    expect(screen.getByText('bcb-85-2021-art-6')).toBeInTheDocument();
    expect(screen.getByText('lgpd-art-48-anpd-res-15-2024')).toBeInTheDocument();

    // The period label gets humanized
    expect(screen.getByText(/last 90 days/i)).toBeInTheDocument();
    expect(screen.getByText(/point in time/i)).toBeInTheDocument();
  });

  it('shows the MOCK SEAL warning when the compiled bundle is mock-sealed', async () => {
    swrData.set(PACKS_KEY, SAMPLE_LIST);
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeBundle({ mock_seal: true })),
    });

    render(<EvidencePacksView />);
    const compileBtn = screen.getAllByRole('button', { name: /compile/i })[0];
    await userEvent.click(compileBtn);

    // The amber-bordered banner asserting MOCK SEAL must be visible.
    // Per Parecer 012/2026 § II.5 — this is the operator's last
    // visual reminder before sending the PDF to a regulator.
    expect(
      await screen.findByText(/MOCK SEAL.*dev only/i),
    ).toBeInTheDocument();
  });

  it('omits the MOCK SEAL banner for production-sealed bundles', async () => {
    swrData.set(PACKS_KEY, SAMPLE_LIST);
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeBundle({ mock_seal: false })),
    });

    render(<EvidencePacksView />);
    const compileBtn = screen.getAllByRole('button', { name: /compile/i })[0];
    await userEvent.click(compileBtn);

    // Wait for the bundle section to appear (pack_id heading)
    await screen.findByText('last compiled bundle');
    expect(screen.queryByText(/MOCK SEAL/i)).not.toBeInTheDocument();
  });

  it('surfaces a fetch error message when the compile call fails', async () => {
    swrData.set(PACKS_KEY, SAMPLE_LIST);
    fetchMock.mockResolvedValueOnce({ ok: false, status: 500 });

    render(<EvidencePacksView />);
    const compileBtn = screen.getAllByRole('button', { name: /compile/i })[0];
    await userEvent.click(compileBtn);

    expect(await screen.findByText(/HTTP 500/i)).toBeInTheDocument();
  });

  it('renders an error banner when the catalog fetch itself fails', () => {
    swrErrors.set(PACKS_KEY, new Error('network down'));
    render(<EvidencePacksView />);
    expect(screen.getByText(/failed to load packs/i)).toBeInTheDocument();
    expect(screen.getByText(/network down/i)).toBeInTheDocument();
  });
});
