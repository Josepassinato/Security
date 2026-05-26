/**
 * BenchmarkBR — número honesto de redução de FP medido no harness
 * `customizations/benchmarks/auto_triage_finplay/`.
 *
 * Hardcoded a partir do run `2026-05-26-bb5f7ccc` (100 alertas FinPlay BR).
 * Atualizar quando rodar novo benchmark publicável.
 *
 * Doc canônica: docs/pt-br/benchmark-auto-triage.md
 */

import Link from 'next/link';

const RUN = {
  sha: 'bb5f7ccc',
  date: '2026-05-26',
  dataset: 'FinPlay BR (sintético, 100 alertas)',
  model: 'openai/gpt-4o-mini via OpenRouter',
};

const METRICS = {
  baselineAutoClose: 7,
  llmAutoClose: 36,
  deltaPp: 29,
  multiplier: 5.1,
  falseClose: 0,
  precision: 100,
  latencyP95Ms: 2498,
  costPer1k: 0.094,
  recallTpEsc: 100,
};

export function BenchmarkBR() {
  return (
    <section
      id="benchmark"
      className="border-b border-[#d8d2c4] px-5 py-24 sm:px-8 sm:py-32"
    >
      <div className="mx-auto max-w-6xl">
        <div className="grid gap-16 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
              03 — o que a IA fecha sem humano
            </p>
            <p className="mt-8 font-serif text-[120px] font-medium leading-[0.92] tracking-[-0.035em] text-[#1a1a1a] sm:text-[160px]">
              36<span className="text-[#6b3a1a]">%</span>
            </p>
            <p className="mt-4 max-w-[40ch] text-sm leading-[1.7] text-[#3a362e]">
              dos alertas o auto-triage classifica com confiança suficiente
              para fechar sem chegar ao analista humano. Contra{' '}
              {METRICS.baselineAutoClose}% de uma baseline de regras estáticas
              — {METRICS.multiplier.toFixed(1)}× mais.{' '}
              <span className="italic">Zero falso-fechamento</span> nas duas
              estratégias (nenhum incidente real foi indevidamente arquivado).
            </p>
          </div>

          <div className="lg:col-span-7 lg:pl-8">
            <h2 className="font-serif text-3xl font-medium leading-[1.15] tracking-[-0.01em] text-[#1a1a1a] sm:text-4xl">
              Em vez de prometer{' '}
              <span className="italic">&ldquo;80% de redução&rdquo;</span>,
              publicamos o número.
            </h2>
            <p className="mt-6 max-w-[62ch] text-base leading-[1.7] text-[#3a362e]">
              O auto-triage do Quarry foi medido contra o dataset {RUN.dataset}{' '}
              — distribuição de 60 true-positives, 30 false-positives e 10
              eventos benignos representando fraude Pix, scraping Open Finance,
              SIM swap e outros vetores típicos de fintech regulada BR. Ground
              truth embutido no gerador, métrica reproduzível por commit. Foi a
              primeira rodada publicada; vamos manter cadência a cada release
              do agente.
            </p>

            <table className="mt-12 w-full text-sm">
              <thead>
                <tr className="border-b border-[#d8d2c4] text-left">
                  <th className="pb-3 pr-4 text-[11px] font-medium uppercase tracking-[0.16em] text-[#6b665b]">
                    estratégia
                  </th>
                  <th className="pb-3 pr-4 text-right text-[11px] font-medium uppercase tracking-[0.16em] text-[#6b665b]">
                    auto-close
                  </th>
                  <th className="pb-3 pr-4 text-right text-[11px] font-medium uppercase tracking-[0.16em] text-[#6b665b]">
                    falso-fech.
                  </th>
                  <th className="pb-3 text-right text-[11px] font-medium uppercase tracking-[0.16em] text-[#6b665b]">
                    p95 ms
                  </th>
                </tr>
              </thead>
              <tbody className="font-mono text-[13px] text-[#1a1a1a]">
                <tr className="border-b border-[#e6e0d2]">
                  <td className="py-4 pr-4 align-top">
                    Baseline · regras estáticas
                  </td>
                  <td className="py-4 pr-4 text-right align-top">
                    {METRICS.baselineAutoClose}%
                  </td>
                  <td className="py-4 pr-4 text-right align-top">0%</td>
                  <td className="py-4 text-right align-top text-[#3a362e]">
                    &lt;&nbsp;1
                  </td>
                </tr>
                <tr>
                  <td className="py-4 pr-4 align-top font-medium">
                    Quarry · auto-triage agêntico
                  </td>
                  <td className="py-4 pr-4 text-right align-top font-medium text-[#6b3a1a]">
                    {METRICS.llmAutoClose}%
                  </td>
                  <td className="py-4 pr-4 text-right align-top font-medium">
                    {METRICS.falseClose}%
                  </td>
                  <td className="py-4 text-right align-top text-[#3a362e]">
                    {METRICS.latencyP95Ms.toLocaleString('pt-BR')}
                  </td>
                </tr>
              </tbody>
            </table>

            <dl className="mt-10 grid gap-x-10 gap-y-6 sm:grid-cols-3">
              <div>
                <dt className="text-[11px] uppercase tracking-[0.16em] text-[#6b665b]">
                  Precisão de fechamento
                </dt>
                <dd className="mt-2 font-serif text-2xl text-[#1a1a1a]">
                  {METRICS.precision}%
                </dd>
                <p className="mt-1 text-xs leading-[1.6] text-[#6b665b]">
                  todo alerta fechado era de fato dispensável
                </p>
              </div>
              <div>
                <dt className="text-[11px] uppercase tracking-[0.16em] text-[#6b665b]">
                  Recall de escalação
                </dt>
                <dd className="mt-2 font-serif text-2xl text-[#1a1a1a]">
                  {METRICS.recallTpEsc}%
                </dd>
                <p className="mt-1 text-xs leading-[1.6] text-[#6b665b]">
                  todo true-positive chegou ao humano
                </p>
              </div>
              <div>
                <dt className="text-[11px] uppercase tracking-[0.16em] text-[#6b665b]">
                  Custo do agente
                </dt>
                <dd className="mt-2 font-serif text-2xl text-[#1a1a1a]">
                  US$&nbsp;{METRICS.costPer1k.toFixed(3)}
                </dd>
                <p className="mt-1 text-xs leading-[1.6] text-[#6b665b]">
                  por mil alertas processados (gpt-4o-mini)
                </p>
              </div>
            </dl>

            <p className="mt-10 max-w-[62ch] text-sm italic leading-[1.7] text-[#6b665b]">
              Dataset é sintético. Em piloto com cliente, rodamos contra os
              alertas reais dos últimos 30 dias e republicamos o número
              específico daquele ambiente — nenhuma fintech tem distribuição de
              alerta idêntica à outra.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-[#6b665b]">
              <span>
                run{' '}
                <code className="font-mono">{RUN.sha}</code> · {RUN.date}
              </span>
              <span>modelo: {RUN.model}</span>
              <Link
                href="/docs/pt-br/benchmark-auto-triage"
                className="border-b border-[#6b3a1a] pb-[1px] text-[#6b3a1a] hover:text-[#1a1a1a] hover:border-[#1a1a1a]"
              >
                como reproduzir →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
