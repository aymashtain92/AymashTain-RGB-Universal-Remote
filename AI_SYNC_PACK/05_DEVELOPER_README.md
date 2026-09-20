# AymashTain LED RGB Remote — Developer README

**Version:** v0.51 Alpha  
**Project path:** `D:\Coding projects\aymashtain-led-remote-Source`  
**Contact:** ayman.attia.ab@gmail.com  
**GitHub:** https://github.com/aymashtain92  
**Repo:** https://github.com/aymashtain92/AymashTain-RGB-Universal-Remote

---

## 1. What this is

Windows desktop app for controlling cheap BLE LED strips using the MR Star protocol family.

Target hardware:

- `GATT--DEMO` BLE devices
- Service: `00002022-0000-1000-8000-00805f9b34fb`
- Write characteristic: `0000fff3-0000-1000-8000-00805f9b34fb`

Known strips:

- `41:42:59:F1:C8:68`
- `41:42:43:E7:8B:F6`
- `41:42:F9:D7:45:B0`

---

## 2. Structure

```text
main.py                      → aymashtain.app:main
aymashtain/
  app.py                     bootstrap + qasync loop
  config.py                  Settings (JSON)
  events.py                  EventBus + SessionLogger
  paths.py                   data_dir, logs_dir, db_path
  ble/manager.py             BleManager (serialized per-device queue)
  protocol/mrstar.py         encode/decode, SCROLL_MACRO
  storage/db.py              profiles, buttons, history, devices
  vision/camera.py           CameraVerifier, Sample
  audio/engine.py            AudioEngine
  ui/main_window.py          MainWindow, menus, heartbeat
  ui/theme.py                dark / light
  ui/context.py              AppContext
  ui/widgets/                color_wheel, strip_preview
  ui/tabs/                   8 tabs
tests/                       pytest suite
AymashTain LED Remote.spec   PyInstaller spec
build_exe.bat, run.bat, repair.ps1, session.bat
ai_sync.py, update_github.bat
requirements.txt, pyproject.toml
README.md, CREDITS.md
AI_SYNC_PACK/
```

---

## 3. Environment

- Windows 10 Pro 10.0.19045.6466
- Python 3.14.7 (`C:\Users\aymas\AppData\Local\Python\pythoncore-3.14-64\python.exe`)
- Bleak 3.0.2
- NumPy 2.5.3
- OpenCV 5.0.0.93
- Data folder: `%LOCALAPPDATA%\AymashTain`
- Override: `AYMASHTAIN_DATA_DIR`

---

## 4. Install and run

```powershell
cd "D:\Coding projects\aymashtain-led-remote-Source"
python -m pip install -r .\requirements.txt
python .\main.py
```

Or double-click `run.bat`.

Repair (recreates `.venv`, reinstalls, checks Bluetooth / audio / camera):

```powershell
powershell -ExecutionPolicy Bypass -File .\repair.ps1
```

---

## 5. Compile check

After replacing any file:

```powershell
python -m py_compile .\main.py
python -m py_compile .\aymashtain\app.py
python -m py_compile .\aymashtain\ble\manager.py
python -m py_compile .\aymashtain\protocol\mrstar.py
```

No output = success.

---

## 6. Tests

```powershell
python -m pytest -q
python -m ruff check .
```

---

## 7. Logs and data

Data folder:

```text
%LOCALAPPDATA%\AymashTain
```

Contents:

- `config.json` — settings
- `aymashtain.db` — profiles, buttons, history, devices
- `logs/session_YYYYMMDD_HHMMSS.log`
- `logs/session_YYYYMMDD_HHMMSS.json`
- `logs/session_YYYYMMDD_HHMMSS.csv`

Do not overwrite old logs.

---

## 8. Build EXE

```powershell
.\build_exe.bat
```

Result: `dist\AymashTain LED Remote\AymashTain LED Remote.exe` plus `_internal\`.

Keep the `.exe` and the `_internal` folder together.

---

## 9. How to use AI updates

See `AI_SYNC_PACK\07_HOW_TO_USE_AI_SYNC.md`.  
Short version: upload the whole `AI_SYNC_PACK` folder + the file you want changed + the prompt from `02_UNIVERSAL_AI_PROMPT.md` and tell the AI what to do.

---

## 10. Current status

Working:

- App launches.
- 3/3 strips connect.
- 54 frames sent, 0 failed.
- BleManager serialized queue.
- Colour / brightness separated.
- Session logger.

Not built yet:

- Hidden-feature laboratory.
- Camera ROI visual calibration.
- Exposure / white balance lock.
- 150-LED preview.
- Profile import / export.
- About dialog with credits.
- Version reconciliation (`1.0.0` vs `v0.51 Alpha`).

---

## 11. Troubleshooting

- **No devices:** phone Bluetooth off, MR Star app closed, power-cycle strips.
- **No reaction:** confirm FFF3 UUID, `BC0406` colour, `BC0506` brightness.
- **Far strip drops:** raise inter-device delay in `config.json` or the GUI.
- **Pale colours:** brightness inside colour frame — check `protocol/mrstar.py`.
- **Camera:** install `opencv-python`, try camera index 0/1/2, calibrate ROI.
- **Audio:** pick the right device. Look for Line In / AUX / Stereo Mix / VoiceMeeter.

---

## 12. License

MIT License. See `LICENSE.txt`.  
Third-party libraries keep their own licenses. See `CREDITS.md`.

---

## 13. Contact

- Email: ayman.attia.ab@gmail.com
- GitHub: https://github.com/aymashtain92

When reporting an issue, include:

- Windows version
- Python version
- File name
- Exact error text
- Log from `%LOCALAPPDATA%\AymashTain\logs\`
- What you did before the error