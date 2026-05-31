import type { Metadata } from 'next';
import Link from 'next/link';
import { Fraunces } from 'next/font/google';
import { FooterBR } from '@/components/landing/br/FooterBR';
import { NavBR } from '@/components/landing/br/NavBR';

const fraunces = Fraunces({
  subsets: ['latin'],
  variable: '--font-fraunces',
  display: 'swap',
  axes: ['opsz'],
});

const riskSignals = [
  {
    title: 'Pix em cadeia e contas de passagem',
    body:
      'Detecta sequencias curtas de entrada e saida, fracionamento, rotacao de contas, chaves Pix com comportamento fora do perfil e saltos entre CPFs/CNPJs relacionados.',
  },
  {
    title: 'Incompatibilidade economica',
    body:
      'Compara volume transacional com perfil KYC, CNAE, historico declarado, idade da conta, renda/faturamento esperado e mudancas bruscas de comportamento.',
  },
  {
    title: 'Exposicao a sancoes e listas de risco',
    body:
      'Prepara screening contra listas de sancoes, aliases, entidades relacionadas e sinais externos, sempre com revisao humana antes de qualquer conclusao.',
  },
  {
    title: 'Rede de laranjas, empresas e beneficiarios',
    body:
      'Transforma transacoes, dispositivos, telefones, enderecos, socios, procuradores e chaves Pix em grafo investigativo para revelar clusters e conexoes indiretas.',
  },
];

const workflow = [
  'Ingestao de transacoes, KYC, dispositivos, acessos, Pix, Open Finance e alertas internos.',
  'Normalizacao em eventos auditaveis com timestamp, fonte, hash e trilha de origem.',
  'Execucao de regras deterministicas de tipologia PLD/FT e score por entidade/cluster.',
  'Analise de grafo para identificar contas de passagem, hubs, recorrencia e relacoes ocultas.',
  'Abertura de caso com hipoteses, evidencias, lacunas e recomendacao de proximas acoes.',
  'Dossie exportavel para compliance, juridico, auditoria, Bacen, COAF ou investigacao interna.',
];

const typologies = [
  ['Mule account burst', 'muitas entradas pequenas, saidas rapidas e saldo residual baixo'],
  ['Smurfing Pix', 'fracionamento recorrente para evitar padroes obvios de valor'],
  ['ATO + Pix-out', 'mudanca de dispositivo, reset de senha e transferencia imediata'],
  ['Open Finance abuse', 'consentimento amplo seguido de scraping ou chamada fora do padrao'],
  ['Crypto adjacency', 'saidas para intermediarios de cripto, P2P ou carteiras de alto risco'],
  ['Corporate shell flow', 'CNPJ novo ou de baixa substancia recebendo volume atipico'],
];

const deliverables = [
  'Score de risco por cliente, conta, chave Pix, dispositivo, CNPJ e cluster.',
  'Linha do tempo da movimentacao suspeita, com evidencias citaveis.',
  'Mapa de rede entre pessoas, empresas, telefones, dispositivos e chaves Pix.',
  'Resumo executivo para diretoria e relatorio tecnico para compliance.',
  'Fila de revisao humana com decisao, motivo, aprovador e audit trail.',
  'Pacote de evidencia exportavel para auditoria, juridico e regulador.',
];

const impactRisks = [
  'Sua fintech pode ser usada como conta de passagem.',
  'Seu Pix pode virar trilha de lavagem.',
  'Seu onboarding pode aceitar laranjas e CNPJs de fachada.',
  'Seu compliance pode não conseguir provar que investigou.',
  'Seu board pode descobrir o problema tarde demais.',
];

