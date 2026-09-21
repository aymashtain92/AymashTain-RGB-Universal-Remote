# Original Path: aymashtain/ui/tabs/music_tab.py

"""Media player plus audio-reactive dancing lights.

Round 3 cleanup
---------------
* **Music patterns only.** The four "Controller mode" entries are gone
  from this tab. Those are hardware effects the strip runs on its own
  and they now live in the Remote tab's new "Light modes" section.
  Keeping them here made it look like they were music sources, which
  they are not.
* **Neutral colour on stop.** Pressing Stop, hitting Esc, or closing the
  tab while a reactive pattern is running now sends the Remote tab's
  current static colour back to the strip. Before, the strip was left
  frozen on whatever colour the last audio frame happened to hit --
  usually a muddy purple.
* **Multi-strip targeting.** Colour frames go through
  ``ctx.resolve_targets()`` so the strip selector bar in the main
  window is honoured. The Music tab used to broadcast to every
  connected strip regardless of the user's selection.
* **``sync_clamp_notice()``** hook added so the main window can refresh
  the music tab's clamp notice when the Options range changes.

Round 2 behaviour kept
----------------------
* The Play button plays the selected row. Double-click is a shortcut.
* Mic selection lives in Options. This tab only picks which *pattern*
  is running, not which device.
* Strip preview uses the neon-capsule widget.
* Brightness is clamped through ``settings.clamp_brightness()``.
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
from ..context import AppContext
from ..widgets import StripPreview

#: Only music-reactive software patterns live here now. The four
#: "Controller mode" entries moved to the Remote tab's Light modes
#: section, which is where the strip runs its own effect.
#: Format: (key, display name, default source).
MUSIC_PATTERNS: list[tuple[str, str, str]] = [
    ("spectrum", "Spectrum", MIC_THIRD_PARTY),
    ("pulse", "Pulse (bass)", MIC_THIRD_PARTY),
]

#: Display order for the per-pattern source combo.
SOURCE_LABELS: list[tuple[str, str]] = [
    (MIC_THIRD_PARTY, "3rd-party mic / file (PC drives the lights)"),
    (MIC_USB_INTERNAL, "USB built-in mic (strip drives itself)"),
]


@dataclass
class PatternState:
    key: str
    name: str
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
        # Right: music patterns + preview + meters
        # =============================================================
        right = QVBoxLayout()

        patterns_box = QGroupBox("Music patterns")
        patterns_layout = QVBoxLayout(patterns_box)

        info = QLabel(
            "These patterns drive the strip from what the PC hears. "
            "The source (primary mic, second mic, or the playing file) is "
            "chosen in Options. Light modes — the ones the strip runs on "
            "its own USB mic — live in the Remote tab."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #71717A;")
        patterns_layout.addWidget(info)

        self.pattern_table = QTableWidget(len(MUSIC_PATTERNS), 3)
        self.pattern_table.setHorizontalHeaderLabels(["Pattern", "Source", ""])
        header = self.pattern_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.pattern_table.verticalHeader().setVisible(False)
        self.pattern_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.pattern_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.pattern_table.setFocusPolicy(Qt.NoFocus)

        self._source_combos: dict[str, QComboBox] = {}
        self._start_buttons: dict[str, QPushButton] = {}

        for row, (key, name, default_source) in enumerate(MUSIC_PATTERNS):
            self.pattern_table.setItem(row, 0, QTableWidgetItem(name))

            combo = QComboBox()
            for value, label in SOURCE_LABELS:
                combo.addItem(label, value)
            saved = ctx.settings.pattern_sources.get(key, default_source)
            idx = combo.findData(saved)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            combo.currentIndexChanged.connect(
                lambda _=0, k=key, c=combo: self._on_source_changed(k, c)
            )
            self._source_combos[key] = combo
            self.pattern_table.setCellWidget(row, 1, combo)

            btn = QPushButton("Start")
            btn.setProperty("accent", True)
            btn.clicked.connect(
                lambda _=False, k=key, n=name: self._start_pattern(k, n)
            )
            self._start_buttons[key] = btn
            self.pattern_table.setCellWidget(row, 2, btn)

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

        # --- tuning ---------------------------------------------------
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

        # --- clamp notice ---------------------------------------------
        self.lbl_clamp = QLabel("")
        self.lbl_clamp.setWordWrap(True)
        self.lbl_clamp.setStyleSheet("color: #71717A;")
        right.addWidget(self.lbl_clamp)
        self._refresh_clamp_notice()

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
    # Clamp notice (for the main window fan-out)
    # =================================================================

    def _refresh_clamp_notice(self) -> None:
        lo = self.ctx.settings.brightness_min
        hi = self.ctx.settings.brightness_max
        if lo <= 0 and hi >= 100:
            self.lbl_clamp.setText("")
        else:
            self.lbl_clamp.setText(
                f"Brightness is clamped to {lo}%-{hi}% by the Options tab."
            )

    def sync_clamp_notice(self) -> None:
        """Called by the main window when Options changes the brightness range."""
        self._refresh_clamp_notice()

    # =================================================================
    # Pattern helpers
    # =================================================================

    def _on_source_changed(self, key: str, combo: QComboBox) -> None:
        value = combo.currentData()
        if value is None:
            return
        self.ctx.settings.pattern_sources[key] = value

    def _start_pattern(self, key: str, name: str) -> None:
        # Stop whatever was running first so we never layer patterns.
        self._stop_pattern(send_neutral=False)

        source = self._source_combos[key].currentData() or MIC_THIRD_PARTY
        state = PatternState(key=key, name=name, source=source)
        self._active_pattern = state

        # Only third-party sources are useful on the PC side; the USB
        # internal mic is the strip's own thing and is handled by the
        # controller patterns (now in Remote). If the user picked USB
        # here we fall back to the PC mic so something actually runs.
        device = self._device_for_source(source)
        try:
            self.engine.start_microphone(device if device >= 0 else None)
        except Exception as exc:
            self.lbl_state.setText(str(exc))
            self.ctx.log("error", f"Audio start failed: {exc}")
            self._active_pattern = None
            self.btn_stop_pattern.setEnabled(False)
            self.lbl_pattern_state.setText("No pattern running.")
            return

        self._timer.start(self.spin_rate.value())
        self.btn_stop_pattern.setEnabled(True)
        self.lbl_pattern_state.setText(f"Running: {name}")
        self.ctx.log("audio", f"Music pattern '{name}' started from {source}")

    def _device_for_source(self, source: str) -> int:
        settings = self.ctx.settings
        if source == MIC_USB_INTERNAL:
            return -1
        if settings.audio_mic_device >= 0:
            return settings.audio_mic_device
        if settings.audio_second_mic_device >= 0:
            return settings.audio_second_mic_device
        return -1

    def _stop_pattern(self, send_neutral: bool = True) -> None:
        was_running = self._active_pattern is not None
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

        if was_running and send_neutral:
            # Send the Remote tab's current static colour back to the
            # strip so it does not stay frozen on whatever the last
            # audio frame happened to be.
            self.ctx.run(self._send_stable_colour())

    async def _send_stable_colour(self) -> None:
        r, g, b = self.ctx.settings.last_color
        brightness = self.ctx.settings.clamp_brightness(
            self.ctx.settings.last_brightness / 100.0
        )
        targets = self.ctx.resolve_targets()
        await self.ctx.ble.set_color(
            r, g, b, brightness, addresses=targets
        )
        self.ctx.log(
            "audio",
            f"Pattern stopped - stable colour restored "
            f"rgb({r},{g},{b}) at {int(round(brightness * 100))}%",
        )
        self.preview.set_color(r, g, b, brightness, f"rgb({r},{g},{b})")

    def _stop_reacting(self) -> None:
        """Alias used by MainWindow.stop_all_activity() and the Esc shortcut.

        Same as ``_stop_pattern(send_neutral=True)``. Kept as a stable
        public name so the main window never reaches into a private
        method.
        """
        self._stop_pattern(send_neutral=True)

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
            self.lbl_now.setText("Select a song in the playlist, then press Play.")
            return
        self._play_index(row)

    def _on_row_double_clicked(self, _item: QListWidgetItem) -> None:
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

        pattern_key = self._active_pattern.key if self._active_pattern else "spectrum"
        if pattern_key == "pulse":
            raw_brightness = min(1.0, 0.15 + frame.bass * 6.0 * gain)
        else:
            raw_brightness = rms_to_brightness(
                frame.rms,
                self.ctx.settings.audio_min_brightness / 100.0,
                gain,
            )

        brightness = self.ctx.settings.clamp_brightness(raw_brightness)

        self.preview.set_color(
            r, g, b, brightness,
            self._active_pattern.name if self._active_pattern else "audio",
        )

        if self._busy:
            return
        self._busy = True
        targets = self.ctx.resolve_targets()
        task = self.ctx.run(
            self.ctx.ble.set_color(r, g, b, brightness, addresses=targets)
        )
        task.add_done_callback(lambda _: setattr(self, "_busy", False))

    # =================================================================
    # Lifecycle
    # =================================================================

    def shutdown(self) -> None:
        # Do NOT send neutral colour on app close -- the user may be
        # shutting down mid-look and we do not want to overwrite their
        # last static colour on the way out.
        self._stop_pattern(send_neutral=False)
        self.player.stop()
