<!-- BEGIN FILE: AI_SYNC_PACK/04_AI_ERRORS_ONLY.md -->

# AI Errors Only — Mistakes Never to Repeat

**Version:** v0.61 Alpha
**Last updated:** 2026-09-22 (after Session 12)

This file is a **numbered list of mistakes the AI has made**, so a fresh
AI reading the sync pack does not repeat them. Each item is specific and
actionable.

**Note:** the copy of this file that shipped inside the Session 12
hand-off bundle was corrupted — it contained a duplicate of
`05_DEVELOPER_README.md`. It was restored in Session 12. See item 71.

---

## A. Protocol mistakes (do not repeat)

**1.** Never mix MR Star BC commands with Classic Magic Home 56/CC
commands. They are two different controllers and the byte layout is
incompatible.

**2.** Never pack brightness into the colour frame. Colour is
`BC 04 06 HHHH SSSS 0000 55`. Brightness is a separate
`BC 05 06 BBBB 00000000 55`. Merging them is what makes colours look
pale or white-tinted.

**3.** Never use `FFFF` as a "white" field. The trailing two bytes of the
colour frame are reserved and must be `0000`.

**4.** Never remove the per-device serialized queue in
`aymashtain/ble/manager.py`. It is what keeps colour and brightness in
order and prevents interleaving between strips.

**5.** Never use `asyncio.create_task()` to fire colour and brightness in
parallel. Always go through `BleManager.set_color()`, which sends colour
first, then brightness, in that order.

**6.** Never use a hardcoded handle (13, 19, or anything else) for the
write characteristic. Use the FFF3 UUID:
`0000fff3-0000-1000-8000-00805f9b34fb`.

**7.** Never run Music Sync or the Scroll macro during static colour
tests. The strip will ignore static frames while a captured mode is
active.

**8.** Never claim the app can read the actual LED state over BLE. The
protocol is write-only. The only way to know what the strip is showing
is the camera tab.

**9.** Never send a brightness frame with value above 1024. The
`encode_brightness()` helper clamps correctly — use it, do not build the
frame by hand.

**10.** Always treat the captured Scroll frames in
`protocol/mrstar.py -> SCROLL_MACRO` as immutable. Do not reorder,
truncate, or "clean up" any of the 29 frames.

---

## B. File-delivery mistakes (do not repeat)

**11.** Always provide **full replacement files**, never partial patches,
unless the user explicitly asks for a patch. The user has confirmed this
every session.

**12.** Always wrap the file in a **single** fenced code block. If the
file itself contains markdown with its own triple-backtick code fences
(any `.md` in `AI_SYNC_PACK/`), use **four backticks** on the outer
fence. A triple-backtick outer fence breaks at the first inner triple
backtick and renders the file mangled. See item 72.

**13.** Always give the exact save path **before** the code block, on its
own line, so the user can find the file quickly.

**14.** Always run `python -m py_compile .\path\to\file.py` after the
user pastes a replaced file, and wait for the result before sending the
next file.

**15.** Always run `python -m pytest -q` after touching any package
`__init__.py`. `py_compile` cannot catch a file whose contents are valid
Python but wrong for its role — this is how the Session 8 import
collision got through.

**16.** Never bundle "here is everything at once". Deliver **one file at
a time** and wait for the user to say "next". The user has confirmed
this every session.

**17.** Do not send a follow-up "correction" that re-sends the whole file
just for one forgotten line. If a fix is needed, say what the line is
and where it goes, then wait for the user to paste it — OR clearly state
"this is a full re-send because the previous copy is now stale".

**18.** When re-sending a full file to correct a previous send, say
exactly which line changed and why. Do not silently re-send.

---

## C. Architecture mistakes (do not repeat)

**19.** Do not replace the `aymashtain/` package with a flat single-file
`main.py`. The package layout is deliberate. Top-level `main.py` only
forwards to `aymashtain.app:main`.

**20.** `aymashtain/__init__.py` holds **app identity constants only**.
No imports from other subpackages. It was once overwritten with the
contents of `ui/tabs/__init__.py` and broke every import in the app. See
item 70.

**21.** Each sub-package `__init__.py` (in `ble/`, `protocol/`,
`storage/`, `vision/`, `audio/`, `ui/`, `ui/widgets/`, `ui/tabs/`) only
re-exports names — no logic, no state.

**22.** Do not add new top-level scripts. New features go inside
`aymashtain/`.

**23.** Keep the SQLite schema compatible. If you must add a column, add
it with a default and keep old rows readable.

