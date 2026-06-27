/**
 * validate.ts — Tarefa 2: valida o adapter em N linhas reais do Trans.csv.
 * Uso: tsx validate.ts <Trans.csv> <accounts.csv> [N=10000] [mode=honest]
 * Não roda o motor; só mede se o mapeamento IBM→PldTransaction está sadio.
 */
import { createReadStream } from 'node:fs';
import { createInterface } from 'node:readline';
import { loadAccounts } from './io';
import { parseIbmRow, projectRow, type FanoutMode } from './adapter';

async function main() {
  const [transPath, accountsPath, nArg, modeArg] = process.argv.slice(2);
  const N = Number(nArg) || 10000;
  const mode = (modeArg as FanoutMode) || 'honest';

  console.log(`Carregando accounts.csv …`);
  const accounts = await loadAccounts(accountsPath);
  console.log(`  entidades mapeadas (account→entity): ${accounts.size.toLocaleString()}`);

  const resolve = (acct: string) => accounts.get(acct) || acct;

  let parsed = 0, badParse = 0, selfLoops = 0, unknownCcy = 0, txEmitted = 0;
  let laundering = 0, resolvedEntity = 0, unresolvedEntity = 0;
  const railDist: Record<string, number> = {};
  const ccyDist: Record<string, number> = {};
  const fmtDist: Record<string, number> = {};

  const rl = createInterface({ input: createReadStream(transPath), crlfDelay: Infinity });
  let first = true, i = 0;
  for await (const line of rl) {
    if (first) { first = false; continue; }
    if (i >= N) break;
    i++;
    const row = parseIbmRow(line);
    if (!row) { badParse++; continue; }
    parsed++;
    fmtDist[row.paymentFormat] = (fmtDist[row.paymentFormat] || 0) + 1;
    ccyDist[row.paymentCurrency] = (ccyDist[row.paymentCurrency] || 0) + 1;
    if (row.isLaundering) laundering++;
    if (accounts.has(row.fromAccount.trim())) resolvedEntity++; else unresolvedEntity++;

    const proj = projectRow(row, i, resolve, mode);
    if (proj.selfLoop) selfLoops++;
    if (proj.unknownCurrency) unknownCcy++;
    txEmitted += proj.txs.length;
    for (const tx of proj.txs) railDist[tx.rail] = (railDist[tx.rail] || 0) + 1;
  }

  const pct = (x: number, base: number) => base ? `${((x / base) * 100).toFixed(2)}%` : '—';
  console.log(`\n=== Validação em ${i} linhas (modo: ${mode}) ===`);
  console.log(`linhas parseadas ok ........ ${parsed}  (falhas: ${badParse})`);
  console.log(`self-loops (From==To) ...... ${selfLoops}  (${pct(selfLoops, parsed)})`);
  console.log(`moeda desconhecida (fallback) ${unknownCcy}  (${pct(unknownCcy, parsed)})`);
  console.log(`entidade resolvida (from) .. ${resolvedEntity}  (${pct(resolvedEntity, parsed)})`);
  console.log(`  não resolvida (usa account) ${unresolvedEntity}  (${pct(unresolvedEntity, parsed)})`);
  console.log(`transações lavagem (label=1) ${laundering}  (${pct(laundering, parsed)})`);
  console.log(`PldTransaction emitidas .... ${txEmitted}`);
  console.log(`\nPayment Format:`, fmtDist);
  console.log(`Moeda:`, ccyDist);
  console.log(`Rail mapeado:`, railDist);
}

main().catch((e) => { console.error(e); process.exit(1); });
