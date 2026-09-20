from __future__ import annotations

import numpy as np

from aymashtain.audio.engine import AudioFrame, bands_to_rgb, rms_to_brightness
from aymashtain.ui.tabs.lab_tab import diff_frames
from aymashtain.vision.camera import analyse_region, crop_region


def solid(rgb, size=40):
    frame = np.zeros((size, size, 3), dtype=np.uint8)
    frame[:, :] = rgb
    return frame


def test_crop_region():
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    cropped = crop_region(frame, (0.25, 0.5, 0.75, 1.0))
    assert cropped.shape[:2] == (50, 100)


def test_analyse_pure_red():
    result = analyse_region(solid((255, 0, 0)), expected_rgb=(255, 0, 0))
    assert result.hue_error < 5
    assert result.white_contamination < 0.05
    assert result.passed


def test_analyse_detects_white_contamination():
    result = analyse_region(solid((255, 180, 180)), expected_rgb=(255, 0, 0))
    assert result.white_contamination > 0.5
    assert not result.passed


def test_analyse_dark_region():
    result = analyse_region(solid((2, 2, 2)))
    assert result.brightness < 0.05


def test_bands_to_rgb_and_brightness():
    frame = AudioFrame(bass=1.0, mid=0.0, treble=0.0, rms=0.5, beat=True)
    r, g, b = bands_to_rgb(frame)
    assert r > g and r > b
    assert 0 <= rms_to_brightness(0.0, minimum=0.2) <= 1.0
    assert rms_to_brightness(0.0, minimum=0.2) >= 0.2
    assert rms_to_brightness(10.0) <= 1.0


def test_diff_frames():
    diffs = diff_frames("BC0406000003E8000055", "BC0406005A03E8000055")
    assert diffs == [(4, "00", "5A")]
    assert diff_frames("BC01", "BC01") == []
