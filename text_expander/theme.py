from __future__ import annotations

from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication

from .platform import app_root

# macOS-inspired neutral palette. Surfaces stay quiet; the brand red is used
# only for the primary action and focus rings so the window reads as calm.
WINDOW_BG = "#f2f2f4"
SURFACE = "#ffffff"
SURFACE_SUNKEN = "#fafafb"
BORDER = "#e2e2e6"
BORDER_STRONG = "#d3d3d9"
TEXT = "#1c1c1e"
TEXT_MUTED = "#6e6e76"
TEXT_FAINT = "#8e8e96"
ACCENT = "#e0242b"
ACCENT_HOVER = "#c41d24"
ACCENT_SOFT = "#fdeced"
SELECTION = "#ececed"
FOCUS = "#8e8e96"
DANGER = "#c0271f"

# Preferred UI faces per platform, closest-first. SF Pro on macOS, then the
# common Linux/Windows humanist sans faces that pair well with it.
_FONT_STACK = (
    "SF Pro Text",
    "Inter",
    "Inter Display",
    "Segoe UI Variable Text",
    "Segoe UI",
    "Ubuntu",
    "Cantarell",
    "Noto Sans",
    "DejaVu Sans",
)


def apply_theme(app: QApplication) -> None:
    """Apply the FlitKey look: consistent widget style, UI font, stylesheet."""
    app.setStyle("Fusion")
    app.setFont(ui_font())
    app.setStyleSheet(app_stylesheet())


def ui_font(point_size: int = 10) -> QFont:
    available = set(QFontDatabase.families())
    for family in _FONT_STACK:
        if family in available:
            font = QFont(family, point_size)
            break
    else:
        font = QFont()
        font.setPointSize(point_size)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    return font


def _icon_url(filename: str) -> str:
    """Stylesheet url() for a bundled icon, "none" if the asset is missing."""
    path = app_root() / "assets" / filename
    if not path.exists():
        return "none"
    return f'url("{path.as_posix()}")'


