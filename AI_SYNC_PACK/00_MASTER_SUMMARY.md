# AymashTain LED RGB Remote — Master Summary for AI Assistants

**Version target:** v0.51 Alpha  
**Project path:** `D:\Coding projects\aymashtain-led-remote-Source`  
**GitHub:** https://github.com/aymashtain92/AymashTain-RGB-Universal-Remote  
**Contact:** ayman.attia.ab@gmail.com  
**Owner:** aymashtain92  
**Free software. No ads. No telemetry.**

---

## 1. What this project is

Windows desktop app for controlling cheap BLE LED strips that use the **MR Star app** and related clone controllers.

Three physical strips:

- `41:42:59:F1:C8:68`
- `41:42:43:E7:8B:F6`
- `41:42:F9:D7:45:B0`

They advertise as `GATT--DEMO` and use:

- Service: `00002022-0000-1000-8000-00805f9b34fb`
- Write characteristic: `0000fff3-0000-1000-8000-00805f9b34fb`

This project is a **package**, not a single `main.py`. The real code is inside the `aymashtain/` folder.

---

## 2. Environment

- Windows 10 Pro version 10.0.19045.6466
- Python 3.14.7
- Bleak 3.0.2
- NumPy 2.5.3
- OpenCV 5.0.0.93
- Project path: `D:\Coding projects\aymashtain-led-remote-Source`
- Data path (Windows): `%LOCALAPPDATA%\AymashTain`
- Override with env var: `AYMASHTAIN_DATA_DIR`

---

## 3. Project structure

```text
main.py                      Launcher → aymashtain.app:main
aymashtain/
  __init__.py                APP_NAME, APP_SLUG, APP_VERSION
  app.py                     bootstrap + qasync event loop
  config.py                  Settings dataclass (JSON)
  events.py                  EventBus + SessionLogger
  paths.py                   data_dir, logs_dir, db_path
  ble/
    manager.py               BleManager (serialized queue PER device)
  protocol/
    mrstar.py                encode_color, encode_brightness, decode
  storage/
    db.py                    profiles, buttons, history, devices
  vision/
    camera.py                CameraVerifier, Sample, analyse_region
  audio/
    engine.py                AudioEngine, bands_to_rgb
  ui/
    context.py               AppContext passed to every tab
    theme.py                 dark/light stylesheet
    main_window.py           MainWindow, menus, heartbeat
    widgets/
      color_wheel.py         HSV wheel
      strip_preview.py       24-LED preview (needs 150-LED version)
    tabs/
      connect_tab.py
      remote_tab.py
      music_tab.py
      sweep_tab.py
      camera_tab.py
      console_tab.py
      lab_tab.py
      events_tab.py
tests/
  test_protocol.py
  test_storage_and_events.py
  test_vision_and_audio.py
AymashTain LED Remote.spec  PyInstaller build spec
build_exe.bat
run.bat
session.bat
session.py
ai_sync.py
update_github.bat
requirements.txt
pyproject.toml
README.md
CREDITS.md
AI_SYNC_PACK/               ← this folder
```

---

## 4. What already works (do not remove)

- **Serialized BLE queue per device** in `ble/manager.py`. Every device owns its own `asyncio.Queue` and worker task. Colour and brightness cannot interleave.
- **Ordered colour → brightness** in `BleManager.set_color()`. Colour first, then brightness.
- **Session logger** writes `.log`, `.json`, `.csv` on every event.
- **Auto-save on close** via `closeEvent` → `session_logger.flush_json()`.
- **Auto-reconnect** with backoff.
- **8 tabs** — Connect, Remote, Music & Media, Sweep, Camera, Console, Lab, Events.
- **Camera sampling** with white-contamination scoring.
- **Sweep tab** with optional camera verification.
- **Emergency stop** via Esc key and Control menu.
- **PyInstaller spec** with Qt module exclusions.
- **3/3 strips connect, 54 frames sent, 0 failed** (verified from running app).

Do **not** replace this with a flat single-file `main.py`. The package is better.

---

## 5. Confirmed protocol

### Colour
```text
BC 04 06 HH HH SS SS 00 00 55
```
Hue 0–359, saturation 0–1000, reserved `0000`.

Examples:
```text
Red:   BC0406000003E8000055
Green: BC0406007803E8000055
Blue:  BC040600F003E8000055
```

### Brightness (separate command)
```text
BC 05 06 BB BB 00 00 00 00 55
```
0–1024. Examples:
```text
100% = BC0506040000000055
75%  = BC0506030000000055
50%  = BC0506020000000055
25%  = BC0506010000000055
0%   = BC0506000000000055
```

### Power
```text
ON  = BC01010155
OFF = BC01010055
```

### Captured static / exit dynamic mode
```text
BC04010055
```

### Captured Scroll macro (setup + 25 frames + end)
See `protocol/mrstar.py` → `SCROLL_MACRO`. Do not modify.

### Classic Magic Home (separate family)
```text
ON  = CC2333
OFF = CC2433
RGB = 56RRGGBB00F0AA
```

---

## 6. Current status

### Working
- App launches, connects to all 3 strips, sends frames.
- BleManager queue serializes correctly.
- Colour / brightness separated correctly.
- Session logs saved.

### Not built yet
- **Hidden-feature laboratory** — send one candidate hex, wait, capture camera sample, log it, emergency stop. Lab tab only diffs right now.
- **Camera ROI visual calibration** — region is a number field; no live rectangle overlay picker.
- **Camera exposure / white balance lock** — not exposed.
- **150-LED horizontal preview** — current `StripPreview` is 24 LEDs.
- **Profile import / export** — not implemented.
- **About dialog with credits** — not implemented.
- **Version clarity** — code says `1.0.0`, release is `v0.51 Alpha`. Pick one and stick to it.

---

## 7. Versioning rule

Release name: **v0.51 Alpha** (from user).
Code constant: `aymashtain/__init__.py` → `APP_VERSION`.
Keep them consistent. Right now they disagree.

---

## 8. Golden rules for any AI reading this

1. Never mix MR Star BC commands with Classic 56/CC commands.
2. Never put brightness inside the colour frame.
3. Never use `FFFF` as a white field.
4. Never use `asyncio.create_task()` to fire colour and brightness in parallel.
5. Keep the per-device serialized queue in `BleManager`. Do not remove it.
6. Never run Music Sync or Scroll during static colour tests.
7. Never claim the app can read actual LED state over BLE.
8. Camera stays local-only. No uploads.
9. Python is 3.14.7. Do not use `py -3.12`.
10. Provide full replacement files, not partial patches.
11. Always run `python -m py_compile .\file.py` after replacement.
12. Do not auto-elevate to administrator.
13. Do not overwrite logs.
14. Preserve captured Scroll frames exactly.
15. This project is free forever. No ads. No telemetry.