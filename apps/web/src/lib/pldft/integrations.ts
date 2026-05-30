export type PldIntegrationStatus = 'configured' | 'pending';

export interface PldIntegration {
  id: string;
  name: string;
  status: PldIntegrationStatus;
  envKeys: string[];
  purpose: string;
  nextStep: string;
}

function configured(envKeys: string[]): PldIntegrationStatus {
  return envKeys.some((key) => Boolean(process.env[key])) ? 'configured' : 'pending';
}

export function getPldIntegrations(): PldIntegration[] {
  const items = [
    {
      id: 'pix-core',
      name: 'Pix / Core Banking',
      envKeys: ['QUARRY_PLD_PIX_WEBHOOK_SECRET', 'QUARRY_PLD_CORE_BANKING_URL', 'QUARRY_PLD_CORE_BANKING_TOKEN'],
      purpose: 'Receber eventos transacionais em tempo real ou lote diário.',
      nextStep: 'Conectar webhook/API da fintech e mapear campos para PldTransaction.',
    },
    {
      id: 'kyc',
      name: 'KYC / Cadastro',
      envKeys: ['QUARRY_PLD_KYC_URL', 'QUARRY_PLD_KYC_TOKEN'],
      purpose: 'Trazer renda, faturamento, CNAE, endereço, idade da conta e documentos.',
      nextStep: 'Ligar provedor KYC ou base cadastral interna da fintech.',
    },
    {
      id: 'sanctions',
      name: 'Sanções internacionais',
      envKeys: ['QUARRY_PLD_SANCTIONS_URL', 'QUARRY_PLD_SANCTIONS_TOKEN', 'OFAC_API_KEY'],
      purpose: 'Triagem contra listas restritivas, aliases e entidades relacionadas.',
      nextStep: 'Definir provedor oficial/comercial e política de atualização.',
    },
    {
      id: 'pep',
      name: 'PEP e listas nacionais',
      envKeys: ['QUARRY_PLD_PEP_URL', 'QUARRY_PLD_PEP_TOKEN'],
      purpose: 'Marcar pessoas politicamente expostas e vínculos de risco aumentado.',
      nextStep: 'Conectar base PEP e revisar regras de enhanced due diligence.',
    },
    {
      id: 'adverse-media',
      name: 'Mídia adversa',
      envKeys: ['QUARRY_PLD_ADVERSE_MEDIA_URL', 'QUARRY_PLD_ADVERSE_MEDIA_TOKEN'],
      purpose: 'Complementar a revisão com notícias e sinais reputacionais.',
      nextStep: 'Escolher fonte e estabelecer critérios de materialidade.',
    },
    {
      id: 'case-management',
      name: 'Fila de casos / GRC',
      envKeys: ['QUARRY_PLD_CASE_WEBHOOK_URL', 'QUARRY_PLD_CASE_WEBHOOK_TOKEN'],
      purpose: 'Enviar casos críticos para fluxo operacional de compliance.',
      nextStep: 'Configurar webhook ou integração com ferramenta interna de casos.',
    },
  ];

  return items.map((item) => ({
    ...item,
    status: configured(item.envKeys),
  }));
}
