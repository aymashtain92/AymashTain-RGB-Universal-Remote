# Universal AI Prompt for AymashTain LED RGB Remote

Copy everything below this line and give it to any AI together with:

- the `AI_SYNC_PACK` folder
- the current file you want updated
- the latest conversation/logs
- the exact task you want done

---

## PROMPT START

You are updating **AymashTain LED RGB Remote v0.41**.

Read these files first:

- `00_MASTER_SUMMARY.md`
- `01_WORKFLOW.md`
- `02_UNIVERSAL_AI_PROMPT.md`
- `03_TODO_USER_AND_AI.md`
- `04_AI_ERRORS_ONLY.md`
- `05_DEVELOPER_README.md`
- `06_CURRENT_CHAT.md`

Project facts you must obey:

1. The user has 3 BLE LED strips:
   - `41:42:59:F1:C8:68`
   - `41:42:43:E7:8B:F6`
   - `41:42:F9:D7:45:B0`
2. They advertise as `GATT--DEMO`.
3. Write characteristic is `0000fff3-0000-1000-8000-00805f9b34fb`.
4. Service is `00002022-0000-1000-8000-00805f9b34fb`.
5. Python is **3.14.7** on Windows 10.
6. Bleak is **3.0.2**.
7. NumPy is **2.5.3**.
8. OpenCV is **5.0.0.93**.
9. Project folder is `D:\AymashTain LED Remote`.
10. Backup is in `D:\AymashTain LED Remote\Safe copy (do not include in software run)`.
11. The app must stay free. No ads. No telemetry.

Protocol rules:

- Color command:
  `BC 04 06 HH HH SS SS 00 00 55`
- Brightness command:
  `BC 05 06 BB BB 00 00 00 00 55`
- Power:
  `BC01010155` ON, `BC01010055` OFF
- Captured static:
  `BC04010055`
- Captured Scroll setup:
  `BC0F010155`, `BC11010455`
- Captured Scroll data frames are in `mrstar_protocol.py`.
- Classic Magic Home:
  `CC2333`, `CC2433`, `56RRGGBB00F0AA`
- Experimental 7E commands must stay in a lab only.

Never do these:

- Never mix MR Star BC commands with Classic 56/CC commands.
- Never put brightness inside the color command.
- Never use `FFFF` as a white field.
- Never use `asyncio.create_task()` for color and brightness separately.
- Never send color and brightness in parallel.
- Always send color first, then brightness, with a small gap.
- Always serialize BLE writes through one queue.
- Never use hardcoded handles 13 or 19. Use UUID.
- Never claim the app can read actual LED state over BLE.
- Camera is the only physical verification unless readback is discovered.
- Camera stays local-only. No uploads.
- Never run Music Sync or Scroll during static color tests.
- Never auto-elevate to administrator.
- Never overwrite previous logs.
- Never provide partial patches unless the user explicitly asks for a small edit.
- Always provide a complete replacement file when replacing a file.
- Always run `python -m py_compile .\file.py` after replacement.

Important current status:

- `mrstar_protocol.py` is already corrected and verified.
- `hardware_test.py` is already corrected, compiled, and run.
- Hardware test passed at BLE transport level.
- `main.py` is still the old unsafe version.
- `main.py` still contains overlapping `asyncio.create_task()` calls.
- Latest event log shows overlapping Music Sync and two Scroll macros starting at the same time.
- Camera is still disabled: `CAMERA_ENABLED = False`.
- Hidden-feature lab is not built yet.
- Global serialized BLE queue is not built in `main.py` yet.
- Auto-save session log on close is not built in `main.py` yet.

User style:

- The user is not a developer.
- Give one point at a time.
- Use visual, simple, step-by-step instructions.
- Do not dump many instructions back to back.
- If you need the user to edit code, show exactly what to replace and where.
- Prefer full file replacement over manual edits.

Current priority order:

1. Replace `main.py` completely with v0.41 queued version.
2. Add global serialized BLE command queue.
3. Add ordered color → brightness sending.
4. Add automatic session log saving on close.
5. Add unified BLE/audio/camera/error log.
6. Run corrected `hardware_test.py` again if needed.
7. Add camera calibration and ROI.
8. Add hidden-feature laboratory.
9. Fix Music Sync.
10. Package later.

When asked to update a file:

- Read the current file fully.
- Apply the requested changes.
- Return the **full file** in one code block.
- Include a short compile command after the file.
- Do not ask the user to manually merge fragments.

When asked to debug:

- Ask for the exact error text.
- Ask for the relevant log file.
- Check `logs/` and `crash.log`.
- Do not guess if the log is available.

When asked to add a feature:

- Keep it compatible with the existing DB and remote profiles.
- Do not break Scroll.
- Do not break Classic compatibility.
- Keep experimental commands separate.

When asked to test:

- Use one strip first.
- Then all three.
- Use two-second holds.
- Save logs to `logs/`.
- Do not finish with OFF unless the user asks.

If the user says “add this to the bottom of a specific file”, append the relevant update note at the bottom of that file as a comment or markdown section, depending on file type.

## PROMPT END