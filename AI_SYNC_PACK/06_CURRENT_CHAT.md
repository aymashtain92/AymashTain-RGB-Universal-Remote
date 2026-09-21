<!-- BEGIN FILE: AI_SYNC_PACK/06_CURRENT_CHAT.md -->

# Current Chat Summary — 2026-09-22

This file records the conversation history between the user and the AI.
Update it after every session.

---

## Session 1 — Sync pack correction

### User request

- Confirm which project folder is the real one.
- Rewrite `00`–`06` of the `AI_SYNC_PACK` to match the real project.

### Decision made

Real project folder:

```text
D:\Coding projects\aymashtain-led-remote-Source
```

This is a **package** project (Devin AI rewrite), not the flat `main.py`
version.

### What this chat did

- Confirmed from screenshots that the package app runs.
- Confirmed 3/3 strips connect, 54 frames sent, 0 failed.
- Rewrote `00`–`06` for the package structure.

---

## Session 2 — Hidden-feature laboratory

### User request

- Add a hidden-feature laboratory to the app.

### What this chat did

- Replaced `aymashtain/ui/tabs/lab_tab.py` with a version that adds:
  - Template generator (`XX` sweep)
  - Candidate list (one hex per line)
  - Delay / hold / capture-camera controls
  - Start sweep / Test first candidate only / Emergency stop
  - Export CSV / Export JSON
  - Results table with editable notes
- Replaced `aymashtain/ui/main_window.py` with:
  - `camera_tab=self.tab_camera` passed to `LabTab`
  - `stop_all_activity()` method
  - Esc + Ctrl+. emergency stop
  - `_disconnect_with_timeout()` safer close
  - `import asyncio`, `import time`, `QEventLoop`, `QKeySequence` added
- Compiled both files cleanly.

---

## Session 3 — Test round

### What was tested

- Compile: silent, pass.
- App launches, 8 tabs present.
- 3/3 strips connected.
- Colour + brightness send correctly.
- Sweep tab works, results table fills, camera sampling works.
- Console good.
- Events tab good.
- Lab tab present and functional.

### What was found broken or rough

- Dark mode highlights too bright.
- Remote tab "white" colour renders wrong.
- Some menus broken in dark mode (not all).
- Light mode: Camera tab borders not indicating open/closed state.
- Music tab: Play button doesn't play a highlighted song (must double-click).
- Camera: Nuroum V11 still uses auto-exposure. No forced lock.
- LED strip preview in Remote and Music: just boxes filling with colour.
  Needs neon-strip look with individual capsules and glow.
- Hidden-feature lab too complicated for now.
- App does not scroll when window is small. No minimum size.
- Max brightness issue still not resolved.
- Macros/Modes naming confusing.
- Music tab mixes mic selection with pattern selection.
- Media player weak. User wants retro visualizer (Winamp-style) later.
- Logs and dev tabs exposed to end users. Must be lockable.
- Version string `1.0.0` disagrees with release `v0.51 Alpha`.

---

## Session 4 — Round 2 spec (v0.61 Alpha)

### Decision

- Next version: **v0.61 Alpha**.
- The full Round 2 Feature Spec was written for a new chat session.
- The user will run the next update round in a fresh chat, using the
  `AI_SYNC_PACK` and the spec, to test whether the auto-update method works.

### Round 2 spec covers

1. New **Options** tab (save location, theme, developer toggle, language
   stub, brightness min/max, audio devices, camera device/resolution/FPS/
   exposure lock/WB lock, window geometry memory).
2. View menu additions (dark mode, developer toggle, extract log, options).
3. Developer tabs lock (Lab hidden unless Developer Tools = ON).
4. Camera tab: open/closed border states; resolution, FPS, exposure lock,
   WB lock; live LED indicator in Remote tab.
5. LED / neon strip preview redesign (capsules + glow, grey background,
   per-LED colour).
6. Scrolling everywhere; minimum window size ~300x300.
7. Music tab cleanup: mic selection moves to Options; per-pattern source
   assignment.
8. Media player upgrade (later): retro Winamp-style visualizer, video
   playback, MPC + K-Lite support.
9. Logs: user-facing export only; auto-save on close.
10. Max brightness: internal clamp controlled from Options.
11. Icon: user re-adds manually.
12. Play button fix.
13. Dark mode softening + menu audit.
14. Version -> v0.61 Alpha.

### Priority order

