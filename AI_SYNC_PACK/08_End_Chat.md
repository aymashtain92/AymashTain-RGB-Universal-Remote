# 08 — End of Chat Ritual

**Version:** v0.61 Alpha
**Added in:** Session 10 (2026-09-21)

This file is **not** part of the handoff bundle contents the next AI reads
first. It is a tool **you** use at the end of a session to get the sync
pack updated cleanly.

---

## When to use this

Paste the prompt below when you are **done** with an AI chat session and
you want:

- A written record of what the session did.
- Updated `06_CURRENT_CHAT.md` with a new session section.
- Ticked / added items in `03_TODO_USER_AND_AI.md`.
- A dated entry in `01_WORKFLOW.md`.
- New entries in `04_AI_ERRORS_ONLY.md` if the AI made a mistake.
- A clean "start here" line for the next chat.

---

## How to use it

1. Finish whatever you were doing in the chat.
2. Copy everything between `PROMPT START` and `PROMPT END`.
3. Paste it into the same chat as your final message.
4. The AI will answer with the updated files, **one at a time, as full
   replacements**.
5. Save each file. Then run `make_handoff.bat` before you start the
   next chat.

---

## PROMPT START

Session is ending. Do the closing ritual.

**Rules for this reply:**

- One file at a time. Wait for me to say "next" before sending the next
  file.
- Full replacement files only, in one code block each.
- UTF-8, standard markdown, blank line before and after every code
  fence.
- Do not invent facts. Only record what actually happened in this
  session.
- If a file does not need to change this session, say so and skip it.

**Files to produce, in this order:**

### 1. `06_CURRENT_CHAT.md` — always

Append a new session section at the bottom. Use exactly this shape:

```markdown
## Session N — <short title> (v0.61 Alpha)

**Date:** <YYYY-MM-DD>
**AI name:** <your real model name, not "ChatGPT">
**Version target:** v0.61 Alpha

### User request

- <bullet list of what I asked for>

### Files replaced in this session

1. `<path>` — <one-line description of what changed>
2. `<path>` — <one-line description>

### What was compiled

- <list of files that passed `python -m py_compile`>

### What still needs testing

- <list>

### What's left to do (next session)

1. <bullet>

### Suggested next-chat opening line

> Continue from Session N. Next file is `<path>`. <what to do>. Full
> replacement files only. Do not touch `ble/manager.py`,
> `protocol/mrstar.py`, or `storage/db.py` schema.
```

Do not touch Sessions 1 through 9. Only append.

### 2. `03_TODO_USER_AND_AI.md` — always

- Tick every `[ ]` that this session actually completed.
- Move any "Passed" live-test items from Section B into the "Live test
  run" subsection in Section A.
- Move any "Failed" live-test items into the correct Round 3 phase in
  Section B.
- Add new items under the correct phase if the session discovered new
  work.
- Update the `**Last updated:**` line at the top.

### 3. `01_WORKFLOW.md` — always

Add a dated entry for this session, following the existing pattern:

```markdown
## <YYYY-MM-DD> - <short title> (Session N)

**<AI name>**

- <what was done>
```

Add a matching row to the "Who did what" table at the bottom.

### 4. `04_AI_ERRORS_ONLY.md` — only if a mistake was made

If the AI (you) made a mistake this session — wrong file edit, wrong
protocol command, wrong assumption — add a new numbered rule under the
correct section. Keep the rule specific and actionable. Do not add
generic warnings.

If no mistake was made, skip this file and say so.

### 5. `00_MASTER_SUMMARY.md` — only if status or structure changed

Update only if:

- The project version changed.
- A new top-level file or folder was added.
- A "Working" item moved to "Not built yet" or vice versa.
- A golden rule changed.

Otherwise skip it and say so.

### 6. `05_DEVELOPER_README.md` — only if environment changed

Update only if:

- A dependency version changed.
- A new folder or file structure was added.
- The install / run instructions changed.

Otherwise skip it and say so.

### 7. `02_UNIVERSAL_AI_PROMPT.md` — only if the workflow changed

Update only if:

- The "read these files in this order" list changed.
- The project facts section changed (Python version, strips, UUIDs).
- The "never do these" rules changed.
- The "current status" section changed materially.

Otherwise skip it and say so.

### 8. `07_HOW_TO_USE_AI_SYNC.md` — only if the handoff workflow changed

Update only if:

- The bundle layout changed.
- The FAQ has a new common question.
- The step-by-step instructions changed.

Otherwise skip it and say so.

---

**After all files are delivered:**

Print a short summary at the end of your reply, in plain text:

```
=== END OF SESSION SUMMARY ===
Session: N
Files produced: <list>
Files skipped:  <list, with reason>
Next file to work on: <path>
Save these files, then run: make_handoff.bat
=== END ===
```

Then stop. Do not ask follow-up questions. Do not propose more work.

## PROMPT END

---

## What you do after the AI replies

1. Save each file the AI sends, in the order it sends them.
2. Remember: no `py_compile` is needed for `.md` files.
3. Run `make_handoff.bat` in the project root.
4. Unzip the newest `handoff\handoff_NNN.zip` somewhere.
5. Open a **fresh AI chat**.
6. Drag the unzipped folder in.
7. Paste the "Suggested next-chat opening line" the AI printed at the
   end of its reply.

That's the whole cycle.

---

## Quick reference — what to save where

| AI sends | Save as (on your PC) |
|---|---|
| `06_CURRENT_CHAT.md` | `AI_SYNC_PACK\06_CURRENT_CHAT.md` |
| `03_TODO_USER_AND_AI.md` | `AI_SYNC_PACK\03_TODO_USER_AND_AI.md` |
| `01_WORKFLOW.md` | `AI_SYNC_PACK\01_WORKFLOW.md` |
| `04_AI_ERRORS_ONLY.md` | `AI_SYNC_PACK\04_AI_ERRORS_ONLY.md` |
| `00_MASTER_SUMMARY.md` | `AI_SYNC_PACK\00_MASTER_SUMMARY.md` |
| `05_DEVELOPER_README.md` | `AI_SYNC_PACK\05_DEVELOPER_README.md` |
| `02_UNIVERSAL_AI_PROMPT.md` | `AI_SYNC_PACK\02_UNIVERSAL_AI_PROMPT.md` |
| `07_HOW_TO_USE_AI_SYNC.md` | `AI_SYNC_PACK\07_HOW_TO_USE_AI_SYNC.md` |

---

## FAQ

**Q: Do I have to paste this every time?**
A: Only when you want a clean written record of the session. If you just
want to keep working, you can skip it and only run the ritual before you
start the *next* chat.

**Q: What if the AI only updates one file?**
A: That's correct. Files marked "only if…" get skipped when nothing
changed. The AI will tell you which files it skipped and why.

**Q: What if the AI forgets to add the session to `06_CURRENT_CHAT.md`?**
A: Say: "You skipped `06_CURRENT_CHAT.md`. Add the session entry now,
full replacement, then continue."

**Q: What if the AI invents a file path?**
A: Say: "That path does not exist. Check the flat bundle and use the
`# Original Path:` header."

**Q: The AI says "everything is fine, no changes needed". What now?**
A: That means no sync-pack file needed an update. Just run
`make_handoff.bat` and start the next chat — the old sync pack still
applies.

**Q: Where does this file live?**
A: `AI_SYNC_PACK\08_End_Chat.md`. It is **not** merged into the flat
bundle. It lives only on your PC, as a reference for you.