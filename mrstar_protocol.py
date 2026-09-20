# AymashTain LED RGB Remote v0.41
from __future__ import annotations

import colorsys
import re


MRSTAR_SERVICE_UUID = "00002022-0000-1000-8000-00805f9b34fb"
MRSTAR_WRITE_CHAR_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"

CMD_ON = "BC01010155"
CMD_OFF = "BC01010055"
CMD_STATIC = "BC04010055"


SCROLL_SETUP = [
    "BC0F010155",
    "BC11010455",
]

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

SCROLL_END = [
    "BC0F010155",
    "BC11010455",
]

SCROLL_MACRO = SCROLL_SETUP + SCROLL_DATA + SCROLL_END


def clean_hex(value: str) -> str:
    return re.sub(r"[^0-9A-Fa-f]", "", value or "").upper()


def hex_to_bytes(value: str) -> bytes:
    cleaned = clean_hex(value)

    if not cleaned:
        raise ValueError("Hex command is empty.")

    if len(cleaned) % 2:
        raise ValueError("Hex command has an odd number of digits.")

    return bytes.fromhex(cleaned)


def validate_hex(value: str) -> tuple[bool, str]:
    cleaned = clean_hex(value)

    if not cleaned:
        return False, "empty command"

    if len(cleaned) % 2:
        return False, "odd number of hex digits"

    try:
        bytes.fromhex(cleaned)
    except ValueError:
        return False, "invalid hex characters"

    return True, "valid"


def clamp_byte(value: int) -> int:
    return max(0, min(255, int(value)))


