# Universal AI Prompt for AymashTain LED RGB Remote

Copy everything below this line and give it to any AI.

**In the new one-click workflow you don't need to attach anything by
hand** — the hand-off bundle already contains every file listed here.
Just drag the unzipped bundle folder into the chat and paste the prompt.

---

## PROMPT START

You are updating **AymashTain LED RGB Remote v0.61 Alpha**.

You have been handed a complete snapshot of the project. Read these
files first, in this order:

1. `HANDOFF_README.txt` (top of the bundle — tells you what's inside)
2. `AI_SYNC_PACK/02_UNIVERSAL_AI_PROMPT.md` (this file)
3. `AI_SYNC_PACK/00_MASTER_SUMMARY.md`
4. `AI_SYNC_PACK/01_WORKFLOW.md`
5. `AI_SYNC_PACK/03_TODO_USER_AND_AI.md`
6. `AI_SYNC_PACK/04_AI_ERRORS_ONLY.md`
7. `AI_SYNC_PACK/05_DEVELOPER_README.md`
8. `AI_SYNC_PACK/06_CURRENT_CHAT.md` — **read this last** — it records
   exactly what the previous session did and what comes next.
9. `AI_SYNC_PACK/07_HOW_TO_USE_AI_SYNC.md` — if you need to understand
   how the user works.

Project facts:

1. Project folder: `D:\Coding projects\aymashtain-led-remote-Source`
2. This is a **package** project, not a single `main.py`.
   Real code is in `aymashtain/`.
   Entry point: `main.py` -> `aymashtain.app:main`.
3. Python is **3.14.7** on Windows 10.
4. Bleak is **3.0.2**.
5. NumPy is **2.5.3**.
6. OpenCV is **5.0.0.93**.
7. Three strips:
   - `41:42:59:F1:C8:68`
   - `41:42:43:E7:8B:F6`
   - `41:42:F9:D7:45:B0`
8. They advertise as `GATT--DEMO`.
9. Write characteristic: `0000fff3-0000-1000-8000-00805f9b34fb`.
10. Service: `00002022-0000-1000-8000-00805f9b34fb`.
11. App must stay free. No ads. No telemetry.

Protocol rules:

- Colour: `BC 04 06 HH HH SS SS 00 00 55`
- Brightness (separate): `BC 05 06 BB BB 00 00 00 00 55`
- Power: `BC01010155` ON, `BC01010055` OFF
- Captured static: `BC04010055`
- Captured Scroll lives in `aymashtain/protocol/mrstar.py`
- Classic Magic Home: `CC2333`, `CC2433`, `56RRGGBB00F0AA`

Never do these:

- Never mix MR Star BC commands with Classic 56/CC commands.
- Never put brightness inside the colour frame.
- Never use `FFFF` as a white field.
- Never remove the per-device serialized queue in
  `aymashtain/ble/manager.py`. It is what keeps colour and brightness in
  order.
- Never use `asyncio.create_task()` to fire colour and brightness in
  parallel.
- Never use hardcoded handle 13 or 19. Use the FFF3 UUID.
- Never claim the app can read actual LED state over BLE.
- Camera stays local-only. No uploads.
- Never run Music Sync or Scroll during static colour tests.
- Never auto-elevate to administrator.
- Never overwrite previous logs.
- Never provide partial patches unless the user explicitly asks.
- Always give a complete replacement file when replacing a file.
- Always run `python -m py_compile .\file.py` after replacement.
- Do not use `py -3.12`. Use `python`.

Current status (v0.61 Alpha):

- App runs. 3/3 strips connect. 54 frames sent, 0 failed.
- `BleManager` queue works.
- Colour/brightness order works.
- Session logger works.
- Hidden-feature laboratory built.
- Options tab built (theme, dev lock, brightness clamp, audio, camera,
  window memory).
- Neon strip preview built (per-LED capsules + glow).
- Camera exposure + WB lock built with honest driver reporting.
- Remote tab: brightness clamp + live per-LED preview built.
- **Still to do:** `events.py` / `events_tab.py` user-facing "Export
  log" only; `theme.py` dark-mode softening + menu audit; `sweep_tab.py`
  brightness clamp; `console_tab.py` clamp; final compile pass.

User style:

- The user is not a developer.
- Give one point at a time.
- Visual, simple, step-by-step.
- Prefer full file replacement over manual edits.
- Never ask the user to merge fragments by hand.

When asked to update a file:

- Read the current file fully.
- Apply the changes.
- Return the **full file** in one code block.
- After the file, give the compile command:
  `python -m py_compile .\path\to\file.py`

When asked to debug:

- Ask for the exact error text.
- Ask for the relevant log file from `%LOCALAPPDATA%\AymashTain\logs\`.
- Do not guess.

When asked to add a feature:

- Keep it inside the `aymashtain/` package.
- Do not add new top-level scripts.
- Keep the existing SQLite schema compatible.
- Do not break Scroll.
- Keep experimental commands separate.

## PROMPT END