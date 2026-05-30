import { NextResponse } from 'next/server';
import { analyzePldFt, type PldInput } from '@/lib/pldft/engine';
import { samplePldInput } from '@/lib/pldft/sample';

export const dynamic = 'force-dynamic';

function isPldInput(value: unknown): value is PldInput {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<PldInput>;
  return Array.isArray(candidate.transactions);
}

export async function GET() {
  const dossier = analyzePldFt(samplePldInput);
  return NextResponse.json({
    mode: 'sample',
    dossier,
  });
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: 'JSON inválido. Envie { institution, customers, transactions }.' },
      { status: 400 },
    );
  }

  if (!isPldInput(body)) {
    return NextResponse.json(
      { error: 'Payload inválido. O campo transactions deve ser uma lista.' },
      { status: 422 },
    );
  }

  if (!body.transactions.length) {
    return NextResponse.json(
      { error: 'Nenhuma transação enviada para análise.' },
      { status: 422 },
    );
  }

  if (body.transactions.length > 5000) {
    return NextResponse.json(
      { error: 'Limite desta rota demonstrativa: 5.000 transações por análise.' },
      { status: 413 },
    );
  }

  const dossier = analyzePldFt({
    ...body,
    generatedAt: body.generatedAt || new Date().toISOString(),
  });

  return NextResponse.json({
    mode: 'custom',
    dossier,
  });
}
