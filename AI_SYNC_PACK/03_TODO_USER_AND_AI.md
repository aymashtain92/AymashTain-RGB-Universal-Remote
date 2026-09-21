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

### Round 2 - Session 5

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

### Round 2 - Session 6

- [x] `remote_tab.py` - brightness clamp on every path, live per-LED
      preview on slider drag, wired to new neon preview.
- [x] `make_handoff.py` - one-click bundle builder, numbered zips in
      `handoff\`.
- [x] `make_handoff.bat` - double-click wrapper.
- [x] `AI_SYNC_PACK/07_HOW_TO_USE_AI_SYNC.md` - rewritten for one-click
      flow.
- [x] `AI_SYNC_PACK/00_MASTER_SUMMARY.md` - v0.61, new structure,
      hand-off section.
- [x] `AI_SYNC_PACK/01_WORKFLOW.md` - new sessions logged.
- [x] `AI_SYNC_PACK/02_UNIVERSAL_AI_PROMPT.md` - v0.61, one-click flow.
- [x] `AI_SYNC_PACK/05_DEVELOPER_README.md` - v0.61, hand-off section.
- [x] `AI_SYNC_PACK/06_CURRENT_CHAT.md` - Sessions 5 and 6 appended.

### Round 2 - Session 7 (remaining code + sync pack cleanup)

- [x] `events_tab.py` - user-facing "Export log..." only. Log path is
      never shown to the end user. Format picked by file dialog
      extension. Default filename uses the Options save location.
- [x] `theme.py` - dark-mode highlights softened (indigo-800 tabs,
      indigo-700 accent buttons, zinc-300 slider handle). Menu audit:
      `pressed`, `disabled`, `separator`, `indicator` rules added to
      both themes. Light theme brought to parity with dark.
- [x] `remote_tab.py` - preset buttons now carry colour as a small icon
      (`_color_swatch()`) instead of an inline `border-left` stylesheet.
      Old approach wiped every other button rule, which is why "warm
      white" / "cool white" rendered as plain grey rectangles. Inline
      `color: #71717A` on the clamp label removed (theme handles muted
      text now). Remaining unicode chars swapped for ASCII.
- [x] `sweep_tab.py` - brightness sweep now runs *within* the Options
      min/max range instead of sweeping 0..1 and clamping step by step.
      Reads `settings.brightness_min` / `brightness_max` fresh on every
      step. New info line shows the range when brightness mode is
      selected. `sync_clamp_notice()` public hook for the main window.
- [x] `console_tab.py` - any `BC0506` brightness frame typed or pasted
      in is clamped against the Options min/max before it is queued.
      "Decode only" shows a preview of what would be clamped without
      sending. Output line prints `original -> clamped` when a frame was
      adjusted. New info label + `sync_clamp_notice()` hook.
- [x] Sync pack cleanup - `00_MASTER_SUMMARY.md`, `01_WORKFLOW.md`,
      `03_TODO_USER_AND_AI.md` re-saved clean as UTF-8.

### Round 2 - Final compile pass

- [x] `options_tab.py`, `tabs/__init__.py`, `main_window.py`, `main.py`
- [x] `camera_tab.py`, `strip_preview.py`, `music_tab.py`
- [x] `make_handoff.py`, `theme.py`, `remote_tab.py`
- [x] `events_tab.py`, `sweep_tab.py`, `console_tab.py`

---

## B. Now - test round

Do these in order. Tick as you go.

### Compile

- [ ] Run the full compile pass (see the command block at the bottom
      of this file). No output on any line = all clean.

### Launch and smoke test

- [ ] App launches with `python .\main.py` or `run.bat`.
- [ ] 9 tabs visible when Developer Tools is ON.
- [ ] 8 tabs visible when Developer Tools is OFF (Lab hidden).
- [ ] Version string shows `v0.61 Alpha` in the title bar and About box.

### Remote tab

- [ ] Preset buttons render with small coloured square icons next to
      the label (Red, Orange, Yellow, Green, Cyan, Blue, Violet,
      Magenta, Warm white, Cool white).
