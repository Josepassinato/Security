# Initial Statement of Applicability

This is the first ISO/IEC 27001:2022 Annex A applicability baseline for the Quarry certification scope. It is not a final audited SoA.

| Annex A theme | Applicability | Quarry implementation direction | Evidence target |
| --- | --- | --- | --- |
| Organizational controls | Applicable | Security policy, risk process, supplier management, incident process, change management. | Approved policies, risk register, supplier register, incident tabletop. |
| People controls | Applicable | Operator responsibilities, onboarding/offboarding, security awareness, confidentiality expectations. | Training record, access grant/revoke records. |
| Physical controls | Partially applicable | Limited direct office dependence; cloud/VPS providers own physical facilities. Control via supplier assurance. | Supplier documentation, hosting provider terms. |
| Technological controls | Applicable | Access control, MFA, secrets management, logging, backup, vulnerability management, secure development, monitoring. | Access reviews, backup tests, scan reports, deployment logs. |
| Threat intelligence | Applicable | Detection corpora, MITRE mapping, Brazilian fintech threat patterns, supplier advisories. | Threat intel register, detection update records. |
| Identity and access management | Applicable | Named accounts, least privilege, SSH key review, GitHub role review. | Access review evidence. |
| Information backup | Applicable | Backup schedule, restore testing, retention. | Backup logs and restore test records. |
| Logging and monitoring | Applicable | PM2/Nginx/app logs, audit logs, case ledger, alerting for service failure. | Log samples, monitoring screenshots, incident records. |
| Secure coding | Applicable | Pull request review, dependency scanning, type-check/build gates, secret scanning. | PR evidence, build logs, scan reports. |
| Supplier relationships | Applicable | LLM providers, VPS/cloud, GitHub, DNS, email providers. | Supplier register and risk review. |
| Cloud services | Applicable | VPS/cloud hosting and optional hosted customer deployment. | Architecture diagram, provider assurance, configuration review. |
| Data leakage prevention | Applicable | Secrets handling, least privilege, evidence retention, customer data minimization. | Secret scan, DLP review, data flow diagram. |

## Initial exclusions

Controls tied to physical office security are limited in first scope because Quarry operations are primarily cloud/VPS and remote-development based. Supplier assurance and endpoint/operator controls should cover the practical risk.
