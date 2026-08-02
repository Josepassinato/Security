# Quarry — Competitive Landscape (EN)

**Where Quarry stands against the global compliance & SOC stack — and why
no foreign player solves the Brazilian regulated-fintech problem natively.**

---

## 01 · The Market

Brazilian fintechs under BACEN oversight live with three pressing
regulatory obligations:

- **24-hour cyber-incident notification** — Comunicado BACEN 44.323/2024
- **3-business-day ANPD breach notification** — LGPD Art. 48 + Res. CD/ANPD 15/2024
- **90-day evidence of a working incident-response plan** — Res. BCB 85/2021 Art. 6º

Today these are produced by hand: consultants, Word documents, screenshots.
The cost of a single Big4 engagement runs **R$ 50k–500k per regulatory
cycle**, with multi-week turnaround.

---

## 02 · Four Tiers of Competition

Quarry competes against four different categories of vendor:

1. **Global GRC SaaS** — Vanta, Drata, Secureframe, OneTrust
2. **SIEM / SOC platforms** — Splunk, Microsoft Sentinel, CrowdStrike
3. **Brazilian security houses** — Tempest, Cipher, Apura
4. **Big4 and consulting** — Deloitte, PwC, KPMG, EY

Each tier has a real customer base. **None ship a native Bacen Evidence
Pack with TSA ICP-Brasil and e-CNPJ A3.**

---

## 03 · Tier 1 — Global GRC SaaS

**Players:** Vanta, Drata, Secureframe, OneTrust, AuditBoard, Hyperproof, LogicGate

**Strengths:**
- Continuous control monitoring
- 100+ pre-built control catalogs
- Massive customer bases (Vanta ~8,000 / Drata ~3,000)
- Funding north of $200M each

**Gaps vs Quarry:**
- Zero native BACEN packs (BCB 85, Comunicado 24h)
- No TSA ICP-Brasil integration
- No e-CNPJ A3 digital signature
- English-first interface
- Data residency outside Brazil

**Threat level:** **HIGH** — if they decide to ship a BR module, ~6-month build to catch up.

---

## 04 · Tier 2 — SIEM / SOC Platforms

**Players:** Splunk (Cisco), Microsoft Sentinel, CrowdStrike Falcon,
Palo Alto Cortex XSIAM, Elastic Security, Datadog Cloud SIEM, IBM QRadar

**Strengths:**
- Strong real-time threat detection
- Mature SOAR + automation
- Gartner leadership position
- Enterprise pricing power

**Gaps vs Quarry:**
- Detection tools, not evidence engines
- No regulatory artifacts at the edge
- Bacen compliance requires a separate integrator on top
- Months of professional services to reach a usable Bacen output

**Threat level:** **MEDIUM** — same buyer at the security layer, not the regulatory layer.

---

## 05 · Tier 3 — Brazilian Security Houses

**Players:** Tempest (Embraer), Cipher (Prosegur Cyber), Apura Cyber
Intelligence, NCT, Convexa

**Strengths:**
- Local presence and Portuguese-language support
- Existing relationships with Brazilian banks
- MSSP service muscle

**Gaps vs Quarry:**
- Service-based, not product-based
- No automation of the evidence pack itself
- Pricing is per-hour or per-engagement (R$ 30k–80k/month typical)
- No open auditable cryptographic chain

**Threat level:** **MEDIUM-LOW** — partners as much as competitors.

---

## 06 · Tier 4 — Big4 and Consulting

**Players:** Deloitte, PwC, KPMG, EY, Accenture Security, Mandiant (Google Cloud)

**Strengths:**
- Trust and brand
- Deep regulatory practices
- Direct lines to BACEN supervisors

**Gaps vs Quarry:**
- Delivers Word documents and Excel spreadsheets
- No reproducible cryptographic seal
- Cost: R$ 50k–500k per engagement
- Cycle time: weeks to months per artifact

**Threat level:** **LOW** as a product, **HIGH** as a relationship.
Big4 owns the C-suite room.

---

## 07 · Feature Matrix

