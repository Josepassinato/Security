import { describe, expect, it } from 'vitest';
import { analyzePldFt, pldDossierToMarkdown } from './engine';
import { samplePldInput } from './sample';

describe('PLD/FT deterministic engine', () => {
  it('detects high-risk mule and pass-through behavior in the sample dataset', () => {
    const dossier = analyzePldFt(samplePldInput);

    expect(dossier.riskScore).toBeGreaterThanOrEqual(85);
    expect(dossier.severity).toBe('critical');
    expect(dossier.findings.map((finding) => finding.ruleId)).toContain('PLD-PIX-001');
    expect(dossier.findings.map((finding) => finding.ruleId)).toContain('PLD-DEV-006');
    expect(dossier.suspiciousAmount).toBeGreaterThan(0);
    expect(dossier.disclaimer).toContain('não declara crime');
  });

  it('keeps clean recurring payroll-like flows below review threshold', () => {
    const dossier = analyzePldFt({
      institution: 'Banco limpo',
      generatedAt: '2026-05-30T12:00:00-03:00',
      customers: [
        {
          customerId: 'CLEAN-01',
          name: 'Empresa limpa',
          accountAgeDays: 900,
          declaredMonthlyRevenue: 150000,
          customerType: 'PJ',
        },
      ],
      transactions: [
        {
          id: 'OK-1',
          timestamp: '2026-05-30T10:00:00-03:00',
          accountId: 'ACC-CLEAN',
          customerId: 'CLEAN-01',
          direction: 'out',
          rail: 'TED',
          amount: 4200,
          counterpartyId: 'PAYROLL-01',
          counterpartyName: 'Folha de pagamento',
          deviceId: 'DEVICE-CORP',
        },
        {
          id: 'OK-2',
          timestamp: '2026-05-30T11:00:00-03:00',
          accountId: 'ACC-CLEAN',
          customerId: 'CLEAN-01',
          direction: 'out',
          rail: 'Boleto',
          amount: 1800,
          counterpartyId: 'SUPPLIER-01',
          counterpartyName: 'Fornecedor recorrente',
          deviceId: 'DEVICE-CORP',
        },
      ],
    });

    expect(dossier.riskScore).toBe(0);
    expect(dossier.severity).toBe('low');
    expect(dossier.findings).toHaveLength(0);
  });

  it('exports a markdown dossier with evidence and analyst checklist', () => {
    const dossier = analyzePldFt(samplePldInput);
    const markdown = pldDossierToMarkdown(dossier);

    expect(markdown).toContain('# Dossiê PLD/FT');
    expect(markdown).toContain('## Achados');
    expect(markdown).toContain('## Checklist do analista');
    expect(markdown).toContain('PLD-PIX-001');
  });

  it('allows specialist-calibrated thresholds without changing rule code', () => {
    const dossier = analyzePldFt({
      ...samplePldInput,
      thresholds: {
        passThroughMinAmount: 1000000,
        outboundFanoutMinTotal: 1000000,
        multiVictimMinInboundTotal: 1000000,
        deviceReuseMinCustomers: 20,
      },
    });

    expect(dossier.findings.map((finding) => finding.ruleId)).not.toContain('PLD-PIX-001');
    expect(dossier.findings.map((finding) => finding.ruleId)).not.toContain('PLD-DEV-006');
  });
});
