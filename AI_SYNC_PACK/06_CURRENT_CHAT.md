# Current Chat Summary — 2026-09-21

This file records the current conversation between the user and ChatGPT.

---

## User request

- Confirm which project folder is the real one.
- Rewrite `00`–`06` of the `AI_SYNC_PACK` to match the real project.

---

## Decision made

Real project folder:

```text
D:\Coding projects\aymashtain-led-remote-Source
```

This is a **package** project (Devin AI rewrite), not the flat `main.py` version.

The `AI_SYNC_PACK` was previously describing the flat project. It is now corrected.

---

## What this chat did

- Confirmed from screenshots that the package app runs.
- Confirmed 3/3 strips connect, 54 frames sent, 0 failed.
- Confirmed BleManager serialized queue works.
- Confirmed colour / brightness order works.
- Confirmed session logs work.
- Rewrote `00`–`06` for the package structure.
- Listed remaining gaps: hidden-feature lab, camera ROI picker, exposure lock, 150-LED preview, profile import/export, About dialog, version reconciliation.

---

## Next step

Build the **hidden-feature laboratory** in `aymashtain/ui/tabs/lab_tab.py`.

Then:

1. Camera ROI visual calibration.
2. Camera exposure / white balance lock.
3. 150-LED horizontal preview.
4. About dialog with credits.
5. Profile import / export.
6. Version reconciliation to `v0.51 Alpha`.

---

## Important note

Update this file after every AI session. Add:

- Date
- AI name
- What was asked
- What changed
- Files replaced
- What still needs testing