1. Options tab.
2. View menu + developer lock.
3. Dark mode + menu fixes.
4. Camera exposure lock + resolution / FPS.
5. LED strip preview redesign.
6. Scrolling + min window size.
7. Music tab cleanup.
8. Max brightness option.
9. Play button fix.
10. Remember monitor / scale / position.
11. Media player + retro visualizer (later).
12. Version -> v0.61 Alpha.

---

## Session 5 — Round 2 implementation (v0.61 Alpha)

**Date:** 2026-09-21
**AI name:** DeepSeek
**Version target:** v0.61 Alpha

### User request

Implement the Round 2 Feature Spec, one file at a time, full replacements
only.

### Files replaced in this session

1. `aymashtain/__init__.py` — version bumped to `0.61.0`, added
   `APP_DISPLAY_VERSION = "v0.61 Alpha"`.
2. `aymashtain/config.py` — full rewrite. Added `theme_mode`
   (light/dark/system), `developer_tools` lock, `save_location`,
   `brightness_min`/`brightness_max` + `clamp_brightness()`, audio device
   slots, camera slots, window memory, per-pattern mic sources, language
   stub. Backwards-compatible load: old `dark_theme` migrates into
   `theme_mode`.
3. `aymashtain/ui/tabs/options_tab.py` — **NEW FILE**. Full Options tab
   with General / Appearance / Developer / Brightness limits / Audio
   devices / Camera / Window sections.
4. `aymashtain/ui/tabs/__init__.py` — now exports `OptionsTab`.
5. `aymashtain/ui/main_window.py` — full rewrite. Options tab added as
   last tab. New top-level **Options** menu. View menu now has: Dark mode,
   Developer tools, Extract log, Options. Developer lock hides Lab tab via
   `setTabVisible`. Min window 300x300. Window memory. Extract log bundles
   logs + config + `system_info.txt` into a zip.
6. `aymashtain/ui/tabs/camera_tab.py` — full rewrite. Border states,
   resolution + FPS dropdowns, forced exposure lock, WB lock, honest
   driver report.
7. `aymashtain/ui/widgets/strip_preview.py` — full rewrite. Grey backing,
   neon capsules, per-LED glow, `set_led_colors()`, `set_color()`
   backwards compatible, `set_leds(count)` for 150-LED view.
8. `aymashtain/ui/tabs/music_tab.py` — full rewrite. Mic selection moved
   out, per-pattern source combo, controller vs software pattern split,
   **Play button fixed**, brightness clamp, neon preview.

### What was compiled

User confirmed `__init__.py` and `config.py` compile cleanly.

### What still needs compiling and testing

- `options_tab.py`
- `tabs/__init__.py`
- `main_window.py`
- `camera_tab.py`
- `strip_preview.py`
- `music_tab.py`

### Honest notes on what's best-guess

- Controller music pattern uses `BC 06 02 0B MM 00 55` with `MM` = mode
  1..4. Best guess — verify with Lab tab on real hardware.
- Camera exposure lock reports what the driver accepted. If the Nuroum V11
  still wins on auto, the status line will say so; the code does not
  pretend.

---

## Session 6 — Hand-off tooling + `remote_tab.py` (v0.61 Alpha)

**Date:** 2026-09-21
**AI name:** DeepSeek
**Version target:** v0.61 Alpha

### User request

- Add a one-click tool that bundles the whole project into a numbered zip
  so the next hand-off is "double-click, unzip, drop into a new chat".
- Drop exported `events.csv` / `events.json` from the bundle (junk logs).
- Align `AI_SYNC_PACK/00-07` with the new hand-off workflow.

### Files created / replaced in this session

1. **NEW `make_handoff.py`** — one-click bundle builder. Creates
   `handoff/handoff_NNN_YYYYMMDD_HHMMSS.zip`. Includes the source tree,
   `AI_SYNC_PACK/`, and optional `AI_*` context files.
2. **NEW `make_handoff.bat`** — double-click wrapper.
3. `AI_SYNC_PACK/07_HOW_TO_USE_AI_SYNC.md` — full rewrite for one-click
   flow.
4. `AI_SYNC_PACK/00_MASTER_SUMMARY.md` — v0.61, new structure, hand-off
   section.
