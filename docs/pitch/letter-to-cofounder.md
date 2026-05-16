# Quarry - Strategic Note Before Our Conversation

Prepared for a confidential strategic discussion  
Date: May 16, 2026  
Author: Jose / Increase Trainer

## Purpose

I am sharing this before we meet so the conversation can start at the right level. This is not a fundraising memo and it is not an attempt to pressure a decision. It is a concise explanation of why I believe the market has opened, what I have built so far, where I think the opportunity sits, and why your perspective could materially change the quality of the next phase.

I also recognize that you currently have obligations and constraints through your employment at Meta. Any conversation about role, equity, advisory work, introductions, technical feedback, or future operating involvement should be handled carefully, transparently, and only in a way that is compatible with those obligations. The immediate goal is alignment and diligence, not a premature commitment.

---

## 1. Why Now: The Post-Mythos Context

On April 7, 2026, Anthropic published its assessment of Claude Mythos Preview, a frontier model with unusually strong cybersecurity capability. The important point is not the branding of one model. The important point is the market signal: agentic systems are now credible enough to compress vulnerability discovery, exploit development, and defensive analysis into timelines that are meaningfully shorter than traditional human-led security workflows.

Anthropic framed Mythos and Project Glasswing as a defensive security effort and as a watershed moment for the security industry. The Federal Reserve later referenced Mythos in the context of AI, cybersecurity, risk management, and financial stability discussions. Treasury has also been moving in the same direction, releasing public-private AI cybersecurity resources for financial services and earlier guidance on AI-specific cybersecurity risks, operational risk, fraud, explainability, and capability gaps.

My read is simple: the security market is entering a transitional window. Attackers will use autonomy to move faster. Defenders will not be able to respond by only hiring more analysts or buying another alert dashboard. The winning pattern will be governed autonomy: systems that can reason, query, correlate, and draft evidence-backed reports while preserving auditability, provenance, cost control, and policy boundaries.

This is the exact gap Quarry is designed to address.

## 2. The Opportunity: Regulated Financial Hunting, Starting in Brazil

I am not framing Quarry as a generic AI security assistant. The wedge is narrower and more practical: autonomous threat investigation for regulated financial environments, starting with Brazilian fintech and payment operations.

Brazil is an unusually strong first market because Pix created a national-scale, real-time payment rail with massive adoption and a very clear fraud and incident-response surface. Banco Central public Pix statistics report more than 170 million individual Pix users, more than 7 billion Pix transactions in January 2026, and more than R$3 trillion in monthly volume in October 2025. That makes Brazil a serious proving ground for real-time financial investigation, not just an interesting regional market.

The urgency is not only fraud volume. It is operational complexity. A fintech investigation may need to correlate Pix events, mobile banking authentication, device behavior, Open Finance access, boleto creation, account takeover attempts, mule accounts, alerts, analyst notes, and regulatory reporting. Today, that work often depends on senior analysts who know how to turn a vague incident brief into a sequence of queries, hypotheses, and evidence.

That does not scale well.

The opportunity is to make the senior-investigator workflow executable, measurable, and repeatable. The platform should not replace accountability. It should increase the number of investigations a competent team can complete while improving the traceability of how conclusions were reached.

The Brazilian wedge can then extend into U.S. and global regulated markets, but only after the product earns trust through benchmarks, pilots, and operational discipline. The pitch is not "AI will replace the SOC." The pitch is "auditable agents can compress investigation time while keeping security teams in control."

## 3. What I Built: Quarry Overview

Quarry is an autonomous threat-hunting and investigation platform for the post-Mythos era.

The current demo focuses on an organized Pix fraud investigation involving a fictitious Brazilian fintech persona, FinPlay Pagamentos. The synthetic dataset is intentionally fictional and designed for demonstration and development. It includes Pix transactions, fraudulent Pix patterns, mobile banking logins, account takeover attempts, Open Finance activity, boleto creation, and injected attack scenarios such as mule-account rings, SIM swap, anomalous scraping, and boleto fraud.

The product flow is built around a simple operating model:

