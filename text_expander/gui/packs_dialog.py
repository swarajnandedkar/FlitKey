from __future__ import annotations

from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..packs import PackMetadata, list_available_packs


class PacksDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("FlitKey Expansion Packs")
        self.resize(640, 520)

        self.available_packs: list[PackMetadata] = list_available_packs()
        self.checkbox_items: dict[str, QListWidgetItem] = {}

        heading = QLabel("Expansion Packs")
        heading.setObjectName("windowTitle")

        intro_label = QLabel(
            "Add pre-built snippets to your library. "
            "Packs are merged in without overwriting your existing triggers."
        )
        intro_label.setObjectName("mutedText")
        intro_label.setWordWrap(True)

        self.pack_list_widget = QListWidget()
        self.pack_list_widget.setSpacing(2)
        self.pack_list_widget.setWordWrap(True)
        self.pack_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        for pack in self.available_packs:
            item_text = f"{pack.name}  ·  {pack.snippet_count} snippets\n{pack.description}"
            item = QListWidgetItem(item_text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, pack)
            self.pack_list_widget.addItem(item)

        select_all_btn = QPushButton("Select All")
        deselect_all_btn = QPushButton("Deselect All")
        select_all_btn.clicked.connect(self._select_all)
        deselect_all_btn.clicked.connect(self._deselect_all)

        btn_row = QHBoxLayout()
        btn_row.addWidget(select_all_btn)
        btn_row.addWidget(deselect_all_btn)
        btn_row.addStretch(1)

        self.filter_os_checkbox = QCheckBox("Filter snippets incompatible with current operating system")
        self.filter_os_checkbox.setChecked(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Load Selected Packs")
        ok_button.setObjectName("primaryButton")
        for button in buttons.buttons():
            button.setIcon(QIcon())
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        header = QVBoxLayout()
        header.setSpacing(4)
        header.addWidget(heading)
        header.addWidget(intro_label)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        layout.addLayout(header)
        layout.addLayout(btn_row)
        layout.addWidget(self.pack_list_widget, 1)
        layout.addWidget(self.filter_os_checkbox)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _select_all(self):
        for i in range(self.pack_list_widget.count()):
            self.pack_list_widget.item(i).setCheckState(Qt.CheckState.Checked)

    def _deselect_all(self):
        for i in range(self.pack_list_widget.count()):
            self.pack_list_widget.item(i).setCheckState(Qt.CheckState.Unchecked)

    def get_selected_packs(self) -> tuple[list[PackMetadata], bool]:
        selected: list[PackMetadata] = []
        for i in range(self.pack_list_widget.count()):
            item = self.pack_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                pack_data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(pack_data, PackMetadata):
                    selected.append(pack_data)
        return selected, self.filter_os_checkbox.isChecked()

    def _accept(self):
        selected, _ = self.get_selected_packs()
        if not selected:
            QMessageBox.information(self, "Expansion Packs", "Please select at least one expansion pack to load.")
            return
        self.accept()
