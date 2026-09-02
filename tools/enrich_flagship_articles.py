#!/usr/bin/env python3
"""Add maintained, page-specific depth and shared chrome to flagship articles."""

from __future__ import annotations

import re
from pathlib import Path

from build_content_hubs import footer, header


ROOT = Path(__file__).resolve().parents[1] / "FlitKey HP"
START = "<!-- editorial-expansion:start -->"
END = "<!-- editorial-expansion:end -->"


def comparison_method(product: str) -> list[tuple[str, str, str]]:
    return [
        (
            "evaluation-method",
            f"How this {product} comparison was evaluated",
            f"""<p>This page compares the jobs a person can complete, not the number of rows on a feature list. FlitKey behavior was checked against version 0.5.0, its public source, bundled documentation, and release artifacts. {product} claims are limited to the vendor pages linked below and should be rechecked before purchase because platforms, editions, pricing, and features change. The page does not award a performance winner: no shared, reproducible latency, memory, or startup dataset exists for these products.</p>
<p>The decision criteria are platform coverage, editing workflow, expansion behavior, dynamic content, migration risk, data location, administration, and support expectations. Each criterion matters only when it maps to a real task. A solo Linux user with fifty plain-text replies should not score team administration as if it were required. A managed support organization should not treat the absence of an account as automatically beneficial if it actually needs controlled sharing, roles, and offboarding.</p>""",
        ),
        (
            "test-fixture",
            "Use one small fixture before moving a real library",
            """<p>Create six disposable snippets: a one-line email address, a multiline support reply, Unicode text, a date placeholder, a clipboard placeholder, and a cursor-position marker. Add one trigger that deliberately collides with an existing shortcut. Test the fixture in a plain-text editor first, then in the browser, mail client, terminal, IDE, remote session, and line-of-business application you actually use. Record the operating system, session type, application version, expander version, and result.</p>
<p>Check more than whether text eventually appeared. Note whether the trigger characters were removed, line breaks survived, punctuation was duplicated, the clipboard changed, the cursor landed correctly, and undo restored the original input. Repeat the test in elevated applications if that is part of the job. A tool that passes Notepad or a basic editor can still fail in a rich editor, terminal, virtual machine, or administrator window because those applications process synthetic input differently.</p>""",
        ),
        (
            "scorecard",
            "Turn the choice into a written scorecard",
            """<p>Write five non-negotiable requirements and five useful extras. Give a product one point only after the requirement works in a real destination application. Keep unknown items marked unknown instead of interpreting an unchecked box as support. Include the cost of conversion, retraining, backups, updates, and support—not only the license price. This prevents a familiar interface from hiding a missing capability and prevents a free tool from appearing cheaper when manual maintenance is substantial.</p>
<p>Finish with a rollback decision. Keep the old tool and an untouched library backup until the new setup has survived normal work for several days. Disable overlapping triggers during the trial so two expanders do not act on the same input. If the new tool cannot preserve a critical script, form, rich-text item, or shared workflow, a partial migration can be safer than forcing every record into the same application.</p>""",
        ),
    ]


