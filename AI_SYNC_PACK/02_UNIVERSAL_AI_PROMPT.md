# Universal AI Prompt for AymashTain LED RGB Remote

Copy everything below this line and give it to any AI together with:

- the `AI_SYNC_PACK` folder
- the current file you want updated
- the latest conversation/logs
- the exact task you want done

---

## PROMPT START

You are updating **AymashTain LED RGB Remote v0.51 Alpha**.

Read these files first:

- `00_MASTER_SUMMARY.md`
- `01_WORKFLOW.md`
- `02_UNIVERSAL_AI_PROMPT.md`
- `03_TODO_USER_AND_AI.md`
- `04_AI_ERRORS_ONLY.md`
- `05_DEVELOPER_README.md`
- `06_CURRENT_CHAT.md`

Project facts:

1. Project folder: `D:\Coding projects\aymashtain-led-remote-Source`
2. This is a **package** project, not a single `main.py`.
   Real code is in `aymashtain/`.
   Entry point: `main.py` → `aymashtain.app:main`.
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
- Never remove the per-device serialized queue in `aymashtain/ble/manager.py`. It is what keeps colour and brightness in order.
- Never use `asyncio.create_task()` to fire colour and brightness in parallel.
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

Current status:

- App runs. 3/3 strips connect. 54 frames sent, 0 failed.
- `BleManager` queue works.
- Colour/brightness order works.
- Session logger works.
- **Not built yet:** hidden-feature laboratory, camera ROI visual calibration, exposure lock, 150-LED preview, profile import/export, About dialog with credits.
- Version: release is `v0.51 Alpha`; code currently says `1.0.0`. Keep them consistent.

User style:

- The user is not a developer.
- Give one point at a time.
- Visual, simple, step-by-step.
- Prefer full file replacement over manual edits.
- Never ask the user to merge fragments by hand.

Priority order:

1. Hidden-feature laboratory in `aymashtain/ui/tabs/lab_tab.py`.
2. Camera ROI visual calibration in `aymashtain/ui/tabs/camera_tab.py`.
3. Camera exposure / white balance lock.
4. 150-LED horizontal preview in `aymashtain/ui/widgets/strip_preview.py`.
5. About dialog with credits.
6. Profile import / export.
7. Final packaging.

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