import type { PldCaseDecision, PldCaseRecord, PldCaseStatus } from './cases';
import type { PldAiAnalyst, PldDossier, PldInput, PldThresholds } from './engine';

interface BackendAnalyzeResponse {
  mode: 'backend';
  importId: string;
  payloadHash: string;
  transactionCount: number;
  dossier: PldDossier;
}

interface BackendCasesResponse {
  cases: Array<{
    id: string;
    createdAt: string;
    updatedAt?: string;
    status: PldCaseStatus;
    importId?: string | null;
    dossier: PldDossier;
    decisions?: PldCaseDecision[];
  }>;
}

export interface PldDecisionMemoryItem {
  caseId: string;
  dossierId: string;
  status: PldCaseStatus;
  riskScore: number;
  severity: string;
  similarityScore: number;
  overlapRules: string[];
  overlapEntities: string[];
  lastDecision?: PldCaseDecision;
}

export interface PldAiAnalystResponse {
  caseId: string;
  dossierId: string;
  aiAnalyst: PldAiAnalyst;
  decisionMemory: PldDecisionMemoryItem[];
  operatorBrief: {
    headline: string;
    recommendedAction?: string;
    memoryInsight: string;
    guardrail: string;
  };
}

export interface PldCustomerRiskRecord {
  customerId: string;
  riskScore: number;
  severity: string;
  totalCases: number;
  openCases: number;
  escalatedCases: number;
  falsePositiveCases: number;
  totalAmount: number;
  topRules: Array<{ ruleId: string; count: number }>;
  evidence: Array<{ caseId: string; dossierId: string; status: string; riskScore: number; severity: string }>;
  lastCaseAt?: string | null;
  updatedAt?: string | null;
}

export interface PldRuleSimulationResponse {
  mode: string;
  baseline?: { riskScore: number; severity: string; findingCount: number; rules: string[] };
  simulated?: { riskScore: number; severity: string; findingCount: number; rules: string[] };
  delta?: { riskScore: number; findingCount: number; addedRules: string[]; removedRules: string[] };
  sampleSize?: number;
  openCases?: number;
  falsePositiveCases?: number;
  falsePositivePressure?: number;
  strictnessDelta?: number;
  estimatedImpact?: string;
  recommendation?: string;
  nextStep?: string;
}

export interface PldRuleVersion {
  id: string;
  versionName: string;
  thresholds: Partial<PldThresholds>;
  status: string;
  rationale: string;
  submittedAt?: string | null;
  approvedAt?: string | null;
  rejectedAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
  note?: string;
}

export interface PldExecutiveReport {
  generatedAt: string;
  executiveSummary: string;
  kpis: {
    totalCases: number;
    openCases: number;
    criticalCases: number;
    escalatedCases: number;
    falsePositiveCases: number;
    overdueCases: number;
  };
  topRules: Array<{ ruleId: string; count: number }>;
  topCustomers: PldCustomerRiskRecord[];
  ruleVersionStatus: Record<string, number>;
  committeeRecommendations: string[];
}

export interface PldMonthlyMetrics {
  month: string;
  period: { start: string; end: string };
  kpis: {
    alerts: number;
    cases: number;
    archived: number;
    escalated: number;
    slaTracked: number;
    slaOverdue: number;
    slaComplianceRate: number;
    criticalCases: number;
    averageRiskScore: number;
  };
  noisyRules: Array<{ ruleId: string; count: number; falsePositive: number; noiseScore: number }>;
  recommendations: string[];
}

export interface PldAuditEntry {
  id: string;
  actorEmail: string;
  actorRole: string;
  action: string;
  resource: string;
  resourceId: string;
  details: Record<string, unknown>;
  prevHash?: string | null;
  entryHash: string;
  createdAt?: string | null;
}