1. The analyst enters or selects an investigation brief.
2. Quarry decomposes the brief into hypotheses.
3. The system runs controlled queries against available data sources.
4. Findings are written into an Investigation Ledger.
5. Evidence is correlated into a timeline, graph, MITRE context, and report.
6. Cost, tokens, reasoning steps, and outputs are visible instead of hidden.

The important design choice is that Quarry is not just a chat layer. It is a control plane for agentic investigation. The Investigation Ledger is the source of truth for auditability. Policy guardrails and read-only evaluation paths are part of the design. The product is intended for environments where a security leader needs speed, but also needs to defend how the system reached a conclusion.

I also completed a pitch-grade SecRL smoke run against Microsoft's SecRL / ExCyTIn-Bench style cyber threat investigation benchmark. The current result is intentionally stated conservatively: 8 scenarios, one question per incident, 8/8 correct, average 8.54 seconds, 95,460 total tokens, and approximately $0.243 estimated cost. This is not being represented as a full official benchmark certification. It is early evidence that the investigation loop is directionally sound and worth deeper evaluation.

The current public demo is available at:

https://quarry.12brain.org

Demo credentials should be shared separately through a secure channel.

## 4. Why Your Perspective Matters

I am reaching out because I think the next phase benefits from someone who understands scale, trust, enterprise credibility, and the realities of deploying AI in serious environments.

The product needs more than code. It needs strategic judgment around what a regulated buyer will trust, what a security team will reject, what must be measured before a pilot, and what should not be claimed too early. It also needs a partner who can help pressure-test whether this is a product, a services-led wedge, a platform opportunity, or a narrower enterprise workflow that should be sold through existing security channels.

Your value is not only network access. The more important value is judgment:

- How to position an autonomous system without triggering unnecessary buyer skepticism.
- Which governance controls must exist before enterprise conversations.
- Which claims are credible and which should be removed.
- How to think about partnership structure without creating conflicts with current employment obligations.
- How to decide whether Quarry should first sell to fintechs, MSSPs, banks, or security vendors.

I do not want to assume what role, if any, makes sense for you. I would rather use the first conversation to determine whether the opportunity is interesting enough to justify further diligence.

## 5. Proposed Engagement Options

These are possible paths, not demands. The point is to make the range of engagement explicit so the conversation can be clean.

### Option A: Strategic Advisor

You would stay outside operations and help with product positioning, enterprise-readiness review, partner introductions where appropriate, and periodic strategic feedback. This is the lowest-friction path and likely the easiest to evaluate first given current employment constraints.

Potential scope:

- Review the deck, demo, and product thesis.
- Help identify must-have controls for credible enterprise pilots.
- Advise on positioning for regulated financial security teams.
- Make introductions only where appropriate and compliant.

Possible structure:

- Advisor agreement only after conflict review.
- Light equity or success-based arrangement if there is mutual fit.
- No operational commitment.

### Option B: Co-founder / Operating Partner Path

This would only make sense if there is strong mutual conviction and if your current obligations allow a future transition. I am not asking for that now. I am naming it because, if Quarry becomes a serious company, the ideal partner profile is someone who can bring product, enterprise trust, AI judgment, and strategic distribution.

Potential scope:

- Define company strategy and initial market.
- Shape enterprise-grade product requirements.
- Lead or support partner/customer conversations.
- Help recruit the first technical and go-to-market hires.

Possible structure:

- Only after diligence, legal review, and employment-conflict clearance.
- Equity tied to role, contribution, and timing.
- No assumption of immediate availability.

### Option C: Design Partner / Network Sponsor

This is a middle path. You would not formally join, but would help Quarry get sharper through structured feedback and possibly one or two highly selective conversations with trusted operators.

Potential scope:

- Review the product as if you were a skeptical buyer or platform partner.
- Identify which claims are strongest and weakest.
- Help decide the first commercial wedge.
- Suggest the right profile for early pilot customers.

Possible structure:

- No formal title initially.
- No commitment beyond a defined diligence period.
- Later conversion to advisor or partner only if both sides want it.

## 6. Next Steps and Timeline

I suggest a staged process:

### Step 1 - 45-minute strategic conversation

Goal: determine whether the thesis is worth deeper diligence.

Topics:

