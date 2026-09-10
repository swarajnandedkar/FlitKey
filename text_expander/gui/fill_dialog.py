from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from ..placeholders import Field


class FillDialog(QDialog):
    """Prompts for {{field:..}} / {{choice:..}} values before a snippet is inserted."""

    def __init__(self, title: str, fields: list[Field], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"Fill in: {title}")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self._inputs: dict[str, QLineEdit | QComboBox] = {}

        heading = QLabel(title)
        heading.setObjectName("windowTitle")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)
        for item in fields:
            if item.kind == "choice":
                combo = QComboBox()
                combo.addItems(item.options)
                self._inputs[item.name] = combo
                form.addRow(item.name, combo)
            else:
                edit = QLineEdit(item.default)
                self._inputs[item.name] = edit
                form.addRow(item.name, edit)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 14)
        card_layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Insert")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("primaryButton")
        for button in buttons.buttons():
            button.setIcon(QIcon())
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        layout.addWidget(heading)
        layout.addWidget(card)
        layout.addWidget(buttons)
        self.setLayout(layout)

        first = next(iter(self._inputs.values()), None)
        if first is not None:
            first.setFocus()
            if isinstance(first, QLineEdit):
                first.selectAll()

    def values(self) -> dict[str, str]:
        return {
            name: widget.currentText() if isinstance(widget, QComboBox) else widget.text()
            for name, widget in self._inputs.items()
        }
