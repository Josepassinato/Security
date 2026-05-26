import { FinancialOpsSimulation } from '@/components/demo/FinancialOpsSimulation';

export const metadata = {
  title: 'Demo Financeira | Quarry',
  description:
    'Simulação de uma financeira operando transações enquanto o Quarry fiscaliza riscos, abre caso e emite relatórios.',
};

export default function FinancialDemoPage() {
  return <FinancialOpsSimulation />;
}
