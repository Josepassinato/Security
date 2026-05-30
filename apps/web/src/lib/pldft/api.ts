import type { PldCaseDecision, PldCaseRecord, PldCaseStatus } from './cases';
import type { PldDossier, PldInput, PldThresholds } from './engine';

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

export async function savePldThresholdsBackend(thresholds: Partial<PldThresholds>): Promise<void> {
  await requestJson('/api/v1/pld-ft/thresholds', {
    method: 'PUT',
    body: JSON.stringify({ thresholds }),
  });
}