5. `AI_SYNC_PACK/05_DEVELOPER_README.md` — same updates.
6. `AI_SYNC_PACK/06_CURRENT_CHAT.md` — Session 6 appended.
7. `aymashtain/ui/tabs/remote_tab.py` — brightness clamp via
   `settings.clamp_brightness()`; live per-LED preview update on slider
   drag; `sync_clamp_notice()` helper.

---

## Session 7 — Remaining Round 2 UI polish (v0.61 Alpha)

**Date:** 2026-09-21
**AI name:** DeepSeek
**Version target:** v0.61 Alpha

### User request

- Finish the remaining Round 2 items: Events tab export, theme softening,
  sweep clamp, console clamp.

### Files replaced in this session

1. `aymashtain/ui/tabs/events_tab.py` — user-facing "Export log..." only.
   Log path is never shown to the end user. Format picked by file dialog
   extension. Default filename uses the Options save location.
2. `aymashtain/ui/theme.py` — dark-mode highlights softened (indigo-800
   tabs, indigo-700 accent buttons, zinc-300 slider handle). Menu audit:
   `pressed`, `disabled`, `separator`, `indicator` rules added to both
   themes. Light theme brought to parity with dark.
3. `aymashtain/ui/tabs/remote_tab.py` — preset buttons now carry colour as
   a small icon (`_color_swatch()`) instead of an inline `border-left`
   stylesheet. Remaining unicode chars swapped for ASCII.
4. `aymashtain/ui/tabs/sweep_tab.py` — brightness sweep now runs *within*
   the Options min/max range. Reads `settings.brightness_min` /
   `brightness_max` fresh on every step. New info line. New
   `sync_clamp_notice()` public hook.
5. `aymashtain/ui/tabs/console_tab.py` — any `BC0506` brightness frame
   typed or pasted in is clamped against the Options min/max before it is
   queued. "Decode only" shows a preview. New info label +
   `sync_clamp_notice()` hook.
6. Sync pack cleanup — `00`, `01`, `03` re-saved clean as UTF-8.

---

## Session 8 — Compile pass + blocker fixes (v0.61 Alpha)

**Date:** 2026-09-21
**AI name:** DeepSeek
**Version target:** v0.61 Alpha

### User request

- Review every file replaced in Sessions 5–7 before the first test run.
- Fix anything that would crash the app on launch.
- Confirm every package `__init__.py` exports what its callers import.

### Blockers found and fixed

1. **`aymashtain/ui/tabs/__init__.py`** — `OptionsTab` was missing from
   the exports. `main_window.py` imports it, so the app crashed at launch
   with `ImportError: cannot import name 'OptionsTab'`. Fixed by adding
   `from .options_tab import OptionsTab  # noqa: F401`.
2. **`aymashtain/ui/tabs/music_tab.py`** — `_stop_reacting()` was missing.
   `main_window.stop_all_activity()` calls it, so pressing Esc or
   Control → Stop all activity raised `AttributeError`. Fixed by adding
   `_stop_reacting()` as a thin alias for `_stop_pattern()`.

### Compile pass

Every file passed `python -m py_compile` with no output.

### Still open

- Phase 0 in Section C of `03_TODO_USER_AND_AI.md`: wire
  `sync_clamp_notice()` so Remote / Sweep / Console refresh their clamp
  notice when the Options brightness range changes.

---

## Session 8 (continued) — Pytest discovery + top-level init fix

**Date:** 2026-09-21
**AI name:** DeepSeek
**Version target:** v0.61 Alpha

### What happened

Compile pass was clean, but `python -m pytest -q` failed during collection
with:

```text
ModuleNotFoundError: No module named 'aymashtain.camera_tab'
```

### Root cause

`aymashtain/__init__.py` (the top-level package init) had been
overwritten with the contents of `aymashtain/ui/tabs/__init__.py`. That
made every import of the `aymashtain` package try to pull in Qt tab
classes from the wrong path.

### Fix

`aymashtain/__init__.py` restored to its correct role: app identity
constants only. First line is a docstring, then `APP_NAME`, `APP_SLUG`,
`APP_VERSION = "0.61.0"`, `APP_DISPLAY_VERSION = "v0.61 Alpha"`. No
imports.

### Result

`python -m pytest -q` → **27 passed in 0.78s**.

### Lesson for future sessions

`py_compile` cannot catch a file whose contents are syntactically valid
but semantically wrong. Always run pytest after touching any
`__init__.py`.

---

## Session 9 — Handoff prep

**Date:** 2026-09-21
**AI name:** DeepSeek
**Version target:** v0.61 Alpha

