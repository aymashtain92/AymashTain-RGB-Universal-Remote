#!/usr/bin/env python3
"""
AymashTain LED RGB Remote - PySide6 Graphical Desktop GUI
Universal MR Star & Triones Bluetooth LED Strip Controller.
"""

from __future__ import annotations
import sys
import os
import json
import time
import asyncio
from pathlib import Path
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QSlider, QSpinBox,
    QTextEdit, QGroupBox, QFileDialog, QListWidget, QProgressBar,
    QMessageBox, QColorDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QUrl
from PySide6.QtGui import QColor, QFont, QImage, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

import qasync
from bleak import BleakClient, BleakScanner
import numpy as np

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

# Import protocol encoders
try:
    from mrstar_protocol import (
        CMD_ON, CMD_OFF,
        encode_mrstar_color,
        encode_mrstar_brightness,
        MRSTAR_WRITE_CHAR_UUID,
    )
except ImportError:
    # Fallback if mrstar_protocol.py is not in the same folder
    CMD_ON = "BC01010155"
    CMD_OFF = "BC01010055"
    MRSTAR_WRITE_CHAR_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
    def encode_mrstar_color(r: int, g: int, b: int) -> str:
        import colorsys
        h, s, _ = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        return f"BC0406{int(h*360)%360:04X}{int(s*1000):04X}000055"
    def encode_mrstar_brightness(bri: float) -> str:
        val = int(max(0.0, min(1.0, bri)) * 1024)
        return f"BC0506{val:04X}0000000055"

DEFAULT_STRIPS = [
    {"name": "Strip 1 (Desk Left)",   "address": "41:42:59:F1:C8:68"},
    {"name": "Strip 2 (Desk Center)", "address": "41:42:43:E7:8B:F6"},
    {"name": "Strip 3 (Wall Ambient)","address": "41:42:F9:D7:45:B0"},
]

class BleManager(QObject):
    log_signal = Signal(str, str)
    status_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.clients: Dict[str, BleakClient] = {}
        self.chars: Dict[str, str] = {}

    async def connect_device(self, address: str) -> bool:
        self.log_signal.emit("ble", f"Connecting to {address}...")
        self.status_signal.emit(address, "connecting")
        try:
            client = BleakClient(address, timeout=12.0)
            await client.connect()
            if not client.is_connected:
                self.status_signal.emit(address, "disconnected")
                return False

            write_char = None
            for s in client.services:
                for ch in s.characteristics:
                    props = [p.lower() for p in ch.properties]
                    if "write" in props or "write-without-response" in props:
                        if "fff3" in ch.uuid.lower() or "2022" in ch.uuid.lower():
                            write_char = ch.uuid
                            break
                        if not write_char:
                            write_char = ch.uuid

            self.clients[address] = client
            self.chars[address] = write_char or MRSTAR_WRITE_CHAR_UUID
            self.status_signal.emit(address, "connected")
            self.log_signal.emit("ble", f"Connected {address} ({self.chars[address]})")
            return True
        except Exception as e:
            self.status_signal.emit(address, "disconnected")
            self.log_signal.emit("error", f"Connection failed {address}: {e}")
            return False

    async def disconnect_device(self, address: str):
        if address in self.clients:
            try:
                await self.clients[address].disconnect()
            except Exception:
                pass
            del self.clients[address]
        self.status_signal.emit(address, "disconnected")

    async def send_hex_all(self, hex_cmd: str) -> int:
        success = 0
        for addr, client in list(self.clients.items()):
            if client.is_connected:
                ch = self.chars.get(addr, MRSTAR_WRITE_CHAR_UUID)
                try:
                    await client.write_gatt_char(ch, bytes.fromhex(hex_cmd), response=False)
                    success += 1
                except Exception as e:
                    self.log_signal.emit("error", f"Write error {addr}: {e}")
                await asyncio.sleep(0.08)
        return success

    async def pulse(self):
        await self.send_hex_all(CMD_OFF)
        await asyncio.sleep(0.18)
        await self.send_hex_all(CMD_ON)
        await asyncio.sleep(0.12)
        await self.send_hex_all(encode_mrstar_color(0, 255, 255))
        await asyncio.sleep(0.18)
        await self.send_hex_all(encode_mrstar_color(255, 0, 0))
        await self.send_hex_all(encode_mrstar_brightness(1.0))

