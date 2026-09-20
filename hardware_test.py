# hardware_test.py
from __future__ import annotations

import asyncio
import csv
import datetime as dt
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from bleak import BleakClient

from mrstar_protocol import (
    CMD_ON,
    CMD_OFF,
    MRSTAR_WRITE_CHAR_UUID,
    encode_mrstar_brightness,
    encode_mrstar_color,
)

STRIPS = [
    "41:42:59:F1:C8:68",
    "41:42:43:E7:8B:F6",
    "41:42:F9:D7:45:B0",
]

CHARACTERISTIC_UUID = MRSTAR_WRITE_CHAR_UUID
CAMERA_ENABLED = False
CAMERA_INDEX = 0
CAMERA_REGION = (0, 0, 640, 480)

HOLD_SECONDS = 2.0
INTER_DEVICE_DELAY_SECONDS = 0.25
COMMAND_GAP_SECONDS = 0.12
RETRY_DELAY_SECONDS = 0.30

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"

RED = encode_mrstar_color(255, 0, 0)
GREEN = encode_mrstar_color(0, 255, 0)
BLUE = encode_mrstar_color(0, 0, 255)

TEST_STEPS = [
    ("red_100", "Red 100%", "red", [("power_on", CMD_ON), ("red_color", RED), ("brightness_100", encode_mrstar_brightness(1.00))]),
    ("green_100", "Green 100%", "green", [("power_on", CMD_ON), ("green_color", GREEN), ("brightness_100", encode_mrstar_brightness(1.00))]),
    ("blue_100", "Blue 100%", "blue", [("power_on", CMD_ON), ("blue_color", BLUE), ("brightness_100", encode_mrstar_brightness(1.00))]),
    ("red_75", "Red 75%", "red", [("red_color", RED), ("brightness_75", encode_mrstar_brightness(0.75))]),
    ("red_50", "Red 50%", "red", [("red_color", RED), ("brightness_50", encode_mrstar_brightness(0.50))]),
    ("red_25", "Red 25%", "red", [("red_color", RED), ("brightness_25", encode_mrstar_brightness(0.25))]),
    ("red_0", "Red 0%", "red", [("brightness_0", encode_mrstar_brightness(0.00))]),
    ("red_restore", "Red 100% restored", "red", [("power_on", CMD_ON), ("red_color", RED), ("brightness_100", encode_mrstar_brightness(1.00))]),
]

@dataclass
class DeviceResult:
    timestamp: str
    step_id: str
    step_label: str
    command_label: str
    hex_command: str
    address: str
    characteristic: str
    accepted: bool
    duration_ms: float
    retry_used: bool
    connected_before: bool
    connected_after: bool
    error: str = ""

@dataclass
class CameraResult:
    timestamp: str
    step_id: str
    step_label: str
    expected_color: str
    red: float
    green: float
    blue: float
    brightness: float
    white_contamination: float
    error: str = ""

