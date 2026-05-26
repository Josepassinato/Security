# ISO/IEC 27001 evidence register

| Evidence area | Example evidence | Collection cadence | Owner |
| --- | --- | --- | --- |
| Scope approval | Signed/approved scope statement and exclusions. | At scope change | ISMS owner |
| Asset inventory | Repositories, servers, domains, data stores, SaaS tools, secrets inventory. | Monthly | Operations |
| Access review | GitHub access, VPS/root authorized keys, DNS, email, LLM provider, payment/CRM if used. | Monthly | ISMS owner |
| Change management | Commit hash, PR/review, build output, deploy command, PM2 restart, public validation. | Every release | Engineering |
| Backup | Backup job output, storage location, retention, restore test. | Monthly | Operations |
| Vulnerability management | Dependency scan, OS/package patch review, critical fix tracking. | Monthly and after critical advisory | Engineering |
| Incident response | Incident records, tabletop exercises, communications, lessons learned. | Quarterly or per incident | ISMS owner |
| Logging and monitoring | Nginx/PM2/app log samples, uptime checks, alert records. | Monthly | Operations |
| Supplier management | Supplier register, risk rating, contracts/terms, assurance documents. | Quarterly | Commercial/Operations |
| Security training | Security awareness record for maintainers/operators. | Onboarding and annual | ISMS owner |
| Risk management | Risk register, treatment plan, accepted risks, review minutes. | Monthly during readiness, quarterly after | ISMS owner |
| Management review | Review minutes, KPI review, corrective actions. | Quarterly | Leadership |
| Product auditability | Threat Ledger export, AuditChain sample, agent decision rationale, human approval evidence. | Per release/demo | Product |

## Evidence naming convention

Use:

`YYYY-MM-DD_control-area_short-description_owner`

Example:

`2026-06-05_access-review_github-vps_ism-owner`
