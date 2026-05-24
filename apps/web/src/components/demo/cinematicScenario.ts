export type DemoPhaseId =
  | 'brief'
  | 'hypotheses'
  | 'queries'
  | 'findings'
  | 'correlation'
  | 'report'
  | 'complete';

export interface DemoPhase {
  id: DemoPhaseId;
  label: string;
  theatre: string;
  startsAt: number;
  endsAt: number;
}

export interface DemoHypothesis {
  id: string;
  title: string;
  detail: string;
  confidence: number;
  tactic: string;
}

export interface DemoQuery {
  id: string;
  source: string;
  query: string;
  startsAt: number;
  endsAt: number;
  rows: number;
}

export interface DemoFinding {
  id: string;
  severity: 'critical' | 'high' | 'medium';
  title: string;
  description: string;
  evidence: string;
  appearsAt: number;
}

export interface DemoGraphNode {
  id: string;
  label: string;
  x: number;
  y: number;
  tone: 'account' | 'device' | 'pix' | 'merchant' | 'risk';
  appearsAt: number;
}

export interface DemoGraphEdge {
  from: string;
  to: string;
  label: string;
  appearsAt: number;
}

export interface DemoMitreCell {
  tactic: string;
  technique: string;
  label: string;
  appearsAt: number;
  intensity: 1 | 2 | 3;
}

export interface DemoReportPage {
  page: number;
  title: string;
  bullets: string[];
}

export interface DemoRegulatoryArtifact {
  id: string;
  norma: string;
  titulo: string;
  detalhe: string;
  appearsAt: number;
}

export interface DemoState {
  elapsedSeconds: number;
  totalSeconds: number;
  overallProgress: number;
  activePhase: DemoPhase;
  visibleHypotheses: DemoHypothesis[];
  activeQueries: Array<DemoQuery & { progress: number; status: 'queued' | 'running' | 'done' }>;
  visibleFindings: DemoFinding[];
  visibleGraphNodes: DemoGraphNode[];
  visibleGraphEdges: DemoGraphEdge[];
  visibleMitreCells: DemoMitreCell[];
  reportPages: DemoReportPage[];
  reportReady: boolean;
  visibleRegulatoryArtifacts: DemoRegulatoryArtifact[];
  activeRegulatoryArtifact: DemoRegulatoryArtifact | null;
  metrics: {
    elapsedLabel: string;
    costUsd: number;
    humanCostUsd: number;
    hoursSaved: number;
    transactionsScanned: number;
    accountsCorrelated: number;
    pixValueBrl: number;
  };
}

export const HERO_BRIEF =
  'Investigar possível fraude Pix organizada na FinPlay Pagamentos: 500 transações suspeitas em 30 dias, contas recém-criadas recebendo valores fracionados e repasses em cadeia para possíveis contas-laranja.';

export const TOTAL_SECONDS = 270;

export const DEMO_PHASES: DemoPhase[] = [
  {
    id: 'brief',
    label: 'Brief recebido',
    theatre: 'Preparando investigação...',
    startsAt: 0,
    endsAt: 10,
  },
  {
    id: 'hypotheses',
    label: 'Hipóteses',
    theatre: 'Decompondo brief em hipóteses...',
    startsAt: 10,
    endsAt: 20,
  },
  {
    id: 'queries',
    label: 'Consultas',
    theatre: 'Consultando fontes de dados...',
    startsAt: 20,
    endsAt: 50,
  },
  {
    id: 'findings',
    label: 'Evidências',
    theatre: 'Correlacionando achados...',
    startsAt: 50,
    endsAt: 105,
  },
  {
    id: 'correlation',
    label: 'Grafo e MITRE',
    theatre: 'Construindo cadeia de ataque...',
    startsAt: 105,
    endsAt: 190,
  },
  {
    id: 'report',
    label: 'Relatório',
    theatre: 'Gerando relatório...',
    startsAt: 190,
    endsAt: 250,
  },
  {
    id: 'complete',
    label: 'Pronto',
    theatre: 'Relatório pronto para apresentação.',
    startsAt: 250,
    endsAt: TOTAL_SECONDS,
  },
];