const diagnosticSteps = [
  {
    title: '1. Reunião remota de contexto',
    body:
      'Em 60 a 90 minutos entendemos produto financeiro, volume, Pix, boleto, cartão, cripto, BaaS, KYC/KYB e controles PLD/FT já existentes.',
  },
  {
    title: '2. Checklist de prontidão',
    body:
      'A fintech responde um formulário sobre política PLD/FT, matriz de risco, sanções, PEP, monitoramento, decisões, COAF e retenção de evidências.',
  },
  {
    title: '3. Amostra anonimizada',
    body:
      'Recebemos 30 a 90 dias de transações com IDs internos, valores, datas, origem/destino, canal, device e perfil econômico mínimo. CPF real não é necessário.',
  },
  {
    title: '4. Análise no Quarry',
    body:
      'Rodamos regras, score de risco, contas de passagem, fracionamento, incompatibilidade econômica, clientes críticos e regras mais acionadas.',
  },
  {
    title: '5. Devolutiva executiva',
    body:
      'Entregamos relatório com vulnerabilidades, dados faltantes, evidências encontradas, riscos prioritários e o que a fintech conseguiria ou não provar hoje.',
  },
  {
    title: '6. Plano de piloto',
    body:
      'Se o diagnóstico mostrar risco real, propomos um piloto controlado para conectar fontes, abrir casos, registrar decisões e criar trilha auditável.',
  },
];

const positioning = [
  {
    title: 'Mais profundo que screening',
    body:
      'Ferramentas de KYC, PEP e sancoes ajudam no cadastro. Quarry entra depois: monitora transacoes, comportamento, rede, recorrencia e evidencia operacional.',
  },
  {
    title: 'Mais leve que suite bancaria legada',
    body:
      'Bancos grandes compram plataformas caras e longas de implantar. Quarry foi desenhado para fintech brasileira que precisa maturidade PLD/FT sem um projeto de 12 meses.',
  },
  {
    title: 'Mais brasileiro que AML generico',
    body:
      'Pix, conta digital, Bacen, COAF, LGPD, Open Finance, decisao humana e trilha auditavel entram como centro do produto, nao como adaptacao de rodape.',
  },
];

export const metadata: Metadata = {
  title: { absolute: 'Quarry PLD/FT — monitoramento AML brasileiro para fintechs' },
  description:
    'Monitoramento transacional PLD/FT para fintechs brasileiras com foco em prevencao a lavagem de dinheiro por organizacoes criminosas: score de risco, casos, trilha auditavel e aprovacao humana.',
  alternates: { canonical: '/br/pld-ft' },
  openGraph: {
    title: 'Quarry PLD/FT — risco transacional e evidência auditável',
    description:
      'Detecção de padrões compatíveis com PLD/FT, triagem de sanções, grafo investigativo e dossiê auditável para fintechs brasileiras.',
    locale: 'pt_BR',
    type: 'website',
  },
};

