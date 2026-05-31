export type TransactionRail = 'Pix' | 'TED' | 'Boleto' | 'Cartao' | 'Open Finance' | 'Crypto' | 'Outro';
export type TransactionDirection = 'in' | 'out';
export type RiskSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface PldCustomerProfile {
  customerId: string;
  name: string;
  document?: string;
  accountAgeDays?: number;
  declaredMonthlyIncome?: number;
  declaredMonthlyRevenue?: number;
  customerType?: 'PF' | 'PJ';
  city?: string;
  state?: string;
  pep?: boolean;
  sanctionsHit?: boolean;
  adverseMedia?: boolean;
  highRiskActivity?: boolean;
}

export interface PldTransaction {
  id: string;
  timestamp: string;
  accountId: string;
  customerId: string;
  direction: TransactionDirection;
  rail: TransactionRail;
  amount: number;
  counterpartyId: string;
  counterpartyName?: string;
  counterpartyDocument?: string;
  deviceId?: string;
  ip?: string;
  city?: string;
  country?: string;
  status?: string;
  tags?: string[];
}

export interface PldInput {
  institution?: string;
  generatedAt?: string;
  transactions: PldTransaction[];
  customers?: PldCustomerProfile[];
  thresholds?: Partial<PldThresholds>;
}

export interface PldThresholds {
  passThroughMinAmount: number;
  passThroughWindowMinutes: number;
  passThroughRatio: number;
  outboundFanoutMinCounterparties: number;
  outboundFanoutMinTotal: number;
  multiVictimMinSenders: number;
  multiVictimMinInboundTotal: number;
  multiVictimOutboundRatio: number;
  economicMismatchMinAmount: number;
  economicMismatchMultiplier: number;
  economicMismatchCriticalMultiplier: number;
  newAccountMaxAgeDays: number;
  newAccountLargeSendMinAmount: number;
  deviceReuseMinCustomers: number;
  structuringMinTransactions: number;
  structuringMinSingleAmount: number;
  structuringMaxSingleAmount: number;
  structuringMinTotal: number;
  cryptoAdjacencyMinAmount: number;
  cryptoAdjacencyInboundRatio: number;
}

export interface RuleFinding {
  ruleId: string;
  title: string;
  severity: RiskSeverity;
  score: number;
  entityId: string;
  entityType: 'customer' | 'account' | 'device' | 'counterparty' | 'cluster';
  rationale: string;
  evidence: string[];
  transactionIds: string[];
  amountInScope: number;
  recommendedAction: string;
}

export interface PldNetworkNode {
  id: string;
  label: string;
  type: 'customer' | 'account' | 'counterparty' | 'device';
  risk: number;
}

export interface PldNetworkEdge {
  from: string;
  to: string;
  label: string;
  amount: number;
  transactionIds: string[];
}

export interface PldAiHypothesis {
  title: string;
  confidence: 'alta' | 'media' | 'baixa' | string;
  basis: string;
  evidenceIds: string[];
  evidence: string[];
  alternateExplanation: string;
  nextSteps: string[];
}

export interface PldAiAnalyst {
  version: string;
  mode: string;
  caseNarrative: {
    summary: string;
    timeline: Array<{
      timestamp?: string;
      transactionId: string;
      direction?: string;
      rail?: string;
      amount: number;
      customerId?: string;
      counterpartyId?: string;
      description: string;
    }>;
    keyRiskDrivers: Array<{
      ruleId: string;
      title: string;
      severity: RiskSeverity;
      score: number;
      amountInScope: number;
      evidence: string[];
    }>;
    counterpoints: string[];
    recommendedDecision: string;
  };
  hypotheses: PldAiHypothesis[];
  investigationPlan: string[];
  critic: {
    verdict: string;
    gaps: string[];
    unsupportedClaims: string[];
    requiredHumanChecks: string[];
  };
  coafDraft: {
    shouldPrepare: boolean;
    rationale: string;
    objectiveFacts: string[];
    humanApprovalRequired: boolean;
  };
  similarityFingerprint: {
    rules: string[];
    entities: string[];
    severity: RiskSeverity;
  };
}

