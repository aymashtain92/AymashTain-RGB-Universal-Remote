# How to hand off to an AI — the one-click method

This is the easiest way to get help from any AI.
Follow these steps exactly. Don't skip.

---

## What you need

- The project folder at
  `D:\Coding projects\aymashtain-led-remote-Source`
- Nothing else. The tool does the rest.

---

## Step-by-step

1. **Double-click `make_handoff.bat`** in the project root.

2. **Wait two seconds.** A black window prints the hand-off number,
   e.g. `Hand-off #007 created`, and opens the `handoff\` folder for you.

3. **Inside `handoff\` you'll see a new zip**, named like
   `handoff_007_20260921_1530.zip`. The number goes up every time —
   nothing is ever overwritten.

4. **Right-click the zip → Extract All** (or drag it out and unzip it
   with 7-Zip / WinRAR). Anywhere is fine.

5. **Open a brand-new AI chat.**

6. **Drag the unzipped folder into the chat.** The whole folder. The AI
   gets the source tree, the sync pack, and a README at the top telling
   it where to start.

7. **Paste the prompt from `AI_SYNC_PACK\02_UNIVERSAL_AI_PROMPT.md`** as
   your first message. (If you forget, the bundle README tells the AI to
   go read it itself.)

8. **Tell the AI exactly what to do**, one thing at a time. For example:
   "Continue from Session 6. Next file is
   `aymashtain/events.py`. Full replacement only."

9. **When the AI sends a full file**, replace the old one on your PC:
   - Open the old file in Notepad.
   - Ctrl+A, Delete.
   - Paste the new content.
   - Save.

10. **Compile-check.** Open PowerShell in the project folder and run:
    ```
    python -m py_compile .\aymashtain\ui\tabs\remote_tab.py
    ```
    No output = success.

11. **Test the app.** `python .\main.py` or double-click `run.bat`.

12. **Update the sync pack** (see "After you test" below), then run
    `make_handoff.bat` again before the next chat.

---

## After you test the app

Update these files in `AI_SYNC_PACK\`:

- `06_CURRENT_CHAT.md` — **always** add a new session section (date, AI
  name, what was asked, what changed, what still needs testing).
- `00_MASTER_SUMMARY.md` — only if status or structure changed.
- `01_WORKFLOW.md` — add a dated entry for the session.
- `03_TODO_USER_AND_AI.md` — tick done items, add new ones.
- `04_AI_ERRORS_ONLY.md` — only if the AI made a new mistake worth
  recording.
- `05_DEVELOPER_README.md` — only if environment or install changed.

Then run `make_handoff.bat` again before the next chat.

---

## FAQ

**Q: Which files get bundled?**
A: Everything in `aymashtain\`, everything in `AI_SYNC_PACK\`, plus
`main.py`, `requirements.txt`, `pyproject.toml`, `README.md`,
`CREDITS.md`, `.gitignore`, the PyInstaller `.spec`, and your
`AI_CONTEXT.md` / `AI_NOTES.md` / `AI_SESSIONS.md` if you keep them.
Tests and assets too if present.

**Q: What does NOT get bundled?**
A: `__pycache__`, `.venv`, `build\`, `dist\`, your `.db` file, session
logs, and anything in `handoff\` (so bundles never nest). Also
`events.csv`, `events.json`, and `test.txt` — those are session junk.

**Q: The AI gave me only part of the file. What do I do?**
A: Say: "Send the FULL file. Do not send pieces."

**Q: I ran the compile command and got an error.**
A: Copy the whole red error into the chat and say: "Fix this error and
send the full file."

**Q: The app doesn't open.**
A: In PowerShell, run `python .\main.py`. Copy the real error into the
chat.

**Q: Can I edit the sync pack by hand?**
A: Yes. It's just markdown. Keep the numbering (00-07) intact so the
next AI reads them in the right order.

**Q: Where does the handoff zip go?**
A: `<project root>\handoff\`. You can delete old ones whenever you like
— a new run creates a new number, it does not touch the old ones.

**Q: Do I still need `ai_sync.py`?**
A: Yes, it auto-generates `AI_CONTEXT.md` on every git commit, which is
included in the hand-off bundle as a bonus. The sync pack (00-07) is
still the main document the AI reads first.

---

## Why this works

The zip contains a `HANDOFF_README.txt` as its first file. When the AI
opens the unzipped folder, that file tells it:

- This is a snapshot, not a live folder.
- Read `AI_SYNC_PACK/02_UNIVERSAL_AI_PROMPT.md` first.
- Then read `00` through `05` in order.
- Read `06_CURRENT_CHAT.md` last — that is the "where we left off".
- Then ask the user which single file to work on.

That means you can just drop the folder and type "continue", and the
AI knows what to do.

---

## Current release

**v0.61 Alpha** — package project. Launcher is `main.py` →
`aymashtain.app:main`.

---

## License

MIT License. See `LICENSE.txt`.
Third-party libraries have their own licenses. See `CREDITS.md`.