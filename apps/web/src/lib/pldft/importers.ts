import type { PldInput, PldTransaction } from './engine';

function splitCsvLine(line: string): string[] {
  const values: string[] = [];
  let current = '';
  let quoted = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    const next = line[i + 1];
    if (char === '"' && quoted && next === '"') {
      current += '"';
      i += 1;
      continue;
    }
    if (char === '"') {
      quoted = !quoted;
      continue;
    }
    if (char === ',' && !quoted) {
      values.push(current.trim());
      current = '';
      continue;
    }
    current += char;
  }
  values.push(current.trim());
  return values;
}

function normalizeHeader(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, '_');
}

function requireField(row: Record<string, string>, name: string, index: number): string {
  const value = row[name];
  if (!value) {
    throw new Error(`Linha ${index + 2}: campo obrigatório ausente: ${name}.`);
  }
  return value;
}

function parseAmount(value: string, index: number): number {
  const normalized = value.replace(/\./g, '').replace(',', '.').replace(/[^\d.-]/g, '');
  const amount = Number(normalized);
  if (!Number.isFinite(amount)) {
    throw new Error(`Linha ${index + 2}: valor inválido em amount.`);
  }
  return amount;
}

export function parsePldCsv(text: string, institution = 'Instituição financeira'): PldInput {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) {
    throw new Error('CSV precisa ter cabeçalho e pelo menos uma transação.');
  }

  const headers = splitCsvLine(lines[0]).map(normalizeHeader);
  const transactions: PldTransaction[] = lines.slice(1).map((line, index) => {
    const cells = splitCsvLine(line);
    const row = Object.fromEntries(headers.map((header, i) => [header, cells[i] || '']));
    const direction = requireField(row, 'direction', index).toLowerCase();
    if (direction !== 'in' && direction !== 'out') {
      throw new Error(`Linha ${index + 2}: direction deve ser "in" ou "out".`);
    }

    return {
      id: requireField(row, 'id', index),
      timestamp: requireField(row, 'timestamp', index),
      accountId: requireField(row, 'accountid', index),
      customerId: requireField(row, 'customerid', index),
      direction,
      rail: (row.rail || 'Outro') as PldTransaction['rail'],
      amount: parseAmount(requireField(row, 'amount', index), index),
      counterpartyId: requireField(row, 'counterpartyid', index),
      counterpartyName: row.counterpartyname,
      counterpartyDocument: row.counterpartydocument,
      deviceId: row.deviceid,
      ip: row.ip,
      city: row.city,
      country: row.country || 'BR',
      status: row.status,
      tags: row.tags ? row.tags.split(/[|;]/).map((tag) => tag.trim()).filter(Boolean) : undefined,
    };
  });

  return {
    institution,
    generatedAt: new Date().toISOString(),
    transactions,
  };
}

export const pldCsvTemplate = [
  'id,timestamp,accountId,customerId,direction,rail,amount,counterpartyId,counterpartyName,deviceId,ip,country,tags',
  'TX-1,2026-05-30T09:00:00-03:00,ACC-1,CUST-1,in,Pix,12000,REM-1,Remetente A,DEV-1,177.10.20.41,BR,',
  'TX-2,2026-05-30T09:15:00-03:00,ACC-1,CUST-1,out,Pix,9800,ACC-2,Favorecido B,DEV-1,177.10.20.41,BR,',
].join('\n');
