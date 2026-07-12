from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..branding import APP_NAME
from ..models import CapabilityReport, Settings, Snippet


class MainWindow(QMainWindow):
    add_requested = pyqtSignal()
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    toggle_requested = pyqtSignal(str)
    pause_toggled = pyqtSignal(bool)
    autostart_toggled = pyqtSignal(bool)
    picker_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(900, 560)

        self.status_label = QLabel()
        self.capabilities_label = QLabel()
        self.capabilities_label.setWordWrap(True)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search snippets (by label, trigger, or preview)...")
        self.search_input.textChanged.connect(self._filter_snippets)

        self.snippet_table = QTableWidget(0, 5)
        self.snippet_table.setHorizontalHeaderLabels(["Label", "Type", "Trigger", "Enabled", "Preview"])
        self.snippet_table.horizontalHeader().setStretchLastSection(True)
        self.snippet_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.snippet_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        add_button = QPushButton("Add")
        edit_button = QPushButton("Edit")
        delete_button = QPushButton("Delete")
        toggle_button = QPushButton("Enable / Disable")
        picker_button = QPushButton("Snippet Picker")

        add_button.clicked.connect(self.add_requested.emit)
        edit_button.clicked.connect(self._emit_edit)
        delete_button.clicked.connect(self._emit_delete)
        toggle_button.clicked.connect(self._emit_toggle)
        picker_button.clicked.connect(self.picker_requested.emit)

        buttons = QHBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(edit_button)
        buttons.addWidget(delete_button)
        buttons.addWidget(toggle_button)
        buttons.addStretch(1)
        buttons.addWidget(picker_button)

        self.pause_checkbox = QCheckBox("Pause expansion")
        self.autostart_checkbox = QCheckBox("Launch at login")
        self.start_minimized_checkbox = QCheckBox("Start minimized to tray")
        self.case_sensitive_checkbox = QCheckBox("Case sensitive keyword matching")

        self.pause_checkbox.toggled.connect(self.pause_toggled.emit)
        self.autostart_checkbox.toggled.connect(self.autostart_toggled.emit)

        settings_box = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(self.pause_checkbox)
        settings_layout.addWidget(self.autostart_checkbox)
        settings_layout.addWidget(self.start_minimized_checkbox)
        settings_layout.addWidget(self.case_sensitive_checkbox)
        settings_box.setLayout(settings_layout)

        status_box = QGroupBox("Runtime Status")
        status_layout = QVBoxLayout()
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.capabilities_label)
        status_box.setLayout(status_layout)

        top_layout = QGridLayout()
        top_layout.addWidget(settings_box, 0, 0)
        top_layout.addWidget(status_box, 0, 1)

        central = QWidget()
        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.search_input)
        layout.addWidget(self.snippet_table)
        layout.addLayout(buttons)
        central.setLayout(layout)
        self.setCentralWidget(central)

    def current_snippet_id(self) -> str | None:
        selected = self.snippet_table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        item = self.snippet_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _emit_edit(self) -> None:
        snippet_id = self.current_snippet_id()
        if snippet_id:
            self.edit_requested.emit(snippet_id)

    def _emit_delete(self) -> None:
        snippet_id = self.current_snippet_id()
        if snippet_id:
            self.delete_requested.emit(snippet_id)

    def _emit_toggle(self) -> None:
        snippet_id = self.current_snippet_id()
        if snippet_id:
            self.toggle_requested.emit(snippet_id)

    def update_snippets(self, snippets: list[Snippet]) -> None:
        self.snippet_table.setRowCount(len(snippets))
        for row, snippet in enumerate(snippets):
            label_item = QTableWidgetItem(snippet.label)
            label_item.setData(Qt.ItemDataRole.UserRole, snippet.id)
            self.snippet_table.setItem(row, 0, label_item)
            self.snippet_table.setItem(row, 1, QTableWidgetItem(snippet.trigger_type))
            self.snippet_table.setItem(row, 2, QTableWidgetItem(snippet.trigger_value()))
            self.snippet_table.setItem(row, 3, QTableWidgetItem("Yes" if snippet.enabled else "No"))
            preview = snippet.expansion_text.replace("\n", " ")[:80]
            self.snippet_table.setItem(row, 4, QTableWidgetItem(preview))
        self.snippet_table.resizeColumnsToContents()
        self._filter_snippets()

    def _filter_snippets(self) -> None:
        query = self.search_input.text().strip().lower()
        for row in range(self.snippet_table.rowCount()):
            if not query:
                self.snippet_table.setRowHidden(row, False)
                continue
            
            # Read text from table items to filter
            label = self.snippet_table.item(row, 0).text().lower() if self.snippet_table.item(row, 0) else ""
            trigger_type = self.snippet_table.item(row, 1).text().lower() if self.snippet_table.item(row, 1) else ""
            trigger_val = self.snippet_table.item(row, 2).text().lower() if self.snippet_table.item(row, 2) else ""
            preview = self.snippet_table.item(row, 4).text().lower() if self.snippet_table.item(row, 4) else ""
            
            match = (query in label) or (query in trigger_type) or (query in trigger_val) or (query in preview)
            self.snippet_table.setRowHidden(row, not match)

    def update_settings(self, settings: Settings) -> None:
        self.pause_checkbox.blockSignals(True)
        self.autostart_checkbox.blockSignals(True)
        self.start_minimized_checkbox.blockSignals(True)
        self.case_sensitive_checkbox.blockSignals(True)
        self.pause_checkbox.setChecked(settings.paused)
        self.autostart_checkbox.setChecked(settings.autostart)
        self.start_minimized_checkbox.setChecked(settings.start_minimized)
        self.case_sensitive_checkbox.setChecked(settings.case_sensitive)
        self.pause_checkbox.blockSignals(False)
        self.autostart_checkbox.blockSignals(False)
        self.start_minimized_checkbox.blockSignals(False)
        self.case_sensitive_checkbox.blockSignals(False)

    def update_capabilities(self, report: CapabilityReport) -> None:
        self.status_label.setText(report.status_message)
        self.capabilities_label.setText(
            "\n".join(
                [
                    f"Session: {report.session_type}",
                    f"Backend: {report.backend_name}",
                    f"Typed expansion: {'Yes' if report.typed_expansion_supported else 'No'}",
                    f"Global hotkeys: {'Yes' if report.global_hotkeys_supported else 'No'}",
                    f"Tray: {'Yes' if report.tray_supported else 'No'}",
                    f"Autostart: {'Yes' if report.autostart_supported else 'No'}",
                ]
            )
        )

    def confirm_delete(self, snippet: Snippet) -> bool:
        answer = QMessageBox.question(
            self,
            "Delete Snippet",
            f"Delete snippet '{snippet.label}'?",
        )
        return answer == QMessageBox.StandardButton.Yes

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()
