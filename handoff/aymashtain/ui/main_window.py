"""Main window: assembles tabs, status bar, menus and lifecycle.

Round 2 changes
---------------
* Options tab added (last tab). Also reachable from the menu bar.
* View menu now has: dark-mode toggle, developer-tools toggle (mirrors
  Options), Extract log, and Open Options.
* Developer-tools lock hides the Lab tab when off.
* Theme reads ``settings.resolved_dark()`` so light / dark / follow-OS works.
* Window screen, position, size and DPI scale are saved on close and
  restored on the same monitor when possible.
* Minimum size 300x300, per the spec.
"""

from __future__ import annotations

import asyncio
import platform
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QByteArray, QEventLoop, Qt, QTimer
from PySide6.QtGui import QAction, QGuiApplication, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTableWidget,
    QTabWidget,
    QWidget,
)

from .. import APP_DISPLAY_VERSION, APP_NAME, APP_VERSION, paths
from ..config import THEME_DARK, THEME_LIGHT, THEME_SYSTEM
from ..protocol import CMD_OFF, CMD_ON
from . import theme
from .context import AppContext
from .tabs import (
    CameraTab,
    ConnectTab,
    ConsoleTab,
    EventsTab,
    LabTab,
    MusicTab,
    OptionsTab,
    RemoteTab,
    SweepTab,
)

MIN_WIDTH = 300
MIN_HEIGHT = 300