PAGES: dict[str, list[tuple[str, str, str]]] = {
    "blogs/comparisons/atext-vs-flitkey/index.html": comparison_method("aText") + [
        (
            "daily-workflow",
            "What daily editing feels like",
            """<p>Both products appeal to people who want to see and edit snippets rather than maintain a directory of configuration files. In FlitKey, a snippet has a label, trigger, expansion, optional hotkey, enabled state, and platform scope. The searchable Quick Insert window provides a second route when remembering a trigger is inconvenient. The application also exposes expansion packs and import from its main window.</p>
<p>That simplicity is a boundary as well as a benefit. FlitKey is centered on plain reusable text and a short list of placeholders. Users who depend on aText-specific rich content, images, scripting, application rules, synchronization, or other current edition features should prove those workflows separately. Do not infer equivalence from the fact that both products have a graphical snippet list.</p>""",
        ),
        (
            "windows-fit",
            "Windows: compare trust, features, and maintenance",
            """<p>On Windows, FlitKey 0.5.0 supports typed triggers, assigned hotkeys, Quick Insert, tray access, and local configuration. Its installer is not code-signed, so Microsoft Defender SmartScreen may show an unknown-publisher warning. That limitation matters on managed endpoints, where users may not be allowed to install unsigned software. Download from the project release page and follow organizational approval rules rather than dismissing the warning.</p>
<p>aText is a commercial application with a different release, support, and licensing relationship. That can be the stronger choice when vendor accountability or its specific Windows integration matters. Check the current system requirements and edition terms on the official site. The right comparison is not “paid versus free”; it is whether each distribution and maintenance model fits the machine on which the expander will run.</p>""",
        ),
        (
            "linux-fit",
            "Linux: session type changes the answer",
            """<p>FlitKey has a Linux build and documented source installation. In an X11 session, it uses <code>xinput</code> to observe triggers and <code>xdotool</code> to insert text. In a native Wayland session, version 0.5.0 does not provide typed triggers, global snippet hotkeys, or a global picker shortcut. The supported workflow is to open Quick Insert from the running application or tray, choose a rendered snippet, return to the destination, and paste.</p>
<p>The aText vendor site listed Windows and macOS, but not Linux, when this page was updated. Recheck that list before deciding. If Linux is mandatory, test FlitKey on the exact GNOME, KDE Plasma, Hyprland, X11, or Wayland setup in use. A distribution name alone does not establish session behavior.</p>""",
        ),
        (
            "dynamic-content",
            "Placeholders and content complexity",
            """<p>FlitKey recognizes <code>{{date}}</code>, <code>{{time}}</code>, <code>{{datetime}}</code>, <code>{{clipboard}}</code>, <code>{{cursor}}</code>, and a limited <code>{{choice:...}}</code> pattern. These cover common dates, clipboard reuse, cursor placement, and small choice lists. They are intentionally not a general scripting language. Nested logic, network lookups, application control, arbitrary code, and complex interactive forms are outside the product's stated scope.</p>
<p>Audit an aText library by classifying each item as static text, supported placeholder, rich content, automation, or unknown. Static items are the best migration candidates. Preserve anything product-specific until a manual replacement is tested. A successful CSV import proves that characters moved; it does not prove that the source product's behavior was recreated.</p>""",
        ),
        (
            "storage-backup",
            "Storage, backup, and device movement",
            """<p>FlitKey stores settings and snippets in a local JSON configuration file and does not provide a hosted account or built-in cloud synchronization. That makes the primary copy and deletion path easy to identify, but it places backup and multi-device movement on the user. Copy the configuration only through a storage method appropriate for the sensitivity of the snippets, and avoid editing the live file while FlitKey is running.</p>
<p>Local storage is not the same as secret storage. Administrators, malware running as the user, disk backups, search indexers, and anyone with access to an unlocked device may reach the file. Clipboard placeholders and the Wayland paste workflow can also leave data in clipboard history. Neither product should be treated as a password manager without a separately reviewed design.</p>""",
        ),
        (
            "migration-details",
            "A reversible aText-to-FlitKey migration",
            """<ol><li>Back up the complete aText library in its native format.</li><li>If the installed aText edition offers a plain CSV export, export a copied subset rather than the only library.</li><li>Normalize it to <code>trigger,expansion</code> or <code>label,trigger,expansion</code>.</li><li>Open FlitKey, select <strong>Import</strong>, and inspect the preview and result.</li><li>Compare counts and spot-check every migrated category.</li><li>Test triggers in real applications before disabling aText.</li></ol>
<p>FlitKey does not advertise a native reader for aText's proprietary database. Images, rich formatting, scripts, nested groups, application restrictions, and aText variables can be lost in a tabular export. Duplicate triggers also need attention: FlitKey 0.5.0 adds imported snippets and does not provide a full deduplication review screen. Keep dated backups of both configurations until the trial is complete.</p>""",
        ),
        (
            "choose-atext",
            "Choose aText when its strengths are requirements",
            """<p>aText is the more credible candidate when macOS support is required, when the team already depends on its current commercial features, or when a vendor-supported desktop product is preferable to maintaining an open-source utility. It may also be the lower-risk choice when an existing library contains complex content that cannot be represented by FlitKey's plain-text model. Verify the exact platform, edition, feature, and support term on the vendor site before purchase.</p>
<p>Staying put is a valid result. Switching costs include conversion, validation, trigger retraining, packaging, endpoint approval, and recovery planning. A subscription or license saving is not real if a critical workflow becomes manual or unsupported.</p>""",
        ),
        (
            "choose-flitkey",
            "Choose FlitKey when a focused local tool is enough",
            """<p>FlitKey is a good fit for an individual who uses Windows or Linux, wants a visual library, needs straightforward plain-text snippets, prefers an MIT-licensed codebase, and does not need a hosted account. The Espanso, AutoHotkey, CSV, TSV, and JSON import paths can reduce conversion work for supported static records. Expansion packs provide inspectable starting examples rather than a managed content service.</p>
<p>Do not choose it for macOS, mobile, centralized team permissions, cloud synchronization, SSO, SCIM, formal vendor certification, or full desktop automation. On Wayland, choose it only if the picker-and-paste process is acceptable. Those exclusions are part of the product decision, not footnotes to discover after installation.</p>""",
        ),
    ],
    "blogs/comparisons/phraseexpress-vs-flitkey/index.html": comparison_method("PhraseExpress") + [
        (
            "scope-difference",
            "The products have different ambitions",
            """<p>PhraseExpress is positioned as a mature commercial productivity and text-automation product with a broader feature surface. FlitKey is a small open-source desktop snippet manager. Both can reduce repeated typing, but that shared category does not make their automation, administration, formatting, or support models equivalent. A buyer who begins with a long feature table can miss this fundamental scope difference.</p>
<p>Start with the smallest complete workflow. If the requirement is “type a short trigger and insert approved plain text on one Windows or Linux machine,” FlitKey may cover it with less configuration. If the requirement includes rich formatting, complex macros, shared content, managed deployment, or vendor support, investigate the relevant PhraseExpress edition first. Confirm every feature against its current documentation rather than assuming it exists in all editions.</p>""",
        ),
        (
            "platforms",
            "Platform coverage is a hard gate",
            """<p>FlitKey supports Windows and Linux. PhraseExpress's official download information should be treated as the source of truth for its current desktop and mobile coverage. When this article was updated, the vendor download page did not list a Linux desktop build. That makes FlitKey the direct candidate in a Linux-only evaluation, but it does not automatically make FlitKey equivalent to PhraseExpress's Windows capabilities.</p>
<p>On Linux, distinguish X11 from Wayland. FlitKey provides typed triggers and global hotkeys on X11 when the documented utilities are available. Native Wayland sessions use Quick Insert and clipboard paste, without typed triggers or global expansion hotkeys in version 0.5.0. Test that sequence before committing a Linux team to a migration.</p>""",
        ),
        (
            "individual-team",
            "Individual utility versus managed content",
            """<p>FlitKey stores a library for the current desktop user. It does not provide a hosted organization, central policy console, role-based permissions, SSO, SCIM, or managed shared groups. A small team can exchange exported files through its own approved system, but that is file distribution, not collaborative administration. Someone must own naming, review, conflicts, updates, and offboarding.</p>
<p>PhraseExpress should be evaluated when shared content and administrative control are central. Check which collaboration, networking, or client-management features exist in the relevant edition and how they are licensed. For regulated or managed environments, include deployment, audit, access revocation, update control, vendor terms, and support response in the decision—not just whether a phrase can expand.</p>""",
        ),
        (
            "automation-depth",
            "Macros, forms, and automation depth",
            """<p>FlitKey's dynamic model is deliberately small: dates, times, clipboard text, cursor placement, and limited choices. It does not claim a PhraseExpress-compatible macro engine. It cannot reproduce arbitrary automation merely because the visible end result contains text. Application launching, calculations, conditional branches, complex prompts, data sources, and product-specific macros need separate evaluation.</p>
<p>Inventory a PhraseExpress library before exporting it. Mark each entry as static plain text, basic variable, rich content, macro, application-specific rule, shared resource, or unknown. Count how many items fall outside plain text. If the important value sits in advanced groups, FlitKey is probably the wrong replacement; preserving the current product can be safer than flattening behavior into fragile manual steps.</p>""",
        ),
        (
            "formatting",
            "Plain text, rich text, and destination applications",
            """<p>FlitKey is designed around text. That makes snippets portable across many editors, but it does not promise to preserve fonts, colors, tables, embedded images, or document-specific formatting from another product. Rich email signatures, medical layouts, formatted legal clauses, and branded responses should be tested as separate artifacts. A CSV export normally cannot carry the behavior or fidelity of a proprietary rich-content record.</p>
<p>Even plain text deserves application testing. Outlook, browsers, terminals, IDEs, remote desktops, and elevated windows can handle injected text differently. Include multiline output, Unicode, punctuation, undo, clipboard state, and cursor position in the fixture. Name the exact version and platform in the test log so a later software update can be compared with evidence.</p>""",
        ),
        (
            "privacy-model",
            "Data location is one part of the threat model",
            """<p>FlitKey has no hosted FlitKey account or telemetry service and keeps its JSON configuration locally. This can fit users who want to avoid sending a snippet library to a product-operated cloud. It does not guarantee confidentiality or legal compliance. The endpoint account, keyboard access, clipboard manager, synced folders, backups, logs, destination application, and update path all remain relevant.</p>
<p>PhraseExpress data handling depends on the selected product, edition, configuration, and any networking or cloud services the user enables. Review the vendor's current documentation and contracts for the actual deployment. Avoid collapsing the decision into “local equals safe” or “commercial equals compliant.” Security and compliance conclusions require the organization's data, controls, legal role, and operating environment.</p>""",
        ),
        (
            "migration-path",
            "Move only what the target can represent",
            """<p>FlitKey does not claim a native importer for PhraseExpress's proprietary database. If the installed PhraseExpress edition can export selected records to a plain tabular format, work from a copy and normalize supported text into two columns (<code>trigger,expansion</code>) or three (<code>label,trigger,expansion</code>). Import a small batch with FlitKey's main-window <strong>Import</strong> action, then compare the generated records one by one.</p>
<p>Do not delete the source library after a successful count. Counts cannot reveal stripped formatting, flattened variables, disabled application filters, changed trigger options, or lost hierarchy. Test representative items in their real destinations and keep PhraseExpress available until the new workflow has survived ordinary use. Unsupported macro-heavy categories can remain in PhraseExpress during a partial migration.</p>""",
        ),
        (
            "operations",
            "Updates, support, and operational ownership",
            """<p>A commercial vendor and an open-source project create different operational obligations. With PhraseExpress, evaluate the license term, update channel, deployment controls, documentation, and support commitment applicable to the chosen edition. With FlitKey, review GitHub releases, source changes, dependencies, unsigned Windows packaging, and who will test updates before distribution.</p>
<p>Free licensing does not eliminate maintenance. Someone must back up local configuration, validate releases, respond to platform changes, and answer user questions. Conversely, purchasing software does not by itself satisfy internal controls. Document the owner, update cadence, rollback package, approved source, and support route for either product.</p>""",
        ),
        (
            "choose-phraseexpress",
            "Choose PhraseExpress when breadth reduces risk",
            """<p>PhraseExpress is the stronger candidate when the required workflow depends on its verified advanced automation, rich content, team or network capabilities, supported platform integrations, or commercial support. It is also the conservative choice for an established library whose important behavior would be lost in plain-text export. Evaluate the correct edition and total operating cost rather than a generic product name.</p>
<p>Organizations should run a limited pilot with representative users and applications. Include content owners, endpoint administrators, security reviewers, and the people who will maintain shared material. The best result may be to retain PhraseExpress for managed workflows while using simpler tools only where their narrower scope is an advantage.</p>""",
        ),
        (
            "choose-flitkey-phrase",
            "Choose FlitKey for a smaller, inspectable workflow",
            """<p>FlitKey fits individuals who need plain-text expansion on Windows or Linux, prefer a visual editor, want a local file they can back up themselves, and do not require commercial administration. Its MIT license and public source support inspection and modification. Its importers and packs can accelerate setup for supported records without promising compatibility with a broader automation suite.</p>
<p>Reject FlitKey if the job requires macOS, mobile access, rich-text fidelity, central sharing, permissions, vendor certification, complex macros, or automatic typed expansion on Wayland. A clear rejection criterion is useful: it prevents a download from becoming a failed migration and keeps the comparison honest.</p>""",
        ),
    ],
}

