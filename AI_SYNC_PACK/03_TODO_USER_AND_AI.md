<!-- BEGIN FILE: AI_SYNC_PACK/03_TODO_USER_AND_AI.md -->

# TODO - User and AI

Easy-to-read list of what is done and what is left.

**Version:** v0.61 Alpha
**Last updated:** 2026-09-22 (after Session 12 — Round 3 batch delivered, **app does not launch, cause unknown**)

---

## A0. P0 — BLOCKING: Fix the launch failure from Session 12

**The app does not start after the Session 12 batch. No error text, no
traceback, no log file was shared. This is undiagnosed and it blocks
everything else.**

Do this before any other task:

- [ ] **[P0] Collect the real failure output.** No guessing. Ask the
      user for:
  - [ ] `python .\main.py` in PowerShell from the project root —
        paste the **exact** error text.
  - [ ] `python -m py_compile` on each of these ten files, paste any
        output:
    - `.\aymashtain\config.py`
    - `.\aymashtain\ui\context.py`
    - `.\aymashtain\ui\theme.py`
    - `.\aymashtain\ui\main_window.py`
    - `.\aymashtain\ui\tabs\console_tab.py`
    - `.\aymashtain\ui\tabs\sweep_tab.py`
    - `.\aymashtain\ui\tabs\options_tab.py`
    - `.\aymashtain\ui\tabs\camera_tab.py`
    - `.\aymashtain\ui\tabs\music_tab.py`
    - `.\aymashtain\ui\tabs\remote_tab.py`
  - [ ] `python -m pytest -q` — paste the result.
  - [ ] The newest `session_*.log` and `session_*.json` from
        `%LOCALAPPDATA%\AymashTain\logs\`.

- [ ] **[P0] Fix the launch failure**, one file at a time, full
      replacements only.
- [ ] **[P0] Re-run** `py_compile` + `pytest` after every file.
- [ ] **[P0] Do not start any new feature work** until the app launches
      again and the Round 3 verification checklist below is done.

### Suspicion candidates to check first (do not act on these without evidence)

These are things that changed in Session 12 that could plausibly break
the launch. **Check the error text before acting on any of them**:

1. `main_window.py` — new `StripSelectorBar` class is defined in the
   same file. The `_tick()` method calls `self.strip_bar.refresh()`
   every 400 ms. If `refresh()` throws on first build, the app dies
   silently.
2. `main_window.py` — `_on_brightness_limits_changed` calls
   `sync_clamp_notice()` on `self.tab_music` as well as Remote / Sweep
   / Console. `MusicTab.sync_clamp_notice()` exists now — verify.
3. `main_window.py` — About dialog uses
   `dialog.layout().addWidget(...)` on a `QMessageBox` layout, which is
   unusual. If the layout is `None` at that point the app crashes on
   first About open — but that is not a launch failure.
4. `context.py` — new `selected_strips: list[str] = field(default_factory=list)`
   on a dataclass. `AppContext(...)` is constructed positionally in
   `app.py` with four arguments, so the default keeps working. Verify.
5. `remote_tab.py` — `StripPreviewRow` calls `StripPreview()` with no
   args. `StripPreview.__init__(self, leds=30)` — fine.
6. `options_tab.py` — `brightness_limits_changed = Signal(int, int)`
   added to a `QWidget` subclass. If the class is not a `QObject`
   descendant this raises at import time. `QWidget` is fine, but check
   the import line was not disturbed.

Again: **get the error first**, then look at this list.

---

## A1. P0 — Round 3 verification checklist (after the app launches again)

Nothing below can be marked done until the app launches. Once it does,
walk this list one item at a time and report the result of each:

- [ ] **Console clamp — short form.** Options max = 60%. Paste
      `BC0506040000000055` in Console. Expected: orange
      `clamp: … → … (100% -> 60%)` preview in "Decode only", and
      `→ clamped to …` line on send. Strip stops at 60%.
- [ ] **Console clamp — long form.** Same, with
      `BC050604000000000055`. Same expected result.
- [ ] **Console info label refresh.** Change the Options range while the
      Console tab is visible. Expected: label under the editor updates
      to the new range immediately.
- [ ] **Sweep mid-run range change.** Start a brightness sweep. Slide
      the Options max while it runs. Expected: Events tab shows
      `Brightness range now X%-Y%` each time it changes; steps follow
      the new range.
- [ ] **Remote clamp notice refresh.** Change Options range. Expected:
      Remote brightness slider notice updates to `Clamped to X%-Y%`.
- [ ] **Music clamp notice refresh.** Same on the Music & Media tab.
- [ ] **Multi-strip selector.** Tick one strip in the bar under the menu
      bar. Expected: every tab sends only to that strip. Tick "All
      strips" again — back to broadcast.
- [ ] **Light modes section.** Remote tab → click any category header
      (e.g. "Basic"). Expected: buttons expand below. Click "Colourful
      jumps". Expected: a `BC060204000055` frame goes out.
- [ ] **Camera backend switch.** Options → Capture backend →
      DirectShow. Reopen the Camera tab. Expected: no more fake
      "locked" — either a real value or "driver refused".
- [ ] **Music stop sends stable colour.** Start Spectrum, let it run,
      press Esc. Expected: strip snaps back to the Remote tab's current
      static colour, not the last audio frame.
- [ ] **Dark + light theme still readable** on every tab.

---

## A. Done (Sessions 1-11)

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
- [x] App confirmed running: 3/3 strips connect, 54 frames sent, 0 failed.
- [x] PyInstaller spec, `build_exe.bat`, `run.bat`, `repair.ps1`.
- [x] `CREDITS.md` added.
- [x] `.gitignore` cleaned.
- [x] GitHub sync working.

### Round 2 — Sessions 5-9

- [x] `__init__.py` — version bumped to `0.61.0` + `APP_DISPLAY_VERSION`.
- [x] `config.py` — `theme_mode`, dev lock, brightness clamp, camera /
      audio slots, window memory, per-pattern sources.
- [x] `options_tab.py` — **NEW FILE**.
- [x] `tabs/__init__.py` — exports `OptionsTab`.
- [x] `main_window.py` — Options tab, View + Options menus, dev lock,
      Extract log, min window 300x300, window memory.
- [x] `camera_tab.py` — border states, resolution / FPS dropdowns, real
      exposure + WB lock attempt, honest driver report.
- [x] `strip_preview.py` — neon capsules, per-LED glow, grey backing.
- [x] `music_tab.py` — mic selection moved out, per-pattern source,
      **Play button fixed**, brightness clamp, neon preview.
- [x] `remote_tab.py` — brightness clamp, live per-LED preview, colour
      swatch icons.
- [x] `events_tab.py` — user-facing "Export log..." only.
- [x] `theme.py` — dark-mode softened, menu audit, light parity.
- [x] `sweep_tab.py` — brightness sweep within Options range, info line,
      `sync_clamp_notice()` hook.
- [x] `console_tab.py` — brightness frame clamp, "Decode only" preview.
- [x] `tabs/__init__.py` — `OptionsTab` export was missing, added.
- [x] `music_tab.py` — `_stop_reacting()` alias added.
- [x] `aymashtain/__init__.py` — restored after import-collision incident.
- [x] Full compile pass clean.
- [x] `python -m pytest -q` -> **27 passed**.
- [x] All Round 2 code edits complete.
- [x] Sync pack updated for first live test run.

### Live test run — 2026-09-21

**Passed** (from Section B walkthrough)

- [x] App launches with `python .\main.py` or `run.bat`.
- [x] 9 tabs visible when Developer Tools is ON.
- [x] 8 tabs visible when Developer Tools is OFF (Lab hidden).
- [x] Version string shows `v0.61 Alpha` in title bar and About box.
- [x] Remote preset buttons render with small coloured square icons.
- [x] Dragging the brightness slider updates the neon preview *live*.
- [x] Releasing the slider sends exactly one `BC0506` frame.
- [x] Remote brightness clamp notice appears under the slider.
- [x] Sweep every step lands inside the Options range (no collapse).
- [x] Colour frame `BC0406000003E8000055` passes through Console untouched.
- [x] Events tab filter checkboxes work.
- [x] Events search box filters live.
- [x] "Export log..." opens a save dialog at the Options save location.
- [x] Save as `.csv` opens cleanly in Excel.
- [x] Save as `.json` is valid JSON.
- [x] After export, the status line just says "Log exported" — no path shown.
- [x] Dark mode — no harsh bright highlights.
- [x] Every menu opens and its selected item is readable.
- [x] Options — changing theme updates the app instantly.
- [x] Options — toggling Developer Tools hides/shows the Lab tab.
- [x] Options — brightness min/max sliders stay ordered.
- [x] Options — Save location Browse button works; Reset clears it.
- [x] Options — Camera device / resolution / FPS dropdowns reflect settings.
- [x] Options — Window "Remember screen, position, size" saves and restores.
- [x] Camera — preview border is light grey when closed, dark grey when open.
- [x] Music — Play button plays the selected row.
- [x] Music — double-click on a row still plays it.
- [x] Music — mic devices are NOT listed (only in Options).
- [x] Music — controller patterns disable the source combo.
- [x] Music — brightness respects the Options clamp.
- [x] Esc stops a sweep.
- [x] Esc stops a hidden lab run.
- [x] Control menu -> "Stop all activity" works.
- [x] Session log `session_*.log` / `*.json` / `*.csv` created fresh.
- [x] Closing the app writes the `.json` file.
- [x] Nothing overwrote an older session log.

### Hand-off tooling — Sessions 10-11

- [x] `make_handoff.py` rewritten with explicit allowlist of 27 source
      files; docs merged into 3 files; 5 sub-package `__init__.py` files
      merged into `_package_init_exports.md`; `--dry-run` flag added.
- [x] `make_handoff.bat` — `cd /d "%~dp0"`, python/py fallback, error
      pause, opens `handoff\`.
- [x] `AI_SYNC_PACK/08_End_Chat.md` — reusable end-of-chat ritual prompt.
- [x] Dry run: **32 files**, zero subfolders, under 35, no collisions.

### Session 12 — Round 3 batch (delivered, not verified)

Ten files were replaced and delivered but **no compile or runtime
output was shared.** They are listed here as "delivered" not "done",
because the app does not launch after applying them.

- [x] `aymashtain/ui/context.py` — `selected_strips`,
      `resolve_targets()`, `selected_strip_count()`, `is_strip_selected()`.
- [x] `aymashtain/ui/tabs/console_tab.py` — clamp parses both 18-char and
      20-char `BC0506` frames; orange preview in "Decode only"; sends via
      `resolve_targets()`.
- [x] `aymashtain/ui/tabs/sweep_tab.py` — fresh range read every step;
      logs mid-run changes; sends via `resolve_targets()`.
- [x] `aymashtain/ui/tabs/options_tab.py` — `brightness_limits_changed`
      signal; camera backend dropdown; longer capture-size list;
      "Capture size" rename.
- [x] `aymashtain/ui/main_window.py` — `StripSelectorBar`; "Options" menu
      renamed to "Settings"; `brightness_limits_changed` fanned out to
      `sync_clamp_notice()`; proper About dialog reading `CREDITS.md`.
- [x] `aymashtain/ui/tabs/camera_tab.py` — backend picker
      (auto/dshow/msmf); honest exposure + WB readback; theme-aware
      border colours.
- [x] `aymashtain/config.py` — `camera_backend` field with validation.
- [x] `aymashtain/ui/tabs/music_tab.py` — controller modes removed; Esc
      sends stable colour; `sync_clamp_notice()` hook added.
- [x] `aymashtain/ui/tabs/remote_tab.py` — Light-modes section (6
      collapsible categories); multi-strip preview rows; per-mode hex
      override via right-click. **Correction pass** added the missing
      `setProperty("sectionHeader", True)`.
- [x] `aymashtain/ui/theme.py` — `sectionHeader="true"` styles in both
      themes.

**These ten files are "delivered", not "verified".** Move them into
"Done" only after the launch failure is fixed and the Round 3
verification checklist (Section A1) passes end to end.

---

## B. Round 3 — remaining work

### Phase 0 — clamp-notice wiring (partly delivered in Session 12, unverified)

- [ ] `main_window.py` — `sync_clamp_notice()` fan-out. **Delivered in
      Session 12, not verified** (app does not launch).
- [ ] `console_tab.py` — clamp logic and orange preview. **Delivered in
      Session 12, not verified.**
- [ ] `sweep_tab.py` — fresh range read. **Delivered in Session 12, not
      verified.**
- [ ] Test all of the above once the app launches (see Section A1).

### Phase 1 — Camera batch (partly delivered in Session 12, unverified)

- [ ] `camera_tab.py` — resolution list, "Capture size" rename, honest
      exposure / WB readback, backend picker. **Delivered in Session 12,
      not verified.**
- [ ] Test once the app launches.
- [ ] `config.py` — save / load ROI once the visual picker is added.
- [ ] Visual ROI picker — click-drag a rectangle on the preview.
- [ ] Live rectangle overlay drawn from the ROI.
- [ ] "Calibrate" button — average 30 frames of a static colour, store
      the baseline.
- [ ] Re-test the camera with the new ROI before moving on.

### Phase 2 — Light theme fix (partly delivered in Session 12, unverified)

- [ ] `camera_tab.py` — light mode camera borders. **Delivered in
      Session 12, not verified.**
- [ ] `theme.py` — light theme parity for the new section headers.
      **Delivered in Session 12, not verified.**
- [ ] Test once the app launches.

### Phase 3 — Music tab cleanup (partly delivered in Session 12, unverified)

- [ ] `music_tab.py` — split patterns into music-only (Spectrum, Pulse).
      Controller modes moved to Remote → Light modes. **Delivered in
      Session 12, not verified.**
- [ ] `music_tab.py` — Esc during a pattern sends a stable neutral
      colour. **Delivered in Session 12, not verified.**
- [ ] Test once the app launches.

### Phase 4 — Small UI wins

- [x] Full About dialog with `CREDITS.md` content and GitHub link.
      **Delivered in Session 12, not verified.**
- [ ] Icon check: confirm `assets\aymashtain.ico` is picked up by
      `paths.icon_file()`.
- [ ] Any remaining menu polish in dark mode.

### Phase 5 — Profile import / export

- [ ] `db.py` — export a profile to a JSON file.
- [ ] `db.py` — import a profile; handle name collisions (rename,
      skip, or overwrite).
- [ ] `remote_tab.py` — wire the UI for import / export.
- [ ] Round-trip test: export, delete, import, confirm buttons intact.

### Phase 6 — 150-LED preview

- [ ] **Decide the data source before writing code.** The protocol sends
      one colour per frame — there is no per-LED data yet. Options:
      (a) load a captured animation file, (b) run a locally-simulated
      chase, (c) replay the Scroll macro frame-by-frame.
- [ ] Touch `strip_preview.py` (already supports `set_led_colors()`).
- [ ] Then touch whichever tab drives it.

### Phase 7 — Music & Media big feature

- [ ] Retro Winamp-style visualizer.
- [ ] Video file playback.
- [ ] MPC + K-Lite integration.

### Phase 8 — Final test sweep

- [ ] Run the hidden lab on **one** strip only first, then all three.
- [ ] Confirm no Scroll / M1 corruption after a lab session.
- [ ] Confirm the far strip stays connected with
      `inter_device_delay_ms = 60`.
- [ ] Smoke test every tab in both themes one more time.

### Phase 9 — Packaging (always last)

- [ ] Rebuild the EXE from the package.
- [ ] Test on a clean Windows machine.
- [ ] Publish the GitHub release with the EXE + `_internal` folder.
- [ ] Verify the downloaded ZIP runs.

---

## C. Housekeeping — optional

- [ ] Delete leftover junk from the project root: `test.txt`,
      `events.csv`, `events.json`, `build\`.
- [ ] Decide whether to keep `AI_CONTEXT.md`, `AI_NOTES.md`,
      `AI_SESSIONS.md`, `AI_BRIEF.md`, `AI_BACKLOG.md`, `PROJECT.md`,
      `ai_sync.py`.
- [ ] Move `aymashtain.ico` into a new `assets\` folder (or update
      `paths.py` to look in the project root).
- [ ] Consider persisting `ctx.selected_strips` in `Settings` so the
      user's strip selection survives an app restart (intentional
      Session 12 gap).

---

## D. Compile pass command block

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
```

<!-- END FILE: AI_SYNC_PACK/03_TODO_USER_AND_AI.md -->