import Link from 'next/link';

export function RegulatoryDeliverablesBR() {
  return (
    <section
      id="entregaveis"
      className="border-b border-[#d8d2c4] bg-[#1a1a1a] px-5 py-24 text-[#f4efe5] sm:px-8 sm:py-32"
    >
      <div className="mx-auto max-w-6xl">
        <p className="text-[11px] uppercase tracking-[0.22em] text-[#a09a8e]">
          04 — o que sai do produto
        </p>
        <h2 className="mt-6 max-w-[20ch] font-serif text-3xl font-medium leading-[1.12] tracking-[-0.01em] text-[#f4efe5] sm:text-4xl lg:text-5xl">
          Cada investigação termina em três artefatos auditáveis.
        </h2>

        <div className="mt-16 grid gap-12 lg:grid-cols-3">
          <article className="border-t border-[#3a362e] pt-8">
            <p className="text-[11px] uppercase tracking-[0.18em] text-[#a09a8e]">
              i — comunicação Bacen
            </p>
            <h3 className="mt-3 font-serif text-2xl font-medium text-[#f4efe5]">
              Relatório de incidente relevante
            </h3>
            <p className="mt-4 text-[15px] leading-[1.7] text-[#c9c2b3]">
              Formato pronto para envio em até 24h. Inclui classificação,
              vetores, medidas tomadas e evidência indexada. Versão imutável
              fica arquivada com hash; supervisor pode comparar com a versão
              recebida pelo regulador.
            </p>
          </article>

          <article className="border-t border-[#3a362e] pt-8">
            <p className="text-[11px] uppercase tracking-[0.18em] text-[#a09a8e]">
              ii — cadeia probatória
            </p>
            <h3 className="mt-3 font-serif text-2xl font-medium text-[#f4efe5]">
              Replayable ledger
            </h3>
            <p className="mt-4 text-[15px] leading-[1.7] text-[#c9c2b3]">
              Cada chamada de modelo, cada query rodada, cada decisão dos
              agentes Detect/Triage/Hunt/Respond fica registrada. Auditor
              externo consegue refazer a investigação do zero, com os mesmos
              dados e os mesmos prompts.
            </p>
          </article>

          <article className="border-t border-[#3a362e] pt-8">
            <p className="text-[11px] uppercase tracking-[0.18em] text-[#a09a8e]">
              iii — controle mapeado
            </p>
            <h3 className="mt-3 font-serif text-2xl font-medium text-[#f4efe5]">
              Crosswalk Res. BCB 85 ↔ detecção
            </h3>
            <p className="mt-4 text-[15px] leading-[1.7] text-[#c9c2b3]">
              Catálogo público liga cada artigo da Res. 85, IN BCB 314 e itens
              da LGPD que tocam segurança cibernética a regras Sigma específicas
              em <span className="font-mono text-[13px] text-[#e6e0d2]">customizations/detections/br-fintech</span>.
              Quando um item perde cobertura, o CI marca antes de chegar em produção.
            </p>
          </article>
        </div>

        <div className="mt-16 border-l border-[#3a362e] pl-6">
          <p className="max-w-[58ch] font-serif text-xl leading-[1.5] italic text-[#f4efe5]">
            “O Bacen não exige que você tenha o SOC mais caro do mercado. Exige
            que você consiga, na hora da inspeção, mostrar o que detectou,
            quando detectou, como classificou e o que fez.”
          </p>
          <p className="mt-4 text-[11px] uppercase tracking-[0.18em] text-[#a09a8e]">
            leitura informal da Res. BCB 85/2021 e IN BCB 314, por quem já passou pela inspeção
          </p>
        </div>

        <div className="mt-16">
          <Link
            href="/demo-cinematografica"
            className="group inline-flex items-baseline gap-2 text-base text-[#f4efe5] no-underline"
          >
            <span className="border-b border-[#f4efe5] pb-0.5 italic group-hover:border-[#d8b58a]">
              ver a investigação acontecendo
            </span>
            <span aria-hidden="true" className="transition-transform group-hover:translate-x-0.5">
              →
            </span>
          </Link>
        </div>
      </div>
    </section>
  );
}
