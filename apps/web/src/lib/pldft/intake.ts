import { promises as fs } from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export type DiagnosticIntakeInput = {
  companyName?: string;
  cnpj?: string;
  website?: string;
  contactName?: string;
  contactRole?: string;
  email?: string;
  phone?: string;
  fintechModel?: string;
  monthlyTransactions?: string;
  monthlyVolume?: string;
  currentControls?: string;
  pain?: string;
};

export type IntakeUpload = {
  id: string;
  purpose: string;
  originalName: string;
  storedName: string;
  size: number;
  contentType: string;
  uploadedAt: string;
};

export type DiagnosticIntake = Required<DiagnosticIntakeInput> & {
  id: string;
  status: 'registered' | 'diagnostic_pending_payment' | 'diagnostic_paid' | 'onboarding' | 'analysis_ready';
  product: 'diagnostico-pld-ft';
  listPriceBrl: number;
  offerPriceBrl: number;
  riskTier: 'baixo' | 'medio' | 'alto' | 'critico';
  riskScore: number;
  triageNotes: string[];
  paymentMode: 'external_checkout' | 'proposal';
  checkoutUrl: string | null;
  onboardingPath: string;
  checklist: Record<string, boolean>;
  uploads: IntakeUpload[];
  createdAt: string;
  updatedAt: string;
};

const DATA_DIR = process.env.QUARRY_INTAKE_DIR || path.join(process.cwd(), 'data', 'pld-ft-intakes');
const LIST_PRICE_BRL = 60000;
const OFFER_PRICE_BRL = 18000;
const PUBLIC_SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || process.env.PUBLIC_SITE_URL || 'https://quarry.12brain.org').replace(/\/$/, '');

const checklistDefaults: Record<string, boolean> = {
  contexto_operacional: false,
  politica_pldft: false,
  matriz_risco: false,
  amostra_transacoes: false,
  base_clientes: false,
  regras_monitoramento: false,
  responsavel_compliance: false,
  agenda_devolutiva: false,
};

function clean(value: unknown, max = 500): string {
  return String(value || '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}

function safeIdPart(value: string): string {
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 42) || 'fintech';
}

function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function scoreInput(input: Required<DiagnosticIntakeInput>): {
  riskScore: number;
  riskTier: DiagnosticIntake['riskTier'];
  notes: string[];
} {
  let score = 35;
  const notes: string[] = [];
  const model = input.fintechModel.toLowerCase();
  const volume = input.monthlyTransactions.toLowerCase();
  const pain = `${input.pain} ${input.currentControls}`.toLowerCase();

  if (/pix|conta|baas|pagamento|crypto|cripto|cambio|câmbio/.test(model)) {
    score += 18;
    notes.push('Modelo com superficie PLD/FT relevante para monitoramento transacional.');
  }
  if (/100\.?000|500\.?000|milh|alto|grande|acima/.test(volume)) {
    score += 16;
    notes.push('Volume declarado sugere necessidade de automacao e trilha de evidencia.');
  }
  if (/pix|laranja|lavagem|fraude|crime|organiz/.test(pain)) {
    score += 20;
    notes.push('Dor declarada envolve sinais fortes de fraude, lavagem ou uso indevido da infraestrutura.');
  }
  if (/nao temos|não temos|manual|planilha|basico|básico/.test(pain)) {
    score += 12;
    notes.push('Controles atuais parecem manuais ou pouco defensaveis para auditoria.');
  }

  const riskScore = Math.min(100, score);
  const riskTier: DiagnosticIntake['riskTier'] =
    riskScore >= 80 ? 'critico' : riskScore >= 65 ? 'alto' : riskScore >= 45 ? 'medio' : 'baixo';
  if (!notes.length) notes.push('Cadastro recebido. A qualificacao sera refinada no checklist de onboarding.');
  return { riskScore, riskTier, notes };
}

async function ensureDir() {
  await fs.mkdir(DATA_DIR, { recursive: true });
}

async function createStripeCheckoutSession({
  intakeId,
  companyName,
  email,
}: {
  intakeId: string;
  companyName: string;
  email: string;
}): Promise<string | null> {
  const secretKey = process.env.STRIPE_SECRET_KEY || '';
  if (!secretKey) return null;

  const successUrl = `${PUBLIC_SITE_URL}/diagnostico-pld-ft/onboarding?id=${encodeURIComponent(intakeId)}&payment=success`;
  const cancelUrl = `${PUBLIC_SITE_URL}/diagnostico-pld-ft?payment=cancelled`;
  const params = new URLSearchParams();
  params.set('mode', 'payment');
  params.set('success_url', successUrl);
  params.set('cancel_url', cancelUrl);
  params.set('customer_email', email);
  params.set('client_reference_id', intakeId);
  params.set('metadata[intake_id]', intakeId);
  params.set('metadata[company_name]', companyName);
  params.set('metadata[product]', 'diagnostico-pld-ft');
  params.set('payment_method_types[0]', 'card');
  params.set('line_items[0][quantity]', '1');

  if (process.env.STRIPE_DIAGNOSTIC_PRICE_ID) {
    params.set('line_items[0][price]', process.env.STRIPE_DIAGNOSTIC_PRICE_ID);
  } else {
    params.set('line_items[0][price_data][currency]', 'brl');
    params.set('line_items[0][price_data][unit_amount]', String(OFFER_PRICE_BRL * 100));
    params.set('line_items[0][price_data][product_data][name]', 'Diagnostico PLD/FT Quarry');
    params.set(
      'line_items[0][price_data][product_data][description]',
      'Avaliacao de exposicao a fraude, lavagem de dinheiro e movimentacoes anormais em fintech.',
    );
  }

  const response = await fetch('https://api.stripe.com/v1/checkout/sessions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${secretKey}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: params,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    console.error('[pld-ft intake] Stripe checkout failed', {
      status: response.status,
      type: payload?.error?.type,
      code: payload?.error?.code,
    });
    return null;
  }
  return typeof payload.url === 'string' ? payload.url : null;
}

