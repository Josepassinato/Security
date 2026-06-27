/**
 * adapter.ts — IBM AML (ealtman2019) → schema PldTransaction do motor Quarry PLD/FT.
 *
 * Funções PURAS e testáveis. Sem I/O de rede, sem dependência externa.
 * O motor vive em apps/web/src/lib/pldft/engine.ts e NÃO é modificado.
 *
 * Decisões documentadas (aprovadas 2026-06-24):
 *  - Moeda: normalizar todo `Amount Paid` para USD via tabela FX estática (~2022).
 *  - Entidade: customerId = Entity ID (accounts.csv) — agrupa contas sob o dono.
 *  - Reinvestment / self-loop (From==To): descartado (não é transferência entre partes).
 *  - Fan-out: dois modos — 'honest' (rails reais) e 'generalized' (ACH/Wire→Pix
 *    só pro benchmark, pra MEDIR o ganho de generalizar a regra PLD-PIX-002,
 *    que hoje é Pix-only e portanto cega a fan-out em outros trilhos).
 */

import type { PldTransaction, TransactionRail } from '../../../apps/web/src/lib/pldft/engine';

export type FanoutMode = 'honest' | 'generalized';

/** Taxas estáticas: 1 unidade da moeda = X USD (aprox. 2022, documentado como tal). */
export const FX_TO_USD: Record<string, number> = {
  'US Dollar': 1,
  Euro: 1.05,
  'UK Pound': 1.2,
  'Canadian Dollar': 0.78,
  'Australian Dollar': 0.68,
  'Swiss Franc': 1.04,
  Yuan: 0.145,
  Rupee: 0.012,
  Ruble: 0.016,
  Yen: 0.0072,
  Shekel: 0.29,
  'Mexican Peso': 0.05,
  'Brazil Real': 0.19,
  'Saudi Riyal': 0.27,
  Bitcoin: 20000,
};

/** Câmbio usado pra converter os thresholds BRL do motor → USD-equivalente. */
export const BRL_PER_USD = 5.2;

/** Mapeia Payment Format do IBM → rail do motor. */
export function mapRail(paymentFormat: string, mode: FanoutMode): TransactionRail {
  const fmt = paymentFormat.trim();
  if (fmt === 'Bitcoin') return 'Crypto';
  if (fmt === 'Credit Card') return 'Cartao';
  // Trilhos de transferência: ACH / Wire (e Cheque) são o "Pix-equivalente" doméstico.
  const isTransfer = fmt === 'ACH' || fmt === 'Wire' || fmt === 'Cheque';
  if (mode === 'generalized' && isTransfer) return 'Pix';
  if (fmt === 'Wire' || fmt === 'ACH') return 'TED';
  return 'Outro';
}

export function toUsd(amountPaid: number, currency: string): { usd: number; known: boolean } {
  const rate = FX_TO_USD[currency.trim()];
  if (rate === undefined) return { usd: amountPaid, known: false }; // fallback: trata como USD + sinaliza
  return { usd: amountPaid * rate, known: true };
}

/** Uma linha bruta do HI-*_Trans.csv (11 colunas, com 2 colunas "Account"). */
export interface IbmRow {
  timestamp: string;
  fromBank: string;
  fromAccount: string;
  toBank: string;
  toAccount: string;
  amountReceived: number;
  receivingCurrency: string;
  amountPaid: number;
  paymentCurrency: string;
  paymentFormat: string;
  isLaundering: 0 | 1;
}

/**
 * Parse posicional de uma linha do Trans.csv. As DUAS colunas "Account" têm o
 * mesmo nome no header, então parse por POSIÇÃO, não por nome.
 * Colunas: 0 ts, 1 fromBank, 2 fromAcct, 3 toBank, 4 toAcct, 5 amtRecv,
 *          6 recvCcy, 7 amtPaid, 8 payCcy, 9 payFormat, 10 isLaundering
 */
export function parseIbmRow(line: string): IbmRow | null {
  const c = line.split(',');
  if (c.length < 11) return null;
  return {
    timestamp: c[0],
    fromBank: c[1],
    fromAccount: c[2],
    toBank: c[3],
    toAccount: c[4],
    amountReceived: Number(c[5]) || 0,
    receivingCurrency: c[6],
    amountPaid: Number(c[7]) || 0,
    paymentCurrency: c[8],
    paymentFormat: c[9],
    isLaundering: (c[10]?.trim() === '1' ? 1 : 0) as 0 | 1,
  };
}

/** Timestamp IBM "2022/09/01 00:20" → ISO "2022-09-01T00:20:00". */
export function ibmTimestampToIso(ts: string): string {
  const m = ts.trim().match(/^(\d{4})\/(\d{2})\/(\d{2})\s+(\d{2}):(\d{2})$/);
  if (!m) return ts;
  const [, y, mo, d, h, mi] = m;
  return `${y}-${mo}-${d}T${h}:${mi}:00`;
}

/** Chave de conta usada pra resolver Entity ID (account number é a chave do accounts.csv). */
export function accountKey(account: string): string {
  return account.trim();
}

/**
 * Projeta uma linha IBM em 0..2 PldTransaction (uma por perspectiva: o pagador
 * vê 'out', o recebedor vê 'in'). Descarta self-loop (From==To).
 * `resolve` mapeia account number → entityId (ou o próprio account se desconhecido).
 */
export interface ProjectResult {
  txs: Array<PldTransaction & { customerId: string; isLaundering: 0 | 1 }>;
  selfLoop: boolean;
  unknownCurrency: boolean;
}

export function projectRow(
  row: IbmRow,
  index: number,
  resolve: (account: string) => string,
  mode: FanoutMode,
): ProjectResult {
  const fromEntity = resolve(accountKey(row.fromAccount));
  const toEntity = resolve(accountKey(row.toAccount));
  if (fromEntity === toEntity) {
    return { txs: [], selfLoop: true, unknownCurrency: false };
  }
  const { usd, known } = toUsd(row.amountPaid, row.paymentCurrency);
  const iso = ibmTimestampToIso(row.timestamp);
  const rail = mapRail(row.paymentFormat, mode);
  const id = `IBM-${index}`;

  const outTx = {
    id: `${id}-o`,
    timestamp: iso,
    accountId: `${row.fromBank}:${row.fromAccount}`,
    customerId: fromEntity,
    direction: 'out' as const,
    rail,
    amount: usd,
    counterpartyId: toEntity,
    counterpartyName: toEntity,
    country: 'XX',
    isLaundering: row.isLaundering,
  };
  const inTx = {
    id: `${id}-i`,
    timestamp: iso,
    accountId: `${row.toBank}:${row.toAccount}`,
    customerId: toEntity,
    direction: 'in' as const,
    rail,
    amount: usd,
    counterpartyId: fromEntity,
    counterpartyName: fromEntity,
    country: 'XX',
    isLaundering: row.isLaundering,
  };
  return { txs: [outTx, inTx], selfLoop: false, unknownCurrency: !known };
}
