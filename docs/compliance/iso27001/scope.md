# ISO/IEC 27001 scope

## Organization

12Brain Solutions LLC, controlling company address:

428 Plaza Real, Boca Raton, FL, United States.

## ISMS scope

The ISMS covers the people, processes, technology, suppliers, and evidence used to develop, operate, support, and sell Quarry as an AI-assisted Security Operations Center for regulated companies.

Included:

- Quarry source code and repositories.
- Quarry production and staging infrastructure.
- CI/CD, deployment, change management, and release evidence.
- Access to VPS, GitHub, cloud services, LLM providers, email, monitoring, and operational tools.
- Security monitoring, logs, audit trail, backup, and restore verification.
- Incident response and customer-facing security communications.
- Product security features that support auditability: Threat Ledger, AuditChain, agent decision records, playbooks, and compliance evidence.
- Supplier management for providers that can affect confidentiality, integrity, availability, or privacy.

Excluded from first certification scope:

- Other 12Brain products not directly required to operate Quarry.
- Customer environments where Quarry may be self-hosted.
- Customer data imported into self-hosted deployments.
- Experimental demos that are not part of the paid Quarry operating environment.

## Interfaces and dependencies

- GitHub: source code, pull requests, issues, release history, repository access.
- VPS and hosting infrastructure: production runtime, Nginx, PM2, logs, backups.
- Domain and DNS providers: public service resolution.
- LLM providers: agent reasoning and enrichment where configured.
- Email provider: commercial and incident communications.
- Security tooling: vulnerability checks, dependency alerts, endpoint/device security where available.

## First audit goal

The first audit should prove that Quarry is developed and operated under controlled security processes, not that every possible product module is mature. The certification should make enterprise buyers comfortable that security is managed systematically.