function intakePath(id: string) {
  return path.join(DATA_DIR, `${safeIdPart(id)}.json`);
}

export async function createDiagnosticIntake(input: DiagnosticIntakeInput): Promise<DiagnosticIntake> {
  const normalized: Required<DiagnosticIntakeInput> = {
    companyName: clean(input.companyName, 160),
    cnpj: clean(input.cnpj, 40),
    website: clean(input.website, 180),
    contactName: clean(input.contactName, 120),
    contactRole: clean(input.contactRole, 120),
    email: clean(input.email, 160).toLowerCase(),
    phone: clean(input.phone, 60),
    fintechModel: clean(input.fintechModel, 160),
    monthlyTransactions: clean(input.monthlyTransactions, 120),
    monthlyVolume: clean(input.monthlyVolume, 120),
    currentControls: clean(input.currentControls, 1200),
    pain: clean(input.pain, 1200),
  };

  if (!normalized.companyName) throw new Error('Nome da fintech e obrigatorio.');
  if (!validateEmail(normalized.email)) throw new Error('E-mail corporativo invalido.');
  if (!normalized.contactName) throw new Error('Nome do responsavel e obrigatorio.');
  if (!normalized.fintechModel) throw new Error('Modelo da fintech e obrigatorio.');

  await ensureDir();
  const now = new Date().toISOString();
  const slug = safeIdPart(normalized.companyName);
  const id = `diag_${slug}_${crypto.randomBytes(4).toString('hex')}`;
  const checkoutUrl =
    process.env.QUARRY_DIAGNOSTIC_CHECKOUT_URL ||
    (await createStripeCheckoutSession({
      intakeId: id,
      companyName: normalized.companyName,
      email: normalized.email,
    }).catch(() => null));
  const triage = scoreInput(normalized);
  const intake: DiagnosticIntake = {
    ...normalized,
    id,
    status: checkoutUrl ? 'diagnostic_pending_payment' : 'registered',
    product: 'diagnostico-pld-ft',
    listPriceBrl: LIST_PRICE_BRL,
    offerPriceBrl: OFFER_PRICE_BRL,
    riskTier: triage.riskTier,
    riskScore: triage.riskScore,
    triageNotes: triage.notes,
    paymentMode: checkoutUrl ? 'external_checkout' : 'proposal',
    checkoutUrl,
    onboardingPath: `/diagnostico-pld-ft/onboarding?id=${encodeURIComponent(id)}`,
    checklist: { ...checklistDefaults },
    uploads: [],
    createdAt: now,
    updatedAt: now,
  };
  await fs.writeFile(intakePath(id), `${JSON.stringify(intake, null, 2)}\n`, 'utf8');
  return intake;
}

export async function getDiagnosticIntake(id: string): Promise<DiagnosticIntake | null> {
  await ensureDir();
  try {
    const raw = await fs.readFile(intakePath(id), 'utf8');
    return JSON.parse(raw) as DiagnosticIntake;
  } catch {
    return null;
  }
}

export async function saveDiagnosticIntake(intake: DiagnosticIntake): Promise<DiagnosticIntake> {
  const next = { ...intake, updatedAt: new Date().toISOString() };
  await ensureDir();
  await fs.writeFile(intakePath(next.id), `${JSON.stringify(next, null, 2)}\n`, 'utf8');
  return next;
}

export async function updateChecklist(id: string, checklist: Record<string, boolean>) {
  const intake = await getDiagnosticIntake(id);
  if (!intake) throw new Error('Cadastro nao encontrado.');
  intake.checklist = { ...intake.checklist, ...checklist };
  intake.status = 'onboarding';
  return saveDiagnosticIntake(intake);
}

export async function saveIntakeUpload({
  id,
  purpose,
  file,
}: {
  id: string;
  purpose: string;
  file: File;
}) {
  const intake = await getDiagnosticIntake(id);
  if (!intake) throw new Error('Cadastro nao encontrado.');
  const bytes = Buffer.from(await file.arrayBuffer());
  if (bytes.length > 15 * 1024 * 1024) throw new Error('Arquivo acima de 15MB.');
  const uploadId = crypto.randomBytes(6).toString('hex');
  const originalName = clean(file.name || 'upload.bin', 180);
  const ext = path.extname(originalName).toLowerCase().replace(/[^a-z0-9.]/g, '').slice(0, 12);
  const storedName = `${Date.now()}-${uploadId}${ext || '.bin'}`;
  const dir = path.join(DATA_DIR, safeIdPart(id), 'uploads');
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(path.join(dir, storedName), bytes);
  const upload: IntakeUpload = {
    id: uploadId,
    purpose: clean(purpose || 'documento', 80),
    originalName,
    storedName,
    size: bytes.length,
    contentType: clean(file.type || 'application/octet-stream', 80),
    uploadedAt: new Date().toISOString(),
  };
  intake.uploads.unshift(upload);
  intake.status = 'onboarding';
  return saveDiagnosticIntake(intake);
}