export interface PldIngestionJob {
  id: string;
  name: string;
  sourceType: string;
  status: string;
  intervalSeconds: number;
  autoCaseMinScore: number;
  config: Record<string, unknown>;
  lastRunAt?: string | null;
  nextRunAt?: string | null;
  lastResult: Record<string, unknown>;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface PldRegulatoryExport {
  id: string;
  caseId: string;
  exportType: string;
  status: string;
  structuredPayload: Record<string, unknown>;
  approvalNote: string;
  approvedAt?: string | null;
  exportedAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      'content-type': 'application/json',
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function analyzePldFtBackend(input: PldInput): Promise<BackendAnalyzeResponse> {
  return requestJson<BackendAnalyzeResponse>('/api/v1/pld-ft/analyze', {
    method: 'POST',
    body: JSON.stringify({ sourceType: 'ui-json', ...input }),
  });
}

export async function savePldCaseBackend(dossier: PldDossier, importId?: string | null): Promise<PldCaseRecord> {
  const record = await requestJson<PldCaseRecord>('/api/v1/pld-ft/cases', {
    method: 'POST',
    body: JSON.stringify({ dossier, importId: importId || undefined, status: 'novo' }),
  });
  return record;
}

export async function listPldCasesBackend(): Promise<PldCaseRecord[]> {
  const payload = await requestJson<BackendCasesResponse>('/api/v1/pld-ft/cases');
  return payload.cases.map((record) => ({
    ...record,
    decisions: record.decisions || [],
  }));
}

export async function addPldCaseDecisionBackend(
  caseId: string,
  decision: Omit<PldCaseDecision, 'decidedAt'>,
): Promise<PldCaseRecord> {
  return requestJson<PldCaseRecord>(`/api/v1/pld-ft/cases/${caseId}/decision`, {
    method: 'PATCH',
    body: JSON.stringify(decision),
  });
}

export async function downloadPldCaseReportBackend(caseId: string): Promise<Blob> {
  const response = await fetch(`/api/v1/pld-ft/cases/${caseId}/report.pdf`);
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  return response.blob();
}

export async function getPldCaseAiAnalystBackend(caseId: string): Promise<PldAiAnalystResponse> {
  return requestJson<PldAiAnalystResponse>(`/api/v1/pld-ft/cases/${caseId}/ai-analyst`);
}

export async function savePldThresholdsBackend(thresholds: Partial<PldThresholds>): Promise<void> {
  await requestJson('/api/v1/pld-ft/thresholds', {
    method: 'PUT',
    body: JSON.stringify({ thresholds }),
  });
}

export async function listPldCustomerRiskBackend(): Promise<PldCustomerRiskRecord[]> {
  const payload = await requestJson<{ customers: PldCustomerRiskRecord[] }>('/api/v1/pld-ft/customer-risk');
  return payload.customers;
}

export async function recomputePldCustomerRiskBackend(): Promise<PldCustomerRiskRecord[]> {
  const payload = await requestJson<{ customers: PldCustomerRiskRecord[] }>('/api/v1/pld-ft/customer-risk/recompute', {
    method: 'POST',
    body: JSON.stringify({}),
  });
  return payload.customers;
}

export async function simulatePldRulesBackend(thresholds: Partial<PldThresholds>): Promise<PldRuleSimulationResponse> {
  return requestJson<PldRuleSimulationResponse>('/api/v1/pld-ft/rule-simulations', {
    method: 'POST',
    body: JSON.stringify({ thresholds }),
  });
}

export async function listPldRuleVersionsBackend(): Promise<PldRuleVersion[]> {
  const payload = await requestJson<{ versions: PldRuleVersion[] }>('/api/v1/pld-ft/rule-versions');
  return payload.versions;
}

export async function createPldRuleVersionBackend(
  versionName: string,
  thresholds: Partial<PldThresholds>,
  rationale: string,
): Promise<PldRuleVersion> {
  return requestJson<PldRuleVersion>('/api/v1/pld-ft/rule-versions', {
    method: 'POST',
    body: JSON.stringify({ versionName, thresholds, rationale }),
  });
}

export async function decidePldRuleVersionBackend(
  versionId: string,
  action: 'submit' | 'approve' | 'reject',
  note = '',
): Promise<PldRuleVersion> {
  return requestJson<PldRuleVersion>(`/api/v1/pld-ft/rule-versions/${versionId}/${action}`, {
    method: 'PATCH',
    body: JSON.stringify({ note }),
  });
}

export async function getPldExecutiveReportBackend(): Promise<PldExecutiveReport> {
  return requestJson<PldExecutiveReport>('/api/v1/pld-ft/executive-report');
}

export async function downloadPldExecutiveReportBackend(): Promise<Blob> {
  const response = await fetch('/api/v1/pld-ft/executive-report.pdf');
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  return response.blob();
}

export async function getPldMonthlyMetricsBackend(month?: string): Promise<PldMonthlyMetrics> {
  const suffix = month ? `?month=${encodeURIComponent(month)}` : '';
  return requestJson<PldMonthlyMetrics>(`/api/v1/pld-ft/monthly-metrics${suffix}`);
}

export async function listPldAuditLogBackend(): Promise<{ chainVerifiedForWindow: boolean; entries: PldAuditEntry[] }> {
  return requestJson<{ chainVerifiedForWindow: boolean; entries: PldAuditEntry[] }>('/api/v1/pld-ft/audit-log');
}

export async function ingestPldStreamBackend(input: PldInput, autoCaseMinScore = 65): Promise<BackendAnalyzeResponse & { createdCase?: PldCaseRecord | null }> {
  return requestJson<BackendAnalyzeResponse & { createdCase?: PldCaseRecord | null }>('/api/v1/pld-ft/ingest-stream', {
    method: 'POST',
    body: JSON.stringify({ sourceType: 'ui-stream', ...input, autoCaseMinScore, openCase: true }),
  });
}

export async function listPldIngestionJobsBackend(): Promise<PldIngestionJob[]> {
  const payload = await requestJson<{ jobs: PldIngestionJob[] }>('/api/v1/pld-ft/ingestion-jobs');
  return payload.jobs;
}

export async function createPldIngestionJobBackend(payload: {
  name: string;
  sourceType?: string;
  intervalSeconds?: number;
  autoCaseMinScore?: number;
  config?: Record<string, unknown>;
}): Promise<PldIngestionJob> {
  return requestJson<PldIngestionJob>('/api/v1/pld-ft/ingestion-jobs', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function runPldIngestionJobBackend(jobId: string): Promise<{ job: PldIngestionJob; result: Record<string, unknown> }> {
  return requestJson<{ job: PldIngestionJob; result: Record<string, unknown> }>(`/api/v1/pld-ft/ingestion-jobs/${jobId}/run`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export async function createPldRegulatoryExportBackend(caseId: string, approvalNote = ''): Promise<PldRegulatoryExport> {
  return requestJson<PldRegulatoryExport>(`/api/v1/pld-ft/cases/${caseId}/regulatory-exports`, {
    method: 'POST',
    body: JSON.stringify({ exportType: 'coaf_internal', approvalNote }),
  });
}

export async function listPldRegulatoryExportsBackend(): Promise<PldRegulatoryExport[]> {
  const payload = await requestJson<{ exports: PldRegulatoryExport[] }>('/api/v1/pld-ft/regulatory-exports');
  return payload.exports;
}

export async function approvePldRegulatoryExportBackend(exportId: string, approvalNote: string): Promise<PldRegulatoryExport> {
  return requestJson<PldRegulatoryExport>(`/api/v1/pld-ft/regulatory-exports/${exportId}/approve`, {
    method: 'PATCH',
    body: JSON.stringify({ exportType: 'coaf_internal', approvalNote }),
  });
}

export async function downloadPldRegulatoryExportBackend(exportId: string): Promise<Blob> {
  const response = await fetch(`/api/v1/pld-ft/regulatory-exports/${exportId}.json`);
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  return response.blob();
}

export async function updatePldCaseWorkflowBackend(
  caseId: string,
  payload: {
    assignee?: string;
    priority?: string;
    slaDueAt?: string;
    status?: PldCaseStatus;
    note?: string;
  },
): Promise<PldCaseRecord> {
  return requestJson<PldCaseRecord>(`/api/v1/pld-ft/cases/${caseId}/workflow`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function listPldCaseCommentsBackend(caseId: string): Promise<Array<{ id: string; body: string; author: string; createdAt?: string }>> {
  const payload = await requestJson<{ comments: Array<{ id: string; body: string; author: string; createdAt?: string }> }>(
    `/api/v1/pld-ft/cases/${caseId}/comments`,
  );
  return payload.comments;
}

export async function createPldCaseCommentBackend(caseId: string, body: string, author?: string): Promise<Array<{ id: string; body: string; author: string; createdAt?: string }>> {
  const payload = await requestJson<{ comments: Array<{ id: string; body: string; author: string; createdAt?: string }> }>(
    `/api/v1/pld-ft/cases/${caseId}/comments`,
    {
      method: 'POST',
      body: JSON.stringify({ body, author }),
    },
  );
  return payload.comments;
}

export async function createPldCaseAttachmentBackend(
  caseId: string,
  attachment: { fileName: string; contentType?: string; fileSize?: number; description?: string; storageUrl?: string },
): Promise<Array<{ id: string; fileName: string; contentType: string; fileSize: number; description: string; storageUrl: string; createdAt?: string }>> {
  const payload = await requestJson<{ attachments: Array<{ id: string; fileName: string; contentType: string; fileSize: number; description: string; storageUrl: string; createdAt?: string }> }>(
    `/api/v1/pld-ft/cases/${caseId}/attachments`,
    {
      method: 'POST',
      body: JSON.stringify(attachment),
    },
  );
  return payload.attachments;
}
