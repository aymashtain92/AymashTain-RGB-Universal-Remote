"""MR Star BLE protocol.

Frame layout (all values big-endian, ``55`` terminator):

===============  ==========================================
Power            ``BC 01 01 XX 55``           XX = 01 on / 00 off
Static mode      ``BC 04 01 00 55``
Color            ``BC 04 06 HHHH SSSS 0000 55`` hue 0..359, sat 0..1000
Brightness       ``BC 05 06 BBBB 00000000 55`` value 0..1024
Effect           ``BC 06 02 XX 0000 55``
Captured mode    ``BC 0F ...`` / ``BC 11 ...``
===============  ==========================================

Colour and brightness are deliberately **two separate frames**. Packing the
value channel into the colour frame is what produces the washed-out / white
tinted output that older builds suffered from: the controller treats the
trailing bytes of ``BC0406`` as reserved and clamps saturation when they are
non-zero.
"""

from __future__ import annotations

import colorsys
import re
from collections.abc import Iterable

MRSTAR_SERVICE_UUID = "00002022-0000-1000-8000-00805f9b34fb"
MRSTAR_WRITE_CHAR_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"

CMD_ON = "BC01010155"
CMD_OFF = "BC01010055"
CMD_STATIC = "BC04010055"

HUE_MAX = 359
SATURATION_MAX = 1000
BRIGHTNESS_MAX = 1024

#: Effect byte -> human name. Values marked "captured" came from sniffing the
#: vendor app; the rest follow the documented BC0602 range.
EFFECTS: dict[str, str] = {
    "01": "Static",
    "02": "Breathe",
    "03": "Strobe",
    "04": "Flash",
    "05": "Fade",
    "06": "Rainbow",
    "07": "Rainbow fade",
    "08": "Chase",
    "09": "Scroll",
    "0A": "Twinkle",
    "0B": "Music",
}

SCROLL_SETUP = ["BC0F010155", "BC11010455"]
SCROLL_DATA = [
    "BC0406000003E8000055",
    "BC0406013E0032000055",
    "BC04060131002B000055",
    "BC040600E200A8000055",
    "BC040600E400B8000055",
    "BC040600E60091000055",
    "BC040600E90046000055",
    "BC040600F00027000055",
    "BC040600F00023000055",
    "BC040600F00023000055",
    "BC040600FF003E000055",
    "BC040601050081000055",
    "BC0406011B00EB000055",
    "BC0406013D01A3000055",
    "BC0406014D0230000055",
    "BC04060161026F000055",
    "BC0406001B02FC000055",
    "BC0406002C0372000055",
    "BC0406003E02E1000055",
    "BC0406005A0215000055",
    "BC0406008701BF000055",
    "BC040600B00215000055",
    "BC040600C90296000055",
    "BC040600DF0314000055",
    "BC040600F7033B000055",
]
SCROLL_END = ["BC0F010155", "BC11010455"]
SCROLL_MACRO = [*SCROLL_SETUP, *SCROLL_DATA, *SCROLL_END]


def clean_hex(value: str) -> str:
    return re.sub(r"[^0-9A-Fa-f]", "", value or "").upper()


def validate_hex(value: str) -> tuple[bool, str]:
    cleaned = clean_hex(value)
    if not cleaned:
        return False, "empty command"
    if len(cleaned) % 2:
        return False, "odd number of hex digits"
    return True, "valid"


def hex_to_bytes(value: str) -> bytes:
    cleaned = clean_hex(value)
    valid, reason = validate_hex(cleaned)
    if not valid:
        raise ValueError(f"Cannot encode command: {reason}")
    return bytes.fromhex(cleaned)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def clamp_byte(value: float) -> int:
    return int(clamp(round(value), 0, 255))


def encode_power(on: bool) -> str:
    return CMD_ON if on else CMD_OFF


def encode_static() -> str:
    return CMD_STATIC


def encode_color(r: int, g: int, b: int) -> str:
    """Hue/saturation frame. Brightness is *not* encoded here."""
    r, g, b = clamp_byte(r), clamp_byte(g), clamp_byte(b)
    if r + g + b < 8:
        return CMD_OFF

    hue, saturation, _value = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    hue_deg = int(round(hue * 360.0)) % 360
    sat_units = int(clamp(round(saturation * SATURATION_MAX), 0, SATURATION_MAX))
    return f"BC0406{hue_deg:04X}{sat_units:04X}000055"


def encode_color_hs(hue_deg: int, saturation: float) -> str:
    """Encode directly from hue degrees and 0..1 saturation."""
    hue = int(round(hue_deg)) % 360
    sat_units = int(clamp(round(saturation * SATURATION_MAX), 0, SATURATION_MAX))
    return f"BC0406{hue:04X}{sat_units:04X}000055"


def encode_brightness(brightness: float) -> str:
    """``brightness`` is 0.0..1.0 and maps onto the 0..1024 hardware range."""
    value = int(clamp(round(clamp(brightness, 0.0, 1.0) * BRIGHTNESS_MAX), 0, BRIGHTNESS_MAX))
    return f"BC0506{value:04X}0000000055"


def encode_effect(effect_byte: str | int, speed: int | None = None) -> str:
    if isinstance(effect_byte, int):
        code = f"{clamp_byte(effect_byte):02X}"
    else:
        code = clean_hex(effect_byte)[:2].zfill(2)
    tail = f"{clamp_byte(speed):02X}00" if speed is not None else "0000"
    return f"BC0602{code}{tail}55"


