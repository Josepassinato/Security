import { ScreeningReviewQueue } from '@/components/screening/ScreeningReviewQueue';

export const metadata = {
  title: 'Screening — Review Queue',
};

export default function ScreeningReviewPage() {
  return (
    <div className="p-6">
      <ScreeningReviewQueue />
    </div>
  );
}
