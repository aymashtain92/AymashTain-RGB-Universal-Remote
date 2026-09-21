"""Options tab: the single place for app-wide settings.

Everything the Round 2 spec moved out of individual tabs lives here:

* save location for exports
* theme (light / dark / follow OS)
* developer tools lock (gates the Lab tab)
* language stub (English only for now)
* brightness min / max clamp
* audio devices (mic, second mic, speaker)
* camera device, resolution, FPS, exposure lock, white-balance lock
* remember-window toggle
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ... import paths
from ...audio import AudioEngine
from ...config import (
    MIC_THIRD_PARTY,
    MIC_USB_INTERNAL,
    THEME_DARK,
    THEME_LIGHT,
    THEME_SYSTEM,
)
from ..context import AppContext

#: Common camera capture sizes. The Nuroum V11 tops out at 1440p @ 60 fps.
CAMERA_RESOLUTIONS = [
    "640x480",
    "1280x720",
    "1920x1080",
    "2560x1440",
]
CAMERA_FPS_CHOICES = [15, 24, 30, 60]


class OptionsTab(QWidget):
    """Application-wide settings page."""

    #: Fired when the developer-tools lock flips, so the main window can
    #: show or hide the Lab tab.
    developer_tools_changed = Signal(bool)

    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self._audio_engine = AudioEngine()

        # The whole page scrolls when the window is small.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        page = QWidget()
        scroll.setWidget(page)
        layout = QVBoxLayout(page)

        layout.addWidget(self._build_general_box())
        layout.addWidget(self._build_appearance_box())
        layout.addWidget(self._build_developer_box())
        layout.addWidget(self._build_brightness_box())
        layout.addWidget(self._build_audio_box())
        layout.addWidget(self._build_camera_box())
        layout.addWidget(self._build_window_box())
        layout.addStretch()

        self._populate_audio_devices()

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_general_box(self) -> QGroupBox:
        box = QGroupBox("General")
        form = QFormLayout(box)

        row = QHBoxLayout()
        self.edit_save = QLineEdit(self.ctx.settings.save_location)
        self.edit_save.setPlaceholderText(str(paths.data_dir()))
        self.edit_save.editingFinished.connect(self._on_save_location_changed)
        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self._pick_save_location)
        btn_reset = QPushButton("Reset to default")
        btn_reset.clicked.connect(self._reset_save_location)
        row.addWidget(self.edit_save, stretch=1)
        row.addWidget(btn_browse)
        row.addWidget(btn_reset)
        row_widget = QWidget()
        row_widget.setLayout(row)
        form.addRow("Export save location", row_widget)

        self.combo_language = QComboBox()
        self.combo_language.addItem("English (en)", "en")
        # Arabic (and others) will be added when translation lands.
        self.combo_language.setEnabled(False)
        self.combo_language.setToolTip(
            "Only English is available in this build. Arabic is planned."
        )
        form.addRow("Language", self.combo_language)

        return box

    def _build_appearance_box(self) -> QGroupBox:
        box = QGroupBox("Appearance")
        form = QFormLayout(box)

        self.combo_theme = QComboBox()
        self.combo_theme.addItem("Follow system", THEME_SYSTEM)
        self.combo_theme.addItem("Dark", THEME_DARK)
        self.combo_theme.addItem("Light", THEME_LIGHT)
        index = self.combo_theme.findData(self.ctx.settings.theme_mode)
        self.combo_theme.setCurrentIndex(max(0, index))
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        form.addRow("Theme", self.combo_theme)

        return box

    def _build_developer_box(self) -> QGroupBox:
        box = QGroupBox("Developer")
        form = QFormLayout(box)

        self.chk_dev = QCheckBox("Enable developer tools (Lab tab and hidden tooling)")
        self.chk_dev.setChecked(self.ctx.settings.developer_tools)
        self.chk_dev.stateChanged.connect(self._on_dev_toggled)
        form.addRow("", self.chk_dev)

        note = QLabel(
            "Off for normal use. When off, the Lab tab is hidden. "
            "Turn it on only when experimenting with raw frames."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #71717A;")
        form.addRow("", note)

        return box

    def _build_brightness_box(self) -> QGroupBox:
        box = QGroupBox("Brightness limits")
        form = QFormLayout(box)

        # --- minimum ---
        min_row = QHBoxLayout()
        self.slider_min = QSlider(Qt.Horizontal)
        self.slider_min.setRange(0, 100)
        self.slider_min.setValue(self.ctx.settings.brightness_min)
        self.lbl_min = QLabel(f"{self.slider_min.value()}%")
        self.lbl_min.setMinimumWidth(48)
        self.slider_min.valueChanged.connect(self._on_brightness_limits_changed)
        min_row.addWidget(self.slider_min, stretch=1)
        min_row.addWidget(self.lbl_min)
        min_widget = QWidget()
        min_widget.setLayout(min_row)
        form.addRow("Minimum brightness", min_widget)

        # --- maximum ---
        max_row = QHBoxLayout()
        self.slider_max = QSlider(Qt.Horizontal)
        self.slider_max.setRange(0, 100)
        self.slider_max.setValue(self.ctx.settings.brightness_max)
        self.lbl_max = QLabel(f"{self.slider_max.value()}%")
        self.lbl_max.setMinimumWidth(48)
        self.slider_max.valueChanged.connect(self._on_brightness_limits_changed)
        max_row.addWidget(self.slider_max, stretch=1)
        max_row.addWidget(self.lbl_max)
        max_widget = QWidget()
        max_widget.setLayout(max_row)
        form.addRow("Maximum brightness", max_widget)

        note = QLabel(
            "Nothing above the maximum is ever sent to a strip. "
            "If your controller stops responding at a high value, lower the "
            "maximum below that point."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #71717A;")
        form.addRow("", note)

        return box

    def _build_audio_box(self) -> QGroupBox:
        box = QGroupBox("Audio devices")
        form = QFormLayout(box)

        self.combo_mic = QComboBox()
        self.combo_mic2 = QComboBox()
        self.combo_speaker = QComboBox()
        self.combo_mic.currentIndexChanged.connect(self._on_audio_changed)
        self.combo_mic2.currentIndexChanged.connect(self._on_audio_changed)
        self.combo_speaker.currentIndexChanged.connect(self._on_audio_changed)

        form.addRow("Input mic (primary)", self.combo_mic)
        form.addRow("Second mic / line-in", self.combo_mic2)
        form.addRow("Speaker output (loopback)", self.combo_speaker)

        btn_refresh = QPushButton("Refresh device lists")
        btn_refresh.clicked.connect(self._populate_audio_devices)
        form.addRow("", btn_refresh)

        self.lbl_audio_status = QLabel("")
        self.lbl_audio_status.setWordWrap(True)
        self.lbl_audio_status.setStyleSheet("color: #71717A;")
        form.addRow("", self.lbl_audio_status)

        return box

    def _build_camera_box(self) -> QGroupBox:
        box = QGroupBox("Camera")
        form = QFormLayout(box)

        self.spin_camera = QSpinBox()
        self.spin_camera.setRange(0, 8)
        self.spin_camera.setValue(self.ctx.settings.camera_index)
        self.spin_camera.valueChanged.connect(self._on_camera_changed)
        form.addRow("Camera device index", self.spin_camera)

        self.combo_resolution = QComboBox()
        for value in CAMERA_RESOLUTIONS:
            self.combo_resolution.addItem(value, value)
        idx = self.combo_resolution.findData(self.ctx.settings.camera_resolution)
        self.combo_resolution.setCurrentIndex(max(0, idx))
        self.combo_resolution.currentIndexChanged.connect(self._on_camera_changed)
        form.addRow("Resolution", self.combo_resolution)

        self.combo_fps = QComboBox()
        for value in CAMERA_FPS_CHOICES:
            self.combo_fps.addItem(f"{value} fps", value)
        idx = self.combo_fps.findData(self.ctx.settings.camera_fps)
        self.combo_fps.setCurrentIndex(max(0, idx))
        self.combo_fps.currentIndexChanged.connect(self._on_camera_changed)
        form.addRow("Frame rate", self.combo_fps)

        self.chk_exposure_lock = QCheckBox("Lock exposure (disable auto-exposure)")
        self.chk_exposure_lock.setChecked(self.ctx.settings.camera_exposure_lock)
        self.chk_exposure_lock.stateChanged.connect(self._on_camera_changed)
        form.addRow("", self.chk_exposure_lock)

        exp_row = QHBoxLayout()
        self.slider_exposure = QSlider(Qt.Horizontal)
        self.slider_exposure.setRange(-13, 0)  # OpenCV uses log2 seconds
        self.slider_exposure.setValue(self.ctx.settings.camera_exposure_value)
        self.lbl_exposure = QLabel(self._exposure_text(self.slider_exposure.value()))
        self.lbl_exposure.setMinimumWidth(80)
        self.slider_exposure.valueChanged.connect(self._on_exposure_slider)
        exp_row.addWidget(self.slider_exposure, stretch=1)
        exp_row.addWidget(self.lbl_exposure)
        exp_widget = QWidget()
        exp_widget.setLayout(exp_row)
        form.addRow("Manual exposure value", exp_widget)

        self.chk_wb_lock = QCheckBox("Lock white balance")
        self.chk_wb_lock.setChecked(self.ctx.settings.camera_wb_lock)
        self.chk_wb_lock.stateChanged.connect(self._on_camera_changed)
        form.addRow("", self.chk_wb_lock)

        note = QLabel(
            "The Nuroum V11 supports up to 1440p @ 60 fps. If exposure stays "
            "auto even with the lock on, close and reopen the Camera tab."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #71717A;")
        form.addRow("", note)

        return box

    def _build_window_box(self) -> QGroupBox:
        box = QGroupBox("Window")
        form = QFormLayout(box)

        self.chk_remember = QCheckBox(
            "Remember screen, position, size and scale between sessions"
        )
        self.chk_remember.setChecked(self.ctx.settings.remember_window)
        self.chk_remember.stateChanged.connect(self._on_remember_changed)
        form.addRow("", self.chk_remember)

        self.lbl_screens = QLabel("")
        self.lbl_screens.setWordWrap(True)
        self.lbl_screens.setStyleSheet("color: #71717A;")
        form.addRow("", self.lbl_screens)
        self._update_screen_summary()

        return box

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_save_location_changed(self) -> None:
        self.ctx.settings.save_location = self.edit_save.text().strip()

    def _pick_save_location(self) -> None:
        start = self.edit_save.text().strip() or str(paths.data_dir())
        chosen = QFileDialog.getExistingDirectory(
            self, "Choose export folder", start
        )
        if chosen:
            self.edit_save.setText(chosen)
            self.ctx.settings.save_location = chosen

    def _reset_save_location(self) -> None:
        self.edit_save.setText("")
        self.ctx.settings.save_location = ""

    def _on_theme_changed(self) -> None:
        mode = self.combo_theme.currentData()
        self.ctx.settings.theme_mode = mode
        # Legacy mirror for anything still reading dark_theme.
        self.ctx.settings.dark_theme = self.ctx.settings.resolved_dark()
        window = self.window()
        if hasattr(window, "apply_theme"):
            window.apply_theme()

    def _on_dev_toggled(self) -> None:
        enabled = self.chk_dev.isChecked()
        self.ctx.settings.developer_tools = enabled
        self.developer_tools_changed.emit(enabled)

    def _on_brightness_limits_changed(self) -> None:
        lo = self.slider_min.value()
        hi = self.slider_max.value()
        if lo > hi:
            # Keep them ordered: whichever the user just moved wins.
            if self.sender() is self.slider_min:
                hi = lo
                self.slider_max.blockSignals(True)
                self.slider_max.setValue(hi)
                self.slider_max.blockSignals(False)
            else:
                lo = hi
                self.slider_min.blockSignals(True)
                self.slider_min.setValue(lo)
                self.slider_min.blockSignals(False)

        self.lbl_min.setText(f"{lo}%")
        self.lbl_max.setText(f"{hi}%")
        self.ctx.settings.brightness_min = lo
        self.ctx.settings.brightness_max = hi

    def _on_audio_changed(self) -> None:
        self.ctx.settings.audio_mic_device = int(self.combo_mic.currentData() or -1)
        self.ctx.settings.audio_second_mic_device = int(self.combo_mic2.currentData() or -1)
        self.ctx.settings.audio_speaker_device = int(self.combo_speaker.currentData() or -1)

    def _populate_audio_devices(self) -> None:
        inputs: list[tuple[int, str, str]] = []
        outputs: list[tuple[int, str, str]] = []

        if AudioEngine.available():
            try:
                inputs = self._audio_engine.list_inputs()
                outputs = self._audio_engine.list_outputs()
            except Exception as exc:  # pragma: no cover - host dependent
                self.lbl_audio_status.setText(f"Audio backend error: {exc}")
        else:
            self.lbl_audio_status.setText(
                "sounddevice is not installed — dancing lights disabled."
            )

        self._fill_combo(self.combo_mic, inputs, self.ctx.settings.audio_mic_device)
        self._fill_combo(self.combo_mic2, inputs, self.ctx.settings.audio_second_mic_device)
        self._fill_combo(self.combo_speaker, outputs, self.ctx.settings.audio_speaker_device)

    @staticmethod
    def _fill_combo(combo: QComboBox, devices: list[tuple[int, str, str]], current: int) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("(none)", -1)
        for index, name, api in devices:
            combo.addItem(f"{name} [{api}]", index)
        idx = combo.findData(current)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)

    def _on_camera_changed(self) -> None:
        self.ctx.settings.camera_index = self.spin_camera.value()
        self.ctx.settings.camera_resolution = (
            self.combo_resolution.currentData() or "1280x720"
        )
        self.ctx.settings.camera_fps = int(self.combo_fps.currentData() or 30)
        self.ctx.settings.camera_exposure_lock = self.chk_exposure_lock.isChecked()
        self.ctx.settings.camera_exposure_value = self.slider_exposure.value()
        self.ctx.settings.camera_wb_lock = self.chk_wb_lock.isChecked()

    def _on_exposure_slider(self, value: int) -> None:
        self.lbl_exposure.setText(self._exposure_text(value))
        self.ctx.settings.camera_exposure_value = value

    @staticmethod
    def _exposure_text(value: int) -> str:
        if value >= 0:
            return "auto"
        return f"1/{2 ** (-value)} s"

    def _on_remember_changed(self) -> None:
        self.ctx.settings.remember_window = self.chk_remember.isChecked()
        self._update_screen_summary()

    def _update_screen_summary(self) -> None:
        screens = QGuiApplication.screens()
        names = ", ".join(s.name() for s in screens) or "(no screens detected)"
        self.lbl_screens.setText(
            f"Detected screens: {names}. "
            f"Position, size and scale are restored on the same monitor when remembered."
        )

    # ------------------------------------------------------------------
    # External helpers
    # ------------------------------------------------------------------

    def export_directory(self) -> str:
        """Folder exports should default to. Empty means use the data dir."""
        return self.ctx.settings.save_location.strip()