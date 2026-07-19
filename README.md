# TypeFlux

TypeFlux is a lightweight, open-source Linux and Windows desktop text expander designed to create reusable text snippets and insert them instantly using typed keywords, global hotkeys, or a searchable quick-insert picker.

Built with **Python** and **PyQt6**, TypeFlux operates completely locally and dynamically adjusts its runtime behavior based on whether you are running an X11 or Wayland desktop session.

---

## Quick Reference & Tech Specs

| Specification | Details |
| --- | --- |
| **Language** | Python 3.10+ |
| **GUI Framework** | PyQt6 |
| **Compatible Platforms** | Linux (X11/Wayland) and Windows 10/11 (64-bit) |
| **Supported Displays** | X11, Wayland, and native Windows keyboard hooks |
| **Dependencies** | `python3-pyqt6`, `xdotool`, `xinput`, `x11-xserver-utils` (for X11) |
| **Configuration Path** | `~/.config/typeflux/config.json` |
| **License** | [MIT License](LICENSE) |
| **Current Version** | `0.3.0` |

---

## Key Features

*   **Snippet Manager**: A clean PyQt6 interface to manage, preview, and toggle snippet triggers.
*   **Live Search Filter**: Real-time filtering in the main snippet manager to find snippets by label, type, keyword, or preview text.
*   **X11 Keyword Triggers**: Automatically detects typed keywords and expands them in place.
*   **X11 Global Hotkeys**: Triggers expansions via custom key combinations (e.g. `Ctrl+Alt+A`).
*   **Wayland Clipboard Fallback**: Copies snippets to the system clipboard and notifies the user if native keyboard simulation is restricted.
*   **System Tray Integration**: Access quick insert, pause/resume, or settings from a dedicated tray menu.
*   **Interactive Snippet Picker**: A searchable overlay window to select and insert snippets on demand.
*   **Dynamic Placeholders**: Expand variables like date, time, clipboard data, or specify cursor placement after expansion.

---

## Platform Support Matrix

TypeFlux automatically probes your current desktop session and selects the appropriate runtime backend.

| Feature / Session | X11 Desktop | Wayland Desktop | Technical Mechanism |
| --- | --- | --- | --- |
| **Typed Keyword Expansion** | Yes | No | Listens to root raw inputs via `xinput test-xi2` |
| **Global Hotkeys** | Yes | No | Simulates key sequences using `xdotool` |
| **Searchable Picker Insertion**| Yes | Clipboard Fallback | Pastes text or copies to clipboard via `QClipboard` |
| **System Tray controls** | Yes | Yes | PyQt6 QSystemTrayIcon |
| **Autostart at Login** | Yes | Yes | XDG Autostart `.desktop` entry |

---

## System Requirements & Installation

### Prerequisite Packages (Ubuntu/Debian)

TypeFlux requires Python 3.10 or newer and specific X11 utility tools for expansion triggers.

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

TypeFlux includes a native Windows backend for typed keyword expansion, global hotkeys, Unicode text insertion, system tray controls, and per-user startup. A self-contained 64-bit Windows 10/11 installer can be built with `python build_windows.py` on Windows or downloaded from the GitHub Actions artifact. See [WINDOWS.md](WINDOWS.md) for build instructions and Windows limitations.

## Installation & Running

### Method 1: Install via Debian Package (Recommended)

1. Build the Debian package:
   ```bash
   python3 build_deb.py
   ```
2. Install the generated package:
   ```bash
   sudo apt install ./dist/typeflux_0.3.0_all.deb
   ```
3. Run the application:
   ```bash
   typeflux
   ```

*The package installs the app files under `/opt/typeflux`, a binary launcher at `/usr/bin/typeflux`, a desktop entry at `/usr/share/applications/typeflux.desktop`, and icons.*

### Method 2: Run from Source

1. Clone and enter the directory:
   ```bash
   git clone https://github.com/swarajnandedkar/TypeFlow.git
   cd TypeFlow
   ```
2. Run the application entry point:
   ```bash
   python3 run.py
   ```
3. Start minimized to the system tray:
   ```bash
   python3 run.py --minimized
   ```
4. Create a local desktop launcher shortcut:
   ```bash
   python3 install.py
   ```

---

## Dynamic Placeholders Guide

TypeFlux renders dynamic placeholders at the time of expansion. Use the following tokens in your snippet expansion text:

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

### Does TypeFlux support Wayland?
Yes. While Wayland's security model blocks global key listening and text injection tools (like `xinput` and `xdotool`), TypeFlux detects Wayland sessions and defaults to a clipboard fallback. When you select a snippet in the picker, TypeFlux copies it to your clipboard and notifies you, allowing you to paste it anywhere.

### How does cursor positioning (`{{cursor}}`) work?
On X11, TypeFlux splits the snippet text at `{{cursor}}`, types the entire text, and then calculates the remaining characters after the cursor position. It then executes `xdotool key --repeat <count> Left` to move your cursor back to the designated position.

### How is TypeFlux different from other Linux text expanders like AutoKey or Espanso?
TypeFlux is designed to be highly lightweight and zero-dependency beyond PyQt6 and standard X11 utilities. Unlike AutoKey, it features a modern, clean PyQt6 user interface. Unlike Espanso, it does not require editing YAML files and provides a graphical settings menu, system tray integration, and automatic migration from legacy text expander configurations.

### Where are snippets stored and is it secure?
Snippets are stored locally as plain-text JSON in `~/.config/typeflux/config.json` (respecting `XDG_CONFIG_HOME`). TypeFlux runs entirely on your local machine and never transmits your snippets, typed text, or configurations to external servers.

---

## Technical Architecture

```text
.
├── assets/                  # SVG icons and graphics
├── text_expander/
│   ├── app.py               # Main application controller & tray interface
│   ├── config.py            # Local JSON storage & configuration migration
│   ├── models.py            # Snippet, settings, and capability models
│   ├── placeholders.py      # Dynamic placeholder parsing engine
│   ├── platform.py          # OS environment & desktop launcher helpers
│   ├── theme.py             # App styling guidelines
│   ├── gui/                 # PyQt6 window and dialog components
│   └── runtime/             # Platform runtime backends (X11 & Wayland)
├── tests/                   # Automated unit test suite
├── build_deb.py             # Debian package builder
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
