# FlitKey security policy

## Reporting a vulnerability

Please do not disclose exploitable vulnerabilities in a public issue. Use a private GitHub Security Advisory for the FlitKey repository. Include the affected version, platform, reproduction steps, impact, and any proposed mitigation. Do not include real PHI, credentials, or customer data in a report.

The maintainers must add a monitored security contact and response-time commitments before making an enterprise security commitment.

## Supported versions

Security fixes should target the latest release. The supported-version policy and end-of-life schedule must be published before a SOC or FSQS assessment.

## Security expectations

- Snippet and settings data is local application data and should be protected by the operating-system user account.
- FlitKey does not intentionally transmit snippets, clipboard values, or typed keys in the current repository.
- New network, synchronization, crash-reporting, analytics, or support functionality requires a data-flow review, threat model, privacy review, and dependency/vendor review before release.
- Releases should be built from CI, dependency-scanned, reviewed, and signed before distribution.

## Incident handling

Security incidents must be recorded, triaged, contained, investigated, remediated, and reviewed for notification obligations. The organization must maintain an incident response plan with named owners and legal/privacy escalation paths; this repository does not make a legal breach-notification determination.
