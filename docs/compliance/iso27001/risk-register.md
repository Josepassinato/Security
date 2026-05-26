# Initial ISO/IEC 27001 risk register

| ID | Risk | Impact | Likelihood | Initial rating | Treatment | Owner | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QR-ISO-R01 | Unauthorized VPS/root access changes production or exposes secrets. | High | Medium | High | Key-based SSH, authorized_keys review, access owner, periodic review, no shared keys. | ISMS owner | Access review, SSH config snapshot, user list. |
| QR-ISO-R02 | Secrets/API keys are stored in code, logs, or chat history. | High | Medium | High | Secrets inventory, env-only storage, rotation process, repo secret scanning. | Engineering | Secret scan report, rotation log. |
| QR-ISO-R03 | Production deploys happen without traceability. | Medium | Medium | Medium | Commit-linked deploys, PM2 restart logs, build logs, change record. | Engineering | Commit, build output, deployment note. |
| QR-ISO-R04 | Loss of production data or evidence due to missing backup verification. | High | Medium | High | Backup policy, restore test, retention schedule. | Operations | Backup log, restore test record. |
| QR-ISO-R05 | LLM-generated security decisions are not explainable to auditors. | High | Medium | High | Threat Ledger, AuditChain, prompt/tool/rationale retention, human approval gates. | Product | Case ledger export, approval record. |
| QR-ISO-R06 | External supplier outage affects Quarry availability. | Medium | Medium | Medium | Supplier register, fallback path, incident process. | Operations | Supplier register, incident test. |
| QR-ISO-R07 | Vulnerable dependencies introduce exploitable flaws. | High | Medium | High | Dependency scanning, patch cadence, critical fix SLA. | Engineering | Scan report, patch tickets. |
| QR-ISO-R08 | Inadequate incident response causes delayed customer/regulator communication. | High | Low | Medium | Incident response policy, tabletop, communication templates. | ISMS owner | Tabletop record, comms template. |
| QR-ISO-R09 | Misleading public claims create legal/commercial risk. | Medium | Medium | Medium | Claim approval process; use "readiness" until certified. | Commercial | Website review, copy approval. |
| QR-ISO-R10 | Customer data is mixed across tenants in hosted mode. | High | Low | Medium | Tenant isolation design review, RLS/access tests, logging. | Engineering | Isolation test, architecture record. |

## Review cadence

Review monthly during certification preparation, then quarterly after certification.
