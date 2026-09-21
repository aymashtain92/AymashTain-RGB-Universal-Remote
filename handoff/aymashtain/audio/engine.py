"""Audio capture and the music → colour mapping used by dancing-lights mode.

``sounddevice``/``numpy`` are imported lazily: the app must still start on a
machine with no working audio backend, it just disables this tab.
"""

from __future__ import annotations

import queue
import sys
import threading
import time
from dataclasses import dataclass

SAMPLE_RATE = 22050
BLOCK_SIZE = 1024
BANDS = {"bass": (20, 250), "mid": (250, 2000), "treble": (2000, 8000)}


@dataclass
class AudioFrame:
    bass: float = 0.0
    mid: float = 0.0
    treble: float = 0.0
    rms: float = 0.0
    beat: bool = False


def bands_to_rgb(frame: AudioFrame, gain: float = 1.0) -> tuple[int, int, int]:
    """Map the three bands onto R/G/B with a normalised, gamma-ish curve.

    Bass drives red, mids green, treble blue; the strongest band is scaled to
    full so quiet passages still produce saturated colour instead of mud.
    """
    values = [max(0.0, frame.bass), max(0.0, frame.mid), max(0.0, frame.treble)]
    peak = max(values)
    if peak <= 1e-9:
        return (0, 0, 0)
    scaled = [min(1.0, (value / peak) * gain) ** 0.75 for value in values]
    return tuple(int(round(channel * 255)) for channel in scaled)  # type: ignore[return-value]


def rms_to_brightness(rms: float, minimum: float = 0.15, gain: float = 1.0) -> float:
    """Loudness → 0..1 brightness with a floor so the strip never blacks out."""
    level = min(1.0, max(0.0, rms * 8.0 * gain) ** 0.6)
    return minimum + (1.0 - minimum) * level


