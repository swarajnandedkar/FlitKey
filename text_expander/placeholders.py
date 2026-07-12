from __future__ import annotations

from datetime import datetime
from PyQt6.QtGui import QGuiApplication


def render_placeholders(text: str) -> str:
    now = datetime.now()
    replacements = {
        "{{date}}": now.strftime("%Y-%m-%d"),
        "{{time}}": now.strftime("%H:%M"),
        "{{datetime}}": now.strftime("%Y-%m-%d %H:%M"),
    }

    if "{{clipboard}}" in text:
        clipboard_text = ""
        if QGuiApplication.instance() is not None:
            clipboard = QGuiApplication.clipboard()
            if clipboard:
                clipboard_text = clipboard.text()
        replacements["{{clipboard}}"] = clipboard_text

    rendered = text
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered
