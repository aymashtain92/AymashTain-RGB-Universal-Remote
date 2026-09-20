# AymashTain LED RGB Remote — Developer README

**Version:** v0.51 Alpha  
**Status:** Active development  
**Project folder:** `D:\AymashTain LED Remote`  
**Contact:** ayman.attia.ab@gmail.com  
**GitHub:** https://github.com/aymashtain92

---

## What this is

Windows desktop app for controlling cheap BLE LED strips that use the MR Star app and related clone controllers.

Target hardware:

- `GATT--DEMO` BLE devices
- Service: `00002022-0000-1000-8000-00805f9b34fb`
- Write characteristic: `0000fff3-0000-1000-8000-00805f9b34fb`

Known strips:

- `41:42:59:F1:C8:68`
- `41:42:43:E7:8B:F6`
- `41:42:F9:D7:45:B0`

---

## Quick start

**For users:**  
Run `AymashTain LED Remote.exe`. Keep the `_internal` folder next to it.

**For developers:**

```powershell
cd "D:\AymashTain LED Remote"
python -m pip install -r .\requirements.txt
python .\main.py
```

**Hardware test:**

```powershell
python .\hardware_test.py
```

**Compile check:**

```powershell
python -m py_compile .\main.py
python -m py_compile .\mrstar_protocol.py
python -m py_compile .\hardware_test.py
```

---

## How to use AI updates

This project uses an `AI_SYNC_PACK` folder to keep every AI assistant in sync.  
The full step‑by‑step guide is in:

```text
AI_SYNC_PACK\07_HOW_TO_USE_AI_SYNC.md
```

Read that file first. It tells you exactly what to upload to an AI, what prompt to use, and how to update the pack after every change.

---

## License

This project is released under the **MIT License**.  
See `LICENSE.txt` for the full text.

Third‑party libraries (PySide6, bleak, qasync, sounddevice, numpy, opencv‑python, etc.) have their own licenses.  
Check each library’s documentation before redistribution.

---

## Current status

- `mrstar_protocol.py` — verified.
- `hardware_test.py` — compiled and run. Passed at BLE transport level.
- `main.py` — still old, unsafe queue. Replacement pending.
- Camera — disabled, not calibrated.
- Hidden‑feature lab — not built.
- Global BLE queue — not built in `main.py`.
- Auto‑save logs on close — not built in `main.py`.

---

## Logs

Logs are in:

```text
D:\AymashTain LED Remote\logs\
```

Latest hardware test:

```text
hardware_test_20260919_211043.log
hardware_test_20260919_211043.json
hardware_test_20260919_211043.csv
```

Do not overwrite old logs.

---

## Troubleshooting

See the full guide in `07_HOW_TO_USE_AI_SYNC.md`.  
Quick tips:

- No devices: turn off phone Bluetooth, close MR Star app, power‑cycle strips.
- No reaction: confirm FFF3 UUID, use `BC0406` color, `BC0506` brightness.
- Far strip disconnects: increase inter‑device delay.
- Camera: install `opencv-python`, try index 0/1/2.
- Audio: look for Line In / AUX / Stereo Mix / VoiceMeeter.

---

## Contact

Email: ayman.attia.ab@gmail.com  
GitHub: https://github.com/aymashtain92