# AymashTain LED RGB Remote

A free, open, no-ads desktop app for Windows that controls BLE LED strips and
bulbs using the MR Star protocol family (also known as MR-Star, Magic Home
compatible variants, and clones).

Written in Python with PySide6. Uses Bleak for BLE, OpenCV for local camera
verification, and QtMultimedia for audio playback.

## What it does

- Scans and connects to multiple BLE LED strips at once.
- Sends documented MR Star commands: color (`BC0406...`), brightness (`BC0506...`),
  power (`BC01...`), and effects (`BC06...`).
- Keeps color and brightness as **separate** commands, which is the correct
  MR Star behavior. This fixes the white-tint / pale-color bug that appears
  when they are merged.
- Builds custom remotes with buttons, groups, and macros.
- Replays captured multi-frame sequences (Scroll / M-capture) exactly as recorded.
- Runs automated sweeps of color, saturation, brightness, or effect bytes.
- Verifies the physical output with a local webcam: RGB, brightness, and white
  contamination per sample.
- Optional multi-sample per command to measure how fast the strip settles.
- Full Media Player tab: play, pause, stop, prev, next, seek, volume, playlist,
  shuffle, repeat.
- Automatic session logs (`.log`, `.json`, `.csv`) saved to `logs/`.
- Auto-cleans log files older than 3 days on startup.
- Persistent settings: window position, camera exposure and region, sweep timing,
  media volume.

## Requirements

- Windows 10 or 11 (64-bit)
- Python 3.10 or newer (3.12 recommended)
- Bluetooth enabled
- Visual C++ Redistributable 2022
- Optional: any USB or built-in webcam, for camera verification

## Install

Double-click or run in PowerShell:

```powershell
.\install_and_repair.ps1