### State at handoff

- All code edits for Round 2 are complete.
- Compile pass clean.
- Unit tests: 27 passed.
- App has NOT yet been launched for the first full test run.

### Next task in the new chat

1. Wait for user to paste the first test-run log.
2. Fix whatever breaks.
3. Then Phase 0 from Section C of `03_TODO_USER_AND_AI.md` (clamp-notice
   wiring across Remote / Sweep / Console).
4. Then Phase 1 (Camera ROI batch).

---

## Session 10 — Live test + sync pack cleanup + flat handoff (v0.61 Alpha)

**Date:** 2026-09-21
**AI name:** DeepSeek
**Version target:** v0.61 Alpha

### User request

- Walk Section B of `03_TODO_USER_AND_AI.md` against the live app and
  report every result.
- The sync pack markdown files had been damaged in a prior attempt
  (code fences never closed, headings lost, whole sections missing).
  Rewrite every file as a full clean replacement in UTF-8.
- Design a **flat hand-off bundle**: fewer files, zero subfolders inside
  the ZIP, no duplicate filenames, and `__init__.py` files renamed by
  parent folder so they can coexist in one folder.
- Add the flat-handoff task as the top P0 item in the TODO list.

### Live test results

**Passed**

- App launches. 9 tabs with Dev Tools ON, 8 with it OFF.
- Version string shows `v0.61 Alpha` in title and About.
- Remote tab: preset colour swatches, live preview on drag, single
  `BC0506` on release, clamp notice under slider.
- Sweep: steps stay inside Options range, no collapse.
- Colour frame `BC0406000003E8000055` passes Console untouched.
- Events: filters, live search, `.csv` / `.json` export, no path shown.
- Theme: dark mode readable, menus readable.
- Options: everything works including window memory restore.
- Music: Play button, double-click, mic split, controller combos
  disabled.
- Emergency stop: Esc + Control menu work on sweep, music, and lab.
- Session logs: fresh `.log` / `.json` / `.csv`, no overwrites.

**Failed**

- Console clamp silently passes `BC0506040000000055` through when
  Options max is 60%. Strip forced to max brightness.
- Console info label never updates when the Options range changes.
- Console "Decode only" doesn't show the orange clamp preview line.
- Sweep doesn't pick up mid-run Options range changes.
- Light-mode camera tab borders still wrong.
- Camera: resolution list too short, FPS dropdown no effect, exposure
  reports fake `1/2 s`, WB lock does nothing.
- Music: the 4 controller modes are mixed with the music source list;
  Esc during a pattern leaves the strip on the last frame.
- Remote clamp notice doesn't refresh when Options range changes.

### Sync pack corruption found and fixed this session

1. `00_MASTER_SUMMARY.md` — Section 3 code fence never closed; Sections
   4–8 lost their `## ` headings; protocol blocks lost their fences.
2. `01_WORKFLOW.md` — timeline stopped at Session 6; Sessions 7–9
   missing.
3. `02_UNIVERSAL_AI_PROMPT.md` — "read in this order" list still pointed
   at nested paths.
4. `03_TODO_USER_AND_AI.md` — Section A stopped at Session 6;
   Section B was still a pre-test checklist; no P0 flat-handoff task.
5. `04_AI_ERRORS_ONLY.md` — no rules for the live-test clamp failures;
   no rule for the Session 8 `__init__.py` incident.
6. `05_DEVELOPER_README.md` — Section 2 code fence never closed;
   Section 9 described the old nested workflow.
7. `06_CURRENT_CHAT.md` — Session 7 was missing.

### Flat handoff design

The rewritten `make_handoff.py` merges `AI_SYNC_PACK/00-07` into **3
files** (`00_PROJECT_MASTER_DOCS.md`, `01_WORKFLOW_AND_TODO.md`,
`02_CURRENT_CHAT.md`), flattens the source tree using `__` separators,
and injects `# Original Path:` headers.

---

## Session 11 — Flat handoff refinement + end-of-chat ritual (v0.61 Alpha)

**Date:** 2026-09-21
**AI name:** DeepSeek
**Version target:** v0.61 Alpha

### User request

- Refine `make_handoff.py` so the flat bundle stays **well under 35
  files** — the first version produced 83 files, too many for DeepSeek's
  50-file cap once the user attaches screenshots.
