"""Persistent user settings, stored as a single JSON document."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, ClassVar

from . import paths


@dataclass
class Settings:
    # Window
    window_geometry: str = ""
    dark_theme: bool = True

    # BLE
    known_devices: list[dict[str, str]] = field(default_factory=list)
    auto_connect_on_start: bool = False
    auto_reconnect: bool = True
    inter_device_delay_ms: int = 60
    write_retries: int = 2
    scan_seconds: float = 6.0

    # Remote
    last_profile: str = "MR Star Default"
    last_color: list[int] = field(default_factory=lambda: [255, 0, 0])
    last_brightness: int = 100

    # Sweep engine
    sweep_step_ms: int = 400
    sweep_steps: int = 12
    sweep_settle_ms: int = 150

    # Camera verification
    camera_index: int = 0
    camera_region: list[float] = field(default_factory=lambda: [0.3, 0.35, 0.7, 0.65])
    camera_samples_per_command: int = 3

    # Audio reactive
    audio_source: str = "microphone"
    audio_device_index: int = -1
    audio_gain: float = 1.0
    audio_min_brightness: int = 15
    media_volume: int = 70

    # Logging
    log_retention_days: int = 3

    #: Where this instance was loaded from; ``save()`` writes back here.
    _path: ClassVar[Path | None] = None

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
        settings._path = path
        return settings

    def save(self, path: Path | None = None) -> None:
        path = path or self._path or paths.config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        tmp.replace(path)
