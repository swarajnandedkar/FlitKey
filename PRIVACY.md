# FlitKey privacy notice

**Status:** draft for legal review. This notice describes the current open-source desktop application and is not legal advice.

## What FlitKey processes

FlitKey stores snippets, triggers, and settings locally on the device. It does not create an account, send snippets to a FlitKey server, or include telemetry in this repository. The optional `{{clipboard}}` placeholder reads the operating-system clipboard only when the user expands a snippet containing that placeholder; the value is held in memory for that operation and is not persisted by FlitKey.

On X11 and Windows, FlitKey observes keyboard events locally to detect enabled triggers. The events are processed in memory and are not recorded as a keystroke history. Wayland uses the documented clipboard fallback.

## User controls

The configuration file can be exported with `text_expander.config.export_state()` and deleted with `text_expander.config.delete_state()`. Users can also remove the FlitKey configuration directory using their operating system file tools. The application does not provide a hosted account portal, so access, deletion, and portability requests for local data are performed on the device.

## Retention and sharing

Data remains on the device until the user deletes it. FlitKey has no network sharing path in the current repository. Distribution services, operating-system components, or future hosted features may have separate privacy terms and must be added to the data inventory before release.

## Regulated data

Do not enter protected health information, payment-card data, secrets, or other regulated information unless your organization has completed its own risk assessment and approved the device, operating system, deployment, and support process. A local-only application is not automatically HIPAA, GDPR, CCPA, SOC, or FSQS compliant.

## Contact and changes

Before production publication, the legal entity must add a privacy contact, applicable controller/processor role, legal bases, jurisdictional disclosures, and an effective date. Review this notice whenever a network, account, synchronization, analytics, crash-reporting, or support feature is added.