export interface PldDossier {
  id: string;
  institution: string;
  generatedAt: string;
  riskScore: number;
  severity: RiskSeverity;
  totalTransactions: number;
  totalAmount: number;
  suspiciousAmount: number;
  findings: RuleFinding[];
  network: {
    nodes: PldNetworkNode[];
    edges: PldNetworkEdge[];
  };
  aiAnalyst?: PldAiAnalyst;
  executiveSummary: string;
  analystChecklist: string[];
  auditTrail: string[];
  disclaimer: string;
}

const BRL = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 2,
});

export const defaultPldThresholds: PldThresholds = {
  passThroughMinAmount: 3000,
  passThroughWindowMinutes: 90,
  passThroughRatio: 0.8,
  outboundFanoutMinCounterparties: 3,
  outboundFanoutMinTotal: 12000,
  multiVictimMinSenders: 4,
  multiVictimMinInboundTotal: 8000,
  multiVictimOutboundRatio: 0.65,
  economicMismatchMinAmount: 15000,
  economicMismatchMultiplier: 4,
  economicMismatchCriticalMultiplier: 8,
  newAccountMaxAgeDays: 20,
  newAccountLargeSendMinAmount: 5000,
  deviceReuseMinCustomers: 3,
  structuringMinTransactions: 5,
  structuringMinSingleAmount: 1000,
  structuringMaxSingleAmount: 10000,
  structuringMinTotal: 25000,
  cryptoAdjacencyMinAmount: 3000,
  cryptoAdjacencyInboundRatio: 0.7,
};

function normalizeThresholds(input?: Partial<PldThresholds>): PldThresholds {
  return {
    ...defaultPldThresholds,
    ...(input || {}),
  };
}

function toTime(value: string): number {
  const time = Date.parse(value);
  return Number.isFinite(time) ? time : 0;
}

function sumAmount(transactions: PldTransaction[]): number {
  return transactions.reduce((total, tx) => total + Math.max(0, Number(tx.amount) || 0), 0);
}

function distinct<T>(items: T[]): T[] {
  return [...new Set(items)];
}

function severityFromScore(score: number): RiskSeverity {
  if (score >= 85) return 'critical';
  if (score >= 65) return 'high';
  if (score >= 40) return 'medium';
  return 'low';
}

function addFinding(findings: RuleFinding[], finding: RuleFinding): void {
  const key = `${finding.ruleId}:${finding.entityId}:${finding.transactionIds.sort().join(',')}`;
  const exists = findings.some(
    (item) => `${item.ruleId}:${item.entityId}:${item.transactionIds.sort().join(',')}` === key,
  );
  if (!exists) findings.push(finding);
}

function byCustomer(transactions: PldTransaction[]): Map<string, PldTransaction[]> {
  const groups = new Map<string, PldTransaction[]>();
  for (const tx of transactions) {
    const key = tx.customerId || tx.accountId;
    groups.set(key, [...(groups.get(key) || []), tx]);
  }
  return groups;
}

function customerProfileMap(customers: PldCustomerProfile[] = []): Map<string, PldCustomerProfile> {
  return new Map(customers.map((customer) => [customer.customerId, customer]));
}

