const FAQ = [
  {
    q: 'Por que partir de um fork e não construir do zero?',
    a:
      'O motor agentic (Detect, Triage, Hunt, Respond) é a parte mais cara de construir e a menos diferenciada para o usuário fintech BR. Em vez de queimar 6-12 meses de equipe refazendo orquestrador, partimos de uma base AGPLcompatível e investimos a engenharia no que importa para o regulador brasileiro: detecções fintech BR, conectores Pix/Open Finance, geração de comunicação Bacen.',
  },
  {
    q: 'Os dados saem do Brasil?',
    a:
      'Depende do plano. Self-host: você decide onde Postgres, ClickHouse e Redis rodam — pode ser tudo em VPC brasileira. Managed: regiões disponíveis incluem EU, US e Índia; ainda não há região São Paulo dedicada (próximo passo no roadmap se houver demanda confirmada). Air-gap: nenhuma chamada externa, com modelo local via Ollama.',
  },
  {
    q: 'Quem é o owner legal?',
    a:
      'Increase Trainer Inc., empresa americana (FL), responsável pelo produto. Para contrato com fintech brasileira, ainda estamos avaliando se vale entidade brasileira espelho ou contrato cross-border. Conversável caso a caso.',
  },
  {
    q: 'O relatório regulatório pode ser usado direto na comunicação ao Bacen?',
    a:
      'O formato e os campos seguem o que a Res. BCB 85/2021 pede. O texto final passa por revisão da pessoa responsável pela comunicação — o relatório é insumo, não substitui o compliance officer. O que ele evita é a pessoa ter que reconstituir o incidente do zero três dias depois.',
  },
  {
    q: 'Tem demo?',
    a:
      'A demo cinematográfica de fraude Pix organizada (FinPlay Pagamentos, ~4min30s) está disponível por convite. Use o link “ver a plataforma” no topo. Dados 100% sintéticos.',
  },
];

export function FaqBR() {
  return (
    <section
      id="faq"
      className="border-b border-[#d8d2c4] bg-[#efeae0] px-5 py-24 sm:px-8 sm:py-32"
    >
      <div className="mx-auto max-w-6xl">
        <div className="grid gap-12 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
              07 — o que perguntam
            </p>
            <h2 className="mt-6 font-serif text-3xl font-medium leading-[1.15] tracking-[-0.01em] text-[#1a1a1a] sm:text-4xl">
              Perguntas que apareceram nas primeiras conversas com fintechs.
            </h2>
            <p className="mt-6 max-w-[40ch] text-sm leading-[1.7] text-[#3a362e]">
              Atualizado conforme a conversa evolui. Se sua dúvida não está
              aqui, escreva — provavelmente ela vira item desta lista.
            </p>
          </div>

          <dl className="space-y-10 lg:col-span-8 lg:pl-8">
            {FAQ.map((item, idx) => (
              <div key={item.q} className="border-b border-[#d8d2c4] pb-8 last:border-b-0">
                <dt className="flex items-baseline gap-4">
                  <span className="font-serif text-xs text-[#6b3a1a]">
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                  <span className="font-serif text-xl font-medium leading-snug text-[#1a1a1a]">
                    {item.q}
                  </span>
                </dt>
                <dd className="mt-3 max-w-[66ch] pl-8 text-base leading-[1.7] text-[#3a362e]">
                  {item.a}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  );
}