class SessionLogger:
    def __init__(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.stamp = stamp
        self.text_path = LOG_DIR / f"hardware_test_{stamp}.log"
        self.json_path = LOG_DIR / f"hardware_test_{stamp}.json"
        self.csv_path = LOG_DIR / f"hardware_test_{stamp}.csv"
        self.events: list[dict] = []
        self.device_results: list[DeviceResult] = []
        self.camera_results: list[CameraResult] = []

    def event(self, message: str, kind: str = "info"):
        row = {"timestamp": dt.datetime.now().isoformat(timespec="milliseconds"), "kind": kind, "message": message}
        self.events.append(row)
        print(f"[{kind.upper()}] {message}")
        with self.text_path.open("a", encoding="utf-8") as file:
            file.write(f"{row['timestamp']} [{kind.upper()}] {message}\n")

    def save(self):
        payload = {
            "application": "AymashTain LED RGB Remote",
            "version": "v0.41",
            "created_at": self.stamp,
            "settings": {
                "strips": STRIPS,
                "characteristic": CHARACTERISTIC_UUID,
                "hold_seconds": HOLD_SECONDS,
                "inter_device_delay_seconds": INTER_DEVICE_DELAY_SECONDS,
                "camera_enabled": CAMERA_ENABLED,
                "camera_index": CAMERA_INDEX,
                "camera_region": CAMERA_REGION,
            },
            "events": self.events,
            "device_results": [asdict(x) for x in self.device_results],
            "camera_results": [asdict(x) for x in self.camera_results],
        }
        self.json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        with self.csv_path.open("w", newline="", encoding="utf-8") as file:
            fields = [
                "timestamp", "step_id", "step_label", "command_label", "hex_command",
                "address", "characteristic", "accepted", "duration_ms", "retry_used",
                "connected_before", "connected_after", "error"
            ]
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            for r in self.device_results:
                writer.writerow(asdict(r))
        self.event(f"Saved log: {self.text_path}")

class StripConnection:
    def __init__(self, address: str, logger: SessionLogger):
        self.address = address
        self.logger = logger
        self.client: Optional[BleakClient] = None
        self.characteristic = CHARACTERISTIC_UUID

    async def connect(self):
        self.logger.event(f"{self.address}: connecting")
        self.client = BleakClient(self.address, timeout=15.0)
        await self.client.connect()
        if not self.client.is_connected:
            raise RuntimeError("BLE client reports disconnected.")
        writable = []
        for service in self.client.services:
            for char in service.characteristics:
                props = {str(item).lower() for item in char.properties}
                if "write" in props or "write-without-response" in props:
                    writable.append(char.uuid.lower())
        if self.characteristic.lower() not in writable:
            fallback = next((v for v in writable if "fff3" in v), None)
            if fallback is None:
                raise RuntimeError(f"FFF3 unavailable. Writable characteristics: {writable}")
            self.characteristic = fallback
        self.logger.event(f"{self.address}: connected using {self.characteristic}", "ble")

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()

    async def send(self, hex_command: str, step_id: str, step_label: str, command_label: str) -> bool:
        if not self.client:
            raise RuntimeError("Not connected.")
        started = time.perf_counter()
        accepted = False
        error_message = ""
        for attempt in range(2):
            try:
                await self.client.write_gatt_char(self.characteristic, bytes.fromhex(hex_command), response=False)
                accepted = True
                break
            except Exception as exc:
                error_message = str(exc)
                if attempt == 0:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
        duration_ms = (time.perf_counter() - started) * 1000.0
        self.logger.device_results.append(DeviceResult(
            timestamp=dt.datetime.now().isoformat(timespec="milliseconds"),
            step_id=step_id, step_label=step_label, command_label=command_label,
            hex_command=hex_command, address=self.address, characteristic=self.characteristic,
            accepted=accepted, duration_ms=round(duration_ms, 3), retry_used=False,
            connected_before=True, connected_after=bool(self.client.is_connected),
            error="" if accepted else error_message
        ))
        self.logger.event(f"{self.address}: {command_label} {'accepted' if accepted else 'FAILED'} ({duration_ms:.1f} ms)", "ble" if accepted else "error")
        return accepted

async def run_test():
    logger = SessionLogger()
    connections = []
    try:
        logger.event("Starting AymashTain LED RGB Remote hardware test.")
        for addr in STRIPS:
            conn = StripConnection(addr, logger)
            try:
                await conn.connect()
                connections.append(conn)
            except Exception as e:
                logger.event(f"{addr}: connection failed: {e}", "error")
        if not connections:
            logger.event("No strips connected. Test aborted.", "error")
            return
        for step_id, step_label, _, commands in TEST_STEPS:
            logger.event(f"Beginning {step_label}")
            for command_label, cmd in commands:
                for c in connections:
                    await c.send(cmd, step_id, step_label, command_label)
                    await asyncio.sleep(INTER_DEVICE_DELAY_SECONDS)
                await asyncio.sleep(COMMAND_GAP_SECONDS)
            logger.event(f"Completed {step_label}")
    finally:
        for c in connections:
            await c.disconnect()
        logger.save()

if __name__ == "__main__":
    asyncio.run(run_test())