function detectPassThrough(
  transactions: PldTransaction[],
  findings: RuleFinding[],
  thresholds: PldThresholds,
): void {
  for (const [customerId, customerTxs] of byCustomer(transactions)) {
    const inbound = customerTxs.filter((tx) => tx.direction === 'in').sort((a, b) => toTime(a.timestamp) - toTime(b.timestamp));
    const outbound = customerTxs.filter((tx) => tx.direction === 'out').sort((a, b) => toTime(a.timestamp) - toTime(b.timestamp));

    for (const txIn of inbound) {
      const start = toTime(txIn.timestamp);
      const closeOut = outbound.filter((txOut) => {
        const deltaMinutes = (toTime(txOut.timestamp) - start) / 60000;
        return deltaMinutes >= 0 && deltaMinutes <= thresholds.passThroughWindowMinutes;
      });
      const outTotal = sumAmount(closeOut);
      if (txIn.amount >= thresholds.passThroughMinAmount && outTotal >= txIn.amount * thresholds.passThroughRatio) {
        addFinding(findings, {
          ruleId: 'PLD-PIX-001',
          title: 'Conta de passagem: entrada seguida de saída rápida',
          severity: 'critical',
          score: 92,
          entityId: customerId,
          entityType: 'customer',
          rationale:
            'O cliente recebeu valor relevante e repassou pelo menos 80% em até 90 minutos, padrão compatível com conta de passagem ou cash-out.',
          evidence: [
            `Entrada ${txIn.id} de ${BRL.format(txIn.amount)} em ${txIn.timestamp}.`,
            `Saídas próximas somam ${BRL.format(outTotal)} para ${distinct(closeOut.map((tx) => tx.counterpartyId)).length} favorecido(s).`,
            `Parâmetro aplicado: ${Math.round(thresholds.passThroughRatio * 100)}% em até ${thresholds.passThroughWindowMinutes} minutos.`,
          ],
          transactionIds: [txIn.id, ...closeOut.map((tx) => tx.id)],
          amountInScope: txIn.amount + outTotal,
          recommendedAction: 'Abrir caso PLD/FT, revisar origem dos recursos e bloquear preventivamente novas saídas se a política interna permitir.',
        });
      }
    }
  }
}

function detectOutboundFanout(
  transactions: PldTransaction[],
  findings: RuleFinding[],
  thresholds: PldThresholds,
): void {
  for (const [customerId, customerTxs] of byCustomer(transactions)) {
    const outboundPix = customerTxs.filter((tx) => tx.direction === 'out' && tx.rail === 'Pix');
    const counterparties = distinct(outboundPix.map((tx) => tx.counterpartyId));
    const total = sumAmount(outboundPix);
    if (counterparties.length >= thresholds.outboundFanoutMinCounterparties && total >= thresholds.outboundFanoutMinTotal) {
      addFinding(findings, {
        ruleId: 'PLD-PIX-002',
        title: 'Fan-out Pix para múltiplos favorecidos',
        severity: 'high',
        score: 76,
        entityId: customerId,
        entityType: 'customer',
        rationale:
          'Múltiplas saídas Pix para favorecidos distintos no mesmo recorte sugerem dispersão de recursos e tentativa de reduzir rastreabilidade.',
        evidence: [
          `${counterparties.length} favorecidos distintos em ${outboundPix.length} transações Pix.`,
          `Volume de saída no recorte: ${BRL.format(total)}.`,
        ],
        transactionIds: outboundPix.map((tx) => tx.id),
        amountInScope: total,
        recommendedAction: 'Validar finalidade econômica declarada, relação com favorecidos e recorrência histórica do cliente.',
      });
    }
  }
}

