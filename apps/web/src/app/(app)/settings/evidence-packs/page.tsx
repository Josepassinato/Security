import { EvidencePacksView } from '@/components/settings/EvidencePacksView';

export const metadata = {
  title: 'Evidence Packs',
};

export default function EvidencePacksPage() {
  return (
    <div className="p-6">
      <EvidencePacksView />
    </div>
  );
}
