import type { Metadata } from 'next';
import { Suspense } from 'react';
import { OnboardingWorkspace } from '@/components/pldft/OnboardingWorkspace';

export const metadata: Metadata = {
  title: { absolute: 'Onboarding do diagnóstico PLD/FT | Quarry' },
  description:
    'Checklist técnico, documentos e amostras para iniciar o diagnóstico PLD/FT do Quarry sem integração profunda em produção.',
  alternates: { canonical: '/diagnostico-pld-ft/onboarding' },
};

export default function DiagnosticoOnboardingPage() {
  return (
    <main data-theme="light" className="min-h-screen bg-[#f7f4ef] text-[#17140f]">
      <Suspense
        fallback={
          <div className="flex min-h-screen items-center justify-center text-[#514839]">
            Carregando onboarding...
          </div>
        }
      >
        <OnboardingWorkspace />
      </Suspense>
    </main>
  );
}
