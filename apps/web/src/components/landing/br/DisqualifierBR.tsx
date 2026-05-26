export function DisqualifierBR() {
  return (
    <section
      id="para-quem-nao-e"
      className="border-b border-[#d8d2c4] px-5 py-24 sm:px-8 sm:py-32"
    >
      <div className="mx-auto max-w-6xl">
        <div className="grid gap-12 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
              06 — para quem isso não é
            </p>
            <h2 className="mt-6 font-serif text-3xl font-medium leading-[1.15] tracking-[-0.01em] text-[#1a1a1a] sm:text-4xl">
              Vale a meia hora de leitura, mas só se você se reconhece aqui.
            </h2>
          </div>

          <div className="lg:col-span-8 lg:pl-8">
            <ul className="space-y-8 text-base leading-[1.7] text-[#3a362e]">
              <li className="border-b border-[#e6e0d2] pb-8">
                <p className="font-serif text-lg font-medium text-[#1a1a1a]">
                  Banco grande, conglomerado ou IF S1/S2.
                </p>
                <p className="mt-2 max-w-[68ch]">
                  Quarry foi feito propositalmente abaixo do escopo de SOC
                  enterprise. Se a sua área de cibersegurança já tem squad
                  dedicado, MSSP contratado e SIEM próprio, este produto não
                  acrescenta nada — provavelmente substitui mal.
                </p>
              </li>
              <li className="border-b border-[#e6e0d2] pb-8">
                <p className="font-serif text-lg font-medium text-[#1a1a1a]">
                  Fintech que precisa de antifraude transacional em tempo real.
                </p>
                <p className="mt-2 max-w-[68ch]">
                  Antifraude no instante da transação (score, velocity, device
                  fingerprint para bloquear o Pix antes do envio) é outro
                  produto. Quarry investiga depois — encontra o anel, monta
                  a evidência, gera o relatório. Os dois são complementares,
                  não substitutos.
                </p>
              </li>
              <li className="border-b border-[#e6e0d2] pb-8">
                <p className="font-serif text-lg font-medium text-[#1a1a1a]">
                  Empresa que quer “AI-powered cyber” como argumento de captação.
                </p>
                <p className="mt-2 max-w-[68ch]">
                  Quarry usa modelos, sim, mas o relógio do produto é o relógio
                  do regulador, não o do pitch deck. Se a expectativa é vender
                  IA para fundo, esta provavelmente não é a ferramenta certa.
                </p>
              </li>
              <li>
                <p className="font-serif text-lg font-medium text-[#1a1a1a]">
                  Quem ainda não decidiu se vai operar regulado no Brasil.
                </p>
                <p className="mt-2 max-w-[68ch]">
                  Se o roadmap regulatório está aberto (talvez Pix indireto,
                  talvez BaaS, talvez nada disso), vale primeiro fechar o
                  desenho. Quarry depende de saber qual regime se aplica.
                </p>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
