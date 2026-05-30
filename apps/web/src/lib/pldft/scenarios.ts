import { analyzePldFt, type PldInput } from './engine';
import { samplePldInput } from './sample';

export interface PldScenario {
  id: string;
  name: string;
  description: string;
  expectedSeverity: 'low' | 'medium' | 'high' | 'critical';
  input: PldInput;
}

const cleanFlow: PldInput = {
  institution: 'Banco Limpo S.A.',
  generatedAt: '2026-05-30T12:00:00-03:00',
  customers: [
    {
      customerId: 'CLEAN-PJ-01',
      name: 'Empresa recorrente',
      customerType: 'PJ',
      accountAgeDays: 1200,
      declaredMonthlyRevenue: 280000,
    },
  ],
  transactions: [
    {
      id: 'CLEAN-1',
      timestamp: '2026-05-30T09:00:00-03:00',
      accountId: 'ACC-CLEAN',
      customerId: 'CLEAN-PJ-01',
      direction: 'out',
      rail: 'TED',
      amount: 8200,
      counterpartyId: 'PAYROLL-01',
      counterpartyName: 'Folha de pagamento',
      deviceId: 'DEV-CORP',
    },
    {
      id: 'CLEAN-2',
      timestamp: '2026-05-30T10:00:00-03:00',
      accountId: 'ACC-CLEAN',
      customerId: 'CLEAN-PJ-01',
      direction: 'out',
      rail: 'Boleto',
      amount: 3200,
      counterpartyId: 'SUPPLIER-01',
      counterpartyName: 'Fornecedor recorrente',
      deviceId: 'DEV-CORP',
    },
  ],
};

const pepCompatible: PldInput = {
  institution: 'Fintech PEP Monitor',
  generatedAt: '2026-05-30T12:10:00-03:00',
  customers: [
    {
      customerId: 'PEP-01',
      name: 'Cliente PEP com renda compatível',
      customerType: 'PF',
      accountAgeDays: 1300,
      declaredMonthlyIncome: 80000,
      pep: true,
    },
  ],
  transactions: [
    {
      id: 'PEP-1',
      timestamp: '2026-05-30T09:00:00-03:00',
      accountId: 'ACC-PEP',
      customerId: 'PEP-01',
      direction: 'out',
      rail: 'Pix',
      amount: 7000,
      counterpartyId: 'FAM-01',
      counterpartyName: 'Familiar declarado',
      deviceId: 'DEV-PEP',
    },
  ],
};

const structuring: PldInput = {
  institution: 'Fintech Estruturação',
  generatedAt: '2026-05-30T13:00:00-03:00',
  customers: [
    {
      customerId: 'STR-01',
      name: 'Cliente com fracionamento',
      customerType: 'PF',
      accountAgeDays: 250,
      declaredMonthlyIncome: 9000,
    },
  ],
  transactions: Array.from({ length: 6 }, (_, index) => ({
    id: `STR-${index + 1}`,
    timestamp: `2026-05-30T10:${String(index * 4).padStart(2, '0')}:00-03:00`,
    accountId: 'ACC-STR',
    customerId: 'STR-01',
    direction: 'out' as const,
    rail: 'Pix' as const,
    amount: 4900,
    counterpartyId: `CP-${index + 1}`,
    counterpartyName: `Favorecido ${index + 1}`,
    deviceId: 'DEV-STR',
  })),
};

const passThrough = samplePldInput;

const sanctions = {
  ...samplePldInput,
  institution: 'Fintech Screening',
  customers: [
    ...(samplePldInput.customers || []),
    {
      customerId: 'SANCTION-01',
      name: 'Cliente com hit sancionatório simulado',
      customerType: 'PJ' as const,
      accountAgeDays: 100,
      declaredMonthlyRevenue: 50000,
      sanctionsHit: true,
    },
  ],
  transactions: [
    ...samplePldInput.transactions,
    {
      id: 'SAN-1',
      timestamp: '2026-05-30T11:00:00-03:00',
      accountId: 'ACC-SAN',
      customerId: 'SANCTION-01',
      direction: 'out' as const,
      rail: 'Pix' as const,
      amount: 12000,
      counterpartyId: 'EXT-RISK-01',
      counterpartyName: 'Contraparte de alto risco',
      deviceId: 'DEV-SAN',
    },
  ],
} satisfies PldInput;

export const pldScenarios: PldScenario[] = [
  {
    id: 'conta-laranja-pix',
    name: 'Conta laranja / Pix em cadeia',
    description: 'Recebimento relevante seguido de saídas rápidas, device reutilizado e adjacência cripto.',
    expectedSeverity: 'critical',
    input: passThrough,
  },
  {
    id: 'fluxo-limpo',
    name: 'Fluxo limpo recorrente',
    description: 'Pagamentos compatíveis com perfil PJ, sem fan-out suspeito e sem flags externas.',
    expectedSeverity: 'low',
    input: cleanFlow,
  },
  {
    id: 'pep-compativel',
    name: 'PEP com movimentação compatível',
    description: 'Caso com PEP que deve gerar diligência reforçada sem pressupor crime.',
    expectedSeverity: 'high',
    input: pepCompatible,
  },
  {
    id: 'fracionamento',
    name: 'Fracionamento / estruturação',
    description: 'Várias transações abaixo de faixa sensível em sequência para múltiplos favorecidos.',
    expectedSeverity: 'critical',
    input: structuring,
  },
  {
    id: 'sancoes',
    name: 'Screening com sanção simulada',
    description: 'Cliente com flag sancionatória simulada somada a movimentação Pix.',
    expectedSeverity: 'critical',
    input: sanctions,
  },
];

export function runSyntheticBenchmark() {
  return pldScenarios.map((scenario) => {
    const dossier = analyzePldFt(scenario.input);
    return {
      scenarioId: scenario.id,
      name: scenario.name,
      expectedSeverity: scenario.expectedSeverity,
      actualSeverity: dossier.severity,
      riskScore: dossier.riskScore,
      findings: dossier.findings.length,
      matchedExpectation: dossier.severity === scenario.expectedSeverity,
      topRule: dossier.findings[0]?.ruleId || 'none',
    };
  });
}
