"""Automated parameter sweeps, optionally verified with the camera."""

from __future__ import annotations

import asyncio

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...protocol import EFFECTS, encode_brightness, encode_color_hs, encode_effect, hs_to_rgb
from ..context import AppContext

MODES = {
    "Hue (0-359°)": "hue",
    "Saturation (0-100%)": "saturation",
    "Brightness (0-100%)": "brightness",
    "Effect bytes": "effect",
}


class SweepTab(QWidget):
    def __init__(self, ctx: AppContext, camera_tab=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.camera_tab = camera_tab
        self._running = False

        layout = QVBoxLayout(self)

        config = QGroupBox("Sweep configuration")
        form = QFormLayout(config)
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(MODES.keys())
        self.spin_steps = QSpinBox()
        self.spin_steps.setRange(2, 360)
        self.spin_steps.setValue(ctx.settings.sweep_steps)
        self.spin_gap = QSpinBox()
        self.spin_gap.setRange(50, 5000)
        self.spin_gap.setValue(ctx.settings.sweep_step_ms)
        self.spin_gap.setSuffix(" ms")
        self.spin_settle = QSpinBox()
        self.spin_settle.setRange(0, 3000)
        self.spin_settle.setValue(ctx.settings.sweep_settle_ms)
        self.spin_settle.setSuffix(" ms")
        self.chk_verify = QCheckBox("Verify each step with the camera")
        form.addRow("Sweep", self.combo_mode)
        form.addRow("Steps", self.spin_steps)
        form.addRow("Gap between steps", self.spin_gap)
        form.addRow("Settle before sampling", self.spin_settle)
        form.addRow("", self.chk_verify)
        layout.addWidget(config)

        actions = QHBoxLayout()
        self.btn_start = QPushButton("Start sweep")
        self.btn_start.setProperty("accent", True)
        self.btn_start.clicked.connect(self._start)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setProperty("danger", True)
        self.btn_stop.clicked.connect(self._stop)
        self.btn_stop.setEnabled(False)
        self.btn_export = QPushButton("Copy results as CSV")
        self.btn_export.clicked.connect(self._copy_csv)
        actions.addWidget(self.btn_start)
        actions.addWidget(self.btn_stop)
        actions.addWidget(self.btn_export)
        actions.addStretch()
        layout.addLayout(actions)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["#", "Value", "Frame", "Sent", "Measured RGB", "White %"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table, stretch=1)

        self.lbl_summary = QLabel("Idle.")
        layout.addWidget(self.lbl_summary)

    # --- run --------------------------------------------------------------

    def _start(self) -> None:
        if self._running:
            return
        self._running = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.table.setRowCount(0)
        self.ctx.settings.sweep_steps = self.spin_steps.value()
        self.ctx.settings.sweep_step_ms = self.spin_gap.value()
        self.ctx.settings.sweep_settle_ms = self.spin_settle.value()
        self.ctx.run(self._run())

    def _stop(self) -> None:
        self._running = False

    async def _run(self) -> None:
        mode = MODES[self.combo_mode.currentText()]
        steps = self.spin_steps.value()
        gap = self.spin_gap.value() / 1000.0
        settle = self.spin_settle.value() / 1000.0
        self.progress.setRange(0, steps)
        failures = 0

        try:
            for index in range(steps):
                if not self._running:
                    break
                value, frame, expected = self._frame_for(mode, index, steps)
                sent = await self.ctx.ble.send_hex_all(frame, f"sweep:{mode}")
                if sent == 0:
                    failures += 1

                measured = ""
                white = ""
                if self.chk_verify.isChecked() and self.camera_tab is not None:
                    if settle:
                        await asyncio.sleep(settle)
                    sample = self.camera_tab.capture_sample(expected, f"{mode}={value}")
                    if sample is not None:
                        measured = str(sample.rgb)
                        white = f"{sample.white_contamination * 100:.0f}%"

                self._add_row(index + 1, value, frame, sent, measured, white)
                self.progress.setValue(index + 1)
                self.ctx.log("sweep", f"[{index + 1}/{steps}] {frame} → {sent} device(s)")
                await asyncio.sleep(gap)
        finally:
            self._running = False
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.lbl_summary.setText(
                f"Finished {self.progress.value()}/{steps} steps, {failures} step(s) reached no device."
            )

    def _frame_for(self, mode: str, index: int, steps: int) -> tuple[str, str, tuple[int, int, int] | None]:
        if mode == "hue":
            hue = int(index * 360 / steps)
            return f"{hue}°", encode_color_hs(hue, 1.0), hs_to_rgb(hue, 1.0)
        if mode == "saturation":
            saturation = index / max(1, steps - 1)
            return f"{saturation:.0%}", encode_color_hs(0, saturation), hs_to_rgb(0, saturation)
        if mode == "brightness":
            level = index / max(1, steps - 1)
            return f"{level:.0%}", encode_brightness(level), None
        codes = list(EFFECTS)
        code = codes[index % len(codes)]
        return f"0x{code} {EFFECTS[code]}", encode_effect(code), None

    def _add_row(self, number: int, value: str, frame: str, sent: int, measured: str, white: str) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, text in enumerate(
            [str(number), value, frame, str(sent), measured, white]
        ):
            self.table.setItem(row, column, QTableWidgetItem(text))
        self.table.scrollToBottom()

    def _copy_csv(self) -> None:
        from PySide6.QtWidgets import QApplication

        lines = ["number,value,frame,sent,measured_rgb,white_pct"]
        for row in range(self.table.rowCount()):
            cells = [
                (self.table.item(row, column).text() if self.table.item(row, column) else "")
                for column in range(self.table.columnCount())
            ]
            lines.append(",".join(cell.replace(",", ";") for cell in cells))
        QApplication.clipboard().setText("\n".join(lines))
        self.lbl_summary.setText("Results copied to clipboard as CSV.")