function detectMultiVictimAggregation(
  transactions: PldTransaction[],
  findings: RuleFinding[],
  thresholds: PldThresholds,
): void {
  for (const [customerId, customerTxs] of byCustomer(transactions)) {
    const inbound = customerTxs.filter((tx) => tx.direction === 'in');
    const uniqueSenders = distinct(inbound.map((tx) => tx.counterpartyId));
    const inboundTotal = sumAmount(inbound);
    const outboundTotal = sumAmount(customerTxs.filter((tx) => tx.direction === 'out'));
    if (
      uniqueSenders.length >= thresholds.multiVictimMinSenders &&
      inboundTotal >= thresholds.multiVictimMinInboundTotal &&
      outboundTotal >= inboundTotal * thresholds.multiVictimOutboundRatio
    ) {
      addFinding(findings, {
        ruleId: 'PLD-PIX-003',
        title: 'Agregação de múltiplos remetentes e repasse posterior',
        severity: 'critical',
        score: 88,
        entityId: customerId,
        entityType: 'customer',
        rationale:
          'Recebimentos de vários remetentes com repasse relevante posterior podem indicar centralização de valores de vítimas ou rede de contas laranja.',
        evidence: [
          `${uniqueSenders.length} remetentes distintos enviaram ${BRL.format(inboundTotal)}.`,
          `Saídas posteriores somam ${BRL.format(outboundTotal)}.`,
        ],
        transactionIds: customerTxs.map((tx) => tx.id),
        amountInScope: inboundTotal + outboundTotal,
        recommendedAction: 'Priorizar revisão humana, solicitar documentação de origem/finalidade e correlacionar com MED/contestação quando houver.',
      });
    }
  }
}

function detectEconomicMismatch(
  transactions: PldTransaction[],
  customers: Map<string, PldCustomerProfile>,
  findings: RuleFinding[],
  thresholds: PldThresholds,
): void {
  for (const [customerId, customerTxs] of byCustomer(transactions)) {
    const profile = customers.get(customerId);
    const declared = profile?.declaredMonthlyRevenue || profile?.declaredMonthlyIncome || 0;
    if (!declared) continue;
    const moved = sumAmount(customerTxs);
    const multiplier = moved / declared;
    if (moved >= thresholds.economicMismatchMinAmount && multiplier >= thresholds.economicMismatchMultiplier) {
      const severity = multiplier >= thresholds.economicMismatchCriticalMultiplier ? 'critical' : 'high';
      addFinding(findings, {
        ruleId: 'PLD-KYC-004',
        title: 'Movimentação incompatível com perfil econômico declarado',
        severity,
        score: severity === 'critical' ? 90 : 72,
        entityId: customerId,
        entityType: 'customer',
        rationale:
          'O volume movimentado no recorte excede múltiplos relevantes da renda/faturamento declarado no KYC.',
        evidence: [
          `Perfil declarou ${BRL.format(declared)} mensais.`,
          `Movimentação analisada soma ${BRL.format(moved)} (${multiplier.toFixed(1)}x o declarado).`,
        ],
        transactionIds: customerTxs.map((tx) => tx.id),
        amountInScope: moved,
        recommendedAction: 'Atualizar KYC, confirmar atividade econômica e revisar documentação comprobatória antes de manter limites atuais.',
      });
    }
  }
}

function detectNewAccountLargeFirstSend(
  transactions: PldTransaction[],
  customers: Map<string, PldCustomerProfile>,
  findings: RuleFinding[],
  thresholds: PldThresholds,
): void {
  for (const [customerId, customerTxs] of byCustomer(transactions)) {
    const profile = customers.get(customerId);
    if ((profile?.accountAgeDays ?? 999) > thresholds.newAccountMaxAgeDays) continue;
    const outbound = customerTxs.filter((tx) => tx.direction === 'out').sort((a, b) => toTime(a.timestamp) - toTime(b.timestamp));
    const firstLarge = outbound.find((tx) => tx.amount >= thresholds.newAccountLargeSendMinAmount);
    if (firstLarge) {
      addFinding(findings, {
        ruleId: 'PLD-KYC-005',
        title: 'Conta nova com primeira saída relevante',
        severity: 'high',
        score: 70,
        entityId: customerId,
        entityType: 'customer',
        rationale:
          'Conta recém-aberta realizando saída de alto valor antes de formar histórico comportamental confiável.',
        evidence: [
          `Idade da conta: ${profile?.accountAgeDays ?? 0} dia(s).`,
          `Transação ${firstLarge.id} enviou ${BRL.format(firstLarge.amount)} para ${firstLarge.counterpartyName || firstLarge.counterpartyId}.`,
        ],
        transactionIds: [firstLarge.id],
        amountInScope: firstLarge.amount,
        recommendedAction: 'Aplicar revisão reforçada de onboarding, device, IP, origem de fundos e relação com favorecido.',
      });
    }
  }
}