def frames_for_rgb(r: int, g: int, b: int, brightness: float) -> list[tuple[str, str]]:
    """The exact frames, in order, needed to show an RGB colour.

    Returns ``(label, hex)`` pairs so callers can log what each frame did.
    """
    return [
        ("color", encode_color(r, g, b)),
        ("brightness", encode_brightness(brightness)),
    ]


# --- Classic Magic Home / Triones clones -----------------------------------


def encode_classic_power(on: bool) -> str:
    return "CC2333" if on else "CC2433"


def encode_classic_color(r: int, g: int, b: int) -> str:
    return f"56{clamp_byte(r):02X}{clamp_byte(g):02X}{clamp_byte(b):02X}00F0AA"


# --- Decoding ---------------------------------------------------------------

_CONFIDENCE_DOCUMENTED = "documented"
_CONFIDENCE_CAPTURED = "captured"
_CONFIDENCE_UNCONFIRMED = "unconfirmed"


def decode_hex_command(value: str) -> dict:
    """Classify a frame without sending it (used by the console and lab tabs)."""
    cleaned = clean_hex(value)
    valid, reason = validate_hex(cleaned)
    if not valid:
        return {
            "valid": False,
            "hex": cleaned,
            "family": "malformed",
            "meaning": reason,
            "confidence": "unknown",
        }

    base = {"valid": True, "hex": cleaned}

    if cleaned in (CMD_ON, CMD_OFF):
        return {
            **base,
            "family": "mrstar_power",
            "meaning": "Power on" if cleaned == CMD_ON else "Power off",
            "confidence": _CONFIDENCE_DOCUMENTED,
        }

    if cleaned == CMD_STATIC:
        return {
            **base,
            "family": "mrstar_static",
            "meaning": "Static mode",
            "confidence": _CONFIDENCE_CAPTURED,
        }

    if cleaned.startswith("BC0406"):
        result = {
            **base,
            "family": "mrstar_color",
            "meaning": "Colour (hue/saturation)",
            "confidence": _CONFIDENCE_UNCONFIRMED,
        }
        if len(cleaned) == 20 and cleaned.endswith("55"):
            hue = int(cleaned[6:10], 16)
            saturation = int(cleaned[10:14], 16)
            reserved = cleaned[14:18]
            in_range = hue <= HUE_MAX and saturation <= SATURATION_MAX and reserved == "0000"
            result.update(
                hue=hue,
                saturation=saturation,
                saturation_fraction=round(saturation / SATURATION_MAX, 4),
                reserved=reserved,
                rgb=hs_to_rgb(hue, saturation / SATURATION_MAX),
                meaning=f"Colour hue {hue}° sat {saturation / 10:.1f}%",
                confidence=_CONFIDENCE_DOCUMENTED if in_range else "invalid_fields",
            )
        return result

    if cleaned.startswith("BC0506"):
        result = {
            **base,
            "family": "mrstar_brightness",
            "meaning": "Brightness",
            "confidence": _CONFIDENCE_UNCONFIRMED,
        }
        if len(cleaned) == 20 and cleaned.endswith("55"):
            level = int(cleaned[6:10], 16)
            reserved = cleaned[10:18]
            in_range = level <= BRIGHTNESS_MAX and reserved == "00000000"
            result.update(
                brightness_value=level,
                brightness_fraction=round(level / BRIGHTNESS_MAX, 4),
                reserved=reserved,
                meaning=f"Brightness {level}/{BRIGHTNESS_MAX} ({level / BRIGHTNESS_MAX:.0%})",
                confidence=_CONFIDENCE_DOCUMENTED if in_range else "invalid_fields",
            )
        return result

    if cleaned.startswith("BC06"):
        effect_byte = cleaned[6:8] if len(cleaned) >= 8 else ""
        return {
            **base,
            "family": "mrstar_effect",
            "meaning": f"Effect 0x{effect_byte or '??'} ({EFFECTS.get(effect_byte, 'unnamed')})",
            "effect_byte": effect_byte,
            "confidence": _CONFIDENCE_DOCUMENTED if effect_byte in EFFECTS else _CONFIDENCE_CAPTURED,
        }

    if cleaned.startswith(("BC0F", "BC11")):
        return {
            **base,
            "family": "mrstar_captured_mode",
            "meaning": "Captured mode / scroll frame",
            "confidence": _CONFIDENCE_CAPTURED,
        }

    if cleaned.startswith("CC"):
        return {
            **base,
            "family": "classic_magic_home",
            "meaning": "Classic Magic Home power",
            "confidence": _CONFIDENCE_CAPTURED,
        }

    if cleaned.startswith("56"):
        result = {
            **base,
            "family": "classic_magic_home_color",
            "meaning": "Classic Magic Home RGB",
            "confidence": _CONFIDENCE_CAPTURED,
        }
        if len(cleaned) == 14:
            result["rgb"] = (
                int(cleaned[2:4], 16),
                int(cleaned[4:6], 16),
                int(cleaned[6:8], 16),
            )
        return result

    if cleaned.startswith("7E"):
        return {
            **base,
            "family": "experimental_7e",
            "meaning": "Experimental 7E frame",
            "confidence": _CONFIDENCE_UNCONFIRMED,
        }

    return {
        **base,
        "family": "unknown",
        "meaning": "Unrecognised frame",
        "confidence": "unknown",
    }


def hs_to_rgb(hue_deg: float, saturation: float) -> tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb((hue_deg % 360) / 360.0, clamp(saturation, 0.0, 1.0), 1.0)
    return clamp_byte(r * 255), clamp_byte(g * 255), clamp_byte(b * 255)


def describe_frames(frames: Iterable[str]) -> list[dict]:
    return [decode_hex_command(frame) for frame in frames]
