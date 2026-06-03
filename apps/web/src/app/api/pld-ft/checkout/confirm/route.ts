import { NextResponse } from 'next/server';
import { confirmDiagnosticPayment } from '@/lib/pldft/intake';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'JSON invalido.' }, { status: 400 });
  }

  const payload = body && typeof body === 'object' ? body as Record<string, unknown> : {};
  const id = typeof payload.id === 'string' ? payload.id : '';
  const sessionId = typeof payload.sessionId === 'string' ? payload.sessionId : '';

  try {
    const intake = await confirmDiagnosticPayment({ id, sessionId });
    return NextResponse.json({
      ok: true,
      intake,
      payment: {
        status: intake.paymentStatus || 'pending',
        paidAt: intake.paidAt || null,
        amountBrl: intake.paymentAmountBrl || null,
        currency: intake.paymentCurrency || null,
      },
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Erro ao confirmar pagamento.' },
      { status: 422 },
    );
  }
}
