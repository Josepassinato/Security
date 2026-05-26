import type { Metadata } from 'next';
import { Fraunces } from 'next/font/google';
import { NavBR } from '@/components/landing/br/NavBR';
import { HeroBR } from '@/components/landing/br/HeroBR';
import { BacenChecklistBR } from '@/components/landing/br/BacenChecklistBR';
import { BenchmarkBR } from '@/components/landing/br/BenchmarkBR';
import { CostComparisonBR } from '@/components/landing/br/CostComparisonBR';
import { RegulatoryDeliverablesBR } from '@/components/landing/br/RegulatoryDeliverablesBR';
import { DisqualifierBR } from '@/components/landing/br/DisqualifierBR';
import { FaqBR } from '@/components/landing/br/FaqBR';
import { FooterBR } from '@/components/landing/br/FooterBR';

const fraunces = Fraunces({
  subsets: ['latin'],
  variable: '--font-fraunces',
  display: 'swap',
  axes: ['opsz'],
});

export const metadata: Metadata = {
  title: { absolute: 'Quarry — SOC econômico para fintechs brasileiras' },
  description:
    'Quarry é um sistema de segurança financeira para fintechs brasileiras que precisam atender a Resolução BCB 85/2021, IN BCB 314 e LGPD sem sustentar custo de MSSP enterprise. Comunicação Bacen em 24h, cadeia probatória auditável, controles mapeados.',
  alternates: { canonical: '/br' },
  openGraph: {
    title: 'Quarry — SOC econômico para fintechs brasileiras',
    description:
      'O mínimo defensável que o Bacen exige, com cadeia probatória auditável e custo compatível com Series Seed.',
    locale: 'pt_BR',
    type: 'website',
  },
};

export default function BrLandingPage() {
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
      <HeroBR />
      <BacenChecklistBR />
      <BenchmarkBR />
      <CostComparisonBR />
      <RegulatoryDeliverablesBR />
      <DisqualifierBR />
      <FaqBR />
      <FooterBR />
    </main>
  );
}