PAGES.update({
    "blogs/comparisons/espanso-vs-flitkey/index.html": comparison_method("Espanso") + [
        (
            "configuration-model",
            "Visual library or configuration repository",
            """<p>The largest day-to-day difference is how the library is maintained. FlitKey presents labels, triggers, expansions, hotkeys, enabled state, and platform scope in a graphical manager. That suits people who want to browse and edit snippets without remembering file locations or YAML structure. Quick Insert also gives the library a searchable interface when a trigger is forgotten.</p><p>Espanso treats configuration files as a first-class interface. For developers, that can be an advantage: files are easy to review, version, generate, and share with familiar tools. Its package ecosystem, variables, forms, regex, scripts, and configuration depth cover workflows FlitKey does not attempt. A GUI is not automatically simpler if the existing team already has reliable configuration review and deployment.</p>""",
        ),
        (
            "capability-map",
            "Map advanced entries before choosing",
            """<p>Classify the current Espanso matches into static replacements, multiple triggers, variables, forms, scripts, regex triggers, packages, and application-specific rules. FlitKey's importer is intended for supported static <code>trigger</code> or <code>triggers</code> entries with text <code>replace</code> values and optional labels. It does not execute Espanso's configuration language or recreate every extension.</p><p>If most value comes from static responses and the maintenance problem is YAML friction, FlitKey is a credible trial. If the library is built around dynamic forms, shell output, regex, global variables, packages, or carefully reviewed configuration, Espanso is likely the better fit. Count important records, not total records: one critical script can outweigh hundreds of simple phrases.</p>""",
        ),
        (
            "wayland-comparison",
            "Wayland requires product- and version-specific testing",
            """<p>Do not interpret either product's Linux support as a promise that every compositor and application behaves the same. FlitKey 0.5.0 detects a Wayland session and switches to a limited picker-and-clipboard workflow. It does not provide typed triggers, global snippet hotkeys, or a global Quick Insert shortcut there. This page deliberately calls that Wayland-aware rather than native automatic expansion.</p><p>Espanso's Wayland behavior and installation method can change by release and environment; consult its current official documentation and issues for the exact distribution, desktop, and compositor. Test both products on the real session. Record whether the target is a native Wayland client or XWayland client, and include browsers, terminals, IDEs, and secure fields separately.</p>""",
        ),
        (
            "import-boundary",
            "What the Espanso importer preserves",
            """<p>Work from copied YAML. FlitKey reads supported match records, converts recognized static fields, and reports warnings for unsupported or malformed entries. Multiple source triggers can become separate FlitKey snippets. A successful import does not mean variables, forms, scripts, regex behavior, packages, filters, or source-file organization survived. Review the generated labels, triggers, and expansion text before testing runtime behavior.</p><p>Import only one small file first. Record the source count, imported count, skipped count, and warnings. Check multiline YAML, quotation marks, Unicode, escaped characters, and duplicate triggers. FlitKey adds imported records rather than treating the operation as a reversible synchronization, so restore from a backup if the test creates an unwanted batch.</p>""",
        ),
        (
            "maintenance-model",
            "Updates and backups follow different models",
            """<p>An Espanso library can live naturally in a version-control repository, but repositories containing personal or customer text need appropriate access controls and history management. FlitKey keeps a local JSON configuration that can be copied and diffed, although it offers no built-in cloud service, shared review workflow, or merge interface. In both cases, a backup should be tested before a large conversion.</p><p>For product updates, identify the approved package source, current version, rollback method, and owner. Open source gives both projects transparency, but it does not guarantee that every binary matches reviewed source or that dependencies are risk-free. Evaluate release provenance and permissions with the same care applied to other software that observes keyboard input.</p>""",
        ),
        (
            "choose-espanso",
            "Choose Espanso for programmable expansion",
            """<p>Espanso is the stronger choice for users comfortable with configuration files who need its verified packages, forms, scripts, regex triggers, variables, or advanced match controls. It is also a better match when the snippet library is already reviewed and distributed as code. Moving such a system into a smaller visual data model can remove the very capabilities that justified the tool.</p><p>Choose FlitKey when the actual library is mostly plain text, a visual manager will improve maintenance, Windows and Linux coverage is sufficient, and local individual use matters more than automation depth. On Wayland, accept the picker workflow explicitly. A two-tool arrangement can be valid during migration, but overlapping triggers should be disabled to prevent double expansion.</p>""",
        ),
    ],
    "blogs/comparisons/autohotkey-vs-flitkey/index.html": comparison_method("AutoHotkey") + [
        (
            "hotstrings-or-automation",
            "Separate hotstrings from the rest of the script",
            """<p>AutoHotkey is a Windows automation language; text expansion is one of many jobs it can perform. A plain hotstring that turns a short abbreviation into static text is conceptually close to a FlitKey snippet. A script that checks the active window, remaps keys, launches processes, manipulates controls, reads files, calculates values, or branches on conditions is not. FlitKey is not an AutoHotkey runtime.</p><p>Before comparing interfaces, count how many useful lines are simple hotstrings and how many depend on executable logic. FlitKey can reduce the editing burden for the first group. The second group should remain in AutoHotkey or be redesigned with full knowledge of the lost behavior. Never import or run an unknown script solely to inspect it; review copied text safely.</p>""",
        ),
        (
            "conversion-examples",
            "What a safe conversion looks like",
            """<p>A basic AutoHotkey hotstring with a static replacement can become a label, trigger, and expansion. Supported hotkey lines can also be recognized by FlitKey's importer. Options, continuation sections, escaping, expressions, functions, includes, and version-specific syntax require scrutiny. AutoHotkey v1 and v2 are different languages, so name the source version in the migration notes.</p><p>Use FlitKey's import preview and warning output as a filter, not as proof of equivalence. Compare every generated record with the source and test it in a disposable editor. If a line is skipped, preserve it in the original file until its intent is understood. Do not manually flatten a security-sensitive automation into text without reviewing the consequence.</p>""",
        ),
        (
            "windows-boundaries",
            "Windows permissions and application boundaries",
            """<p>Both tools can interact with input across applications, which makes integrity level, endpoint security, remote sessions, and application behavior relevant. A process running as a normal user may not control an elevated window. Games, secure desktops, virtual machines, remote applications, terminals, and rich editors can respond differently to hooks or simulated input. Test the exact boundary instead of relying on a global compatibility claim.</p><p>FlitKey's version 0.5.0 installer is unsigned and may trigger SmartScreen's unknown-publisher warning. AutoHotkey scripts can also be blocked or scrutinized by organizational controls because they are executable automation. Follow endpoint policy for either tool and use a controlled source, reviewed scripts, limited privileges, and documented rollback.</p>""",
        ),
        (
            "maintenance",
            "A GUI changes maintenance, not capability by itself",
            """<p>FlitKey makes straightforward snippets easier to discover visually. Labels, search, Quick Insert, enabled state, hotkeys, and platform scope are editable without writing syntax. That is useful for users who inherit a small response library or who rarely write code. The JSON file can be backed up, but there is no built-in team review or deployment service.</p><p>AutoHotkey source is explicit, composable, and well suited to version control when maintained by people who understand it. Tests and code review can make a complex automation more dependable than an opaque collection of GUI settings. The tradeoff is ownership: someone must understand language versions, permissions, includes, and failure modes. Choose the maintenance model the actual owner can sustain.</p>""",
        ),
        (
            "choose-ahk",
            "Choose AutoHotkey when the job is automation",
            """<p>Keep AutoHotkey when window management, key remapping, mouse control, conditional behavior, application APIs, loops, calculations, or script composition are requirements. It is also the rational choice when a mature script already works and has an accountable maintainer. Replacing it merely to gain a visual snippet list may create more risk than value.</p><p>Choose FlitKey when the job is primarily reusable plain text, users should edit entries visually, Linux support is useful, and a small set of placeholders is sufficient. A partial migration is often best: move static hotstrings into FlitKey and retain reviewed automation in AutoHotkey, with non-overlapping shortcuts and a written record of which tool owns each behavior.</p>""",
        ),
    ],
    "blogs/comparisons/textexpander-vs-flitkey/index.html": comparison_method("TextExpander") + [
        (
            "service-or-utility",
            "Hosted service or local desktop utility",
            """<p>TextExpander and FlitKey solve different organizational problems. TextExpander is built around an account, synchronized snippets, supported platforms, and team-oriented workflows. FlitKey is an individual desktop utility with local JSON storage and no hosted FlitKey account. The absence of a service reduces one data path, but also removes managed sharing, browser access, centralized administration, and vendor-operated synchronization.</p><p>For one person with a Windows or Linux desktop and a plain-text library, the smaller model may be sufficient. For a distributed team that must publish approved content, control access, synchronize changes, and offboard users, a local file per device is not an equivalent substitute. Compare the operating model before comparing price.</p>""",
        ),
        (
            "platform-reach",
            "Platform reach can settle the decision",
            """<p>FlitKey supports Windows and Linux but has no macOS, browser-extension, or mobile client. On Linux X11 it supports typed triggers and global hotkeys with the documented utilities. On native Wayland, version 0.5.0 uses Quick Insert plus clipboard paste and does not offer automatic typed triggers. TextExpander's current supported applications and operating systems should be confirmed on its official site for the intended plan.</p><p>A person moving between several device types may reasonably prefer a synchronized service even if local desktop software is free. Conversely, a Linux-first user should confirm that the candidate provides the required Linux workflow. “Cross-platform” is too broad to decide anything without listing each device and destination application.</p>""",
        ),
        (
            "team-controls",
            "Sharing is more than copying a file",
            """<p>A managed snippet group needs an owner, review process, publishing rule, access model, version history, and removal process. TextExpander should be evaluated when those capabilities are requirements, using the current plan documentation and organizational terms. FlitKey can export and import files through a user's chosen channel, but it does not provide roles, centrally managed groups, SSO, SCIM, or an administrative console.</p><p>It is possible to build file distribution around FlitKey, but that becomes the organization's system to secure and maintain. Conflicts, stale copies, departed users, local modifications, and sensitive snippet content need explicit handling. Do not describe manual file sharing as equivalent to a supported collaboration product.</p>""",
        ),
        (
            "content-model",
            "Compare the content model, not only trigger syntax",
            """<p>FlitKey handles plain text, labels, keyword triggers, optional hotkeys, platform scope, Quick Insert, and a small placeholder set for date, time, clipboard, cursor, and choices. It does not claim parity with TextExpander's current rich content, fill-ins, team features, integrations, or other plan-specific capabilities. Verify the precise TextExpander feature used by the library before attempting a conversion.</p><p>Inventory every snippet as static text, supported placeholder, interactive content, rich content, shared content, or unknown. A CSV can move simple rows while discarding behavior that has no column. Preserve the original account and export until representative records pass in the real applications and devices.</p>""",
        ),
        (
            "privacy-cost",
            "Privacy and cost need complete accounting",
            """<p>FlitKey does not send a library to a FlitKey-operated account, charge a subscription, or provide telemetry. The endpoint, configuration file, clipboard, backups, and destination applications can still expose content. Local operation is not a HIPAA, GDPR, SOC 2, or other compliance certification. Organizations must assess their own legal role and controls.</p><p>TextExpander pricing, data practices, contractual options, and security documentation can change; use the official pages for the current plan. Include staff time, administration, migration, support, device coverage, and failure recovery in total cost. Free software with a hand-built sharing system can cost more to operate than a subscription, while an individual who needs no sharing may receive little value from recurring team features.</p>""",
        ),
        (
            "choose-te",
            "Choose the product that matches ownership",
            """<p>Choose TextExpander when synchronized access, supported multi-device workflows, shared content, administration, or vendor services justify the account and recurring price. It can be the safer choice for an organization already relying on those capabilities. Validate the current plan, platform, export options, data terms, and support channel before committing.</p><p>Choose FlitKey for individual Windows or Linux use when visual plain-text management, local files, open source, and no subscription are the actual requirements. Reject it when macOS, mobile, centralized teams, rich content, or automatic Wayland triggers are mandatory. Run the fixture and migration sample before canceling anything; a decision page cannot validate a private library.</p>""",
        ),
    ],
    "wayland-text-expander.html": [
        (
            "protocol-basics",
            "Why Wayland changes global text expansion",
            """<p>X11 historically allowed desktop clients broad access to global input and synthetic input. That made system-wide triggers possible, but it also created a large trust boundary. Wayland compositors intentionally mediate those capabilities. There is no single universal replacement that every compositor, toolkit, desktop, sandbox, and application exposes in the same way.</p><p>As a result, “supports Linux” and “runs on Wayland” do not answer whether typed expansion works. A program can display its window under Wayland while lacking global keyboard observation or cross-application insertion. Ask three separate questions: can the manager launch, can it detect a trigger outside itself, and can it insert text into the focused client?</p>""",
        ),
        (
            "identify-stack",
            "Identify the actual desktop stack",
            """<p>Run <code>echo $XDG_SESSION_TYPE</code> to distinguish <code>x11</code> from <code>wayland</code>. Record the distribution, desktop or compositor, and version as separate facts: Ubuntu with GNOME, Fedora with KDE Plasma, and Arch with Hyprland are not interchangeable test environments. An XWayland application inside a Wayland session does not convert the whole session into X11.</p><p>Also record how FlitKey was launched, whether a tray implementation is present, and whether the destination is native Wayland or XWayland. This makes a bug report reproducible and prevents a fix for one compositor from being presented as universal support.</p>""",
        ),
        (
            "picker-workflow",
            "The supported FlitKey 0.5.0 Wayland workflow",
            """<ol><li>Launch FlitKey and keep its main window or tray item available.</li><li>Open Quick Insert from the application or tray menu.</li><li>Search by label, trigger, or content.</li><li>Select the snippet so FlitKey renders placeholders and copies the result.</li><li>Return to the destination and paste using its normal shortcut.</li></ol><p>There is no global Quick Insert shortcut, typed trigger monitoring, or global expansion hotkey on native Wayland in this release. The extra focus and paste steps are the practical cost of the fallback. If those steps interrupt the job, evaluate another documented input method rather than relabeling the limitation.</p>""",
        ),
        (
            "clipboard-risk",
            "Clipboard behavior needs its own test",
            """<p>The picker workflow places rendered content on the clipboard. Clipboard managers may keep a history; synchronized clipboards and remote-desktop tools may copy it to other devices; the destination may log or upload the pasted value. Disable history or synchronization where required, clear sensitive content, and avoid passwords, tokens, recovery codes, private keys, or regulated records in ordinary snippets.</p><p>Test multiline text, Unicode, very long content, dates, choices, cursor markers, and the current clipboard value. Note whether FlitKey restores prior clipboard content and whether the destination preserves line breaks. Clipboard behavior can differ even when selection from the picker succeeds.</p>""",
        ),
        (
            "desktop-matrix",
            "Test GNOME, KDE Plasma, and Hyprland separately",
            """<p>A desktop matrix should name the session and applications, not simply mark a distribution “supported.” On GNOME, verify tray availability as well as the picker. On KDE Plasma, test the same actions without assuming GNOME results transfer. On Hyprland or another wlroots-based compositor, record the compositor version and any portal or tray components in use.</p><p>For every environment, test a native editor, browser, terminal, and one work-specific application. Record launch, tray, picker, placeholder rendering, copy, paste, and autostart as distinct outcomes. Publish unknown results as unknown until tested.</p>""",
        ),
        (
            "troubleshooting",
            "Troubleshoot the failed stage",
            """<p>If the window does not launch, start from a terminal and capture a sanitized error with the FlitKey and Python versions. If Quick Insert opens but search fails, reproduce with a new non-sensitive snippet. If selection works but paste fails, test the clipboard in a plain editor and inspect clipboard-manager policy. If the tray is missing, confirm the desktop's status-notifier support rather than treating it as an input-backend defect.</p><p>On X11, separately verify that <code>xinput</code> and <code>xdotool</code> are installed. Do not install X11 utilities expecting them to bypass a native Wayland compositor's security model. Report session type, desktop, versions, installation method, and minimal reproduction in the issue.</p>""",
        ),
        (
            "selection-guide",
            "When another approach is the better choice",
            """<p>Choose FlitKey on Wayland when a visual local library and explicit picker-and-paste interaction are acceptable. Choose an alternative when automatic triggers are non-negotiable, but examine how that alternative obtains input and injection access. Possible approaches can involve input methods, accessibility services, compositor protocols, portals, device access, or privileged components; each has compatibility and security tradeoffs.</p><p>Users who control their login session can also evaluate an X11 session if its broader input model fits their threat model and desktop roadmap. Do not recommend changing protocols solely for text expansion without considering screen sharing, input isolation, display features, and distribution support.</p>""",
        ),
    ],
    "espanso-migration-guide.html": [
        (
            "migration-inventory",
            "Build an inventory before opening the importer",
            """<p>Count YAML files and match records, then label each record static text, multiple-trigger static text, variable, form, script, regex, package dependency, application rule, or unknown. Record global variables and includes that may make a simple-looking replacement dynamic. The inventory provides a denominator for the import report and exposes categories that need to remain in Espanso.</p><p>Search for duplicate triggers across files. FlitKey 0.5.0 adds imported snippets and does not provide a complete deduplication preview, so importing overlapping files or repeating a batch can create collisions. Decide which source wins before conversion.</p>""",
        ),
        (
            "sample-yaml",
            "Start with a minimal copied YAML fixture",
            """<pre><code>matches:
  - trigger: ":hello"
    label: "Greeting"
    replace: "Hello, thanks for your message."
  - triggers: [":addr", ":address"]
    replace: "Example Street\nExample City"</code></pre><p>Use non-sensitive sample content and keep the original file untouched. After import, expect supported static records to appear as FlitKey snippets. Multiple triggers may produce separate records. Quoting, newlines, Unicode, and escape sequences deserve manual comparison. Variables, forms, shell commands, regex matches, application filters, and package behavior are not made equivalent by reading the file.</p>""",
        ),
        (
            "read-report",
            "Read warnings as required work",
            """<p>Write down the imported, skipped, and warning counts. Inspect every warning and preserve the source entry until its behavior is either recreated safely or intentionally retired. A count match alone is insufficient: a converted value may have different line breaks, placeholders, trigger boundaries, or application behavior.</p><p>Review labels and triggers inside FlitKey before enabling both applications. Test in a disposable editor, then the actual browser, terminal, IDE, mail client, and remote session. On native Wayland, use Quick Insert and clipboard paste; typed-trigger testing is not applicable to FlitKey 0.5.0 there.</p>""",
        ),
        (
            "rollback-plan",
            "Define rollback before the trial",
            """<p>Back up Espanso's complete configuration tree and FlitKey's <code>config.json</code> outside their live directories. Give each copy a date, source version, and checksum if the library matters operationally. Pause one expander while validating the other so the same abbreviation cannot expand twice.</p><p>Keep Espanso installed until important snippets have survived normal use for several days. If an import batch is wrong, restore the backed-up FlitKey configuration rather than deleting records from memory. A partial migration is acceptable: static text can move while forms, regex, scripts, and packages remain in Espanso with distinct triggers.</p>""",
        ),
    ],
})