**24.** Keep experimental commands in the Lab tab, not in the Remote tab.

**25.** Do not auto-elevate to administrator. Do not write to
`C:\Program Files`. Everything the app writes lives under
`%LOCALAPPDATA%\AymashTain` (or the override in `AYMASHTAIN_DATA_DIR`).

**26.** Do not overwrite old session logs. Every run gets a fresh
timestamped `.log`, `.json`, `.csv`.

**27.** Do not upload anything anywhere. Camera stays local-only. No
telemetry, no analytics, no crash reporting to a remote server.

**28.** The project is free forever. No ads, no telemetry, no paywalls,
no "pro" mode.

---

## D. Testing / verification mistakes (do not repeat)

**29.** Never claim a file "compiles" or "works" without seeing the
actual output from the user. A file being *delivered* is not the same as
a file being *verified*.

**30.** When a batch spans multiple files, **verify each file before
sending the next**. Do not deliver all ten files and then ask the user
to compile them all at the end. This is exactly the mistake from
Session 12 — ten files were delivered with zero compile output in
between, and the app stopped launching with no diagnosable error.

**31.** Never say "should work" or "should be fine". Say "here is what
to run, paste the output".

**32.** When the user reports a problem, ask for the **exact error
text**, the **exact command** they ran, and the newest log file from
`%LOCALAPPDATA%\AymashTain\logs\`. Do not guess at the cause.

**33.** Never invent a file path. If you are unsure where a file lives,
read the `# Original Path:` header from the flat bundle. The user has
confirmed the flat-bundle convention.

**34.** Never invent a screenshot observation. If the user shares a
screenshot, describe only what is visible. Do not infer state that is
not shown.

---

## E. Environment / tooling mistakes (do not repeat)

**35.** Python is **3.14.7**. Never write `py -3.12` or any other
version. Use `python` (or the `.venv\Scripts\python.exe` if one exists).

**36.** Bleak is **3.0.2**. Do not use APIs removed before 3.0.

**37.** NumPy is **2.5.3**. Do not use removed aliases like
`np.float`, `np.int`, `np.bool`.

**38.** OpenCV is **5.0.0.93**. `cv2.CAP_DSHOW` and `cv2.CAP_MSMF` both
exist; `cv2.CAP_ANY` is the default.

**39.** The project path on the user's PC is
`D:\Coding projects\aymashtain-led-remote-Source`. The bundle is
**flat** — every file sits in one folder, subpaths use `__` separators,
and every source file starts with a `# Original Path:` header.

**40.** Do not assume the user is a developer. Give one step at a time,
with the exact command to paste, and the exact expected output.

---

## F. Session-specific mistakes (do not repeat)

### Session 8

**68.** `aymashtain/__init__.py` was overwritten with the contents of
`aymashtain/ui/tabs/__init__.py`. That made `import aymashtain` try to
pull in Qt tab classes from the wrong path and every submodule import
failed. **Never** put imports of subpackages into the top-level
`__init__.py`. It holds app identity constants only.

**69.** `py_compile` reported clean for the file above, because the
contents were valid Python — they just were not valid for the file's
role. This is the whole reason the pytest rule exists (item 15).

**70.** The import error only surfaced at runtime, as
`ModuleNotFoundError: No module named 'aymashtain.camera_tab'`. If a
file passes `py_compile` but the app crashes on import, check
`aymashtain/__init__.py` first.

### Session 10

**71.** `04_AI_ERRORS_ONLY.md` in the hand-off bundle was a duplicate of
`05_DEVELOPER_README.md`. The sync pack had been damaged in a prior
attempt. Every sync-pack file was rewritten clean as UTF-8 to fix it.
If the bundle ever again contains a `04_AI_ERRORS_ONLY.md` that talks
about "Environment" and "Install and run" instead of a numbered mistake
list, the wrong file is on disk — replace it with this one.

**72.** The Session 11 end-of-chat reply wrapped a `.md` file in a
**triple-backtick** outer fence. The file contained its own triple
backticks for code samples, which broke the outer fence and mangled the
file. **Any `.md` file the AI sends must use four backticks on the
outer fence.**

### Session 12 (this session)

**73.** Ten files were delivered in one session with **no `py_compile`
or `pytest` output** collected in between. The user confirmed at the end
of the session that the app does not launch. The failure is
undiagnosed. **This is the exact failure mode items 29 and 30 warn
about.** Do not repeat it: verify each file before sending the next.