function detectDeviceReuse(
  transactions: PldTransaction[],
  findings: RuleFinding[],
  thresholds: PldThresholds,
): void {
  const deviceMap = new Map<string, Set<string>>();
  for (const tx of transactions) {
    if (!tx.deviceId) continue;
    if (!deviceMap.has(tx.deviceId)) deviceMap.set(tx.deviceId, new Set());
    deviceMap.get(tx.deviceId)?.add(tx.customerId);
  }
  for (const [deviceId, customers] of deviceMap) {
    if (customers.size >= thresholds.deviceReuseMinCustomers) {
      const related = transactions.filter((tx) => tx.deviceId === deviceId);
      addFinding(findings, {
        ruleId: 'PLD-DEV-006',
        title: 'Dispositivo reutilizado por múltiplas contas',
        severity: 'critical',
        score: 87,
        entityId: deviceId,
        entityType: 'device',
        rationale:
          'O mesmo device aparece em três ou mais clientes, sinal forte de rede operacional, onboarding coordenado ou conta laranja.',
        evidence: [
          `Device ${deviceId} aparece em ${customers.size} clientes.`,
          `Volume relacionado: ${BRL.format(sumAmount(related))}.`,
        ],
        transactionIds: related.map((tx) => tx.id),
        amountInScope: sumAmount(related),
        recommendedAction: 'Correlacionar KYC, IP, geolocalização e documentos usados nas contas ligadas ao dispositivo.',
      });
    }
  }
}

function detectStructuring(
  transactions: PldTransaction[],
  findings: RuleFinding[],
  thresholds: PldThresholds,
): void {
  for (const [customerId, customerTxs] of byCustomer(transactions)) {
    const outbound = customerTxs.filter(
      (tx) =>
        tx.direction === 'out' &&
        tx.amount >= thresholds.structuringMinSingleAmount &&
        tx.amount < thresholds.structuringMaxSingleAmount,
    );
    const total = sumAmount(outbound);
    if (outbound.length >= thresholds.structuringMinTransactions && total >= thresholds.structuringMinTotal) {
      addFinding(findings, {
        ruleId: 'PLD-STR-007',
        title: 'Fracionamento recorrente abaixo de faixa sensível',
        severity: 'high',
        score: 74,
        entityId: customerId,
        entityType: 'customer',
        rationale:
          'Várias transações abaixo de valores sensíveis, em sequência, podem indicar estruturação para escapar de controles simples por valor.',
        evidence: [
          `${outbound.length} saídas entre R$ 1.000,00 e R$ 10.000,00.`,
          `Total fracionado: ${BRL.format(total)}.`,
        ],
        transactionIds: outbound.map((tx) => tx.id),
        amountInScope: total,
        recommendedAction: 'Avaliar padrão agregado, finalidade declarada e vínculo entre favorecidos antes de liberar novas janelas de envio.',
      });
    }
  }
}

