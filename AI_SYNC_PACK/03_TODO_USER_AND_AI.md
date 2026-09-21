# TODO - User and AI

Easy-to-read list of what is done and what is left.

**Version:** v0.61 Alpha

---

## A. Done

### Protocol and hardware

- [x] `mrstar_protocol.py` corrected and verified.
- [x] Colour command verified: `BC0406000003E8000055`.
- [x] Brightness command verified: `BC0506040000000055`.
- [x] Decoder shows `confidence: documented`.
- [x] Hardware test passed at BLE transport level (2026-09-19 21:10).
- [x] Logs saved:
  - `hardware_test_20260919_211043.log`
  - `hardware_test_20260919_211043.json`
  - `hardware_test_20260919_211043.csv`

### Core app

- [x] Project rebuilt as a package `aymashtain/` (Devin AI).
- [x] Per-device serialized BLE queue in `ble/manager.py`.
- [x] Ordered colour -> brightness in `BleManager.set_color()`.
- [x] Session logger with `.log`, `.json`, `.csv`.
- [x] 9 tabs: Connect, Remote, Music & Media, Sweep, Camera, Console,
      Lab, Events, Options.
- [x] Auto-reconnect.
- [x] Emergency stop (Esc + Control menu).
- [x] App confirmed running: 3/3 strips connect, 54 frames sent, 0
      failed.
- [x] PyInstaller spec, `build_exe.bat`, `run.bat`, `repair.ps1`.
- [x] `CREDITS.md` added.
- [x] `.gitignore` cleaned.
- [x] GitHub sync working.

### Round 2 (Session 5)

- [x] `__init__.py` - version bumped to `0.61.0` +
      `APP_DISPLAY_VERSION`.
- [x] `config.py` - `theme_mode`, dev lock, brightness clamp, camera /
      audio slots, window memory, per-pattern sources.
- [x] `options_tab.py` - **NEW FILE**, all app-wide settings in one
      place.
- [x] `tabs/__init__.py` - exports `OptionsTab`.
- [x] `main_window.py` - Options tab, View + Options menus, dev lock,
      Extract log, min window 300x300, window memory.
- [x] `camera_tab.py` - border states, resolution / FPS dropdowns, real
      exposure + WB lock, honest driver report.
- [x] `strip_preview.py` - neon capsules, per-LED glow, grey backing.
- [x] `music_tab.py` - mic selection moved out, per-pattern source,
      **Play button fixed**, brightness clamp, neon preview.
- [x] `remote_tab.py` - brightness clamp on every path, live per-LED
      preview on slider drag, wired to new neon preview. (Session 6)

### Hand-off tooling (Session 6)

- [x] `make_handoff.py` - one-click bundle builder, numbered zips in
      `handoff\`.
- [x] `make_handoff.bat` - double-click wrapper.
- [x] `AI_SYNC_PACK/07_HOW_TO_USE_AI_SYNC.md` - rewritten for one-click
      flow.
- [x] `AI_SYNC_PACK/00_MASTER_SUMMARY.md` - v0.61, new structure,
      hand-off section.
- [x] `AI_SYNC_PACK/01_WORKFLOW.md` - new sessions logged.
- [x] `AI_SYNC_PACK/02_UNIVERSAL_AI_PROMPT.md` - v0.61, one-click flow.
- [x] `AI_SYNC_PACK/03_TODO_USER_AND_AI.md` - this file.
- [x] `AI_SYNC_PACK/05_DEVELOPER_README.md` - v0.61, hand-off section.
- [x] `AI_SYNC_PACK/06_CURRENT_CHAT.md` - Sessions 5 and 6 appended.

---

## B. Next up - remaining Round 2 items

In priority order:

- [ ] **`events.py` / `events_tab.py`** - user-facing "Export log" only.
      No log path shown to the end user. Auto-save on close stays.
- [ ] **`theme.py`** - soften dark-mode highlights; fix Remote "white"
      colour rendering; audit every menu in dark mode.
- [ ] **`sweep_tab.py`** - route its brightness sweep through
      `settings.clamp_brightness()`.
- [ ] **`console_tab.py`** - clamp user-supplied brightness frames
      (optional but recommended).
- [ ] **Final compile pass** on every replaced file, then a full test
      run.

---

## C. Later - Round 3 candidates

### Camera

- [ ] Visual ROI picker for Strip 1 / 2 / 3 in `camera_tab.py`.
- [ ] Live rectangle overlay on the preview.
- [ ] Save ROI to `config.json` on change.
- [ ] "Calibrate" button that averages 30 frames of a static colour and
      stores a baseline.

### UI

- [ ] 150-LED horizontal preview driven by real per-LED data.
- [ ] About dialog with `CREDITS.md` content and GitHub link.
- [ ] Profile import / export in `remote_tab.py`.
- [ ] Icon: verify `assets\aymashtain.ico` is picked up.

### Music & Media

- [ ] Confirm microphone path works on user's PC.
- [ ] Confirm WASAPI loopback fallback works on user's PC.
- [ ] Confirm "playing file" source works.
- [ ] Add duplicate-colour suppression.
- [ ] Add "ensure on" before starting music.
- [ ] Retro Winamp-style visualizer.
- [ ] Video file playback.
- [ ] MPC + K-Lite integration.

### Testing

- [ ] Run hidden-feature lab on one strip only first, then all three.
- [ ] Confirm no Scroll / M1 corruption after a lab session.
- [ ] Confirm far strip stays connected with `inter_device_delay_ms =
      60`.
- [ ] Re-test camera with new ROI.

### Packaging

- [ ] Rebuild EXE from the package.
- [ ] Test on a clean Windows machine.
- [ ] Publish GitHub release with the EXE + `_internal` folder.
- [ ] Verify downloaded ZIP runs.

---

## D. Housekeeping - optional

- [ ] Delete leftover junk from the project root: `test.txt`,
      `events.csv`, `events.json`, `build/`. The hand-off tool ignores
      them, but they add clutter.
- [ ] Decide whether to keep `AI_CONTEXT.md`, `AI_NOTES.md`,
      `AI_SESSIONS.md`, `AI_BRIEF.md`, `AI_BACKLOG.md`, `PROJECT.md`,
      `ai_sync.py`. They currently stay and ship in the bundle as a
      bonus.
- [ ] Move `aymashtain.ico` into a new `assets\` folder (or update
      `paths.py` to look in the project root).