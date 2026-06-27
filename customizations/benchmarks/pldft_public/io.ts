/**
 * io.ts — leitura dos arquivos auxiliares do IBM AML.
 *  - loadAccounts: Account Number → Entity ID (resolução de dono beneficiário)
 *  - loadPatterns: assinatura de transação → tipologia de lavagem (ground-truth por tipo)
 */
import { createReadStream } from 'node:fs';
import { createInterface } from 'node:readline';

/** accounts.csv: Bank Name,Bank ID,Account Number,Entity ID,Entity Name */
export async function loadAccounts(path: string): Promise<Map<string, string>> {
  const map = new Map<string, string>();
  const rl = createInterface({ input: createReadStream(path), crlfDelay: Infinity });
  let first = true;
  for await (const line of rl) {
    if (first) { first = false; continue; }
    if (!line) continue;
    const c = line.split(',');
    if (c.length < 4) continue;
    const account = c[2]?.trim();
    const entity = c[3]?.trim();
    if (account && entity) map.set(account, entity);
  }
  return map;
}

export interface PatternSignature {
  typology: string;          // FAN-OUT, FAN-IN, CYCLE, GATHER-SCATTER, SCATTER-GATHER, STACK, ...
}

/**
 * Patterns.txt: blocos delimitados por
 *   BEGIN LAUNDERING ATTEMPT - <TYPE>: <desc>
 *   <linhas de transação no mesmo formato do Trans.csv, isLaundering=1>
 *   END LAUNDERING ATTEMPT - <TYPE>
 *
 * Chave da assinatura = "timestamp|fromAcct|toAcct|amountPaid" (col 0,2,4,7).
 * Retorna mapa assinatura → tipologia.
 */
export async function loadPatterns(path: string): Promise<Map<string, string>> {
  const map = new Map<string, string>();
  const rl = createInterface({ input: createReadStream(path), crlfDelay: Infinity });
  let typology = 'UNKNOWN';
  for await (const line of rl) {
    const begin = line.match(/^BEGIN LAUNDERING ATTEMPT\s*-\s*([A-Z-]+)/i);
    if (begin) { typology = begin[1].toUpperCase(); continue; }
    if (/^END LAUNDERING ATTEMPT/i.test(line)) { typology = 'UNKNOWN'; continue; }
    const c = line.split(',');
    if (c.length < 11) continue;
    const sig = patternSignature(c[0], c[2], c[4], c[7]);
    map.set(sig, typology);
  }
  return map;
}

export function patternSignature(ts: string, fromAcct: string, toAcct: string, amountPaid: string): string {
  return `${ts.trim()}|${fromAcct.trim()}|${toAcct.trim()}|${amountPaid.trim()}`;
}
