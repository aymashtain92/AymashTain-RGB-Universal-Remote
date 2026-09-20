"""Media player plus audio-reactive dancing lights."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...audio import AudioEngine, bands_to_rgb
from ...audio.engine import rms_to_brightness
from ..context import AppContext
from ..widgets import StripPreview

SOURCES = {
    "Microphone / line-in": "microphone",
    "System audio (loopback)": "loopback",
    "Playing file": "file",
}


class MusicTab(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.engine = AudioEngine()
        self.playlist: list[Path] = []
        self._index = -1
        self._busy = False

        self.player = QMediaPlayer(self)
        self.audio_out = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_out)
        self.audio_out.setVolume(ctx.settings.media_volume / 100.0)
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(lambda d: self.seek.setRange(0, max(0, d)))
        self.player.mediaStatusChanged.connect(self._on_media_status)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        layout = QHBoxLayout(self)

        # --- playlist -----------------------------------------------------
        left = QVBoxLayout()
        left.addWidget(QLabel("<b>Playlist</b>"))
        self.list_files = QListWidget()
        self.list_files.itemDoubleClicked.connect(lambda _: self._play_index(self.list_files.currentRow()))
        left.addWidget(self.list_files, stretch=1)

        file_buttons = QHBoxLayout()
        btn_add = QPushButton("Add files…")
        btn_add.clicked.connect(self._add_files)
        btn_remove = QPushButton("Remove")
        btn_remove.clicked.connect(self._remove_file)
        file_buttons.addWidget(btn_add)
        file_buttons.addWidget(btn_remove)
        left.addLayout(file_buttons)

        transport = QHBoxLayout()
        for label, slot in (
            ("◀◀", lambda: self._play_index(self._index - 1)),
            ("▶", self.player.play),
            ("❚❚", self.player.pause),
            ("■", self._stop_media),
            ("▶▶", lambda: self._play_index(self._index + 1)),
        ):
            button = QPushButton(label)
            button.clicked.connect(slot)
            transport.addWidget(button)
        left.addLayout(transport)

        self.seek = QSlider(Qt.Horizontal)
        self.seek.sliderReleased.connect(lambda: self.player.setPosition(self.seek.value()))
        left.addWidget(self.seek)

        volume_row = QHBoxLayout()
        volume_row.addWidget(QLabel("Volume"))
        self.slider_volume = QSlider(Qt.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(ctx.settings.media_volume)
        self.slider_volume.valueChanged.connect(self._on_volume)
        volume_row.addWidget(self.slider_volume)
        left.addLayout(volume_row)

        self.lbl_now = QLabel("Nothing playing.")
        left.addWidget(self.lbl_now)
        layout.addLayout(left, stretch=2)

        # --- reactive -----------------------------------------------------
        right = QVBoxLayout()
        source_box = QGroupBox("Dancing lights")
        source_layout = QVBoxLayout(source_box)

        self.combo_source = QComboBox()
        self.combo_source.addItems(SOURCES.keys())
        self.combo_source.currentIndexChanged.connect(self._populate_devices)
        self.combo_device = QComboBox()
        source_layout.addWidget(self.combo_source)
        source_layout.addWidget(self.combo_device)

        rates = QHBoxLayout()
        rates.addWidget(QLabel("Update every"))
        self.spin_rate = QSpinBox()
        self.spin_rate.setRange(40, 1000)
        self.spin_rate.setValue(120)
        self.spin_rate.setSuffix(" ms")
        rates.addWidget(self.spin_rate)
        rates.addWidget(QLabel("Gain"))
        self.spin_gain = QSpinBox()
        self.spin_gain.setRange(1, 10)
        self.spin_gain.setValue(int(ctx.settings.audio_gain * 2))
        rates.addWidget(self.spin_gain)
        source_layout.addLayout(rates)

        buttons = QHBoxLayout()
        self.btn_start = QPushButton("Start reacting")
        self.btn_start.setProperty("accent", True)
        self.btn_start.clicked.connect(self._start)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setProperty("danger", True)
        self.btn_stop.clicked.connect(self._stop_reacting)
        self.btn_stop.setEnabled(False)
        buttons.addWidget(self.btn_start)
        buttons.addWidget(self.btn_stop)
        source_layout.addLayout(buttons)
        right.addWidget(source_box)

        meters = QGroupBox("Levels")
        meters_layout = QVBoxLayout(meters)
        self.bars = {}
        for name in ("bass", "mid", "treble"):
            row = QHBoxLayout()
            row.addWidget(QLabel(name.title()))
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(False)
            self.bars[name] = bar
            row.addWidget(bar)
            meters_layout.addLayout(row)
        right.addWidget(meters)

        self.preview = StripPreview()
        right.addWidget(self.preview)
        self.lbl_state = QLabel(
            "Audio backend ready." if AudioEngine.available() else
            "sounddevice/numpy not installed — dancing lights disabled."
        )
        self.lbl_state.setWordWrap(True)
        right.addWidget(self.lbl_state)
        right.addStretch()
        layout.addLayout(right, stretch=2)

        self._populate_devices()

    # --- media player -----------------------------------------------------

    def _add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Add audio files", "", "Audio (*.mp3 *.wav *.flac *.ogg *.m4a);;All files (*)"
        )
        for path in files:
            self.playlist.append(Path(path))
            self.list_files.addItem(Path(path).name)

    def _remove_file(self) -> None:
        row = self.list_files.currentRow()
        if row < 0:
            return
        self.list_files.takeItem(row)
        del self.playlist[row]

    def _play_index(self, index: int) -> None:
        if not self.playlist:
            return
        self._index = index % len(self.playlist)
        path = self.playlist[self._index]
        self.list_files.setCurrentRow(self._index)
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.play()
        self.lbl_now.setText(f"Playing: {path.name}")

    def _stop_media(self) -> None:
        self.player.stop()
        self.lbl_now.setText("Stopped.")

    def _on_position(self, position: int) -> None:
        if not self.seek.isSliderDown():
            self.seek.setValue(position)

    def _on_media_status(self, status) -> None:
        if status == QMediaPlayer.EndOfMedia and self.playlist:
            self._play_index(self._index + 1)

    def _on_volume(self, value: int) -> None:
        self.ctx.settings.media_volume = value
        self.audio_out.setVolume(value / 100.0)

    # --- reactive ---------------------------------------------------------

    def _populate_devices(self) -> None:
        self.combo_device.clear()
        source = SOURCES[self.combo_source.currentText()]
        if not AudioEngine.available():
            return
        if source == "microphone":
            devices = self.engine.list_inputs()
        elif source == "loopback":
            devices = self.engine.list_outputs()
        else:
            self.combo_device.addItem("Uses the playlist above", -1)
            return
        for index, name, api in devices:
            self.combo_device.addItem(f"{name} [{api}]", index)

    def _start(self) -> None:
        source = SOURCES[self.combo_source.currentText()]
        device = self.combo_device.currentData()
        try:
            if source == "microphone":
                self.engine.start_microphone(device if device is not None and device >= 0 else None)
            elif source == "loopback":
                self.engine.start_system_loopback(device if device is not None and device >= 0 else None)
            else:
                if self._index < 0:
                    self._play_index(0)
                self.engine.start_file(str(self.playlist[self._index]))
        except Exception as exc:
            self.lbl_state.setText(str(exc))
            self.ctx.log("error", f"Audio start failed: {exc}")
            return

        self.ctx.settings.audio_source = source
        self.ctx.settings.audio_device_index = int(device) if device is not None else -1
        self._timer.start(self.spin_rate.value())
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_state.setText(f"Reacting to {self.combo_source.currentText().lower()}.")

    def _stop_reacting(self) -> None:
        self._timer.stop()
        self.engine.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_state.setText("Stopped.")

    def _tick(self) -> None:
        frame = self.engine.analyse()
        peak = max(frame.bass, frame.mid, frame.treble, 1e-6)
        for name in ("bass", "mid", "treble"):
            self.bars[name].setValue(int(min(1.0, getattr(frame, name) / peak) * 100))

        gain = self.spin_gain.value() / 2.0
        r, g, b = bands_to_rgb(frame, gain)
        brightness = rms_to_brightness(
            frame.rms, self.ctx.settings.audio_min_brightness / 100.0, gain
        )
        self.preview.set_color(r, g, b, brightness, "audio")

        if self._busy:
            return
        self._busy = True
        task = self.ctx.run(self.ctx.ble.set_color(r, g, b, brightness))
        task.add_done_callback(lambda _: setattr(self, "_busy", False))

    def shutdown(self) -> None:
        self._timer.stop()
        self.engine.stop()
        self.player.stop()
