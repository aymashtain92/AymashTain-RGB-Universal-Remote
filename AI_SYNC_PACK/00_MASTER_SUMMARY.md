# AymashTain LED RGB Remote — Master Summary for AI Assistants

Version: v0.41 target  
Project folder: D:\AymashTain LED Remote  
Backup folder: D:\AymashTain LED Remote\Safe copy (do not include in software run)  
GitHub: https://github.com/aymashtain92/AymashTain-RGB-Universal-Remote  
Contact email: ayman.attia.ab@gmail.com  
Owner: aymashtain92  
Free software. No ads. No telemetry. 100% free now and in future.

---

## 1. What this project is

AymashTain LED RGB Remote is a Windows desktop app for controlling cheap generic BLE LED strips that use the **MR Star app** and related clone controllers.

The user has **3 physical LED strips**:

- `41:42:59:F1:C8:68`
- `41:42:43:E7:8B:F6`
- `41:42:F9:D7:45:B0`

They advertise as `GATT--DEMO` and use the BLE write characteristic:

- Service: `00002022-0000-1000-8000-00805f9b34fb`
- Write characteristic: `0000fff3-0000-1000-8000-00805f9b34fb`

The controller family is **MR Star / Triones / Tuya-like**, but the exact working protocol is the one captured from the phone btsnoop log.

---

## 2. Current environment

- Windows 10 Pro version 10.0.19045.6466
- Python 3.14.7 installed
- Python executable: `C:\Users\aymas\AppData\Local\Python\pythoncore-3.14-64\python.exe`
- Bleak 3.0.2 installed
- NumPy 2.5.3 installed
- OpenCV 5.0.0.93 installed
- Project path: `D:\AymashTain LED Remote`
- Backup path: `D:\AymashTain LED Remote\Safe copy (do not include in software run)`

Important: do not assume Python 3.12. The real machine uses Python 3.14.7.  
Installers and dependency files must accept Python 3.14.

---

## 3. Current file status

| File | Status | Notes |
|---|---|---|
| `mrstar_protocol.py` | UPDATED and verified | Correct documented MR Star color/brightness split. Has `confidence` decoding. |
| `hardware_test.py` | UPDATED and compiles | Uses protocol functions, sequential writes, two-second holds, saves logs. Not yet hardware-run after update. |
| `main.py` | OLD / NOT UPDATED | Still contains overlapping `asyncio.create_task()` calls. No global queue. No auto-save session log. Still branded LumenForge in many places. |
| `requirements.txt` | OLD | Needs update to Python 3.14-compatible pins and missing packages. |
| `Launch AymashTain LED RGB Remote.bat` | Present | Uses `pythonw` or `python`. |
| `install_lumenforge.ps1` | OLD | Still references LumenForge and Python 3.12 assumptions. |
| `README.md` | OLD | Still LumenForge / old protocol notes. |
| `lumenforge.db` | Present | Old database. Can be backed up and migrated. |
| `logs/` | Present | Contains hardware test logs. |
| `events_20260919_201738.txt` | Present | Old event log. |

---

## 4. Confirmed working protocol

### 4.1 Documented MR Star color

Format:

```text
BC 04 06 HH HH SS SS 00 00 55

Where:

HH HH = hue, big-endian, 0–359

SS SS = saturation, big-endian, 0–1000

00 00 = reserved

55 = terminator

Examples:

text
Red:   BC0406000003E8000055
Green: BC0406007803E8000055
Blue:  BC040600F003E8000055
4.2 Documented MR Star brightness
Brightness is a separate command.

Format:

text
BC 05 06 BB BB 00 00 00 00 55
Where:

BB BB = brightness, big-endian, 0–1024

00 00 00 00 = reserved

55 = terminator

Examples:

text
100% = BC0506040000000055
75%  = BC0506030000000055
50%  = BC0506020000000055
25%  = BC0506010000000055
0%   = BC0506000000000055
4.3 Power
text
ON  = BC01010155
OFF = BC01010055
4.4 Captured static / exit dynamic mode
text
BC04010055
This is captured, not fully documented. Use carefully.

4.5 Captured Scroll sequence
Setup:

text
BC0F010155
BC11010455
Data frames:

text
BC0406000003E8000055
BC0406013E0032000055
BC04060131002B000055
BC040600E200A8000055
BC040600E400B8000055
BC040600E60091000055
BC040600E90046000055
BC040600F00027000055
BC040600F00023000055
BC040600F00023000055
BC040600FF003E000055
BC040601050081000055
BC0406011B00EB000055
BC0406013D01A3000055
BC0406014D0230000055
BC04060161026F000055
BC0406001B02FC000055
BC0406002C0372000055
BC0406003E02E1000055
BC0406005A0215000055
BC0406008701BF000055
BC040600B00215000055
BC040600C90296000055
BC040600DF0314000055
BC040600F7033B000055
End:

text
BC0F010155
BC11010455
This is experimental/captured. It must be isolated from normal color tests.

4.6 Classic Magic Home / Triones compatibility
Not the same protocol.

text
ON  = CC2333
OFF = CC2433
Color = 56RRGGBB00F0AA
Keep separate. Do not mix with MR Star BC commands.

4.7 Experimental 7E commands
Not confirmed. Keep in a lab only.

Examples:

text
7E00040101000000EF
7E00040102000000EF
7E...
Never use in normal remote or music mode.

5. The white contamination bug
Earlier builds used:

python
w = 0xFFFF if pure else 0x0000
return f"BC0406{hue:04X}{bri:04X}{w:04X}55"
This mixed brightness and a fake white channel into the color command.

Result:

Red looked pink/white

Green/blue looked pale

Yellow looked yellow-green

Music modes dominated by white

Static button produced yellow-greenish color

Correct fix:

Color command is only BC0406HHHHSSSS000055

Brightness is a separate BC0506BBBB0000000055

Do not use FFFF as a white field

Achromatic/white should be handled as a separate neutral command or tested separately

6. Hardware test results so far
The original hardware_test.py connected to all 3 strips and all writes were accepted:

41:42:59:F1:C8:68 connected using FFF3

41:42:43:E7:8B:F6 connected using FFF3

41:42:F9:D7:45:B0 connected using FFF3

Logs saved in:

text
D:\AymashTain LED Remote\logs\hardware_test_20260919_211043.log
D:\AymashTain LED Remote\logs\hardware_test_20260919_211043.json
D:\AymashTain LED Remote\logs\hardware_test_20260919_211043.csv
User visual observations from earlier tests:

Connection RGB pulse was not visible in old test.

Test 1 primary colors were correct.

Brightness changes happened too fast to see clearly.

Far strip disconnected during some tests.

M1/Scroll was disturbed by rapid test commands.

Magenta sometimes appeared yellow.

Scroll/music kept flipping.

Camera would help because user cannot reliably judge shades.

The corrected hardware_test.py has not yet been run on hardware.

7. Current known problems in main.py
main.py still has:

asyncio.create_task(self.send_hex(color_hex))

asyncio.create_task(self.send_hex(brightness_hex))

This allows color and brightness to arrive out of order.

It also:

Has no global serialized command queue

Allows Music Sync to flood BLE

Allows two Scroll macros to start at once

Does not automatically save session logs on close

Still uses BRIGHTNESS_MIN = 100, so true zero brightness is impossible

Still uses old LumenForge branding in many places

Has no camera calibration

Has no hidden-feature lab

Has no per-device result model in the GUI

Has no safe shutdown for qasync

8. Required v0.41 architecture
The next main.py must include:

AymashTain branding

Version v0.41

One global serialized BLE command queue

Ordered color → brightness sending

Per-device write results

Three-strip broadcast support

Configurable inter-device delay

Visible RGB connection confirmation

Two-second hardware-test holds

No automatic final OFF

No M1/Scroll reset during static-color tests

Local-only OpenCV camera analysis

Camera preview and region selection

JSON, CSV, and text logs

Automatic event-log saving on application close

Command classification/cataloguing

Correct zero-brightness handling

Safer shutdown

AUX/Line-In naming improvements

No automatic administrator elevation

Python 3.14-compatible installer checks

9. Required hardware test architecture
The corrected hardware_test.py must:

Connect all three strips

Use FFF3

Send commands sequentially

Wait two seconds between visible stages

Record every device result separately

Not send a final OFF command

Optionally sample one camera region locally

Save JSON, CSV, and text logs automatically

Never upload anything

Corrected test steps:

text
1. Connect all selected strips
2. RGB connection confirmation pulse
3. Red 100% — hold 2 seconds
4. Green 100% — hold 2 seconds
5. Blue 100% — hold 2 seconds
6. Red 100% — hold 2 seconds
7. Red 75% — hold 2 seconds
8. Red 50% — hold 2 seconds
9. Red 25% — hold 2 seconds
10. Red 0% — hold 2 seconds
11. Restore red 100% — hold 2 seconds
12. Leave the lights ON
Each command order:

text
power/color command
wait 100 ms
brightness command
wait 2 seconds
camera capture
No Scroll, M1, experimental 7E, or automatic OFF in this test.

10. Camera plan
Camera must be local-only.

No internet. No cloud. No uploads.

Required:

Select camera

Show live preview

Define Strip 1 region

Define Strip 2 region

Define Strip 3 region

Run synchronized test

Capture each region after every command

Export results to CSV and JSON

Measure average RGB

Measure brightness

Measure white contamination

Compare expected vs observed color

Report PASS / FAIL

Example result:

text
Expected: pure red
Observed: RGB(224, 36, 42)
White contamination: low
Result: PASS
The current camera region (0, 0, 640, 480) is only a placeholder.

11. Hidden-feature laboratory plan
Purpose: discover all hidden patterns and functions.

Must include:

Catalog known commands

Generate safe candidate hex commands

Send one candidate at a time

Wait and capture camera result

Record:

exact command

device

timestamp

BLE success/failure

observed RGB

brightness

white contamination

user label/notes

Include stop button

Conservative limits

Emergency stop

No uncontrolled brute-force by default

Do not start hidden-command sweep until logging, queue, camera calibration, and emergency stop are in place.

12. Audio / music sync plan
Current music sync is unreliable because:

It sends too many commands

Commands overlap

It is not rate-limited

It has no duplicate suppression

It does not use real FFT spectrum bars

Sensitivity and speed behavior are wrong

Strobe and pulse are nearly identical

It can turn lights off after song ends

AUX/Line-In naming is confusing

It cannot read actual LED state

Required:

Use same serialized command queue

Log audio and LED timing together

Prevent duplicate commands

Prevent Scroll/M1 interference

Add proper spectrum and beat behavior later

Add media player with play/pause/stop/next/back/speed/equalizer presets later

Distinguish:

Microphone

Line In / AUX input

Bluetooth audio input

Stereo Mix

WASAPI loopback

music files

13. GUI / UX requirements
Compact startup size

Correct aspect ratio

150-LED horizontal strip visualization

Connection RGB pulse

Application-wide File, View, Help menus

Profile management outside main remote panel

Import/export remote profiles

About dialog

Contact email: ayman.attia.ab@gmail.com

GitHub: https://github.com/aymashtain92

Automatic session log saving on close

Timestamped logs that are not overwritten

Version v0.41

14. Packaging requirements
Later, not now:

PyInstaller

--noconsole

Name: AymashTain LED Remote

Icon: aymashtaine.ico or AymashTain.ico

Do not bundle _internal.rar

Do not include .gitignore in release ZIP

Keep only:

_internal/

AymashTain LED Remote.exe

install_and_repair.ps1

LICENSE.txt

README.md

No EXE extraction now.

15. Current chat summary
This current conversation is between the user and ChatGPT (this assistant).

The user asked for a complete sync pack so any future AI can catch up without long back-and-forth.

This assistant:

Reviewed all previous AI conversations and logs.

Confirmed the documented MR Star color/brightness split.

Provided a full corrected mrstar_protocol.py.

Provided a full corrected hardware_test.py.

Confirmed both files compile.

Confirmed main.py is still the old unsafe version.

Began creating this AI sync pack.

The next real step is to replace main.py completely with the v0.41 queued version, then run the corrected hardware test, then add camera calibration and hidden-feature lab.

16. Golden rules for any AI reading this
Never mix MR Star BC commands with Classic 56/CC commands.

Never put brightness inside the color command.

Never use FFFF as a white field.

Never use asyncio.create_task() for color and brightness separately.

Always send color first, then brightness, with a small gap.

Always serialize BLE writes through one queue.

Never run Music Sync or Scroll during static color tests.

Never claim the app can read actual LED state over BLE.

Camera is the only physical verification unless controller readback is discovered.

Camera stays local-only. No uploads.

Use UUID, not hardcoded handle 13/19.

Python is 3.14.7, not 3.12.

Provide full replacement files, not partial patches, unless the user explicitly asks for a small edit.

Always run python -m py_compile .\file.py after replacement.

Do not auto-elevate to administrator.

Do not overwrite previous logs.

Preserve all captured Scroll frames exactly.

Keep experimental commands in a separate lab.

The user is not a developer. Give visual, step-by-step, one point at a time.

This project is free. No ads. No telemetry.