- Does the post-Mythos framing feel credible?
- Is regulated financial threat hunting the right first wedge?
- Does the current demo show enough to justify a pilot path?
- What claims should be removed before external conversations?

### Step 2 - 30-day diligence window

Goal: turn interest into evidence.

Work items:

- Review the public demo and 5-minute narrated demo.
- Review the SecRL smoke-run report and decide what full benchmark would be needed.
- Review the architecture at a strategic level, not an IP-disclosing deep dive.
- Identify the first two likely buyer profiles.
- Decide which engagement option, if any, is worth discussing.

### Step 3 - 60-day pilot definition

Goal: define a real external test without overbuilding.

Possible deliverables:

- One Brazilian fintech or MSSP pilot target.
- One enterprise-security design partner target.
- Clear success criteria: time-to-investigation, accuracy, auditability, report quality, cost per investigation, and analyst acceptance.
- Clear non-goals: no broad autonomous action in production systems, no unsupervised remediation, no unsupported claims.

### Step 4 - Decision point

At the end of the diligence period, we should decide one of four things:

1. Continue as advisor.
2. Explore a future co-founder or operating-partner path.
3. Keep the relationship informal and product-feedback oriented.
4. Stop cleanly if the fit is not strong enough.

That is the right level of pressure: serious, but not rushed.

## Attachments and Links

Primary materials:

- Pitch deck PDF: `docs/pitch/quarry-v1.pdf`
- Editable deck: `docs/pitch/quarry-v1.pptx`
- Live demo: `https://quarry.12brain.org`
- 5-minute narrated demo: `docs/pitch/videos/quarry-demo-5min.mp4`
- Short executive cut: `artifacts/demo-videos/demo-cinematografica-executive.mp4`

Supporting materials:

- Source notes for deck claims: `docs/pitch/quarry-v1-sources.md`
- SecRL smoke-run report: `docs/benchmarks/microsoft-secrl-results.md`
- Demo screenshot: `artifacts/public-deploy/quarry-public-demo-current.png`

Demo credentials should be sent separately through a secure channel, not embedded in this document.

## Source Notes

- Anthropic Red Team, "Assessing Claude Mythos Preview's cybersecurity capabilities", April 7, 2026: https://red.anthropic.com/2026/mythos-preview/
- Federal Reserve Board, Michelle W. Bowman, "Artificial Intelligence in the Financial System", May 1, 2026: https://www.federalreserve.gov/newsevents/speech/bowman20260501a.htm
- U.S. Treasury, "Treasury Announces Public-Private Initiative to Strengthen Cybersecurity and Risk Management for AI", February 18, 2026: https://home.treasury.gov/news/press-releases/sb0395
- U.S. Treasury, "Managing Artificial Intelligence-Specific Cybersecurity Risks in the Financial Services Sector", March 27, 2024: https://home.treasury.gov/news/press-releases/jy2212
- Microsoft SecRL repository: https://github.com/microsoft/SecRL
- Banco Central do Brasil Pix statistics: https://www.bcb.gov.br/estabilidadefinanceira/pix-em-numeros-estatisticas

---

# Email Template

Subject: Quarry - strategic note before our conversation

Hi [Name],

I am sending a short strategic note before we meet so the conversation can start with context instead of a cold demo.

The note explains why I think the post-Mythos window matters, what I have built with Quarry so far, why regulated financial threat investigation is the first wedge, and a few possible ways you could engage if the thesis is interesting after diligence.

I want to be clear that I am not asking for an immediate decision or assuming any commitment. I also recognize your current obligations at Meta, so any discussion about advisory work, introductions, role, or equity should be handled carefully and only if it is appropriate.

Attached:

- Strategic note: `letter-to-cofounder.md`
- Pitch deck PDF: `quarry-v1.pdf`
- Editable deck: `quarry-v1.pptx`
- 5-minute narrated demo: `quarry-demo-5min.mp4`
- Live demo: https://quarry.12brain.org

I will send demo credentials separately through a secure channel.

For the meeting, I would value your honest read on three questions:

1. Is the post-Mythos framing credible or too early?
2. Is regulated financial threat hunting the right first wedge?
3. What would need to be true for this to be worth deeper diligence?

Best,  
Jose
