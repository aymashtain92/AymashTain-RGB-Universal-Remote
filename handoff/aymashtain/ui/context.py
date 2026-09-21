"""Shared application context handed to every tab."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from dataclasses import dataclass
from typing import Any

from ..ble import BleManager
from ..config import Settings
from ..events import EventBus
from ..storage import Database


@dataclass
class AppContext:
    settings: Settings
    bus: EventBus
    db: Database
    ble: BleManager

    def log(self, kind: str, message: str, source: str = "ui") -> None:
        self.bus.emit(kind, message, source)

    def run(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Task:
        """Schedule an async action from a Qt signal handler."""
        task = asyncio.ensure_future(coro)
        task.add_done_callback(self._report_failure)
        return task

    def _report_failure(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        error = task.exception()
        if error is not None:
            self.bus.emit("error", f"{type(error).__name__}: {error}", "async")
