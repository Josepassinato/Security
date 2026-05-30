import { NextResponse } from 'next/server';
import { getPldIntegrations } from '@/lib/pldft/integrations';

export const dynamic = 'force-dynamic';

export async function GET() {
  const integrations = getPldIntegrations();
  return NextResponse.json({
    configured: integrations.filter((item) => item.status === 'configured').length,
    pending: integrations.filter((item) => item.status === 'pending').length,
    integrations,
  });
}
