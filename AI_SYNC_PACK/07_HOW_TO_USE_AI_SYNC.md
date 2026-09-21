# How to hand off to an AI — the one-click method

This is the easiest way to get help from any AI. Follow these steps
exactly. Don't skip.

---

## What you need

- The project folder at
  `D:\Coding projects\aymashtain-led-remote-Source`
- Nothing else. The tool does the rest.

---

## Step-by-step

1. **Double-click `make_handoff.bat`** in the project root.

2. **Wait two seconds.** A black window prints progress, shows the file
   count and the "under 35 / under 50" check, and opens the `handoff\`
   folder for you.

3. **Inside `handoff\` you'll see a new zip**, named like
   `handoff_007.zip`. The number goes up every time — nothing is ever
   overwritten. Each run creates a new number.

4. **Right-click the zip → Extract All** (or drag it out and unzip it
   with 7-Zip / WinRAR). Anywhere is fine.

5. **Open the unzipped folder.** Inside you will see **one flat list of
   files, no subfolders**. That is intentional — most AI chat platforms
   refuse nested folders or mangle them on drag-and-drop.

6. **Open a brand-new AI chat.**

7. **Drag the unzipped folder into the chat.** The whole folder. The AI
   gets the source tree, the merged docs, and a `HANDOFF_README.txt` at
   the top telling it where to start.

8. **Paste the prompt** from the top of `00_PROJECT_MASTER_DOCS.md` (it
   contains the universal prompt inline) as your first message. If you
   forget, the bundle's `HANDOFF_README.txt` tells the AI to go read it
   itself.

9. **Tell the AI exactly what to do**, one thing at a time. For example:
   "Continue from Session 11. Next file is `console_tab.py`. Full
   replacement only."

10. **When the AI sends a full file**, replace the old one on your PC:

    - Open the old file in Notepad.
    - Ctrl+A, Delete.
    - Paste the new content.
    - Save.

    Remember the real path — in the bundle it looks like
    `aymashtain__ui__tabs__remote_tab.py`, but on your PC it lives at
    `aymashtain\ui\tabs\remote_tab.py`. The `# Original Path:` comment at
    the top of every file tells you where it belongs.

11. **Compile-check.** Open PowerShell in the project folder and run:

    ```
    python -m py_compile .\aymashtain\ui\tabs\remote_tab.py
    ```

    No output = success.

12. **Test the app.** `python .\main.py` or double-click `run.bat`.

13. **Update the sync pack** — the fastest way is to paste
    `AI_SYNC_PACK\08_End_Chat.md` (see "End of session" below), then run
    `make_handoff.bat` again before the next chat.

---

## What's inside the flat bundle (32 files)

Three merged docs, one package-init reference doc, and one file per
source file. Here's the exact breakdown:

### Documentation (5 files)

- **`HANDOFF_README.txt`** — quick orientation for the next AI.
- **`00_PROJECT_MASTER_DOCS.md`** — merged from the old `00`, `02`,
  `05`, `07`. Contains the project summary, the universal AI prompt
  (ready to paste), the developer README, and this handoff guide.
- **`01_WORKFLOW_AND_TODO.md`** — merged from the old `01`, `03`, `04`.
  Contains the full timeline, the current TODO list (done / now /
  future), and the "AI ERRORS ONLY" list of mistakes never to repeat.
- **`02_CURRENT_CHAT.md`** — the old `06`. **Read this last** — it
  records exactly what the previous session did and what comes next.
- **`_package_init_exports.md`** — the five tiny sub-package
  `__init__.py` files merged into one reference doc. They were re-export
  shims; too small to justify five separate files.

### Source files (27 files)

- `main.py`
- `aymashtain/__init__.py`, `app.py`, `config.py`, `events.py`,
  `paths.py`
