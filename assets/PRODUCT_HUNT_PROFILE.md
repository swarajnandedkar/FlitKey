# FlitKey — Product Hunt Launch Profile

## Submission essentials

| Field | Copy |
| --- | --- |
| Product name | FlitKey |
| Tagline | A free, offline text expander for Windows and Linux |
| Website | https://flitkey.xyz/ |
| Product URL | https://flitkey.xyz/ |
| GitHub | https://github.com/swarajnandedkar/FlitKey |
| Pricing | Free — MIT licensed. No account, paid tier, trial, or telemetry. |
| Platforms | Windows 10/11; Linux (full typed-expansion support on X11; Quick Insert clipboard workflow on native Wayland). |
| Suggested topics | Productivity, Open Source, Developer Tools |
| Maker | Swaraj Nandedkar — https://github.com/swarajnandedkar |

## Thumbnail and gallery

Use the FlitKey logo as the thumbnail: `assets/new-flitkey-logo.png`.

Upload these gallery images in this order:

1. `assets/product-hunt-screenshots/03-snippet-library.png` — **Your snippets, in one calm workspace.** Browse, search, edit, and toggle every shortcut without touching a config file.
2. `assets/product-hunt-screenshots/04-quick-insert.png` — **Find the right snippet in seconds.** Open Quick Insert, search by name or trigger, and press Enter to insert.
3. `assets/product-hunt-screenshots/02-expansion-packs.png` — **Start with a useful library.** Load packs for AI prompts, development, support, design, DevOps, and everyday work.
4. `assets/product-hunt-screenshots/01-main-window.png` — **Built for local-first workflows.** See runtime capabilities and manage preferences from the desktop app.

Optional fifth gallery image: `assets/Flitkey Snippet Customer Support.gif` with the caption **Turn a short trigger into a complete reply.**

## Product description

FlitKey turns short triggers into the text you use every day — without sending your snippets or typing to a cloud service.

Create keyword shortcuts, attach global hotkeys, or open a searchable Quick Insert picker. FlitKey supports dynamic date, time, clipboard, and cursor placeholders, so a snippet can be more than static text. Need a faster start? Load built-in packs for AI prompts, developer workflows, customer support, design, DevOps, and everyday productivity. Moving from another tool? Import Espanso YAML, AutoHotkey scripts, CSV/TSV, or JSON.

Everything lives locally on your machine. FlitKey is free, open source, and MIT licensed for Windows and Linux.

## Maker comment

Hey Product Hunt — I’m Swaraj, maker of FlitKey.

I built FlitKey because text expansion should not require a subscription, a cloud account, or a pile of YAML just to save a reply, prompt, or command you type every week. I wanted a small desktop app where the important work is visible: create a snippet, give it a trigger, search it later, and keep the data on your own machine.

FlitKey gives you three ways to reuse text:

- Type a keyword trigger on supported systems.
- Use a global hotkey.
- Search with Quick Insert and press Enter.

It also handles the practical details: dynamic date/time and clipboard placeholders, cursor placement, built-in expansion packs, and imports from Espanso, AutoHotkey, and common text formats.

The platform detail worth calling out: X11 supports typed triggers, hotkeys, and direct insertion. On native Wayland, its security model limits global key listening and simulated input, so FlitKey uses the Quick Insert + clipboard paste workflow instead.

FlitKey is free, MIT licensed, and runs completely offline — no accounts and no telemetry. I’d love to hear which snippets, import paths, or Linux desktop setups you want it to support next.

## First reply / FAQ

**Is FlitKey really offline?**  
Yes. Snippets and settings are stored locally. FlitKey has no account requirement, cloud service, or telemetry.

**Which systems work best?**  
Windows 10/11 and Linux X11 support typed triggers, global hotkeys, and direct insertion. On native Wayland, use Quick Insert and paste from the clipboard.

**Can I move from Espanso or AutoHotkey?**  
Yes. FlitKey imports Espanso YAML, AutoHotkey `.ahk`, plus CSV, TSV, and JSON files.

**Do I need to make every snippet myself?**  
No. The built-in packs cover AI prompts, developer workflows, customer support, artist/designer work, system administration/DevOps, and everyday productivity.

**How much does it cost?**  
Nothing. Every feature is free under the MIT license.

## Product Hunt founder / investor questions

### Why are you the right founder/team to work on this?

I built FlitKey from the constraint that makes text expansion hard to get right: it has to work where people actually type, while respecting the operating system rather than pretending every desktop has the same permissions.

