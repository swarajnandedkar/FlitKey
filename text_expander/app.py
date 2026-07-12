from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QAction, QGuiApplication, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from .branding import APP_NAME, ICON_FILE, PICKER_TITLE
from .config import load_state, save_state
from .gui.main_window import MainWindow
from .gui.picker_dialog import SnippetPickerDialog
from .gui.snippet_dialog import SnippetDialog
from .models import Snippet
from .platform import install_launcher, set_autostart
from .placeholders import render_placeholders
from .runtime.factory import create_backend


class AppController(QObject):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.snippets, self.settings = load_state()
        self.window = MainWindow()
        self.window.update_snippets(self.snippets)
        self.window.update_settings(self.settings)

        self.backend = create_backend()
        self.window.update_capabilities(self.backend.capability_report)

        self.tray = QSystemTrayIcon(self._load_icon(), self.app)
        self.tray.setToolTip(APP_NAME)
        self.tray.setContextMenu(self._build_tray_menu())
        self.tray.activated.connect(self._tray_activated)

        self.window.add_requested.connect(self.add_snippet)
        self.window.edit_requested.connect(self.edit_snippet)
        self.window.delete_requested.connect(self.delete_snippet)
        self.window.toggle_requested.connect(self.toggle_snippet)
        self.window.pause_toggled.connect(self.set_paused)
        self.window.autostart_toggled.connect(self.set_autostart_enabled)
        self.window.picker_requested.connect(self.open_picker)

        self.window.start_minimized_checkbox.toggled.connect(self._settings_checkbox_changed)
        self.window.case_sensitive_checkbox.toggled.connect(self._settings_checkbox_changed)
        self.backend.status_changed.connect(self._update_status)
        self.backend.snippet_triggered.connect(self._notify_snippet_triggered)

        install_launcher()
        if self.settings.autostart:
            set_autostart(True)

        self._start_backend()
        self.tray.show()
        self._update_status(self.backend.capability_report.status_message)

    def _load_icon(self) -> QIcon:
        icon = QIcon.fromTheme("preferences-desktop-keyboard-shortcuts")
        if not icon.isNull():
            return icon
        return QIcon(str(Path(__file__).resolve().parent.parent / "assets" / ICON_FILE))

    def _build_tray_menu(self) -> QMenu:
        menu = QMenu()
        show_action = QAction(f"Open {APP_NAME}", menu)
        picker_action = QAction("Quick insert", menu)
        self.pause_action = QAction("Pause", menu)
        quit_action = QAction("Quit", menu)

        show_action.triggered.connect(self.show_window)
        picker_action.triggered.connect(self.open_picker)
        self.pause_action.triggered.connect(lambda: self.set_paused(not self.settings.paused))
        quit_action.triggered.connect(self.quit)

        menu.addAction(show_action)
        menu.addAction(picker_action)
        menu.addAction(self.pause_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        return menu

    def _start_backend(self) -> None:
        self.backend.start(self.snippets, self.settings.case_sensitive)
        self.backend.set_paused(self.settings.paused)
        self._sync_pause_action()

    def show_initial_window(self, start_minimized: bool = False) -> None:
        if start_minimized and self.settings.start_minimized:
            return
        self.show_window()

    def show_window(self) -> None:
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def add_snippet(self) -> None:
        dialog = SnippetDialog(self.window)
        if dialog.exec():
            snippet = dialog.snippet()
            if self._duplicate_hotkey(snippet):
                QMessageBox.warning(self.window, "Duplicate hotkey", "Another snippet already uses that hotkey.")
                return
            self.snippets.append(snippet)
            self._persist_and_reload()

    def edit_snippet(self, snippet_id: str) -> None:
        snippet = self._find_snippet(snippet_id)
        if not snippet:
            return
        dialog = SnippetDialog(self.window, snippet)
        if dialog.exec():
            replacement = dialog.snippet()
            if self._duplicate_hotkey(replacement, exclude_id=snippet_id):
                QMessageBox.warning(self.window, "Duplicate hotkey", "Another snippet already uses that hotkey.")
                return
            index = self.snippets.index(snippet)
            self.snippets[index] = replacement
            self._persist_and_reload()

    def delete_snippet(self, snippet_id: str) -> None:
        snippet = self._find_snippet(snippet_id)
        if not snippet or not self.window.confirm_delete(snippet):
            return
        self.snippets = [item for item in self.snippets if item.id != snippet_id]
        self._persist_and_reload()

    def toggle_snippet(self, snippet_id: str) -> None:
        snippet = self._find_snippet(snippet_id)
        if not snippet:
            return
        snippet.enabled = not snippet.enabled
        self._persist_and_reload()

    def set_paused(self, paused: bool) -> None:
        self.settings.paused = paused
        self.backend.set_paused(paused)
        self._persist()
        self.window.update_settings(self.settings)
        self._sync_pause_action()

    def set_autostart_enabled(self, enabled: bool) -> None:
        self.settings.autostart = enabled
        set_autostart(enabled)
        self._persist()

    def open_picker(self) -> None:
        dialog = SnippetPickerDialog(self.snippets, self.window)
        if not dialog.exec() or not dialog.selected_snippet:
            return
        snippet = dialog.selected_snippet
        if self.backend.can_inject_text():
            ok = self.backend.inject_text(snippet.expansion_text)
            if ok:
                self._notify_snippet_triggered(snippet.label)
                return
        
        rendered_text = render_placeholders(snippet.expansion_text).replace("{{cursor}}", "")
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(rendered_text)
        self.tray.showMessage(f"{APP_NAME} copied text", f"{snippet.label} copied to clipboard.")

    def _settings_checkbox_changed(self) -> None:
        self.settings.start_minimized = self.window.start_minimized_checkbox.isChecked()
        self.settings.case_sensitive = self.window.case_sensitive_checkbox.isChecked()
        self._persist()
        self.backend.reload(self.snippets, self.settings.case_sensitive)

    def _persist(self) -> None:
        save_state(self.snippets, self.settings)

    def _persist_and_reload(self) -> None:
        self._persist()
        self.window.update_snippets(self.snippets)
        self.window.update_settings(self.settings)
        self.backend.reload(self.snippets, self.settings.case_sensitive)

    def _find_snippet(self, snippet_id: str) -> Snippet | None:
        return next((snippet for snippet in self.snippets if snippet.id == snippet_id), None)

    def _duplicate_hotkey(self, candidate: Snippet, exclude_id: str | None = None) -> bool:
        if candidate.trigger_type != "hotkey" or not candidate.hotkey:
            return False
        normalized = candidate.hotkey.strip().lower()
        for snippet in self.snippets:
            if snippet.id == exclude_id:
                continue
            if snippet.trigger_type == "hotkey" and snippet.hotkey.strip().lower() == normalized:
                return True
        return False

    def _update_status(self, message: str) -> None:
        self.window.status_label.setText(message)
        if self.settings.paused:
            self.tray.setToolTip(f"{APP_NAME} (Paused)")
        else:
            self.tray.setToolTip(APP_NAME)

    def _notify_snippet_triggered(self, label: str) -> None:
        self.tray.showMessage(f"{APP_NAME} expanded a snippet", label)

    def _sync_pause_action(self) -> None:
        self.pause_action.setText("Resume" if self.settings.paused else "Pause")

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick}:
            self.show_window()

    def quit(self) -> None:
        self.backend.stop()
        self.tray.hide()
        self.app.quit()
