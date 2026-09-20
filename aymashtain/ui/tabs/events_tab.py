"""Live event log with filtering and export."""

from __future__ import annotations

import csv
import json

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..context import AppContext

KINDS = ["info", "ble", "send", "error", "camera", "audio", "sweep"]


class EventsTab(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self._rows: list = []

        layout = QVBoxLayout(self)

        filters = QHBoxLayout()
        self.checks = {}
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

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Time", "Kind", "Source", "Message"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.table, stretch=1)

        actions = QHBoxLayout()
        btn_export_csv = QPushButton("Export CSV…")
        btn_export_csv.clicked.connect(lambda: self._export("csv"))
        btn_export_json = QPushButton("Export JSON…")
        btn_export_json.clicked.connect(lambda: self._export("json"))
        btn_clear = QPushButton("Clear view")
        btn_clear.clicked.connect(lambda: (self._rows.clear(), self._reload()))
        actions.addWidget(btn_export_csv)
        actions.addWidget(btn_export_json)
        actions.addWidget(btn_clear)
        actions.addStretch()
        self.lbl_counts = QLabel("0 events")
        actions.addWidget(self.lbl_counts)
        layout.addLayout(actions)

    def drain(self) -> None:
        new_events = self.ctx.bus.drain()
        if not new_events:
            return
        self._rows.extend(new_events)
        if len(self._rows) > 5000:
            del self._rows[:1000]
        self._reload()

    def _reload(self) -> None:
        needle = self.edit_search.text().lower()
        enabled = {kind for kind, check in self.checks.items() if check.isChecked()}
        visible = [
            event
            for event in self._rows
            if event.kind in enabled and (not needle or needle in event.message.lower())
        ]
        self.table.setRowCount(len(visible))
        for row, event in enumerate(visible):
            for column, text in enumerate(
                [event.timestamp, event.kind, event.source, event.message]
            ):
                self.table.setItem(row, column, QTableWidgetItem(text))
        self.table.scrollToBottom()
        self.lbl_counts.setText(f"{len(visible)} / {len(self._rows)} events")

    def _export(self, fmt: str) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export events", f"events.{fmt}", f"{fmt.upper()} (*.{fmt})"
        )
        if not path:
            return
        events = self.ctx.bus.history()
        if fmt == "csv":
            with open(path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["timestamp", "kind", "source", "message"])
                for event in events:
                    writer.writerow([event.timestamp, event.kind, event.source, event.message])
        else:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump([event.__dict__ for event in events], handle, indent=2)
        self.ctx.log("info", f"Exported {len(events)} events to {path}")
