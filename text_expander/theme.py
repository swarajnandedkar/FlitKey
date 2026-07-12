from __future__ import annotations


def app_stylesheet() -> str:
    return """
    QWidget {
        background: #f5f1ea;
        color: #1f2933;
        font-size: 14px;
    }
    QMainWindow {
        background: #efe7db;
    }
    QLabel#eyebrow {
        color: #8a6f4d;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    QLabel#heroTitle {
        color: #102a43;
        font-size: 28px;
        font-weight: 700;
    }
    QLabel#heroSubtitle {
        color: #52606d;
        font-size: 14px;
    }
    QLabel#sectionTitle {
        color: #102a43;
        font-size: 16px;
        font-weight: 700;
    }
    QLabel#mutedText {
        color: #7b8794;
        font-size: 13px;
    }
    QLabel#metricValue {
        color: #102a43;
        font-size: 22px;
        font-weight: 700;
    }
    QLabel#metricCaption {
        color: #7b8794;
        font-size: 12px;
    }
    QFrame#surfaceCard {
        background: #fffdf8;
        border: 1px solid #e7ddcf;
        border-radius: 18px;
    }
    QFrame#accentCard {
        background: #102a43;
        border: 1px solid #102a43;
        border-radius: 22px;
    }
    QFrame#sidebarCard {
        background: #fffaf2;
        border: 1px solid #e7ddcf;
        border-radius: 18px;
    }
    QPushButton {
        background: #fffdf8;
        border: 1px solid #d9ccb8;
        border-radius: 12px;
        padding: 10px 16px;
        font-weight: 600;
    }
    QPushButton:hover {
        background: #f8f2e8;
        border-color: #c7b59c;
    }
    QPushButton#primaryButton {
        background: #e07a3f;
        color: #ffffff;
        border: none;
    }
    QPushButton#primaryButton:hover {
        background: #c9652f;
    }
    QPushButton#dangerButton {
        background: #fff5f5;
        color: #a61b1b;
        border: 1px solid #efc7c7;
    }
    QLineEdit, QPlainTextEdit, QComboBox, QListWidget {
        background: #fffdf8;
        border: 1px solid #d9ccb8;
        border-radius: 12px;
        padding: 10px 12px;
        selection-background-color: #e07a3f;
    }
    QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QListWidget:focus {
        border: 1px solid #e07a3f;
    }
    QTableWidget {
        background: #fffdf8;
        border: 1px solid #e7ddcf;
        border-radius: 16px;
        gridline-color: #efe6da;
        padding: 6px;
    }
    QHeaderView::section {
        background: #f7f1e7;
        color: #486581;
        border: none;
        padding: 12px 10px;
        font-weight: 700;
    }
    QTableWidget::item {
        padding: 10px;
        border-bottom: 1px solid #f1e9dd;
    }
    QTableWidget::item:selected {
        background: #fff0e3;
        color: #102a43;
    }
    QCheckBox {
        spacing: 10px;
        color: #334e68;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 6px;
        border: 1px solid #c7b59c;
        background: #fffdf8;
    }
    QCheckBox::indicator:checked {
        background: #e07a3f;
        border: 1px solid #e07a3f;
    }
    QDialog {
        background: #f8f3eb;
    }
    QScrollBar:vertical {
        background: transparent;
        width: 12px;
        margin: 4px;
    }
    QScrollBar::handle:vertical {
        background: #d5c3ab;
        border-radius: 6px;
        min-height: 28px;
    }
    """
