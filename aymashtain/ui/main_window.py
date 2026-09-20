"""Main window: assembles tabs, status bar and lifecycle."""

from __future__ import annotations

import asyncio
import time

from PySide6.QtCore import QByteArray, QEventLoop, Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTableWidget,
    QTabWidget,
    QWidget,
)

from .. import APP_NAME, APP_VERSION, paths
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
    RemoteTab,
    SweepTab,
)

ABOUT = f"""<h3>{APP_NAME} {APP_VERSION}</h3>
<p>Free, ad-free controller for MR Star / Magic Home style BLE LED strips.</p>
<p><b>Protocol</b><br>
Power <code>BC 01 01 XX 55</code><br>
Colour <code>BC 04 06 HHHH SSSS 0000 55</code> (hue 0-359, saturation 0-1000)<br>
Brightness <code>BC 05 06 BBBB 00000000 55</code> (0-1024)<br>
Effect <code>BC 06 02 XX 0000 55</code></p>
<p>Colour and brightness are sent as separate frames on purpose — merging them
is what makes colours look pale or white-tinted.</p>
<p>Data folder: <code>{paths.data_dir()}</code></p>
<p>Credits: see <code>CREDITS.md</code> in the repository root.</p>
"""


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1180, 840)
        icon = paths.icon_file()
        if icon is not None:
            self.setWindowIcon(QIcon(str(icon)))
        self.setStyleSheet(theme.stylesheet(ctx.settings.dark_theme))

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

        for widget, title in (
            (self.tab_connect, "Connect"),
            (self.tab_remote, "Remote"),
            (self.tab_music, "Music && Media"),
            (self.tab_sweep, "Sweep"),
            (self.tab_camera, "Camera"),
            (self.tab_console, "Console"),
            (self.tab_lab, "Lab"),
            (self.tab_events, "Events"),
        ):
            self.tabs.addTab(widget, title)

        for table in self.findChildren(QTableWidget):
            table.setAlternatingRowColors(True)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.verticalHeader().setVisible(False)
            table.verticalHeader().setDefaultSectionSize(26)

        self._build_menu()

        self.lbl_devices = QLabel()
        self.lbl_frames = QLabel()
        self.statusBar().addPermanentWidget(self.lbl_devices)
        self.statusBar().addPermanentWidget(self.lbl_frames)

        self._heartbeat = QTimer(self)
        self._heartbeat.timeout.connect(self._tick)
        self._heartbeat.start(400)

        if ctx.settings.window_geometry:
            self.restoreGeometry(QByteArray.fromBase64(ctx.settings.window_geometry.encode()))

        ctx.log("info", f"{APP_NAME} {APP_VERSION} started")
        if ctx.settings.auto_connect_on_start:
            for entry in ctx.settings.known_devices:
                ctx.run(ctx.ble.connect(entry["address"], entry.get("name", "")))

    # --- chrome -----------------------------------------------------------

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        action_folder = QAction("Open data folder", self)
        action_folder.triggered.connect(self._open_data_folder)
        file_menu.addAction(action_folder)
        file_menu.addSeparator()
        action_quit = QAction("Quit", self)
        action_quit.setShortcuts([QKeySequence("Ctrl+Q"), QKeySequence("Alt+F4")])
        action_quit.triggered.connect(self.close)
        file_menu.addAction(action_quit)

        control_menu = self.menuBar().addMenu("&Control")
        for label, hex_cmd in (("All strips ON", CMD_ON), ("All strips OFF", CMD_OFF)):
            action = QAction(label, self)
            action.triggered.connect(
                lambda _=False, cmd=hex_cmd: self.ctx.run(self.ctx.ble.send_hex_all(cmd, "menu"))
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

        view_menu = self.menuBar().addMenu("&View")
        action_theme = QAction("Toggle light / dark", self)
        action_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(action_theme)

        help_menu = self.menuBar().addMenu("&Help")
        action_about = QAction("About", self)
        action_about.triggered.connect(
            lambda: QMessageBox.about(self, f"About {APP_NAME}", ABOUT)
        )
        help_menu.addAction(action_about)

    def stop_all_activity(self) -> None:
        self.tab_sweep._stop()
        self.tab_console._stop()
        self.tab_music._stop_reacting()
        if hasattr(self.tab_lab, "_lab_stop"):
            self.tab_lab._lab_stop()
        self.ctx.log("info", "Stopped all running activity")
        self.statusBar().showMessage("Stopped all running activity", 4000)

    def _toggle_theme(self) -> None:
        self.ctx.settings.dark_theme = not self.ctx.settings.dark_theme
        self.setStyleSheet(theme.stylesheet(self.ctx.settings.dark_theme))

    def _open_data_folder(self) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(paths.data_dir())))

    # --- lifecycle --------------------------------------------------------

    def _tick(self) -> None:
        self.tab_events.drain()
        self.tab_connect.refresh()
        connected = len(self.ctx.ble.connected_addresses())
        total = len(self.ctx.ble.devices)
        self.lbl_devices.setText(f"  Strips: {connected}/{total}  ")
        self.lbl_frames.setText(
            f"  Frames sent: {self.ctx.ble.sent_frames}  failed: {self.ctx.ble.failed_frames}  "
        )

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self._heartbeat.stop()
        self.stop_all_activity()
        for tab in (self.tab_camera, self.tab_music):
            shutdown = getattr(tab, "shutdown", None)
            if shutdown is not None:
                shutdown()

        settings = self.ctx.settings
        settings.window_geometry = bytes(self.saveGeometry().toBase64()).decode()
        settings.save()
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