- `aymashtain/ble/manager.py`
- `aymashtain/protocol/mrstar.py`
- `aymashtain/storage/db.py`
- `aymashtain/vision/camera.py`
- `aymashtain/audio/engine.py`
- `aymashtain/ui/context.py`, `theme.py`, `main_window.py`
- `aymashtain/ui/widgets/__init__.py`, `color_wheel.py`,
  `strip_preview.py`
- `aymashtain/ui/tabs/__init__.py` + all 9 tab files

Every source file is flattened. Here's the naming scheme:

| Real path on your PC | Flat name in the bundle |
|---|---|
| `main.py` | `main.py` |
| `aymashtain\__init__.py` | `aymashtain____init__.py` |
| `aymashtain\ble\manager.py` | `aymashtain__ble__manager.py` |
| `aymashtain\ui\tabs\remote_tab.py` | `aymashtain__ui__tabs__remote_tab.py` |
| `aymashtain\ui\tabs\__init__.py` | `aymashtain__ui__tabs____init__.py` |

Each source file starts with a `# Original Path: <real/path>` header on
line 1. That is how you and the AI both know where it belongs.

### What is NOT in the bundle

- `.gitignore`, `pyproject.toml`, `requirements.txt`, `.spec`,
  `README.md`, `CREDITS.md`, `LICENSE.txt` — not needed by the AI.
- `tests/`, `assets/` — not needed by the AI.
- `.db` files — they hold private profiles and buttons.
- Session logs, exported `events.csv` / `events.json`, `test.txt` —
  per-run junk.
- The `handoff/` folder itself — so bundles never nest.
- All `AI_*` helper files (`AI_CONTEXT.md`, `AI_NOTES.md`,
  `AI_SESSIONS.md`, `AI_BRIEF.md`, `AI_BACKLOG.md`, `PROJECT.md`,
  `ai_sync.py`).

Why 32 files? DeepSeek caps uploads at 50. The user needs room for
screenshots (usually 10–15). 32 + 18 = 50. Tight, but fits.

---

## Pre-flight check

Before you send the bundle, unzip it once and verify:

- Total files: **32**.
- **Zero subfolders** inside the unzipped folder.
- Every `.py` starts with a `# Original Path:` line.
- `00_PROJECT_MASTER_DOCS.md`, `01_WORKFLOW_AND_TODO.md`, and
  `02_CURRENT_CHAT.md` all exist.

If any of those is wrong, re-run `make_handoff.bat` and check the
output. If the count is not 32, the wrong `make_handoff.py` is on disk —
replace it with the version from Session 11.

---

## End of session — the ritual

When you are done with a chat session and want the sync pack updated
cleanly, do this:

1. Open `AI_SYNC_PACK\08_End_Chat.md`.
2. Copy everything between `PROMPT START` and `PROMPT END`.
3. Paste it into the same chat as your final message.
4. The AI will reply with **one file at a time** — usually 3 to 5
   files, depending on what changed.
5. Save each file as it comes. Reply "next" to get the following one.
6. When the AI prints the `=== END OF SESSION SUMMARY ===` block, you
   are done.

Then run `make_handoff.bat` before you start the next chat.

### Why `08_End_Chat.md` is not in the bundle

