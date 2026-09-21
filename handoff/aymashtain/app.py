"""Application bootstrap: wiring, crash handling and the qasync event loop."""

from __future__ import annotations

import asyncio
import sys
import traceback

from . import APP_NAME, APP_VERSION, paths
from .ble import BleManager
from .config import Settings
from .events import EventBus, SessionLogger
from .storage import Database


def _install_excepthook(bus: EventBus) -> None:
    def hook(exc_type, exc_value, exc_tb) -> None:
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        bus.emit("error", f"Unhandled exception:\n{text}", "crash")
        try:
            (paths.data_dir() / "crash.log").write_text(text, encoding="utf-8")
        except OSError:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = hook


def build_context():
    from .ui.context import AppContext

    settings = Settings.load()
    logger = SessionLogger(retention_days=settings.log_retention_days)
    bus = EventBus(session_logger=logger)
    _install_excepthook(bus)

    db = Database()
    ble = BleManager(
        log=lambda kind, message: bus.emit(kind, message, "ble"),
        inter_device_delay_ms=settings.inter_device_delay_ms,
        write_retries=settings.write_retries,
        auto_reconnect=settings.auto_reconnect,
    )
    return AppContext(settings=settings, bus=bus, db=db, ble=ble)


def main(argv: list[str] | None = None) -> int:
    import qasync
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from .ui.main_window import MainWindow

    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    icon = paths.icon_file()
    if icon is not None:
        app.setWindowIcon(QIcon(str(icon)))

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    ctx = build_context()
    window = MainWindow(ctx)
    window.show()

    with loop:
        loop.run_forever()
    return 0
