const CHECKLIST = [
  {
    id: 'psc',
    norma: 'Resolução BCB 85/2021',
    titulo: 'Política de Segurança Cibernética',
    descricao:
      'Documento obrigatório, atualizado, com escopo, governança e plano de resposta. ' +
      'Quarry gera o template inicial a partir do desenho de incidentes reais e mantém ' +
      'a versão vigente vinculada às detecções ativas.',
  },
  {
    id: 'registro',
    norma: 'Res. BCB 85/2021 · Art. 8',
    titulo: 'Registro de incidentes relevantes',
    descricao:
      'Cada incidente classificado como relevante precisa estar registrado, datado e com ' +
      'evidência rastreável. O agente Triage marca classificação e cadeia probatória já no ' +
      'momento do achado — não depende de analista preencher planilha depois.',
  },
  {
    id: 'comunicacao',
    norma: 'Res. BCB 85/2021 · Art. 9',
    titulo: 'Comunicação ao Bacen em até 24 horas',
    descricao:
      'Quando o incidente cruza o limiar de relevância, o relatório regulatório é montado ' +
      'em formato de comunicação imediata ao Bacen, com classificação, vetores e medidas ' +
      'tomadas. O relógio começa no momento da detecção, não no momento em que alguém abriu ' +
      'o ticket.',
  },
  {
    id: 'continuidade',
    norma: 'IN BCB 314',
    titulo: 'Continuidade operacional e teste',
    descricao:
      'Plano de continuidade testado, com responsáveis, RTO e RPO. Quarry executa drills ' +
      'cinematográficos a partir de cenários sintéticos (fraude Pix, SIM swap, scraping Open ' +
      'Finance) e arquiva o resultado como evidência de teste periódico.',
  },
  {
    id: 'lgpd',
    norma: 'LGPD · Art. 48',
    titulo: 'Notificação de incidente com dado pessoal',
    descricao:
      'Quando o incidente toca dado pessoal de cliente, a notificação para ANPD e titular ' +
      'precisa ser específica. O relatório separa o que é vazamento, o que é exposição e o ' +
      'que é uso indevido — três regimes diferentes na ANPD.',
  },
];

export function BacenChecklistBR() {
  return (
    <section
      id="bacen"
      className="border-b border-[#d8d2c4] bg-[#efeae0] px-5 py-20 sm:px-8 sm:py-24"
    >
      <div className="mx-auto max-w-6xl">
        <div className="grid gap-12 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
              02 — o que o regulador pede
            </p>
            <h2 className="mt-6 font-serif text-3xl font-medium leading-[1.15] tracking-[-0.01em] text-[#1a1a1a] sm:text-4xl">
              Os <span className="italic">cinco artefatos</span> que toda fintech brasileira precisa ter prontos.
            </h2>
            <p className="mt-6 max-w-[40ch] text-base leading-[1.7] text-[#3a362e]">
              Não é teoria. É o que aparece em supervisão direta do Bacen e em
              due diligence de banco custodiante quando uma fintech tenta fechar
              contrato de BaaS, Pix indireto ou IP de pagamento.
            </p>
          </div>

          <ol className="space-y-10 lg:col-span-8">
            {CHECKLIST.map((item, idx) => (
              <li key={item.id} className="grid gap-3 sm:grid-cols-[3rem_1fr]">
                <span className="font-serif text-2xl font-medium text-[#6b3a1a]">
                  {String(idx + 1).padStart(2, '0')}
                </span>
                <div>
                  <p className="text-[11px] uppercase tracking-[0.16em] text-[#6b665b]">
                    {item.norma}
                  </p>
                  <h3 className="mt-1 font-serif text-xl font-medium leading-snug text-[#1a1a1a]">
                    {item.titulo}
                  </h3>
                  <p className="mt-3 max-w-[62ch] text-base leading-[1.7] text-[#3a362e]">
                    {item.descricao}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
