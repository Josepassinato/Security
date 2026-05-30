import { describe, expect, it } from 'vitest';
import { pldScenarios, runSyntheticBenchmark } from './scenarios';

describe('PLD/FT scenarios and benchmark', () => {
  it('provides ready-to-run scenarios for the lab', () => {
    expect(pldScenarios.length).toBeGreaterThanOrEqual(5);
    expect(pldScenarios.map((scenario) => scenario.id)).toContain('fluxo-limpo');
  });

  it('runs a deterministic synthetic benchmark', () => {
    const rows = runSyntheticBenchmark();

    expect(rows).toHaveLength(pldScenarios.length);
    expect(rows.every((row) => typeof row.riskScore === 'number')).toBe(true);
    expect(rows.some((row) => row.actualSeverity === 'critical')).toBe(true);
  });
});
