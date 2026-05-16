import { Suspense } from 'react';
import { CinematicPixDemo } from '@/components/demo/CinematicPixDemo';

export const metadata = {
  title: 'Demo Cinematografica | Quarry',
};

function DemoFallback() {
  return (
    <main className="min-h-screen bg-slate-950 px-6 py-8 text-slate-100">
      <div className="mx-auto max-w-5xl rounded-md border border-slate-800 bg-slate-900 p-6">
        Preparando demo cinematografica...
      </div>
    </main>
  );
}

export default function CinematicDemoPage() {
  return (
    <Suspense fallback={<DemoFallback />}>
      <CinematicPixDemo />
    </Suspense>
  );
}
