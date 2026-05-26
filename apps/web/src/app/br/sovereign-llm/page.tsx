import type { Metadata } from 'next';
import { Fraunces } from 'next/font/google';
import { NavBR } from '@/components/landing/br/NavBR';
import { FooterBR } from '@/components/landing/br/FooterBR';
import { SovereignLlmBR } from '@/components/landing/br/SovereignLlmBR';

const fraunces = Fraunces({
  subsets: ['latin'],
  variable: '--font-fraunces',
  display: 'swap',
  axes: ['opsz'],
});

export const metadata: Metadata = {
  title: { absolute: 'Sovereign LLM — Quarry para fintech BR Bacen' },
  description:
    'Três modalidades de soberania (Mac Mini físico, VPS dedicada, BYOK cloud). LLM dentro do seu perímetro. Mapeamento direto com Res. BCB 85/2021 e LGPD. CARD-015 da Quarry.',
  alternates: { canonical: '/br/sovereign-llm' },
  openGraph: {
    title: 'Sovereign LLM — três modalidades, um padrão forense',
    description:
      'Modalidade A — Mac Mini na sala-cofre. Modalidade B — VPS Llama dedicada. Modalidade C — BYOK cloud. Você decide onde o motor pensa.',
    locale: 'pt_BR',
    type: 'website',
  },
};

export default function SovereignLlmPage() {
  return (
    <main
      data-theme="light"
      className={
        fraunces.variable +
        ' min-h-screen bg-[#f7f4ef] font-sans text-[#1a1a1a]'
      }
      style={{ fontFeatureSettings: '"ss01", "ss02"' }}
    >
      <NavBR />
      <SovereignLlmBR />
      <FooterBR />
    </main>
  );
}
