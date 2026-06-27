/**
 * run_benchmark.ts — Tarefas 3+4: roda o motor PLD/FT do Quarry contra o IBM AML
 * e pontua contra o label `Is Laundering` + tipologias do Patterns.txt.
 *
 * Pipeline (memória limitada, escala até o Medium):
 *   1. prepare  — stream Trans.csv → projeta cada linha (in/out) → prepared.tsv keyed por entidade
 *   2. sort     — `sort` em disco por entidade (não segura tudo na RAM)
 *   3. run      — stream sorted.tsv, agrupa por entidade, chama analyzePldFt() por entidade
 *   4. score    — recall/precision por entidade, por tipologia e por regra → report.md
 *
 * NÃO modifica o motor (apps/web/src/lib/pldft/engine.ts) — só importa.
 *
 * Uso:
 *   tsx run_benchmark.ts <Trans.csv> <accounts.csv> <Patterns.txt> <outDir> [mode=honest|generalized]
 */
import { createReadStream, createWriteStream, mkdirSync, writeFileSync } from 'node:fs';
import { createInterface } from 'node:readline';
import { execFileSync } from 'node:child_process';
import { once } from 'node:events';
import {
  analyzePldFt,
  defaultPldThresholds,
  type PldTransaction,
  type PldThresholds,
} from '../../../apps/web/src/lib/pldft/engine';
import { loadAccounts, loadPatterns, patternSignature } from './io';
import { parseIbmRow, projectRow, type FanoutMode, BRL_PER_USD } from './adapter';

const MAX_ENTITY_TXS = 60000; // hub guard: entidades acima disso são logadas e puladas (não são mule)

/** Thresholds do motor (BRL) → USD-equivalente pra rodar sobre valores convertidos. */
function usdThresholds(): Partial<PldThresholds> {
  const d = defaultPldThresholds;
  const r = BRL_PER_USD;
  return {
    passThroughMinAmount: d.passThroughMinAmount / r,
    outboundFanoutMinTotal: d.outboundFanoutMinTotal / r,
    multiVictimMinInboundTotal: d.multiVictimMinInboundTotal / r,
    economicMismatchMinAmount: d.economicMismatchMinAmount / r,
    newAccountLargeSendMinAmount: d.newAccountLargeSendMinAmount / r,
    structuringMinSingleAmount: d.structuringMinSingleAmount / r,
    structuringMaxSingleAmount: d.structuringMaxSingleAmount / r,
    structuringMinTotal: d.structuringMinTotal / r,
    cryptoAdjacencyMinAmount: d.cryptoAdjacencyMinAmount / r,
  };
}

function rowIndexFromTxId(txId: string): number {
  // formato IBM-<index>-o|i
  const m = txId.match(/^IBM-(\d+)-/);
  return m ? Number(m[1]) : -1;
}

async function prepare(
  transPath: string,
  accountsPath: string,
  patternsPath: string,
  preparedPath: string,
  mode: FanoutMode,
) {
  console.log('[prepare] carregando accounts + patterns…');
  const accounts = await loadAccounts(accountsPath);
  const patterns = await loadPatterns(patternsPath);
  const resolve = (acct: string) => accounts.get(acct) || acct;

  // rowIndex (de linha lavadora) → tipologia, pra scoring por tipo.
  const launderingTypology = new Map<number, string>();
  const dirtyEntities = new Set<string>();

  const out = createWriteStream(preparedPath);
  const rl = createInterface({ input: createReadStream(transPath), crlfDelay: Infinity });
  let first = true, idx = 0, written = 0, selfLoops = 0, launderTx = 0;

  for await (const line of rl) {
    if (first) { first = false; continue; }
    if (!line) continue;
    idx++;
    const row = parseIbmRow(line);
    if (!row) continue;

    if (row.isLaundering) {
      const sig = patternSignature(row.timestamp, row.fromAccount, row.toAccount, String(row.amountPaid));
      launderingTypology.set(idx, patterns.get(sig) || 'UNLABELED');
    }

    const proj = projectRow(row, idx, resolve, mode);
    if (proj.selfLoop) { selfLoops++; continue; }
    for (const tx of proj.txs) {
      if (tx.isLaundering) { launderTx++; dirtyEntities.add(tx.customerId); }
      // colunas: customerId, txId, timestamp, direction, rail, amount, counterpartyId, accountId, isLaundering
      const rec = `${tx.customerId}\t${tx.id}\t${tx.timestamp}\t${tx.direction}\t${tx.rail}\t${tx.amount}\t${tx.counterpartyId}\t${tx.accountId}\t${tx.isLaundering}\n`;
      if (!out.write(rec)) await once(out, 'drain');
      written++;
    }
    if (idx % 1_000_000 === 0) console.log(`[prepare] ${idx.toLocaleString()} linhas…`);
  }
  out.end();
  await once(out, 'finish');
  console.log(`[prepare] linhas=${idx} self-loops=${selfLoops} txEmitidas=${written} txLavagem=${launderTx} entidadesSujas=${dirtyEntities.size}`);
  return { launderingTypology, dirtyEntities, totalRows: idx, launderTx };
}