function detectSanctionsAndPep(
  transactions: PldTransaction[],
  customers: Map<string, PldCustomerProfile>,
  findings: RuleFinding[],
): void {
  for (const [customerId, customerTxs] of byCustomer(transactions)) {
    const profile = customers.get(customerId);
    if (!profile?.sanctionsHit && !profile?.pep && !profile?.adverseMedia && !profile?.highRiskActivity) continue;
    const flags = [
      profile.sanctionsHit ? 'sanctions/lista restritiva' : null,
      profile.pep ? 'PEP' : null,
      profile.adverseMedia ? 'mídia adversa' : null,
      profile.highRiskActivity ? 'atividade de alto risco' : null,
    ].filter(Boolean);
    addFinding(findings, {
      ruleId: 'PLD-LIST-008',
      title: 'Exposição de cadastro a lista, PEP ou sinal externo de risco',
      severity: profile.sanctionsHit ? 'critical' : 'high',
      score: profile.sanctionsHit ? 95 : 78,
      entityId: customerId,
      entityType: 'customer',
      rationale:
        'O cadastro possui flags externas ou cadastrais que exigem diligência reforçada antes de manter relacionamento/transações.',
      evidence: [
        `Flags encontradas: ${flags.join(', ')}.`,
        `Movimentação vinculada no recorte: ${BRL.format(sumAmount(customerTxs))}.`,
      ],
      transactionIds: customerTxs.map((tx) => tx.id),
      amountInScope: sumAmount(customerTxs),
      recommendedAction: 'Executar enhanced due diligence, preservar evidência da fonte e submeter decisão ao responsável PLD.',
    });
  }
}

function detectCryptoAdjacency(
  transactions: PldTransaction[],
  findings: RuleFinding[],
  thresholds: PldThresholds,
): void {
  for (const [customerId, customerTxs] of byCustomer(transactions)) {
    const cryptoOut = customerTxs.filter((tx) => tx.direction === 'out' && (tx.rail === 'Crypto' || tx.tags?.includes('crypto')));
    if (!cryptoOut.length) continue;
    const inbound = customerTxs.filter((tx) => tx.direction === 'in');
    const cryptoTotal = sumAmount(cryptoOut);
    const inboundTotal = sumAmount(inbound);
    if (cryptoTotal >= thresholds.cryptoAdjacencyMinAmount && inboundTotal >= cryptoTotal * thresholds.cryptoAdjacencyInboundRatio) {
      addFinding(findings, {
        ruleId: 'PLD-CRYPTO-009',
        title: 'Adjacência cripto após entrada de recursos',
        severity: 'high',
        score: 79,
        entityId: customerId,
        entityType: 'customer',
        rationale:
          'Saída para trilha cripto após entradas recentes pode aumentar opacidade e exige investigação reforçada de origem e finalidade.',
        evidence: [
          `Saídas cripto/P2P somam ${BRL.format(cryptoTotal)}.`,
          `Entradas relacionadas no recorte somam ${BRL.format(inboundTotal)}.`,
        ],
        transactionIds: [...cryptoOut.map((tx) => tx.id), ...inbound.map((tx) => tx.id)],
        amountInScope: cryptoTotal + inboundTotal,
        recommendedAction: 'Checar exchange/beneficiário, origem dos fundos, histórico do cliente e política interna para cripto/P2P.',
      });
    }
  }
}

