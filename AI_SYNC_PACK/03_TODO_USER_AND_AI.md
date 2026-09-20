# TODO — User and AI

This is the easy-to-read list of things not done yet.

---

## A. Completed already

- [x] `mrstar_protocol.py` replaced and verified.
- [x] Color command verified: `BC0406000003E8000055`
- [x] Brightness command verified: `BC0506040000000055`
- [x] Decoder shows `confidence: documented`.
- [x] `hardware_test.py` replaced and compiled.
- [x] `hardware_test.py` run on hardware.
- [x] All 3 strips connected.
- [x] All commands accepted.
- [x] Hardware test logs saved:
  - `hardware_test_20260919_211043.log`
  - `hardware_test_20260919_211043.json`
  - `hardware_test_20260919_211043.csv`
- [x] Full backup made by user.

---

## B. Immediate next steps

- [ ] Replace `main.py` completely with v0.41 queued version.
- [ ] Add global serialized BLE command queue.
- [ ] Send color first, brightness second, with 100 ms gap.
- [ ] Remove old `asyncio.create_task()` color/brightness overlap.
- [ ] Add automatic session log saving on close.
- [ ] Add unified BLE/audio/camera/error log.
- [ ] Prevent Music Sync from flooding BLE.
- [ ] Prevent two Scroll macros from running at once.
- [ ] Confirm far strip stays connected.
- [ ] Confirm 0% brightness turns strip dark.
- [ ] Confirm final red 100% is restored.
- [ ] Update `requirements.txt` for Python 3.14.7 and `bleak>=0.22`.
- [ ] Rename all LumenForge references to AymashTain.
- [ ] Rename launcher to `Launch AymashTain LED RGB Remote.bat`.

---

## C. Camera

- [ ] Add camera selection.
- [ ] Add camera preview.
- [ ] Add region selection for Strip 1.
- [ ] Add region selection for Strip 2.
- [ ] Add region selection for Strip 3.
- [ ] Save calibration locally.
- [ ] Capture after each command.
- [ ] Measure RGB.
- [ ] Measure brightness.
- [ ] Measure white contamination.
- [ ] Report PASS / FAIL.
- [ ] Export CSV and JSON.
- [ ] Keep camera local-only.
- [ ] Add exposure lock.
- [ ] Add white balance lock.

---

## D. Hidden-feature lab

- [ ] Add command catalog.
- [ ] Add safe candidate generator.
- [ ] Send one candidate at a time.
- [ ] Wait and capture camera result.
- [ ] Record command, device, timestamp, BLE result, RGB, brightness, white contamination, notes.
- [ ] Add stop button.
- [ ] Add emergency stop.
- [ ] Add conservative limits.
- [ ] Never brute-force without emergency stop.

---

## E. Main app

- [ ] Change all branding from LumenForge to AymashTain.
- [ ] Set version to v0.41.
- [ ] Set `BRIGHTNESS_MIN = 0`.
- [ ] Set `BRIGHTNESS_MAX = 1000` or 900 depending on final test.
- [ ] Remove old `FFFF` white logic.
- [ ] Use `encode_mrstar_color` and `encode_mrstar_brightness`.
- [ ] Add per-device write results.
- [ ] Add configurable inter-device delay.
- [ ] Add visible RGB connection pulse.
- [ ] Add safe reconnect.
- [ ] Add safer shutdown.
- [ ] Add automatic log save on close.
- [ ] Add File menu.
- [ ] Add View menu.
- [ ] Add Help menu.
- [ ] Add About dialog with email and GitHub.
- [ ] Add profile import/export.
- [ ] Add compact startup size.
- [ ] Add 150-LED horizontal strip view.
- [ ] Add better audio device names.
- [ ] Add AUX/Line-In separation.
- [ ] Add VoiceMeeter loopback support.
- [ ] Add media player later.
- [ ] Add equalizer presets later.
- [ ] Add screen/audio reactive effects later.

---

## F. Music sync

- [ ] Use serialized command queue.
- [ ] Add rate limiting.
- [ ] Add duplicate suppression.
- [ ] Add real FFT spectrum bars.
- [ ] Fix sensitivity.
- [ ] Fix speed.
- [ ] Fix brightness cap.
- [ ] Fix strobe.
- [ ] Fix pulse.
- [ ] Fix rainbow.
- [ ] Fix beat flash.
- [ ] Stop cleanly at song end.
- [ ] Do not leave lights off after song.
- [ ] Log audio and LED timing together.
- [ ] Prevent Scroll/M1 interference.

---

## G. Protocol / testing

- [ ] Confirm white/neutral command.
- [ ] Confirm static command across all strips.
- [ ] Confirm Scroll behavior on all strips.
- [ ] Confirm M1 behavior.
- [ ] Confirm far strip disconnect cause.
- [ ] Confirm power source stability.
- [ ] Confirm no command overlap.
- [ ] Confirm logs are complete.

---

## H. Packaging later

- [ ] Update `requirements.txt`.
- [ ] Update installer to Python 3.14.
- [ ] Build EXE with PyInstaller.
- [ ] Test EXE on clean Windows.
- [ ] Publish GitHub release.
- [ ] Add LICENSE.
- [ ] Add developer README.
- [ ] Add user README later.