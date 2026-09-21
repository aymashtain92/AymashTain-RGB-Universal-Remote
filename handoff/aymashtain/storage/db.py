"""SQLite storage for remote profiles, buttons, captured commands and devices."""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .. import paths
from ..protocol import CMD_OFF, CMD_ON, CMD_STATIC, SCROLL_MACRO, encode_brightness, encode_color

SCHEMA_VERSION = 2


@dataclass
class RemoteProfile:
    id: int
    name: str
    protocol: str
    created_at: str


@dataclass
class RemoteButton:
    id: int
    profile_id: int
    label: str
    hex: str
    group_name: str
    sort_order: int
    char_uuid: str = ""
    macro_frames: list[str] | None = None
    macro_delay_ms: int = 120

    @property
    def is_macro(self) -> bool:
        return bool(self.macro_frames)


class Database:
    """Small hand-rolled data layer.

    A single connection guarded by a lock is plenty for a desktop app and
    avoids the "SQLite objects created in a thread" class of crash that the
    earlier builds hit when BLE callbacks wrote to the DB.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else paths.db_path()
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()
        self._seed()

    # --- schema -----------------------------------------------------------

    def _migrate(self) -> None:
        with self._lock, self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    protocol TEXT NOT NULL DEFAULT 'MRStar',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS remote_buttons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                    label TEXT NOT NULL,
                    hex TEXT NOT NULL,
                    char_uuid TEXT NOT NULL DEFAULT '',
                    group_name TEXT NOT NULL DEFAULT 'Ungrouped',
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    macro_frames TEXT NOT NULL DEFAULT '',
                    macro_delay_ms INTEGER NOT NULL DEFAULT 120
                );
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    device TEXT NOT NULL DEFAULT '',
                    char_uuid TEXT NOT NULL DEFAULT '',
                    hex TEXT NOT NULL,
                    label TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    ok INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS devices (
                    address TEXT PRIMARY KEY,
                    name TEXT NOT NULL DEFAULT '',
                    char_uuid TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS idx_buttons_profile
                    ON remote_buttons(profile_id, group_name, sort_order);
                CREATE INDEX IF NOT EXISTS idx_commands_ts ON commands(ts DESC);
                """
            )
            self.conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )

    def _seed(self) -> None:
        if self.get_profiles():
            return
        profile_id = self.create_profile("MR Star Default", "MRStar")
        defaults: list[tuple[str, str, str]] = [
            ("Power ON", CMD_ON, "Power"),
            ("Power OFF", CMD_OFF, "Power"),
            ("Static mode", CMD_STATIC, "Modes"),
            ("Red", encode_color(255, 0, 0), "Colours"),
            ("Green", encode_color(0, 255, 0), "Colours"),
            ("Blue", encode_color(0, 0, 255), "Colours"),
            ("Cyan", encode_color(0, 255, 255), "Colours"),
            ("Magenta", encode_color(255, 0, 255), "Colours"),
            ("Warm white", encode_color(255, 190, 120), "Colours"),
            ("Brightness 100%", encode_brightness(1.0), "Brightness"),
            ("Brightness 50%", encode_brightness(0.5), "Brightness"),
            ("Brightness 10%", encode_brightness(0.1), "Brightness"),
        ]
        for order, (label, hex_cmd, group) in enumerate(defaults):
            self.add_button(profile_id, label, hex_cmd, group_name=group, sort_order=order)
        self.add_button(
            profile_id,
            "Scroll chase (captured)",
            SCROLL_MACRO[0],
            group_name="Macros",
            sort_order=100,
            macro_frames=SCROLL_MACRO,
            macro_delay_ms=120,
        )

    # --- profiles ---------------------------------------------------------

    def get_profiles(self) -> list[RemoteProfile]:
        with self._lock:
            rows = self.conn.execute("SELECT * FROM profiles ORDER BY name").fetchall()
        return [RemoteProfile(r["id"], r["name"], r["protocol"], r["created_at"]) for r in rows]

    def get_profile(self, name: str) -> RemoteProfile | None:
        with self._lock:
            row = self.conn.execute("SELECT * FROM profiles WHERE name=?", (name,)).fetchone()
        if row is None:
            return None
        return RemoteProfile(row["id"], row["name"], row["protocol"], row["created_at"])

    def create_profile(self, name: str, protocol: str = "MRStar") -> int:
        with self._lock, self.conn:
            cursor = self.conn.execute(
                "INSERT INTO profiles(name, protocol, created_at) VALUES(?, ?, ?)",
                (name, protocol, datetime.now().isoformat(timespec="seconds")),
            )
        return int(cursor.lastrowid)

    def rename_profile(self, profile_id: int, new_name: str) -> None:
        with self._lock, self.conn:
            self.conn.execute("UPDATE profiles SET name=? WHERE id=?", (new_name, profile_id))

    def delete_profile(self, profile_id: int) -> None:
        with self._lock, self.conn:
            self.conn.execute("DELETE FROM profiles WHERE id=?", (profile_id,))

    # --- buttons ----------------------------------------------------------

    def add_button(
        self,
        profile_id: int,
        label: str,
        hex_cmd: str,
        group_name: str = "Ungrouped",
        sort_order: int = 0,
        char_uuid: str = "",
        macro_frames: list[str] | None = None,
        macro_delay_ms: int = 120,
    ) -> int:
        with self._lock, self.conn:
            cursor = self.conn.execute(
                """INSERT INTO remote_buttons
                   (profile_id, label, hex, char_uuid, group_name, sort_order,
                    macro_frames, macro_delay_ms)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile_id,
                    label,
                    hex_cmd,
                    char_uuid,
                    group_name,
                    sort_order,
                    "\n".join(macro_frames or []),
                    macro_delay_ms,
                ),
            )
        return int(cursor.lastrowid)

    def get_buttons(self, profile_id: int) -> list[RemoteButton]:
        with self._lock:
            rows = self.conn.execute(
                """SELECT * FROM remote_buttons WHERE profile_id=?
                   ORDER BY group_name, sort_order, id""",
                (profile_id,),
            ).fetchall()
        return [self._row_to_button(row) for row in rows]

    def get_button(self, button_id: int) -> RemoteButton | None:
        with self._lock:
            row = self.conn.execute(
                "SELECT * FROM remote_buttons WHERE id=?", (button_id,)
            ).fetchone()
        return self._row_to_button(row) if row else None

    def update_button(
        self,
        button_id: int,
        label: str | None = None,
        hex_cmd: str | None = None,
        group_name: str | None = None,
        macro_frames: list[str] | None = None,
        macro_delay_ms: int | None = None,
    ) -> None:
        """Partial update — any argument left as ``None`` keeps its value."""
        frames = "\n".join(macro_frames) if macro_frames is not None else None
        with self._lock, self.conn:
            self.conn.execute(
                """UPDATE remote_buttons
                   SET label=COALESCE(?, label),
                       hex=COALESCE(?, hex),
                       group_name=COALESCE(?, group_name),
                       macro_frames=COALESCE(?, macro_frames),
                       macro_delay_ms=COALESCE(?, macro_delay_ms)
                   WHERE id=?""",
                (label, hex_cmd, group_name, frames, macro_delay_ms, button_id),
            )

    def delete_button(self, button_id: int) -> None:
        with self._lock, self.conn:
            self.conn.execute("DELETE FROM remote_buttons WHERE id=?", (button_id,))

    def clone_button(self, button_id: int) -> int | None:
        button = self.get_button(button_id)
        if button is None:
            return None
        return self.add_button(
            button.profile_id,
            f"{button.label} (copy)",
            button.hex,
            button.group_name,
            button.sort_order + 1,
            button.char_uuid,
            button.macro_frames,
            button.macro_delay_ms,
        )

    @staticmethod
    def _row_to_button(row: sqlite3.Row) -> RemoteButton:
        frames = [line for line in (row["macro_frames"] or "").splitlines() if line.strip()]
        return RemoteButton(
            id=row["id"],
            profile_id=row["profile_id"],
            label=row["label"],
            hex=row["hex"],
            group_name=row["group_name"],
            sort_order=row["sort_order"],
            char_uuid=row["char_uuid"],
            macro_frames=frames or None,
            macro_delay_ms=row["macro_delay_ms"],
        )

    # --- command history --------------------------------------------------

    def add_command(
        self,
        hex_cmd: str,
        device: str = "",
        char_uuid: str = "",
        label: str = "",
        notes: str = "",
        ok: bool = True,
    ) -> int:
        with self._lock, self.conn:
            cursor = self.conn.execute(
                """INSERT INTO commands(ts, device, char_uuid, hex, label, notes, ok)
                   VALUES(?, ?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now().isoformat(timespec="seconds"),
                    device,
                    char_uuid,
                    hex_cmd,
                    label,
                    notes,
                    int(ok),
                ),
            )
        return int(cursor.lastrowid)

    def get_commands(self, limit: int = 500) -> list[sqlite3.Row]:
        with self._lock:
            return self.conn.execute(
                "SELECT * FROM commands ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    def clear_commands(self) -> None:
        with self._lock, self.conn:
            self.conn.execute("DELETE FROM commands")

    # --- devices ----------------------------------------------------------

    def upsert_device(self, address: str, name: str = "", char_uuid: str = "") -> None:
        with self._lock, self.conn:
            self.conn.execute(
                """INSERT INTO devices(address, name, char_uuid, last_seen)
                   VALUES(?, ?, ?, ?)
                   ON CONFLICT(address) DO UPDATE SET
                       name=excluded.name,
                       char_uuid=excluded.char_uuid,
                       last_seen=excluded.last_seen""",
                (address, name, char_uuid, datetime.now().isoformat(timespec="seconds")),
            )

    def get_devices(self) -> list[sqlite3.Row]:
        with self._lock:
            return self.conn.execute("SELECT * FROM devices ORDER BY name, address").fetchall()

    def forget_device(self, address: str) -> None:
        with self._lock, self.conn:
            self.conn.execute("DELETE FROM devices WHERE address=?", (address,))

    def close(self) -> None:
        with self._lock:
            self.conn.close()
