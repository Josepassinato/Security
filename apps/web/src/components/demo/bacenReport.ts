/**
 * Bacen 24h communication generator.
 *
 * Takes the demo investigation state and renders a Markdown communication
 * draft that mirrors the structure a fintech compliance officer would file
 * after a cyber-incident of regulatory relevance, per Res. BCB 85/2021 Art. 9.
 *
 * Pure function — no DOM, no I/O. The download wiring lives in the consumer
 * (CinematicPixDemo) so this module stays testable and reusable when the
 * real CaseWorkspace plugs in a non-demo state shape.
 */

import {
  FINDINGS,
  HERO_BRIEF,
  MITRE_CELLS,
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

function addHours(d: Date, hours: number): Date {
  return new Date(d.getTime() + hours * 60 * 60 * 1000);
}

const SEVERITY_LABEL: Record<string, string> = {
  critical: 'Crítico',
  high: 'Alto',
  medium: 'Médio',
  low: 'Baixo',
};

function escapeCell(text: string): string {
  return text.replace(/\|/g, '\\|');
}

export interface BacenCommunicationInput {
  state: DemoState;
  now?: Date;
  institutionName?: string;
  institutionCnpj?: string;
  caseId?: string;
}

export function buildBacenCommunication(input: BacenCommunicationInput): string {
  const {
    state,
    now = new Date(),
    institutionName = 'FinPlay Pagamentos S.A. (cenário demonstrativo)',
    institutionCnpj = '00.000.000/0001-00',
    caseId = 'DEMO-FINPLAY-2026',
  } = input;

  const deadline = addHours(now, 24);
  const detectedAt = new Date(now.getTime() - state.elapsedSeconds * 1000);

  const lines: string[] = [];

  lines.push(`# Comunicação imediata de incidente cibernético — Bacen`);
  lines.push('');
  lines.push(`> Conforme **Res. BCB 85/2021, Art. 9** — comunicação em até 24 horas da detecção.`);
  lines.push(`> Documento gerado pelo Quarry como rascunho para validação humana antes do envio oficial.`);
  lines.push('');
  lines.push(`**Identificador do caso:** \`${caseId}\``);
  lines.push(`**Instituição:** ${institutionName}`);
  lines.push(`**CNPJ:** ${institutionCnpj}`);
  lines.push(`**Detectado em:** ${formatDateTime(detectedAt)}`);
  lines.push(`**Documento emitido em:** ${formatDateTime(now)}`);
  lines.push(`**Prazo regulatório de comunicação (24h):** ${formatDateTime(deadline)}`);
  lines.push('');
  lines.push('---');
  lines.push('');

  lines.push(`## 1. Classificação do incidente`);
  lines.push('');
  lines.push(`- **Natureza:** fraude organizada explorando rail Pix com indícios de SIM swap e scraping de Open Finance.`);
  lines.push(`- **Relevância (Art. 8):** confirmada — valor financeiro envolvido + dado pessoal de cliente de alto valor.`);
  lines.push(`- **Valor financeiro sob risco:** ${BRL.format(state.metrics.pixValueBrl)}.`);
  lines.push(`- **Escala da análise:** ${INT.format(state.metrics.transactionsScanned)} transações varridas, ${INT.format(state.metrics.accountsCorrelated)} contas correlacionadas.`);
  lines.push(`- **Tempo entre detecção e este documento:** ${state.metrics.elapsedLabel}.`);
  lines.push('');

  lines.push(`## 2. Resumo executivo`);
  lines.push('');
  lines.push(HERO_BRIEF);
  lines.push('');

  lines.push(`## 3. Evidências consolidadas`);
  lines.push('');
  lines.push(`| # | Severidade | Achado | Evidência |`);
  lines.push(`|---|---|---|---|`);
  FINDINGS.forEach((f, idx) => {
    const sev = SEVERITY_LABEL[f.severity] ?? f.severity;
    lines.push(`| ${idx + 1} | ${sev} | ${escapeCell(f.title)} | ${escapeCell(f.evidence)} |`);
  });
  lines.push('');
  FINDINGS.forEach((f, idx) => {
    lines.push(`**${idx + 1}. ${f.title}** — ${f.description}`);
    lines.push('');
  });

  lines.push(`## 4. Controles regulatórios ativados`);
  lines.push('');
  lines.push(`Mapeamento explícito dos artefatos cobertos durante a investigação. Cada item está vinculado a evidência arquivada no ledger imutável do caso.`);
  lines.push('');
  REGULATORY_ARTIFACTS.forEach((art) => {
    const satisfied = state.visibleRegulatoryArtifacts.some((a) => a.id === art.id);
    const mark = satisfied ? '[x]' : '[ ]';
    lines.push(`- ${mark} **${art.norma} — ${art.titulo}**`);
    lines.push(`  ${art.detalhe}`);
  });
  lines.push('');

  lines.push(`## 5. Medidas adotadas`);
  lines.push('');
  lines.push(`- Contas envolvidas marcadas para revisão antifraude prioritária.`);
  lines.push(`- Chaves Pix das contas-laranja sinalizadas para reanálise junto ao DICT.`);
  lines.push(`- Boletos suspeitos congelados até validação manual.`);
  lines.push(`- Acesso por consentimento Open Finance do app suspeito revogado preventivamente.`);
  lines.push(`- Ledger probatório iniciado conforme **LGPD Art. 48 e 50**.`);
  lines.push('');

  lines.push(`## 6. Vetores técnicos identificados (MITRE ATT&CK)`);
  lines.push('');
  lines.push(`| Tática | Técnica | Descrição |`);
  lines.push(`|---|---|---|`);
  MITRE_CELLS.forEach((cell) => {
    lines.push(`| ${escapeCell(cell.tactic)} | ${escapeCell(cell.technique)} | ${escapeCell(cell.label)} |`);
  });
  lines.push('');

  lines.push(`## 7. Próximos passos`);
  lines.push('');
  lines.push(`1. Validação humana deste rascunho pelo DPO + responsável de segurança cibernética antes do envio oficial.`);
  lines.push(`2. Submissão pelo canal oficial Bacen dentro do prazo de 24h indicado no cabeçalho.`);
  lines.push(`3. Comunicação à ANPD se confirmado vazamento de dado pessoal (LGPD Art. 48 §1º).`);
  lines.push(`4. Monitoramento intensivo das contas correlacionadas por 72h.`);
  lines.push(`5. Atualização da Política de Segurança Cibernética (PSC) se for identificada lacuna de controle.`);
  lines.push('');

  lines.push(`## 8. Cadeia probatória e continuidade`);
  lines.push('');
  lines.push(`- Cada query, prompt e decisão dos agentes Quarry fica registrada em ledger imutável (Res. BCB 85/2021 Art. 8; LGPD Art. 48 e 50).`);
  lines.push(`- Este caso é arquivado como **artefato de teste do plano de continuidade**, atendendo IN BCB 314 (drill anual).`);
  lines.push(`- Auditor externo consegue refazer a investigação do zero com os mesmos dados e a mesma sequência.`);
  lines.push('');

  lines.push(`---`);
  lines.push('');
  lines.push(`_Documento gerado automaticamente pelo Quarry — SOC econômico para fintechs BR. Este é um rascunho assistido por IA; envio oficial requer revisão humana qualificada._`);

  return lines.join('\n');
}

export function buildBacenFilename(now: Date = new Date()): string {
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  const hh = String(now.getHours()).padStart(2, '0');
  const min = String(now.getMinutes()).padStart(2, '0');
  return `bacen-24h-${yyyy}${mm}${dd}-${hh}${min}.md`;
}
