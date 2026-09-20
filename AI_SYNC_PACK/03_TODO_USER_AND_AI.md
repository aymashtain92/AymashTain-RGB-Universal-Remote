# TODO — User and AI

Easy-to-read list of what is done and what is left.

---

## A. Done

- [x] `mrstar_protocol.py` corrected and verified.
- [x] Colour command verified: `BC0406000003E8000055`.
- [x] Brightness command verified: `BC0506040000000055`.
- [x] Decoder shows `confidence: documented`.
- [x] Hardware test passed at BLE transport level (2026-09-19 21:10).
- [x] Logs saved:
  - `hardware_test_20260919_211043.log`
  - `hardware_test_20260919_211043.json`
  - `hardware_test_20260919_211043.csv`
- [x] Project rebuilt as a package `aymashtain/` (Devin AI).
- [x] Per-device serialized BLE queue in `ble/manager.py`.
- [x] Ordered colour → brightness in `BleManager.set_color()`.
- [x] Session logger with `.log`, `.json`, `.csv`.
- [x] 8 tabs: Connect, Remote, Music & Media, Sweep, Camera, Console, Lab, Events.
- [x] Auto-reconnect.
- [x] Emergency stop (Esc + Control menu).
- [x] App confirmed running: 3/3 strips connect, 54 frames sent, 0 failed.
- [x] PyInstaller spec, `build_exe.bat`, `run.bat`, `repair.ps1`.
- [x] `CREDITS.md` added.
- [x] `.gitignore` cleaned.
- [x] GitHub sync working.

---

## B. Immediate next: hidden-feature laboratory

- [ ] Add a new section to `aymashtain/ui/tabs/lab_tab.py`.
- [ ] Candidate hex list input (one per line, or generated from a template).
- [ ] Send one candidate at a time, with a small delay.
- [ ] After each send, wait 2 seconds, capture a camera sample.
- [ ] Log: hex, BLE result, observed RGB, white contamination, timestamp.
- [ ] Emergency stop button + Esc integration.
- [ ] Export results to CSV and JSON.
- [ ] Conservative limits (no brute force of thousands at once).
- [ ] Warn the user before starting.

---

## C. Camera improvements

- [ ] Visual ROI picker for Strip 1 / 2 / 3 in `camera_tab.py`.
- [ ] Live rectangle overlay on the preview.
- [ ] Save ROI to `config.json` on change.
- [ ] Exposure lock toggle.
- [ ] White balance lock toggle.
- [ ] Exposure value slider.
- [ ] "Calibrate" button that averages 30 frames of a static colour and stores a baseline.

---

## D. UI improvements

- [ ] Replace 24-LED preview with a 150-LED horizontal view in `widgets/strip_preview.py`.
- [ ] Compact startup size (currently 1180×840).
- [ ] About dialog with `CREDITS.md` content and GitHub link.
- [ ] Profile import / export in `remote_tab.py`.
- [ ] Reconcile version string: code says `1.0.0`, release is `v0.51 Alpha`.

---

## E. Music & Media

- [ ] Confirm microphone path works on user's PC.
- [ ] Confirm WASAPI loopback fallback works on user's PC.
- [ ] Confirm "playing file" source works.
- [ ] Rate-limit BLE writes (already partly done via queue).
- [ ] Add duplicate-colour suppression.
- [ ] Add "ensure on" before starting music.

---

## F. Testing

- [ ] Run hidden-feature lab on one strip only first.
- [ ] Then all three.
- [ ] Confirm no Scroll / M1 corruption after a lab session.
- [ ] Confirm far strip stays connected with `inter_device_delay_ms = 60`.
- [ ] Re-test camera with new ROI.

---

## G. Packaging later

- [ ] Reconcile version: `v0.51 Alpha`.
- [ ] Rebuild EXE from the package.
- [ ] Test on a clean Windows machine.
- [ ] Publish GitHub release with the EXE + `_internal` folder.
- [ ] Verify downloaded ZIP runs.