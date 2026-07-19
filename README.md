# FlitKey

FlitKey is a lightweight, open-source Linux and Windows desktop text expander designed to create reusable text snippets and insert them instantly using typed keywords, global hotkeys, or a searchable quick-insert picker.

Built with **Python** and **PyQt6**, FlitKey operates completely locally and dynamically adjusts its runtime behavior based on whether you are running Linux (X11/Wayland) or Windows.

---

## Quick Reference & Tech Specs

| Specification | Details |
| --- | --- |
| **Language** | Python 3.10+ |
| **GUI Framework** | PyQt6 |
| **Compatible Platforms** | Linux (X11/Wayland) and Windows 10/11 (64-bit) |
| **Supported Displays** | X11, Wayland, and native Windows keyboard hooks |
| **Dependencies** | `python3-pyqt6`, `xdotool`, `xinput`, `x11-xserver-utils` (for Linux X11) |
| **Configuration Path** | `~/.config/flitkey/config.json` (Linux) / `%APPDATA%\flitkey\config.json` (Windows) |
| **License** | [MIT License](LICENSE) |
| **Current Version** | `0.4.0` |


---

## Key Features

*   **Snippet Manager**: A clean PyQt6 interface to manage, preview, and toggle snippet triggers.
*   **Live Search Filter**: Real-time filtering in the main snippet manager to find snippets by label, type, keyword, or preview text.
*   **X11 & Windows Keyword Triggers**: Automatically detects typed keywords and expands them in place.
*   **Global Hotkeys**: Triggers expansions via custom key combinations (e.g. `Ctrl+Alt+A`).
*   **Wayland Clipboard Fallback**: Copies snippets to the system clipboard and notifies the user if native keyboard simulation is restricted.
*   **System Tray Integration**: Access quick insert, pause/resume, or settings from a dedicated tray menu.
*   **Interactive Snippet Picker**: A searchable overlay window to select and insert snippets on demand.
*   **Dynamic Placeholders**: Expand variables like date, time, clipboard data, or specify cursor placement after expansion.

---

## Interface & Screenshots

### Main Window & Snippet Manager
![FlitKey Main Window](assets/main_window.png)

### Snippet Editor
![FlitKey Snippet Editor](assets/snippet_editor.png)

---

## Platform Support Matrix

FlitKey automatically probes your current desktop session and selects the appropriate runtime backend.

| Feature / Session | X11 Desktop | Wayland Desktop | Windows (10/11) | Technical Mechanism |
| --- | --- | --- | --- | --- |
| **Typed Keyword Expansion** | Yes | No | Yes | `xinput test-xi2` (Linux) / `SetWindowsHookEx` (Windows) |
| **Global Hotkeys** | Yes | No | Yes | `xdotool` (Linux) / Windows Key Hooks |
| **Searchable Picker Insertion**| Yes | Clipboard Fallback | Yes | Pastes text or copies to clipboard via `QClipboard` / `SendInput` |
| **System Tray controls** | Yes | Yes | Yes | PyQt6 `QSystemTrayIcon` |
| **Autostart at Login** | Yes | Yes | Yes | XDG Autostart `.desktop` entry (Linux) / Registry key (Windows) |

---

## System Requirements & Installation

### Prerequisite Packages (Ubuntu/Debian)

FlitKey requires Python 3.10 or newer and specific X11 utility tools for expansion triggers.

```bash
sudo apt update
sudo apt install python3 python3-pyqt6 xdotool xinput x11-xserver-utils
```

For building the Debian package locally, you also need:
```bash
sudo apt install desktop-file-utils dpkg
```

---

### Windows Support

FlitKey includes a native Windows backend for typed keyword expansion, global hotkeys, Unicode text insertion, system tray controls, and per-user startup. A self-contained 64-bit Windows 10/11 installer can be built with `python build_windows.py` on Windows or downloaded from the GitHub Actions artifact. See [WINDOWS.md](WINDOWS.md) for detailed build instructions and Windows specific behavior.

### Security and Privacy

FlitKey is local-first and currently has no hosted account, telemetry, or central data service. Data handling, privacy policies, and security guidelines are documented in [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md).

---

## Installation & Running

### Method 1: Install via Debian Package (Recommended for Debian/Ubuntu)

1. Build the Debian package:
   ```bash
   python3 build_deb.py
   ```
2. Install the generated package:
   ```bash
   sudo apt install ./dist/flitkey_0.3.0_all.deb
   ```
