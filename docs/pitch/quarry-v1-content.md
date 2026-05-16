# Quarry Pitch Deck v1 - Slide Content

## Slide 01: Quarry — Autonomous Threat Hunting for the Post-Mythos Era

A governed agentic investigation platform for financial-sector cyber defense.



Source footer: Demo: https://quarry.12brain.org

## Slide 02: April 7, 2026 changed the threat-hunting clock.

Frontier agents are now credible enough to compress vulnerability discovery, exploitation, and defensive response cycles.

- Anthropic disclosed Claude Mythos Preview and Project Glasswing, explicitly framing the launch as a security watershed.
- The Federal Reserve later cited Mythos at an FSOC AI / cybersecurity roundtable as evidence of rapidly evolving capability.
- The implication for financial institutions is operational: investigation workflows must move from analyst-hours to machine-minutes while remaining auditable.

Source footer: Sources: Anthropic Red Team, Apr 7 2026; Federal Reserve Bowman speech, May 1 2026.

## Slide 03: The next 6-12 months are the adoption window.

Regulators are turning AI-cyber guidance into operating expectations while attackers gain agentic leverage first.

- Treasury launched public-private AI cybersecurity resources for financial services in 2026.
- Treasury's earlier AI cybersecurity report identified immediate operational risk, cybersecurity, and fraud challenges.
- The buyer will not want a chatbot. The buyer will want governed autonomy: provenance, cost control, reproducibility, and policy guardrails.

Source footer: Sources: U.S. Treasury AI cybersecurity initiative, Feb 18 2026; Treasury AI cybersecurity report, Mar 27 2024.

## Slide 04: Hunters cannot scale linearly with telemetry.

The industry has more alerts, more tools, more data, and fewer people who can connect it all under time pressure.

- SIEM / EDR / cloud logs are searchable, but the investigation work is still mostly human orchestration.
- Senior hunters are the bottleneck: hypothesis generation, query selection, evidence correlation, and report writing.
- Static detections miss the operating need: turning a vague brief into a defensible investigation trail.

Source footer: Sources: Microsoft SecRL benchmark framing; Quarry architecture docs.

## Slide 05: Quarry turns a brief into governed investigation work.

An agentic hunting platform that decomposes the brief, queries telemetry, correlates evidence, and writes the report with a ledger.



Source footer: Source: Quarry product architecture and demo build.

## Slide 06: The analyst sees a live investigation, not a black box.

Brief, hypotheses, data queries, findings, graph, MITRE coverage, cost, and report generation are visible in one flow.

- Input: natural-language investigation brief.
- Process: hypotheses -> connector queries -> evidence ledger -> report.
- Output: analyst-ready narrative with supporting artifacts.

Source footer: Source: Quarry public demo screenshot captured May 16 2026.

## Slide 07: SecRL smoke run: 8/8 scenarios correct.

A pitch-grade regression run against Microsoft's cyber threat investigation benchmark, using the Quarry SQL investigation adapter.

- Model: gpt-4o; evaluator: gpt-4o; temperature: 0; max steps: 25.
- Scope note: this is an 8-scenario pitch smoke run, not the full official question-set claim.

Metrics:
- 8/8: correct scenarios (one question per incident)
- 8.54s: avg time (brief to answer)
- 95,460: tokens (total run)
- $0.243: cost (estimated total)

Source footer: Sources: docs/benchmarks/microsoft-secrl-results.md; microsoft/SecRL GitHub.

## Slide 08: Brazilian fintechs are the first wedge.

Pix created a national-scale real-time payment environment where fraud, identity, mobile, and infrastructure signals converge.

- Demo persona: FinPlay Pagamentos, a fictitious Sao Paulo fintech with 50,000 active customers.
- Synthetic 30-day dataset covers Pix, mobile banking auth, Open Finance, boleto creation, and injected fraud campaigns.
- Initial use case: Pix fraud and account-takeover investigations that require fast correlation and an auditable report.

Metrics:
- +170M: individual Pix users (BCB public stats)
- +7B: Pix transactions (January 2026)
- +R$3T: monthly volume (October 2025)

Source footer: Sources: Banco Central do Brasil Pix statistics; CARD-009 synthetic dataset.

## Slide 09: Founder-led product, partner-scaled distribution.

The right early team pairs Brazilian market access with global enterprise-security credibility.

- Jose / Increase Trainer: product vision, Brazilian market access, and hands-on operator discovery.
- Meta co-founder partner: enterprise credibility, security-network leverage, and strategic distribution.
- Operating model: narrow wedge, visible demo, measurable benchmark, then regulated pilot.

Source footer: Source: founder / partner operating thesis.

## Slide 10: BR -> US -> Global, with evidence gates at each step.

The roadmap protects credibility by pairing expansion with benchmark, security, and deployment milestones.



Source footer: Source: Quarry product roadmap, May 2026.

## Slide 11: Structure the partnership now.

The near-term ask is not broad fundraising. It is a focused partnership discussion tied to diligence and pilot execution.

- Align on co-founder / advisor / equity structure and operating responsibilities.
- Run 30-day technical diligence: public demo, architecture, SecRL harness, and synthetic fintech dataset.
- Define 60-day pilot path with one Brazilian fintech or MSSP and one enterprise-security design partner.
- Decision point: strategic partnership, seed vehicle, or customer-led buildout.

Source footer: Source: proposed partnership timeline.

## Slide 12: Human-speed teams are entering machine-speed investigations.

Quarry is the control plane that keeps autonomous hunting useful, governed, and defensible.

- Live demo: https://quarry.12brain.org
- Backup artifacts: docs/pitch/quarry-v1.pdf and docs/pitch/quarry-v1.pptx
- Next steps: partner diligence, full SecRL question-set run, first regulated pilot.

Source footer: Sources: Quarry demo and source notes in docs/pitch/quarry-v1-sources.md.