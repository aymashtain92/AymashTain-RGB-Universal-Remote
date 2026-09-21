# Original Path: aymashtain/ui/context.py

"""Shared application context handed to every tab.

Round 3 additions
-----------------
* **Multi-strip selection.** ``selected_strips`` holds the addresses the
  user wants to control right now. Empty list means "all connected".
  Every tab that used to pass ``addresses=None`` (meaning all) should now
  pass ``ctx.resolve_targets()`` so the user's selection is honoured.
* ``resolve_targets()`` returns either a concrete list of addresses or
  ``None`` (which BleManager interprets as "all connected"). It prunes
  addresses that are no longer connected so a stale selection never
  silently drops frames.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from dataclasses import dataclass, field
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

    #: Addresses the user has ticked in the strip selector. Empty list
    #: means "all connected strips".
    selected_strips: list[str] = field(default_factory=list)

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

    # ------------------------------------------------------------------
    # Strip selection
    # ------------------------------------------------------------------

    def resolve_targets(self) -> list[str] | None:
        """Return the addresses commands should go to.

        * ``None`` -> "every connected strip" (BleManager's own default).
        * A concrete list -> only those addresses, pruned to what is
          actually connected right now. If the pruned list would be empty
          -- for example the user had one strip selected and it just
          dropped -- fall back to ``None`` so the app keeps working and
          the user is not left sending to nowhere.
        """
        if not self.selected_strips:
            return None
        connected = set(self.ble.connected_addresses())
        live = [addr for addr in self.selected_strips if addr in connected]
        if not live:
            return None
        return live

    def selected_strip_count(self) -> int:
        """How many strips are currently targeted (for status display)."""
        targets = self.resolve_targets()
        if targets is None:
            return len(self.ble.connected_addresses())
        return len(targets)

    def is_strip_selected(self, address: str) -> bool:
        """True when the strip should receive commands.

        Empty ``selected_strips`` means "everything", so any connected
        strip returns True.
        """
        if not self.selected_strips:
            return True
        return address in self.selected_strips
