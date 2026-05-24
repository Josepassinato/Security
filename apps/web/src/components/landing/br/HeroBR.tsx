import Link from 'next/link';

export function HeroBR() {
  return (
    <section
      id="proporcao"
      className="border-b border-[#d8d2c4] px-5 pb-20 pt-32 sm:px-8 sm:pt-40"
    >
      <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-12 lg:gap-8">
        <div className="lg:col-span-8">
          <p className="mb-6 text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
            01 — proporção
          </p>
          <h1 className="font-serif text-4xl font-medium leading-[1.08] tracking-[-0.02em] text-[#1a1a1a] sm:text-5xl lg:text-[64px] lg:leading-[1.05]">
            Um SOC econômico para fintechs brasileiras que precisam{' '}
            <span className="italic text-[#6b3a1a]">passar pela inspeção do Bacen</span>
            {' '}sem queimar o caixa de Series Seed.
          </h1>
          <p className="mt-8 max-w-[62ch] text-lg leading-[1.7] text-[#3a362e]">
            A regulação está clara. A Resolução BCB 85/2021 e a Política de
            Segurança Cibernética obrigatória pegam fintechs de qualquer porte —
            BaaS, gateway Pix, conta digital, exchange cripto. O problema é que
            a maioria das opções no mercado foi desenhada para banco grande:
            MSSP enterprise cobra de R$ 80 mil a R$ 300 mil por mês, contratos
            longos, oversold. Quem está começando precisa de outra coisa: o
            mínimo defensável, registrado, auditável, e que cabe no budget
            de um Series Seed.
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-x-8 gap-y-3">
            <Link
              href="/demo-cinematografica"
              className="group inline-flex items-baseline gap-2 text-base text-[#1a1a1a] no-underline"
            >
              <span className="border-b border-[#1a1a1a] pb-0.5 italic group-hover:border-[#6b3a1a]">
                ver a plataforma
              </span>
              <span aria-hidden="true" className="transition-transform group-hover:translate-x-0.5">
                →
              </span>
            </Link>
            <a
              href="mailto:contato@quarry.dev?subject=Conversa%20Quarry%20fintech%20BR"
              className="inline-flex items-baseline gap-2 text-base text-[#3a362e] no-underline hover:text-[#1a1a1a]"
            >
              <span className="border-b border-dotted border-[#6b665b] pb-0.5">
                conversar com o time
              </span>
              <span aria-hidden="true">→</span>
            </a>
          </div>
        </div>

        <aside className="lg:col-span-4 lg:pl-8">
          <div className="border-l border-[#d8d2c4] pl-6">
            <p className="text-[11px] uppercase tracking-[0.18em] text-[#6b665b]">
              maio 2026 · em valida&ccedil;&atilde;o t&eacute;cnica
            </p>
            <p className="mt-6 text-sm leading-[1.7] text-[#3a362e]">
              Quarry está em validação com fintechs em estágio Seed e Series A
              no Brasil. Acesso por convite, demo cinematográfica de aproximadamente
              4&nbsp;min&nbsp;30&nbsp;s. Não é ferramenta para SOC enterprise;
              é o oposto disso de propósito.
            </p>
          </div>
        </aside>
      </div>
    </section>
  );
}
