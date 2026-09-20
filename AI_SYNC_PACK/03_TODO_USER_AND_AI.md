# TODO — User and AI

This is the easy-to-read list of things not done yet.

---

## A. Immediate next steps

- [ ] Replace `main.py` completely with v0.41 queued version.
- [ ] Add global serialized BLE command queue.
- [ ] Send color first, brightness second, with 100 ms gap.
- [ ] Add automatic session log saving on close.
- [ ] Add unified BLE/audio/camera/error log.
- [ ] Run corrected `hardware_test.py`.
- [ ] Confirm all 3 strips react correctly.
- [ ] Confirm far strip stays connected.
- [ ] Confirm 0% brightness turns strip dark.
- [ ] Confirm final red 100% is restored.

## B. Camera

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

## C. Hidden-feature lab

- [ ] Add command catalog.
- [ ] Add safe candidate generator.
- [ ] Send one candidate at a time.
- [ ] Wait and capture camera result.
- [ ] Record command, device, timestamp, BLE result, RGB, brightness, white contamination, notes.
- [ ] Add stop button.
- [ ] Add emergency stop.
- [ ] Add conservative limits.
- [ ] Never brute-force without emergency stop.

## D. Main app

- [ ] Change all branding from LumenForge to AymashTain.
- [ ] Set version to v0.41.
- [ ] Set `BRIGHTNESS_MIN = 0`.
- [ ] Set `BRIGHTNESS_MAX = 1000`.
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

## E. Music sync

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

## F. Protocol / testing

- [ ] Confirm white/neutral command.
- [ ] Confirm static command across all strips.
- [ ] Confirm Scroll behavior on all strips.
- [ ] Confirm M1 behavior.
- [ ] Confirm far strip disconnect cause.
- [ ] Confirm power source stability.
- [ ] Confirm no command overlap.
- [ ] Confirm logs are complete.

## G. Packaging later

- [ ] Update `requirements.txt`.
- [ ] Update installer to Python 3.14.
- [ ] Build EXE with PyInstaller.
- [ ] Test EXE on clean Windows.
- [ ] Publish GitHub release.
- [ ] Add LICENSE.
- [ ] Add developer README.
- [ ] Add user README later.

## H. Legal & User Documentation

- [ ] Create `README_USER.md` (non-developer guide).
- [ ] Create `LEGAL.md` (terms, disclaimer, privacy, free-software pledge).
- [ ] Add exposure lock controls to Camera tab (Lock Exposure checkbox, Exposure slider, Lock White Balance checkbox).
- [ ] Cap brightness slider to 900 max in the UI to prevent controller crashing.
- [ ] Add warning label next to brightness slider: "Above 900 may cause controller lag."