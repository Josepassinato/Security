import { describe, expect, it } from 'vitest';
import {
  TOTAL_SECONDS,
  REGULATORY_ARTIFACTS,
  FINDINGS,
  MITRE_CELLS,
  getDemoState,
} from './cinematicScenario';
import { buildBacenCommunication, buildBacenFilename } from './bacenReport';

const FIXED_NOW = new Date('2026-05-23T14:00:00-03:00');

describe('buildBacenCommunication', () => {
  it('returns a non-empty markdown document with the canonical headers', () => {
    const state = getDemoState(TOTAL_SECONDS);
    const md = buildBacenCommunication({ state, now: FIXED_NOW });
    expect(md.length).toBeGreaterThan(500);
    expect(md).toMatch(/^# Comunicação imediata de incidente cibernético — Bacen/);
    expect(md).toContain('## 1. Classificação do incidente');
    expect(md).toContain('## 4. Controles regulatórios ativados');
    expect(md).toContain('## 8. Cadeia probatória e continuidade');
  });

  it('cites the 24h regulatory deadline anchored to the provided clock', () => {
    const state = getDemoState(TOTAL_SECONDS);
    const md = buildBacenCommunication({ state, now: FIXED_NOW });
    expect(md).toContain('Res. BCB 85/2021, Art. 9');
    expect(md).toContain('Prazo regulatório de comunicação (24h)');
    expect(md).toMatch(/24\/05\/2026 14:00 \(BRT\)/);
  });

  it('renders all five regulatory artifacts and marks satisfied ones with [x]', () => {
    const state = getDemoState(TOTAL_SECONDS);
    const md = buildBacenCommunication({ state, now: FIXED_NOW });
    for (const artifact of REGULATORY_ARTIFACTS) {
      expect(md).toContain(artifact.norma);
      expect(md).toContain(artifact.titulo);
    }
    const satisfiedCount = (md.match(/- \[x\]/g) ?? []).length;
    expect(satisfiedCount).toBe(REGULATORY_ARTIFACTS.length);
  });

  it('partial-state document marks unsatisfied artifacts with [ ]', () => {
    const state = getDemoState(60);
    const md = buildBacenCommunication({ state, now: FIXED_NOW });
    expect(md).toMatch(/- \[ \]/);
    expect(md).toMatch(/- \[x\]/);
  });

  it('includes the financial impact in BRL and the investigation scale', () => {
    const state = getDemoState(TOTAL_SECONDS);
    const md = buildBacenCommunication({ state, now: FIXED_NOW });
    expect(md).toMatch(/R\$\s/);
    expect(md).toContain('transações varridas');
    expect(md).toContain('contas correlacionadas');
  });

  it('lists every finding and every MITRE cell', () => {
    const state = getDemoState(TOTAL_SECONDS);
    const md = buildBacenCommunication({ state, now: FIXED_NOW });
    for (const f of FINDINGS) {
      expect(md).toContain(f.title);
      // Evidence may contain `|` which we escape in the markdown table.
      expect(md).toContain(f.evidence.replace(/\|/g, '\\|'));
    }
    for (const cell of MITRE_CELLS) {
      expect(md).toContain(cell.tactic);
      expect(md).toContain(cell.technique);
    }
  });

  it('escapes pipe characters inside table cells so markdown tables stay valid', () => {
    const state = getDemoState(TOTAL_SECONDS);
    const md = buildBacenCommunication({ state, now: FIXED_NOW });
    // No unescaped pipe should appear inside the evidence table rows.
    const evidenceRows = md
      .split('\n')
      .filter((l) => l.startsWith('| ') && /Crítico|Alto|Médio/.test(l));
    expect(evidenceRows.length).toBeGreaterThan(0);
    for (const row of evidenceRows) {
      // Strip escaped pipes, then count remaining pipes — should be exactly 5 (4 columns + borders).
      const pipes = row.replace(/\\\|/g, '').match(/\|/g) ?? [];
      expect(pipes.length).toBe(5);
    }
  });

  it('cites LGPD and IN BCB 314 in addition to Res. BCB 85/2021', () => {
    const state = getDemoState(TOTAL_SECONDS);
    const md = buildBacenCommunication({ state, now: FIXED_NOW });
    expect(md).toContain('LGPD');
    expect(md).toContain('IN BCB 314');
    expect(md).toContain('Res. BCB 85/2021');
  });

  it('honors custom institution name, CNPJ, and caseId', () => {
    const state = getDemoState(TOTAL_SECONDS);
    const md = buildBacenCommunication({
      state,
      now: FIXED_NOW,
      institutionName: 'Acme Bank Digital',
      institutionCnpj: '12.345.678/0001-99',
      caseId: 'CASE-XYZ-001',
    });
    expect(md).toContain('Acme Bank Digital');
    expect(md).toContain('12.345.678/0001-99');
    expect(md).toContain('CASE-XYZ-001');
  });
});

describe('buildBacenFilename', () => {
  it('produces a filename with date and time slug ending in .md', () => {
    const name = buildBacenFilename(FIXED_NOW);
    expect(name).toMatch(/^bacen-24h-2026052[34]-\d{4}\.md$/);
  });
});
