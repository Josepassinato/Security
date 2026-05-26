# Minimum policy set for ISO/IEC 27001 readiness

The first ISO 27001 run should keep policies short, enforceable, and evidence-driven.

## Required policies

1. Information Security Policy
   - Purpose, scope, leadership commitment, security objectives.

2. Risk Management Policy
   - Risk scoring method, acceptance rules, treatment plan, review cadence.

3. Access Control Policy
   - Named accounts, least privilege, MFA, SSH key review, offboarding.

4. Acceptable Use and Operator Responsibility Policy
   - Device expectations, handling production access, prohibited behavior.

5. Secure Development and Change Management Policy
   - Pull requests, build checks, release approval, emergency changes.

6. Secrets Management Policy
   - API keys, env vars, rotation, no secrets in code, chat, logs, or docs.

7. Backup and Restore Policy
   - Backup scope, retention, restore testing, ownership.

8. Incident Response Policy
   - Severity, escalation, evidence preservation, customer/regulator communication.

9. Supplier Security Policy
   - Supplier register, risk rating, assurance collection, annual review.

10. Evidence Retention Policy
    - What evidence is retained, retention period, location, access restrictions.

11. AI Governance Policy
    - Human approval, agent decision logging, prompt/tool traceability, prohibited autonomous actions.

12. Public Security Claims Policy
    - Controls how the company says "aligned", "readiness", "certified", or "audited".

## Implementation note

Do not create long policies that nobody follows. The certification will be stronger if each policy maps to actual logs, screenshots, tickets, commits, and reviews.
