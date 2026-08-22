from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..branding import APP_NAME, APP_TAGLINE
from ..models import CapabilityReport, Settings, Snippet


def _card() -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    return frame


def _section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    return label


class MainWindow(QMainWindow):
    add_requested = pyqtSignal()
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    toggle_requested = pyqtSignal(str)
    import_requested = pyqtSignal()
    packs_requested = pyqtSignal()
    pause_toggled = pyqtSignal(bool)
    autostart_toggled = pyqtSignal(bool)
    notify_toggled = pyqtSignal(bool)
    picker_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(960, 640)
        self.setMinimumSize(760, 520)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        layout.addLayout(self._build_header())
        layout.addLayout(self._build_toolbar())
        layout.addWidget(self._build_snippets_card(), 1)
        layout.addWidget(self._build_footer())
        self.setCentralWidget(central)

    # ---- Layout builders -------------------------------------------------

    def _build_header(self) -> QVBoxLayout:
        title = QLabel(APP_NAME)
        title.setObjectName("windowTitle")

        subtitle = QLabel(APP_TAGLINE)
        subtitle.setObjectName("windowSubtitle")

        header = QVBoxLayout()
        header.setSpacing(2)
        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _build_toolbar(self) -> QHBoxLayout:
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchField")
        self.search_input.setPlaceholderText("Search by label, trigger, or preview")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._filter_snippets)

        add_button = QPushButton("New Snippet")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.add_requested.emit)

        picker_button = QPushButton("Quick Insert")
        picker_button.clicked.connect(self.picker_requested.emit)

        packs_button = QPushButton("Expansion Packs")
        packs_button.clicked.connect(self.packs_requested.emit)

        import_button = QPushButton("Import")
        import_button.clicked.connect(self.import_requested.emit)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addWidget(self.search_input, 1)
        toolbar.addWidget(import_button)
        toolbar.addWidget(packs_button)
        toolbar.addWidget(picker_button)
        toolbar.addWidget(add_button)
        return toolbar

    def _build_snippets_card(self) -> QFrame:
        self.snippet_table = QTableWidget(0, 5)
        self.snippet_table.setHorizontalHeaderLabels(["Label", "Type", "Trigger", "Enabled", "Preview"])
        self.snippet_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.snippet_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.snippet_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.snippet_table.setAlternatingRowColors(True)
        self.snippet_table.setShowGrid(False)
        self.snippet_table.setFrameShape(QFrame.Shape.NoFrame)
        self.snippet_table.verticalHeader().setVisible(False)
        self.snippet_table.verticalHeader().setDefaultSectionSize(34)
        self.snippet_table.horizontalHeader().setHighlightSections(False)
        self.snippet_table.horizontalHeader().setStretchLastSection(True)
        self.snippet_table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.snippet_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.snippet_table.itemDoubleClicked.connect(lambda _item: self._emit_edit())
        self.snippet_table.itemSelectionChanged.connect(self._sync_row_actions)

        self.empty_label = QLabel("No snippets yet — create one or load an expansion pack to get started.")
        self.empty_label.setObjectName("mutedText")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()

        self.edit_button = QPushButton("Edit")
        self.toggle_button = QPushButton("Enable / Disable")
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("dangerButton")
        self.edit_button.clicked.connect(self._emit_edit)
        self.toggle_button.clicked.connect(self._emit_toggle)
        self.delete_button.clicked.connect(self._emit_delete)

        self.count_label = QLabel()
        self.count_label.setObjectName("mutedText")

        row_actions = QHBoxLayout()
        row_actions.setSpacing(8)
        row_actions.addWidget(self.count_label)
        row_actions.addStretch(1)
        row_actions.addWidget(self.edit_button)
        row_actions.addWidget(self.toggle_button)
        row_actions.addWidget(self.delete_button)

        card = _card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)
        card_layout.addWidget(_section_title("Snippets"))
        card_layout.addWidget(self.snippet_table, 1)
        card_layout.addWidget(self.empty_label)
        card_layout.addLayout(row_actions)

        self._sync_row_actions()
        return card

    def _build_footer(self) -> QWidget:
        self.pause_checkbox = QCheckBox("Pause expansion")
        self.autostart_checkbox = QCheckBox("Launch at login")
        self.start_minimized_checkbox = QCheckBox("Start minimized to tray")
        self.case_sensitive_checkbox = QCheckBox("Case sensitive keywords")
        self.notify_checkbox = QCheckBox("Notify on expansion")

        self.pause_checkbox.toggled.connect(self.pause_toggled.emit)
        self.autostart_checkbox.toggled.connect(self.autostart_toggled.emit)
        self.notify_checkbox.toggled.connect(self.notify_toggled.emit)

        settings_grid = QGridLayout()
        settings_grid.setHorizontalSpacing(24)
        settings_grid.setVerticalSpacing(4)
        settings_grid.addWidget(self.pause_checkbox, 0, 0)
        settings_grid.addWidget(self.autostart_checkbox, 1, 0)
        settings_grid.addWidget(self.start_minimized_checkbox, 0, 1)
        settings_grid.addWidget(self.case_sensitive_checkbox, 1, 1)
        settings_grid.addWidget(self.notify_checkbox, 2, 0)
        settings_grid.setColumnStretch(2, 1)

        settings_card = _card()
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(14, 12, 14, 12)
        settings_layout.setSpacing(10)
        settings_layout.addWidget(_section_title("Preferences"))
        settings_layout.addLayout(settings_grid)
        settings_layout.addStretch(1)

        self.status_label = QLabel()
        self.status_label.setObjectName("statusText")
        self.status_label.setWordWrap(True)

        # Capability rows are laid out as two label/value columns so the card
        # stays readable instead of wrapping into a paragraph.
        self._capability_values: dict[str, QLabel] = {}
        capabilities_grid = QGridLayout()
        capabilities_grid.setHorizontalSpacing(8)
        capabilities_grid.setVerticalSpacing(4)
        for index, name in enumerate(
            ("Session", "Backend", "Typed expansion", "Global hotkeys", "Tray", "Autostart")
        ):
            row, column = index % 3, index // 3
            name_label = QLabel(f"{name}")
            name_label.setObjectName("mutedText")
            value_label = QLabel("—")
            self._capability_values[name] = value_label
            capabilities_grid.addWidget(name_label, row, column * 2)
            capabilities_grid.addWidget(value_label, row, column * 2 + 1)
        capabilities_grid.setColumnStretch(1, 1)
        capabilities_grid.setColumnStretch(3, 1)

        status_card = _card()
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(14, 12, 14, 12)
        status_layout.setSpacing(8)
        status_layout.addWidget(_section_title("Runtime"))
        status_layout.addWidget(self.status_label)
        status_layout.addLayout(capabilities_grid)
        status_layout.addStretch(1)

        footer = QWidget()
        footer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(16)
        footer_layout.addWidget(settings_card, 1)
        footer_layout.addWidget(status_card, 1)
        return footer

    # ---- Selection helpers ----------------------------------------------

    def current_snippet_id(self) -> str | None:
        selected = self.snippet_table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        item = self.snippet_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _sync_row_actions(self) -> None:
        has_selection = self.current_snippet_id() is not None
        for button in (self.edit_button, self.toggle_button, self.delete_button):
            button.setEnabled(has_selection)

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

    # ---- Data binding ----------------------------------------------------

    def update_snippets(self, snippets: list[Snippet]) -> None:
        self.snippet_table.setRowCount(len(snippets))
        for row, snippet in enumerate(snippets):
            label_item = QTableWidgetItem(snippet.label)
            label_item.setData(Qt.ItemDataRole.UserRole, snippet.id)
            self.snippet_table.setItem(row, 0, label_item)
            self.snippet_table.setItem(row, 1, QTableWidgetItem(snippet.trigger_type.title()))
            self.snippet_table.setItem(row, 2, QTableWidgetItem(snippet.trigger_value()))
            self.snippet_table.setItem(row, 3, QTableWidgetItem("On" if snippet.enabled else "Off"))
            preview = snippet.expansion_text.replace("\n", " ")[:80]
            self.snippet_table.setItem(row, 4, QTableWidgetItem(preview))
        self.snippet_table.resizeColumnsToContents()
        self.snippet_table.setVisible(bool(snippets))
        self.empty_label.setVisible(not snippets)
        self._filter_snippets()

    def _filter_snippets(self) -> None:
        query = self.search_input.text().strip().lower()
        visible = 0
        for row in range(self.snippet_table.rowCount()):
            if not query:
                self.snippet_table.setRowHidden(row, False)
                visible += 1
                continue

            # Read text from table items to filter
            label = self.snippet_table.item(row, 0).text().lower() if self.snippet_table.item(row, 0) else ""
            trigger_type = self.snippet_table.item(row, 1).text().lower() if self.snippet_table.item(row, 1) else ""
            trigger_val = self.snippet_table.item(row, 2).text().lower() if self.snippet_table.item(row, 2) else ""
            preview = self.snippet_table.item(row, 4).text().lower() if self.snippet_table.item(row, 4) else ""

            match = (query in label) or (query in trigger_type) or (query in trigger_val) or (query in preview)
            self.snippet_table.setRowHidden(row, not match)
            visible += int(match)

        total = self.snippet_table.rowCount()
        if query and visible != total:
            self.count_label.setText(f"{visible} of {total} snippets")
        else:
            self.count_label.setText(f"{total} snippet{'' if total == 1 else 's'}")
        self._sync_row_actions()

    def update_settings(self, settings: Settings) -> None:
        self.pause_checkbox.blockSignals(True)
        self.autostart_checkbox.blockSignals(True)
        self.start_minimized_checkbox.blockSignals(True)
        self.case_sensitive_checkbox.blockSignals(True)
        self.notify_checkbox.blockSignals(True)
        self.pause_checkbox.setChecked(settings.paused)
        self.autostart_checkbox.setChecked(settings.autostart)
        self.start_minimized_checkbox.setChecked(settings.start_minimized)
        self.case_sensitive_checkbox.setChecked(settings.case_sensitive)
        self.notify_checkbox.setChecked(settings.notify_on_expansion)
        self.pause_checkbox.blockSignals(False)
        self.autostart_checkbox.blockSignals(False)
        self.start_minimized_checkbox.blockSignals(False)
        self.case_sensitive_checkbox.blockSignals(False)
        self.notify_checkbox.blockSignals(False)

    def update_capabilities(self, report: CapabilityReport) -> None:
        self.status_label.setText(report.status_message)
        values = {
            "Session": report.session_type,
            "Backend": report.backend_name,
            "Typed expansion": "Yes" if report.typed_expansion_supported else "No",
            "Global hotkeys": "Yes" if report.global_hotkeys_supported else "No",
            "Tray": "Yes" if report.tray_supported else "No",
            "Autostart": "Yes" if report.autostart_supported else "No",
        }
        for name, value in values.items():
            self._capability_values[name].setText(value)

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