interface RunAcc {
  findingsByRule: Map<string, number>;
  caughtLaunderTxByRule: Map<string, Set<string>>;
  flaggedEntities: Set<string>;
  caughtLaunderTx: Set<string>;        // txIds lavagem cobertos por algum finding
  caughtLaunderRowIdx: Set<number>;    // rowIndex lavagem coberto (pra tipologia)
  sweptTx: number;                     // total de txIds varridos por findings (denominador de precisão-tx)
  entitiesAnalyzed: number;
  entitiesSkippedHub: number;
}

function processEntity(
  customerId: string,
  lines: string[],
  thresholds: Partial<PldThresholds>,
  launderingTypology: Map<number, string>,
  acc: RunAcc,
) {
  if (lines.length > MAX_ENTITY_TXS) {
    acc.entitiesSkippedHub++;
    console.log(`[run] HUB pulado: ${customerId} com ${lines.length} txs (> ${MAX_ENTITY_TXS})`);
    return;
  }
  const transactions: PldTransaction[] = lines.map((l) => {
    const c = l.split('\t');
    return {
      id: c[1], timestamp: c[2], accountId: c[7], customerId: c[0],
      direction: c[3] as 'in' | 'out', rail: c[4] as PldTransaction['rail'],
      amount: Number(c[5]), counterpartyId: c[6],
    };
  });
  const dossier = analyzePldFt({ transactions, thresholds });
  if (!dossier.findings.length) return;

  acc.entitiesAnalyzed++; // só conta entidade que gerou ao menos 1 finding como "flagada"
  acc.flaggedEntities.add(customerId);

  for (const f of dossier.findings) {
    acc.findingsByRule.set(f.ruleId, (acc.findingsByRule.get(f.ruleId) || 0) + 1);
    for (const txId of f.transactionIds) {
      acc.sweptTx++;
      // a tx é lavagem? (label viaja no rowIndex)
      const ix = rowIndexFromTxId(txId);
      if (ix >= 0 && launderingTypology.has(ix)) {
        acc.caughtLaunderTx.add(txId);
        acc.caughtLaunderRowIdx.add(ix);
        if (!acc.caughtLaunderTxByRule.has(f.ruleId)) acc.caughtLaunderTxByRule.set(f.ruleId, new Set());
        acc.caughtLaunderTxByRule.get(f.ruleId)!.add(txId);
      }
    }
  }
}

async function run(
  sortedPath: string,
  thresholds: Partial<PldThresholds>,
  launderingTypology: Map<number, string>,
): Promise<RunAcc> {
  const acc: RunAcc = {
    findingsByRule: new Map(), caughtLaunderTxByRule: new Map(),
    flaggedEntities: new Set(), caughtLaunderTx: new Set(), caughtLaunderRowIdx: new Set(),
    sweptTx: 0, entitiesAnalyzed: 0, entitiesSkippedHub: 0,
  };
  const rl = createInterface({ input: createReadStream(sortedPath), crlfDelay: Infinity });
  let current = '', buf: string[] = [], groups = 0;
  for await (const line of rl) {
    if (!line) continue;
    const tab = line.indexOf('\t');
    const cid = line.slice(0, tab);
    if (cid !== current) {
      if (buf.length) { processEntity(current, buf, thresholds, launderingTypology, acc); groups++; }
      current = cid; buf = [];
    }
    buf.push(line);
  }
  if (buf.length) { processEntity(current, buf, thresholds, launderingTypology, acc); groups++; }
  console.log(`[run] entidades processadas=${groups} comFinding=${acc.flaggedEntities.size} hubsPulados=${acc.entitiesSkippedHub}`);
  return acc;
}

