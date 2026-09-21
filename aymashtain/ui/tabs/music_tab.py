"""Media player plus audio-reactive dancing lights.

Round 2 cleanup
---------------
* Microphone *selection* now lives in Options. This tab never lists audio
  devices anymore — it just uses the indices chosen there.
* The old source dropdown is gone. Instead there is a **pattern list**, and
  each pattern carries its own source assignment.
* Two categories of pattern:
    - **Controller** patterns — sent once as an effect frame; the strip's
      own USB mic drives the dance. No PC audio is fed. This is what the
      vendor app's "music mode" does.
    - **Software** patterns — the PC keeps sending colour + brightness in a
      loop, driven by the mic / line-in / speaker loopback / playing file.
* The Play button now plays the *selected* row. Single click selects, Play
  starts. Double-click still works as a shortcut.
* The strip preview uses the new neon-capsule widget.
* Brightness is clamped through ``settings.clamp_brightness()`` before every
  frame, so the Options min / max always wins.

Planned (not built in this file): Winamp-style frequency visualiser, video
file playback, MPC + K-Lite integration. Those land in a later phase.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...audio import AudioEngine, bands_to_rgb
from ...audio.engine import rms_to_brightness
from ...config import MIC_THIRD_PARTY, MIC_USB_INTERNAL
from ...protocol import encode_effect
from ..context import AppContext
from ..widgets import StripPreview

#: Kind: "controller" → fire one effect frame, then leave the strip alone.
#: Kind: "software"   → drive colour + brightness from a live audio feed.
PATTERNS: list[tuple[str, str, str]] = [
    ("spectrum", "Spectrum", "software"),
    ("pulse", "Pulse (bass)", "software"),
    ("ctrl_1", "Controller mode 1", "controller"),
    ("ctrl_2", "Controller mode 2", "controller"),
    ("ctrl_3", "Controller mode 3", "controller"),
    ("ctrl_4", "Controller mode 4", "controller"),
]

#: Display order for the per-pattern source combo.
SOURCE_LABELS: list[tuple[str, str]] = [
    (MIC_THIRD_PARTY, "3rd-party mic / file (PC drives the lights)"),
    (MIC_USB_INTERNAL, "USB built-in mic (strip drives itself)"),
]

#: The strip's native music effect is 0x0B. The four "modes" are mapped onto
#: the speed byte in ``BC 06 02 0B MM 00 55``. Values are a best guess — if a
#: mode does nothing, verify with the Lab tab on your hardware.
CONTROLLER_EFFECT_BYTE = "0B"


@dataclass
class PatternState:
    key: str
    name: str
    kind: str          # controller | software
    source: str        # MIC_USB_INTERNAL | MIC_THIRD_PARTY


class MusicTab(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.engine = AudioEngine()
        self.playlist: list[Path] = []
        self._index = -1
        self._busy = False
        self._active_pattern: PatternState | None = None

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

        # =============================================================
        # Left: playlist + transport + volume
        # =============================================================
        left = QVBoxLayout()
        left.addWidget(QLabel("<b>Playlist</b>"))

        self.list_files = QListWidget()
        self.list_files.setSelectionMode(QAbstractItemView.SingleSelection)
        # Double-click is a convenience only; the Play button does the real work.
        self.list_files.itemDoubleClicked.connect(self._on_row_double_clicked)
        left.addWidget(self.list_files, stretch=1)

        file_buttons = QHBoxLayout()
        btn_add = QPushButton("Add files…")
        btn_add.clicked.connect(self._add_files)
        btn_remove = QPushButton("Remove selected")
        btn_remove.clicked.connect(self._remove_selected)
        file_buttons.addWidget(btn_add)
        file_buttons.addWidget(btn_remove)
        left.addLayout(file_buttons)

        transport = QHBoxLayout()
        btn_prev = QPushButton("◀◀")
        btn_prev.clicked.connect(lambda: self._step_track(-1))
        btn_play = QPushButton("▶  Play")
        btn_play.setProperty("accent", True)
        btn_play.clicked.connect(self._play_selected)
        btn_pause = QPushButton("❚❚")
        btn_pause.clicked.connect(self.player.pause)
        btn_stop = QPushButton("■")
        btn_stop.clicked.connect(self._stop_media)
        btn_next = QPushButton("▶▶")
        btn_next.clicked.connect(lambda: self._step_track(+1))
        for button in (btn_prev, btn_play, btn_pause, btn_stop, btn_next):
            transport.addWidget(button)
        left.addLayout(transport)

        self.seek = QSlider(Qt.Horizontal)
        self.seek.sliderReleased.connect(
            lambda: self.player.setPosition(self.seek.value())
        )
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
        self.lbl_now.setWordWrap(True)
        left.addWidget(self.lbl_now)

        layout.addLayout(left, stretch=2)

        # =============================================================
        # Right: patterns + preview + meters
        # =============================================================
        right = QVBoxLayout()

        patterns_box = QGroupBox("Patterns")
        patterns_layout = QVBoxLayout(patterns_box)

        info = QLabel(
            "Pick a source per pattern. Mic devices are chosen in the Options tab. "
            "Controller patterns send a single effect frame — the strip does its "
            "own thing from its USB mic. Software patterns drive the lights from "
            "the PC in real time."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #71717A;")
        patterns_layout.addWidget(info)

        self.pattern_table = QTableWidget(len(PATTERNS), 4)
        self.pattern_table.setHorizontalHeaderLabels(
            ["Pattern", "Source", "Kind", ""]
        )
        header = self.pattern_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.pattern_table.verticalHeader().setVisible(False)
        self.pattern_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.pattern_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.pattern_table.setFocusPolicy(Qt.NoFocus)

        self._source_combos: dict[str, QComboBox] = {}
        self._start_buttons: dict[str, QPushButton] = {}

        for row, (key, name, kind) in enumerate(PATTERNS):
            self.pattern_table.setItem(row, 0, QTableWidgetItem(name))
            self.pattern_table.setItem(
                row, 2, QTableWidgetItem("controller" if kind == "controller" else "software")
            )

            combo = QComboBox()
            for value, label in SOURCE_LABELS:
                combo.addItem(label, value)
            default = self._default_source_for(kind)
            saved = ctx.settings.pattern_sources.get(key, default)
            idx = combo.findData(saved)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            combo.currentIndexChanged.connect(
                lambda _=0, k=key, c=combo: self._on_source_changed(k, c)
            )
            self._source_combos[key] = combo

            if kind == "controller":
                # The strip uses its own mic; PC source is irrelevant.
                combo.setCurrentIndex(combo.findData(MIC_USB_INTERNAL))
                combo.setEnabled(False)

            self.pattern_table.setCellWidget(row, 1, combo)

            btn = QPushButton("Start")
            btn.setProperty("accent", True)
            btn.clicked.connect(
                lambda _=False, k=key, n=name, kd=kind: self._start_pattern(k, n, kd)
            )
            self._start_buttons[key] = btn
            self.pattern_table.setCellWidget(row, 3, btn)

        self.pattern_table.resizeRowsToContents()
        patterns_layout.addWidget(self.pattern_table)

        stop_row = QHBoxLayout()
        self.btn_stop_pattern = QPushButton("Stop pattern")
        self.btn_stop_pattern.setProperty("danger", True)
        self.btn_stop_pattern.setEnabled(False)
        self.btn_stop_pattern.clicked.connect(self._stop_pattern)
        stop_row.addWidget(self.btn_stop_pattern)
        self.lbl_pattern_state = QLabel("No pattern running.")
        self.lbl_pattern_state.setWordWrap(True)
        self.lbl_pattern_state.setStyleSheet("color: #71717A;")
        stop_row.addWidget(self.lbl_pattern_state, stretch=1)
        patterns_layout.addLayout(stop_row)

        right.addWidget(patterns_box)

        # --- gain / rate (software patterns only) --------------------
        tune_box = QGroupBox("Software pattern tuning")
        tune_layout = QHBoxLayout(tune_box)
        tune_layout.addWidget(QLabel("Update every"))
        self.spin_rate = QSpinBox()
        self.spin_rate.setRange(40, 1000)
        self.spin_rate.setValue(120)
        self.spin_rate.setSuffix(" ms")
        tune_layout.addWidget(self.spin_rate)
        tune_layout.addWidget(QLabel("Gain"))
        self.spin_gain = QSpinBox()
        self.spin_gain.setRange(1, 10)
        self.spin_gain.setValue(int(ctx.settings.audio_gain * 2))
        tune_layout.addWidget(self.spin_gain)
        tune_layout.addStretch()
        right.addWidget(tune_box)

        # --- levels ---------------------------------------------------
        meters = QGroupBox("Levels")
        meters_layout = QVBoxLayout(meters)
        self.bars: dict[str, QProgressBar] = {}
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

        # --- preview --------------------------------------------------
        self.preview = StripPreview()
        right.addWidget(self.preview)

        self.lbl_state = QLabel(
            "Audio backend ready."
            if AudioEngine.available()
            else "sounddevice/numpy not installed — software patterns disabled."
        )
        self.lbl_state.setWordWrap(True)
        right.addWidget(self.lbl_state)

        right.addStretch()
        layout.addLayout(right, stretch=3)

    # =================================================================
    # Pattern helpers
    # =================================================================

    @staticmethod
    def _default_source_for(kind: str) -> str:
        return MIC_USB_INTERNAL if kind == "controller" else MIC_THIRD_PARTY

    def _on_source_changed(self, key: str, combo: QComboBox) -> None:
        value = combo.currentData()
        if value is None:
            return
        self.ctx.settings.pattern_sources[key] = value

    def _start_pattern(self, key: str, name: str, kind: str) -> None:
        self._stop_pattern()

        source = self._source_combos[key].currentData() or self._default_source_for(kind)
        state = PatternState(key=key, name=name, kind=kind, source=source)
        self._active_pattern = state

        if kind == "controller":
            self._start_controller_pattern(state)
        else:
            self._start_software_pattern(state)

        self.btn_stop_pattern.setEnabled(True)
        self.lbl_pattern_state.setText(f"Running: {name} ({kind})")

    def _start_controller_pattern(self, state: PatternState) -> None:
        # Map the mode index out of the pattern key ("ctrl_3" → 3).
        try:
            mode = int(state.key.split("_", 1)[1])
        except (IndexError, ValueError):
            mode = 1
        mode = max(1, min(4, mode))

        # BC 06 02 0B MM 00 55 — mode byte in the "speed" slot.
        frame = encode_effect(CONTROLLER_EFFECT_BYTE, speed=mode)
        self.ctx.log(
            "audio",
            f"Controller pattern '{state.name}': sending {frame} (strip uses its USB mic)",
        )
        self.ctx.run(self.ctx.ble.send_hex_all(frame, label=f"music:{state.key}"))

    def _start_software_pattern(self, state: PatternState) -> None:
        device = self._device_for_source(state.source)

        try:
            if state.source == MIC_THIRD_PARTY:
                # Prefer the primary mic chosen in Options.
                self.engine.start_microphone(device if device is not None and device >= 0 else None)
            else:
                # USB internal is a controller concept; software shouldn't need it.
                self.engine.start_microphone(device if device is not None and device >= 0 else None)
        except Exception as exc:
            self.lbl_state.setText(str(exc))
            self.ctx.log("error", f"Audio start failed: {exc}")
            self._active_pattern = None
            self.btn_stop_pattern.setEnabled(False)
            self.lbl_pattern_state.setText("No pattern running.")
            return

        self._timer.start(self.spin_rate.value())
        self.ctx.log(
            "audio",
            f"Software pattern '{state.name}' started from {state.source}",
        )

    def _device_for_source(self, source: str) -> int:
        """Pick a device index based on the source kind and Options settings."""
        settings = self.ctx.settings
        if source == MIC_USB_INTERNAL:
            # Not a PC device; caller falls back to default mic if used.
            return -1
        # Third-party: prefer the primary mic, fall back to the second mic.
        if settings.audio_mic_device >= 0:
            return settings.audio_mic_device
        if settings.audio_second_mic_device >= 0:
            return settings.audio_second_mic_device
        return -1

    def _stop_pattern(self) -> None:
        self._timer.stop()
        try:
            self.engine.stop()
        except Exception:
            pass
        self._active_pattern = None
        self.btn_stop_pattern.setEnabled(False)
        self.lbl_pattern_state.setText("No pattern running.")
        for bar in self.bars.values():
            bar.setValue(0)

    # =================================================================
    # Media player
    # =================================================================

    def _add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Add audio files",
            "",
            "Audio (*.mp3 *.wav *.flac *.ogg *.m4a);;All files (*)",
        )
        for path in files:
            self.playlist.append(Path(path))
            self.list_files.addItem(QListWidgetItem(Path(path).name))

    def _remove_selected(self) -> None:
        row = self.list_files.currentRow()
        if row < 0:
            return
        self.list_files.takeItem(row)
        del self.playlist[row]
        if self._index == row:
            self._index = -1
        elif self._index > row:
            self._index -= 1

    def _play_selected(self) -> None:
        """Play the highlighted row. This is the fixed Play button behaviour."""
        row = self.list_files.currentRow()
        if row < 0:
            # Nothing selected — do nothing rather than pick something at random.
            self.lbl_now.setText("Select a song in the playlist, then press Play.")
            return
        self._play_index(row)

    def _on_row_double_clicked(self, _item: QListWidgetItem) -> None:
        # Double-click is just a shortcut for "select + Play".
        self._play_selected()

    def _step_track(self, delta: int) -> None:
        if not self.playlist:
            return
        if self._index < 0:
            self._play_index(0)
            return
        self._play_index((self._index + delta) % len(self.playlist))

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
            self._step_track(+1)

    def _on_volume(self, value: int) -> None:
        self.ctx.settings.media_volume = value
        self.audio_out.setVolume(value / 100.0)

    # =================================================================
    # Reactive loop
    # =================================================================

    def _tick(self) -> None:
        frame = self.engine.analyse()

        peak = max(frame.bass, frame.mid, frame.treble, 1e-6)
        for name in ("bass", "mid", "treble"):
            self.bars[name].setValue(int(min(1.0, getattr(frame, name) / peak) * 100))

        gain = self.spin_gain.value() / 2.0
        r, g, b = bands_to_rgb(frame, gain)

        # Pattern-specific brightness shape.
        pattern_key = self._active_pattern.key if self._active_pattern else "spectrum"
        if pattern_key == "pulse":
            # Bass slams brightness: quiet passages go dim, peaks go bright.
            raw_brightness = min(1.0, 0.15 + frame.bass * 6.0 * gain)
        else:
            raw_brightness = rms_to_brightness(
                frame.rms,
                self.ctx.settings.audio_min_brightness / 100.0,
                gain,
            )

        # The Options min/max always wins.
        brightness = self.ctx.settings.clamp_brightness(raw_brightness)

        # The physical protocol sends ONE colour per frame, so the preview
        # shows one colour across the strip honestly.
        self.preview.set_color(
            r, g, b, brightness, self._active_pattern.name if self._active_pattern else "audio"
        )

        if self._busy:
            return
        self._busy = True
        task = self.ctx.run(self.ctx.ble.set_color(r, g, b, brightness))
        task.add_done_callback(lambda _: setattr(self, "_busy", False))

    # =================================================================
    # Lifecycle
    # =================================================================

    def shutdown(self) -> None:
        self._timer.stop()
        try:
            self.engine.stop()
        except Exception:
            pass
        self.player.stop()