def app_stylesheet() -> str:
    checkmark = _icon_url("checkmark-white.png")
    chevron = _icon_url("chevron-down.png")
    return f"""
    QWidget {{
        background: transparent;
        color: {TEXT};
        font-size: 13px;
    }}
    QMainWindow, QDialog {{
        background: {WINDOW_BG};
    }}

    /* ---- Typography ---- */
    QLabel#windowTitle {{
        color: {TEXT};
        font-size: 20px;
        font-weight: 600;
    }}
    QLabel#windowSubtitle {{
        color: {TEXT_MUTED};
        font-size: 13px;
    }}
    QLabel#sectionTitle {{
        color: {TEXT_FAINT};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.6px;
        text-transform: uppercase;
    }}
    QLabel#mutedText {{
        color: {TEXT_MUTED};
    }}
    QLabel#statusText {{
        color: {TEXT};
        font-weight: 500;
    }}

    /* ---- Cards ---- */
    QFrame#card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 12px;
    }}
    QFrame#separator {{
        background: {BORDER};
        border: none;
        max-height: 1px;
    }}

    /* ---- Buttons ---- */
    QPushButton {{
        background: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER_STRONG};
        border-radius: 7px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 500;
        min-height: 20px;
    }}
    QPushButton:hover {{
        background: {SURFACE_SUNKEN};
        border-color: {TEXT_FAINT};
    }}
    QPushButton:pressed {{
        background: {SELECTION};
    }}
    QPushButton:disabled {{
        color: {TEXT_FAINT};
        background: {SURFACE_SUNKEN};
        border-color: {BORDER};
    }}
    QPushButton#primaryButton {{
        background: {ACCENT};
        color: #ffffff;
        border: 1px solid {ACCENT};
    }}
    QPushButton#primaryButton:hover {{
        background: {ACCENT_HOVER};
        border-color: {ACCENT_HOVER};
    }}
    QPushButton#primaryButton:pressed {{
        background: {ACCENT_HOVER};
    }}
    QPushButton#dangerButton {{
        color: {DANGER};
    }}
    QPushButton#dangerButton:disabled {{
        color: {TEXT_FAINT};
    }}
    QPushButton#dangerButton:hover {{
        background: {ACCENT_SOFT};
        border-color: {DANGER};
    }}
    QPushButton#linkButton {{
        background: transparent;
        border: none;
        color: {ACCENT};
        padding: 6px 8px;
    }}
    QPushButton#linkButton:hover {{
        color: {ACCENT_HOVER};
        background: transparent;
    }}

    /* ---- Inputs ---- */
    QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox {{
        background: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER_STRONG};
        border-radius: 8px;
        padding: 6px 10px;
        selection-background-color: {ACCENT};
        selection-color: #ffffff;
    }}
    QLineEdit#searchField {{
        background: {SURFACE};
        border-radius: 9px;
        padding: 7px 12px;
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
    QComboBox:focus, QSpinBox:focus {{
        border-color: {FOCUS};
    }}
    QLineEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled {{
        background: {SURFACE_SUNKEN};
        color: {TEXT_FAINT};
    }}
    QComboBox::drop-down {{
        background: transparent;
        border: none;
        width: 26px;
        subcontrol-origin: padding;
        subcontrol-position: center right;
    }}
    QComboBox::down-arrow {{
        image: {chevron};
        width: 11px;
        height: 11px;
    }}
    QComboBox QAbstractItemView {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 4px;
        selection-background-color: {SELECTION};
        selection-color: {TEXT};
        outline: none;
    }}

    /* ---- Lists & tables ---- */
    QTableWidget, QTableView {{
        background: {SURFACE};
        alternate-background-color: {SURFACE_SUNKEN};
        border: none;
        gridline-color: transparent;
        outline: none;
    }}
    QTableWidget::item, QTableView::item {{
        padding: 7px 8px;
        border: none;
    }}
    QTableWidget::item:selected, QTableView::item:selected {{
        background: {SELECTION};
        color: {TEXT};
    }}
    QHeaderView {{
        background: transparent;
    }}
    QHeaderView::section {{
        background: transparent;
        color: {TEXT_MUTED};
        border: none;
        border-bottom: 1px solid {BORDER};
        padding: 8px;
        font-size: 12px;
        font-weight: 600;
    }}
    QTableCornerButton::section {{
        background: transparent;
        border: none;
        border-bottom: 1px solid {BORDER};
    }}
    QListWidget {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 4px;
        outline: none;
    }}
    QListWidget::item {{
        border-radius: 7px;
        padding: 7px 8px;
        margin: 1px 2px;
    }}
    QListWidget::item:selected {{
        background: {SELECTION};
        color: {TEXT};
    }}
    QListWidget::item:hover {{
        background: {SURFACE_SUNKEN};
    }}
    QListWidget::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 5px;
        border: 1px solid {BORDER_STRONG};
        background: {SURFACE};
        margin-right: 8px;
    }}
    QListWidget::indicator:checked {{
        background: {ACCENT};
        border-color: {ACCENT};
        image: {checkmark};
    }}

    /* ---- Checkboxes ---- */
    QCheckBox {{
        spacing: 9px;
        color: {TEXT};
        padding: 3px 0;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 5px;
        border: 1px solid {BORDER_STRONG};
        background: {SURFACE};
    }}
    QCheckBox::indicator:hover {{
        border-color: {TEXT_FAINT};
    }}
    QCheckBox::indicator:checked {{
        background: {ACCENT};
        border-color: {ACCENT};
        image: {checkmark};
    }}

    /* ---- Scrollbars ---- */
    QScrollBar:vertical {{
        background: transparent;
        width: 11px;
        margin: 4px 2px;
    }}
    QScrollBar::handle:vertical {{
        background: #c6c6cc;
        border-radius: 4px;
        min-height: 32px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #adadb4;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 11px;
        margin: 2px 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: #c6c6cc;
        border-radius: 4px;
        min-width: 32px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        width: 0;
        height: 0;
    }}
    QScrollBar::add-page, QScrollBar::sub-page {{
        background: transparent;
    }}

    /* ---- Misc ---- */
    QToolTip {{
        background: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER_STRONG};
        border-radius: 6px;
        padding: 5px 8px;
    }}
    QMenu {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 5px;
    }}
    QMenu::item {{
        padding: 6px 22px 6px 14px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background: {SELECTION};
    }}
    QMenu::separator {{
        height: 1px;
        background: {BORDER};
        margin: 5px 8px;
    }}
    """