export const HYPOTHESES: DemoHypothesis[] = [
  {
    id: 'h1',
    title: 'Anel de contas-laranja com baixa maturidade cadastral',
    detail: '20 contas recebem Pix de valores próximos e redistribuem em até 18 minutos.',
    confidence: 0.92,
    tactic: 'Defense Evasion',
  },
  {
    id: 'h2',
    title: 'SIM swap em cliente high-value como origem do pico',
    detail: 'Dispositivo, biometria e operadora mudaram antes de uma sequência de Pix.',
    confidence: 0.88,
    tactic: 'Credential Access',
  },
  {
    id: 'h3',
    title: 'Scraping de Open Finance usado para selecionar vítimas',
    detail: 'Consultas em massa antecederam as transferências fraudulentas.',
    confidence: 0.84,
    tactic: 'Collection',
  },
  {
    id: 'h4',
    title: 'Campanha de boleto falso sustentando cash-out',
    detail: 'Boletos recém-criados aparecem como ponte entre vítimas e laranjas.',
    confidence: 0.79,
    tactic: 'Impact',
  },
];

export const QUERIES: DemoQuery[] = [
  {
    id: 'q1',
    source: 'Pix SPI simplificado',
    query: 'pix.transferências | agrupar por chave destino, device_id, janela 30m',
    startsAt: 20,
    endsAt: 36,
    rows: 100500,
  },
  {
    id: 'q2',
    source: 'Auth OAuth2 + biometria',
    query: 'auth.logins | detectar troca de SIM, device novo, falha biométrica',
    startsAt: 25,
    endsAt: 43,
    rows: 50200,
  },
  {
    id: 'q3',
    source: 'Open Finance Bacen',
    query: 'openfinance.access | buscar scraping por cliente e consentimento',
    startsAt: 31,
    endsAt: 49,
    rows: 10030,
  },
  {
    id: 'q4',
    source: 'Boleto e antifraude',
    query: 'boletos.criados | correlacionar beneficiário, pagador, IP e recebedor',
    startsAt: 37,
    endsAt: 59,
    rows: 5050,
  },
];

export const FINDINGS: DemoFinding[] = [
  {
    id: 'f1',
    severity: 'critical',
    title: 'R$ 1,84 mi em Pix atravessam 20 contas-laranja',
    description: 'O padrão de cash-out usa repasses abaixo do limite manual e repete dispositivo virtualizado.',
    evidence: '20 contas | 500 transações | 14 recebedores finais',
    appearsAt: 49,
  },
  {
    id: 'f2',
    severity: 'high',
    title: 'SIM swap antecede 37 Pix de uma conta high-value',
    description: 'Troca de operadora e primeiro login em aparelho novo ocorreram 11 minutos antes do saque.',
    evidence: 'Cliente FP-8841 | device novo | biometria reprovada',
    appearsAt: 67,
  },
  {
    id: 'f3',
    severity: 'high',
    title: 'Scraping Open Finance escolheu vítimas com saldo alto',
    description: 'A mesma aplicação consultou múltiplos consentimentos e focou contas com limite disponível.',
    evidence: '30 anomalias | 6 clientes | app_id ofx-ghost',
    appearsAt: 85,
  },
  {
    id: 'f4',
    severity: 'medium',
    title: 'Boletos falsos fecham a rota de saída',
    description: 'Boletos de pequenos valores foram usados para testar titularidade antes do repasse maior.',
    evidence: '50 boletos | 8 beneficiários | 3 CNPJs recém-abertos',
    appearsAt: 101,
  },
];

export const GRAPH_NODES: DemoGraphNode[] = [
  { id: 'victim', label: 'Cliente high-value', x: 8, y: 42, tone: 'account', appearsAt: 110 },
  { id: 'device', label: 'Aparelho novo', x: 25, y: 22, tone: 'device', appearsAt: 116 },
  { id: 'openfinance', label: 'Open Finance scraping', x: 28, y: 64, tone: 'risk', appearsAt: 122 },
  { id: 'mule1', label: 'Conta-laranja A', x: 50, y: 34, tone: 'pix', appearsAt: 130 },
  { id: 'mule2', label: 'Conta-laranja B', x: 58, y: 70, tone: 'pix', appearsAt: 138 },
  { id: 'boleto', label: 'Boleto falso', x: 74, y: 48, tone: 'merchant', appearsAt: 149 },
  { id: 'cashout', label: 'Recebedor final', x: 91, y: 50, tone: 'risk', appearsAt: 163 },
];

export const GRAPH_EDGES: DemoGraphEdge[] = [
  { from: 'device', to: 'victim', label: 'login novo', appearsAt: 120 },
  { from: 'openfinance', to: 'victim', label: 'seleção', appearsAt: 128 },
  { from: 'victim', to: 'mule1', label: 'Pix R$ 312k', appearsAt: 136 },
  { from: 'victim', to: 'mule2', label: 'Pix R$ 184k', appearsAt: 143 },
  { from: 'mule1', to: 'boleto', label: 'teste boleto', appearsAt: 155 },
  { from: 'mule2', to: 'boleto', label: 'ponte', appearsAt: 160 },
  { from: 'boleto', to: 'cashout', label: 'cash-out', appearsAt: 170 },
];

