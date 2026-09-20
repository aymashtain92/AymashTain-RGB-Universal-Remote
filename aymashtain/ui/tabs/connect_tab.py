"""Scan, connect and manage LED controllers."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..context import AppContext

STATUS_COLORS = {"connected": "#10B981", "connecting": "#F59E0B", "disconnected": "#EF4444"}


class ConnectTab(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx

        layout = QVBoxLayout(self)

        controls = QHBoxLayout()
        self.btn_scan = QPushButton("Scan for devices")
        self.btn_scan.setProperty("accent", True)
        self.btn_scan.clicked.connect(self._scan)
        self.spin_scan = QSpinBox()
        self.spin_scan.setRange(2, 30)
        self.spin_scan.setValue(int(ctx.settings.scan_seconds))
        self.spin_scan.setSuffix(" s")
        self.chk_only_candidates = QCheckBox("Only likely LED controllers")
        self.chk_only_candidates.setChecked(True)
        self.chk_only_candidates.stateChanged.connect(self._refresh_scan_table)
        self.chk_auto_reconnect = QCheckBox("Auto-reconnect")
        self.chk_auto_reconnect.setChecked(ctx.settings.auto_reconnect)
        self.chk_auto_reconnect.stateChanged.connect(self._toggle_reconnect)

        controls.addWidget(self.btn_scan)
        controls.addWidget(QLabel("Duration"))
        controls.addWidget(self.spin_scan)
        controls.addWidget(self.chk_only_candidates)
        controls.addWidget(self.chk_auto_reconnect)
        controls.addStretch()
        layout.addLayout(controls)

        scan_box = QGroupBox("Discovered devices")
        scan_layout = QVBoxLayout(scan_box)
        self.table_scan = QTableWidget(0, 4)
        self.table_scan.setHorizontalHeaderLabels(["Name", "Address", "RSSI", "Likely LED"])
        self.table_scan.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_scan.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_scan.doubleClicked.connect(self._connect_selected)
        scan_layout.addWidget(self.table_scan)

        scan_actions = QHBoxLayout()
        btn_add = QPushButton("Connect selected")
        btn_add.clicked.connect(self._connect_selected)
        btn_save = QPushButton("Remember selected")
        btn_save.clicked.connect(self._remember_selected)
        scan_actions.addWidget(btn_add)
        scan_actions.addWidget(btn_save)
        scan_actions.addStretch()
        scan_layout.addLayout(scan_actions)
        layout.addWidget(scan_box)

        known_box = QGroupBox("My strips")
        known_layout = QVBoxLayout(known_box)
        self.table_known = QTableWidget(0, 4)
        self.table_known.setHorizontalHeaderLabels(["Name", "Address", "Status", "Write char"])
        self.table_known.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_known.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        known_layout.addWidget(self.table_known)

        known_actions = QHBoxLayout()
        for label, slot, accent in (
            ("Connect all", self._connect_all, True),
            ("Connect selected", self._connect_known_selected, False),
            ("Identify (blink)", self._identify_selected, False),
            ("Disconnect all", self._disconnect_all, False),
            ("Forget selected", self._forget_selected, False),
        ):
            button = QPushButton(label)
            button.setProperty("accent", accent)
            button.clicked.connect(slot)
            known_actions.addWidget(button)
        known_actions.addStretch()
        known_layout.addLayout(known_actions)
        layout.addWidget(known_box, stretch=1)

        self._scan_results = []
        self.refresh()

    # --- scanning ---------------------------------------------------------

    def _scan(self) -> None:
        self.btn_scan.setEnabled(False)
        self.btn_scan.setText("Scanning…")
        self.ctx.settings.scan_seconds = float(self.spin_scan.value())
        self.ctx.run(self._scan_async())

    async def _scan_async(self) -> None:
        try:
            self._scan_results = await self.ctx.ble.scan(self.ctx.settings.scan_seconds)
            self._refresh_scan_table()
        finally:
            self.btn_scan.setEnabled(True)
            self.btn_scan.setText("Scan for devices")

    def _refresh_scan_table(self) -> None:
        only_candidates = self.chk_only_candidates.isChecked()
        rows = [r for r in self._scan_results if r.is_candidate or not only_candidates]
        self.table_scan.setRowCount(len(rows))
        for row, result in enumerate(rows):
            self.table_scan.setItem(row, 0, QTableWidgetItem(result.name))
            self.table_scan.setItem(row, 1, QTableWidgetItem(result.address))
            self.table_scan.setItem(
                row, 2, QTableWidgetItem("—" if result.rssi is None else f"{result.rssi} dBm")
            )
            self.table_scan.setItem(row, 3, QTableWidgetItem("yes" if result.is_candidate else ""))

    def _selected_scan_rows(self) -> list[tuple[str, str]]:
        out = []
        for index in self.table_scan.selectionModel().selectedRows():
            name = self.table_scan.item(index.row(), 0).text()
            address = self.table_scan.item(index.row(), 1).text()
            out.append((address, name))
        return out

    def _connect_selected(self) -> None:
        for address, name in self._selected_scan_rows():
            self._remember(address, name)
            self.ctx.run(self.ctx.ble.connect(address, name))
        self.refresh()

    def _remember_selected(self) -> None:
        for address, name in self._selected_scan_rows():
            self._remember(address, name)
        self.refresh()

    def _remember(self, address: str, name: str) -> None:
        self.ctx.db.upsert_device(address, name)
        known = {entry["address"] for entry in self.ctx.settings.known_devices}
        if address not in known:
            self.ctx.settings.known_devices.append({"address": address, "name": name})
        self.ctx.ble.track(address, name)

    # --- known devices ----------------------------------------------------

    def refresh(self) -> None:
        for entry in self.ctx.settings.known_devices:
            self.ctx.ble.track(entry["address"], entry.get("name", ""))

        states = list(self.ctx.ble.devices.values())
        self.table_known.setRowCount(len(states))
        for row, state in enumerate(states):
            self.table_known.setItem(row, 0, QTableWidgetItem(state.name))
            self.table_known.setItem(row, 1, QTableWidgetItem(state.address))
            status_item = QTableWidgetItem(state.status)
            status_item.setForeground(Qt.GlobalColor.white)
            status_item.setToolTip(f"failures: {state.failures}")
            self.table_known.setItem(row, 2, status_item)
            self.table_known.setItem(row, 3, QTableWidgetItem(state.char_uuid))
            color = STATUS_COLORS.get(state.status, "#A1A1AA")
            self.table_known.item(row, 2).setData(Qt.ToolTipRole, state.status)
            self.table_known.item(row, 0).setData(Qt.UserRole, state.address)
            self.table_known.item(row, 2).setForeground(_brush(color))

    def _selected_known(self) -> list[str]:
        return [
            self.table_known.item(index.row(), 1).text()
            for index in self.table_known.selectionModel().selectedRows()
        ]

    def _connect_all(self) -> None:
        for address, state in self.ctx.ble.devices.items():
            self.ctx.run(self.ctx.ble.connect(address, state.name))

    def _connect_known_selected(self) -> None:
        for address in self._selected_known():
            state = self.ctx.ble.devices.get(address)
            self.ctx.run(self.ctx.ble.connect(address, state.name if state else ""))

    def _identify_selected(self) -> None:
        for address in self._selected_known():
            self.ctx.run(self.ctx.ble.identify(address))

    def _disconnect_all(self) -> None:
        self.ctx.run(self.ctx.ble.disconnect_all())

    def _forget_selected(self) -> None:
        for address in self._selected_known():
            self.ctx.run(self.ctx.ble.disconnect(address))
            self.ctx.ble.devices.pop(address, None)
            self.ctx.db.forget_device(address)
            self.ctx.settings.known_devices = [
                entry for entry in self.ctx.settings.known_devices if entry["address"] != address
            ]
        self.refresh()

    def _toggle_reconnect(self) -> None:
        enabled = self.chk_auto_reconnect.isChecked()
        self.ctx.settings.auto_reconnect = enabled
        self.ctx.ble.auto_reconnect = enabled


def _brush(color: str):
    from PySide6.QtGui import QBrush, QColor

    return QBrush(QColor(color))