function score(
  acc: RunAcc,
  prep: { launderingTypology: Map<number, string>; dirtyEntities: Set<string>; totalRows: number; launderTx: number },
  mode: FanoutMode,
  outDir: string,
) {
  // ENTIDADE: suja = tem ≥1 tx lavagem; flagada = gerou ≥1 finding.
  let tpEntity = 0;
  for (const e of acc.flaggedEntities) if (prep.dirtyEntities.has(e)) tpEntity++;
  const recallEntity = prep.dirtyEntities.size ? tpEntity / prep.dirtyEntities.size : 0;
  const precisionEntity = acc.flaggedEntities.size ? tpEntity / acc.flaggedEntities.size : 0;

  // TIPOLOGIA: dos rowIndex lavadores de cada tipo, quantos cobertos.
  const typTotal = new Map<string, number>(), typCaught = new Map<string, number>();
  for (const [ix, typ] of prep.launderingTypology) {
    typTotal.set(typ, (typTotal.get(typ) || 0) + 1);
    if (acc.caughtLaunderRowIdx.has(ix)) typCaught.set(typ, (typCaught.get(typ) || 0) + 1);
  }

  // TX-level: recall e precision (precision baixa esperada — entidade varre txs limpas junto).
  const launderRowsCaught = acc.caughtLaunderRowIdx.size;
  const recallRowLaunder = prep.launderingTypology.size ? launderRowsCaught / prep.launderingTypology.size : 0;
  const precisionTx = acc.sweptTx ? acc.caughtLaunderTx.size / acc.sweptTx : 0;

  const pct = (x: number) => `${(x * 100).toFixed(1)}%`;
  const lines: string[] = [];
  lines.push(`# Benchmark PLD/FT — Quarry × IBM AML (HI-Small)`);
  lines.push('');
  lines.push(`- **Modo:** ${mode}  ·  **Motor:** apps/web/src/lib/pldft/engine.ts (não modificado)`);
  lines.push(`- **Dataset:** ealtman2019 IBM AML · HI-Small_Trans.csv`);
  lines.push(`- **Transações totais:** ${prep.totalRows.toLocaleString()}`);
  lines.push(`- **Anéis de lavagem (linhas label=1):** ${prep.launderingTypology.size.toLocaleString()}`);
  lines.push(`- **Entidades sujas (≥1 tx lavagem):** ${prep.dirtyEntities.size.toLocaleString()}`);
  lines.push('');
  lines.push(`## Resultado — nível ENTIDADE (o que importa pra um analista)`);
  lines.push(`| métrica | valor |`);
  lines.push(`|---|---|`);
  lines.push(`| Recall (entidades sujas pegas) | **${pct(recallEntity)}** (${tpEntity}/${prep.dirtyEntities.size}) |`);
  lines.push(`| Precision (entidades flagadas que eram sujas) | **${pct(precisionEntity)}** (${tpEntity}/${acc.flaggedEntities.size}) |`);
  lines.push(`| Entidades flagadas no total | ${acc.flaggedEntities.size.toLocaleString()} |`);
  lines.push(`| Hubs pulados (> ${MAX_ENTITY_TXS} txs) | ${acc.entitiesSkippedHub} |`);
  lines.push('');
  lines.push(`## Recall por TIPOLOGIA (cobertura do Patterns.txt)`);
  lines.push(`| tipologia | pego | total | recall |`);
  lines.push(`|---|---|---|---|`);
  for (const typ of [...typTotal.keys()].sort()) {
    const t = typTotal.get(typ)!, c = typCaught.get(typ) || 0;
    lines.push(`| ${typ} | ${c} | ${t} | ${pct(t ? c / t : 0)} |`);
  }
  lines.push('');
  lines.push(`## Por REGRA (quais dispararam e quanta lavagem cada uma pegou)`);
  lines.push(`| regra | nº findings | tx-lavagem cobertas |`);
  lines.push(`|---|---|---|`);
  for (const [rule, n] of [...acc.findingsByRule.entries()].sort((a, b) => b[1] - a[1])) {
    lines.push(`| ${rule} | ${n.toLocaleString()} | ${(acc.caughtLaunderTxByRule.get(rule)?.size || 0).toLocaleString()} |`);
  }
  lines.push('');
  lines.push(`## Nível TRANSAÇÃO (contexto, não a métrica principal)`);
  lines.push(`- Recall (linhas lavagem cobertas): **${pct(recallRowLaunder)}** (${launderRowsCaught}/${prep.launderingTypology.size})`);
  lines.push(`- Precision-tx: **${pct(precisionTx)}** — baixa por construção: um finding varre todas as txs da entidade, inclusive limpas. Use a precisão por ENTIDADE como referência.`);
  lines.push(`- Custo de inferência: **US$ 0,00** (motor determinístico, zero LLM).`);
  lines.push('');
  lines.push(`## Limitações honestas`);
  lines.push(`- IBM AML não tem KYC/idade-de-conta/device/listas → regras PLD-KYC-004/005, PLD-DEV-006, PLD-LIST-008 **não são exercitadas** aqui (ver gerador sintético br-fintech).`);
  lines.push(`- Valores convertidos a USD por tabela FX estática (~2022); thresholds BRL→USD a ${BRL_PER_USD}.`);
  lines.push(`- Modo \`honest\`: PLD-PIX-002 (fan-out) é Pix-only → cego a fan-out ACH/Wire. Rode \`generalized\` pra medir o ganho de generalizar a regra.`);

  const report = lines.join('\n');
  writeFileSync(`${outDir}/report.md`, report);
  writeFileSync(`${outDir}/metrics.json`, JSON.stringify({
    mode, totalRows: prep.totalRows, launderRings: prep.launderingTypology.size,
    dirtyEntities: prep.dirtyEntities.size, flaggedEntities: acc.flaggedEntities.size,
    recallEntity, precisionEntity, recallRowLaunder, precisionTx,
    byTypology: Object.fromEntries([...typTotal.keys()].map(t => [t, { caught: typCaught.get(t) || 0, total: typTotal.get(t) }])),
    byRule: Object.fromEntries([...acc.findingsByRule.entries()].map(([r, n]) => [r, { findings: n, caughtLaunderTx: acc.caughtLaunderTxByRule.get(r)?.size || 0 }])),
  }, null, 2));
  console.log('\n' + report);
}

async function main() {
  const [transPath, accountsPath, patternsPath, outDir, modeArg] = process.argv.slice(2);
  if (!transPath || !accountsPath || !patternsPath || !outDir) {
    console.error('uso: tsx run_benchmark.ts <Trans.csv> <accounts.csv> <Patterns.txt> <outDir> [honest|generalized]');
    process.exit(1);
  }
  const mode = (modeArg as FanoutMode) || 'honest';
  mkdirSync(outDir, { recursive: true });
  const preparedPath = `${outDir}/prepared.tsv`;
  const sortedPath = `${outDir}/sorted.tsv`;

  const t0 = Date.now();
  const prep = await prepare(transPath, accountsPath, patternsPath, preparedPath, mode);

  console.log('[sort] ordenando por entidade em disco…');
  execFileSync('sort', ['-t', '\t', '-k1,1', '-S', '50%', '-o', sortedPath, preparedPath], { stdio: 'inherit' });

  const acc = await run(sortedPath, usdThresholds(), prep.launderingTypology);
  score(acc, prep, mode, outDir);
  console.log(`\n[done] ${((Date.now() - t0) / 1000).toFixed(1)}s`);
}

main().catch((e) => { console.error(e); process.exit(1); });
