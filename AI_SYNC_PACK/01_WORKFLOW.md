# AymashTain LED RGB Remote — Workflow and Timeline

Dates are based on timestamps in the provided conversations and logs.  
Some dates are approximate because several AI chats overlapped.

---

## 2026-09-17 — First troubleshooting and protocol capture

**User**
- Asked why MR Star LED strips lag behind music.
- Corrected multiple AIs: the strips use the **USB device mic**, not the phone mic.
- Said they do not want to buy new hardware.
- Wanted PC control for MR Star strips.
- Provided btsnoop HCI log: `btsnoop_hci_260917_192456.log`.

**Meta AI**
- First suggested WLED/LedFx and new hardware.
- User corrected: no new hardware.
- Meta AI then suggested PC app routes, LumaBLE, mr_star_ble, Android emulator.

**DeepSeek**
- Parsed btsnoop log.
- Found exact Scroll sequence.
- Found opcodes:
  - `BC11 01 XX 55` — pattern slot
  - `BC06 02 00 XX 55` — speed/param
  - `BC0F 01 XX 55` — flag
  - `BC01 01 XX 55` — toggle
- Built `RGB_controller_v2.py`.
- Confirmed Scroll worked on one strip.
- Confirmed FFF3 write handle = 13.

**User**
- Tested hardware.
- Found ON/OFF/color failed with old Triones commands.
- Found only Scroll worked.

**DeepSeek**
- Found color and brightness are separate commands.
- Recommended `BC0406...` for color and `BC0506...` for brightness.

---

## 2026-09-18 — App building and bug discovery

**Claude**
- Built LumenBench HTML artifact.
- Built BLE Light Command Deck.
- Included MR Star and Classic Magic Home.
- Included remote builder, music sync, IR notes.

**User**
- Reported camera not working, color wheel reversed, strips not changing.
- Reported indicators not syncing.
- Asked for connection blink.
- Asked for better logs.
- Asked for hidden feature testing.

**Gemini Studio AI**
- Built React/PySide-style app.
- Added many tabs: Connect, Remote, Music, Camera, Sweep, Console, Lab, Events.
- Added strip canvas with 450 nodes.
- Had bugs: camera, color wheel, BLE, label overlap.
- User reported scan not finding devices.
- Gemini changed core, user said it broke.
- User asked for Python `main.py` again.

**User**
- Demanded full files, not partial edits.
- Said editing code is very hard.
- Asked for auto-save logs.
- Asked for camera analysis.
- Asked for all hidden features.

---

## 2026-09-19 — GitHub sync, hardware test, protocol correction

**User**
- Provided current files:
  - `main.py`
  - `mrstar_protocol.py`
  - `hardware_test.py`
  - `requirements.txt`
  - `Launch AymashTain LED RGB Remote.bat`
  - `install_lumenforge.ps1`
  - `README.md`
- Provided logs:
  - `events_20260919_201738.txt`
  - hardware test logs
- Provided GitHub repo: `https://github.com/aymashtain92/AymashTain-RGB-Universal-Remote`

**GitHub Copilot**
- Reviewed code.
- Found:
  - Event loop shutdown risky
  - Music loopback can crash
  - Audio analysis too lossy
  - `load_audio()` sticky fail
  - `closeEvent()` blocking
- Then found the bigger issue:
  - Color and brightness must be separate.
  - `BC0406HHHHSSSS000055`
  - `BC0506BBBB0000000055`
  - Do not use `FFFF` white field.

**User**
- Ran hardware test.
- All 3 strips connected.
- All commands accepted.
- Far strip disconnected sometimes.
- M1/Scroll got disturbed.
- Brightness too fast to see.
- Asked for camera and better logs.

**DeepSeek**
- Recommended serialized command queue.
- Recommended auto-save logs.
- Recommended local camera only.
- Recommended no final OFF.
- Recommended two-second holds.

**User**
- Replaced `mrstar_protocol.py` with corrected version.
- Verified:
  - `BC0406000003E8000055`
  - `BC0506040000000055`
  - `confidence: documented`
- Replaced `hardware_test.py` with corrected version.
- Compiled both files.

**Assistant / ChatGPT**
- Confirmed protocol file correct.
- Confirmed `hardware_test.py` compiles.
- Confirmed `main.py` is still old and unsafe.
- Started creating AI sync pack.

**Later on 2026-09-19**
- User made full backup as restore point.
- User asked where `main.py` replacement is.
- Assistant admitted it had not yet provided the full `main.py`.
- User ran:
  - `python -m py_compile .\hardware_test.py`
  - `python -m py_compile .\main.py`
- Both compiled.
- Assistant confirmed `main.py` is still the old unsafe version.
- User ran corrected `hardware_test.py`.
- Hardware test passed at BLE transport level.
- All 3 strips connected.
- All commands accepted.
- Logs saved:
  - `hardware_test_20260919_211043.log`
  - `hardware_test_20260919_211043.json`
  - `hardware_test_20260919_211043.csv`

---

## 2026-09-20 — Current sync pack update

**User**
- Asked whether `00_`–`06_` files are 100% up to date.
- Asked whether to add updates at start or end.
- Asked for full updated files to copy-paste and overwrite.

**ChatGPT / Current Assistant**
- Confirmed the pack is not 100% up to date.
- Listed missing updates:
  - `mrstar_protocol.py` verified.
  - `hardware_test.py` compiled and run.
  - Hardware test passed at BLE transport level.
  - `main.py` still old and unsafe.
  - Latest event log shows overlapping Music Sync and duplicate Scroll macros.
  - Camera still disabled.
  - Hidden-feature lab still not built.
  - Global queue and auto-save logs still not built.
- Providing full replacement content for `00_` through `06_`.
- Next real step: replace `main.py` completely with v0.41 queued version.

---

## Who did what

| Date | AI / Person | Contribution |
|---|---|---|
| 2026-09-17 | User | Provided btsnoop log, corrected USB mic assumption |
| 2026-09-17 | DeepSeek | Reverse-engineered Scroll, found opcodes, built controller v2 |
| 2026-09-17 | Meta AI | Suggested PC control routes, LumaBLE, mr_star_ble |
| 2026-09-18 | Claude | Built LumenBench HTML artifact |
| 2026-09-18 | Gemini Studio | Built React/PySide app with many tabs |
| 2026-09-18 | User | Tested, reported bugs, demanded full files |
| 2026-09-19 | GitHub Copilot | Found color/brightness split, recommended MR Star library |
| 2026-09-19 | DeepSeek | Recommended queue, auto-save, camera |
| 2026-09-19 | User | Replaced protocol and hardware test, compiled, ran hardware test |
| 2026-09-19 | ChatGPT / Assistant | Confirmed protocol, hardware test, main.py still old |
| 2026-09-20 | ChatGPT / Current | Updated AI sync pack, next full `main.py` rebuild |