class MainWindow(QMainWindow):
    def __init__(self, ble: BleManager):
        super().__init__()
        self.ble = ble
        self.setWindowTitle("AymashTain LED RGB Remote - Desktop Control Center")
        self.resize(1000, 820)
        self.setStyleSheet("""
            QMainWindow { background-color: #121217; }
            QWidget { color: #E4E4E7; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
            QTabWidget::pane { border: 1px solid #27272A; background: #18181B; border-radius: 8px; }
            QTabBar::tab { background: #27272A; border: 1px solid #3F3F46; padding: 8px 18px; margin-right: 4px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #4F46E5; color: #FFFFFF; font-weight: bold; border-color: #6366F1; }
            QPushButton { background: #27272A; border: 1px solid #3F3F46; border-radius: 6px; padding: 7px 14px; font-weight: 600; }
            QPushButton:hover { background: #3F3F46; border-color: #6366F1; }
            QGroupBox { border: 1px solid #27272A; border-radius: 8px; margin-top: 14px; font-weight: bold; padding: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #818CF8; }
            QSlider::groove:horizontal { height: 6px; background: #27272A; border-radius: 3px; }
            QSlider::sub-page:horizontal { background: #6366F1; border-radius: 3px; }
            QSlider::handle:horizontal { background: #FAFAFA; width: 16px; margin: -5px 0; border-radius: 8px; }
            QTextEdit { background: #09090B; border: 1px solid #27272A; font-family: 'Consolas', monospace; font-size: 11px; color: #A5B4FC; }
        """)

        self.ble.log_signal.connect(self.append_log)
        self.ble.status_signal.connect(self.on_device_status)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Header
        hdr = QHBoxLayout()
        lbl_title = QLabel("AymashTain LED RGB Remote <span style='color:#818CF8;font-size:11px;'>v0.48-desktop</span>")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        hdr.addWidget(lbl_title)
        hdr.addStretch()
        self.lbl_status = QLabel("Connected: 0/3 Strips")
        self.lbl_status.setStyleSheet("color: #10B981; font-weight: bold;")
        hdr.addWidget(self.lbl_status)
        layout.addLayout(hdr)

        # Tabs
        tabs = QTabWidget()
        self.tab_strips = QWidget()
        self.tab_remote = QWidget()
        self.tab_sweep = QWidget()
        self.tab_cam = QWidget()

        self.build_strips_tab()
        self.build_remote_tab()
        self.build_sweep_tab()
        self.build_camera_tab()

        tabs.addTab(self.tab_strips, "Strips & Bluetooth")
        tabs.addTab(self.tab_remote, "Remote & Color")
        tabs.addTab(self.tab_sweep, "Sweep Engine")
        tabs.addTab(self.tab_cam, "Camera Verification")
        layout.addWidget(tabs, stretch=1)

        # Log box
        log_box = QGroupBox("System Logs")
        lb_layout = QVBoxLayout(log_box)
        self.log_txt = QTextEdit()
        self.log_txt.setReadOnly(True)
        self.log_txt.setMaximumHeight(130)
        lb_layout.addWidget(self.log_txt)
        layout.addWidget(log_box)

    def build_strips_tab(self):
        l = QVBoxLayout(self.tab_strips)
        grp = QGroupBox("Configured Physical Strips")
        gl = QVBoxLayout(grp)
        self.strip_lbls = {}
        for dev in DEFAULT_STRIPS:
            addr = dev["address"]
            r = QHBoxLayout()
            r.addWidget(QLabel(f"<b>{dev['name']}</b> ({addr})"), stretch=2)
            st = QLabel("Disconnected")
            st.setStyleSheet("color: #EF4444; font-weight: bold;")
            self.strip_lbls[addr] = st
            r.addWidget(st, stretch=1)
            b_c = QPushButton("Connect")
            b_c.clicked.connect(lambda _, a=addr: asyncio.create_task(self.ble.connect_device(a)))
            b_d = QPushButton("Disconnect")
            b_d.clicked.connect(lambda _, a=addr: asyncio.create_task(self.ble.disconnect_device(a)))
            r.addWidget(b_c)
            r.addWidget(b_d)
            gl.addLayout(r)
        l.addWidget(grp)

        bar = QHBoxLayout()
        b_all = QPushButton("Connect All Strips")
        b_all.setStyleSheet("background: #4F46E5; color: white;")
        b_all.clicked.connect(lambda: [asyncio.create_task(self.ble.connect_device(d["address"])) for d in DEFAULT_STRIPS])
        b_p = QPushButton("Blink / Flash Confirmation")
        b_p.clicked.connect(lambda: asyncio.create_task(self.ble.pulse()))
        bar.addWidget(b_all)
        bar.addWidget(b_p)
        l.addLayout(bar)
        l.addStretch()

    def build_remote_tab(self):
        l = QVBoxLayout(self.tab_remote)
        pwr = QHBoxLayout()
        b_on = QPushButton("POWER ON (BC01010155)")
        b_on.setStyleSheet("background: #059669; color: white; padding: 10px;")
        b_on.clicked.connect(lambda: asyncio.create_task(self.ble.send_hex_all(CMD_ON)))
        b_off = QPushButton("POWER OFF (BC01010055)")
        b_off.setStyleSheet("background: #DC2626; color: white; padding: 10px;")
        b_off.clicked.connect(lambda: asyncio.create_task(self.ble.send_hex_all(CMD_OFF)))
        pwr.addWidget(b_on)
        pwr.addWidget(b_off)
        l.addLayout(pwr)

        grp = QGroupBox("Color Presets")
        gl = QHBoxLayout(grp)
        presets = [
            ("Red", 255, 0, 0, "#EF4444"), ("Green", 0, 255, 0, "#10B981"),
            ("Blue", 0, 0, 255, "#3B82F6"), ("Cyan", 0, 255, 255, "#06B6D4"),
            ("Purple", 255, 0, 255, "#A855F7"), ("Yellow", 255, 220, 0, "#EAB308"),
            ("White", 255, 255, 255, "#FAFAFA"),
        ]
        for name, r, g, b, col in presets:
            btn = QPushButton(name)
            btn.setStyleSheet(f"border-left: 5px solid {col};")
            btn.clicked.connect(lambda _, cr=r, cg=g, cb=b: asyncio.create_task(self.ble.send_hex_all(encode_mrstar_color(cr, cg, cb))))
            gl.addWidget(btn)
        btn_pick = QPushButton("Picker...")
        btn_pick.clicked.connect(self.pick_color)
        gl.addWidget(btn_pick)
        l.addWidget(grp)

        bg = QGroupBox("Brightness")
        bgl = QVBoxLayout(bg)
        self.sli = QSlider(Qt.Horizontal)
        self.sli.setRange(0, 100)
        self.sli.setValue(100)
        self.sli.valueChanged.connect(lambda val: asyncio.create_task(self.ble.send_hex_all(encode_mrstar_brightness(val/100.0))))
        bgl.addWidget(self.sli)
        l.addWidget(bg)
        l.addStretch()

    def pick_color(self):
        c = QColorDialog.getColor(Qt.red, self)
        if c.isValid():
            asyncio.create_task(self.ble.send_hex_all(encode_mrstar_color(c.red(), c.green(), c.blue())))

    def build_sweep_tab(self):
        l = QVBoxLayout(self.tab_sweep)
        b = QPushButton("Start 12-Step Hue Sweep (BC0406... 400ms)")
        b.setStyleSheet("background: #4F46E5; color: white; padding: 10px;")
        b.clicked.connect(self.run_sweep)
        l.addWidget(b)
        self.sw_log = QTextEdit()
        self.sw_log.setReadOnly(True)
        l.addWidget(self.sw_log)

    def run_sweep(self):
        asyncio.create_task(self._sweep())

    async def _sweep(self):
        self.sw_log.clear()
        self.sw_log.append("[Sweep] Starting sequence with 12 commands. Gap: 400ms...")
        for i in range(12):
            hue = (i * 30) % 360
            cmd = f"BC0406{hue:04X}03E8000055"
            await self.ble.send_hex_all(cmd)
            self.sw_log.append(f"[{i + 1}/12] {time.strftime('%H:%M:%S')} {cmd} -> OK")
            await asyncio.sleep(0.4)
        self.sw_log.append("[Sweep] Completed sweep run.\n")

    def build_camera_tab(self):
        l = QVBoxLayout(self.tab_cam)
        self.btn_cam = QPushButton("Start Webcam Preview")
        self.btn_cam.clicked.connect(self.toggle_cam)
        l.addWidget(self.btn_cam)
        self.cam_disp = QLabel("Camera idle. Click 'Start Webcam Preview'.")
        self.cam_disp.setAlignment(Qt.AlignCenter)
        self.cam_disp.setStyleSheet("background: #000; min-height: 360px; border-radius: 8px;")
        l.addWidget(self.cam_disp, stretch=1)
        self.cap = None
        self.tm = QTimer(self)
        self.tm.timeout.connect(self.read_cam)

    def toggle_cam(self):
        if not HAS_OPENCV:
            QMessageBox.warning(self, "OpenCV Missing", "Run: pip install opencv-python")
            return
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                QMessageBox.warning(self, "Camera Error", "Could not open webcam.")
                self.cap = None
                return
            self.tm.start(33)
            self.btn_cam.setText("Stop Webcam Preview")
        else:
            self.tm.stop()
            self.cap.release()
            self.cap = None
            self.btn_cam.setText("Start Webcam Preview")
            self.cam_disp.setText("Camera idle.")

    def read_cam(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                h, w, _ = frame.shape
                cv2.rectangle(frame, (int(w*0.3), int(h*0.35)), (int(w*0.7), int(h*0.65)), (0, 255, 0), 2)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = QImage(rgb.data, w, h, 3*w, QImage.Format_RGB888)
                self.cam_disp.setPixmap(QPixmap.fromImage(img).scaled(self.cam_disp.size(), Qt.KeepAspectRatio))

    def on_device_status(self, address: str, status: str):
        if address in self.strip_lbls:
            lbl = self.strip_lbls[address]
            lbl.setText(status.capitalize())
            lbl.setStyleSheet("color: #10B981; font-weight: bold;" if status == "connected" else "color: #EF4444;")
        cnt = len([c for c in self.ble.clients.values() if c.is_connected])
        self.lbl_status.setText(f"Connected: {cnt}/3 Strips")

    def append_log(self, kind: str, msg: str):
        self.log_txt.append(f"[{time.strftime('%H:%M:%S')}] [{kind.upper()}] {msg}")

def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    ble = BleManager()
    win = MainWindow(ble)
    win.show()
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