# Target-closing sections are intentionally page-specific. They prevent the
# published editorial briefs from being satisfied with repeated filler.
PAGES["blogs/comparisons/espanso-vs-flitkey/index.html"].append((
    "decision-scenarios",
    "Three realistic decision scenarios",
    """<p>A Linux developer who keeps snippets beside source code, reviews YAML in pull requests, and relies on regex or shell variables should prefer Espanso. The configuration model is part of that workflow, not an obstacle. A support specialist with a few hundred static replies, no scripts, and difficulty finding the correct YAML file is a better FlitKey candidate because labels, search, editing, and Quick Insert are visible in one interface.</p><p>A Wayland user needs a third answer. If typing the trigger must immediately insert text in every destination, FlitKey 0.5.0 does not meet the requirement. If opening a local picker and pasting is acceptable, its visual library remains useful. Test the actual compositor and applications before moving anything. These scenarios illustrate why “GUI alternative” describes an editing preference, not feature parity or universal Linux compatibility.</p><p>For a mixed Windows and Linux setup, run the same fixture on each machine and compare the maintenance burden as well as expansion output. A shared source format may favor Espanso; a shared visual workflow may favor FlitKey. Platform consistency across machines must be demonstrated with dated, reproducible application test notes, not inferred from two download buttons.</p>""",
))
PAGES["blogs/comparisons/autohotkey-vs-flitkey/index.html"].append((
    "migration-checklist-ahk",
    "A practical hotstring migration checklist",
    """<ol><li>Copy the script and identify whether it targets AutoHotkey v1 or v2.</li><li>Separate static hotstrings and hotkeys from expressions, functions, remaps, includes, and window conditions.</li><li>Back up FlitKey's current configuration.</li><li>Import the copied sample and read every warning.</li><li>Compare the generated trigger and text with the source line.</li><li>Disable the corresponding AutoHotkey hotstring before runtime testing.</li></ol><p>Include option-sensitive cases such as immediate expansion, case behavior, ending characters, escaped punctuation, multiline content, and application-specific directives. If the migrated record behaves differently, restore the source behavior rather than layering additional keystroke automation blindly. Keep executable scripts under their existing review process; a text-expander import should never become a route around script security policy.</p><p>Document deliberately retained scripts, their owners, versions, and backup locations so future users know where to edit, test, and recover them safely.</p>""",
))
PAGES["blogs/comparisons/textexpander-vs-flitkey/index.html"].append((
    "exit-plan",
    "Plan for export, cancellation, and recovery",
    """<p>Before changing a subscription, confirm which export formats the current TextExpander account and plan provide, who owns shared groups, and what happens to access after cancellation. Export a sanitized copy, retain the native backup where available, and document the date and product version. Do not make the only backup dependent on an account that is about to be closed.</p><p>Import a small plain-text subset into FlitKey through a supported CSV, TSV, or JSON shape. Compare labels, abbreviations, content, line breaks, and placeholders. Shared permissions, usage data, rich content, interactive fields, and service integrations may not have a FlitKey equivalent. Keep the existing service active until owners confirm that required content was preserved and representative users pass the application fixture. The ability to import rows is not an exit guarantee.</p><p>After the trial, test restore from both exports and record who can access each backup. Remove temporary files containing real customer or organizational content according to the applicable retention policy.</p>""",
))
PAGES["wayland-text-expander.html"].append((
    "wayland-acceptance",
    "A clear acceptance test for Wayland",
    """<p>Call the setup successful only when FlitKey starts reliably, the chosen access path remains available, Quick Insert finds the expected snippet, placeholders render correctly, the clipboard receives the intended text, and every required destination accepts the paste. Repeat after logout and after enabling autostart. Record failures by stage instead of describing the whole product as broken.</p><p>Call it unsuitable when the work requires hands-free trigger expansion, policy forbids clipboard use, the tray or main window cannot remain accessible, or sensitive content would enter unmanaged clipboard history. That negative result is useful: it identifies a product-workflow mismatch without pretending a hidden setting will restore unavailable global input.</p>""",
))
PAGES["espanso-migration-guide.html"].append((
    "completion-criteria",
    "Define when the migration is complete",
    """<p>A migration is complete when the inventory is reconciled, unsupported entries have an explicit owner, representative snippets pass in their destination applications, backups can be restored, and users know which expander owns each remaining trigger. It is not complete merely because the importer displayed a success message.</p><p>Archive the conversion notes with the source version, FlitKey version, operating system, session type, imported files, warnings, manual edits, and rollback location. Remove the old expander only after an agreed observation period. If advanced Espanso records remain, document the partial migration and keep triggers distinct so future maintainers do not mistake two active tools for duplication or corruption.</p>""",
))
PAGES["blogs/comparisons/textexpander-vs-flitkey/index.html"].append((
    "official-textexpander-sources",
    "Official TextExpander sources checked",
    """<p>Product facts were checked on August 3, 2026. Use TextExpander's <a href="https://textexpander.com/pricing" target="_blank" rel="noopener">official pricing page</a> for current plans, its <a href="https://textexpander.com/learn/accounts/installing-textexpander" target="_blank" rel="noopener">installation guide</a> for current Windows, macOS, Chrome/Linux, and iOS routes, and its <a href="https://textexpander.com/security" target="_blank" rel="noopener">security page</a> for vendor-stated controls and certifications. Those sources describe TextExpander's current offering; they do not certify a customer's deployment.</p><p>FlitKey behavior is based on version 0.5.0 source, tests, and documentation linked from this site. Recheck both products after a material release, plan change, or platform update.</p>""",
))


