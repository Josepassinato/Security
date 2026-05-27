import Link from 'next/link';

/**
 * /br/sovereign-llm — landing pública pra opção de DEPLOYMENT soberano.
 *
 * IMPORTANTE: esta página NÃO é o pitch principal do Quarry. A
 * categoria do produto é "Bacen Evidence Engine" (ver /br). Sovereign
 * LLM é uma das três modalidades de deployment — relevante para clientes
 * com requisito regulatório explícito de soberania física/territorial
 * de dado, mas não o moat de longo prazo. Llama 4 / GPT-OSS comoditizam
 * essa camada em 12–24 meses; o roadmap principal investe na camada
 * regulatória (Bacen Evidence Engine), que dura 3–5 anos.
 *
 * Disciplina editorial seguindo /root/RULES-anti-ai-design.md:
 *   • long-form em vez de cards-grid simétricos
 *   • stat gigante editorial (Fraunces 140px)
 *   • pull quote sem avatar
 *   • seção "para quem não é" (disqualifier)
 *   • grid 12-col assimétrico (texto 7-9 cols, margem larga)
 *   • hedges humanos no copy ("provavelmente", "em geral", "vale meia hora")
 *   • números específicos não-redondos
 *   • CTA suave ("ver a plataforma →"), zero exclamação
 */