export default function PldFtPage() {
  return (
    <main
      data-theme="light"
      className={
        fraunces.variable +
        ' min-h-screen bg-[#f7f4ef] font-sans text-[#1a1a1a]'
      }
    >
      <NavBR />

      <section className="border-b border-[#ddd4c6] px-5 pb-16 pt-28 sm:px-8 lg:pb-20">
        <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[1.08fr_0.92fr] lg:items-end">
          <div>
            <p className="mb-4 text-xs font-semibold uppercase tracking-[0.24em] text-[#916f3b]">
              PLD/FT para fintechs brasileiras
            </p>
            <h1 className="max-w-4xl font-serif text-4xl font-semibold leading-[0.98] tracking-tight text-[#17140f] sm:text-6xl">
              Proteja sua fintech antes que ela vire infraestrutura financeira do crime.
            </h1>
            <p className="mt-6 max-w-3xl text-lg leading-8 text-[#4d4639]">
              Organizações criminosas usam contas digitais, Pix, CNPJs de fachada,
              laranjas e redes de repasse para lavar dinheiro. O Quarry monitora
              sinais compatíveis com PLD/FT, abre casos, organiza evidências, registra
              decisões humanas e cria trilha auditável para Bacen, COAF, jurídico e
              auditoria.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/br/pld-ft/governance"
                className="inline-flex items-center justify-center rounded-full bg-[#17140f] px-6 py-3 text-sm font-semibold text-white no-underline transition hover:bg-[#2a241b]"
              >
                Ver risco da minha fintech
              </Link>
              <Link
                href="/br/pld-ft/lab"
                className="inline-flex items-center justify-center rounded-full border border-[#17140f] bg-white px-6 py-3 text-sm font-semibold text-[#17140f] no-underline transition hover:bg-[#f0e8d8]"
              >
                Abrir simulação PLD/FT
              </Link>
              <Link
                href="/demo-financeira"
                className="inline-flex items-center justify-center rounded-full border border-[#b9ad9a] px-6 py-3 text-sm font-semibold text-[#262017] no-underline transition hover:border-[#17140f]"
              >
                Ver simulação financeira
              </Link>
              <Link
                href="/br"
                className="inline-flex items-center justify-center rounded-full border border-[#b9ad9a] px-6 py-3 text-sm font-semibold text-[#262017] no-underline transition hover:border-[#17140f]"
              >
                Voltar para Quarry BR
              </Link>
            </div>
          </div>

          <aside className="rounded-[2rem] border border-[#d8cdb9] bg-[#fffaf1] p-6 shadow-[0_24px_80px_rgba(64,45,20,0.12)]">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#916f3b]">
              Regra de posicionamento
            </p>
            <p className="mt-4 font-serif text-2xl leading-tight text-[#17140f]">
              Quarry não acusa. Quarry detecta padrões compatíveis com risco, organiza
              evidência e entrega para revisão humana.
            </p>
            <div className="mt-6 grid gap-3 text-sm text-[#514839]">
              <div className="rounded-2xl bg-white p-4">
                <strong className="text-[#17140f]">Sem promessa perigosa:</strong> o
                sistema não afirma que alguém pertence a uma organização criminosa.
              </div>
              <div className="rounded-2xl bg-white p-4">
                <strong className="text-[#17140f]">Com prova operacional:</strong> toda
                hipótese precisa de fonte, regra, timestamp e decisão registrada.
              </div>
              <div className="rounded-2xl bg-white p-4">
                <strong className="text-[#17140f]">Com trilha defensável:</strong> o
                dossiê nasce pronto para compliance, jurídico e auditoria.
              </div>
            </div>
          </aside>
        </div>
      </section>

      <section className="border-b border-[#ddd4c6] bg-[#17140f] px-5 py-16 text-[#f7f4ef] sm:px-8 lg:py-20">
        <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#d8b56d]">
              O risco não é só multa
            </p>
            <h2 className="mt-3 font-serif text-3xl font-semibold tracking-tight sm:text-5xl">
              Não espere sua fintech aparecer em uma investigação para descobrir que ela foi usada.
            </h2>
            <p className="mt-5 text-base leading-8 text-[#c8bdad]">
              A ameaça real é operacional, reputacional e regulatória ao mesmo tempo.
              Quando o problema aparece fora da empresa, a pergunta deixa de ser
              “houve fraude?” e vira “por que ninguém detectou antes?”.
            </p>
          </div>
          <div className="grid gap-3">
            {impactRisks.map((item) => (
              <div
                key={item}
                className="rounded-2xl border border-white/10 bg-white/[0.05] p-5 text-base leading-7 text-[#f3eadc]"
              >
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-[#ddd4c6] bg-[#f7f4ef] px-5 py-16 sm:px-8 lg:py-20">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-8 lg:grid-cols-[0.92fr_1.08fr] lg:items-end">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#916f3b]">
                Diagnóstico remoto PLD/FT
              </p>
              <h2 className="mt-3 font-serif text-3xl font-semibold tracking-tight sm:text-5xl">
                Em 7 dias, sua fintech descobre onde está exposta sem instalar nada pesado.
              </h2>
            </div>
            <div className="rounded-3xl border border-[#d8cdb9] bg-white p-6 shadow-[0_16px_50px_rgba(64,45,20,0.08)]">
              <p className="text-base leading-8 text-[#4d4639]">
                O diagnóstico inicial é online, assistido e controlado. Não precisa
                técnico nosso dentro da fintech. Trabalhamos com dados anonimizados,
                termo de confidencialidade e uma amostra segura para gerar relatório
                executivo, mapa de risco e proposta objetiva de piloto.
              </p>
              <div className="mt-5 flex flex-col gap-3 sm:flex-row">
                <Link
                  href="mailto:contato@quarry.dev?subject=Diagnostico%20PLD%2FFT%20Quarry"
                  className="inline-flex items-center justify-center rounded-full bg-[#17140f] px-5 py-3 text-sm font-semibold text-white no-underline transition hover:bg-[#2a241b]"
                >
                  Solicitar diagnóstico
                </Link>
                <Link
                  href="/br/pld-ft/readiness"
                  className="inline-flex items-center justify-center rounded-full border border-[#17140f] px-5 py-3 text-sm font-semibold text-[#17140f] no-underline transition hover:bg-[#efe6d8]"
                >
                  Ver prontidão PLD/FT
                </Link>
              </div>
            </div>
          </div>

          <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {diagnosticSteps.map((step) => (
              <article
                key={step.title}
                className="rounded-3xl border border-[#ddd4c6] bg-white p-6"
              >
                <h3 className="font-serif text-xl font-semibold text-[#17140f]">
                  {step.title}
                </h3>
                <p className="mt-3 text-sm leading-7 text-[#544b3c]">{step.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-[#ddd4c6] bg-[#fffaf1] px-5 py-16 sm:px-8 lg:py-20">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-end">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#916f3b]">
                Categoria de mercado
              </p>
              <h2 className="mt-3 font-serif text-3xl font-semibold tracking-tight sm:text-5xl">
                Uma camada moderna de AML transaction monitoring para o contexto brasileiro.
              </h2>
            </div>
            <p className="text-base leading-8 text-[#4d4639]">
              O posicionamento correto do Quarry PLD/FT não é “curso de compliance”,
              nem “screening de listas”, nem “suite bancaria enterprise”. É uma
              plataforma operacional para fintech: detectar padrões, priorizar risco,
              abrir casos, registrar decisões e entregar evidência defensável ao
              compliance officer.
            </p>
          </div>

          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {positioning.map((item) => (
              <article
                key={item.title}
                className="rounded-3xl border border-[#dccfbd] bg-white p-6 shadow-[0_16px_50px_rgba(64,45,20,0.07)]"
              >
                <h3 className="font-serif text-2xl font-semibold text-[#17140f]">
                  {item.title}
                </h3>
                <p className="mt-3 text-sm leading-7 text-[#544b3c]">{item.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="px-5 py-16 sm:px-8 lg:py-20">
        <div className="mx-auto max-w-6xl">
          <div className="max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#916f3b]">
              Como ajuda a fintech
            </p>
            <h2 className="mt-3 font-serif text-3xl font-semibold tracking-tight sm:text-5xl">
              Quatro camadas para reduzir cegueira operacional.
            </h2>
          </div>
          <div className="mt-10 grid gap-4 md:grid-cols-2">
            {riskSignals.map((signal) => (
              <article
                key={signal.title}
                className="rounded-3xl border border-[#ddd4c6] bg-white p-6"
              >
                <h3 className="font-serif text-2xl font-semibold text-[#17140f]">
                  {signal.title}
                </h3>
                <p className="mt-3 text-sm leading-7 text-[#544b3c]">{signal.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-[#17140f] px-5 py-16 text-[#f7f4ef] sm:px-8 lg:py-20">
        <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#d8b56d]">
              Fluxo determinístico
            </p>
            <h2 className="mt-3 font-serif text-3xl font-semibold tracking-tight sm:text-5xl">
              Do evento bruto ao dossiê auditável.
            </h2>
            <p className="mt-5 text-base leading-8 text-[#c8bdad]">
              A IA interpreta e resume, mas o coração da confiabilidade fica em regras,
              grafo, normalização, hashes, fontes e decisões humanas registradas.
            </p>
            <Link
              href="/br/pld-ft/lab"
              className="mt-7 inline-flex items-center justify-center rounded-full bg-[#d8b56d] px-6 py-3 text-sm font-semibold text-[#17140f] no-underline transition hover:bg-[#f0d28a]"
            >
              Testar engine determinístico
            </Link>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link href="/br/pld-ft/cases" className="text-sm font-semibold text-[#f3eadc] underline-offset-4 hover:underline">
                Fila de casos
              </Link>
              <Link href="/br/pld-ft/rules" className="text-sm font-semibold text-[#f3eadc] underline-offset-4 hover:underline">
                Matriz de regras
              </Link>
              <Link href="/br/pld-ft/benchmark" className="text-sm font-semibold text-[#f3eadc] underline-offset-4 hover:underline">
                Benchmark
              </Link>
              <Link href="/br/pld-ft/readiness" className="text-sm font-semibold text-[#f3eadc] underline-offset-4 hover:underline">
                Prontidão
              </Link>
            </div>
          </div>
          <ol className="grid gap-3">
            {workflow.map((step, index) => (
              <li
                key={step}
                className="grid grid-cols-[3rem_1fr] gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#d8b56d] text-sm font-bold text-[#17140f]">
                  {index + 1}
                </span>
                <span className="self-center text-sm leading-6 text-[#f3eadc]">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="px-5 py-16 sm:px-8 lg:py-20">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-8 lg:grid-cols-[0.92fr_1.08fr] lg:items-start">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#916f3b]">
                Tipologias que o produto deve observar
              </p>
              <h2 className="mt-3 font-serif text-3xl font-semibold tracking-tight sm:text-5xl">
                Sinais práticos, não slogans de compliance.
              </h2>
              <p className="mt-5 text-base leading-8 text-[#4d4639]">
                O módulo PLD/FT trabalha com cenários que uma fintech realmente vê
                em operação: Pix, conta digital, mobile banking, Open Finance,
                onboarding e movimentação entre CPFs/CNPJs.
              </p>
            </div>
            <div className="overflow-hidden rounded-3xl border border-[#d8cdb9] bg-white">
              <table className="w-full border-collapse text-left text-sm">
                <thead className="bg-[#efe6d8] text-xs uppercase tracking-[0.16em] text-[#5b4a2d]">
                  <tr>
                    <th className="px-5 py-4">Tipologia</th>
                    <th className="px-5 py-4">Sinal operacional</th>
                  </tr>
                </thead>
                <tbody>
                  {typologies.map(([name, description]) => (
                    <tr key={name} className="border-t border-[#eadfce]">
                      <td className="px-5 py-4 font-semibold text-[#17140f]">{name}</td>
                      <td className="px-5 py-4 leading-6 text-[#554b3e]">{description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-[#ddd4c6] bg-[#fffaf1] px-5 py-16 sm:px-8 lg:py-20">
        <div className="mx-auto max-w-6xl">
          <div className="max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#916f3b]">
              Entregáveis
            </p>
            <h2 className="mt-3 font-serif text-3xl font-semibold tracking-tight sm:text-5xl">
              O resultado precisa servir para operar, decidir e prestar contas.
            </h2>
          </div>
          <div className="mt-10 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {deliverables.map((item) => (
              <div
                key={item}
                className="rounded-2xl border border-[#dccfbd] bg-white p-5 text-sm leading-7 text-[#4d4639]"
              >
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-5 py-16 sm:px-8 lg:py-20">
        <div className="mx-auto max-w-6xl rounded-[2rem] bg-[#17140f] p-8 text-[#f7f4ef] sm:p-10 lg:p-12">
          <div className="grid gap-8 lg:grid-cols-[1fr_0.8fr] lg:items-center">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#d8b56d]">
                Proxima evolucao do Quarry
              </p>
              <h2 className="mt-3 font-serif text-3xl font-semibold tracking-tight sm:text-5xl">
                PLD/FT Threat Desk para fintechs brasileiras.
              </h2>
              <p className="mt-5 text-base leading-8 text-[#d9cfbf]">
                O módulo deve nascer com regras versionadas, grafo, screening,
                fila de revisão humana e pacote de evidência. A promessa comercial
                correta é aumentar auditabilidade e velocidade de investigação,
                não substituir o compliance officer.
              </p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/[0.05] p-6">
              <p className="font-serif text-2xl leading-tight">
                “Detectar padrões compatíveis com risco PLD/FT e produzir evidência
                auditável para decisão humana.”
              </p>
              <p className="mt-4 text-sm leading-6 text-[#c8bdad]">
                Esta é a frase segura: tecnicamente defensável, comercialmente forte
                e juridicamente mais prudente.
              </p>
            </div>
          </div>
        </div>
      </section>

      <FooterBR />
    </main>
  );
}
