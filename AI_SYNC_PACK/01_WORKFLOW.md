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

## 2026-09-21 - Remaining Round 2 UI polish (Session 7)

**DeepSeek**

- `events_tab.py` - user-facing "Export log..." only. Log path never
  shown to the end user. Format picked by file dialog extension. Default
  filename uses the Options save location.
- `theme.py` - dark-mode highlights softened (indigo-800 tabs, indigo-700
  accent buttons, zinc-300 slider handle). Menu audit: `pressed`,
  `disabled`, `separator`, `indicator` rules added to both themes. Light
  theme brought to parity with dark.
- `remote_tab.py` - preset buttons now carry colour as a small icon
  (`_color_swatch()`), inline `border-left` stylesheet removed, unicode
  chars swapped for ASCII.
- `sweep_tab.py` - brightness sweep runs *within* Options min/max range
  instead of sweeping 0..1 and clamping step by step. New info line.
  `sync_clamp_notice()` public hook for the main window.
- `console_tab.py` - any `BC0506` frame typed or pasted in is clamped
  against the Options min/max before it is queued. "Decode only" shows a
  preview of what would be clamped without sending. New info label +
  `sync_clamp_notice()` hook.
- Sync pack cleanup - `00`, `01`, `03` re-saved clean as UTF-8.

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

## 2026-09-21 - Pytest discovery + handoff prep (Sessions 8 cont. + 9)

**DeepSeek**

- Ran `python -m pytest -q` for the first time.
- Discovered `aymashtain/__init__.py` had been overwritten with the
  contents of `ui/tabs/__init__.py`.
- Restored `aymashtain/__init__.py` to app-identity constants only.
- Re-ran pytest: **27 passed**.
- Prepared handoff bundle for the first live test run.
- App not yet launched.

---

## 2026-09-21 - Live test + sync pack cleanup (Session 10)

**User**

- Ran the app live and walked Section B of `03_TODO_USER_AND_AI.md`.
- Reported every result — most passed; a small set failed (Console
  clamp, Sweep mid-run range, light-theme camera borders, camera
  exposure / WB, Music grouping, Remote clamp notice).
- Asked for the sync pack to be rewritten cleanly — several files were
  damaged from a prior attempt (code fences never closed, headings
  lost, whole sections missing).
- Asked for a **flat hand-off bundle**: fewer files, zero subfolders,
  no duplicate filenames, `__init__.py` files renamed by parent folder.

**DeepSeek**

- Delivered full replacement sync pack files 00–07 as UTF-8 markdown,
  one at a time.
- Recorded every passed / failed live-test item in `03_TODO` and
  `04_AI_ERRORS_ONLY`.
- Designed the flat bundle layout.
- Created `make_handoff.py` (first flat version).

---

## 2026-09-21 - Flat handoff refinement + end-of-chat ritual (Session 11)

**User**

- First flat-bundle version produced **83 files** — too many.
- Requested **under 35 files** to leave room for screenshots under
  DeepSeek's 50-file cap.
- Requested `.gitignore` and anything else AI chats don't accept be
  dropped.
- Requested a reusable `08_End_Chat.md` so any session can close
  cleanly.

**DeepSeek**

- Rewrote `make_handoff.py` with an **explicit allowlist** of 27 source
  files (previously "bundle everything and exclude").
- Merged docs into 3 files (`00_PROJECT_MASTER_DOCS.md`,
  `01_WORKFLOW_AND_TODO.md`, `02_CURRENT_CHAT.md`).
- Merged 5 sub-package `__init__.py` files into
  `_package_init_exports.md`.
- Added `--dry-run` flag.
- Fixed `make_handoff.bat` (working-directory, error handling, pause).
- Created `AI_SYNC_PACK/08_End_Chat.md`.
- Dry run: **32 files total**, zero subdirectories, no collisions, no
  read failures.

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
| 2026-09-21 | DeepSeek | Remaining Round 2 UI polish (Session 7) |
| 2026-09-21 | DeepSeek | Compile pass + blocker fixes (Session 8) |
| 2026-09-21 | DeepSeek | Pytest fix + handoff prep (Session 9) |
| 2026-09-21 | User + DeepSeek | Live test + sync pack cleanup (Session 10) |
| 2026-09-21 | User + DeepSeek | Flat handoff refinement + `08_End_Chat.md` (Session 11) |