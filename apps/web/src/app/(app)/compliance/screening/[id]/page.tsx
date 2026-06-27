import { ScreeningDecisionDetail } from '@/components/screening/ScreeningDecisionDetail';

export const metadata = {
  title: 'Screening — Decision',
};

export default async function ScreeningDecisionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div className="p-6">
      <ScreeningDecisionDetail id={id} />
    </div>
  );
}