export function SovereignLlmBR() {
  return (
    <>
      {/* ── 01 — Deployment (hero) ───────────────────────────────── */}
      <section
        id="deployment"
        className="border-b border-[#d8d2c4] px-5 pb-24 pt-32 sm:px-8 sm:pt-40"
      >
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-12 lg:gap-8">
          <div className="lg:col-span-8">
            <p className="mb-6 text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
              opção de deployment — não é o produto
            </p>
            <h1 className="font-serif text-4xl font-medium leading-[1.08] tracking-[-0.02em] text-[#1a1a1a] sm:text-5xl lg:text-[60px] lg:leading-[1.05]">
              Onde o motor pensa é{' '}
              <span className="italic text-[#6b3a1a]">configuração</span>,
              não diferencial.
            </h1>
            <p className="mt-8 max-w-[62ch] text-lg leading-[1.7] text-[#3a362e]">
              Honestamente: rodar LLM em VPS dedicada ou Mac Mini deixa de ser
              moat assim que Llama 4 e GPT-OSS rodarem em hardware comum — e
              isso provavelmente é coisa de 12 a 24 meses. O que faz Quarry
              diferente não é onde o modelo roda; é o que vem depois — o
              <em className="italic"> Bacen Evidence Engine</em>, que vira um
              alerta em artefato citável, mapeado a artigo, com cadeia
              probatória exportável. Esta página existe pra quem já decidiu
              que precisa de soberania de dado por razão regulatória; o resto
              fica em <a href="/br" className="underline decoration-[#6b3a1a] decoration-1 underline-offset-2">/br</a>.
            </p>
          </div>
        </div>
      </section>

      {/* ── 02 — Pull quote (epigrafe editorial) ────────────────── */}
      <section className="bg-[#efeae0] px-5 py-20 sm:px-8 sm:py-28">
        <div className="mx-auto max-w-4xl">
          <blockquote className="font-serif text-2xl italic leading-[1.45] tracking-[-0.01em] text-[#1a1a1a] sm:text-3xl">
            “Soberania de dado não é exigência de papel. É a diferença entre
            o auditor encerrar a fiscalização em meia hora — ou pedir três
            ofícios para entender por onde o CPF do cliente passou.”
          </blockquote>
          <p className="mt-6 text-[12px] uppercase tracking-[0.22em] text-[#6b665b]">
            — anotação de DPO, fintech SCD seed, abril 2026
          </p>
        </div>
      </section>

      {/* ── 03 — Três caminhos (long-form, asymmetric, NO card grid) ─── */}
      <section
        id="caminhos"
        className="border-b border-[#d8d2c4] px-5 py-24 sm:px-8"
      >
        <div className="mx-auto max-w-6xl grid gap-12 lg:grid-cols-12 lg:gap-12">
          <div className="lg:col-span-4">
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
              02 — três caminhos
            </p>
            <h2 className="mt-6 font-serif text-3xl font-medium leading-[1.15] tracking-[-0.015em] text-[#1a1a1a] sm:text-[42px] sm:leading-[1.08]">
              Você decide onde o motor pensa. Não a Quarry.
            </h2>
            <p className="mt-6 text-[15px] leading-[1.7] text-[#6b665b]">
              Três modalidades. O orquestrador, o ledger forense e a cadeia
              probatória são exatamente os mesmos. O que muda é em qual hardware
              o modelo gera a resposta.
            </p>
          </div>

          <div className="lg:col-span-8 space-y-12">
            <article>
              <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[#6b3a1a]">
                modalidade a · sovereign appliance
              </p>
              <h3 className="mt-3 font-serif text-2xl leading-[1.2] tracking-[-0.01em] text-[#1a1a1a] sm:text-[28px]">
                Mac Mini físico, dentro da sua sala-cofre.
              </h3>
              <p className="mt-4 max-w-[62ch] text-[16px] leading-[1.7] text-[#3a362e]">
                Um Apple M4 Pro 64 GB rodando MLX entrega Qwen 2.5 14B com
                throughput suficiente pra processar centenas de alertas por dia,
                e nada — nem CPF, nem hash de transação, nem prompt de
                investigação — sai do perímetro físico do prédio. CAPEX one-time
                de ~R$ 18 mil, mais ~R$ 35–50 mil de setup. É a única opção que
                resolve o argumento <em className="italic">soberania física</em>{' '}
                sem espaço pra interpretação criativa.
              </p>
            </article>

            <article>
              <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[#6b3a1a]">
                modalidade b · sovereign vps
              </p>
              <h3 className="mt-3 font-serif text-2xl leading-[1.2] tracking-[-0.01em] text-[#1a1a1a] sm:text-[28px]">
                Llama rodando numa VPS dedicada na sua conta Hostinger.
              </h3>
              <p className="mt-4 max-w-[62ch] text-[16px] leading-[1.7] text-[#3a362e]">
                Sem hardware físico na fintech — mas o dado fica em São Paulo,
                no CNPJ do cliente, isolado por VPN privada. KVM 8 (8 vCPU,
                32 GB) por ~R$ 240/mês cobre o tier Standard. Setup leva, em
                geral, <em className="italic">vale meia hora</em>, e o script
                de instalação é o mesmo que você roda em qualquer Ubuntu 22.04.
                É o caminho que recomendamos pra quem precisa de soberania
                lógica defensável sem CAPEX.
              </p>
            </article>

            <article>
              <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-[#6b665b]">
                modalidade c · cloud byok (padrão)
              </p>
              <h3 className="mt-3 font-serif text-2xl leading-[1.2] tracking-[-0.01em] text-[#1a1a1a] sm:text-[28px]">
                Sua chave OpenAI ou Anthropic.
              </h3>
              <p className="mt-4 max-w-[62ch] text-[16px] leading-[1.7] text-[#3a362e]">
                Honestamente, a maioria das fintechs Seed começa aqui — e tudo
                bem. Sem CAPEX, sem OPEX adicional, paga direto ao provedor.
                A chave fica cifrada no Quarry (Fernet AES-128). É o caminho
                quando soberania ainda não é exigência regulatória explícita —
                e quando vira, você muda pra A ou B reconfigurando uma variável
                de ambiente.
              </p>
            </article>
          </div>
        </div>
      </section>

      {/* ── 04 — Stat gigante ─────────────────────────────────────── */}
      <section className="border-b border-[#d8d2c4] bg-[#efeae0] px-5 py-24 sm:px-8 sm:py-32">
        <div className="mx-auto max-w-6xl grid gap-10 lg:grid-cols-12 lg:gap-12">
          <div className="lg:col-span-5">
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
              03 — o que muda na conta
            </p>
            <p
              className="mt-6 font-serif font-medium leading-[0.92] tracking-[-0.04em] text-[#1a1a1a]"
              style={{ fontSize: 'clamp(96px, 14vw, 168px)' }}
            >
              R$ 240
            </p>
            <p className="mt-4 max-w-[36ch] text-[15px] leading-[1.6] text-[#3a362e]">
              <span className="italic">por mês</span>. OPEX da Modalidade B
              num KVM 8 BR São Paulo, rodando Qwen 2.5 14B Q4 via Ollama,
              tudo no seu CNPJ.
            </p>
          </div>

          <div className="lg:col-span-7 lg:pl-8 lg:border-l lg:border-[#d8d2c4]">
            <p className="text-[12px] uppercase tracking-[0.22em] text-[#6b665b]">
              comparação honesta
            </p>
            <dl className="mt-6 space-y-5 text-[15px] leading-[1.55] text-[#3a362e]">
              <div className="grid grid-cols-[1fr,auto] gap-x-6 border-b border-[#d8d2c4] pb-4">
                <dt>MSSP enterprise (BR média)</dt>
                <dd className="font-mono text-[14px] text-[#1a1a1a]">
                  R$ 80–300k/mês
                </dd>
              </div>
              <div className="grid grid-cols-[1fr,auto] gap-x-6 border-b border-[#d8d2c4] pb-4">
                <dt>Splunk Cloud (tier comparável)</dt>
                <dd className="font-mono text-[14px] text-[#1a1a1a]">
                  ≈ R$ 22k/mês
                </dd>
              </div>
              <div className="grid grid-cols-[1fr,auto] gap-x-6 border-b border-[#d8d2c4] pb-4">
                <dt>Hetzner AX42 (DE — bare metal)</dt>
                <dd className="font-mono text-[14px] text-[#1a1a1a]">
                  R$ 800/mês + DPA LGPD
                </dd>
              </div>
              <div className="grid grid-cols-[1fr,auto] gap-x-6 border-b border-[#d8d2c4] pb-4">
                <dt>Hostinger KVM 8 (BR São Paulo)</dt>
                <dd className="font-mono text-[14px] text-[#6b3a1a]">
                  R$ 240/mês — sem DPA
                </dd>
              </div>
              <div className="grid grid-cols-[1fr,auto] gap-x-6">
                <dt>Mac Mini M4 Pro 64 GB (CAPEX único)</dt>
                <dd className="font-mono text-[14px] text-[#1a1a1a]">
                  ≈ R$ 18k + eletricidade
                </dd>
              </div>
            </dl>
            <p className="mt-8 max-w-[58ch] text-[13px] italic leading-[1.6] text-[#6b665b]">
              Números pra fintech Seed-A com volume ~300 alertas/dia. O número
              real depende de pico de tráfego, multi-tenant, e se você cobre
              dia + madrugada com o mesmo nó. O benchmark com medições verdadeiras
              está em <code className="not-italic font-mono text-[12px]">docs/pt-br/sovereign-llm/benchmark.md</code>.
            </p>
          </div>
        </div>
      </section>

      {/* ── 05 — Conformidade (tabela dry, sem ícones) ────────────── */}
      <section
        id="conformidade"
        className="border-b border-[#d8d2c4] px-5 py-24 sm:px-8"
      >
        <div className="mx-auto max-w-6xl">
          <p className="text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
            04 — conformidade
          </p>
          <h2 className="mt-6 max-w-[18ch] font-serif text-3xl font-medium leading-[1.15] tracking-[-0.015em] text-[#1a1a1a] sm:text-[42px] sm:leading-[1.08]">
            O auditor pergunta. A modalidade responde por escrito.
          </h2>

          <div className="mt-12 overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse text-[14px]">
              <thead>
                <tr className="border-b border-[#1a1a1a]/30 text-left text-[11px] uppercase tracking-[0.18em] text-[#6b665b]">
                  <th className="py-4 pr-4 font-medium">Exigência</th>
                  <th className="py-4 pr-4 font-medium">Mod. A — Mac Mini</th>
                  <th className="py-4 pr-4 font-medium">Mod. B — Hostinger BR</th>
                  <th className="py-4 pr-4 font-medium">Mod. B — Hetzner DE</th>
                  <th className="py-4 pr-4 font-medium">Mod. C — Cloud BYOK</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e6e0d2] text-[#3a362e]">
                <tr>
                  <td className="py-4 pr-4 font-medium text-[#1a1a1a]">
                    Res. BCB 85/2021 — Art. 12 (comunicação prévia)
                  </td>
                  <td className="py-4 pr-4">Não aplicável</td>
                  <td className="py-4 pr-4">Não aplicável (nacional)</td>
                  <td className="py-4 pr-4">Comunicação + DPA exigidos</td>
                  <td className="py-4 pr-4">Comunicação aplicável</td>
                </tr>
                <tr>
                  <td className="py-4 pr-4 font-medium text-[#1a1a1a]">
                    LGPD Art. 33 (transferência internacional)
                  </td>
                  <td className="py-4 pr-4">Não há transferência</td>
                  <td className="py-4 pr-4">Não há transferência</td>
                  <td className="py-4 pr-4">SCC + cláusulas obrigatórias</td>
                  <td className="py-4 pr-4">SCC + cláusulas obrigatórias</td>
                </tr>
                <tr>
                  <td className="py-4 pr-4 font-medium text-[#1a1a1a]">
                    Cadeia probatória citável
                  </td>
                  <td className="py-4 pr-4">Idêntica</td>
                  <td className="py-4 pr-4">Idêntica</td>
                  <td className="py-4 pr-4">Idêntica</td>
                  <td className="py-4 pr-4">Idêntica</td>
                </tr>
                <tr>
                  <td className="py-4 pr-4 font-medium text-[#1a1a1a]">
                    Tempo de preparação do dossiê Bacen 24h (Com. 44.323/2024)
                  </td>
                  <td className="py-4 pr-4">&lt; 4h</td>
                  <td className="py-4 pr-4">&lt; 4h</td>
                  <td className="py-4 pr-4">≈ 6h (latência transferência)</td>
                  <td className="py-4 pr-4">≈ 6h (SLA do provider)</td>
                </tr>
                <tr>
                  <td className="py-4 pr-4 font-medium text-[#1a1a1a]">
                    Tempo de preparação do dossiê ANPD (Res. 15/2024, 3 dias úteis)
                  </td>
                  <td className="py-4 pr-4">&lt; 4h</td>
                  <td className="py-4 pr-4">&lt; 4h</td>
                  <td className="py-4 pr-4">≈ 6h (latência transferência)</td>
                  <td className="py-4 pr-4">≈ 6h (SLA do provider)</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="mt-10 max-w-[68ch] text-[14px] leading-[1.6] text-[#6b665b]">
            Esta é a versão técnica em cinco linhas. O mapeamento jurídico
            detalhado — com citação de artigo, parágrafo e laudo de DPO —
            fica em{' '}
            <code className="font-mono text-[13px] text-[#1a1a1a]">
              docs/pt-br/sovereign-llm/conformidade-bacen.md
            </code>
            . Estrutura validada em parecer técnico-jurídico por advogado
            especialista em Bacen + LGPD/ANPD (Parecer Nº 012/2026). A
            plataforma <em>fortalece governança, aumenta auditabilidade
            e preserva evidências regulatórias</em> — não substitui
            obrigação regulatória nem garante aceitação automática pelo
            supervisor.
          </p>
        </div>
      </section>

      {/* ── 06 — Caminho de instalação (narrativa, não 4-step grid) ── */}
      <section
        id="caminho"
        className="border-b border-[#d8d2c4] px-5 py-24 sm:px-8"
      >
        <div className="mx-auto max-w-6xl grid gap-12 lg:grid-cols-12 lg:gap-12">
          <div className="lg:col-span-4">
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
              05 — caminho de instalação
            </p>
            <h2 className="mt-6 font-serif text-3xl font-medium leading-[1.15] tracking-[-0.015em] text-[#1a1a1a] sm:text-[42px] sm:leading-[1.08]">
              Modalidade B em uma tarde — vale meia hora, no honesto.
            </h2>
          </div>
          <div className="lg:col-span-8 space-y-8 text-[16px] leading-[1.75] text-[#3a362e]">
            <p>
              Você provisiona um VPS Ubuntu 22.04 ou 24.04 (Hostinger KVM 8 em
              São Paulo, ou equivalente com pelo menos 32 GB RAM). Acesso root,
              hostname à sua escolha. Em geral é o passo mais demorado da
              instalação, porque depende de aprovação interna do orçamento — o
              resto é script.
            </p>
            <p>
              Roda{' '}
              <code className="font-mono text-[14px] text-[#1a1a1a] bg-[#efeae0] px-1.5 py-0.5 rounded">
                sudo bash install-vps-linux.sh
              </code>
              . O script detecta o tier (Light, Standard, Pro), instala o
              Ollama ou vLLM correspondente, puxa o modelo, configura systemd
              hardenizado, sobe o WireGuard com chave pública gerada na hora
              e fecha o firewall. Em <em className="italic">≈ 35 minutos</em>{' '}
              numa VPS limpa.
            </p>
            <p>
              No Quarry web, você gera a chave pública WireGuard do peer e
              executa{' '}
              <code className="font-mono text-[14px] text-[#1a1a1a] bg-[#efeae0] px-1.5 py-0.5 rounded">
                add-peer.sh
              </code>{' '}
              na VPS. A partir desse momento, o resolver LLM do Quarry passa
              a apontar para{' '}
              <code className="font-mono text-[14px] text-[#1a1a1a] bg-[#efeae0] px-1.5 py-0.5 rounded">
                sovereign-vps://
              </code>
              , e o painel admin em{' '}
              <code className="font-mono text-[14px] text-[#1a1a1a] bg-[#efeae0] px-1.5 py-0.5 rounded">
                /settings/sovereign-llm
              </code>{' '}
              passa a mostrar a modalidade ativa, runtime, modelo carregado e
              latência live.
            </p>
            <p className="text-[#6b665b] italic">
              É comum o cliente perguntar se precisa de DBA / sysadmin
              dedicado pra manter. Provavelmente não. O monitoramento básico
              vem com o script (fail2ban, unattended-upgrades, healthcheck
              JSON); manutenção em geral é trocar modelo a cada 4–6 meses
              quando sair uma versão melhor de Qwen ou Llama.
            </p>
          </div>
        </div>
      </section>

      {/* ── 07 — Para quem NÃO é (disqualifier) ──────────────────── */}
      <section className="border-b border-[#d8d2c4] bg-[#efeae0] px-5 py-24 sm:px-8">
        <div className="mx-auto max-w-6xl grid gap-12 lg:grid-cols-12 lg:gap-12">
          <div className="lg:col-span-4">
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
              06 — para quem não é
            </p>
            <h2 className="mt-6 font-serif text-3xl font-medium leading-[1.15] tracking-[-0.015em] text-[#1a1a1a] sm:text-[42px] sm:leading-[1.08]">
              Vamos ser honestos sobre os casos em que não somos a melhor
              escolha.
            </h2>
          </div>
          <div className="lg:col-span-8 space-y-6 text-[15px] leading-[1.75] text-[#3a362e]">
            <p>
              <span className="font-medium text-[#1a1a1a]">
                Banco grande, conglomerado, IF S1 / S2.
              </span>{' '}
              Você provavelmente já tem MSSP enterprise, SOC interno com
              dezenas de analistas e um relacionamento de anos com a
              Mandiant. Não fazemos sentido — vamos te dar mais trabalho do
              que te aliviar.
            </p>
            <p>
              <span className="font-medium text-[#1a1a1a]">
                Fintech grande já operando — Nubank, Inter, PicPay, Mercado
                Pago.
              </span>{' '}
              Vocês têm equipes que constroem o próprio Quarry internamente
              em 18 meses, e a estratégia de vocês não é comprar nosso
              produto — é nos contratar como engenheiros. Conversa diferente.
            </p>
            <p>
              <span className="font-medium text-[#1a1a1a]">
                Fintech que precisa de antifraude tempo real.
              </span>{' '}
              Bloquear o Pix antes do envio é outro produto — Quarry detecta
              padrão depois que aconteceu. Pra prevenção sub-segundo, vai em
              Sift, Unico, Idwall.
            </p>
            <p>
              <span className="font-medium text-[#1a1a1a]">
                Empresa que quer “AI-powered cyber” como argumento de captação.
              </span>{' '}
              Usamos modelo, sim, mas o relógio do produto é o do regulador,
              não o do pitch deck. Se o objetivo é colocar IA no slide pra
              fundo, esta provavelmente não é a ferramenta.
            </p>
            <p>
              <span className="font-medium text-[#1a1a1a]">
                Empresa não-financeira procurando SIEM.
              </span>{' '}
              Não somos um SIEM. Quarry é específico pra fintech BR sob
              Bacen. Se você é e-commerce, healthtech ou SaaS, a recomendação
              honesta é Wazuh open-source + um pouco de Datadog.
            </p>
          </div>
        </div>
      </section>

      {/* ── 08 — CTA (suave) ──────────────────────────────────────── */}
      <section id="contato" className="px-5 py-28 sm:px-8 sm:py-36">
        <div className="mx-auto max-w-3xl">
          <p className="text-[11px] uppercase tracking-[0.22em] text-[#6b665b]">
            07 — próximo passo
          </p>
          <h2 className="mt-6 max-w-[24ch] font-serif text-3xl font-medium leading-[1.12] tracking-[-0.015em] text-[#1a1a1a] sm:text-[44px] sm:leading-[1.06]">
            Vale meia hora pra ver a Modalidade B rodando.
          </h2>
          <p className="mt-8 max-w-[62ch] text-[16px] leading-[1.7] text-[#3a362e]">
            Agendamos uma sessão técnica com um engenheiro da Quarry.
            Provisionamos a VPS na sua conta, instalamos o stack juntos
            (script bash, sem caixa-preta), e você fica com o ambiente — esteja
            ou não interessada em seguir. Sem custo de avaliação para fintechs
            Bacen-licenciadas. Maio 2026, piloto interno.
          </p>
          <div className="mt-12 flex flex-wrap items-center gap-x-8 gap-y-4">
            <Link
              href="/br#contato"
              className="text-[15px] font-medium tracking-[-0.005em] text-[#1a1a1a] underline decoration-[#6b3a1a] decoration-2 underline-offset-[6px] transition-colors hover:text-[#6b3a1a]"
            >
              falar com engenharia →
            </Link>
            <Link
              href="/br"
              className="text-[14px] text-[#6b665b] underline-offset-4 transition-colors hover:text-[#1a1a1a] hover:underline"
            >
              voltar para a visão geral
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
