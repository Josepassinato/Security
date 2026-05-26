export function CostComparisonBR() {
  return (
    <section
      id="custo"
      className="border-b border-[#d8d2c4] px-5 py-24 sm:px-8 sm:py-32"
    >
      <div className="mx-auto max-w-6xl">
        <div className="grid gap-16 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
              04 — o número que pesa
            </p>
            <p className="mt-8 font-serif text-[120px] font-medium leading-[0.92] tracking-[-0.035em] text-[#1a1a1a] sm:text-[160px]">
              R$&nbsp;27<span className="text-[#6b3a1a]">,40</span>
            </p>
            <p className="mt-4 max-w-[40ch] text-sm leading-[1.7] text-[#3a362e]">
              custo médio de uma investigação cinematográfica de fraude Pix
              organizada conduzida pelos agentes Quarry — incluindo modelo,
              consultas, geração de relatório regulatório e arquivamento de
              evidência. Medido no dataset sintético FinPlay Pagamentos
              (R$&nbsp;1,84&nbsp;mi reconstituídos em ~4&nbsp;min&nbsp;30&nbsp;s).
            </p>
          </div>

          <div className="lg:col-span-7 lg:pl-8">
            <h2 className="font-serif text-3xl font-medium leading-[1.15] tracking-[-0.01em] text-[#1a1a1a] sm:text-4xl">
              Comparação <span className="italic">honesta</span>, com hedges humanos onde precisa.
            </h2>
            <p className="mt-6 max-w-[62ch] text-base leading-[1.7] text-[#3a362e]">
              Os números abaixo vieram de cotações reais de MSSP brasileiros
              (2025-2026) atendendo fintech de porte Seed/Series A. Cada caixa
              é um spread, não um ponto. Quarry não cobre tudo que um SOC
              enterprise cobre — cobre o que o regulador exige de fintech
              começando, com auditoria e evidência arquivada.
            </p>

            <table className="mt-12 w-full text-sm">
              <thead>
                <tr className="border-b border-[#d8d2c4] text-left">
                  <th className="pb-3 pr-4 text-[11px] font-medium uppercase tracking-[0.16em] text-[#6b665b]">
                    opção
                  </th>
                  <th className="pb-3 pr-4 text-[11px] font-medium uppercase tracking-[0.16em] text-[#6b665b]">
                    custo mensal
                  </th>
                  <th className="pb-3 text-[11px] font-medium uppercase tracking-[0.16em] text-[#6b665b]">
                    cobertura regulatória
                  </th>
                </tr>
              </thead>
              <tbody className="font-mono text-[13px] text-[#1a1a1a]">
                <tr className="border-b border-[#e6e0d2]">
                  <td className="py-4 pr-4 align-top">
                    MSSP enterprise (Splunk + 24×7)
                  </td>
                  <td className="py-4 pr-4 align-top">R$&nbsp;80k – 300k</td>
                  <td className="py-4 align-top text-[#3a362e]">
                    sobra capacidade; contrato de 24 meses; oversold pra fintech pequena
                  </td>
                </tr>
                <tr className="border-b border-[#e6e0d2]">
                  <td className="py-4 pr-4 align-top">
                    SOC interno (1 squad + ferramentas)
                  </td>
                  <td className="py-4 pr-4 align-top">R$&nbsp;180k – 420k</td>
                  <td className="py-4 align-top text-[#3a362e]">
                    contratação demora ~6 meses; risco de burnout em time pequeno
                  </td>
                </tr>
                <tr className="border-b border-[#e6e0d2]">
                  <td className="py-4 pr-4 align-top">
                    Sem SOC formal
                  </td>
                  <td className="py-4 pr-4 align-top">R$&nbsp;0</td>
                  <td className="py-4 align-top text-[#6b3a1a]">
                    risco regulatório com Bacen; bloqueio de Pix; recusa de banco custodiante
                  </td>
                </tr>
                <tr>
                  <td className="py-4 pr-4 align-top font-medium">
                    Quarry · plano fintech BR
                  </td>
                  <td className="py-4 pr-4 align-top font-medium">
                    R$&nbsp;2,4k – 9,8k
                    <span className="ml-2 text-[11px] font-normal text-[#6b665b]">
                      (a definir)
                    </span>
                  </td>
                  <td className="py-4 align-top text-[#3a362e]">
                    cobre os cinco artefatos do bloco 02; sem cobertura de fraude transacional
                    em tempo real (esse é outro produto)
                  </td>
                </tr>
              </tbody>
            </table>

            <p className="mt-6 text-xs italic leading-[1.7] text-[#6b665b]">
              Spread Quarry calculado contra perfil de uso típico Seed (3-8
              conectores, 1-3 incidentes relevantes/mês). Preço final ainda
              não publicado.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
