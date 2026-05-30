import { describe, expect, it } from 'vitest';
import { parsePldCsv, pldCsvTemplate } from './importers';

describe('PLD/FT importers', () => {
  it('parses the CSV template into PLD transactions', () => {
    const input = parsePldCsv(pldCsvTemplate, 'CSV Bank');

    expect(input.institution).toBe('CSV Bank');
    expect(input.transactions).toHaveLength(2);
    expect(input.transactions[0].direction).toBe('in');
    expect(input.transactions[1].amount).toBe(9800);
  });

  it('rejects CSV without mandatory fields', () => {
    expect(() => parsePldCsv('id,amount\nA,10')).toThrow(/campo obrigatório/);
  });
});