3. Run the application:
   ```bash
   flitkey
   ```

*The package installs the app files under `/opt/flitkey`, a binary launcher at `/usr/bin/flitkey`, a desktop entry at `/usr/share/applications/flitkey.desktop`, and icons.*

### Method 2: Run from Source

1. Clone and enter the directory:
   ```bash
   git clone https://github.com/swarajnandedkar/FlitKey.git
   cd FlitKey
   ```
2. Install requirements (Windows):
   ```cmd
   pip install -r requirements-windows.txt
   ```
3. Run the application entry point:
   ```bash
   python3 run.py
   ```
4. Start minimized to the system tray:
   ```bash
   python3 run.py --minimized
   ```
5. Create a local desktop launcher shortcut:
   ```bash
   python3 install.py
   ```

---

## Dynamic Placeholders Guide

FlitKey renders dynamic placeholders at the time of expansion. Use the following tokens in your snippet expansion text:

| Token | Replacement Value | Example Output |
| --- | --- | --- |
| `{{date}}` | Current date (YYYY-MM-DD) | `2026-07-12` |
| `{{time}}` | Current time (HH:MM) | `14:30` |
| `{{datetime}}` | Current date and time | `2026-07-12 14:30` |
| `{{clipboard}}` | Injects current clipboard text | *Contents of system clipboard* |
| `{{cursor}}` | Positions the text cursor here after pasting | *Removes tag and moves cursor left* |

*Note: On Wayland, the `{{cursor}}` tag is stripped from the text before copying to the clipboard, and `{{clipboard}}` inserts the text currently held in your clipboard buffer.*

---

## Frequently Asked Questions (FAQ)

### Does FlitKey support Wayland?
Yes. While Wayland's security model blocks global key listening and text injection tools (like `xinput` and `xdotool`), FlitKey detects Wayland sessions and defaults to a clipboard fallback. When you select a snippet in the picker, FlitKey copies it to your clipboard and notifies you, allowing you to paste it anywhere.

### How does cursor positioning (`{{cursor}}`) work?
On X11, FlitKey splits the snippet text at `{{cursor}}`, types the entire text, and then calculates the remaining characters after the cursor position. It then executes `xdotool key --repeat <count> Left` to move your cursor back to the designated position.

### How do I import snippets from Espanso, AutoHotkey, or AutoText?
Click the **Import...** button in the main FlitKey window. FlitKey natively supports importing snippets from:
* **Espanso** (`.yml`, `.yaml`)
* **AutoHotkey** (`.ahk`)
* **AutoText / CSV / TSV** (`.csv`, `.tsv`, `.txt`)
* **FlitKey / JSON** (`.json`)

### How is FlitKey different from other Linux text expanders like AutoKey or Espanso?
FlitKey is designed to be highly lightweight and zero-dependency beyond PyQt6 and standard X11 utilities. Unlike AutoKey, it features a modern, clean PyQt6 user interface. Unlike Espanso, it does not require editing YAML files and provides a graphical settings menu, system tray integration, and automatic migration from legacy text expander configurations.

### Where are snippets stored and is it secure?
Snippets are stored locally as plain-text JSON in `~/.config/flitkey/config.json` on Linux and `%APPDATA%\flitkey\config.json` on Windows. FlitKey runs entirely on your local machine and never transmits your snippets, typed text, or configurations to external servers.

---

## Technical Architecture

```text
.
├── assets/                  # SVG icons, logo, and UI screenshots
├── text_expander/
│   ├── app.py               # Main application controller & tray interface
│   ├── config.py            # Local JSON storage & configuration migration
│   ├── importers.py         # Multi-format snippet importer (Espanso, AHK, CSV, JSON)
│   ├── models.py            # Snippet, settings, and capability models
│   ├── placeholders.py      # Dynamic placeholder parsing engine
│   ├── platform.py          # OS environment & desktop launcher helpers
│   ├── theme.py             # App styling guidelines
│   ├── gui/                 # PyQt6 window and dialog components
│   └── runtime/             # Platform runtime backends (X11, Wayland, & Windows)
├── tests/                   # Automated unit test suite
├── build_deb.py             # Debian package builder
├── build_windows.py         # Windows 64-bit installer builder
├── requirements-windows.txt # Windows dependencies
├── install.py               # Source local installer
└── run.py                   # App launch wrapper
```

### Running Tests
Execute the unit test suite:
```bash
python3 -m unittest discover -s tests
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

