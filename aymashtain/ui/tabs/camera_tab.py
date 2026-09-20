"""Webcam verification of what the strip actually emits."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
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

from ...vision import CameraVerifier
from ..context import AppContext


class CameraTab(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.verifier = CameraVerifier(ctx.settings.camera_index)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        layout = QHBoxLayout(self)

        left = QVBoxLayout()
        self.view = QLabel("Camera idle — press Start preview.")
        self.view.setAlignment(Qt.AlignCenter)
        self.view.setMinimumSize(480, 360)
        self.view.setStyleSheet("background:#000; border-radius:10px; color:#71717A;")
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

        right = QVBoxLayout()
        config = QGroupBox("Sample window")
        form = QFormLayout(config)
        self.spin_index = QSpinBox()
        self.spin_index.setRange(0, 8)
        self.spin_index.setValue(ctx.settings.camera_index)
        self.spin_samples = QSpinBox()
        self.spin_samples.setRange(1, 15)
        self.spin_samples.setValue(ctx.settings.camera_samples_per_command)
        self.region_spins = []
        region_row = QHBoxLayout()
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
        form.addRow("Camera index", self.spin_index)
        form.addRow("Samples per command", self.spin_samples)
        form.addRow("Region x0,y0,x1,y1", region_widget)
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

    # --- preview ----------------------------------------------------------

    def _toggle(self) -> None:
        if self.verifier.is_open:
            self._timer.stop()
            self.verifier.close()
            self.btn_toggle.setText("Start preview")
            self.view.setText("Camera idle.")
            return

        if not CameraVerifier.available():
            self.lbl_status.setText("OpenCV is not installed — run: pip install opencv-python")
            return

        self.verifier.index = self.spin_index.value()
        self.ctx.settings.camera_index = self.verifier.index
        if not self.verifier.open():
            self.lbl_status.setText(f"Could not open camera {self.verifier.index}.")
            return

        self._timer.start(33)
        self.btn_toggle.setText("Stop preview")
        self.ctx.log("camera", f"Preview started on camera {self.verifier.index}")

    def _tick(self) -> None:
        frame = self.verifier.read_rgb()
        if frame is None:
            return
        height, width, _ = frame.shape
        x0, y0, x1, y1 = self.region()
        import cv2

        annotated = frame.copy()
        cv2.rectangle(
            annotated,
            (int(x0 * width), int(y0 * height)),
            (int(x1 * width), int(y1 * height)),
            (99, 102, 241),
            2,
        )
        image = QImage(annotated.data, width, height, 3 * width, QImage.Format_RGB888)
        self.view.setPixmap(
            QPixmap.fromImage(image).scaled(self.view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    # --- sampling ---------------------------------------------------------

    def region(self) -> tuple[float, float, float, float]:
        return tuple(spin.value() for spin in self.region_spins)  # type: ignore[return-value]

    def _region_changed(self) -> None:
        self.ctx.settings.camera_region = list(self.region())

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