- [ ] Dragging the brightness slider updates the neon preview *live*.
- [ ] Releasing the slider sends exactly one `BC0506` frame (check the
      Events tab counter).
- [ ] Set Options brightness max to 60%, come back to Remote, release
      the slider at 100% — the strip stops at 60% and the clamp notice
      appears under the slider.

### Sweep tab

- [ ] Select "Brightness (0-100%)" mode — the info line shows the
      Options range (e.g. "Brightness sweep will run from 20% to 80%").
- [ ] Run the sweep — every step lands inside the Options range, no
      step collapses to the same value.
- [ ] Change the Options range mid-run — the next step follows the new
      range.

### Console tab

- [ ] The info label at the top says whether the clamp is active.
- [ ] Paste `BC0506040000000055` (100%) with Options max at 60%.
- [ ] Click "Decode only" — an orange clamp preview line appears.
- [ ] Click "Send all" — the output shows
      `BC0506040000000055 -> clamped to BC050603... -> N device(s)`.
- [ ] A colour frame like `BC0406000003E8000055` passes through
      untouched.

### Events tab

- [ ] Filter checkboxes work.
- [ ] Search box filters live.
- [ ] "Export log…" opens a save dialog defaulting to the Options save
      location.
- [ ] Save as `.csv` — file opens cleanly in Excel.
- [ ] Save as `.json` — file is valid JSON.
- [ ] After export, the status line just says "Log exported" — the path
      is NOT shown.

### Theme

- [ ] Toggle dark mode from the View menu — no harsh bright highlights.
- [ ] Every menu opens and its selected item is readable.
- [ ] Toggle light mode — camera tab borders, tab bar, menus all look
      correct.
- [ ] Toggle "Follow system" in Options — picks up the OS setting.

### Options tab

- [ ] Changing theme updates the app instantly.
- [ ] Toggling Developer Tools hides/shows the Lab tab.
- [ ] Brightness min / max sliders stay ordered (min never above max).
- [ ] Save location Browse button works; Reset clears it.
- [ ] Camera device / resolution / FPS dropdowns reflect current
      settings.
- [ ] Window "Remember screen, position, size" checkbox saves on close
      and restores on next launch.

### Camera tab

- [ ] Preview border is light grey when closed, dark grey when open.
- [ ] Resolution dropdown changes the capture size.
- [ ] FPS dropdown changes the frame rate.
- [ ] Exposure lock: status line honestly says whether the driver
      accepted it, or "driver refused lock — auto may win".
- [ ] WB lock: same honesty.
- [ ] Camera is local-only — no network traffic.

### Music & Media tab

- [ ] Play button plays the *selected* row (single click selects,
      click Play).
- [ ] Double-click on a row still plays it (shortcut).
- [ ] Mic devices are NOT listed here — only in Options.
- [ ] Per-pattern source combo is present for each software pattern.
- [ ] Controller patterns disable the source combo (strip uses its own
      USB mic).
- [ ] Brightness respects the Options clamp.

### Emergency stop

- [ ] Press Esc during a sweep — it stops.
- [ ] Press Esc during a music pattern — it stops.
- [ ] Press Esc during a hidden lab run — it stops.
- [ ] Control menu → "Stop all activity" does the same.

### Session log