function buildNetwork(transactions: PldTransaction[], findings: RuleFinding[]): PldDossier['network'] {
  const riskByEntity = new Map<string, number>();
  for (const finding of findings) {
    riskByEntity.set(finding.entityId, Math.max(riskByEntity.get(finding.entityId) || 0, finding.score));
    for (const txId of finding.transactionIds) {
      const tx = transactions.find((item) => item.id === txId);
      if (!tx) continue;
      riskByEntity.set(tx.customerId, Math.max(riskByEntity.get(tx.customerId) || 0, finding.score));
      riskByEntity.set(tx.accountId, Math.max(riskByEntity.get(tx.accountId) || 0, finding.score));
      riskByEntity.set(tx.counterpartyId, Math.max(riskByEntity.get(tx.counterpartyId) || 0, finding.score));
      if (tx.deviceId) riskByEntity.set(tx.deviceId, Math.max(riskByEntity.get(tx.deviceId) || 0, finding.score));
    }
  }

  const nodes = new Map<string, PldNetworkNode>();
  const edges = new Map<string, PldNetworkEdge>();
  for (const tx of transactions) {
    nodes.set(tx.customerId, {
      id: tx.customerId,
      label: tx.customerId,
      type: 'customer',
      risk: riskByEntity.get(tx.customerId) || 0,
    });
    nodes.set(tx.accountId, {
      id: tx.accountId,
      label: tx.accountId,
      type: 'account',
      risk: riskByEntity.get(tx.accountId) || 0,
    });
    nodes.set(tx.counterpartyId, {
      id: tx.counterpartyId,
      label: tx.counterpartyName || tx.counterpartyId,
      type: 'counterparty',
      risk: riskByEntity.get(tx.counterpartyId) || 0,
    });
    if (tx.deviceId) {
      nodes.set(tx.deviceId, {
        id: tx.deviceId,
        label: tx.deviceId,
        type: 'device',
        risk: riskByEntity.get(tx.deviceId) || 0,
      });
    }
    const from = tx.direction === 'in' ? tx.counterpartyId : tx.accountId;
    const to = tx.direction === 'in' ? tx.accountId : tx.counterpartyId;
    const key = `${from}->${to}:${tx.rail}`;
    const current = edges.get(key);
    if (current) {
      current.amount += tx.amount;
      current.transactionIds.push(tx.id);
    } else {
      edges.set(key, {
        from,
        to,
        label: tx.rail,
        amount: tx.amount,
        transactionIds: [tx.id],
      });
    }
  }
  return {
    nodes: [...nodes.values()].sort((a, b) => b.risk - a.risk).slice(0, 24),
    edges: [...edges.values()].sort((a, b) => b.amount - a.amount).slice(0, 32),
  };
}

function executiveSummary(dossier: Omit<PldDossier, 'executiveSummary'>): string {
  const topRules = dossier.findings.slice(0, 3).map((finding) => finding.title);
  if (!dossier.findings.length) {
    return 'Nenhum padrão crítico foi identificado no conjunto analisado. O resultado não elimina risco: ele apenas indica que as regras determinísticas desta execução não encontraram sinal suficiente para abrir caso prioritário.';
  }
  return [
    `O Quarry identificou ${dossier.findings.length} achado(s) compatíveis com risco PLD/FT em ${dossier.totalTransactions} transações.`,
    `O score consolidado foi ${dossier.riskScore}/100 (${dossier.severity}), com ${BRL.format(dossier.suspiciousAmount)} em escopo suspeito.`,
    `Principais sinais: ${topRules.join('; ')}.`,
    'A recomendação é revisão humana documentada, preservação de evidências e decisão do responsável PLD antes de qualquer conclusão externa.',
  ].join(' ');
}

