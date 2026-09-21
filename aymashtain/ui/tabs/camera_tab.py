# Original Path: aymashtain/ui/tabs/camera_tab.py

"""Webcam verification of what the strip actually emits.

Round 3 Phase 1 fixes
---------------------
* **Backend picker.** A new "Capture backend" dropdown mirrors Options:
  Auto (try DSHOW, then MSMF, then default), DirectShow, Media
  Foundation. DSHOW is the only backend that reliably honours manual
  exposure / WB on most Windows webcams, but MSMF is faster, so both
  are offered.
* **Capture size, not "Resolution".** The row is renamed because the
  value is the size of the frames the driver hands back, not the
  sensor's optical resolution. The list matches Options.
* **Honest exposure reporting.** The old code claimed "locked at X" as
  soon as the driver *accepted the write*. That is not the same as
  actually being locked -- several drivers accept the write and then
  keep running auto. We now read ``CAP_PROP_AUTO_EXPOSURE`` *and*
  ``CAP_PROP_EXPOSURE`` back and print what the driver actually reports,
  not what we asked for.
* **Honest WB reporting.** Same for white balance: read
  ``CAP_PROP_AUTO_WB`` back and say exactly what the driver returned.
* **Theme-aware borders.** The preview frame now uses colours that
  match the active theme, so light mode is legible too.

Round 2 behaviour kept
----------------------
* Preview border changes state between closed and open.
* Resolution, FPS, exposure lock and WB lock all read from Settings
  (Options is the single source of truth).
* Camera stays local-only. No uploads.
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

#: Same list as the Options tab, so the two dropdowns never disagree.
CAMERA_RESOLUTIONS = [
    "640x480",
    "800x600",
    "1280x720",
    "1600x1200",
    "1920x1080",
    "2560x1440",
    "3840x2160",
]
CAMERA_FPS_CHOICES = [15, 24, 30, 60]

CAMERA_BACKENDS: list[tuple[str, str]] = [
    ("auto", "Auto (try DSHOW, then MSMF)"),
    ("dshow", "DirectShow"),
    ("msmf", "Media Foundation"),
]

#: Preview border colours, resolved per theme at paint time.
DARK_BORDER_CLOSED = "2px solid #27272A"
DARK_BORDER_OPEN = "2px solid #4338CA"
LIGHT_BORDER_CLOSED = "2px solid #D4D4D8"
LIGHT_BORDER_OPEN = "2px solid #4F46E5"


class CameraTab(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.verifier = CameraVerifier(ctx.settings.camera_index)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._locks_applied: dict[str, str] = {}
        #: Populated by ``_apply_capture_settings`` for the info line.
        self._last_report: str = ""

        layout = QHBoxLayout(self)

        # =============================================================
        # Left: preview + capture controls
        # =============================================================
        left = QVBoxLayout()

        self.view = QLabel("Camera closed.")
        self.view.setAlignment(Qt.AlignCenter)
        self.view.setMinimumSize(480, 360)
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

        # --- backend --------------------------------------------------
        self.combo_backend = QComboBox()
        for value, label in CAMERA_BACKENDS:
            self.combo_backend.addItem(label, value)
        idx = self.combo_backend.findData(
            getattr(ctx.settings, "camera_backend", "auto")
        )
        self.combo_backend.setCurrentIndex(max(0, idx))
        form.addRow("Capture backend", self.combo_backend)

        # --- capture size (was "Resolution") -------------------------
        self.combo_resolution = QComboBox()
        for value in CAMERA_RESOLUTIONS:
            self.combo_resolution.addItem(value, value)
        idx = self.combo_resolution.findData(ctx.settings.camera_resolution)
        self.combo_resolution.setCurrentIndex(max(0, idx))
        form.addRow("Capture size", self.combo_resolution)

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
            "White % is min(r,g,b)/max(r,g,b): high values mean the colour "
            "is being washed out."
        )
        self.lbl_status.setWordWrap(True)
        right.addWidget(self.lbl_status)

        layout.addLayout(right, stretch=2)

        # --- initial border paint ------------------------------------
        self._apply_border(open_=False)

        # --- persist changes back to Settings ------------------------
        self.chk_exposure.stateChanged.connect(self._on_lock_toggled)
        self.chk_wb.stateChanged.connect(self._on_lock_toggled)
        self.combo_resolution.currentIndexChanged.connect(self._on_settings_changed)
        self.combo_fps.currentIndexChanged.connect(self._on_settings_changed)
        self.combo_backend.currentIndexChanged.connect(self._on_settings_changed)
        self.spin_index.valueChanged.connect(self._on_settings_changed)

    # =================================================================
    # Theme-aware preview border
    # =================================================================

    def _border_css(self, open_: bool) -> str:
        dark = self.ctx.settings.resolved_dark()
        if dark:
            border = DARK_BORDER_OPEN if open_ else DARK_BORDER_CLOSED
            return (
                f"background:#0B0B0F; border-radius:10px; color:#71717A; "
                f"border: {border};"
            )
        border = LIGHT_BORDER_OPEN if open_ else LIGHT_BORDER_CLOSED
        return (
            f"background:#18181B; border-radius:10px; color:#A1A1AA; "
            f"border: {border};"
        )

    def _apply_border(self, open_: bool) -> None:
        self.view.setStyleSheet(self._border_css(open_))

    # =================================================================
    # Preview
    # =================================================================

    def _toggle(self) -> None:
        if self.verifier.is_open:
            self._timer.stop()
            self.verifier.close()
            self.btn_toggle.setText("Start preview")
            self.view.setText("Camera closed.")
            self.view.setPixmap(QPixmap())
            self._apply_border(open_=False)
            self.lbl_lock_status.setText("")
            self._locks_applied.clear()
            return

        if not CameraVerifier.available():
            self.lbl_status.setText(
                "OpenCV is not installed — run: pip install opencv-python"
            )
            return

        self.verifier.index = self.spin_index.value()
        self.ctx.settings.camera_index = self.verifier.index
        backend = self.combo_backend.currentData() or "auto"

        if not self._open_with_backend(backend):
            self.lbl_status.setText(
                f"Could not open camera {self.verifier.index} with backend "
                f"{backend}. Try a different backend or index."
            )
            return

        # Apply resolution / fps / locks right after opening.
        self._apply_capture_settings()

        self._timer.start(33)
        self.btn_toggle.setText("Stop preview")
        self.view.setText("")
        self._apply_border(open_=True)
        self.ctx.log(
            "camera",
            f"Preview started on camera {self.verifier.index} "
            f"(backend={backend})",
        )

    def _open_with_backend(self, backend: str) -> bool:
        """Open the camera, honouring the selected backend.

        ``auto`` tries DirectShow first, then Media Foundation, then the
        OpenCV default. Any failure falls through to the next option so a
        machine without one of the backends still works.
        """
        import cv2

        if backend == "dshow":
            order = ["dshow"]
        elif backend == "msmf":
            order = ["msmf"]
        else:  # auto
            order = ["dshow", "msmf", "any"]

        for name in order:
            if name == "dshow" and not hasattr(cv2, "CAP_DSHOW"):
                continue
            if name == "msmf" and not hasattr(cv2, "CAP_MSMF"):
                continue

            self.verifier.close()
            capture = None
            try:
                if name == "dshow":
                    capture = cv2.VideoCapture(self.verifier.index, cv2.CAP_DSHOW)
                elif name == "msmf":
                    capture = cv2.VideoCapture(self.verifier.index, cv2.CAP_MSMF)
                else:
                    capture = cv2.VideoCapture(self.verifier.index)
            except Exception as exc:  # noqa: BLE001 - driver-specific
                self.ctx.log(
                    "camera", f"Backend {name} raised {type(exc).__name__}: {exc}"
                )
                continue

            if capture is not None and capture.isOpened():
                self.verifier.capture = capture
                self.ctx.log("camera", f"Opened camera via backend '{name}'")
                return True

            if capture is not None:
                capture.release()

        return False

    def _apply_capture_settings(self) -> None:
        """Push resolution, fps, exposure lock and wb lock to the driver.

        Every step is reported back to the user from the *readback* value,
        not from the value we requested. If the driver silently ignores a
        setting, the info line says so -- we would rather be honest than
        pretend the lock is on when it is not.
        """
        cap = self.verifier.capture
        if cap is None:
            return

        import cv2

        # --- capture size ------------------------------------------------
        width, height = self._parse_resolution(self.combo_resolution.currentData())
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))
        got_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        got_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        # --- fps ---------------------------------------------------------
        fps_target = float(self.combo_fps.currentData() or 30)
        cap.set(cv2.CAP_PROP_FPS, fps_target)
        got_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)

        # --- exposure ----------------------------------------------------
        exp_msg = self._apply_exposure(cap, cv2)

        # --- white balance ----------------------------------------------
        wb_msg = self._apply_wb(cap, cv2)

        # --- report ------------------------------------------------------
        self._locks_applied = {
            "resolution": f"{got_w}x{got_h} (asked {width}x{height})",
            "fps": f"{got_fps:.1f} (asked {fps_target:.0f})",
            "exposure": exp_msg,
            "white_balance": wb_msg,
        }
        self._last_report = (
            f"Driver reports — capture size: {got_w}x{got_h}, "
            f"fps: {got_fps:.1f}. Exposure: {exp_msg}. White balance: {wb_msg}."
        )
        self.lbl_lock_status.setText(self._last_report)
        self.ctx.log("camera", self._last_report)

    def _apply_exposure(self, cap, cv2) -> str:
        """Set or clear exposure lock; return a human-readable result.

        Windows DirectShow expects ``CAP_PROP_AUTO_EXPOSURE = 0.25`` for
        manual and ``0.75`` for auto. V4L2/Linux uses ``1.0`` for manual
        and ``3.0`` for auto. We try both, then read every relevant
        property back to describe what actually happened.
        """
        if not self.chk_exposure.isChecked():
            # Best-effort: hand control back to auto.
            for auto_flag in (0.75, 3.0):
                try:
                    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, auto_flag)
                    break
                except Exception:
                    continue
            auto_read = self._safe_get(cap, cv2.CAP_PROP_AUTO_EXPOSURE)
            return f"auto (flag={auto_read})"

        manual_value = float(self.slider_exposure.value())
        chosen_flag: float | None = None
        for manual_flag in (0.25, 1.0):
            try:
                cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, manual_flag)
                cap.set(cv2.CAP_PROP_EXPOSURE, manual_value)
                # Give the driver a moment to react before reading back.
                read_auto = self._safe_get(cap, cv2.CAP_PROP_AUTO_EXPOSURE)
                # If the driver kept the auto flag on, this manual flag
                # was wrong -- try the other one.
                if read_auto is not None and read_auto >= 0.6:
                    continue
                chosen_flag = manual_flag
                break
            except Exception:
                continue

        read_exposure = self._safe_get(cap, cv2.CAP_PROP_EXPOSURE)
        read_auto = self._safe_get(cap, cv2.CAP_PROP_AUTO_EXPOSURE)

        if chosen_flag is None or read_auto is None or read_auto >= 0.6:
            return (
                f"driver refused lock — asked {self._exposure_text(int(manual_value))}, "
                f"auto flag={read_auto}, exposure={read_exposure}"
            )

        # Manual flag stuck. Now check whether the exposure value landed.
        if read_exposure is None:
            return (
                f"manual flag set (={read_auto}), but driver did not return "
                f"an exposure value"
            )

        try:
            actual = float(read_exposure)
        except (TypeError, ValueError):
            actual = None

        if actual is not None and abs(actual - manual_value) <= 0.5:
            return (
                f"locked at {self._exposure_text(int(round(actual)))} "
                f"(auto flag={read_auto})"
            )

        # Manual flag is set but value readback differs -- report both
        # numbers so the user can see the truth.
        return (
            f"manual flag set (={read_auto}) but exposure reports "
            f"{read_exposure} (asked {manual_value:.2f})"
        )

    def _apply_wb(self, cap, cv2) -> str:
        """Set or clear WB lock; return a human-readable result."""
        if not self.chk_wb.isChecked():
            try:
                cap.set(cv2.CAP_PROP_AUTO_WB, 1.0)
            except Exception:
                pass
            flag = self._safe_get(cap, cv2.CAP_PROP_AUTO_WB)
            return f"auto (flag={flag})"

        try:
            cap.set(cv2.CAP_PROP_AUTO_WB, 0.0)
        except Exception as exc:  # noqa: BLE001 - driver-specific
            return f"driver refused (raised {type(exc).__name__})"

        flag = self._safe_get(cap, cv2.CAP_PROP_AUTO_WB)
        if flag is None:
            return "driver did not return an auto-WB flag"
        if flag >= 0.5:
            return f"driver ignored lock (auto flag still {flag})"
        return f"locked (auto flag={flag})"

    @staticmethod
    def _safe_get(cap, prop) -> float | None:
        try:
            value = cap.get(prop)
        except Exception:  # noqa: BLE001 - driver-specific
            return None
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

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
        self.ctx.settings.camera_resolution = (
            self.combo_resolution.currentData() or "1280x720"
        )
        self.ctx.settings.camera_fps = int(self.combo_fps.currentData() or 30)
        # Persist the backend choice. Harmless if the field does not exist.
        try:
            self.ctx.settings.camera_backend = (
                self.combo_backend.currentData() or "auto"
            )
        except AttributeError:
            pass

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

    # =================================================================
    # Consistency with other tabs
    # =================================================================

    def sync_clamp_notice(self) -> None:
        """No clamp on this tab, but the main window calls every tab
        uniformly so we keep a no-op here."""
        return
