"""Webcam verification: measure what the strip actually emitted.

``analyse_region`` is pure numpy so it can be unit tested without a camera.
"""

from __future__ import annotations

import colorsys
from collections.abc import Sequence
from dataclasses import dataclass, field


@dataclass
class Sample:
    rgb: tuple[int, int, int]
    hue: float
    saturation: float
    brightness: float
    white_contamination: float
    expected_rgb: tuple[int, int, int] | None = None
    hue_error: float | None = None
    label: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        if self.hue_error is None:
            return True
        return self.hue_error <= 20.0 and self.white_contamination <= 0.45


def _to_float_array(frame):
    import numpy as np

    array = np.asarray(frame, dtype="float32")
    if array.ndim != 3 or array.shape[2] < 3:
        raise ValueError("frame must be HxWx3 RGB")
    return array[:, :, :3]


def crop_region(frame, region: Sequence[float]):
    """``region`` is (x0, y0, x1, y1) in 0..1 coordinates."""
    height, width = frame.shape[0], frame.shape[1]
    x0, y0, x1, y1 = region
    left, right = sorted((int(x0 * width), int(x1 * width)))
    top, bottom = sorted((int(y0 * height), int(y1 * height)))
    right = max(right, left + 1)
    bottom = max(bottom, top + 1)
    return frame[top:bottom, left:right]


def analyse_region(
    frame,
    region: Sequence[float] = (0.3, 0.35, 0.7, 0.65),
    expected_rgb: tuple[int, int, int] | None = None,
    label: str = "",
) -> Sample:
    """Average the sample window and report colour quality.

    ``white_contamination`` is ``min(r,g,b) / max(r,g,b)``: 0 means a fully
    saturated colour, 1 means the strip is washing the colour out with white,
    which is the exact symptom of merging brightness into the colour frame.
    """

    patch = crop_region(_to_float_array(frame), region)
    mean = patch.reshape(-1, 3).mean(axis=0)
    r, g, b = (float(channel) for channel in mean)
    peak = max(r, g, b)
    floor = min(r, g, b)

    hue, saturation, value = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    contamination = float(floor / peak) if peak > 1e-6 else 0.0

    hue_error = None
    if expected_rgb is not None:
        expected_hue = colorsys.rgb_to_hsv(*(channel / 255.0 for channel in expected_rgb))[0] * 360
        delta = abs((hue * 360) - expected_hue) % 360
        hue_error = float(min(delta, 360 - delta))

    return Sample(
        rgb=(int(round(r)), int(round(g)), int(round(b))),
        hue=float(hue * 360.0),
        saturation=float(saturation),
        brightness=float(value),
        white_contamination=contamination,
        expected_rgb=expected_rgb,
        hue_error=hue_error,
        label=label,
        meta={"pixels": int(patch.shape[0] * patch.shape[1])},
    )


class CameraVerifier:
    """Thin OpenCV wrapper: open a camera, grab frames, analyse the window."""

    def __init__(self, index: int = 0) -> None:
        self.index = index
        self.capture = None
        self.samples: list[Sample] = []

    @staticmethod
    def available() -> bool:
        try:
            import cv2  # noqa: F401
        except Exception:
            return False
        return True

    def open(self) -> bool:
        import cv2

        self.close()
        capture = cv2.VideoCapture(self.index)
        if not capture.isOpened():
            capture.release()
            return False
        self.capture = capture
        return True

    def close(self) -> None:
        capture, self.capture = self.capture, None
        if capture is not None:
            capture.release()

    @property
    def is_open(self) -> bool:
        return self.capture is not None

    def read_rgb(self):
        """Return the current frame as an RGB array, or ``None``."""
        if self.capture is None:
            return None
        import cv2

        ok, frame = self.capture.read()
        if not ok:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def sample(
        self,
        region: Sequence[float] = (0.3, 0.35, 0.7, 0.65),
        expected_rgb: tuple[int, int, int] | None = None,
        label: str = "",
        count: int = 1,
    ) -> Sample | None:
        """Average ``count`` grabs so a settling strip is measured fairly."""
        import numpy as np

        frames = []
        for _ in range(max(1, count)):
            frame = self.read_rgb()
            if frame is None:
                continue
            frames.append(frame.astype("float32"))
        if not frames:
            return None

        averaged = np.mean(np.stack(frames, axis=0), axis=0)
        result = analyse_region(averaged, region, expected_rgb, label)
        self.samples.append(result)
        return result

    def clear(self) -> None:
        self.samples.clear()