- Drop `.gitignore` and any other files AI chats don't accept.
- Create a reusable **`08_End_Chat.md`** — a prompt the user pastes at
  the end of any AI session to get the sync pack updated cleanly.
- Test the flat bundle with a **`--dry-run`** flag before building.

### Files created / replaced

1. **`make_handoff.py`** — rewritten with:
   - **Explicit allowlist** of 27 source files (no more
     "bundle everything and exclude").
   - **Docs merged into 3 files** (`00_PROJECT_MASTER_DOCS.md`,
     `01_WORKFLOW_AND_TODO.md`, `02_CURRENT_CHAT.md`).
   - **5 sub-package `__init__.py` files merged** into
     `_package_init_exports.md`.
   - **`--dry-run` flag** prints the full file list + count without
     creating a zip.
   - Excludes `.gitignore`, `pyproject.toml`, `requirements.txt`,
     `.spec`, `README.md`, `CREDITS.md`, `LICENSE.txt`, `tests/`,
     `assets/`, `AI_*` helper files, logs and DBs.
   - Target: **32 files**. Dry run confirmed.

2. **`make_handoff.bat`** — rewritten:
   - `cd /d "%~dp0"` sets working directory (fixes silent failure when
     double-clicked from another folder).
   - Prefers `python`, falls back to `py`.
   - Displays error code and pauses on failure.
   - Opens the `handoff\` folder when done.

3. **`AI_SYNC_PACK/08_End_Chat.md`** — **NEW FILE**. Reusable
   end-of-chat ritual prompt.

### What was compiled

- `make_handoff.py` — passed `python -m py_compile` clean.

### What still needs testing

- Real `make_handoff.bat` run (not `--dry-run`) — confirm the zip is
  created and looks right when unzipped.

### Dry-run result

```text
Total files: 32
Under 35-file target: YES
Under 50-file cap:    YES
Zero subdirectories:  YES
Collisions:           none
Read failures:        none
```

### Suggested next-chat opening line

> Continue from Session 11. The flat handoff works (32 files, zero
> subfolders, under 35). Round 3 Phase 0 next: fix the Console clamp bug
> in `console_tab.py`, then `sweep_tab.py` mid-run range read, then wire
> `sync_clamp_notice()` from `main_window.py`. Full replacement files
> only. Do not touch `ble/manager.py`, `protocol/mrstar.py`, or
> `storage/db.py` schema.

---

## Session 12 — Round 3 full batch (multi-strip, light modes, camera backend) — DELIVERED BUT APP NOT WORKING (v0.61 Alpha)

**Date:** 2026-09-22
**AI name:** DeepSeek
**Version target:** v0.61 Alpha

### User request

- Finish Round 3 in one chat, one file at a time, full replacements only.
- Deliver all five batches: Phase 0 clamp wiring, Phase 1 camera,
  Phase 2 light theme, Phase 3 music tab, and the Batch 5 About dialog.
- Add a **multi-strip selector** so the user can pick which strips
  receive commands from every tab. Default = "All connected".
- Move **Light modes** into the Remote tab as collapsible dropdowns,
  placed under colour + brightness, before the strip preview. Mirror
  the vendor app's "Light Mode" categories: Basic, Opening & closing,
  Transition, Running water, Tailing, Running.
- Keep the Music & Media tab for music only — remove the four
  "Controller mode" entries from it. They belong in Remote → Light modes.
- Add an **About dialog** that reads `CREDITS.md` and links to GitHub.
- Rename the top-level "Options" menu to "Settings".
- Camera: add DSHOW / MSMF / auto backend picker; longer capture-size
  list; honest exposure + WB readback; theme-aware preview border.

### Files replaced in this session

1. `aymashtain/ui/context.py` — added `selected_strips` list,
   `resolve_targets()`, `selected_strip_count()`, `is_strip_selected()`
   for multi-strip control.
2. `aymashtain/ui/tabs/console_tab.py` — fixed the clamp bypass: parse
   both 18-char (`BC0506040000000055`) and 20-char
   (`BC050604000000000055`) brightness frames directly; orange clamp
   preview in "Decode only"; sends go through `ctx.resolve_targets()`.
3. `aymashtain/ui/tabs/sweep_tab.py` — brightness range read fresh on
   every step; logs when the range changes mid-run; sends go through
   `ctx.resolve_targets()`.
4. `aymashtain/ui/tabs/options_tab.py` — added
   `brightness_limits_changed(int, int)` signal; camera backend
   dropdown; longer capture-size list; renamed "Resolution" row to
   "Capture size".
5. `aymashtain/ui/main_window.py` — added `StripSelectorBar` (per-strip
   checkboxes under the menu bar); renamed top-level menu "Options" →
   "Settings"; wired `brightness_limits_changed` to
   `sync_clamp_notice()` on Remote / Sweep / Console / Music; replaced
   the plain-text About with a proper dialog that reads `CREDITS.md`;
   Control-menu power commands honour strip selection.
6. `aymashtain/ui/tabs/camera_tab.py` — backend picker
   (Auto / DSHOW / MSMF) with fallback; honest exposure readback (no
   more fake "locked"); honest WB readback; theme-aware border colours.
7. `aymashtain/config.py` — added `camera_backend` field with
   validation against `("auto", "dshow", "msmf")`.
8. `aymashtain/ui/tabs/music_tab.py` — removed the four
   "Controller mode" entries; Esc / Stop now sends the Remote tab's
   current static colour back to the strip; sends go through
   `ctx.resolve_targets()`; added `sync_clamp_notice()` hook.
9. `aymashtain/ui/tabs/remote_tab.py` — **first version**: added
   Light-modes section with six collapsible categories, multi-strip
   preview rows (one row per selected strip), right-click hex override
   per mode. **Second version (correction)**: added the missing
   `setProperty("sectionHeader", True)` in `CollapsibleSection` so the
   theme's header styles apply.
10. `aymashtain/ui/theme.py` — added `sectionHeader="true"` styles in
    both dark and light themes.

### What was compiled

- **None.** No `py_compile` output was shared this session. No pytest
  run was shared this session. The user pasted all ten files without
  reporting compile results between them.

### What still needs testing

- **The app does not work after this batch.** The user confirmed this
  at the end of the session.
- No error text, no traceback, no log file was shared. The failure is
  **undiagnosed.**
- First thing next session:
  1. Run `python .\main.py` in PowerShell from the project root and
     paste the exact error.
  2. Run `python -m py_compile` on every file touched this session
     (see the ten-file list above) and paste any output.
  3. Run `python -m pytest -q` and paste the result.
  4. Attach the newest `session_*.log` and `session_*.json` from
     `%LOCALAPPDATA%\AymashTain\logs\`.

### What's left to do (next session)

1. Diagnose the launch failure — get the real error first, do not
   guess.
2. Fix whatever broke, one file at a time, full replacements.
3. Re-run `py_compile` + `pytest` after each file.
4. Do **not** start any new feature work until Round 3 is verified
   working end to end.
5. Then continue the Round 3 verification checklist:
   - Console clamp on both 18-char and 20-char frames.
   - Sweep mid-run range change.
   - Remote / Sweep / Console / Music clamp-notice refresh when
     Options range changes.
   - Camera backend switch + honest exposure / WB readback.
   - Multi-strip selector (tick one strip, confirm only that strip
     receives commands).
   - Light modes section expand / send.
   - Music: Esc sends stable colour.

### Honest notes on what's best-guess

- **Light-mode hexes are best-guess.** The vendor app's Light Mode
  opcodes are not in the captured protocol. Every button is mapped to
  the closest documented effect byte (`BC 06 02 XX 00 00 55`), and the
  tooltip shows which byte it uses. Right-click any button to override
  with a captured frame — overrides live for the session only.
- **Camera backend "auto"** tries DSHOW, then MSMF, then the OpenCV
  default. DSHOW is more likely to honour manual exposure on Windows.
- **Multi-strip selection** is stored only in `AppContext.selected_strips`
  — it is not persisted across app restarts. That was intentional for
  this round; persistence can be added later if wanted.

### Suggested next-chat opening line

> Continue from Session 12. The Round 3 batch was delivered but the app
> does not start. First, collect the real failure output: run
> `python .\main.py` from the project root and paste the error, run
> `python -m py_compile` on every file touched in Session 12, run
> `python -m pytest -q`, and attach the newest log from
> `%LOCALAPPDATA%\AymashTain\logs\`. Then fix the launch failure one
> file at a time, full replacement files only. Do not touch
> `ble/manager.py`, `protocol/mrstar.py`, or `storage/db.py` schema.
> Do not start Round 4 until Round 3 is verified working.

<!-- END FILE: AI_SYNC_PACK/06_CURRENT_CHAT.md -->