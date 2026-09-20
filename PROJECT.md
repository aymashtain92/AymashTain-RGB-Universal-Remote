# AymashTain RGB Universal Remote

Free, ad-free Windows desktop app for controlling BLE RGB LED strips
speaking the MR Star protocol.

Repo: https://github.com/aymashtain92/AymashTain-RGB-Universal-Remote

## Stack
- Python 3.10+, PySide6, bleak, OpenCV, qasync, sounddevice, numpy
- Windows primary

## Architecture
- main.py — Qt window
- aymashtain/protocol.py — MR Star frames
- aymashtain/storage.py — config + sqlite
- aymashtain/vision.py — webcam sampling
- aymashtain/audio.py — reactive audio
- tests/ — unit tests

## Protocol quick reference
- Power       BC 01 01 XX 55
- Colour      BC 04 06 HHHH SSSS 0000 55
- Brightness  BC 05 06 BBBB 00000000 55
- Effect      BC 06 02 XX 0000 55

Rule: colour and brightness are always two frames.

## Rules for AIs
1. Read this file, then AI_CONTEXT.md.
2. Never edit AI_CONTEXT.md — auto-generated.
3. After a session: python ai_sync.py note "what you did"
4. Keep protocol.py Qt-free.
5. Run python -m pytest -q before suggesting commits.