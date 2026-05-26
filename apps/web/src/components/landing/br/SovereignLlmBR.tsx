import Link from 'next/link';

/**
 * /br/sovereign-llm — the public-facing landing for CARD-015.
 *
 * Positions Quarry's sovereign deployment story (Modalidade A — Mac
 * Mini físico na fintech; Modalidade B — VPS dedicada do cliente;
 * Modalidade C — BYOK cloud default). Read-only marketing — every
 * customer-facing claim here is anchored in docs/pt-br/POSITIONING.md.
 *
 * Typographic conventions mirror HeroBR/BacenChecklistBR: Fraunces
 * serif for headings, italic accents in warm brown (#6b3a1a), eyebrow
 * numbering "01 — propósito" with 0.22em tracking.
 */
export function SovereignLlmBR() {
  return (
    <>
      {/* ── 01 — Hero ─────────────────────────────────────────────── */}
      <section
        id="proporcao"
        className="border-b border-[#d8d2c4] px-5 pb-20 pt-32 sm:px-8 sm:pt-40"
      >
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-12 lg:gap-8">
          <div className="lg:col-span-8">
            <p className="mb-6 text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
              01 — soberania
            </p>
            <h1 className="font-serif text-4xl font-medium leading-[1.08] tracking-[-0.02em] text-[#1a1a1a] sm:text-5xl lg:text-[60px] lg:leading-[1.05]">
              O LLM roda{' '}
              <span className="italic text-[#6b3a1a]">dentro do seu perímetro</span>.
              Não pra cima da cloud global.
            </h1>
            <p className="mt-8 max-w-[62ch] text-lg leading-[1.7] text-[#3a362e]">
              A Resolução BCB 85/2021 obriga sua fintech a manter o monitoramento
              contínuo dos seus sistemas, e a LGPD obriga você a tratar dado de
              transação com perímetro técnico bem definido. Quarry é o único SOC
              do mercado brasileiro que entrega isso com o motor de raciocínio
              forense rodando fisicamente dentro da sua infraestrutura — não num
              datacenter da OpenAI em Iowa.
            </p>
          </div>
          <aside className="lg:col-span-4 lg:pl-6 lg:border-l lg:border-[#d8d2c4]">
            <p className="mb-3 text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
              três modalidades
            </p>
            <ul className="space-y-4 text-[15px] leading-[1.55] text-[#3a362e]">
              <li>
                <span className="font-medium text-[#1a1a1a]">A — Mac Mini físico</span>{' '}
                na sua sala-cofre.
              </li>
              <li>
                <span className="font-medium text-[#1a1a1a]">B — VPS dedicada</span>{' '}
                Llama na sua conta cloud.
              </li>
              <li>
                <span className="font-medium text-[#1a1a1a]">C — BYOK cloud</span>{' '}
                (OpenAI/Anthropic/Gemini), padrão.
              </li>
            </ul>
          </aside>
        </div>
      </section>

      {/* ── 02 — Three modality cards ────────────────────────────── */}
      <section
        id="modalidades"
        className="border-b border-[#d8d2c4] px-5 py-20 sm:px-8"
      >
        <div className="mx-auto max-w-6xl">
          <p className="mb-6 text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
            02 — escolha a modalidade
          </p>
          <h2 className="font-serif text-3xl font-medium leading-[1.15] tracking-[-0.015em] text-[#1a1a1a] sm:text-4xl">
            Você decide{' '}
            <span className="italic text-[#6b3a1a]">onde o motor pensa</span>.
            Não a Quarry.
          </h2>

          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {/* Modalidade A */}
            <article className="rounded border border-[#d8d2c4] bg-[#fbf9f3] p-6">
              <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[#6b3a1a]">
                modalidade a
              </p>
              <h3 className="mt-3 font-serif text-2xl leading-[1.1] tracking-[-0.01em] text-[#1a1a1a]">
                Sovereign Appliance
              </h3>
              <p className="mt-1 text-sm text-[#6b665b]">Mac Mini físico na sala-cofre</p>
              <ul className="mt-6 space-y-3 text-[14px] leading-[1.55] text-[#3a362e]">
                <li>Soberania física máxima — nenhum byte sai do prédio.</li>
                <li>Hardware Apple Silicon (M4 Pro, 64GB), MLX nativo.</li>
                <li>Modelo: Qwen 2.5 14B Q4 ou Llama 3.1 8B fallback.</li>
                <li>CAPEX one-time ~R$ 18k + setup R$ 35–50k.</li>
              </ul>
              <p className="mt-6 border-t border-[#d8d2c4] pt-4 text-[12px] uppercase tracking-[0.18em] text-[#6b665b]">
                indicado para fintech com sala-cofre / on-prem
              </p>
            </article>

            {/* Modalidade B */}
            <article className="rounded border border-[#d8d2c4] bg-[#fbf9f3] p-6">
              <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[#6b3a1a]">
                modalidade b
              </p>
              <h3 className="mt-3 font-serif text-2xl leading-[1.1] tracking-[-0.01em] text-[#1a1a1a]">
                Sovereign VPS
              </h3>
              <p className="mt-1 text-sm text-[#6b665b]">Llama em VPS dedicada do cliente</p>
              <ul className="mt-6 space-y-3 text-[14px] leading-[1.55] text-[#3a362e]">
                <li>Soberania lógica — VPS na sua conta, isolada por VPN.</li>
                <li>Canônico: <span className="font-medium">Hostinger São Paulo</span> — dado no Brasil, BRL nativo.</li>
                <li>Três tiers: 8B (R$ 95), 14B (R$ 240), 70B (R$ 2.5–3.5k em GPU).</li>
                <li>Setup R$ 8–15k + OPEX mensal pago pelo cliente.</li>
              </ul>
              <p className="mt-6 border-t border-[#d8d2c4] pt-4 text-[12px] uppercase tracking-[0.18em] text-[#6b665b]">
                indicado para fintech sem espaço físico próprio
              </p>
            </article>

            {/* Modalidade C */}
            <article className="rounded border border-[#d8d2c4] p-6">
              <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[#6b665b]">
                modalidade c · padrão
              </p>
              <h3 className="mt-3 font-serif text-2xl leading-[1.1] tracking-[-0.01em] text-[#1a1a1a]">
                Cloud BYOK
              </h3>
              <p className="mt-1 text-sm text-[#6b665b]">Sua chave OpenAI / Anthropic / Gemini</p>
              <ul className="mt-6 space-y-3 text-[14px] leading-[1.55] text-[#3a362e]">
                <li>Quem não precisa de soberania máxima fica aqui.</li>
                <li>Pague pelo uso direto ao provedor, sem markup.</li>
                <li>Chave armazenada cifrada (Fernet AES-128) no Quarry.</li>
                <li>Sem CAPEX, sem OPEX adicional ao subscription.</li>
              </ul>
              <p className="mt-6 border-t border-[#d8d2c4] pt-4 text-[12px] uppercase tracking-[0.18em] text-[#6b665b]">
                indicado quando soberania não é exigência regulatória
              </p>
            </article>
          </div>

          <p className="mt-10 max-w-[68ch] text-[15px] leading-[1.7] text-[#3a362e]">
            As três modalidades compartilham o mesmo orquestrador, o mesmo
            ledger forense, a mesma cadeia probatória citável. O que muda é{' '}
            <span className="italic">onde</span> o modelo gera a resposta.
            Você troca a modalidade reconfigurando uma variável de ambiente.
          </p>
        </div>
      </section>

      {/* ── 03 — Bacen mapping ─────────────────────────────────────── */}
      <section
        id="bacen"
        className="border-b border-[#d8d2c4] px-5 py-20 sm:px-8"
      >
        <div className="mx-auto max-w-6xl">
          <p className="mb-6 text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
            03 — conformidade
          </p>
          <h2 className="font-serif text-3xl font-medium leading-[1.15] tracking-[-0.015em] text-[#1a1a1a] sm:text-4xl">
            O auditor pergunta, a modalidade{' '}
            <span className="italic text-[#6b3a1a]">responde por escrito</span>.
          </h2>

          <div className="mt-10 overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse text-[14px]">
              <thead>
                <tr className="border-b border-[#d8d2c4] text-left text-[12px] uppercase tracking-[0.18em] text-[#6b665b]">
                  <th className="py-3 pr-4">Exigência</th>
                  <th className="py-3 pr-4">Modalidade A</th>
                  <th className="py-3 pr-4">Modalidade B</th>
                  <th className="py-3 pr-4">Modalidade C</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e6e0d2] text-[#3a362e]">
                <tr>
                  <td className="py-4 pr-4 font-medium text-[#1a1a1a]">
                    Res. BCB 85/2021 — PSC
                  </td>
                  <td className="py-4 pr-4">Dado nunca sai do prédio</td>
                  <td className="py-4 pr-4">Dado na VPS do cliente</td>
                  <td className="py-4 pr-4">DPA + cláusulas com cloud</td>
                </tr>
                <tr>
                  <td className="py-4 pr-4 font-medium text-[#1a1a1a]">
                    LGPD Art. 46 (medidas técnicas)
                  </td>
                  <td className="py-4 pr-4">Air-gap físico verificável</td>
                  <td className="py-4 pr-4">Air-gap lógico via VPN</td>
                  <td className="py-4 pr-4">Trust transfer ao provedor</td>
                </tr>
                <tr>
                  <td className="py-4 pr-4 font-medium text-[#1a1a1a]">
                    Cadeia probatória citável
                  </td>
                  <td className="py-4 pr-4">Idêntica nas três</td>
                  <td className="py-4 pr-4">Idêntica nas três</td>
                  <td className="py-4 pr-4">Idêntica nas três</td>
                </tr>
                <tr>
                  <td className="py-4 pr-4 font-medium text-[#1a1a1a]">
                    Resposta a incidente ANPD 24h
                  </td>
                  <td className="py-4 pr-4">Idêntica</td>
                  <td className="py-4 pr-4">Idêntica</td>
                  <td className="py-4 pr-4">Idêntica</td>
                </tr>
                <tr>
                  <td className="py-4 pr-4 font-medium text-[#1a1a1a]">
                    Custo total (estimado, primeiros 12 meses)
                  </td>
                  <td className="py-4 pr-4">~R$ 50–65k setup + sub.</td>
                  <td className="py-4 pr-4">~R$ 8–15k setup + R$ 320–3.5k/mês + sub.</td>
                  <td className="py-4 pr-4">Subscription + uso direto</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="mt-8 max-w-[62ch] text-[13px] italic leading-[1.6] text-[#6b665b]">
            Esta tabela é referência técnica. O mapeamento jurídico definitivo
            (com citação de artigo, parágrafo, e laudo de DPO) fica em{' '}
            <span className="not-italic">
              <code className="font-mono text-[12px]">docs/pt-br/sovereign-llm/conformidade-bacen.md</code>
            </span>
            , publicado conforme cada modalidade for validada em produção.
          </p>
        </div>
      </section>

      {/* ── 04 — Install path ─────────────────────────────────────── */}
      <section
        id="caminho"
        className="border-b border-[#d8d2c4] px-5 py-20 sm:px-8"
      >
        <div className="mx-auto max-w-6xl">
          <p className="mb-6 text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
            04 — caminho de instalação
          </p>
          <h2 className="font-serif text-3xl font-medium leading-[1.15] tracking-[-0.015em] text-[#1a1a1a] sm:text-4xl">
            Modalidade B em uma{' '}
            <span className="italic text-[#6b3a1a]">tarde de trabalho</span>.
          </h2>
          <ol className="mt-10 max-w-[68ch] space-y-6 text-[15px] leading-[1.7] text-[#3a362e]">
            <li>
              <span className="block text-[12px] uppercase tracking-[0.18em] text-[#6b665b]">
                passo 1 — provisão
              </span>
              VPS Ubuntu 22.04 ou 24.04 (Hostinger KVM 8 São Paulo ou
              equivalente, ≥32 GB RAM para tier Standard). Acesso root.
            </li>
            <li>
              <span className="block text-[12px] uppercase tracking-[0.18em] text-[#6b665b]">
                passo 2 — instalação
              </span>
              <code className="font-mono text-[13px] text-[#1a1a1a]">
                sudo bash install-vps-linux.sh
              </code>
              . O script detecta o tier, instala Ollama (ou vLLM no tier Pro),
              puxa o modelo, configura systemd + WireGuard + UFW. ≤ 1 hora.
            </li>
            <li>
              <span className="block text-[12px] uppercase tracking-[0.18em] text-[#6b665b]">
                passo 3 — pareamento
              </span>
              Registre a chave pública WireGuard do Quarry web rodando o helper{' '}
              <code className="font-mono text-[13px] text-[#1a1a1a]">
                add-peer.sh
              </code>
              . O resolver LLM do Quarry passa a apontar para{' '}
              <code className="font-mono text-[13px] text-[#1a1a1a]">
                sovereign-vps://
              </code>
              .
            </li>
            <li>
              <span className="block text-[12px] uppercase tracking-[0.18em] text-[#6b665b]">
                passo 4 — verificação
              </span>
              Painel admin em{' '}
              <code className="font-mono text-[13px] text-[#1a1a1a]">
                /settings/sovereign-llm
              </code>{' '}
              mostra a modalidade ativa, runtime, modelo carregado e latência
              live. A partir desse momento, nenhum byte de PII sai do seu
              perímetro.
            </li>
          </ol>
        </div>
      </section>

      {/* ── 05 — CTA ──────────────────────────────────────────────── */}
      <section id="cta" className="bg-[#1a1a1a] px-5 py-24 sm:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="mb-6 text-[11px] uppercase tracking-[0.22em] text-[#a8a8a3]">
            05 — próximo passo
          </p>
          <h2 className="font-serif text-3xl font-medium leading-[1.15] tracking-[-0.015em] text-[#f5f0e6] sm:text-4xl">
            Quer ver a Modalidade B rodando antes de comprar?
          </h2>
          <p className="mx-auto mt-6 max-w-[58ch] text-[15px] leading-[1.7] text-[#cfc8b9]">
            Agendamos uma sessão de 45 minutos com um engenheiro da Quarry. A
            gente provisiona a VPS na sua conta, instala o stack juntos, e
            você fica com o ambiente. Sem custo de avaliação para fintechs
            Bacen-licenciadas.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/br#contato"
              className="rounded-full border border-[#f5f0e6] px-6 py-3 text-sm tracking-wide text-[#f5f0e6] transition hover:bg-[#f5f0e6] hover:text-[#1a1a1a]"
            >
              falar com engenharia
            </Link>
            <Link
              href="/br"
              className="text-sm tracking-wide text-[#a8a8a3] underline-offset-4 hover:text-[#f5f0e6] hover:underline"
            >
              voltar para a visão geral
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
