import type { Metadata } from 'next';
import { PldFtLab } from '@/components/pldft/PldFtLab';

export const metadata: Metadata = {
  title: { absolute: 'Laboratório PLD/FT | Quarry' },
  description:
    'Laboratório operacional Quarry para analisar transações, aplicar regras determinísticas PLD/FT e gerar dossiê auditável.',
  alternates: { canonical: '/br/pld-ft/lab' },
};

export default function PldFtLabPage() {
  return <PldFtLab />;
}
