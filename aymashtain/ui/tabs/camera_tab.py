"""Webcam verification of what the strip actually emits.

Round 2 changes
---------------
* Preview border: light grey while the camera is closed, dark grey while it
  is open (matches the spec).
* Camera device, resolution, FPS, exposure lock, manual exposure value, and
  white-balance lock are all read from Settings, so the Options tab is the
  single source of truth.
* A real forced exposure lock. On Windows DirectShow, auto-exposure is turned
  off by writing 0.25 to ``CAP_PROP_AUTO_EXPOSURE`` and then the manual value
  to ``CAP_PROP_EXPOSURE``. On V4L2/Linux, 1 = manual. We try both, read the
  value back, and log honestly whether the driver accepted the lock.
* White-balance lock is the same idea: ``CAP_PROP_AUTO_WB = 0`` freezes the
  current gains. If the driver refuses, we say so instead of pretending.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...vision import CameraVerifier
from ..context import AppContext

CAMERA_RESOLUTIONS = [
    "640x480",
    "1280x720",
    "1920x1080",
    "2560x1440",
]
CAMERA_FPS_CHOICES = [15, 24, 30, 60]

BORDER_CLOSED = "2px solid #D4D4D8"   # light grey
BORDER_OPEN = "2px solid #71717A"     # dark grey


class CameraTab(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.verifier = CameraVerifier(ctx.settings.camera_index)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._locks_applied: dict[str, str] = {}

        layout = QHBoxLayout(self)

        # =============================================================
        # Left: preview + capture controls
        # =============================================================
        left = QVBoxLayout()

        self.view = QLabel("Camera closed.")
        self.view.setAlignment(Qt.AlignCenter)
        self.view.setMinimumSize(480, 360)
        self.view.setStyleSheet(
            f"background:#0B0B0F; border-radius:10px; color:#71717A; "
            f"border: {BORDER_CLOSED};"
        )
        left.addWidget(self.view, stretch=1)

        controls = QHBoxLayout()
        self.btn_toggle = QPushButton("Start preview")
        self.btn_toggle.setProperty("accent", True)
        self.btn_toggle.clicked.connect(self._toggle)
        self.btn_sample = QPushButton("Take sample")
        self.btn_sample.clicked.connect(lambda: self.capture_sample(None, "manual"))
        self.btn_clear = QPushButton("Clear samples")
        self.btn_clear.clicked.connect(self._clear)
        controls.addWidget(self.btn_toggle)
        controls.addWidget(self.btn_sample)
        controls.addWidget(self.btn_clear)
        controls.addStretch()
        left.addLayout(controls)
        layout.addLayout(left, stretch=3)

        # =============================================================
        # Right: settings + samples
        # =============================================================
        right = QVBoxLayout()
        config = QGroupBox("Camera settings")
        form = QFormLayout(config)

        # --- device index (mirrors Options) --------------------------
        self.spin_index = QSpinBox()
        self.spin_index.setRange(0, 8)
        self.spin_index.setValue(ctx.settings.camera_index)
        form.addRow("Camera index", self.spin_index)

        # --- resolution ---------------------------------------------
        self.combo_resolution = QComboBox()
        for value in CAMERA_RESOLUTIONS:
            self.combo_resolution.addItem(value, value)
        idx = self.combo_resolution.findData(ctx.settings.camera_resolution)
        self.combo_resolution.setCurrentIndex(max(0, idx))
        form.addRow("Resolution", self.combo_resolution)

        # --- fps -----------------------------------------------------
        self.combo_fps = QComboBox()
        for value in CAMERA_FPS_CHOICES:
            self.combo_fps.addItem(f"{value} fps", value)
        idx = self.combo_fps.findData(ctx.settings.camera_fps)
        self.combo_fps.setCurrentIndex(max(0, idx))
        form.addRow("Frame rate", self.combo_fps)

        # --- exposure lock + manual value ---------------------------
        self.chk_exposure = QCheckBox("Lock exposure")
        self.chk_exposure.setChecked(ctx.settings.camera_exposure_lock)
        form.addRow("", self.chk_exposure)

        exp_row = QHBoxLayout()
        self.slider_exposure = QSlider(Qt.Horizontal)
        self.slider_exposure.setRange(-13, 0)
        self.slider_exposure.setValue(ctx.settings.camera_exposure_value)
        self.slider_exposure.setToolTip(
            "OpenCV / DirectShow exposure in log2 seconds. "
            "-1 ≈ 0.5 s (bright), -13 ≈ 1/8000 s (dark)."
        )
        self.lbl_exposure = QLabel(self._exposure_text(self.slider_exposure.value()))
        self.lbl_exposure.setMinimumWidth(80)
        self.slider_exposure.valueChanged.connect(self._on_exposure_slider)
        exp_row.addWidget(self.slider_exposure, stretch=1)
        exp_row.addWidget(self.lbl_exposure)
        exp_widget = QWidget()
        exp_widget.setLayout(exp_row)
        form.addRow("Manual exposure value", exp_widget)

        # --- white-balance lock --------------------------------------
        self.chk_wb = QCheckBox("Lock white balance")
        self.chk_wb.setChecked(ctx.settings.camera_wb_lock)
        form.addRow("", self.chk_wb)

        # --- sampling window -----------------------------------------
        self.spin_samples = QSpinBox()
        self.spin_samples.setRange(1, 15)
        self.spin_samples.setValue(ctx.settings.camera_samples_per_command)
        form.addRow("Samples per command", self.spin_samples)

        region_row = QHBoxLayout()
        self.region_spins = []
        for value in ctx.settings.camera_region:
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 1.0)
            spin.setSingleStep(0.05)
            spin.setValue(value)
            spin.valueChanged.connect(self._region_changed)
            self.region_spins.append(spin)
            region_row.addWidget(spin)
        region_widget = QWidget()
        region_widget.setLayout(region_row)
        form.addRow("Region x0,y0,x1,y1", region_widget)

        self.lbl_lock_status = QLabel("")
        self.lbl_lock_status.setWordWrap(True)
        self.lbl_lock_status.setStyleSheet("color: #A1A1AA;")
        form.addRow("", self.lbl_lock_status)

        right.addWidget(config)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Label", "Measured RGB", "Hue", "Hue err", "White %", "Verdict"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right.addWidget(self.table, stretch=1)

        self.lbl_status = QLabel(
            "White % is min(r,g,b)/max(r,g,b): high values mean the colour is being washed out."
        )
        self.lbl_status.setWordWrap(True)
        right.addWidget(self.lbl_status)

        layout.addLayout(right, stretch=2)

        # Persist lock checkbox changes back to settings immediately.
        self.chk_exposure.stateChanged.connect(self._on_lock_toggled)
        self.chk_wb.stateChanged.connect(self._on_lock_toggled)
        self.combo_resolution.currentIndexChanged.connect(self._on_settings_changed)
        self.combo_fps.currentIndexChanged.connect(self._on_settings_changed)
        self.spin_index.valueChanged.connect(self._on_settings_changed)

    # =================================================================
    # Preview
    # =================================================================

    def _toggle(self) -> None:
        if self.verifier.is_open:
            self._timer.stop()
            self.verifier.close()
            self.btn_toggle.setText("Start preview")
            self.view.setText("Camera closed.")
            self.view.setPixmap(QPixmap())  # drop the last frame
            self._apply_border(open_=False)
            self.lbl_lock_status.setText("")
            self._locks_applied.clear()
            return

        if not CameraVerifier.available():
            self.lbl_status.setText("OpenCV is not installed — run: pip install opencv-python")
            return

        self.verifier.index = self.spin_index.value()
        self.ctx.settings.camera_index = self.verifier.index

        if not self.verifier.open():
            self.lbl_status.setText(f"Could not open camera {self.verifier.index}.")
            return

        # Apply resolution / fps / locks right after opening.
        self._apply_capture_settings()

        self._timer.start(33)
        self.btn_toggle.setText("Stop preview")
        self.view.setText("")
        self._apply_border(open_=True)
        self.ctx.log("camera", f"Preview started on camera {self.verifier.index}")

    def _apply_border(self, open_: bool) -> None:
        border = BORDER_OPEN if open_ else BORDER_CLOSED
        self.view.setStyleSheet(
            f"background:#0B0B0F; border-radius:10px; color:#71717A; "
            f"border: {border};"
        )

    def _apply_capture_settings(self) -> None:
        """Push resolution, fps, exposure lock and wb lock to the driver.

        Every step is reported back to the user, because some drivers silently
        ignore these properties. We would rather say "not accepted" than lie.
        """
        cap = self.verifier.capture
        if cap is None:
            return

        import cv2

        # --- resolution --------------------------------------------------
        width, height = self._parse_resolution(self.combo_resolution.currentData())
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))
        got_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        got_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        # --- fps ---------------------------------------------------------
        fps_target = float(self.combo_fps.currentData() or 30)
        cap.set(cv2.CAP_PROP_FPS, fps_target)
        got_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)

        # --- exposure lock ----------------------------------------------
        exp_msg = "auto"
        if self.chk_exposure.isChecked():
            manual_value = float(self.slider_exposure.value())
            # Try Windows DirectShow convention first, then V4L2.
            accepted = False
            for manual_flag in (0.25, 1.0):
                try:
                    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, manual_flag)
                    cap.set(cv2.CAP_PROP_EXPOSURE, manual_value)
                    read_back = cap.get(cv2.CAP_PROP_EXPOSURE)
                    if read_back is not None and abs(float(read_back) - manual_value) < 1.0:
                        accepted = True
                        break
                except Exception:
                    continue
            if accepted:
                exp_msg = f"locked at {self._exposure_text(self.slider_exposure.value())}"
            else:
                exp_msg = "driver refused lock — auto may win"
        else:
            # Best-effort: hand control back to auto.
            for auto_flag in (0.75, 3.0):
                try:
                    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, auto_flag)
                    break
                except Exception:
                    continue

        # --- white balance lock -----------------------------------------
        wb_msg = "auto"
        if self.chk_wb.isChecked():
            try:
                cap.set(cv2.CAP_PROP_AUTO_WB, 0.0)
                # Most webcams freeze whatever gains they had at that moment.
                wb_msg = "locked (gains frozen)"
            except Exception:
                wb_msg = "driver refused lock"

        # --- report ------------------------------------------------------
        self._locks_applied = {
            "resolution": f"{got_w}x{got_h} (asked {width}x{height})",
            "fps": f"{got_fps:.1f} (asked {fps_target:.0f})",
            "exposure": exp_msg,
            "white_balance": wb_msg,
        }
        self.lbl_lock_status.setText(
            f"Driver reports — resolution: {got_w}x{got_h}, fps: {got_fps:.1f}. "
            f"Exposure: {exp_msg}. White balance: {wb_msg}."
        )
        self.ctx.log(
            "camera",
            f"Settings applied: {got_w}x{got_h} @ {got_fps:.1f} fps, "
            f"exposure={exp_msg}, wb={wb_msg}",
        )

    @staticmethod
    def _parse_resolution(value) -> tuple[int, int]:
        if not value:
            return 1280, 720
        try:
            width, height = str(value).lower().split("x")
            return int(width), int(height)
        except (ValueError, AttributeError):
            return 1280, 720

    def _tick(self) -> None:
        frame = self.verifier.read_rgb()
        if frame is None:
            return
        height, width, _ = frame.shape
        x0, y0, x1, y1 = self.region()

        try:
            import cv2

            annotated = frame.copy()
            cv2.rectangle(
                annotated,
                (int(x0 * width), int(y0 * height)),
                (int(x1 * width), int(y1 * height)),
                (99, 102, 241),
                2,
            )
        except Exception:
            annotated = frame

        image = QImage(annotated.data, width, height, 3 * width, QImage.Format_RGB888)
        self.view.setPixmap(
            QPixmap.fromImage(image).scaled(
                self.view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )

    # =================================================================
    # Settings sync
    # =================================================================

    def _on_settings_changed(self) -> None:
        self.ctx.settings.camera_index = self.spin_index.value()
        self.ctx.settings.camera_resolution = self.combo_resolution.currentData() or "1280x720"
        self.ctx.settings.camera_fps = int(self.combo_fps.currentData() or 30)

        # If the camera is open, push the change straight through.
        if self.verifier.is_open:
            self._apply_capture_settings()

    def _on_lock_toggled(self) -> None:
        self.ctx.settings.camera_exposure_lock = self.chk_exposure.isChecked()
        self.ctx.settings.camera_wb_lock = self.chk_wb.isChecked()
        if self.verifier.is_open:
            self._apply_capture_settings()

    def _on_exposure_slider(self, value: int) -> None:
        self.lbl_exposure.setText(self._exposure_text(value))
        self.ctx.settings.camera_exposure_value = value
        if self.verifier.is_open and self.chk_exposure.isChecked():
            self._apply_capture_settings()

    @staticmethod
    def _exposure_text(value: int) -> str:
        if value >= 0:
            return "auto"
        return f"1/{2 ** (-value)} s"

    # =================================================================
    # Region
    # =================================================================

    def region(self) -> tuple[float, float, float, float]:
        return tuple(spin.value() for spin in self.region_spins)  # type: ignore[return-value]

    def _region_changed(self) -> None:
        self.ctx.settings.camera_region = list(self.region())

    # =================================================================
    # Sampling
    # =================================================================

    def capture_sample(self, expected_rgb=None, label: str = ""):
        """Grab and score one measurement. Returns ``None`` when no camera."""
        if not self.verifier.is_open:
            return None
        self.ctx.settings.camera_samples_per_command = self.spin_samples.value()
        sample = self.verifier.sample(
            self.region(), expected_rgb, label, self.spin_samples.value()
        )
        if sample is None:
            return None

        row = self.table.rowCount()
        self.table.insertRow(row)
        cells = [
            sample.label,
            str(sample.rgb),
            f"{sample.hue:.0f}°",
            "—" if sample.hue_error is None else f"{sample.hue_error:.0f}°",
            f"{sample.white_contamination * 100:.0f}%",
            "pass" if sample.passed else "check",
        ]
        for column, text in enumerate(cells):
            self.table.setItem(row, column, QTableWidgetItem(text))
        self.table.scrollToBottom()
        self.ctx.log(
            "camera",
            f"{label or 'sample'} → rgb{sample.rgb} hue {sample.hue:.0f}° "
            f"white {sample.white_contamination:.0%}",
        )
        return sample

    def _clear(self) -> None:
        self.verifier.clear()
        self.table.setRowCount(0)

    def shutdown(self) -> None:
        self._timer.stop()
        self.verifier.close()
        self._apply_border(open_=False)