class AudioEngine:
    """Captures from a microphone, Windows loopback, or an audio file."""

    def __init__(self, sample_rate: int = SAMPLE_RATE, block: int = BLOCK_SIZE) -> None:
        self.sample_rate = sample_rate
        self.block = block
        self._queue: queue.Queue = queue.Queue(maxsize=8)
        self._stream = None
        self._stop = threading.Event()
        self._file_data = None
        self._file_pos = 0
        self._last_bass = 0.0
        self._beat_cooldown = 0.0
        self.frame = AudioFrame()
        self.error: str | None = None

    # --- backend ----------------------------------------------------------

    @staticmethod
    def available() -> bool:
        try:
            import numpy  # noqa: F401
            import sounddevice  # noqa: F401
        except Exception:
            return False
        return True

    @staticmethod
    def _sd():
        import sounddevice as sd

        return sd

    def list_inputs(self) -> list[tuple[int, str, str]]:
        if not self.available():
            return []
        sd = self._sd()
        hostapis = sd.query_hostapis()
        return [
            (index, device["name"], hostapis[device["hostapi"]]["name"])
            for index, device in enumerate(sd.query_devices())
            if device["max_input_channels"] > 0
        ]

    def list_outputs(self) -> list[tuple[int, str, str]]:
        if not self.available():
            return []
        sd = self._sd()
        hostapis = sd.query_hostapis()
        return [
            (index, device["name"], hostapis[device["hostapi"]]["name"])
            for index, device in enumerate(sd.query_devices())
            if device["max_output_channels"] > 0
        ]

    # --- sources ----------------------------------------------------------

    def start_microphone(self, device_index: int | None = None) -> None:
        sd = self._require()
        self.stop()

        def callback(indata, _frames, _time, _status):
            self._push(indata.copy())

        self._stream = sd.InputStream(
            device=device_index,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.block,
            callback=callback,
        )
        self._stream.start()

    def start_system_loopback(self, output_index: int | None = None) -> None:
        """WASAPI loopback (Windows). Falls back to Stereo Mix style inputs."""
        sd = self._require()
        self.stop()

        def callback(indata, _frames, _time, _status):
            self._push(indata.copy())

        if sys.platform == "win32":
            device = output_index if output_index is not None else sd.default.device[1]
            info = sd.query_devices(device)
            try:
                self._stream = sd.InputStream(
                    device=device,
                    channels=min(2, info["max_output_channels"]),
                    samplerate=self.sample_rate,
                    blocksize=self.block,
                    extra_settings=sd.WasapiSettings(loopback=True),
                    callback=callback,
                )
                self._stream.start()
                return
            except Exception as exc:
                self.error = f"WASAPI loopback unavailable: {exc}"

        for index, device in enumerate(sd.query_devices()):
            name = device["name"].lower()
            if device["max_input_channels"] > 0 and any(
                hint in name for hint in ("loopback", "stereo mix", "what u hear", "monitor")
            ):
                self._stream = sd.InputStream(
                    device=index,
                    channels=min(2, device["max_input_channels"]),
                    samplerate=self.sample_rate,
                    blocksize=self.block,
                    callback=callback,
                )
                self._stream.start()
                return

        raise RuntimeError(
            "No loopback device found. Use Microphone mode and select your "
            "virtual cable / Stereo Mix input."
        )

    def start_file(self, path: str) -> None:
        sd = self._require()
        import soundfile as sf

        self.stop()
        data, sample_rate = sf.read(path, dtype="float32", always_2d=True)
        if data.shape[1] > 1:
            data = data.mean(axis=1, keepdims=True)
        self._file_data = data
        self._file_pos = 0
        self._stop.clear()

        def callback(outdata, frames, _time, _status):
            if self._stop.is_set() or self._file_data is None:
                outdata[:] = 0
                raise sd.CallbackStop
            remaining = len(self._file_data) - self._file_pos
            if remaining <= 0:
                outdata[:] = 0
                raise sd.CallbackStop
            take = min(frames, remaining)
            outdata[:take] = self._file_data[self._file_pos : self._file_pos + take]
            outdata[take:] = 0
            self._file_pos += take
            self._push(outdata[:take].copy())

        self._stream = sd.OutputStream(
            samplerate=sample_rate, channels=1, blocksize=self.block, callback=callback
        )
        self._stream.start()

    def stop(self) -> None:
        self._stop.set()
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
        self._file_data = None
        self._file_pos = 0

    @property
    def running(self) -> bool:
        return self._stream is not None

    # --- analysis ---------------------------------------------------------

    def analyse(self) -> AudioFrame:
        """Consume the newest block and update band energies. Cheap enough for 30 Hz."""
        import numpy as np

        latest = None
        while True:
            try:
                latest = self._queue.get_nowait()
            except queue.Empty:
                break
        if latest is None:
            return self.frame

        samples = latest[:, 0].astype(np.float32)
        if samples.size < 64:
            return self.frame

        windowed = samples * np.hanning(samples.size)
        spectrum = np.abs(np.fft.rfft(windowed))
        freqs = np.fft.rfftfreq(samples.size, 1.0 / self.sample_rate)

        def band_energy(low: float, high: float) -> float:
            mask = (freqs >= low) & (freqs < high)
            return float(np.mean(spectrum[mask])) if mask.any() else 0.0

        bass = band_energy(*BANDS["bass"])
        mid = band_energy(*BANDS["mid"])
        treble = band_energy(*BANDS["treble"])
        rms = float(np.sqrt(np.mean(samples**2)))

        now = time.time()
        beat = bass > self._last_bass * 1.6 and bass > 0.02 and now > self._beat_cooldown
        if beat:
            self._beat_cooldown = now + 0.15
        self._last_bass = 0.85 * self._last_bass + 0.15 * bass

        self.frame = AudioFrame(bass=bass, mid=mid, treble=treble, rms=rms, beat=beat)
        return self.frame

    # --- internals --------------------------------------------------------

    def _require(self):
        if not self.available():
            raise RuntimeError("sounddevice/numpy are not installed")
        self.error = None
        return self._sd()

    def _push(self, block) -> None:
        try:
            self._queue.put_nowait(block)
        except queue.Full:
            pass
