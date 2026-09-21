# Original Path: aymashtain/ui/tabs/sweep_tab.py

"""Automated parameter sweeps, optionally verified with the camera.

Round 3 Phase 0 fixes
---------------------
* Brightness range is read *fresh on every step* directly from
  ``ctx.settings`` (was already doing this, but the range is now logged
  once per step when it changes, so a mid-run Options change is visible
  in the Events tab instead of silent).
* Sends go through ``ctx.resolve_targets()`` so the new multi-strip
  selection is honoured. The camera sample still runs once per step.
* Info line refreshes when Options changes the range -- ``sync_clamp_notice()``
  is wired from the main window.

Round 2 behaviour kept
----------------------
* Brightness sweeps run *within* the Options min/max range instead of
  sweeping 0..1 and getting clamped step by step. If Options says
  20%-80% and the user asked for 12 steps, they get twelve evenly-spaced
  points between 20% and 80%. Every step is useful; none are wasted.
"""

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

from ...protocol import (
    EFFECTS,
    encode_brightness,
    encode_color_hs,
    encode_effect,
    hs_to_rgb,
)
from ..context import AppContext

MODES = {
    "Hue (0-359 deg)": "hue",
    "Saturation (0-100%)": "saturation",
    "Brightness (0-100%)": "brightness",
    "Effect bytes": "effect",
}


class SweepTab(QWidget):
    def __init__(
        self, ctx: AppContext, camera_tab=None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.camera_tab = camera_tab
        self._running = False
        #: The brightness range (lo, hi) that was in force on the last
        #: step, so we can log a message only when it actually changes.
        self._last_range: tuple[int, int] | None = None

        layout = QVBoxLayout(self)

        # --- configuration ------------------------------------------------
        config = QGroupBox("Sweep configuration")
        form = QFormLayout(config)
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(MODES.keys())
        self.combo_mode.currentIndexChanged.connect(self._refresh_brightness_note)
        form.addRow("Sweep", self.combo_mode)

        self.spin_steps = QSpinBox()
        self.spin_steps.setRange(2, 360)
        self.spin_steps.setValue(ctx.settings.sweep_steps)
        form.addRow("Steps", self.spin_steps)

        self.spin_gap = QSpinBox()
        self.spin_gap.setRange(50, 5000)
        self.spin_gap.setValue(ctx.settings.sweep_step_ms)
        self.spin_gap.setSuffix(" ms")
        form.addRow("Gap between steps", self.spin_gap)

        self.spin_settle = QSpinBox()
        self.spin_settle.setRange(0, 3000)
        self.spin_settle.setValue(ctx.settings.sweep_settle_ms)
        self.spin_settle.setSuffix(" ms")
        form.addRow("Settle before sampling", self.spin_settle)

        self.chk_verify = QCheckBox("Verify each step with the camera")
        form.addRow("", self.chk_verify)

        self.lbl_brightness_note = QLabel("")
        self.lbl_brightness_note.setWordWrap(True)
        form.addRow("", self.lbl_brightness_note)

        layout.addWidget(config)

        # --- actions ------------------------------------------------------
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

        self._refresh_brightness_note()

    # ------------------------------------------------------------------
    # Info line
    # ------------------------------------------------------------------

    def _refresh_brightness_note(self) -> None:
        """Tell the user the range the brightness sweep will use."""
        if MODES.get(self.combo_mode.currentText()) != "brightness":
            self.lbl_brightness_note.setText("")
            return
        lo = self.ctx.settings.brightness_min
        hi = self.ctx.settings.brightness_max
        if hi < lo:
            lo, hi = hi, lo
        self.lbl_brightness_note.setText(
            f"Brightness sweep will run from {lo}% to {hi}%. "
            f"Change the range in the Options tab."
        )

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def _start(self) -> None:
        if self._running:
            return
        self._running = True
        self._last_range = None
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
                targets = self.ctx.resolve_targets()
                sent = await self.ctx.ble.send_hex_all(
                    frame, f"sweep:{mode}", addresses=targets
                )
                if sent == 0:
                    failures += 1

                measured = ""
                white = ""
                if self.chk_verify.isChecked() and self.camera_tab is not None:
                    if settle:
                        await asyncio.sleep(settle)
                    sample = self.camera_tab.capture_sample(
                        expected, f"{mode}={value}"
                    )
                    if sample is not None:
                        measured = str(sample.rgb)
                        white = f"{sample.white_contamination * 100:.0f}%"

                self._add_row(index + 1, value, frame, sent, measured, white)
                self.progress.setValue(index + 1)
                self.ctx.log(
                    "sweep", f"[{index + 1}/{steps}] {frame} -> {sent} device(s)"
                )
                await asyncio.sleep(gap)
        finally:
            self._running = False
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.lbl_summary.setText(
                f"Finished {self.progress.value()}/{steps} steps, "
                f"{failures} step(s) reached no device."
            )

    def _frame_for(
        self, mode: str, index: int, steps: int
    ) -> tuple[str, str, tuple[int, int, int] | None]:
        if mode == "hue":
            hue = int(index * 360 / steps)
            return f"{hue} deg", encode_color_hs(hue, 1.0), hs_to_rgb(hue, 1.0)

        if mode == "saturation":
            saturation = index / max(1, steps - 1)
            return (
                f"{saturation:.0%}",
                encode_color_hs(0, saturation),
                hs_to_rgb(0, saturation),
            )

        if mode == "brightness":
            # Read the range fresh from settings on every single step.
            # The sweep must follow a mid-run Options change, so we never
            # cache these values across the loop.
            lo_int = self.ctx.settings.brightness_min
            hi_int = self.ctx.settings.brightness_max
            if hi_int < lo_int:
                lo_int, hi_int = hi_int, lo_int

            # Log when the range changes mid-run so it shows up in Events.
            current_range = (lo_int, hi_int)
            if self._last_range != current_range:
                self.ctx.log(
                    "sweep",
                    f"Brightness range now {lo_int}%-{hi_int}%",
                )
                self._last_range = current_range

            lo = lo_int / 100.0
            hi = hi_int / 100.0
            t = index / max(1, steps - 1)
            level = lo + (hi - lo) * t
            # Belt-and-braces: clamp_brightness re-reads settings in case
            # they changed between the read above and the encode below.
            level = self.ctx.settings.clamp_brightness(level)
            return f"{level:.0%}", encode_brightness(level), None

        # Effect bytes
        codes = list(EFFECTS)
        code = codes[index % len(codes)]
        return f"0x{code} {EFFECTS[code]}", encode_effect(code), None

    def _add_row(
        self, number: int, value: str, frame: str, sent: int, measured: str, white: str
    ) -> None:
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
                (
                    self.table.item(row, column).text()
                    if self.table.item(row, column)
                    else ""
                )
                for column in range(self.table.columnCount())
            ]
            lines.append(",".join(cell.replace(",", ";") for cell in cells))
        QApplication.clipboard().setText("\n".join(lines))
        self.lbl_summary.setText("Results copied to clipboard as CSV.")

    # ------------------------------------------------------------------
    # External hooks
    # ------------------------------------------------------------------

    def sync_clamp_notice(self) -> None:
        """Called by the main window when Options changes the range."""
        self._refresh_brightness_note()
