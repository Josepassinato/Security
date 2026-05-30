import type { Metadata } from 'next';
import { PldFtCases } from '@/components/pldft/PldFtCases';

export const metadata: Metadata = {
  title: { absolute: 'Fila de Casos PLD/FT | Quarry' },
  description: 'Fila local de casos PLD/FT com decisão humana, status, exportação e trilha operacional.',
  alternates: { canonical: '/br/pld-ft/cases' },
};

export default function PldFtCasesPage() {
  return <PldFtCases />;
}
