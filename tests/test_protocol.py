from __future__ import annotations

import pytest

from aymashtain.protocol import (
    CMD_OFF,
    CMD_ON,
    clean_hex,
    decode_hex_command,
    encode_brightness,
    encode_classic_color,
    encode_color,
    encode_effect,
    encode_power,
    frames_for_rgb,
    hex_to_bytes,
    validate_hex,
)
from aymashtain.protocol.mrstar import encode_color_hs, hs_to_rgb


def test_clean_and_validate():
    assert clean_hex("bc 04:06-00") == "BC040600"
    assert validate_hex("BC0101")[0]
    assert not validate_hex("")[0]
    assert not validate_hex("BC0")[0]
    with pytest.raises(ValueError):
        hex_to_bytes("ZZ")


def test_power_frames():
    assert encode_power(True) == CMD_ON == "BC01010155"
    assert encode_power(False) == CMD_OFF == "BC01010055"


@pytest.mark.parametrize(
    "rgb,hue",
    [((255, 0, 0), 0), ((0, 255, 0), 120), ((0, 0, 255), 240), ((255, 255, 0), 60)],
)
def test_encode_color_hue(rgb, hue):
    frame = encode_color(*rgb)
    info = decode_hex_command(frame)
    assert info["family"] == "mrstar_color"
    assert info["hue"] == hue
    assert info["saturation"] == 1000


def test_encode_color_never_carries_brightness():
    """Dim and bright red must produce the *same* colour frame."""
    assert encode_color(255, 0, 0) == encode_color(40, 0, 0)
    assert encode_color(255, 0, 0)[14:18] == "0000"


def test_encode_color_black_is_off():
    assert encode_color(0, 0, 0) == CMD_OFF


def test_brightness_range():
    assert decode_hex_command(encode_brightness(1.0))["brightness_value"] == 1024
    assert decode_hex_command(encode_brightness(0.0))["brightness_value"] == 0
    assert decode_hex_command(encode_brightness(0.5))["brightness_value"] == 512
    # out of range input is clamped, never wrapped
    assert decode_hex_command(encode_brightness(4.0))["brightness_value"] == 1024
    assert len(encode_brightness(0.25)) == 20


def test_frames_for_rgb_is_two_separate_frames():
    frames = frames_for_rgb(0, 128, 255, 0.5)
    assert [label for label, _ in frames] == ["color", "brightness"]
    colour, brightness = (frame for _, frame in frames)
    assert colour.startswith("BC0406")
    assert brightness.startswith("BC0506")


def test_effect_frame():
    assert encode_effect("06") == "BC0602060000" + "55"
    assert decode_hex_command(encode_effect(6))["effect_byte"] == "06"


def test_hs_roundtrip():
    frame = encode_color_hs(200, 0.8)
    info = decode_hex_command(frame)
    assert info["hue"] == 200
    assert info["saturation"] == 800
    assert hs_to_rgb(0, 1.0) == (255, 0, 0)


def test_classic_frames():
    assert encode_classic_color(18, 52, 86) == "56123456" + "00F0AA"
    assert decode_hex_command("56123456" + "00F0AA")["rgb"] == (18, 52, 86)


def test_decode_malformed():
    info = decode_hex_command("BC0")
    assert info["valid"] is False
    assert info["family"] == "malformed"