| Feature | Quarry | Vanta / Drata | OneTrust | Splunk / Sentinel | Tempest / Cipher | Big4 |
|---|---|---|---|---|---|---|
| Native Bacen 24h pack | ✅ ready | ❌ | ❌ | ❌ | ⚠️ service | ⚠️ Word/Excel |
| Native BCB 85 Art. 6º pack | ✅ ready | ❌ | ❌ | ❌ | ⚠️ service | ⚠️ |
| Native LGPD / ANPD Res. 15/2024 pack | ✅ ready | ⚠️ generic | ⚠️ LGPD module | ❌ | ⚠️ service | ⚠️ |
| TSA ICP-Brasil (SafeWeb) | ⚠️ framework ready | ❌ | ❌ | ❌ | ❌ | ❌ |
| e-CNPJ A3 signature | ⚠️ framework ready | ❌ | ❌ | ❌ | ❌ | ❌ |
| Auditable Merkle chain | ✅ verifiable | ❌ | ❌ | ⚠️ via SIEM | ❌ | ❌ |
| Brazilian data residency | ✅ 3 modalities | ❌ US-only | ⚠️ US/EU | ⚠️ Azure BR | ✅ BR | ✅ on-prem |
| PT-BR native (UI + support) | ✅ | ❌ EN-first | ⚠️ translation | ❌ EN | ✅ | ✅ |
| Deterministic HMAC pseudonymization | ✅ | ❌ | ⚠️ generic | ❌ | ❌ | ❌ |
| Counsel-validated structure | ✅ Parecer 012/2026 | ❌ | ❌ | ❌ | ⚠️ contractual | ✅ per engagement |
| Open-source / inspectable | ✅ GitHub | ❌ | ❌ | ❌ | ❌ | ❌ |
| Setup time | days | weeks | months | months | months | months |

---

## 08 · Where Quarry Wins

Three differentiators that **no incumbent can ship in under six months**:

### 1. Regulatory primitives as code

Bacen-specific YAML packs, signed with TSA + e-CNPJ, anchored to a Merkle
chain. A foreign vendor would have to acquire SafeWeb credentials and
ICP-Brasil certificates — they have not.

### 2. Sovereign data path

Three deployment modalities (Mac Mini on-prem, Hostinger BR, Hetzner DE)
plus cloud BYOK. Vanta and Drata send everything to US infrastructure by
default.

### 3. Counsel-validated structure

Independent legal opinion (**Parecer Jurídico Nº 012/2026**, Dr. Ricardo
Mendes) confirms admissibility under:
- CPC Art. 422 (electronic evidence)
- MP 2.200-2/2001 Art. 10 §1 (qualified electronic signature)
- Res. BCB 4.658/2018 (data governance)
- Res. CD/ANPD 15/2024 (breach notification)

None of the competitors publish equivalent legal validation.

---

## 09 · Honest Gaps

What Quarry does not yet have — and what unlocks each:

| Gap | Unlock | Cost |
|---|---|---|
| Production TSA wired (real SafeWeb, not mock) | SafeWeb account | R$ 60–150 / month |
| Production e-CNPJ A3 signer wired | Certificate purchase | R$ 250 / year |
| Public customer case study | First paying customer | — |
| Brand recognition vs Splunk | 12–24 months of execution | — |
| Signed final legal opinion (OAB-pending) | Close engagement with Dr. Ricardo | TBD |

**The technical foundation is built.** What is missing is operational and
commercial, not engineering.

---

## 10 · Strategic Moves

1. **Anchor customer** — one paying fintech under NDA, full pack deployed
   end-to-end. Eliminates the "you're too new" objection in 90% of
   pitches.
2. **Wire SafeWeb + e-CNPJ in production** — roughly R$ 250 / year total.
   Unlocks the "production-ready" pitch.
3. **Sign and publish Parecer 012/2026** with OAB number. Tag the repo
   `legal/v1.0`.
4. **Battle cards** for the top three threats: Vanta, OneTrust, Splunk.
   One-pager each for the sales conversation.

---

## 11 · Bottom Line

Quarry is the **only player on the planet** that ships a
Brazilian-regulator-native evidence engine with cryptographic chain of
custody, sovereign data residency, and counsel-validated structure.

The incumbents are bigger, better funded, and better known. **None of
them solve the specific Brazilian problem.** The window to claim the
category is open.

---

*Last updated: 2026-05-27 · Owner: 12Brain Solutions LLC*
