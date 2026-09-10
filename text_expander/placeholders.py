from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

_TOKEN_RE = re.compile(r"\{\{(\w+)(?::([^{}]*))?\}\}")
_OFFSET_RE = re.compile(r"^([+-]\d+)([dwhm])\s*")
_OFFSET_UNITS = {"d": "days", "w": "weeks", "h": "hours", "m": "minutes"}
_DEFAULT_FORMATS = {"date": "%Y-%m-%d", "time": "%H:%M", "datetime": "%Y-%m-%d %H:%M"}


@dataclass
class Field:
    name: str
    kind: str = "field"  # "field" (free text) or "choice"
    default: str = ""
    options: list[str] = field(default_factory=list)


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


def _parse_field(kind: str, arg: str) -> Field:
    name, _, rest = arg.partition("=")
    if kind == "choice":
        if not rest:  # {{choice:A|B}} — options without a label
            name, rest = "Choice", name
        options = [option.strip() for option in rest.split("|") if option.strip()]
        return Field(name.strip(), "choice", options[0] if options else "", options)
    return Field(name.strip(), "field", rest)


def collect_fields(text: str) -> list[Field]:
    """Return the user-fillable fields in text, deduplicated by name, in order of appearance."""
    fields: dict[str, Field] = {}
    for kind, arg in _TOKEN_RE.findall(text):
        if kind in ("field", "choice") and arg:
            parsed = _parse_field(kind, arg)
            fields.setdefault(parsed.name, parsed)
    return list(fields.values())


def _render_datetime(kind: str, arg: str, now: datetime) -> str:
    fmt = _DEFAULT_FORMATS[kind]
    match = _OFFSET_RE.match(arg)
    if match:
        amount, unit = int(match.group(1)), match.group(2)
        now = now + timedelta(**{_OFFSET_UNITS[unit]: amount})
        arg = arg[match.end():]
    return now.strftime(arg.strip() or fmt)


def render_placeholders(text: str, values: dict[str, str] | None = None) -> str:
    """Expand {{date}}, {{time}}, {{datetime}}, {{clipboard}}, {{field:..}} and {{choice:..}}.

    Date tokens accept an offset and/or strftime format: {{date:+7d}}, {{date:%d %b}},
    {{date:-1w %A}}. Unknown tokens (including {{cursor}}) are left untouched.
    """
    now = datetime.now()
    values = values or {}
    clipboard: str | None = None

    def replace(match: re.Match) -> str:
        nonlocal clipboard
        kind, arg = match.group(1), match.group(2) or ""
        if kind in _DEFAULT_FORMATS:
            return _render_datetime(kind, arg, now)
        if kind == "clipboard":
            if clipboard is None:
                clipboard = _clipboard_text()
            return clipboard
        if kind in ("field", "choice") and arg:
            parsed = _parse_field(kind, arg)
            return values.get(parsed.name, parsed.default)
        return match.group(0)

    return _TOKEN_RE.sub(replace, text)