It is a tool **for you**, not for the next AI. It never needs to be
shipped. It lives only in `AI_SYNC_PACK\` on your PC.

---

## Manual update (if you prefer)

If you don't want to use the ritual prompt, update these files by hand
in `AI_SYNC_PACK\` after a session:

- **`06_CURRENT_CHAT.md`** — **always** add a new session section.
- **`03_TODO_USER_AND_AI.md`** — tick done items, move failures into
  the correct Round 3 phase.
- **`01_WORKFLOW.md`** — add a dated entry for the session.
- **`04_AI_ERRORS_ONLY.md`** — only if the AI made a new mistake.
- **`00_MASTER_SUMMARY.md`** — only if status or structure changed.
- **`05_DEVELOPER_README.md`** — only if environment or install
  changed.

Then run `make_handoff.bat` before the next chat.

---

## FAQ

**Q: Which files get bundled?**
A: Exactly 32. See "What's inside the flat bundle" above for the full
list.

**Q: What does NOT get bundled?**
A: `.gitignore`, `pyproject.toml`, `requirements.txt`, `.spec`,
`README.md`, `CREDITS.md`, `LICENSE.txt`, `tests/`, `assets/`,
`__pycache__`, `.venv`, `build\`, `dist\`, `.git`, the `.db` file,
session logs, exported `events.csv` / `events.json`, `test.txt`, and
everything inside `handoff\`. Also all `AI_*` helper files.

**Q: Why is `.gitignore` not in the bundle?**
A: AI chat platforms don't use it. It adds a file slot without helping
the AI.

**Q: Why are there no folders inside the zip?**
A: Because most AI chat platforms refuse nested folders, and DeepSeek
caps uploads at 50 files. Flattening keeps the bundle compatible with
every AI the user works with.

**Q: Why are there `__` in the file names?**
A: To keep every file unique in one flat folder. Each `__` marks what
was a folder separator on your PC:
`aymashtain__ui__tabs__remote_tab.py` = `aymashtain\ui\tabs\remote_tab.py`.

**Q: How do I know where a file belongs?**
A: Line 1 of every source file says `# Original Path: <real/path>`.
Copy the path on the right, open that file on your PC, and paste the new
content in.

**Q: The AI gave me only part of the file. What do I do?**
A: Say: "Send the FULL file. Do not send pieces."

**Q: I ran the compile command and got an error.**
A: Copy the whole red error into the chat and say: "Fix this error and
send the full file."

**Q: The app doesn't open.**
A: In PowerShell, run `python .\main.py`. Copy the real error into the
chat.

**Q: Can I edit the sync pack by hand?**
A: Yes. It's just markdown. Keep the numbering (`00` through `08`)
intact so the merge into the flat bundle reads them in the right order.

**Q: Where does the handoff zip go?**
A: `<project root>\handoff\`. You can delete old ones whenever you like
— a new run always creates a new number and never touches the old ones.

**Q: Do I still need `ai_sync.py`?**
A: Yes. It auto-generates `AI_CONTEXT.md` on every git commit. But that
file is **not** in the flat bundle — the merge already gives the AI
everything it needs. You can keep `ai_sync.py` for your own repo history
if you like.

**Q: Do I still need `08_End_Chat.md`?**
A: Yes. It is the fastest way to get the sync pack updated. Without it,
you have to remember which files to touch after every session. It lives
only on your PC — never in the bundle.

**Q: How do I check the bundle before sending it?**
A: Unzip it and count the files. Should be 32. Every file should be at
the top level — no subfolders. Every `.py` should start with
`# Original Path:`.

**Q: What if the bundle has more than 32 files?**
A: The wrong `make_handoff.py` is on disk. Replace it with the version
from Session 11 — it uses an explicit allowlist and produces exactly 32.

**Q: Can I use `--dry-run` to preview?**
A: Yes:

```
python .\make_handoff.py --dry-run
```

It prints the full file list and the count, and does not create a zip.

---

## Why this works

The zip contains a `HANDOFF_README.txt` as its first file. When the AI
opens the unzipped folder, that file tells it:

- This is a **flat** snapshot, not a live folder.
- Read `00_PROJECT_MASTER_DOCS.md` first.
- Then `01_WORKFLOW_AND_TODO.md`.
- Then `_package_init_exports.md`.
- Read `02_CURRENT_CHAT.md` last — that is the "where we left off".
- Source files start with `# Original Path:` so it can rebuild the tree
  in its head.
- Then ask the user which single file to work on.

That means you can just drop the folder and type "continue", and the AI
knows what to do.

---

## Current release

**v0.61 Alpha** — package project. Launcher is `main.py` →
`aymashtain.app:main`.

Hand-off bundle: **32 files, zero subfolders**.

---

## License

MIT License. See `LICENSE.txt`.
Third-party libraries have their own licenses. See `CREDITS.md`.