export const MITRE_CELLS: DemoMitreCell[] = [
  { tactic: 'Credential Access', technique: 'T1110', label: 'Brute force / OTP abuse', appearsAt: 114, intensity: 2 },
  { tactic: 'Defense Evasion', technique: 'T1090', label: 'Proxy / anonymizer', appearsAt: 130, intensity: 2 },
  { tactic: 'Collection', technique: 'T1213', label: 'Data from information repositories', appearsAt: 146, intensity: 3 },
  { tactic: 'Command and Control', technique: 'T1102', label: 'Web service relay', appearsAt: 161, intensity: 1 },
  { tactic: 'Exfiltration', technique: 'T1041', label: 'Exfiltration over C2 channel', appearsAt: 177, intensity: 2 },
  { tactic: 'Impact', technique: 'T1499', label: 'Financial impact', appearsAt: 186, intensity: 3 },
];

export const REGULATORY_ARTIFACTS: DemoRegulatoryArtifact[] = [
  {
    id: 'psc',
    norma: 'Res. BCB 85/2021 · Art. 3 e 4',
    titulo: 'Política de Segurança Cibernética em execução',
    detalhe:
      'A investigação roda dentro do escopo previsto na PSC vigente da fintech — agentes, fontes consultadas e ações de contenção já mapeados no documento aprovado pela diretoria.',
    appearsAt: 11,
  },
  {
    id: 'registro',
    norma: 'Res. BCB 85/2021 · Art. 8',
    titulo: 'Registro de incidente relevante aberto',
    detalhe:
      'Limiar de relevância cruzado: valor financeiro envolvido + dado pessoal de cliente alto valor. Incidente classificado e datado no momento do achado.',
    appearsAt: 50,
  },
  {
    id: 'cadeia',
    norma: 'LGPD · Art. 48 e 50',
    titulo: 'Cadeia probatória sendo arquivada',
    detalhe:
      'Cada query, cada prompt, cada decisão dos agentes fica em ledger imutável. Auditor externo refaz a investigação do zero com os mesmos dados e a mesma sequência.',
    appearsAt: 105,
  },
  {
    id: 'comunicacao',
    norma: 'Res. BCB 85/2021 · Art. 9',
    titulo: 'Relógio de comunicação ao Bacen ligado',
    detalhe:
      'Contagem regressiva de 24 horas começa no momento da detecção. Modelo de comunicação imediata já populado com classificação, vetores e medidas tomadas até agora.',
    appearsAt: 190,
  },
  {
    id: 'continuidade',
    norma: 'IN BCB 314',
    titulo: 'Evidência arquivada como teste periódico',
    detalhe:
      'Investigação completa fica disponível como artefato de teste do plano de continuidade — vale como execução de drill anual exigido para fintechs reguladas.',
    appearsAt: 250,
  },
];

export const REPORT_PAGES: DemoReportPage[] = [
  { page: 1, title: 'Resumo executivo', bullets: ['Fraude organizada confirmada', 'R$ 1,84 mi sob risco', '20 contas-laranja priorizadas'] },
  { page: 2, title: 'Linha do tempo', bullets: ['SIM swap', 'login em aparelho novo', 'pico Pix', 'cash-out via boleto'] },
  { page: 3, title: 'Hipóteses testadas', bullets: ['4 hipóteses', '3 confirmadas', '1 parcialmente confirmada'] },
  { page: 4, title: 'Evidências Pix', bullets: ['500 transferências suspeitas', '14 recebedores finais', 'janela média 18 min'] },
  { page: 5, title: 'Open Finance', bullets: ['30 anomalias', 'scraping por consentimento', 'correlação com saldo'] },
  { page: 6, title: 'Grafo de ataque', bullets: ['7 nós críticos', '2 rotas de cash-out', '1 aplicativo pivô'] },
  { page: 7, title: 'MITRE e controles', bullets: ['6 técnicas mapeadas', '3 gaps de detecção', '2 playbooks acionáveis'] },
  { page: 8, title: 'Contenção imediata', bullets: ['bloquear contas', 'revisar chaves Pix', 'congelar boletos suspeitos'] },
  { page: 9, title: 'Impacto financeiro', bullets: ['R$ 1,84 mi rastreado', 'R$ 1,12 mi recuperável', 'R$ 27,40 custo IA'] },
  { page: 10, title: 'Próximos passos', bullets: ['notificação regulatória', 'regras antifraude', 'monitoramento 72h'] },
];

