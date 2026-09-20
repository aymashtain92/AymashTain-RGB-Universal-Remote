"""Asynchronous BLE transport for one or many LED controllers.

Design notes
------------
* Every device owns a serialised send queue, so a colour frame and its
  brightness frame can never interleave with another command.
* Writes are retried and a failure marks the device disconnected instead of
  raising into the UI thread.
* Reconnection is opt-in and backs off, which is what makes multi-strip setups
  survive the controllers' habit of dropping links when idle.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Iterable, Sequence
from dataclasses import dataclass, field

from ..protocol import (
    MRSTAR_SERVICE_UUID,
    MRSTAR_WRITE_CHAR_UUID,
    encode_brightness,
    encode_color,
    hex_to_bytes,
)

StatusCallback = Callable[[str, str], None]
LogCallback = Callable[[str, str], None]


@dataclass
class ScanResult:
    address: str
    name: str
    rssi: int | None = None
    is_candidate: bool = False


@dataclass
class DeviceState:
    address: str
    name: str = ""
    status: str = "disconnected"  # disconnected | connecting | connected
    char_uuid: str = MRSTAR_WRITE_CHAR_UUID
    last_color: tuple[int, int, int] = (255, 255, 255)
    last_brightness: float = 1.0
    last_ok: bool | None = None
    last_write_ts: float = 0.0
    failures: int = 0
    client: object | None = field(default=None, repr=False)

    @property
    def connected(self) -> bool:
        client = self.client
        return bool(client is not None and getattr(client, "is_connected", False))


CANDIDATE_NAME_HINTS = ("mr star", "mrstar", "triones", "elk-ble", "ledble", "ble-led", "qhm-")


def looks_like_led_controller(name: str, address: str) -> bool:
    lowered = (name or "").lower()
    if any(hint in lowered for hint in CANDIDATE_NAME_HINTS):
        return True
    # The user's MR Star clones all advertise 41:42:xx MAC prefixes.
    return address.upper().startswith("41:42:")


class BleManager:
    """Owns all BLE state. Safe to call from the Qt thread via qasync."""

    def __init__(
        self,
        log: LogCallback | None = None,
        on_status_change: Callable[[], None] | None = None,
        inter_device_delay_ms: int = 60,
        write_retries: int = 2,
        auto_reconnect: bool = True,
    ) -> None:
        self.devices: dict[str, DeviceState] = {}
        self._queues: dict[str, asyncio.Queue] = {}
        self._workers: dict[str, asyncio.Task] = {}
        self.log = log or (lambda kind, message: None)
        self.on_status_change = on_status_change or (lambda: None)
        self.inter_device_delay_ms = inter_device_delay_ms
        self.write_retries = write_retries
        self.auto_reconnect = auto_reconnect
        self.sent_frames = 0
        self.failed_frames = 0

    # --- discovery --------------------------------------------------------

    async def scan(self, seconds: float = 6.0) -> list[ScanResult]:
        from bleak import BleakScanner

        self.log("ble", f"Scanning for {seconds:.0f}s…")
        found: list[ScanResult] = []
        try:
            discovered = await BleakScanner.discover(timeout=seconds, return_adv=True)
        except Exception as exc:  # pragma: no cover - depends on host adapter
            self.log("error", f"Scan failed: {exc}")
            return []

        for device, adv in discovered.values():
            name = device.name or adv.local_name or "(unnamed)"
            found.append(
                ScanResult(
                    address=device.address,
                    name=name,
                    rssi=getattr(adv, "rssi", None),
                    is_candidate=looks_like_led_controller(name, device.address)
                    or MRSTAR_SERVICE_UUID in {str(u).lower() for u in adv.service_uuids or []},
                )
            )
        found.sort(key=lambda r: (not r.is_candidate, -(r.rssi or -999)))
        self.log("ble", f"Scan finished: {len(found)} device(s)")
        return found

    # --- connection -------------------------------------------------------

    def track(self, address: str, name: str = "") -> DeviceState:
        state = self.devices.get(address)
        if state is None:
            state = DeviceState(address=address, name=name or address)
            self.devices[address] = state
        elif name:
            state.name = name
        return state

    async def connect(self, address: str, name: str = "", timeout: float = 12.0) -> bool:
        from bleak import BleakClient

        state = self.track(address, name)
        if state.connected:
            return True

        state.status = "connecting"
        self.on_status_change()
        self.log("ble", f"Connecting to {state.name} ({address})…")

        try:
            client = BleakClient(
                address,
                timeout=timeout,
                disconnected_callback=lambda _c, addr=address: self._on_disconnected(addr),
            )
            await client.connect()
            if not client.is_connected:
                raise RuntimeError("adapter reported not connected")

            state.client = client
            state.char_uuid = self._pick_write_characteristic(client)
            state.status = "connected"
            state.failures = 0
            self._ensure_worker(address)
            self.log("ble", f"Connected {state.name} → write char {state.char_uuid}")
            self.on_status_change()
            return True
        except Exception as exc:
            state.client = None
            state.status = "disconnected"
            state.failures += 1
            self.log("error", f"Connect failed {address}: {exc}")
            self.on_status_change()
            return False

    @staticmethod
    def _pick_write_characteristic(client) -> str:
        preferred = None
        fallback = None
        for service in client.services:
            for char in service.characteristics:
                props = {p.lower() for p in char.properties}
                if not props & {"write", "write-without-response"}:
                    continue
                uuid = str(char.uuid).lower()
                if "fff3" in uuid:
                    return char.uuid
                if MRSTAR_SERVICE_UUID[4:8] in uuid or "2022" in uuid:
                    preferred = preferred or char.uuid
                fallback = fallback or char.uuid
        return preferred or fallback or MRSTAR_WRITE_CHAR_UUID

    def _on_disconnected(self, address: str) -> None:
        state = self.devices.get(address)
        if state is None:
            return
        state.status = "disconnected"
        state.client = None
        self.log("ble", f"{state.name} disconnected")
        self.on_status_change()
        if self.auto_reconnect:
            asyncio.get_event_loop().create_task(self._reconnect_later(address))

    async def _reconnect_later(self, address: str) -> None:
        state = self.devices.get(address)
        if state is None:
            return
        for attempt in range(1, 6):
            if state.connected or not self.auto_reconnect:
                return
            delay = min(2 ** attempt, 20)
            await asyncio.sleep(delay)
            self.log("ble", f"Reconnect attempt {attempt} for {state.name}")
            if await self.connect(address, state.name):
                return

    async def disconnect(self, address: str) -> None:
        state = self.devices.get(address)
        if state is None:
            return
        worker = self._workers.pop(address, None)
        if worker is not None:
            worker.cancel()
        self._queues.pop(address, None)
        client = state.client
        state.client = None
        state.status = "disconnected"
        if client is not None:
            try:
                await client.disconnect()
            except Exception as exc:
                self.log("error", f"Disconnect {address}: {exc}")
        self.on_status_change()

    async def disconnect_all(self) -> None:
        await asyncio.gather(*(self.disconnect(a) for a in list(self.devices)))

    def connected_addresses(self) -> list[str]:
        return [addr for addr, state in self.devices.items() if state.connected]

    # --- sending ----------------------------------------------------------

    def _ensure_worker(self, address: str) -> None:
        if address in self._workers and not self._workers[address].done():
            return
        self._queues.setdefault(address, asyncio.Queue())
        self._workers[address] = asyncio.get_event_loop().create_task(self._worker(address))

    async def _worker(self, address: str) -> None:
        queue = self._queues[address]
        while True:
            payload, label, future = await queue.get()
            ok = await self._write_now(address, payload, label)
            if not future.done():
                future.set_result(ok)
            queue.task_done()

    async def _write_now(self, address: str, payload: bytes, label: str) -> bool:
        state = self.devices.get(address)
        if state is None or not state.connected:
            return False

        for attempt in range(self.write_retries + 1):
            try:
                await state.client.write_gatt_char(state.char_uuid, payload, response=False)
                state.last_ok = True
                state.last_write_ts = time.time()
                self.sent_frames += 1
                self.log("send", f"{state.name} ← {payload.hex().upper()} ({label})")
                return True
            except Exception as exc:
                if attempt >= self.write_retries:
                    state.last_ok = False
                    self.failed_frames += 1
                    self.log("error", f"Write failed {state.name}: {exc}")
                    return False
                await asyncio.sleep(0.05 * (attempt + 1))
        return False

    async def send_hex(self, address: str, hex_cmd: str, label: str = "") -> bool:
        payload = hex_to_bytes(hex_cmd)
        self._ensure_worker(address)
        future: asyncio.Future[bool] = asyncio.get_event_loop().create_future()
        await self._queues[address].put((payload, label or hex_cmd, future))
        return await future

    async def send_hex_all(
        self, hex_cmd: str, label: str = "", addresses: Iterable[str] | None = None
    ) -> int:
        targets = list(addresses) if addresses is not None else self.connected_addresses()
        successes = 0
        for index, address in enumerate(targets):
            if index and self.inter_device_delay_ms:
                await asyncio.sleep(self.inter_device_delay_ms / 1000.0)
            successes += int(await self.send_hex(address, hex_cmd, label))
        return successes

    async def set_color(
        self,
        r: int,
        g: int,
        b: int,
        brightness: float = 1.0,
        addresses: Iterable[str] | None = None,
    ) -> int:
        """Colour then brightness, always as two frames — never merged."""
        targets = list(addresses) if addresses is not None else self.connected_addresses()
        successes = 0
        for index, address in enumerate(targets):
            if index and self.inter_device_delay_ms:
                await asyncio.sleep(self.inter_device_delay_ms / 1000.0)
            ok_color = await self.send_hex(address, encode_color(r, g, b), "color")
            ok_bright = await self.send_hex(address, encode_brightness(brightness), "brightness")
            state = self.devices.get(address)
            if state is not None:
                state.last_color = (r, g, b)
                state.last_brightness = brightness
            successes += int(ok_color and ok_bright)
        self.on_status_change()
        return successes

    async def run_macro(
        self,
        frames: Sequence[str],
        delay_ms: int = 120,
        addresses: Iterable[str] | None = None,
        should_continue: Callable[[], bool] | None = None,
        on_frame: Callable[[int, str, int], None] | None = None,
    ) -> int:
        """Replay a captured frame sequence exactly as recorded."""
        sent = 0
        for index, frame in enumerate(frames):
            if should_continue is not None and not should_continue():
                break
            ok = await self.send_hex_all(frame, f"macro[{index}]", addresses)
            sent += ok
            if on_frame is not None:
                on_frame(index, frame, ok)
            if delay_ms:
                await asyncio.sleep(delay_ms / 1000.0)
        return sent

    async def identify(self, address: str) -> None:
        """Blink a strip so the user can tell which physical strip it is."""
        for rgb in ((0, 255, 255), (255, 0, 0), (0, 255, 255)):
            await self.set_color(*rgb, brightness=1.0, addresses=[address])
            await asyncio.sleep(0.25)


async def gather_with_limit(limit: int, tasks: Sequence[Awaitable]) -> list:
    semaphore = asyncio.Semaphore(limit)

    async def runner(task: Awaitable):
        async with semaphore:
            return await task

    return await asyncio.gather(*(runner(t) for t in tasks), return_exceptions=True)
