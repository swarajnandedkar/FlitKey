# Chrome Web Store Publication Guide & Metadata: FlitKey Extension

## 1. Extension Basic Information

- **Extension Name**: FlitKey - Text Expander & Snippet Manager
- **Short Description**: Lightweight, powerful text expander. Expand custom keywords, dynamic placeholders, and snippets instantly on any web page.
- **Detailed Description**:
  FlitKey brings instant text expansion and snippet management directly into your Chrome browser. Automate repetitive typing tasks, insert dynamic dates, timestamps, or clipboard contents, and boost your productivity on any website.

  ### Key Features:
  - **Typed Keyword Expansion**: Automatically detects typed keywords (e.g., `!date`, `!ty`, `!meeting`) and replaces them instantly with your expanded text.
  - **Dynamic Placeholders**: Insert dynamic variables such as `{{date}}`, `{{time}}`, `{{datetime}}`, `{{clipboard}}`, and position your cursor automatically with `{{cursor}}`.
  - **Quick Insert Popup & Picker**: Access your full snippet library via the extension popup (`Ctrl+Shift+K`) to insert snippets with a single click.
  - **Context Menu Integration**: Right-click on any input field or text area to insert your saved snippets.
  - **Multi-Format Importer**: Easily import snippets from Espanso (`.yml`), AutoHotkey (`.ahk`), CSV/TSV, or FlitKey JSON.
  - **100% Local & Private**: All your snippets and settings are stored locally in your browser storage. No data is sent to external servers.

- **Category**: Productivity
- **Language**: English

---

## 2. Permissions Justifications (Required for Review)

| Permission | Purpose / Justification |
| --- | --- |
| `storage` | Required to save user snippets, custom keywords, and settings locally using `chrome.storage.local`. |
| `activeTab` | Required to insert snippet text into the currently active tab when selected from popup or quick insert picker. |
| `scripting` | Required to execute text replacement logic on web elements. |
| `contextMenus` | Required to add the "FlitKey Snippets" menu items when right-clicking on editable web elements. |
| `clipboardRead` | Required to render the `{{clipboard}}` dynamic placeholder tag in snippet expansions. |
| `host_permissions` (`<all_urls>`) | Required to enable real-time keyword detection and auto-expansion across web input fields and text areas on all websites. |

---

## 3. Privacy Policy & Data Handling

- **Single Purpose**: FlitKey's single purpose is to expand text snippets and manage user shortcuts across web pages.
- **Data Collection**: FlitKey does **NOT** collect, transmit, or sell any personal data, user credentials, browsing history, or snippet contents.
- **Storage**: All snippet data is stored strictly on the user's local machine via Chrome's local storage API (`chrome.storage.local`).
- **Remote Code**: FlitKey contains **NO** remote code or external scripts, adhering strictly to Chrome Web Store Manifest V3 guidelines.

---

## 4. Pre-Publish Checklist

- [x] Manifest V3 compliance verified
- [x] Icons generated and verified (`icon-16.png`, `icon-48.png`, `icon-128.png`)
- [x] No `eval()` or inline scripts used
- [x] Plain-text permissions justifications provided
- [x] Multi-format importer tested
- [x] Popup UI & Options page tested for responsive behavior and dark/light themes
