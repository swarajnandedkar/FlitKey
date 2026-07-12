from __future__ import annotations

from datetime import datetime


def render_placeholders(text: str) -> str:
    now = datetime.now()
    replacements = {
        "{{date}}": now.strftime("%Y-%m-%d"),
        "{{time}}": now.strftime("%H:%M"),
        "{{datetime}}": now.strftime("%Y-%m-%d %H:%M"),
    }
    rendered = text
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered
