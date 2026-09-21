# Original Path: aymashtain/ui/main_window.py

"""Main window: assembles tabs, status bar, menus and lifecycle.

Round 3 changes
---------------
* **Strip selector bar** under the menu bar. Ticks decide which strips
  receive commands from every tab. "All" is the default and means every
  connected strip. The list refreshes on every heartbeat.
* **"Options" top-level menu renamed to "Settings"** so it matches what
  the user expects. The tab itself is still called Options.
* ``brightness_limits_changed`` from the Options tab is wired to
  ``sync_clamp_notice()`` on Remote / Sweep / Console / Music, so the
  clamp notices and info lines refresh the moment the sliders move.
* **About dialog** reads ``CREDITS.md`` from the bundle and shows it
  with the project link.
* Everything else from Round 2 kept: theme toggle, dev-tools lock,
  Extract log, window memory, Esc / Ctrl+. emergency stop.
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
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTextBrowser,
    QVBoxLayout,
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


class StripSelectorBar(QWidget):
    """Horizontal strip of checkboxes: which strips commands go to.

    Empty selection means "all connected strips". Clicking "All" clears
    the individual ticks and puts the app back into broadcast mode.
    """

    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self._checkboxes: dict[str, QCheckBox] = {}
        self._building = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        layout.addWidget(QLabel("<b>Control:</b>"))

        self.chk_all = QCheckBox("All strips")
        self.chk_all.setChecked(True)
        self.chk_all.stateChanged.connect(self._on_all_toggled)
        layout.addWidget(self.chk_all)

        # The per-strip checkboxes live in a dedicated container so we can
        # wipe and rebuild them without touching the "All" checkbox.
        self._strip_container = QWidget()
        self._strip_layout = QHBoxLayout(self._strip_container)
        self._strip_layout.setContentsMargins(0, 0, 0, 0)
        self._strip_layout.setSpacing(6)
        layout.addWidget(self._strip_container)

        layout.addStretch()

        # Info label tells the user what the selection currently means.
        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet("color: #71717A;")
        layout.addWidget(self.lbl_info)

        self.refresh()

    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Rebuild the per-strip checkboxes from the BleManager state."""
        self._building = True
        # Wipe existing checkboxes.
        while self._strip_layout.count():
            item = self._strip_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._checkboxes.clear()

        states = sorted(
            self.ctx.ble.devices.values(),
            key=lambda s: (s.status != "connected", s.name or s.address),
        )

        for state in states:
            label = state.name or state.address
            # Shorten long names so the bar stays compact.
            if len(label) > 22:
                label = label[:20] + "…"
            chk = QCheckBox(label)
            chk.setToolTip(
                f"{state.name or state.address}\n"
                f"Address: {state.address}\n"
                f"Status: {state.status}"
            )
            chk.setEnabled(state.connected)
            chk.setChecked(state.address in self.ctx.selected_strips)
            chk.stateChanged.connect(
                lambda _=0, addr=state.address: self._on_strip_toggled(addr)
            )
            self._checkboxes[state.address] = chk
            self._strip_layout.addWidget(chk)

        self._building = False
        self._refresh_info()
        self._sync_all_checkbox()

    def _on_all_toggled(self) -> None:
        if self._building:
            return
        if self.chk_all.isChecked():
            # Clear individual selections -> broadcast mode.
            self._building = True
            for chk in self._checkboxes.values():
                chk.setChecked(False)
            self._building = False
            self.ctx.selected_strips = []
        else:
            # User unchecked "All": pick the currently connected strips as
            # a starting selection so they are not left sending nowhere.
            connected = self.ctx.ble.connected_addresses()
            self._building = True
            for addr, chk in self._checkboxes.items():
                chk.setChecked(addr in connected)
            self._building = False
            self.ctx.selected_strips = list(connected)
        self._refresh_info()

    def _on_strip_toggled(self, address: str) -> None:
        if self._building:
            return
        selected = [
            addr for addr, chk in self._checkboxes.items() if chk.isChecked()
        ]
        self.ctx.selected_strips = selected
        self._sync_all_checkbox()
        self._refresh_info()

    def _sync_all_checkbox(self) -> None:
        """The 'All' checkbox reflects whether the selection is empty."""
        self._building = True
        self.chk_all.setChecked(not self.ctx.selected_strips)
        self._building = False

    def _refresh_info(self) -> None:
        connected = self.ctx.ble.connected_addresses()
        if not connected:
            self.lbl_info.setText("No strips connected")
            return
        if not self.ctx.selected_strips:
            self.lbl_info.setText(f"Broadcast to {len(connected)} strip(s)")
            return
        live = [a for a in self.ctx.selected_strips if a in connected]
        self.lbl_info.setText(f"{len(live)} of {len(connected)} strip(s) selected")


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

        # --- central layout: strip selector + tabs ---------------------
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.strip_bar = StripSelectorBar(ctx)
        outer.addWidget(self.strip_bar)

        self.tabs = QTabWidget()
        outer.addWidget(self.tabs, stretch=1)
        self.setCentralWidget(container)

        # --- tabs ------------------------------------------------------
        self.tab_connect = ConnectTab(ctx)
        self.tab_remote = RemoteTab(ctx)
        self.tab_camera = CameraTab(ctx)
        self.tab_sweep = SweepTab(ctx, camera_tab=self.tab_camera)
        self.tab_music = MusicTab(ctx)
        self.tab_console = ConsoleTab(ctx)
        self.tab_lab = LabTab(
            ctx, remote_tab=self.tab_remote, camera_tab=self.tab_camera
        )
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

        # --- cross-tab wiring -----------------------------------------
        self.tab_options.developer_tools_changed.connect(self._set_developer_tools)
        self.tab_options.brightness_limits_changed.connect(
            self._on_brightness_limits_changed
        )

        # Apply the initial lock state (Lab hidden when dev tools are off).
        self._apply_developer_lock(self.ctx.settings.developer_tools)

        # --- status bar -----------------------------------------------
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
                    self.ctx.ble.send_hex_all(
                        cmd, "menu", addresses=self.ctx.resolve_targets()
                    )
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

        action_settings = QAction("Settings", self)
        action_settings.setShortcut(QKeySequence("Ctrl+,"))
        action_settings.triggered.connect(self._open_options_tab)
        view_menu.addAction(action_settings)

        # --- Settings menu (opens the Options tab) -----------------------
        settings_menu = self.menuBar().addMenu("&Settings")
        action_open_settings = QAction("Open settings tab", self)
        action_open_settings.triggered.connect(self._open_options_tab)
        settings_menu.addAction(action_open_settings)

        action_extract_2 = QAction("Extract log…", self)
        action_extract_2.triggered.connect(self._extract_log)
        settings_menu.addAction(action_extract_2)

        # --- Help ---------------------------------------------------------
        help_menu = self.menuBar().addMenu("&Help")
        action_about = QAction("About", self)
        action_about.triggered.connect(self._show_about)
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

        self.action_dev_tools.blockSignals(True)
        self.action_dev_tools.setChecked(enabled)
        self.action_dev_tools.blockSignals(False)

        self.tab_options.chk_dev.blockSignals(True)
        self.tab_options.chk_dev.setChecked(enabled)
        self.tab_options.chk_dev.blockSignals(False)

        self._apply_developer_lock(enabled)

    def _apply_developer_lock(self, enabled: bool) -> None:
        index = self.tabs.indexOf(self.tab_lab)
        if index >= 0:
            self.tabs.setTabVisible(index, enabled)

    # ------------------------------------------------------------------
    # Clamp notice fan-out
    # ------------------------------------------------------------------

    def _on_brightness_limits_changed(self, lo: int, hi: int) -> None:
        """Options changed the brightness range. Tell every tab that shows it."""
        self.strip_bar._refresh_info()
        for name in ("sync_clamp_notice",):
            for tab in (self.tab_remote, self.tab_sweep, self.tab_console, self.tab_music):
                hook = getattr(tab, name, None)
                if hook is not None:
                    try:
                        hook()
                    except Exception as exc:  # noqa: BLE001 - defensive
                        self.ctx.log(
                            "error",
                            f"{type(tab).__name__}.{name}() failed: {exc}",
                        )

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
    # About dialog
    # ------------------------------------------------------------------

    def _show_about(self) -> None:
        credits = self._load_credits()

        html = f"""
        <h2>{APP_NAME} {APP_DISPLAY_VERSION}</h2>
        <p>Free, ad-free controller for MR Star / Magic Home style BLE LED strips.</p>
        <p><b>Project</b><br>
        <a href="https://github.com/aymashtain92/AymashTain-RGB-Universal-Remote">
        github.com/aymashtain92/AymashTain-RGB-Universal-Remote</a></p>
        <p><b>Protocol</b><br>
        Power <code>BC 01 01 XX 55</code><br>
        Colour <code>BC 04 06 HHHH SSSS 0000 55</code> (hue 0-359, saturation 0-1000)<br>
        Brightness <code>BC 05 06 BBBB 00000000 55</code> (0-1024)<br>
        Effect <code>BC 06 02 XX 0000 55</code></p>
        <p>Colour and brightness are sent as separate frames on purpose —
        merging them is what makes colours look pale or white-tinted.</p>
        <p><b>Data folder</b><br><code>{paths.data_dir()}</code></p>
        <hr>
        <h3>Credits</h3>
        <pre style="white-space: pre-wrap; font-family: inherit;">{credits}</pre>
        """

        dialog = QMessageBox(self)
        dialog.setWindowTitle(f"About {APP_NAME}")
        dialog.setIcon(QMessageBox.Information)
        dialog.setTextFormat(Qt.RichText)
        # QMessageBox does not scroll long text. Use a QTextBrowser instead
        # when the credits block is large.
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(html)
        browser.setMinimumSize(560, 480)

        dialog.layout().addWidget(
            browser, dialog.layout().rowCount(), 0, 1, dialog.layout().columnCount()
        )
        dialog.exec()

    @staticmethod
    def _load_credits() -> str:
        path = paths.bundle_dir() / "CREDITS.md"
        if not path.is_file():
            return "(CREDITS.md not found.)"
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            return f"(Could not read CREDITS.md: {exc})"

    # ------------------------------------------------------------------
    # Window memory
    # ------------------------------------------------------------------

    def _restore_window_state(self) -> None:
        settings = self.ctx.settings

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

            x = max(geo.x(), min(x, geo.x() + geo.width() - width))
            y = max(geo.y(), min(y, geo.y() + geo.height() - height))
            self.setGeometry(x, y, width, height)
        elif settings.window_geometry:
            self.restoreGeometry(
                QByteArray.fromBase64(settings.window_geometry.encode())
            )

    def _capture_window_state(self) -> None:
        settings = self.ctx.settings
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
        self.strip_bar.refresh()
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