ABOUT = f"""<h3>{APP_NAME} {APP_DISPLAY_VERSION}</h3>
<p>Free, ad-free controller for MR Star / Magic Home style BLE LED strips.</p>
<p><b>Protocol</b><br>
Power <code>BC 01 01 XX 55</code><br>
Colour <code>BC 04 06 HHHH SSSS 0000 55</code> (hue 0-359, saturation 0-1000)<br>
Brightness <code>BC 05 06 BBBB 00000000 55</code> (0-1024)<br>
Effect <code>BC 06 02 XX 0000 55</code></p>
<p>Colour and brightness are sent as separate frames on purpose — merging them
is what makes colours look pale or white-tinted.</p>
<p>Data folder: <code>{paths.data_dir()}</code></p>
<p>Credits: see <code>CREDITS.md</code> in the repository root, or the project
page at <a href="https://github.com/aymashtain92/AymashTain-RGB-Universal-Remote">
github.com/aymashtain92/AymashTain-RGB-Universal-Remote</a>.</p>
"""


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle(f"{APP_NAME} {APP_DISPLAY_VERSION}")
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.resize(1180, 840)
        icon = paths.icon_file()
        if icon is not None:
            self.setWindowIcon(QIcon(str(icon)))
        self.setStyleSheet(theme.stylesheet(ctx.settings.resolved_dark()))

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab_connect = ConnectTab(ctx)
        self.tab_remote = RemoteTab(ctx)
        self.tab_camera = CameraTab(ctx)
        self.tab_sweep = SweepTab(ctx, camera_tab=self.tab_camera)
        self.tab_music = MusicTab(ctx)
        self.tab_console = ConsoleTab(ctx)
        self.tab_lab = LabTab(ctx, remote_tab=self.tab_remote, camera_tab=self.tab_camera)
        self.tab_events = EventsTab(ctx)
        self.tab_options = OptionsTab(ctx)

        for widget, title in (
            (self.tab_connect, "Connect"),
            (self.tab_remote, "Remote"),
            (self.tab_music, "Music && Media"),
            (self.tab_sweep, "Sweep"),
            (self.tab_camera, "Camera"),
            (self.tab_console, "Console"),
            (self.tab_lab, "Lab"),
            (self.tab_events, "Events"),
            (self.tab_options, "Options"),
        ):
            self.tabs.addTab(widget, title)

        for table in self.findChildren(QTableWidget):
            table.setAlternatingRowColors(True)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.verticalHeader().setVisible(False)
            table.verticalHeader().setDefaultSectionSize(26)

        self._build_menu()

        # Options tab emits this when the developer checkbox flips.
        self.tab_options.developer_tools_changed.connect(self._set_developer_tools)

        # Apply the initial lock state (Lab hidden when developer tools are off).
        self._apply_developer_lock(self.ctx.settings.developer_tools)

        self.lbl_devices = QLabel()
        self.lbl_frames = QLabel()
        self.statusBar().addPermanentWidget(self.lbl_devices)
        self.statusBar().addPermanentWidget(self.lbl_frames)

        self._heartbeat = QTimer(self)
        self._heartbeat.timeout.connect(self._tick)
        self._heartbeat.start(400)

        self._restore_window_state()

        ctx.log("info", f"{APP_NAME} {APP_VERSION} started")
        if ctx.settings.auto_connect_on_start:
            for entry in ctx.settings.known_devices:
                ctx.run(ctx.ble.connect(entry["address"], entry.get("name", "")))

    # ------------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        # --- File ---------------------------------------------------------
        file_menu = self.menuBar().addMenu("&File")
        action_folder = QAction("Open data folder", self)
        action_folder.triggered.connect(self._open_data_folder)
        file_menu.addAction(action_folder)
        file_menu.addSeparator()
        action_quit = QAction("Quit", self)
        action_quit.setShortcuts([QKeySequence("Ctrl+Q"), QKeySequence("Alt+F4")])
        action_quit.triggered.connect(self.close)
        file_menu.addAction(action_quit)

        # --- Control ------------------------------------------------------
        control_menu = self.menuBar().addMenu("&Control")
        for label, hex_cmd in (("All strips ON", CMD_ON), ("All strips OFF", CMD_OFF)):
            action = QAction(label, self)
            action.triggered.connect(
                lambda _=False, cmd=hex_cmd: self.ctx.run(
                    self.ctx.ble.send_hex_all(cmd, "menu")
                )
            )
            control_menu.addAction(action)
        action_reconnect = QAction("Connect all known strips", self)
        action_reconnect.triggered.connect(self.tab_connect._connect_all)
        control_menu.addAction(action_reconnect)
        control_menu.addSeparator()
        action_panic = QAction("Stop all activity", self)
        action_panic.setShortcuts([QKeySequence("Esc"), QKeySequence("Ctrl+.")])
        action_panic.triggered.connect(self.stop_all_activity)
        control_menu.addAction(action_panic)

        # --- View ---------------------------------------------------------
        view_menu = self.menuBar().addMenu("&View")

        self.action_dark_mode = QAction("Dark mode", self)
        self.action_dark_mode.setCheckable(True)
        self.action_dark_mode.setChecked(self.ctx.settings.resolved_dark())
        self.action_dark_mode.triggered.connect(self._on_dark_mode_toggled)
        view_menu.addAction(self.action_dark_mode)

        self.action_dev_tools = QAction("Developer tools", self)
        self.action_dev_tools.setCheckable(True)
        self.action_dev_tools.setChecked(self.ctx.settings.developer_tools)
        self.action_dev_tools.triggered.connect(self._set_developer_tools)
        view_menu.addAction(self.action_dev_tools)

        view_menu.addSeparator()

        action_extract = QAction("Extract log…", self)
        action_extract.triggered.connect(self._extract_log)
        view_menu.addAction(action_extract)

        action_options = QAction("Options", self)
        action_options.setShortcut(QKeySequence("Ctrl+,"))
        action_options.triggered.connect(self._open_options_tab)
        view_menu.addAction(action_options)

        # --- Options (menu-bar entry that opens the Options tab) ----------
        options_menu = self.menuBar().addMenu("&Options")
        action_open_options = QAction("Open Options tab", self)
        action_open_options.triggered.connect(self._open_options_tab)
        options_menu.addAction(action_open_options)

        action_open_options_2 = QAction("Extract log…", self)
        action_open_options_2.triggered.connect(self._extract_log)
        options_menu.addAction(action_open_options_2)

        # --- Help ---------------------------------------------------------
        help_menu = self.menuBar().addMenu("&Help")
        action_about = QAction("About", self)
        action_about.triggered.connect(
            lambda: QMessageBox.about(self, f"About {APP_NAME}", ABOUT)
        )
        help_menu.addAction(action_about)

    # ------------------------------------------------------------------
    # Options / theme / developer lock
    # ------------------------------------------------------------------

    def _open_options_tab(self) -> None:
        index = self.tabs.indexOf(self.tab_options)
        if index >= 0:
            self.tabs.setCurrentIndex(index)

    def apply_theme(self) -> None:
        """Reapply the stylesheet from the current settings."""
        self.setStyleSheet(theme.stylesheet(self.ctx.settings.resolved_dark()))
        # Keep the View-menu checkmark in sync.
        dark = self.ctx.settings.resolved_dark()
        self.action_dark_mode.blockSignals(True)
        self.action_dark_mode.setChecked(dark)
        self.action_dark_mode.blockSignals(False)

    def _on_dark_mode_toggled(self, checked: bool) -> None:
        # Manual toggle overrides follow-OS.
        self.ctx.settings.theme_mode = THEME_DARK if checked else THEME_LIGHT
        self.ctx.settings.dark_theme = checked
        self.apply_theme()

        # Mirror in the Options combo without re-emitting.
        combo = self.tab_options.combo_theme
        idx = combo.findData(self.ctx.settings.theme_mode)
        if idx >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    def _set_developer_tools(self, enabled: bool) -> None:
        """Single source of truth for the developer-tools lock."""
        enabled = bool(enabled)
        self.ctx.settings.developer_tools = enabled

        # Sync the View-menu checkmark.
        self.action_dev_tools.blockSignals(True)
        self.action_dev_tools.setChecked(enabled)
        self.action_dev_tools.blockSignals(False)

        # Sync the Options checkbox.
        self.tab_options.chk_dev.blockSignals(True)
        self.tab_options.chk_dev.setChecked(enabled)
        self.tab_options.chk_dev.blockSignals(False)

        self._apply_developer_lock(enabled)

    def _apply_developer_lock(self, enabled: bool) -> None:
        """Hide or show the Lab tab based on the lock."""
        index = self.tabs.indexOf(self.tab_lab)
        if index >= 0:
            self.tabs.setTabVisible(index, enabled)

    # ------------------------------------------------------------------
    # Activity control
    # ------------------------------------------------------------------

    def stop_all_activity(self) -> None:
        self.tab_sweep._stop()
        self.tab_console._stop()
        self.tab_music._stop_reacting()
        if hasattr(self.tab_lab, "_lab_stop"):
            self.tab_lab._lab_stop()
        self.ctx.log("info", "Stopped all running activity")
        self.statusBar().showMessage("Stopped all running activity", 4000)

    # ------------------------------------------------------------------
    # Extract log
    # ------------------------------------------------------------------

    def _extract_log(self) -> None:
        """Bundle logs + config + system info into one zip for support."""
        default_dir = self.ctx.settings.save_location.strip() or str(paths.data_dir())
        default_name = f"aymashtain_support_{datetime.now():%Y%m%d_%H%M%S}.zip"
        default_path = str(Path(default_dir) / default_name)

        chosen, _ = QFileDialog.getSaveFileName(
            self,
            "Save support bundle",
            default_path,
            "Zip archive (*.zip)",
        )
        if not chosen:
            return

        try:
            with zipfile.ZipFile(chosen, "w", zipfile.ZIP_DEFLATED) as zf:
                logs = paths.logs_dir()
                if logs.is_dir():
                    for entry in sorted(logs.iterdir()):
                        if entry.is_file():
                            zf.write(entry, arcname=f"logs/{entry.name}")

                cfg = paths.config_path()
                if cfg.is_file():
                    zf.write(cfg, arcname="config.json")

                zf.writestr("system_info.txt", self._collect_system_info())

            self.ctx.log("info", f"Support bundle written: {chosen}")
            QMessageBox.information(
                self,
                "Extract log",
                f"Support bundle saved to:\n{chosen}",
            )
        except Exception as exc:  # pragma: no cover - IO failure path
            self.ctx.log("error", f"Extract log failed: {exc}")
            QMessageBox.critical(self, "Extract log", f"Failed:\n{exc}")

    def _collect_system_info(self) -> str:
        settings = self.ctx.settings
        lines = [
            f"{APP_NAME} {APP_DISPLAY_VERSION} (code {APP_VERSION})",
            f"Python: {sys.version.split()[0]}",
            f"Platform: {platform.platform()}",
            f"Data folder: {paths.data_dir()}",
            f"Logs folder: {paths.logs_dir()}",
            f"Window scale at last close: {settings.window_scale}",
            f"Frames sent this session: {self.ctx.ble.sent_frames}  "
            f"failed: {self.ctx.ble.failed_frames}",
            f"Theme mode: {settings.theme_mode}",
            f"Developer tools: {settings.developer_tools}",
            f"Brightness limits: {settings.brightness_min}% – {settings.brightness_max}%",
            f"Camera: index {settings.camera_index}, "
            f"{settings.camera_resolution} @ {settings.camera_fps} fps, "
            f"exposure lock={settings.camera_exposure_lock}, "
            f"wb lock={settings.camera_wb_lock}",
            f"Audio: mic={settings.audio_mic_device} "
            f"second={settings.audio_second_mic_device} "
            f"speaker={settings.audio_speaker_device}",
            "",
            "Known devices:",
        ]
        for entry in settings.known_devices:
            lines.append(f"  {entry.get('name', '?')}  {entry.get('address', '?')}")
        lines.append("")
        lines.append("Per-pattern mic sources:")
        if settings.pattern_sources:
            for pattern, source in settings.pattern_sources.items():
                lines.append(f"  {pattern}: {source}")
        else:
            lines.append("  (none set)")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Window memory
    # ------------------------------------------------------------------

    def _restore_window_state(self) -> None:
        settings = self.ctx.settings

        # Old builds only had a base64 geometry blob.
        if not settings.remember_window:
            if settings.window_geometry:
                self.restoreGeometry(
                    QByteArray.fromBase64(settings.window_geometry.encode())
                )
            return

        target = None
        if settings.window_screen:
            for screen in QGuiApplication.screens():
                if screen.name() == settings.window_screen:
                    target = screen
                    break
        if target is None:
            target = QGuiApplication.primaryScreen()

        if (
            target is not None
            and settings.window_width > 0
            and settings.window_height > 0
        ):
            geo = target.availableGeometry()
            width = min(settings.window_width, geo.width())
            height = min(settings.window_height, geo.height())
            width = max(width, MIN_WIDTH)
            height = max(height, MIN_HEIGHT)

            if settings.window_x >= 0 and settings.window_y >= 0:
                x = settings.window_x
                y = settings.window_y
            else:
                x = geo.x() + (geo.width() - width) // 2
                y = geo.y() + (geo.height() - height) // 2

            # Clamp so we never restore fully off-screen.
            x = max(geo.x(), min(x, geo.x() + geo.width() - width))
            y = max(geo.y(), min(y, geo.y() + geo.height() - height))
            self.setGeometry(x, y, width, height)
        elif settings.window_geometry:
            self.restoreGeometry(
                QByteArray.fromBase64(settings.window_geometry.encode())
            )

    def _capture_window_state(self) -> None:
        settings = self.ctx.settings
        # Always write the legacy geometry blob so older tooling keeps working.
        settings.window_geometry = bytes(self.saveGeometry().toBase64()).decode()

        if not settings.remember_window:
            return

        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is not None:
            settings.window_screen = screen.name()
            settings.window_scale = float(screen.devicePixelRatio())

        pos = self.pos()
        size = self.size()
        settings.window_x = pos.x()
        settings.window_y = pos.y()
        settings.window_width = size.width()
        settings.window_height = size.height()

    # ------------------------------------------------------------------
    # File / folder helpers
    # ------------------------------------------------------------------

    def _open_data_folder(self) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(paths.data_dir())))

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        self.tab_events.drain()
        self.tab_connect.refresh()
        connected = len(self.ctx.ble.connected_addresses())
        total = len(self.ctx.ble.devices)
        self.lbl_devices.setText(f"  Strips: {connected}/{total}  ")
        self.lbl_frames.setText(
            f"  Frames sent: {self.ctx.ble.sent_frames}  "
            f"failed: {self.ctx.ble.failed_frames}  "
        )

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self._heartbeat.stop()
        self.stop_all_activity()
        for tab in (self.tab_camera, self.tab_music):
            shutdown = getattr(tab, "shutdown", None)
            if shutdown is not None:
                shutdown()

        self._capture_window_state()
        self.ctx.settings.save()

        if self.ctx.bus.session_logger is not None:
            self.ctx.bus.session_logger.flush_json()

        self._disconnect_with_timeout(2.0)
        self.ctx.db.close()
        super().closeEvent(event)
        QApplication.quit()

    def _disconnect_with_timeout(self, seconds: float) -> None:
        try:
            loop = asyncio.get_event_loop()
            task = loop.create_task(self.ctx.ble.disconnect_all())
        except RuntimeError:
            return
        deadline = time.monotonic() + seconds
        while not task.done() and time.monotonic() < deadline:
            QApplication.processEvents(QEventLoop.AllEvents, 50)
        if not task.done():
            task.cancel()


def center_placeholder(text: str) -> QWidget:
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    return label
