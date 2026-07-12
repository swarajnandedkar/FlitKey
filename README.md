# TypeFlow

TypeFlow is a Linux desktop text expander for creating reusable snippets and inserting them with typed keywords, hotkeys, or a searchable quick-insert picker.

It is built with Python and PyQt6, stores data locally as JSON, integrates with the system tray, and adapts its runtime behavior for X11 and Wayland sessions.

## Features

- Snippet manager with labels, trigger types, enabled state, and expansion preview
- Keyword snippets for typed trigger expansion on supported X11 desktops
- Hotkey snippets on supported X11 desktops
- Searchable quick-insert picker from the app window or tray menu
- System tray controls for opening the app, quick insert, pause/resume, and quit
- Launch-at-login support through XDG autostart desktop entries
- Optional start-minimized behavior
- Case-sensitive or case-insensitive keyword matching
- Placeholder rendering for `{{date}}`, `{{time}}`, and `{{datetime}}`
- Local JSON config with automatic migration from the legacy `linux-text-expander` config path

## Platform Support

TypeFlow chooses its runtime backend from the current Linux desktop session.

| Session | Typed keyword expansion | Global hotkeys | Quick insert | Notes |
| --- | --- | --- | --- | --- |
| X11 | Yes | Yes | Yes | Requires `xinput`, `xmodmap`, and `xdotool` |
| Wayland | No | No | Clipboard fallback | Universal text injection is intentionally not implemented for Wayland in this backend |

On Wayland, the app still opens, manages snippets, shows tray/status information, and supports quick insert by copying the selected snippet text to the clipboard.

## Requirements

- Linux desktop environment
- Python 3.10 or newer
- PyQt6
- For full X11 expansion support: `xdotool`, `xinput`, and `x11-xserver-utils` for `xmodmap`

On Debian/Ubuntu-based systems:

```bash
sudo apt update
sudo apt install python3 python3-pyqt6 xdotool xinput x11-xserver-utils
```

For building the Debian package, also install:

```bash
sudo apt install desktop-file-utils dpkg
```

## Run From Source

Clone the repository and start the app:

```bash
git clone <repository-url>
cd typeflow
python3 run.py
```

Start minimized, respecting the in-app "Start minimized to tray" setting:

```bash
python3 run.py --minimized
```

Install or refresh the local desktop launcher:

```bash
python3 install.py
```

This writes a desktop entry to:

```text
~/.local/share/applications/typeflow.desktop
```

## Install From Debian Package

Build the package:

```bash
python3 build_deb.py
```

Install the generated package:

```bash
sudo apt install ./dist/typeflow_0.2.0_all.deb
```

The package installs:

- App files under `/opt/typeflow`
- Launcher at `/usr/bin/typeflow`
- Desktop entry at `/usr/share/applications/typeflow.desktop`
- Icon at `/usr/share/pixmaps/typeflow.svg`

Run the installed app:

```bash
typeflow
```

## Usage

1. Open TypeFlow.
2. Click `Add` to create a snippet.
3. Choose `keyword` for typed expansion on X11, or `hotkey` for a modifier combo on X11.
4. Enter the expansion text.
5. Use the tray menu or `Snippet Picker` button for searchable quick insert.

Supported placeholders inside expansion text:

| Placeholder | Example output |
| --- | --- |
| `{{date}}` | `2026-07-12` |
| `{{time}}` | `14:30` |
| `{{datetime}}` | `2026-07-12 14:30` |

## Data Storage

TypeFlow stores snippets and settings locally:

```text
~/.config/typeflow/config.json
```

If `XDG_CONFIG_HOME` is set, the config path becomes:

```text
$XDG_CONFIG_HOME/typeflow/config.json
```

On first launch, TypeFlow migrates existing data from:

```text
~/.config/linux-text-expander/config.json
```

Snippet text is passed to external tools as arguments, not shell commands.

## Development

Project layout:

```text
.
|-- assets/                  # SVG icons
|-- text_expander/
|   |-- app.py               # Application controller and tray integration
|   |-- config.py            # JSON persistence and legacy migration
|   |-- gui/                 # PyQt6 windows and dialogs
|   |-- runtime/             # X11 and Wayland runtime backends
|   |-- models.py            # Snippet, settings, and capability models
|   |-- placeholders.py      # Date/time placeholder rendering
|   `-- platform.py          # Session detection and desktop entry helpers
|-- tests/                   # Unit tests
|-- build_deb.py             # Debian package builder
|-- install.py               # Local launcher installer
`-- run.py                   # Source entry point
```

Run the test suite:

```bash
python3 -m unittest discover -s tests
```

Run a specific test file:

```bash
python3 -m unittest tests/test_x11_backend_security.py
```

## Packaging Notes

`build_deb.py` creates a self-contained Debian package tree in `dist/pkgroot` and writes the final artifact to:

```text
dist/typeflow_0.2.0_all.deb
```

The generated package declares these runtime dependencies:

```text
python3, python3-pyqt6, xdotool, xinput, x11-xserver-utils
```

## Limitations

- Wayland sessions do not support universal typed-trigger expansion or global hotkeys in the current backend.
- X11 expansion depends on external desktop utilities being installed and available on `PATH`.
- Hotkey capture is implemented by the X11 backend and is intended for explicit modifier combinations such as `Ctrl+Alt+A`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
