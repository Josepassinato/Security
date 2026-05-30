import type { PldDossier } from './engine';

export type PldCaseStatus = 'novo' | 'em_revisao' | 'falso_positivo' | 'escalado' | 'encerrado';

export interface PldCaseDecision {
  status: PldCaseStatus;
  note: string;
  analyst: string;
  decidedAt: string;
}

export interface PldCaseRecord {
  id: string;
  createdAt: string;
  status: PldCaseStatus;
  dossier: PldDossier;
  decisions: PldCaseDecision[];
}

export const PLD_CASES_STORAGE_KEY = 'quarry:pldft:cases:v1';

export const pldCaseStatusLabels: Record<PldCaseStatus, string> = {
  novo: 'Novo',
  em_revisao: 'Em revisão',
  falso_positivo: 'Falso positivo',
  escalado: 'Escalado',
  encerrado: 'Encerrado',
};

function readRaw(): PldCaseRecord[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(PLD_CASES_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as PldCaseRecord[]) : [];
  } catch {
    return [];
  }
}

function writeRaw(records: PldCaseRecord[]): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(PLD_CASES_STORAGE_KEY, JSON.stringify(records));
}

export function listPldCases(): PldCaseRecord[] {
  return readRaw().sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt));
}

export function savePldCase(dossier: PldDossier): PldCaseRecord {
  const records = readRaw();
  const existingIndex = records.findIndex((record) => record.id === dossier.id);
  const next: PldCaseRecord = {
    id: dossier.id,
    createdAt: new Date().toISOString(),
    status: 'novo',
    dossier,
    decisions: [],
  };
  if (existingIndex >= 0) {
    records[existingIndex] = {
      ...records[existingIndex],
      dossier,
    };
  } else {
    records.push(next);
  }
  writeRaw(records);
  return existingIndex >= 0 ? records[existingIndex] : next;
}

export function addPldCaseDecision(
  caseId: string,
  decision: Omit<PldCaseDecision, 'decidedAt'>,
): PldCaseRecord | null {
  const records = readRaw();
  const index = records.findIndex((record) => record.id === caseId);
  if (index < 0) return null;
  const nextDecision: PldCaseDecision = {
    ...decision,
    decidedAt: new Date().toISOString(),
  };
  records[index] = {
    ...records[index],
    status: decision.status,
    decisions: [nextDecision, ...records[index].decisions],
  };
  writeRaw(records);
  return records[index];
}

export function removePldCase(caseId: string): void {
  writeRaw(readRaw().filter((record) => record.id !== caseId));
}