def clamp_brightness(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def encode_mrstar_power(on: bool) -> str:
    return CMD_ON if on else CMD_OFF


def encode_mrstar_static() -> str:
    return CMD_STATIC


def encode_mrstar_color(
    r: int,
    g: int,
    b: int,
    brightness=1.0,
    pure=True,
) -> str:
    """
    Documented MR Star color format:

        BC 04 06 HH HH SS SS 00 00 55

    Brightness is deliberately not encoded here.
    Send encode_mrstar_brightness() separately.
    """
    del brightness
    del pure

    r = clamp_byte(r)
    g = clamp_byte(g)
    b = clamp_byte(b)

    if r + g + b < 8:
        return CMD_OFF

    hue, saturation, _value = colorsys.rgb_to_hsv(
        r / 255.0,
        g / 255.0,
        b / 255.0,
    )

    hue_value = int(round(hue * 360.0)) % 360
    saturation_value = int(round(saturation * 1000.0))
    saturation_value = max(0, min(1000, saturation_value))

    return f"BC0406{hue_value:04X}{saturation_value:04X}000055"


def encode_mrstar_neutral_color() -> str:
    """Neutral color command; brightness remains a separate command."""
    return "BC0406000000000055"


def encode_mrstar_brightness(brightness=1.0) -> str:
    """
    Documented MR Star brightness format:

        BC 05 06 BB BB 00 00 00 00 55

    Brightness is from 0.0 to 1.0 and maps to 0..1024.
    """
    value = int(round(clamp_brightness(brightness) * 1024.0))
    value = max(0, min(1024, value))

    return f"BC0506{value:04X}0000000055"


def encode_mrstar_color_sequence(
    r: int,
    g: int,
    b: int,
    brightness=1.0,
) -> list[tuple[str, str]]:
    """Return color and brightness in the required send order."""
    return [
        ("color", encode_mrstar_color(r, g, b)),
        ("brightness", encode_mrstar_brightness(brightness)),
    ]


def encode_classic_magic_home_on() -> str:
    return "CC2333"


def encode_classic_magic_home_off() -> str:
    return "CC2433"


def encode_classic_magic_home_color(r: int, g: int, b: int) -> str:
    return f"56{clamp_byte(r):02X}{clamp_byte(g):02X}{clamp_byte(b):02X}00F0AA"


def decode_hex_command(hexstr: str) -> dict:
    """Classify a command without sending it."""
    cleaned = clean_hex(hexstr)
    valid, reason = validate_hex(cleaned)

    if not valid:
        return {
            "valid": False,
            "hex": cleaned,
            "family": "malformed",
            "meaning": reason,
        }

    if cleaned == CMD_ON:
        return {
            "valid": True,
            "hex": cleaned,
            "family": "mrstar_power",
            "meaning": "Power on",
            "confidence": "documented",
        }

    if cleaned == CMD_OFF:
        return {
            "valid": True,
            "hex": cleaned,
            "family": "mrstar_power",
            "meaning": "Power off",
            "confidence": "documented",
        }

    if cleaned == CMD_STATIC:
        return {
            "valid": True,
            "hex": cleaned,
            "family": "mrstar_static",
            "meaning": "Captured static-mode command",
            "confidence": "captured",
        }

    if cleaned.startswith("BC0406"):
        result = {
            "valid": True,
            "hex": cleaned,
            "family": "mrstar_color",
            "meaning": "MR Star color command",
            "confidence": "unconfirmed",
        }

        if len(cleaned) == 20 and cleaned.endswith("55"):
            try:
                hue = int(cleaned[6:10], 16)
                saturation = int(cleaned[10:14], 16)
                reserved = cleaned[14:18]

                result.update(
                    {
                        "hue": hue,
                        "saturation": saturation,
                        "reserved": reserved,
                        "confidence": (
                            "documented"
                            if hue <= 359
                            and saturation <= 1000
                            and reserved == "0000"
                            else "invalid_fields"
                        ),
                    }
                )
            except ValueError:
                result["confidence"] = "invalid_fields"

        return result

    if cleaned.startswith("BC0506"):
        result = {
            "valid": True,
            "hex": cleaned,
            "family": "mrstar_brightness",
            "meaning": "MR Star brightness command",
            "confidence": "unconfirmed",
        }

        if len(cleaned) == 20 and cleaned.endswith("55"):
            try:
                value = int(cleaned[6:10], 16)
                reserved = cleaned[10:18]

                result.update(
                    {
                        "brightness_value": value,
                        "brightness_fraction": round(value / 1024.0, 4),
                        "reserved": reserved,
                        "confidence": (
                            "documented"
                            if value <= 1024 and reserved == "00000000"
                            else "invalid_fields"
                        ),
                    }
                )
            except ValueError:
                result["confidence"] = "invalid_fields"

        return result

    if cleaned.startswith("BC06"):
        return {
            "valid": True,
            "hex": cleaned,
            "family": "mrstar_effect",
            "meaning": "MR Star effect/pattern command",
            "confidence": "documented_or_captured",
        }

    if cleaned.startswith("BC0F") or cleaned.startswith("BC11"):
        return {
            "valid": True,
            "hex": cleaned,
            "family": "mrstar_captured_mode",
            "meaning": "Captured mode or Scroll command",
            "confidence": "captured",
        }

    if cleaned.startswith("CC"):
        return {
            "valid": True,
            "hex": cleaned,
            "family": "classic_magic_home",
            "meaning": "Classic Magic Home command",
            "confidence": "captured",
        }

    if cleaned.startswith("56"):
        return {
            "valid": True,
            "hex": cleaned,
            "family": "classic_magic_home_color",
            "meaning": "Classic Magic Home RGB command",
            "confidence": "captured",
        }

    if cleaned.startswith("7E"):
        return {
            "valid": True,
            "hex": cleaned,
            "family": "experimental_7e",
            "meaning": "Experimental 7E command",
            "confidence": "unconfirmed",
        }

    return {
        "valid": True,
        "hex": cleaned,
        "family": "unknown",
        "meaning": "Unknown command",
        "confidence": "unknown",
    }


def mrstar_color_for_ui(r, g, b, brightness=1.0):
    return encode_mrstar_color(r, g, b, brightness=brightness)


def mrstar_brightness_for_ui(brightness=1.0):
    return encode_mrstar_brightness(brightness)
