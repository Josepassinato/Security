/**
 * ANPD breach notification generator (LGPD Art. 48 §1º + IN ANPD 03/2024).
 *
 * Espelha `bacenReport.ts` mas pra notificação à Autoridade Nacional de
 * Proteção de Dados quando o incidente cibernético envolve dado pessoal.
 *
 * Pure function — no DOM, no I/O. Wiring de download fica no consumer.
 *
 * Critério de disparo: o caso precisa ter sido classificado como
 * "vazamento de dado pessoal" pelo detector `pii_breach_detector` no
 * backend. Este template não decide — só renderiza.
 */

import {
  FINDINGS,
  HERO_BRIEF,
  REGULATORY_ARTIFACTS,
  type DemoState,
} from './cinematicScenario';

const BRL = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 2,
});

const INT = new Intl.NumberFormat('pt-BR');

function formatDateTime(now: Date): string {
  const date = now.toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo' });
  const time = now.toLocaleTimeString('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    hour: '2-digit',
    minute: '2-digit',
  });
  return `${date} ${time} (BRT)`;
}

function escapeCell(text: string): string {
  return text.replace(/\|/g, '\\|');
}

const SEVERITY_LABEL: Record<string, string> = {
  critical: 'Crítico',
  high: 'Alto',
  medium: 'Médio',
  low: 'Baixo',
};

export interface AnpdCommunicationInput {
  state: DemoState;
  now?: Date;
  controllerName?: string;
  controllerCnpj?: string;
  dpoName?: string;
  dpoEmail?: string;
  caseId?: string;
  affectedSubjectsCount?: number;
  affectedDataCategories?: string[];
}

const DEFAULT_DATA_CATEGORIES = [
  'dados cadastrais (CPF, nome, e-mail, telefone)',
  'dados de identificação financeira (chave Pix, conta corrente)',
  'metadados transacionais (valores, horários, IPs, dispositivos)',
];

