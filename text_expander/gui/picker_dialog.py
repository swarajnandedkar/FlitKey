from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..branding import PICKER_TITLE
from ..models import Snippet


class SnippetPickerDialog(QDialog):
    def __init__(self, snippets: list[Snippet], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(PICKER_TITLE)
        self.resize(460, 380)
        self._snippets = [snippet for snippet in snippets if snippet.enabled]
        self.selected_snippet: Snippet | None = None

        self.search = QLineEdit()
        self.search.setObjectName("searchField")
        self.search.setPlaceholderText("Search snippets")
        self.search.setClearButtonEnabled(True)
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)

        hint = QLabel("Press Enter to insert · Esc to close")
        hint.setObjectName("mutedText")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)
        layout.addWidget(self.search)
        layout.addWidget(self.list_widget, 1)
        layout.addWidget(hint)
        self.setLayout(layout)

        self.search.textChanged.connect(self._populate)
        self.list_widget.itemActivated.connect(self._choose_item)
        self._populate("")
        self.search.setFocus()

    def _populate(self, query: str) -> None:
        self.list_widget.clear()
        lowered = query.strip().lower()
        for snippet in self._snippets:
            haystack = f"{snippet.label} {snippet.trigger_value()} {snippet.expansion_text}".lower()
            if lowered and lowered not in haystack:
                continue
            item = QListWidgetItem(f"{snippet.label} [{snippet.trigger_value()}]")
            item.setData(Qt.ItemDataRole.UserRole, snippet.id)
            self.list_widget.addItem(item)
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def _choose_item(self, item: QListWidgetItem) -> None:
        snippet_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_snippet = next((snippet for snippet in self._snippets if snippet.id == snippet_id), None)
        self.accept()
