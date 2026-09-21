"""Live event log with filtering and a user-facing export.

Round 2 cleanup
---------------
* One "Export log…" button replaces the old separate "Export CSV…" and
  "Export JSON…" pair. The file dialog lets the user pick the format by
  choosing the extension.
* The log file path is never shown or written to the event log. After a
  successful save the status label just says "Log exported".
* The default filename uses the Options tab's save_location. If that is
  empty it falls back to the app data folder, never the project root.
* The internal session log (auto-saved to the logs folder on close) is
  separate from this user-facing export and is not exposed on this tab.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ... import paths
from ..context import AppContext

KINDS = ["info", "ble", "send", "error", "camera", "audio", "sweep"]


class EventsTab(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self._rows: list = []

        layout = QVBoxLayout(self)

        # --- filter row ---------------------------------------------------
        filters = QHBoxLayout()
        self.checks: dict[str, QCheckBox] = {}
        for kind in KINDS:
            check = QCheckBox(kind)
            check.setChecked(True)
            check.stateChanged.connect(self._reload)
            self.checks[kind] = check
            filters.addWidget(check)
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("Filter text…")
        self.edit_search.textChanged.connect(self._reload)
        filters.addWidget(self.edit_search, stretch=1)
        layout.addLayout(filters)

        # --- table --------------------------------------------------------
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Time", "Kind", "Source", "Message"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.table, stretch=1)

        # --- action row ---------------------------------------------------
        actions = QHBoxLayout()

        btn_export = QPushButton("Export log…")
        btn_export.setProperty("accent", True)
        btn_export.setToolTip(
            "Save the visible events to a file. CSV for spreadsheets, "
            "JSON for bug reports."
        )
        btn_export.clicked.connect(self._export)
        actions.addWidget(btn_export)

        btn_clear = QPushButton("Clear view")
        btn_clear.clicked.connect(self._clear_view)
        actions.addWidget(btn_clear)

        actions.addStretch()

        self.lbl_counts = QLabel("0 events")
        actions.addWidget(self.lbl_counts)

        layout.addLayout(actions)

    # ------------------------------------------------------------------
    # Live drain
    # ------------------------------------------------------------------

    def drain(self) -> None:
        new_events = self.ctx.bus.drain()
        if not new_events:
            return
        self._rows.extend(new_events)
        if len(self._rows) > 5000:
            # Keep the most recent slice so memory stays bounded.
            del self._rows[:1000]
        self._reload()

    def _reload(self) -> None:
        needle = self.edit_search.text().lower()
        enabled = {kind for kind, check in self.checks.items() if check.isChecked()}
        visible = [
            event
            for event in self._rows
            if event.kind in enabled
            and (not needle or needle in event.message.lower())
        ]
        self.table.setRowCount(len(visible))
        for row, event in enumerate(visible):
            for column, text in enumerate(
                [event.timestamp, event.kind, event.source, event.message]
            ):
                self.table.setItem(row, column, QTableWidgetItem(text))
        self.table.scrollToBottom()
        self.lbl_counts.setText(f"{len(visible)} / {len(self._rows)} events")

    def _clear_view(self) -> None:
        self._rows.clear()
        self._reload()

    # ------------------------------------------------------------------
    # User-facing export
    # ------------------------------------------------------------------

    def _export(self) -> None:
        events = self.ctx.bus.history()
        if not events:
            QMessageBox.information(
                self, "Export log", "There is nothing to export yet."
            )
            return

        default_dir = self.ctx.settings.save_location.strip() or str(paths.data_dir())
        default_name = f"aymashtain_log_{datetime.now():%Y%m%d_%H%M%S}.csv"
        default_path = str(Path(default_dir) / default_name)

        chosen, _ = QFileDialog.getSaveFileName(
            self,
            "Export log",
            default_path,
            "Log file (*.csv);;JSON (*.json);;All files (*)",
        )
        if not chosen:
            return

        target = Path(chosen)
        try:
            if target.suffix.lower() == ".json":
                self._write_json(target, events)
            else:
                # Force a .csv extension when the user did not supply one.
                if target.suffix.lower() not in (".csv", ".txt"):
                    target = target.with_suffix(".csv")
                self._write_csv(target, events)
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Export log",
                f"Could not save the log:\n{exc}",
            )
            self.ctx.log("error", f"Log export failed: {type(exc).__name__}")
            return

        # Deliberately no path. The user already chose the location in the
        # save dialog; the log should not repeat it back to them.
        self.ctx.log("info", f"Log exported ({len(events)} events)")
        self.lbl_counts.setText(f"Exported {len(events)} events.")

    @staticmethod
    def _write_csv(path: Path, events) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "kind", "source", "message"])
            for event in events:
                writer.writerow(
                    [event.timestamp, event.kind, event.source, event.message]
                )

    @staticmethod
    def _write_json(path: Path, events) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(
                [
                    {
                        "timestamp": event.timestamp,
                        "kind": event.kind,
                        "source": event.source,
                        "message": event.message,
                    }
                    for event in events
                ],
                handle,
                indent=2,
            )
