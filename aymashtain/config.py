"""Persistent user settings, stored as a single JSON document.

Round 2 additions: theme_mode (light/dark/system), developer_tools lock,
save_location, brightness_min/max clamp, camera resolution/FPS/exposure/WB
locks, dedicated audio device picks, per-pattern mic assignment, and window
screen/position/scale memory.

Legacy ``dark_theme`` is kept in sync so nothing that still reads it breaks.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, ClassVar

from . import paths

THEME_LIGHT = "light"
THEME_DARK = "dark"
THEME_SYSTEM = "system"

#: Which physical mic a music pattern is driven from.
MIC_USB_INTERNAL = "usb_internal"      # strip's own USB mic, 4 built-in modes
MIC_THIRD_PARTY = "third_party"        # PC mic / line-in / file → software-driven


def _system_prefers_dark() -> bool:
    """Best-effort check of the OS colour scheme. Falls back to light when unsure."""
    if sys.platform == "win32":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
        except Exception:
            return False
    if sys.platform == "darwin":
        try:
            import subprocess

            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return "Dark" in (result.stdout or "")
        except Exception:
            return False
    return False


@dataclass
class Settings:
    # --- Window / screen memory ------------------------------------------
    window_geometry: str = ""              # legacy base64 blob, still written
    remember_window: bool = True
    window_screen: str = ""                # monitor name at last close
    window_x: int = -1
    window_y: int = -1
    window_width: int = 1180
    window_height: int = 840
    window_scale: float = 1.0              # DPI scale at last close

    # --- Appearance ------------------------------------------------------
    theme_mode: str = THEME_DARK           # light | dark | system
    dark_theme: bool = True                # legacy mirror; kept in sync on save

    # --- Developer lock --------------------------------------------------
    developer_tools: bool = False          # OFF for end users

    # --- Language (stub for future translation) --------------------------
    language: str = "en"

    # --- Save location for exports --------------------------------------
    save_location: str = ""

    # --- Brightness clamp (internal, never send above max) ---------------
    brightness_min: int = 0                # 0..100
    brightness_max: int = 100              # 0..100

    # --- BLE -------------------------------------------------------------
    known_devices: list[dict[str, str]] = field(default_factory=list)
    auto_connect_on_start: bool = False
    auto_reconnect: bool = True
    inter_device_delay_ms: int = 60
    write_retries: int = 2
    scan_seconds: float = 6.0

    # --- Remote ----------------------------------------------------------
    last_profile: str = "MR Star Default"
    last_color: list[int] = field(default_factory=lambda: [255, 0, 0])
    last_brightness: int = 100

    # --- Sweep engine ----------------------------------------------------
    sweep_step_ms: int = 400
    sweep_steps: int = 12
    sweep_settle_ms: int = 150

    # --- Camera verification --------------------------------------------
    camera_index: int = 0
    camera_region: list[float] = field(default_factory=lambda: [0.3, 0.35, 0.7, 0.65])
    camera_samples_per_command: int = 3
    camera_resolution: str = "1280x720"    # "WxH" as a string
    camera_fps: int = 30
    camera_exposure_lock: bool = False
    camera_exposure_value: int = -1        # -1 = auto
    camera_wb_lock: bool = False

    # --- Audio -----------------------------------------------------------
    audio_source: str = "microphone"       # microphone | loopback | file
    audio_device_index: int = -1           # legacy single-device index
    audio_mic_device: int = -1             # device chosen in Options
    audio_second_mic_device: int = -1      # second mic / line-in
    audio_speaker_device: int = -1         # speaker / output
    audio_gain: float = 1.0
    audio_min_brightness: int = 15
    media_volume: int = 70

    # --- Music patterns: per-pattern mic assignment ----------------------
    # {pattern_key: MIC_USB_INTERNAL | MIC_THIRD_PARTY}
    pattern_sources: dict[str, str] = field(default_factory=dict)

    # --- Logging ---------------------------------------------------------
    log_retention_days: int = 3

    #: Where this instance was loaded from; ``save()`` writes back here.
    _path: ClassVar[Path | None] = None

    # --- Theme resolution ------------------------------------------------

    def resolved_dark(self) -> bool:
        """Return True when the effective theme should render dark."""
        mode = (self.theme_mode or "").strip().lower()
        if mode == THEME_DARK:
            return True
        if mode == THEME_LIGHT:
            return False
        if mode == THEME_SYSTEM:
            return _system_prefers_dark()
        return bool(self.dark_theme)

    # --- Brightness clamp helper -----------------------------------------

    def clamp_brightness(self, value_0_1: float) -> float:
        """Clamp a 0.0–1.0 brightness against the min/max limits."""
        lo = max(0, min(100, int(self.brightness_min))) / 100.0
        hi = max(0, min(100, int(self.brightness_max))) / 100.0
        if hi < lo:
            lo, hi = hi, lo
        return max(lo, min(hi, value_0_1))

    # --- Persistence -----------------------------------------------------

    @classmethod
    def load(cls, path: Path | None = None) -> Settings:
        path = path or paths.config_path()
        raw: dict[str, Any] = {}
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                raw = {}

        known = {f.name for f in fields(cls)}
        settings = cls(**{key: value for key, value in raw.items() if key in known})

        # Migration: old files only had dark_theme.
        if "theme_mode" not in raw and "dark_theme" in raw:
            settings.theme_mode = THEME_DARK if raw["dark_theme"] else THEME_LIGHT

        # Guard against corrupted values slipping through.
        if settings.theme_mode not in (THEME_LIGHT, THEME_DARK, THEME_SYSTEM):
            settings.theme_mode = THEME_DARK
        settings.brightness_min = max(0, min(100, int(settings.brightness_min)))
        settings.brightness_max = max(0, min(100, int(settings.brightness_max)))

        settings._path = path
        return settings

    def save(self, path: Path | None = None) -> None:
        path = path or self._path or paths.config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        # Keep the legacy flag coherent before we serialise.
        self.dark_theme = self.resolved_dark()
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        tmp.replace(path)
