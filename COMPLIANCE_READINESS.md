# FlitKey compliance readiness

This document is a readiness register, not a certification, legal opinion, HIPAA attestation, SOC report, or FSQS qualification. FlitKey is currently a local desktop application with no hosted account service, central database, or telemetry service in this repository.

## Applicability and external assurance

- **HIPAA:** HIPAA applies to covered entities and business associates handling electronic protected health information (ePHI). A local-only design reduces the service boundary but does not by itself establish compliance or replace a risk analysis, policies, workforce training, or a business associate agreement where one is required. See the [HHS Security Rule summary](https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html).
- **SOC 2 and SOC 3:** These are independent CPA examination/reporting engagements against the AICPA Trust Services Criteria, not self-awarded product badges. SOC 2 is detailed for customers; SOC 3 is a general-use report. See [AICPA SOC 2 guidance](https://www.aicpa-cima.com/cpe-learning/publication/soc-2-reporting-on-an-examination-of-controls-at-a-service-organization-relevant-to-security-availability-processing-integrity-confidentiality-or-privacy) and [SOC 3 information](https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-3).
- **GDPR:** Applicability depends on the controller/processor role, location, and processing. The [GDPR text](https://eur-lex.europa.eu/eli/reg/2016/679/oj) requires documented purposes, lawful processing, data minimisation, security, retention, and data-subject rights where applicable.
- **CCPA/CPRA:** Applicability depends on the business and California consumer thresholds. The [California Attorney General CCPA resources](https://oag.ca.gov/privacy/ccpa) cover notice, access, deletion, correction, opt-out, and contract requirements.
- **FSQS:** FSQS is a financial-services supplier qualification and due-diligence process, not a universal technical certification. It requires an organization-level submission and evidence review; see [FSQS supplier information](https://hellios.com/meet-your-community-fsqs-suppliers).

## Current data inventory

| Data | Source | Storage | Purpose | Retention | Sharing |
| --- | --- | --- | --- | --- | --- |
| Snippet labels, triggers, and expansion text | User entry/import | Local `config.json` | User-requested expansion | Until user deletes it | No network sharing in this repository |
| Settings | User choices | Local `config.json` | Application behavior | Until user deletes it | No network sharing |
| Clipboard text | OS clipboard, only for `{{clipboard}}` | In-memory during rendering | User-requested expansion | Not retained by FlitKey | Not transmitted |
| Typed keys | OS input hook | Process memory only | Trigger matching | Not persisted | Not transmitted |

FlitKey must not be marketed as “HIPAA compliant,” “SOC certified,” “GDPR compliant,” “CCPA compliant,” or “FSQS certified” until counsel, an assessor, and the relevant program owner confirm the applicable scope and evidence.

## Control register

| ID | Control | Status / evidence |
| --- | --- | --- |
| SEC-01 | No telemetry or hosted data path | Implemented by current architecture; verify in release review |
| SEC-02 | Atomic config writes | Implemented in `text_expander/security.py` |
| SEC-03 | Restrictive POSIX data directory/file modes | Implemented (`0700`/`0600`); Windows relies on per-user ACLs |
| PRIV-01 | Data inventory and purpose limitation | Documented above; review every feature change |
| PRIV-02 | Local export/access mechanism | Implemented by `config.export_state()` |
| PRIV-03 | Local deletion mechanism | Implemented by `config.delete_state()`; add UI affordance before claiming end-user self-service |
| IR-01 | Incident response and breach escalation | Required organizational process; owner and contacts must be assigned |
| GOV-01 | Risk assessment, asset inventory, access reviews | Required organizational evidence; not represented by this desktop repository |
| GOV-02 | Vendor/subprocessor due diligence | Required before adding cloud services or dependencies |
| ASSUR-01 | SOC 2/SOC 3 independent examination | Not started; engage an accredited CPA firm |
| ASSUR-02 | FSQS qualification | Not started; register with the applicable FSQS/Hellios process |
| LEGAL-01 | DPA, BAA, privacy notice, and terms | Templates/notice required before processing customer-controlled regulated data |

## Required next gates

1. Define the legal entity, product service boundary, target countries/states, and whether FlitKey will ever receive customer-controlled ePHI or other regulated data.
2. Appoint owners for security, privacy, incident response, vendor risk, and evidence collection.
3. Complete a documented risk assessment and system description.
4. Add independent review, dependency scanning, signed release artifacts, access reviews, backup/recovery tests, and security training.
5. Obtain counsel review and engage the appropriate external assessor before publishing compliance claims.
