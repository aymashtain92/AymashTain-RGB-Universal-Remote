# AymashTain LED RGB Remote — Workflow and Timeline

Dates based on timestamps in the provided conversations and logs.

---

## 2026-09-17 — First troubleshooting and protocol capture

**User**
- Asked why MR Star strips lag behind music.
- Corrected AIs: strips use the USB device mic, not phone mic.
- Wanted PC control, no new hardware.
- Provided `btsnoop_hci_260917_192456.log`.

**DeepSeek**
- Parsed btsnoop log.
- Found Scroll sequence and opcodes (`BC11`, `BC06`, `BC0F`, `BC01`).
- Built `RGB_controller_v2.py`.
- Confirmed Scroll on one strip, FFF3 write handle.

**User**
- Tested. Old Triones commands failed. Only Scroll worked.

**DeepSeek**
- Found colour and brightness are separate commands.

---

## 2026-09-18 — App building

**Claude**
- Built LumenBench HTML artifact.
- Built BLE Light Command Deck.

**Gemini Studio AI**
- Built React/PySide-style app with many tabs.
- User reported bugs (camera, colour wheel, BLE, labels).

**User**
- Demanded full files, not partial edits.
- Asked for auto-save logs, camera analysis, all hidden features.

---

## 2026-09-19 — Copilot review, hardware test, protocol correction

**GitHub Copilot**
- Reviewed code.
- Found the core bug: colour and brightness must be separate.
- `BC0406HHHHSSSS000055` for colour, `BC0506BBBB0000000055` for brightness.
- No `FFFF` white field.

**User**
- Ran corrected `mrstar_protocol.py` and `hardware_test.py`.
- Verified colour/brightness decode shows `confidence: documented`.
- Ran hardware test — 3/3 connected, all commands accepted.
- Logs saved:
  - `hardware_test_20260919_211043.log`
  - `hardware_test_20260919_211043.json`
  - `hardware_test_20260919_211043.csv`

---

## 2026-09-20 — Package rewrite, first working app

**Devin AI**
- Rebuilt the project as a proper Python package `aymashtain/`.
- Added: `ble/manager.py` with serialized per-device queue, `protocol/mrstar.py`, `storage/db.py`, `vision/camera.py`, `audio/engine.py`.
- Added 8 tabs: Connect, Remote, Music & Media, Sweep, Camera, Console, Lab, Events.
- Added PyInstaller spec, `run.bat`, `build_exe.bat`, `repair.ps1`.
- Committed to `D:\Coding projects\aymashtain-led-remote-Source`.

**User**
- Confirmed the app runs.
- Confirmed 3/3 strips connect and 54 frames send without failure.

**ChatGPT / Current Assistant**
- Discovered the AI_SYNC_PACK described the old flat project, not this package.
- Rewriting `00`–`06` to match the real project.

---

## 2026-09-21 — Sync pack correction (current)

**User**
- Chose the package project as the real one.
- Requested the sync pack be corrected to describe it.

**ChatGPT / Current Assistant**
- Rewrote `00`–`06` to describe the package structure.
- Confirmed hidden-feature lab, camera ROI, exposure lock, 150-LED preview, profile import/export, About dialog are the remaining gaps.

---

## Who did what

| Date | AI / Person | Contribution |
|---|---|---|
| 2026-09-17 | User | btsnoop log, USB mic correction |
| 2026-09-17 | DeepSeek | Reverse-engineered Scroll, opcodes, controller v2 |
| 2026-09-17 | Meta AI | Suggested PC control routes |
| 2026-09-18 | Claude | LumenBench HTML artifact |
| 2026-09-18 | Gemini Studio | React/PySide app, many tabs |
| 2026-09-19 | GitHub Copilot | Found colour/brightness split |
| 2026-09-19 | DeepSeek | Queue, auto-save, camera recommendations |
| 2026-09-19 | User | Replaced protocol + hardware test, ran test |
| 2026-09-20 | Devin AI | Rebuilt as a package, added BleManager queue, 8 tabs |
| 2026-09-20 | User | Confirmed app runs, 3/3 strips connect |
| 2026-09-21 | ChatGPT / Current | Corrected the sync pack to match the package |