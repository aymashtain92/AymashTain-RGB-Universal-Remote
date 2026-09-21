# TODO - User and AI

Easy-to-read list of what is done and what is left.

**Version:** v0.61 Alpha
**Last updated:** 2026-09-21 (after first live test run)

---

## A0. P0 - Active / Immediate

- [ ] **[P0] Flat handoff bundle**
  - Rewrite `make_handoff.py` so the ZIP it produces is:
    - **One folder, zero subdirectories** (all files at the root of the ZIP).
    - **No duplicate filenames** — nested paths become `folder__file.py`
      (e.g. `aymashtain__ui__tabs__remote_tab.py`).
    - **Every text file starts with a `# Original Path: <real/path>` header**
      so any AI knows where it belongs.
    - **Docs merged into 3 files:**
      - `00_PROJECT_MASTER_DOCS.md` (00_MASTER_SUMMARY + 02_UNIVERSAL_AI_PROMPT + 05_DEVELOPER_README + 07_HOW_TO_USE_AI_SYNC)
      - `01_WORKFLOW_AND_TODO.md` (01_WORKFLOW + 03_TODO + 04_AI_ERRORS_ONLY)
      - `02_CURRENT_CHAT.md` (06_CURRENT_CHAT)
    - **Total file count well under 50** (DeepSeek's upload cap).
    - Still numbered per run: `handoff_001.zip`, `handoff_002.zip`, etc.
  - **Test:** run `make_handoff.bat`, unzip, confirm flat folder, count files, confirm < 50.

---

## A. Done (Sessions 1-9)

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

### Round 2 - Session 5

- [x] `__init__.py` - version bumped to `0.61.0` + `APP_DISPLAY_VERSION`.
- [x] `config.py` - `theme_mode`, dev lock, brightness clamp, camera /
      audio slots, window memory, per-pattern sources.
- [x] `options_tab.py` - **NEW FILE**.
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

### Round 2 - Session 7

- [x] `events_tab.py` - user-facing "Export log..." only. Log path never
      shown to the end user.
- [x] `theme.py` - dark-mode highlights softened. Menu audit done. Light
      theme brought to parity with dark in the stylesheet itself.
- [x] `remote_tab.py` - preset buttons carry colour as a small icon
      (`_color_swatch()`); inline `border-left` stylesheet removed;
      remaining unicode chars swapped for ASCII.
- [x] `sweep_tab.py` - brightness sweep runs *within* the Options min/max
      range. New info line. `sync_clamp_notice()` public hook added.
- [x] `console_tab.py` - `BC0506` frames clamped against Options min/max
      before queueing. "Decode only" preview. New info label +
      `sync_clamp_notice()` hook.
- [x] Sync pack cleanup - `00`, `01`, `03` re-saved clean as UTF-8.

### Round 2 - Session 8

- [x] `tabs/__init__.py` - `OptionsTab` export was missing, added.
- [x] `music_tab.py` - `_stop_reacting()` alias added for emergency stop.
- [x] `aymashtain/__init__.py` - restored after import-collision incident.
- [x] Full compile pass clean.
- [x] `python -m pytest -q` -> **27 passed**.

### Round 2 - Session 9

- [x] All Round 2 code edits complete.
- [x] Sync pack updated for first live test run.
- [x] Hand-off bundle prepared.

### Live test run - 2026-09-21

Results from first full launch and Section B walkthrough:

**Passed**

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
- [x] Dark mode - no harsh bright highlights.
- [x] Every menu opens and its selected item is readable.
- [x] Options - changing theme updates the app instantly.
- [x] Options - toggling Developer Tools hides/shows the Lab tab.
- [x] Options - brightness min/max sliders stay ordered.
- [x] Options - Save location Browse button works; Reset clears it.
- [x] Options - Camera device / resolution / FPS dropdowns reflect settings.
- [x] Options - Window "Remember screen, position, size" saves and restores.
- [x] Camera - preview border is light grey when closed, dark grey when open.
- [x] Music - Play button plays the selected row.
- [x] Music - double-click on a row still plays it.
- [x] Music - mic devices are NOT listed (only in Options).
- [x] Music - controller patterns disable the source combo.
- [x] Music - brightness respects the Options clamp.
- [x] Esc stops a sweep.
- [x] Esc stops a hidden lab run.
- [x] Control menu -> "Stop all activity" works.
- [x] Session log `session_*.log` / `*.json` / `*.csv` created fresh.
- [x] Closing the app writes the `.json` file.
- [x] Nothing overwrote an older session log.

**Failed / broken - to fix in Round 3**

- [ ] **Console clamp does not fire.** Pasting `BC0506040000000055` with
      Options max at 60% sent the frame *as-is* and forced brightness to
      max. Expected: clamp + `original -> clamped` output line.
- [ ] **Console info label for the clamp range never updates** when the
      Options range changes. It keeps showing the range from when the tab
      was first built.
- [ ] **Console "Decode only" doesn't show the orange clamp preview line.**
      Only prints `[ 1] BC0506040000000055 — mrstar_brightness: Brightness
      (unconfirmed)`.
- [ ] **Sweep mid-run Options range change has no effect.** The new range
      only takes hold after re-sliding the Remote tab. Sweep must read
      `settings.brightness_min` / `brightness_max` on every step (it
      already should — verify).
- [ ] **Light theme camera tab borders still wrong.** Border colours in
      light mode don't change between open / closed as expected.
- [ ] **Remote / Sweep / Console clamp notices don't refresh** when the
      Options range changes (this is Phase 0 below).
- [ ] **Camera resolution list too short.** User's max is 2560x1440
      (video 1440p60, photo 3.7 MP). Need more entries and a note that
      this is *capture size*, not sensor resolution.
- [ ] **Camera FPS dropdown doesn't visibly change the frame rate**
      (laggy at 60).
- [ ] **Camera exposure lock reports `1/2 s` and stays locked at that
      value.** Real exposure is not being forced. Status line is honest
      only if the value shown is correct — it isn't.
- [ ] **Camera WB lock does nothing.** Status line says "wb=locked
      (gains frozen)" but the picture behaves as if it isn't.
- [ ] **Music tab - the 4 controller modes are mixed with the music
      sources.** Correct grouping: 5 music sources (1 any-mic + 4 with
      built-in mic), separate from software-pattern sources.
- [ ] **Music - pressing Esc during a pattern stops it but leaves the
      strip in whatever colour the last frame was.** Should flip to a
      stable / neutral colour on stop.
- [ ] **Music - per-pattern source combos show the wrong list.** User
      will provide screenshots showing which is music and which is light
      mode.
- [ ] **Brightness "issue not fixed"** (user's note on the Remote clamp
      test) — even though the frame is clamped, the strip itself still
      goes too bright on some paths. Needs investigation.

---

## B. Now - Round 3 immediate fixes

Ordered by file-touch so each file is opened once.

### Phase 0 - clamp-notice wiring (small, unblocks the rest)

- [ ] **`main_window.py`** - call `sync_clamp_notice()` on Remote, Sweep
      and Console when the Options brightness range changes.
- [ ] **`console_tab.py`** - fix:
  1. Clamp logic must actually rewrite the frame before sending.
  2. Info label must refresh when Options range changes.
  3. "Decode only" must show the orange clamp preview line.
- [ ] **`sweep_tab.py`** - confirm range is read *fresh on every step*,
      not cached at start. If cached, fix.
- [ ] Test: set Options max to 60%, paste `BC0506040000000055` in
      Console, click Decode only, click Send all. Expected: orange
      preview + `original -> clamped` + strip stops at 60%.

### Phase 1 - Camera batch

- [ ] **`camera_tab.py`** - resolution list: add user's real max
      (2560x1440), rename the label from "Resolution" to "Capture size",
      add more entries.
- [ ] **`camera_tab.py`** - FPS: verify the value actually changes the
      capture rate. If not, try a different OpenCV backend
      (`CAP_DSHOW` vs `CAP_MSMF`).
- [ ] **`camera_tab.py`** - exposure lock: the reported `1/2 s` is wrong.
      Log the actual `CAP_PROP_EXPOSURE` readback and show the real
      value. If the driver refused the lock, say so — do not print
      "locked" when it isn't.
- [ ] **`camera_tab.py`** - WB lock: same. Report honestly.
- [ ] **`config.py`** - save / load ROI (region of interest) once the
      visual picker is added.
- [ ] Visual ROI picker - click-drag a rectangle on the preview.
- [ ] Live rectangle overlay drawn from the ROI.
- [ ] "Calibrate" button - average 30 frames of a static colour, store
      the baseline.
- [ ] Re-test the camera with the new ROI before moving on.

### Phase 2 - Light theme fix

- [ ] **`theme.py`** / **`camera_tab.py`** - light mode camera tab
      borders must reflect open / closed state the same way dark mode
      does. Currently wrong.

### Phase 3 - Music tab cleanup

- [ ] **`music_tab.py`** - split the pattern list correctly:
  - 5 music sources (1 any-mic + 4 with built-in mic).
  - Separate section for software-pattern sources.
- [ ] **`music_tab.py`** - per-pattern source combo: fix which list is
      shown for which pattern (user will supply screenshots).
- [ ] **`music_tab.py`** - pressing Esc during a pattern should also
      send a stable neutral colour, not leave the strip on the last
      frame.
- [ ] Re-test the whole tab after these fixes.

### Phase 4 - Small UI wins

- [ ] Full About dialog with `CREDITS.md` content and GitHub link
      (currently a plain text box).
- [ ] Icon check: confirm `assets\aymashtain.ico` is picked up by
      `paths.icon_file()`.
- [ ] Any remaining menu polish in dark mode.

### Phase 5 - Profile import / export

- [ ] **`db.py`** - export a profile to a JSON file.
- [ ] **`db.py`** - import a profile; handle name collisions (rename,
      skip, or overwrite).
- [ ] **`remote_tab.py`** - wire the UI for import / export.
- [ ] Round-trip test: export, delete, import, confirm buttons intact.

### Phase 6 - 150-LED preview

- [ ] **Decide the data source before writing code.** The protocol sends
      one colour per frame — there is no per-LED data yet. Options:
      (a) load a captured animation file, (b) run a locally-simulated
      chase, (c) replay the Scroll macro frame-by-frame.
- [ ] Touch `strip_preview.py` (already supports `set_led_colors()`).
- [ ] Then touch whichever tab drives it (`remote_tab.py` or a new
      preview control in Options).

### Phase 7 - Music & Media big feature

- [ ] Retro Winamp-style visualizer.
- [ ] Video file playback.
- [ ] MPC + K-Lite integration.

### Phase 8 - Final test sweep

- [ ] Run the hidden lab on **one** strip only first, then all three.
- [ ] Confirm no Scroll / M1 corruption after a lab session.
- [ ] Confirm the far strip stays connected with
      `inter_device_delay_ms = 60`.
- [ ] Smoke test every tab in both themes one more time.

### Phase 9 - Packaging (always last)

- [ ] Rebuild the EXE from the package.
- [ ] Test on a clean Windows machine.
- [ ] Publish the GitHub release with the EXE + `_internal` folder.
- [ ] Verify the downloaded ZIP runs.

---

## C. Housekeeping - optional

- [ ] Delete leftover junk from the project root: `test.txt`,
      `events.csv`, `events.json`, `build\`. The hand-off tool ignores
      them, but they add clutter.
- [ ] Decide whether to keep `AI_CONTEXT.md`, `AI_NOTES.md`,
      `AI_SESSIONS.md`, `AI_BRIEF.md`, `AI_BACKLOG.md`, `PROJECT.md`,
      `ai_sync.py`. They currently stay and ship in the bundle as a
      bonus.
- [ ] Move `aymashtain.ico` into a new `assets\` folder (or update
      `paths.py` to look in the project root).

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