import type { Metadata } from 'next';
import { PldFtGovernance } from '@/components/pldft/PldFtGovernance';

export const metadata: Metadata = {
  title: { absolute: 'Governança PLD/FT — Quarry' },
  description: 'Score contínuo, tuning de regras, versionamento aprovado, workflow de casos e relatório executivo PLD/FT.',
  alternates: { canonical: '/br/pld-ft/governance' },
};

export default function PldFtGovernancePage() {
  return <PldFtGovernance />;
}