def render(sections: list[tuple[str, str, str]]) -> str:
    toc = "".join(f'<li><a href="#{section_id}">{title}</a></li>' for section_id, title, _ in sections)
    body = "".join(
        f'<section id="{section_id}" class="article-section"><h2>{title}</h2>{content}</section>'
        for section_id, title, content in sections
    )
    return f'{START}<nav class="article-toc" aria-label="Additional analysis"><h2>Detailed evaluation</h2><ol>{toc}</ol></nav>{body}{END}'


def enrich(relative: str, sections: list[tuple[str, str, str]]) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    text = re.sub(rf"{re.escape(START)}.*?{re.escape(END)}", "", text, flags=re.S)
    text = re.sub(r'<header class="header">.*?</header>', header(), text, count=1, flags=re.S)
    text = re.sub(r'<footer class="footer">.*?</footer>', footer(), text, count=1, flags=re.S)
    text = re.sub(r'<link rel="preconnect" href="https://fonts\.(?:googleapis|gstatic)\.com"(?: crossorigin)?>', '', text)
    text = re.sub(r'<link href="https://fonts\.googleapis\.com/[^\"]+" rel="stylesheet">', '', text)
    text = re.sub(
        r'class="([^"]*\bdocs-main\b[^"]*)"',
        lambda match: f'class="{match.group(1)} article-shell"' if "article-shell" not in match.group(1) else match.group(0),
        text,
        count=1,
    )
    text = text.replace('class="docs-section"', 'class="docs-section article-section"')
    main_start = text.find("<main")
    if main_start != -1:
        prefix, main = text[:main_start], text[main_start:]
        main = re.sub(
            r'<div style="(?=[^"]*background:\s*var\(--bg-card\))(?=[^"]*margin-bottom:\s*(?:30|32)px)[^"]*">',
            '<div class="article-meta">',
            main,
            count=1,
        )
        main = re.sub(r'<header(?:\s+[^>]*)?>', '<header class="article-header">', main, count=1)
        header_pos = main.find('<header class="article-header">')
        if "article-meta" not in main[:header_pos] and header_pos != -1:
            meta = '<div class="article-meta">Written by <a href="/about">Swaraj Nandedkar</a> &bull; Updated August 3, 2026 &bull; Product behavior checked against FlitKey 0.5.0</div>'
            main = main[:header_pos] + meta + main[header_pos:]
        main = re.sub(
            r'<div class="article-meta">(Written by .*?)</div>',
            r'<div class="article-meta"><span>\1</span></div>',
            main,
            count=1,
            flags=re.S,
        )
        main = main.replace('class="badge badge-pulse"', 'class="section-tag"', 1)
        main = re.sub(r'<h1(?:\s+style="[^"]*")?>', '<h1>', main, count=1)
        main = re.sub(
            r'<p(?:\s+style="[^"]*")?>(\s*<strong>Short answer:?</strong>)',
            r'<p class="direct-answer">\1',
            main,
            count=1,
            flags=re.I,
        )
        main = re.sub(
            r'<div style="(?=[^"]*border-left:\s*4px solid var\(--accent\))[^\"]*">',
            '<div class="direct-answer">',
            main,
            count=1,
        )
        text = prefix + main
    expansion = render(sections)
    marker = '<section class="cta-banner"'
    if marker in text:
        text = text.replace(marker, expansion + marker, 1)
    else:
        text = text.replace("</main>", expansion + "</main>", 1)
    path.write_text(text, encoding="utf-8")
    print(path)


def main() -> None:
    for relative, sections in PAGES.items():
        enrich(relative, sections)
    # Keep the regular-file public routes synchronized for Netlify deploys.
    from materialize_public_routes import main as materialize_public_routes

    materialize_public_routes()


if __name__ == "__main__":
    main()