function clamp(n: number, min = 0, max = 1): number {
  return Math.min(max, Math.max(min, n));
}

export function formatElapsed(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

export function getDemoPhase(elapsedSeconds: number): DemoPhase {
  return (
    DEMO_PHASES.find(
      (phase) => elapsedSeconds >= phase.startsAt && elapsedSeconds < phase.endsAt,
    ) ?? DEMO_PHASES[DEMO_PHASES.length - 1]
  );
}

export function getDemoState(elapsedSecondsInput: number): DemoState {
  const elapsedSeconds = Math.min(Math.max(elapsedSecondsInput, 0), TOTAL_SECONDS);
  const activePhase = getDemoPhase(elapsedSeconds);
  const visibleHypotheses = HYPOTHESES.filter((_, index) => elapsedSeconds >= 11 + index * 3);
  const activeQueries = QUERIES.map((query) => {
    const progress = clamp((elapsedSeconds - query.startsAt) / (query.endsAt - query.startsAt));
    const status: 'queued' | 'running' | 'done' =
      progress <= 0 ? 'queued' : progress >= 1 ? 'done' : 'running';
    return { ...query, progress, status };
  });
  const visibleFindings = FINDINGS.filter((finding) => elapsedSeconds >= finding.appearsAt);
  const visibleGraphNodes = GRAPH_NODES.filter((node) => elapsedSeconds >= node.appearsAt);
  const visibleGraphEdges = GRAPH_EDGES.filter((edge) => elapsedSeconds >= edge.appearsAt);
  const visibleMitreCells = MITRE_CELLS.filter((cell) => elapsedSeconds >= cell.appearsAt);
  const visibleRegulatoryArtifacts = REGULATORY_ARTIFACTS.filter(
    (artifact) => elapsedSeconds >= artifact.appearsAt,
  );
  const activeRegulatoryArtifact =
    visibleRegulatoryArtifacts.length > 0
      ? visibleRegulatoryArtifacts[visibleRegulatoryArtifacts.length - 1]
      : null;
  const reportReady = elapsedSeconds >= 235;
  const costUsd = 0.35 + elapsedSeconds * 0.1;
  const humanHours = 18;
  const humanRate = 125;
  const humanCostUsd = humanHours * humanRate;
  const hoursSaved = clamp(elapsedSeconds / 240) * humanHours;

  return {
    elapsedSeconds,
    totalSeconds: TOTAL_SECONDS,
    overallProgress: elapsedSeconds / TOTAL_SECONDS,
    activePhase,
    visibleHypotheses,
    activeQueries,
    visibleFindings,
    visibleGraphNodes,
    visibleGraphEdges,
    visibleMitreCells,
    reportPages: reportReady ? REPORT_PAGES : REPORT_PAGES.slice(0, Math.max(1, Math.floor((elapsedSeconds - 190) / 6))),
    reportReady,
    visibleRegulatoryArtifacts,
    activeRegulatoryArtifact,
    metrics: {
      elapsedLabel: formatElapsed(elapsedSeconds),
      costUsd,
      humanCostUsd,
      hoursSaved,
      transactionsScanned: Math.round(clamp(elapsedSeconds / 75) * 100500),
      accountsCorrelated: Math.round(clamp((elapsedSeconds - 45) / 90) * 50000),
      pixValueBrl: Math.round(clamp((elapsedSeconds - 58) / 100) * 1840000),
    },
  };
}

export function runCinematicConsistencyChecks(iterations = 10): string[] {
  const failures: string[] = [];
  for (let i = 0; i < iterations; i += 1) {
    const state = getDemoState(TOTAL_SECONDS + i);
    if (!state.reportReady) failures.push(`iteration ${i}: report not ready`);
    if (state.visibleFindings.length !== FINDINGS.length) failures.push(`iteration ${i}: missing findings`);
    if (state.visibleGraphNodes.length !== GRAPH_NODES.length) failures.push(`iteration ${i}: graph incomplete`);
    if (state.visibleMitreCells.length !== MITRE_CELLS.length) failures.push(`iteration ${i}: MITRE heatmap incomplete`);
    if (state.metrics.costUsd >= state.metrics.humanCostUsd) failures.push(`iteration ${i}: cost comparison inverted`);
  }
  return failures;
}