That is why FlitKey has separate runtime backends for Windows, X11, and Wayland; native keyword expansion and hotkeys where the platform permits them; and a transparent Quick Insert + clipboard path where Wayland deliberately restricts global input simulation. The product is not a generic web app wrapped in a desktop shell. It is a small, local desktop utility with the implementation details needed to make that promise credible.

I have also kept the scope disciplined. FlitKey is built around the workflows that make a text expander useful on day one: a visual snippet manager, search, imports, placeholders, packs, and a local config users can own. The project is open source, so the product decisions and the implementation are inspectable rather than hidden behind a SaaS account.

### Why did you pick this idea to work on?

The original problem is mundane and expensive: people repeatedly type the same support replies, prompts, commands, introductions, links, and templates. Existing options often ask users to choose between a subscription, a cloud account, editing configuration files, or a setup that does not fit their operating system.

FlitKey is the alternative I wanted to use: a real GUI for creating and finding snippets, no account, no telemetry, and no requirement to send writing or work context to a third party. It is intentionally useful before a user builds a library from scratch: built-in packs provide starting points, and importers reduce the cost of moving from Espanso, AutoHotkey, CSV/TSV, or JSON.

The opportunity is not to make typing look futuristic. It is to remove a small piece of repetitive work without asking users to trade away privacy or control.

### Who are your competitors, and what do you understand about this idea that they don't?

The competitive set includes TextExpander, Espanso, AutoHotkey, AutoKey, and native operating-system shortcuts.

TextExpander established the category, but FlitKey takes a local-first, free, open-source path: no account, paid tier, or cloud dependency. Espanso is powerful and local-first, but its configuration-first workflow can be a barrier for people who want to manage snippets visually; FlitKey offers a GUI and imports Espanso YAML rather than forcing a migration decision. AutoHotkey is extremely flexible on Windows, but it is a scripting environment rather than a focused cross-platform snippet manager; FlitKey imports `.ahk` snippets and gives them a searchable UI. Native shortcuts are convenient, but they do not provide the same combination of packs, placeholders, imports, and a cross-platform library.

The important product insight is that “works on Linux” is not one capability. X11 and Wayland have meaningfully different security and input models. FlitKey communicates that distinction plainly: use typed triggers and global hotkeys on X11; use Quick Insert and clipboard paste on native Wayland. That honest fallback is more useful than claiming universal keyboard automation and then failing silently.

### What's your revenue and/or growth rate?

FlitKey is currently pre-revenue. It is free and MIT licensed, with no paid plan, trial, account, or usage-based service, so there is no software revenue to report at this stage.

The present focus is product distribution and learning: making the Windows and Linux installation paths reliable, reducing switching costs with imports, and validating which snippet packs and workflows earn repeat use. Growth figures will be reported once there is a consistent measurement method that respects the project’s no-telemetry promise.

### Anything else you would like investors to know?

FlitKey is deliberately privacy-preserving by architecture, not by marketing language. Snippets and settings remain local, and the product does not depend on a hosted account or cloud processing to provide its core value. That keeps the operating cost and trust surface small, but it also means growth cannot be measured by quietly collecting user behavior. Any future measurement or paid offering should preserve the local-first default and be explicit and opt-in.

The project has a clear wedge: people who want the speed of text expansion but do not want to rent their shortcut library from a subscription service. From there, the practical expansion path is distribution and workflow depth: stronger onboarding, more shareable packs, better migration tools, and continued platform support. The open-source model is an advantage here: users can inspect the product, carry their data, and contribute improvements without being locked into a proprietary format.

## Short launch posts

### X / Twitter

I made FlitKey: a free, open-source text expander for Windows and Linux.

Turn short triggers into full replies, prompts, commands, and templates. Everything stays offline — no account, cloud, or telemetry.

It includes Quick Insert, expansion packs, dynamic placeholders, and Espanso/AutoHotkey imports.  
https://flitkey.xyz/

### LinkedIn

Today I’m launching FlitKey, a free and open-source desktop text expander for Windows and Linux.

It helps turn the repeated text in your workday — replies, prompts, commands, templates, dates, and more — into fast, searchable shortcuts. Your snippets stay on your own machine: no account, no cloud service, and no telemetry.

FlitKey includes a visual snippet manager, Quick Insert search, dynamic placeholders, built-in packs, and imports from Espanso and AutoHotkey.  
https://flitkey.xyz/

## Launch checklist

- [ ] Set the Product Hunt website field to `https://flitkey.xyz/`.
- [ ] Use the logo and gallery sequence above; do not use the small “packs installed” confirmation image.
- [ ] Paste the maker comment immediately after launch and answer early comments from the maker account.
- [ ] Link the GitHub repository in the product links.
- [ ] Confirm platform wording accurately distinguishes X11 support from Wayland’s Quick Insert fallback.
