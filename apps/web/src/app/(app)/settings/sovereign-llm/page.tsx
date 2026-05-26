import { SovereignLlmView } from '@/components/settings/SovereignLlmView';

export const metadata = {
  title: 'Sovereign LLM',
};

export default function SovereignLlmPage() {
  return (
    <div className="p-6">
      <SovereignLlmView />
    </div>
  );
}
