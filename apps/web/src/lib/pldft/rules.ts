import { defaultPldThresholds } from './engine';

export interface PldRuleCatalogItem {
  id: string;
  title: string;
  objective: string;
  requiredInputs: string[];
  deterministicCondition: string;
  commonFalsePositives: string[];
  recommendedAction: string;
  specialistValidation: string;
}

export const pldRuleCatalog: PldRuleCatalogItem[] = [
  {
    id: 'PLD-PIX-001',
    title: 'Conta de passagem: entrada seguida de saída rápida',
    objective: 'Identificar contas usadas para receber recursos e repassar rapidamente quase todo o valor.',
    requiredInputs: ['timestamp', 'customerId', 'direction', 'amount', 'counterpartyId', 'rail'],
    deterministicCondition: `Entrada >= R$ ${defaultPldThresholds.passThroughMinAmount} e saída >= ${Math.round(defaultPldThresholds.passThroughRatio * 100)}% em até ${defaultPldThresholds.passThroughWindowMinutes} minutos.`,
    commonFalsePositives: ['marketplaces', 'subadquirentes', 'contas escrow', 'tesouraria operacional'],
    recommendedAction: 'Abrir caso, revisar origem/finalidade e avaliar bloqueio preventivo conforme política interna.',
    specialistValidation: 'Validar janela temporal, percentual de repasse e valor mínimo por porte da instituição.',
  },
  {
    id: 'PLD-PIX-002',
    title: 'Fan-out Pix para múltiplos favorecidos',
    objective: 'Detectar dispersão de recursos para vários favorecidos em curto período.',
    requiredInputs: ['customerId', 'direction', 'rail', 'amount', 'counterpartyId'],
    deterministicCondition: `${defaultPldThresholds.outboundFanoutMinCounterparties}+ favorecidos Pix e total >= R$ ${defaultPldThresholds.outboundFanoutMinTotal}.`,
    commonFalsePositives: ['folha de pagamento', 'contas PJ com muitos fornecedores', 'rateio familiar documentado'],
    recommendedAction: 'Validar vínculo econômico dos favorecidos e recorrência histórica.',
    specialistValidation: 'Definir limites por tipo de cliente PF/PJ e por ramo de atividade.',
  },
  {
    id: 'PLD-PIX-003',
    title: 'Agregação de múltiplos remetentes e repasse posterior',
    objective: 'Encontrar contas que centralizam valores de vários remetentes e redistribuem em seguida.',
    requiredInputs: ['customerId', 'direction', 'amount', 'counterpartyId'],
    deterministicCondition: `${defaultPldThresholds.multiVictimMinSenders}+ remetentes, entrada >= R$ ${defaultPldThresholds.multiVictimMinInboundTotal}, saída >= ${Math.round(defaultPldThresholds.multiVictimOutboundRatio * 100)}% da entrada.`,
    commonFalsePositives: ['vaquinhas legítimas', 'eventos', 'clubes', 'condomínios'],
    recommendedAction: 'Checar documentação de finalidade e possíveis contestação/MED.',
    specialistValidation: 'Ajustar por perfil de produto e histórico de contestação.',
  },
  {
    id: 'PLD-KYC-004',
    title: 'Movimentação incompatível com perfil econômico declarado',
    objective: 'Relacionar KYC/renda/faturamento com volume movimentado.',
    requiredInputs: ['customerId', 'amount', 'declaredMonthlyIncome ou declaredMonthlyRevenue'],
    deterministicCondition: `Movimentação >= R$ ${defaultPldThresholds.economicMismatchMinAmount} e >= ${defaultPldThresholds.economicMismatchMultiplier}x o declarado.`,
    commonFalsePositives: ['renda desatualizada', 'sazonalidade comercial', 'aporte patrimonial comprovável'],
    recommendedAction: 'Atualizar KYC e solicitar comprovação da atividade econômica.',
    specialistValidation: 'Calibrar multiplicadores por segmento, região e ticket médio.',
  },
  {
    id: 'PLD-KYC-005',
    title: 'Conta nova com primeira saída relevante',
    objective: 'Priorizar contas recém-abertas que já movimentam valores relevantes.',
    requiredInputs: ['accountAgeDays', 'direction', 'amount', 'counterpartyId'],
    deterministicCondition: `Conta <= ${defaultPldThresholds.newAccountMaxAgeDays} dias e primeira saída >= R$ ${defaultPldThresholds.newAccountLargeSendMinAmount}.`,
    commonFalsePositives: ['cliente PJ migrado', 'conta aberta para evento específico', 'limite pré-aprovado com documentação'],
    recommendedAction: 'Aplicar diligência reforçada de onboarding, device, IP e origem dos fundos.',
    specialistValidation: 'Definir tolerância por canal de aquisição e tipo de produto.',
  },
  {
    id: 'PLD-DEV-006',
    title: 'Dispositivo reutilizado por múltiplas contas',
    objective: 'Revelar clusters operacionais que usam o mesmo device em várias contas.',
    requiredInputs: ['deviceId', 'customerId'],
    deterministicCondition: `Mesmo device usado por ${defaultPldThresholds.deviceReuseMinCustomers}+ clientes.`,
    commonFalsePositives: ['lan house', 'contador', 'celular compartilhado em empresa pequena'],
    recommendedAction: 'Cruzar device, IP, KYC, geolocalização e documentos usados no onboarding.',
    specialistValidation: 'Ajustar conforme qualidade do fingerprint e política de device trust.',
  },
  {
    id: 'PLD-STR-007',
    title: 'Fracionamento recorrente abaixo de faixa sensível',
    objective: 'Detectar estruturação por várias transações menores em vez de uma transação grande.',
    requiredInputs: ['customerId', 'direction', 'amount'],
    deterministicCondition: `${defaultPldThresholds.structuringMinTransactions}+ saídas entre R$ ${defaultPldThresholds.structuringMinSingleAmount} e R$ ${defaultPldThresholds.structuringMaxSingleAmount}, total >= R$ ${defaultPldThresholds.structuringMinTotal}.`,
    commonFalsePositives: ['pagamentos recorrentes', 'fornecedores pequenos', 'rotina operacional de PJ'],
    recommendedAction: 'Avaliar padrão agregado, favorecidos e justificativa econômica.',
    specialistValidation: 'Definir faixas sensíveis por produto e obrigação regulatória aplicável.',
  },
  {
    id: 'PLD-LIST-008',
    title: 'Exposição a lista, PEP ou sinal externo de risco',
    objective: 'Forçar diligência reforçada quando há flag externa relevante.',
    requiredInputs: ['pep', 'sanctionsHit', 'adverseMedia', 'highRiskActivity'],
    deterministicCondition: 'Qualquer flag externa/cadastral de risco gera achado; sanção eleva para crítico.',
    commonFalsePositives: ['homônimos', 'mídia antiga', 'PEP sem relação com a transação'],
    recommendedAction: 'Executar enhanced due diligence e preservar evidência da fonte.',
    specialistValidation: 'Aprovar fontes, frequência de atualização e regra de match/alias.',
  },
  {
    id: 'PLD-CRYPTO-009',
    title: 'Adjacência cripto após entrada de recursos',
    objective: 'Detectar opacidade por saída para cripto/P2P após recebimentos recentes.',
    requiredInputs: ['rail', 'tags', 'direction', 'amount'],
    deterministicCondition: `Saída cripto >= R$ ${defaultPldThresholds.cryptoAdjacencyMinAmount} e entradas >= ${Math.round(defaultPldThresholds.cryptoAdjacencyInboundRatio * 100)}% da saída.`,
    commonFalsePositives: ['cliente investidor documentado', 'exchange regulada', 'tesouraria de corretora'],
    recommendedAction: 'Checar exchange/beneficiário, origem dos fundos e política interna para cripto/P2P.',
    specialistValidation: 'Definir lista de provedores confiáveis e regra para P2P de alto risco.',
  },
];
