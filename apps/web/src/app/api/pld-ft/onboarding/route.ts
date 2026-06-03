import { NextResponse } from 'next/server';
import { saveIntakeUpload, updateChecklist } from '@/lib/pldft/intake';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const contentType = request.headers.get('content-type') || '';

  try {
    if (contentType.includes('multipart/form-data')) {
      const form = await request.formData();
      const id = String(form.get('id') || '');
      const purpose = String(form.get('purpose') || 'documento');
      const file = form.get('file');
      if (!id) return NextResponse.json({ error: 'id obrigatorio.' }, { status: 400 });
      if (!(file instanceof File)) {
        return NextResponse.json({ error: 'Arquivo obrigatorio.' }, { status: 400 });
      }
      const intake = await saveIntakeUpload({ id, purpose, file });
      return NextResponse.json({ ok: true, intake });
    }

    const body = await request.json();
    const id = String(body?.id || '');
    if (!id) return NextResponse.json({ error: 'id obrigatorio.' }, { status: 400 });
    const intake = await updateChecklist(id, body?.checklist || {});
    return NextResponse.json({ ok: true, intake });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Erro no onboarding.' },
      { status: 422 },
    );
  }
}
