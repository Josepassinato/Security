import { NextResponse } from 'next/server';
import { createDiagnosticIntake } from '@/lib/pldft/intake';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'JSON invalido.' }, { status: 400 });
  }

  try {
    const intake = await createDiagnosticIntake(body && typeof body === 'object' ? body : {});
    const isFreeTriage = intake.commercialPath === 'free_triage';
    return NextResponse.json({
      ok: true,
      intake,
      next: {
        onboardingUrl: intake.onboardingPath,
        checkoutUrl: intake.checkoutUrl,
        paymentMode: intake.paymentMode,
        message:
          isFreeTriage
            ? 'Triagem gratuita criada. Abra o workspace para ver o score preliminar, preencher o checklist e experimentar o fluxo com dados declarados ou simulados.'
            : intake.paymentMode === 'external_checkout'
            ? 'Cadastro criado. Siga para o pagamento e depois complete o onboarding tecnico.'
            : 'Cadastro criado. Como o checkout ainda nao esta configurado, o sistema gerou uma proposta comercial e liberou o onboarding tecnico.',
      },
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Erro ao criar cadastro.' },
      { status: 422 },
    );
  }
}