**74.** `remote_tab.py` was sent twice in a row. The first send was
missing the line
`self.btn_header.setProperty("sectionHeader", True)` inside
`CollapsibleSection.__init__`. The `theme.py` styles for
`QPushButton[sectionHeader="true"]` therefore never applied, and the
header just looked like a plain button. The correction pass fixed it,
but it should have been caught before the first send. **When adding a
widget that depends on a `setProperty("...", True)` theme rule, verify
the property is set in the same send that adds the rule.**

**75.** `main_window.py` grew a new `StripSelectorBar` class in the
same file. Its `refresh()` method is called on every heartbeat
(400 ms). If `refresh()` throws on the very first build — for example
because `self.ctx.ble.devices` is empty and something assumes at least
one entry — the app dies silently during launch. This has not been
confirmed as the actual cause, but it is a plausible candidate and the
kind of thing that should be guarded with a `try/except` around the
tick body. **Wrap per-tick UI refreshes so a single tab failing does
not kill the whole window.**

**76.** The About dialog was written as a `QMessageBox` with the
credits browser added via `dialog.layout().addWidget(...)`. That is
unusual and layout-dependent — `QMessageBox` does not officially
support extra widgets being added this way. The safer pattern is a
plain `QDialog` with its own `QVBoxLayout`. **If a dialog needs
scrolling or rich content, use `QDialog`, not `QMessageBox`.**

**77.** The `options_tab.py` send writes
`self.ctx.settings.camera_backend = backend` and wraps it in a
`try/except AttributeError`. But `config.py` was sent later in the same
session to add that field. **When a change depends on a new field in
`Settings`, send the `config.py` change first, then the file that uses
it.** Sending them in the wrong order leaves the app in a state where
the field does not exist for as long as it takes the user to paste
both.

**78.** Camera exposure lock uses `cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)`
then `cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)` to verify. Some Windows
DSHOW drivers return the *manual* flag value they were given (0.25)
even when the exposure is still auto. The new code treats a readback
`< 0.6` as "manual flag set" — it will report "locked" on such drivers
even when the picture keeps changing. **This is still honest
per-driver — it reports what the driver says — but it is not the same
as "the exposure is actually frozen". Do not upgrade the wording to
"locked" unless the readback *and* a captured sample both agree.**

**79.** The Light-mode hexes in `remote_tab.py` are **best guesses.**
The vendor app's Light Mode opcodes are not in the captured protocol.
Every button is mapped to the closest documented effect byte
(`BC 06 02 XX 00 00 55`). Do not present these as "the real opcodes".
The right-click override is the honest escape hatch until the user
captures real frames.

**80.** Multi-strip selection lives only in `AppContext.selected_strips`
— it is not persisted across app restarts. This was intentional for
Session 12, but do not let it silently become a bug report later. If a
future session adds persistence, document it here.

=== END OF SESSION SUMMARY ===
Session: 12
Files produced:
  1. 06_CURRENT_CHAT.md
  2. 03_TODO_USER_AND_AI.md
  3. 01_WORKFLOW.md
  4. 04_AI_ERRORS_ONLY.md   (full rewrite — the copy on disk was corrupted)
Files skipped:
  - 00_MASTER_SUMMARY.md    (status unchanged; still v0.61 Alpha)
  - 05_DEVELOPER_README.md  (environment unchanged)
  - 02_UNIVERSAL_AI_PROMPT.md (workflow unchanged)
  - 07_HOW_TO_USE_AI_SYNC.md (handoff workflow unchanged)
Next file to work on:
  Unknown until the launch error is collected.
  Session 13 must start with `python .\main.py` output, not with code.
Save these files, then run: make_handoff.bat
=== END ===
---

## G. Golden rules (quick reference)

These summarise the list above. If a rule below conflicts with an
earlier item, the earlier item wins — it has more context.

1. Colour and brightness are **two separate frames**, always.
2. Keep the per-device serialized queue. Never bypass it.
3. Never mix MR Star with Classic Magic Home.
4. Full replacement files only, one at a time, wait for "next".
5. Compile each file before sending the next one.
6. Run pytest after any `__init__.py` change.
7. `.md` files use **four-backtick** outer fences.
8. Ask for the exact error text before guessing at a cause.
9. `aymashtain/__init__.py` is identity constants only.
10. Python 3.14.7. Bleak 3.0.2. NumPy 2.5.3. OpenCV 5.0.0.93.
11. Camera stays local. No uploads. No telemetry. No ads. Free forever.
12. Never auto-elevate. Never overwrite logs. Never write outside the
    data folder.

<!-- END FILE: AI_SYNC_PACK/04_AI_ERRORS_ONLY.md -->