export function analyzePldFt(input: PldInput): PldDossier {
  const transactions = [...input.transactions].sort((a, b) => toTime(a.timestamp) - toTime(b.timestamp));
  const customers = customerProfileMap(input.customers);
  const thresholds = normalizeThresholds(input.thresholds);
  const findings: RuleFinding[] = [];

  detectPassThrough(transactions, findings, thresholds);
  detectOutboundFanout(transactions, findings, thresholds);
  detectMultiVictimAggregation(transactions, findings, thresholds);
  detectEconomicMismatch(transactions, customers, findings, thresholds);
  detectNewAccountLargeFirstSend(transactions, customers, findings, thresholds);
  detectDeviceReuse(transactions, findings, thresholds);
  detectStructuring(transactions, findings, thresholds);
  detectSanctionsAndPep(transactions, customers, findings);
  detectCryptoAdjacency(transactions, findings, thresholds);

  const sortedFindings = findings.sort((a, b) => b.score - a.score || b.amountInScope - a.amountInScope);
  const riskScore = Math.min(
    100,
    Math.round(
      sortedFindings.reduce((score, finding, index) => score + finding.score * (index === 0 ? 0.45 : 0.12), 0),
    ),
  );
  const findingTxIds = new Set(sortedFindings.flatMap((finding) => finding.transactionIds));
  const suspiciousAmount = sumAmount(transactions.filter((tx) => findingTxIds.has(tx.id)));
  const base: Omit<PldDossier, 'executiveSummary'> = {
    id: `PLD-${new Date(input.generatedAt || Date.now()).toISOString().slice(0, 10).replace(/-/g, '')}-${Math.abs(
      JSON.stringify(input).split('').reduce((hash, char) => (hash * 31 + char.charCodeAt(0)) | 0, 7),
    )
      .toString(16)
      .toUpperCase()}`,
    institution: input.institution || 'Instituição financeira',
    generatedAt: input.generatedAt || new Date().toISOString(),
    riskScore,
    severity: severityFromScore(riskScore),
    totalTransactions: transactions.length,
    totalAmount: sumAmount(transactions),
    suspiciousAmount,
    findings: sortedFindings,
    network: buildNetwork(transactions, sortedFindings),
    analystChecklist: [
      'Validar identidade, KYC, renda/faturamento e substância econômica das entidades com maior score.',
      'Conferir vínculo declarado entre cliente, favorecidos, dispositivos e contrapartes.',
      'Preservar evidências originais, timestamps, fontes e hashes antes de contato externo.',
      'Registrar decisão humana: falso positivo, monitoramento, bloqueio preventivo, encerramento ou comunicação regulatória.',
      'Submeter casos críticos ao responsável PLD/FT e jurídico antes de qualquer comunicação a terceiros.',
    ],
    auditTrail: [
      'Entrada normalizada no schema Quarry PLD/FT Event v1.',
      'Regras determinísticas executadas sem uso de LLM para cálculo de score.',
      'Achados classificados por severidade, valor em escopo e evidência transacional.',
      'Grafo de entidades criado a partir de cliente, conta, favorecido e dispositivo.',
      'Dossiê gerado com recomendação de revisão humana obrigatória.',
    ],
    disclaimer:
      'Este dossiê não declara crime, culpa ou ilegalidade. Ele identifica padrões compatíveis com risco PLD/FT/fraude e organiza evidências para revisão humana, jurídica e regulatória.',
  };

  return {
    ...base,
    executiveSummary: executiveSummary(base),
  };
}

export function pldDossierToMarkdown(dossier: PldDossier): string {
  const findings = dossier.findings
    .map(
      (finding, index) => [
        `### ${index + 1}. ${finding.title}`,
        `- Regra: ${finding.ruleId}`,
        `- Severidade: ${finding.severity}`,
        `- Score: ${finding.score}/100`,
        `- Entidade: ${finding.entityType} ${finding.entityId}`,
        `- Valor em escopo: ${BRL.format(finding.amountInScope)}`,
        `- Racional: ${finding.rationale}`,
        `- Evidências: ${finding.evidence.join(' | ')}`,
        `- Transações: ${finding.transactionIds.join(', ')}`,
        `- Ação recomendada: ${finding.recommendedAction}`,
      ].join('\n'),
    )
    .join('\n\n');

  return [
    `# Dossiê PLD/FT — ${dossier.id}`,
    '',
    `**Instituição:** ${dossier.institution}`,
    `**Gerado em:** ${dossier.generatedAt}`,
    `**Score consolidado:** ${dossier.riskScore}/100 (${dossier.severity})`,
    `**Transações analisadas:** ${dossier.totalTransactions}`,
    `**Volume total:** ${BRL.format(dossier.totalAmount)}`,
    `**Volume em escopo suspeito:** ${BRL.format(dossier.suspiciousAmount)}`,
    '',
    '## Sumário executivo',
    dossier.executiveSummary,
    '',
    '## Achados',
    findings || 'Nenhum achado prioritário.',
    '',
    '## Checklist do analista',
    ...dossier.analystChecklist.map((item) => `- ${item}`),
    '',
    '## Trilha de auditoria',
    ...dossier.auditTrail.map((item) => `- ${item}`),
    '',
    '## Observação legal',
    dossier.disclaimer,
  ].join('\n');
}
