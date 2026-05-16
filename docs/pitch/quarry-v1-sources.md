# Quarry Pitch Deck v1 - Source Notes

Generated: 2026-05-16T04:24:16.157591+00:00

## External sources

1. Anthropic Red Team, "Assessing Claude Mythos Preview's cybersecurity capabilities", April 7, 2026.
   URL: https://red.anthropic.com/2026/mythos-preview/
   Used for: Mythos launch timing, Project Glasswing framing, and why the deck treats Mythos as a cybersecurity market trigger.

2. Federal Reserve Board, Michelle W. Bowman, "Artificial Intelligence in the Financial System", May 1, 2026.
   URL: https://www.federalreserve.gov/newsevents/speech/bowman20260501a.htm
   Used for: Fed framing of Mythos as rapidly evolving AI cybersecurity capability and the Powell/Bessent bank convening reference.

3. U.S. Department of the Treasury, "Treasury Announces Public-Private Initiative to Strengthen Cybersecurity and Risk Management for AI", February 18, 2026.
   URL: https://home.treasury.gov/news/press-releases/sb0395
   Used for: 2026 public-private AI cybersecurity resources and financial-services risk-management framing.

4. U.S. Department of the Treasury, "Managing Artificial Intelligence-Specific Cybersecurity Risks in the Financial Services Sector", press release March 27, 2024.
   URL: https://home.treasury.gov/news/press-releases/jy2212
   Used for: AI-specific operational risk, cybersecurity, fraud, and capability-gap framing.

5. Microsoft SecRL GitHub repository, "Benchmarking LLM agents on Cyber Threat Investigation".
   URL: https://github.com/microsoft/SecRL
   Used for: benchmark identity and threat-investigation benchmark framing.

6. Banco Central do Brasil, Pix statistics pages.
   URLs:
   - https://www.bcb.gov.br/estabilidadefinanceira/pix-em-numeros-estatisticas
   - https://www.bcb.gov.br/estabilidadefinanceira/pix/estatisticas
   Used for: +170M individual Pix users, +7B Pix transactions in January 2026, +R$3T monthly volume in October 2025, and one-day transaction record context.

## Internal Quarry sources

1. docs/benchmarks/microsoft-secrl-results.md
   Used for: CARD-012 SecRL pitch smoke-run metrics. Conservative claim only: 8 scenarios, one question per incident, 8/8 correct, average 8.54s, 95,460 tokens, $0.2430 estimated cost.

2. docs/benchmarks/secrl-results.json
   Used for: machine-readable SecRL run details.

3. artifacts/public-deploy/quarry-public-demo-current.png
   Used for: demo screenshot in slide 6.

## Claim controls

- The deck intentionally says "SecRL smoke run" rather than "full official SecRL benchmark", because the local result file documents one question per incident.
- The 6-12 month adoption window is an internal strategic thesis. Regulatory facts supporting urgency are sourced separately from Treasury and Federal Reserve materials.
- No real fintech customer data is disclosed; FinPlay Pagamentos is the fictitious CARD-009 persona.
