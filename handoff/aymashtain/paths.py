"""Filesystem locations for data, logs and configuration.

Everything the app writes lives under a single user-writable data directory so
the program keeps working when it is installed next to read-only files (for
example under ``C:\\Program Files`` or when frozen with PyInstaller).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from . import APP_SLUG

_ENV_OVERRIDE = "AYMASHTAIN_DATA_DIR"


def data_dir() -> Path:
    override = os.environ.get(_ENV_OVERRIDE)
    if override:
        base = Path(override)
    elif sys.platform == "win32":
        root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        base = Path(root) / APP_SLUG
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / APP_SLUG
    else:
        root = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        base = Path(root) / APP_SLUG.lower()

    base.mkdir(parents=True, exist_ok=True)
    return base


def logs_dir() -> Path:
    path = data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return data_dir() / "aymashtain.db"


def config_path() -> Path:
    return data_dir() / "config.json"


def bundle_dir() -> Path:
    """Directory holding read-only assets (icon, docs), frozen-aware."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def icon_file() -> Path | None:
    for name in ("aymashtain.ico", "aymashtain.png"):
        candidate = bundle_dir() / "assets" / name
        if candidate.is_file():
            return candidate
    return None
