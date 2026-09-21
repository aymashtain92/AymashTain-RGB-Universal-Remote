# AymashTain LED RGB Remote - Workflow and Timeline

Dates based on timestamps in the provided conversations and logs.

---

## 2026-09-17 - First troubleshooting and protocol capture

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

## 2026-09-18 - App building

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

## 2026-09-19 - Copilot review, hardware test, protocol correction

**GitHub Copilot**
- Reviewed code.
- Found the core bug: colour and brightness must be separate.
- `BC0406HHHHSSSS000055` for colour, `BC0506BBBB0000000055` for
  brightness.
- No `FFFF` white field.

**User**
- Ran corrected `mrstar_protocol.py` and `hardware_test.py`.
- Verified colour/brightness decode shows `confidence: documented`.
- Ran hardware test - 3/3 connected, all commands accepted.
- Logs saved:
  - `hardware_test_20260919_211043.log`
  - `hardware_test_20260919_211043.json`
  - `hardware_test_20260919_211043.csv`

---

## 2026-09-20 - Package rewrite, first working app

**Devin AI**
- Rebuilt the project as a proper Python package `aymashtain/`.
- Added: `ble/manager.py` with serialized per-device queue,
  `protocol/mrstar.py`, `storage/db.py`, `vision/camera.py`,
  `audio/engine.py`.
- Added 8 tabs: Connect, Remote, Music & Media, Sweep, Camera, Console,
  Lab, Events.
- Added PyInstaller spec, `run.bat`, `build_exe.bat`, `repair.ps1`.
- Committed to `D:\Coding projects\aymashtain-led-remote-Source`.

**User**
- Confirmed the app runs.
- Confirmed 3/3 strips connect and 54 frames send without failure.

**DeepSeek**
- Discovered the AI_SYNC_PACK described the old flat project, not this
  package.
- Rewrote `00`-`06` to match the real project.

---

## 2026-09-21 - Sync pack correction (Session 1)

**User**
- Chose the package project as the real one.
- Requested the sync pack be corrected to describe it.

**DeepSeek**
- Rewrote `00`-`06` to describe the package structure.
- Confirmed hidden-feature lab, camera ROI, exposure lock, 150-LED
  preview, profile import/export, About dialog are the remaining gaps.

---

## 2026-09-21 - Hidden-feature laboratory (Session 2)

**User**
- Asked to add a hidden-feature laboratory.

**DeepSeek**
- Replaced `lab_tab.py` with template generator, candidate list,
  delay/hold/capture controls, start/stop/emergency, CSV/JSON export,
  results table with editable notes.
- Replaced `main_window.py` with `stop_all_activity()`, Esc + Ctrl+.
  emergency stop, `_disconnect_with_timeout()`, and passed
  `camera_tab` to the Lab tab.
- Both files compiled cleanly.

---

## 2026-09-21 - Test round (Session 3)

**User**
- Tested the app end to end.

**Findings**
- 3/3 strips connect, colour + brightness send correctly.
- Sweep, Console, Events, Lab all work.
- Broken or rough: dark mode too bright, Remote "white" wrong, camera
  auto-exposure not locked, neon preview missing, no scrolling when
  small, max brightness unresolved, Music tab messy, logs and dev tabs
  exposed, version mismatch `1.0.0` vs `v0.51 Alpha`.

---

## 2026-09-21 - Round 2 spec written (Session 4)

**User**
- Approved a Round 2 feature spec targeting **v0.61 Alpha**.
- Will run it in a fresh chat to test the auto-update workflow.

---

## 2026-09-21 - Round 2 implementation (Session 5)

**DeepSeek**

Files replaced:

- `aymashtain/__init__.py` - version `0.61.0`, `APP_DISPLAY_VERSION`.
- `aymashtain/config.py` - full rewrite: theme_mode, dev lock, brightness
  clamp, camera/audio slots, window memory, per-pattern sources.
- `aymashtain/ui/tabs/options_tab.py` - **NEW**.
- `aymashtain/ui/tabs/__init__.py` - exports `OptionsTab`.
- `aymashtain/ui/main_window.py` - Options tab, View menu, dev lock,
  Extract log, 300x300 min, window memory.
- `aymashtain/ui/tabs/camera_tab.py` - border states, resolution/FPS
  dropdowns, real exposure + WB lock, honest driver report.
- `aymashtain/ui/widgets/strip_preview.py` - neon capsules, per-LED glow.
- `aymashtain/ui/tabs/music_tab.py` - mic out, per-pattern source, Play
  fix, clamp, neon preview.

---

## 2026-09-21 - Hand-off tool + `remote_tab.py` (Session 6)

**DeepSeek**

- **NEW** `make_handoff.py` + `make_handoff.bat` - one-click bundle into
  `handoff\handoff_NNN_<timestamp>.zip`.
- `AI_SYNC_PACK/07_HOW_TO_USE_AI_SYNC.md` - rewritten for one-click flow.
- `AI_SYNC_PACK/00_MASTER_SUMMARY.md` - v0.61, new structure, hand-off
  section.
- `AI_SYNC_PACK/05_DEVELOPER_README.md` - v0.61, hand-off section.
- `AI_SYNC_PACK/06_CURRENT_CHAT.md` - Session 6 appended.
- `aymashtain/ui/tabs/remote_tab.py` - brightness clamp, live per-LED
  preview, wired to new neon preview.

Still pending after Session 6:
- `events.py` / `events_tab.py` - user-facing "Export log" only.
- `theme.py` - dark-mode softening, menu audit, Remote white fix.
- `sweep_tab.py` - brightness clamp.
- `console_tab.py` - clamp user-supplied brightness frames (optional).
- Final compile pass.
---

## 2026-09-21 - Compile pass + blocker fixes (Session 8)

**DeepSeek**
- Reviewed every file replaced in Sessions 5-7 before the first test.
- Fixed `tabs/__init__.py`: `OptionsTab` was missing from the exports.
- Fixed `music_tab.py`: added `_stop_reacting()` alias so the emergency
  stop does not crash.
- Verified all 10 `__init__.py` files export what their callers import.
- Full compile pass ran clean with no output.
- Phase 0 clamp-notice wiring deferred to Round 3.
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
| 2026-09-20 | Devin AI | Rebuilt as a package, BleManager queue, 8 tabs |
| 2026-09-20 | User | Confirmed app runs, 3/3 strips connect |
| 2026-09-21 | DeepSeek | Sync pack correction (Session 1) |
| 2026-09-21 | DeepSeek | Hidden-feature laboratory (Session 2) |
| 2026-09-21 | User | Test round findings (Session 3) |
| 2026-09-21 | User | Round 2 spec authored (Session 4) |
| 2026-09-21 | DeepSeek | Round 2 implementation (Session 5) |
| 2026-09-21 | DeepSeek | Hand-off tool + remote_tab (Session 6) |