- [ ] `%LOCALAPPDATA%\AymashTain\logs\` has a fresh `session_*.log`,
      `*.json`, `*.csv` from this run.
- [ ] Closing the app writes the `.json` file.
- [ ] Nothing overwrote an older session log.

---

## C. Round 3 - rearranged by file-touch order

The order below groups tasks by the file they touch, so each file is
opened once. Do them top to bottom.

### Phase 0 - small fix before Phase 1

- [ ] **`main_window.py`** - wire `sync_clamp_notice()` so the Remote,
      Sweep and Console tabs refresh their clamp notice when the Options
      brightness range changes. Three-line patch.

### Phase 1 - Camera batch (touch `camera_tab.py` + `config.py` once)

- [ ] Visual ROI picker — click-drag a rectangle on the preview.
- [ ] Live rectangle overlay drawn from the ROI (already partly there).
- [ ] Save ROI to `config.json` on change.
- [ ] "Calibrate" button — average 30 frames of a static colour, store
      the baseline.
- [ ] Re-test the camera with the new ROI before moving on.

### Phase 2 - Small UI wins (touch `main_window.py` once)

- [ ] Full About dialog with `CREDITS.md` content and GitHub link
      (currently a plain text box).
- [ ] Icon check: confirm `assets\aymashtain.ico` is picked up by
      `paths.icon_file()`.
- [ ] Any remaining menu polish in dark mode.

### Phase 3 - Profile import / export (touch `db.py`, then `remote_tab.py`)

- [ ] Export a profile to a JSON file.
- [ ] Import a profile; handle name collisions (rename, skip, or
      overwrite).
- [ ] Round-trip test: export, delete, import, confirm buttons intact.

### Phase 4 - 150-LED preview (decide data source first)

- [ ] **Decide the data source before writing code.** The protocol sends
      one colour per frame — there is no per-LED data yet. Options:
      (a) load a captured animation file, (b) run a locally-simulated
      chase, (c) replay the Scroll macro frame-by-frame.
- [ ] Touch `strip_preview.py` (already supports `set_led_colors()`).
- [ ] Then touch whichever tab drives it (`remote_tab.py` or a new
      preview control in Options).

### Phase 5 - Music & Media (touch `music_tab.py` once)

Small fixes first, before the big feature:

- [ ] Confirm microphone path works on your PC (testing only).
- [ ] Confirm WASAPI loopback fallback works on your PC (testing only).
- [ ] Confirm "playing file" source works (testing only).
- [ ] Add duplicate-colour suppression.
- [ ] Add "ensure on" before starting a music pattern.

Then the big feature (its own session):

- [ ] Retro Winamp-style visualizer.
- [ ] Video file playback.
- [ ] MPC + K-Lite integration.

### Phase 6 - Final test sweep

- [ ] Run the hidden lab on **one** strip only first, then all three.
- [ ] Confirm no Scroll / M1 corruption after a lab session.
- [ ] Confirm the far strip stays connected with
      `inter_device_delay_ms = 60`.
- [ ] Smoke test every tab in both themes one more time.

### Phase 7 - Packaging (always last)

- [ ] Rebuild the EXE from the package.
- [ ] Test on a clean Windows machine.
- [ ] Publish the GitHub release with the EXE + `_internal` folder.
- [ ] Verify the downloaded ZIP runs.

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

---

## E. Compile pass command block

Paste this whole block into PowerShell from the project root. No output
on any line = all clean.

```powershell
python -m py_compile .\main.py
python -m py_compile .\aymashtain\app.py
python -m py_compile .\aymashtain\config.py
python -m py_compile .\aymashtain\events.py
python -m py_compile .\aymashtain\paths.py
python -m py_compile .\aymashtain\ble\manager.py
python -m py_compile .\aymashtain\protocol\mrstar.py
python -m py_compile .\aymashtain\storage\db.py
python -m py_compile .\aymashtain\vision\camera.py
python -m py_compile .\aymashtain\audio\engine.py
python -m py_compile .\aymashtain\ui\context.py
python -m py_compile .\aymashtain\ui\theme.py
python -m py_compile .\aymashtain\ui\main_window.py
python -m py_compile .\aymashtain\ui\widgets\color_wheel.py
python -m py_compile .\aymashtain\ui\widgets\strip_preview.py
python -m py_compile .\aymashtain\ui\tabs\__init__.py
python -m py_compile .\aymashtain\ui\tabs\connect_tab.py
python -m py_compile .\aymashtain\ui\tabs\remote_tab.py
python -m py_compile .\aymashtain\ui\tabs\music_tab.py
python -m py_compile .\aymashtain\ui\tabs\sweep_tab.py
python -m py_compile .\aymashtain\ui\tabs\camera_tab.py
python -m py_compile .\aymashtain\ui\tabs\console_tab.py
python -m py_compile .\aymashtain\ui\tabs\lab_tab.py
python -m py_compile .\aymashtain\ui\tabs\events_tab.py
python -m py_compile .\aymashtain\ui\tabs\options_tab.py