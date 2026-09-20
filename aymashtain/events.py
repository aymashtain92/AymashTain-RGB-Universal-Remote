"""Thread-safe event bus plus session logging to .log / .json / .csv."""

from __future__ import annotations

import csv
import json
import queue
import threading
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from . import APP_NAME, APP_VERSION, paths

EventKind = Literal["info", "ble", "send", "error", "camera", "audio", "sweep"]


@dataclass(frozen=True)
class Event:
    timestamp: str
    kind: str
    source: str
    message: str


class EventBus:
    """Collects events from any thread; the UI drains them on a timer.

    Events are also appended to the current session log files so a crash
    still leaves a complete trace on disk.
    """

    def __init__(self, session_logger: SessionLogger | None = None, maxsize: int = 8192) -> None:
        self._queue: queue.Queue[Event] = queue.Queue(maxsize=maxsize)
        self._history: list[Event] = []
        self._lock = threading.Lock()
        self.session_logger = session_logger
        self.dropped = 0

    def emit(self, kind: str, message: str, source: str = "app") -> Event:
        event = Event(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            kind=kind,
            source=source,
            message=message,
        )
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            self.dropped += 1
        with self._lock:
            self._history.append(event)
            if len(self._history) > 20000:
                del self._history[:5000]
        if self.session_logger is not None:
            self.session_logger.write(event)
        return event

    def drain(self, limit: int = 500) -> list[Event]:
        out: list[Event] = []
        while len(out) < limit:
            try:
                out.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return out

    def history(self) -> list[Event]:
        with self._lock:
            return list(self._history)


class SessionLogger:
    """Writes one .log, .json and .csv file per run and prunes old sessions."""

    def __init__(self, directory: Path | None = None, retention_days: int = 3) -> None:
        self.directory = directory or paths.logs_dir()
        self.directory.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        self.log_file = self.directory / f"session_{stamp}.log"
        self.json_file = self.directory / f"session_{stamp}.json"
        self.csv_file = self.directory / f"session_{stamp}.csv"
        self._events: list[Event] = []
        self._lock = threading.Lock()

        with self.log_file.open("w", encoding="utf-8") as handle:
            handle.write(f"# {APP_NAME} {APP_VERSION} — session {stamp}\n")
        with self.csv_file.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerow(["timestamp", "kind", "source", "message"])

        self.prune(retention_days)

    def write(self, event: Event) -> None:
        with self._lock:
            self._events.append(event)
            try:
                with self.log_file.open("a", encoding="utf-8") as handle:
                    handle.write(
                        f"{event.timestamp} [{event.kind.upper():<6}] "
                        f"{event.source}: {event.message}\n"
                    )
                with self.csv_file.open("a", encoding="utf-8", newline="") as handle:
                    csv.writer(handle).writerow(
                        [event.timestamp, event.kind, event.source, event.message]
                    )
            except OSError:
                pass

    def flush_json(self) -> None:
        with self._lock:
            payload = {
                "app": APP_NAME,
                "version": APP_VERSION,
                "events": [asdict(event) for event in self._events],
            }
        try:
            self.json_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            pass

    def prune(self, retention_days: int) -> list[Path]:
        if retention_days <= 0:
            return []
        cutoff = (datetime.now() - timedelta(days=retention_days)).timestamp()
        removed: list[Path] = []
        for path in self._session_files():
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed.append(path)
            except OSError:
                continue
        return removed

    def _session_files(self) -> Iterable[Path]:
        for suffix in ("*.log", "*.json", "*.csv"):
            yield from self.directory.glob(f"session_{suffix}")