export function buildAnpdCommunication(input: AnpdCommunicationInput): string {
  const {
    state,
    now = new Date(),
    controllerName = 'FinPlay Pagamentos S.A. (cenário demonstrativo)',
    controllerCnpj = '00.000.000/0001-00',
    dpoName = 'Encarregado de Dados (DPO) — a designar',
    dpoEmail = 'dpo@exemplo.com.br',
    caseId = 'DEMO-FINPLAY-2026',
    affectedSubjectsCount,
    affectedDataCategories = DEFAULT_DATA_CATEGORIES,
  } = input;

  const detectedAt = new Date(now.getTime() - state.elapsedSeconds * 1000);

  const lines: string[] = [];

  lines.push(`# Comunicação de incidente de segurança com dados pessoais — ANPD`);
  lines.push('');
  lines.push(
    `> Conforme **LGPD Art. 48 §1º** e **IN ANPD nº 03/2024** — notificação ` +
      `à Autoridade Nacional de Proteção de Dados em prazo razoável após ` +
      `tomada de conhecimento.`,
  );
  lines.push(
    `> Documento gerado pelo Quarry como rascunho para validação humana ` +
      `do DPO antes do envio oficial.`,
  );
  lines.push('');
  lines.push(`**Identificador do caso:** \`${caseId}\``);
  lines.push(`**Controlador:** ${controllerName}`);
  lines.push(`**CNPJ:** ${controllerCnpj}`);
  lines.push(`**Encarregado (DPO):** ${dpoName}`);
  lines.push(`**Contato do DPO:** ${dpoEmail}`);
  lines.push(`**Detectado em:** ${formatDateTime(detectedAt)}`);
  lines.push(`**Documento emitido em:** ${formatDateTime(now)}`);
  lines.push('');
  lines.push('---');
  lines.push('');

  lines.push(`## 1. Natureza do incidente`);
  lines.push('');
  lines.push(
    `Incidente cibernético com exposição potencial de dados pessoais de ` +
      `titulares clientes da instituição, decorrente de tentativa de fraude ` +
      `organizada envolvendo rail Pix, indícios de SIM swap e exploração de ` +
      `consentimento Open Finance.`,
  );
  lines.push('');
  lines.push(HERO_BRIEF);
  lines.push('');

  lines.push(`## 2. Categorias de dados pessoais afetadas`);
  lines.push('');
  affectedDataCategories.forEach((cat) => {
    lines.push(`- ${cat}`);
  });
  lines.push('');
  lines.push(
    `> Dados sensíveis (LGPD Art. 5º, II) **não confirmados** nesta análise. ` +
      `Caso a apuração identifique, este rascunho será atualizado e o regime ` +
      `de notificação aos titulares (Art. 48 caput) será ativado.`,
  );
  lines.push('');

  lines.push(`## 3. Número estimado de titulares afetados`);
  lines.push('');
  if (typeof affectedSubjectsCount === 'number') {
    lines.push(`- **Estimativa atual:** ${INT.format(affectedSubjectsCount)} titulares.`);
  } else {
    lines.push(
      `- **Estimativa atual:** em apuração. Limite superior derivado da ` +
        `correlação de ${INT.format(state.metrics.accountsCorrelated)} contas e ` +
        `${INT.format(state.metrics.transactionsScanned)} transações analisadas.`,
    );
  }
  lines.push(
    `- Valor financeiro sob risco no episódio: ${BRL.format(state.metrics.pixValueBrl)}.`,
  );
  lines.push('');

  lines.push(`## 4. Riscos para os titulares`);
  lines.push('');
  lines.push(`- Apropriação indevida de saldo via transações Pix fraudulentas.`);
  lines.push(`- Uso indevido de identidade para abertura de novas relações.`);
  lines.push(`- Engenharia social subsequente (phishing direcionado) com base nos dados extraídos.`);
  lines.push(`- Reputacional e psicológico ao titular ao tomar conhecimento.`);
  lines.push('');

  lines.push(`## 5. Medidas técnicas e de segurança adotadas`);
  lines.push('');
  lines.push(`- Contas envolvidas marcadas para revisão antifraude prioritária.`);
  lines.push(`- Chaves Pix das contas-laranja sinalizadas no DICT.`);
  lines.push(`- Boletos suspeitos congelados até validação manual.`);
  lines.push(`- Consentimento Open Finance do app suspeito revogado preventivamente.`);
  lines.push(`- Ledger probatório iniciado para preservação de evidência (LGPD Art. 50).`);
  lines.push(`- Comunicação ao Bacen disparada em paralelo (Res. BCB 85/2021 Art. 9).`);
  lines.push('');

  lines.push(`## 6. Evidência consolidada do incidente`);
  lines.push('');
  lines.push(`| # | Severidade | Achado | Evidência |`);
  lines.push(`|---|---|---|---|`);
  FINDINGS.forEach((f, idx) => {
    const sev = SEVERITY_LABEL[f.severity] ?? f.severity;
    lines.push(`| ${idx + 1} | ${sev} | ${escapeCell(f.title)} | ${escapeCell(f.evidence)} |`);
  });
  lines.push('');

  lines.push(`## 7. Mapeamento regulatório`);
  lines.push('');
  REGULATORY_ARTIFACTS.forEach((art) => {
    const satisfied = state.visibleRegulatoryArtifacts.some((a) => a.id === art.id);
    const mark = satisfied ? '[x]' : '[ ]';
    lines.push(`- ${mark} **${art.norma} — ${art.titulo}**`);
    lines.push(`  ${art.detalhe}`);
  });
  lines.push('');

  lines.push(`## 8. Próximos passos do controlador`);
  lines.push('');
  lines.push(`1. Validação humana deste rascunho pelo DPO antes do envio oficial.`);
  lines.push(`2. Submissão à ANPD via canal oficial (formulário ANPD ou e-mail).`);
  lines.push(`3. Avaliação se titulares devem ser notificados individualmente (Art. 48 caput).`);
  lines.push(`4. Atualização do registro de operações de tratamento (Art. 37).`);
  lines.push(`5. Revisão do RIPD aplicável e ajuste das salvaguardas técnicas.`);
  lines.push('');

  lines.push(`## 9. Cadeia probatória`);
  lines.push('');
  lines.push(
    `Cada decisão, query e correlação dos agentes Quarry está arquivada em ` +
      `ledger imutável com hash chain (replayable por auditor externo). Esta ` +
      `comunicação foi gerada a partir desses registros — não é redação ` +
      `posterior.`,
  );
  lines.push('');

  lines.push(`---`);
  lines.push('');
  lines.push(
    `_Documento gerado automaticamente pelo Quarry. Rascunho assistido por IA; ` +
      `envio oficial requer revisão humana do Encarregado (DPO)._`,
  );

  return lines.join('\n');
}

export function buildAnpdFilename(now: Date = new Date()): string {
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  const hh = String(now.getHours()).padStart(2, '0');
  const min = String(now.getMinutes()).padStart(2, '0');
  return `anpd-incidente-${yyyy}${mm}${dd}-${hh}${min}.md`;
}
