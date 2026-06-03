import { NextResponse } from 'next/server';
import { getDiagnosticIntake } from '@/lib/pldft/intake';

export const dynamic = 'force-dynamic';

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> | { id: string } },
) {
  const params = await context.params;
  const intake = await getDiagnosticIntake(params.id);
  if (!intake) {
    return NextResponse.json({ error: 'Cadastro nao encontrado.' }, { status: 404 });
  }
  return NextResponse.json({ ok: true, intake });
}
