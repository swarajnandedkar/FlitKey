from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models import Snippet


class SnippetDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, snippet: Snippet | None = None):
        super().__init__(parent)
        self.setWindowTitle("New Snippet" if snippet is None else "Edit Snippet")
        self.resize(560, 440)

        heading = QLabel(self.windowTitle())
        heading.setObjectName("windowTitle")

        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("e.g. Meeting follow-up")
        self.trigger_type_combo = QComboBox()
        self.trigger_type_combo.addItems(["keyword", "hotkey"])
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("e.g. /follow")
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setPlaceholderText("e.g. Ctrl+Alt+F")
        self.expansion_edit = QPlainTextEdit()
        self.expansion_edit.setPlaceholderText("The text that gets inserted…")
        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(True)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)
        form.addRow("Label", self.label_edit)
        form.addRow("Trigger type", self.trigger_type_combo)
        form.addRow("Keyword", self.keyword_edit)
        form.addRow("Hotkey", self.hotkey_edit)
        form.addRow("Expansion", self.expansion_edit)
        form.addRow("", self.enabled_checkbox)

        hint = QLabel("Placeholders: {{date}} · {{time}} · {{datetime}}")
        hint.setObjectName("mutedText")

        form_card = QFrame()
        form_card.setObjectName("card")
        card_layout = QVBoxLayout(form_card)
        card_layout.setContentsMargins(16, 16, 16, 14)
        card_layout.setSpacing(12)
        card_layout.addLayout(form)
        card_layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Save Snippet")
        ok_button.setObjectName("primaryButton")
        for button in buttons.buttons():
            button.setIcon(QIcon())
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        layout.addWidget(heading)
        layout.addWidget(form_card, 1)
        layout.addWidget(buttons)
        self.setLayout(layout)

        self.trigger_type_combo.currentTextChanged.connect(self._refresh_fields)
        self._snippet_id = snippet.id if snippet else None

        if snippet:
            self.label_edit.setText(snippet.label)
            self.trigger_type_combo.setCurrentText(snippet.trigger_type)
            self.keyword_edit.setText(snippet.keyword)
            self.hotkey_edit.setText(snippet.hotkey)
            self.expansion_edit.setPlainText(snippet.expansion_text)
            self.enabled_checkbox.setChecked(snippet.enabled)
        self._refresh_fields()

    def _refresh_fields(self) -> None:
        trigger_type = self.trigger_type_combo.currentText()
        self.keyword_edit.setEnabled(trigger_type == "keyword")
        self.hotkey_edit.setEnabled(trigger_type == "hotkey")

    def _accept(self) -> None:
        snippet = self.snippet()
        if not snippet.label:
            QMessageBox.warning(self, "Validation", "Label is required.")
            return
        if not snippet.expansion_text:
            QMessageBox.warning(self, "Validation", "Expansion text is required.")
            return
        if snippet.trigger_type == "keyword" and not snippet.keyword:
            QMessageBox.warning(self, "Validation", "Keyword is required for keyword snippets.")
            return
        if snippet.trigger_type == "hotkey" and not snippet.hotkey:
            QMessageBox.warning(self, "Validation", "Hotkey is required for hotkey snippets.")
            return
        self.accept()

    def snippet(self) -> Snippet:
        return Snippet(
            id=self._snippet_id or Snippet("", "").id,
            label=self.label_edit.text().strip(),
            trigger_type=self.trigger_type_combo.currentText(),
            keyword=self.keyword_edit.text().strip(),
            hotkey=self.hotkey_edit.text().strip(),
            expansion_text=self.expansion_edit.toPlainText(),
            enabled=self.enabled_checkbox.isChecked(),
        )
