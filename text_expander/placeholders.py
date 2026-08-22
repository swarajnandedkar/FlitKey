from __future__ import annotations

from datetime import datetime


def _clipboard_text() -> str:
    """Read the clipboard if a Qt app exists; empty string otherwise.

    Imported lazily so backends can render placeholders (dates, etc.) in
    tests or headless contexts without PyQt6 installed.
    """
    try:
        from PyQt6.QtGui import QGuiApplication
    except ImportError:
        return ""
    try:
        if QGuiApplication.instance() is None:
            return ""
        clipboard = QGuiApplication.clipboard()
        return clipboard.text() if clipboard else ""
    except Exception:
        return ""


def render_placeholders(text: str) -> str:
    now = datetime.now()
    replacements = {
        "{{date}}": now.strftime("%Y-%m-%d"),
        "{{time}}": now.strftime("%H:%M"),
        "{{datetime}}": now.strftime("%Y-%m-%d %H:%M"),
    }

    if "{{clipboard}}" in text:
        replacements["{{clipboard}}"] = _clipboard_text()

    rendered = text
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered
