AymashTain LED RGB Remote — Developer README
This README is for developers only.
Normal users should use the launcher and installer.

1. Project purpose
Windows desktop app for controlling cheap BLE LED strips that use the MR Star app and related clone controllers.

Target hardware:

GATT--DEMO BLE devices

Service: 00002022-0000-1000-8000-00805f9b34fb

Write characteristic: 0000fff3-0000-1000-8000-00805f9b34fb

Known strips:

41:42:59:F1:C8:68

41:42:43:E7:8B:F6

41:42:F9:D7:45:B0

2. Requirements
Windows 10/11

Python 3.14.7 (current machine)

Bluetooth enabled

Optional: OpenCV for camera

Optional: sounddevice / soundfile for audio

Python packages:

text
PySide6
bleak>=0.22
qasync
sounddevice
soundfile
numpy
opencv-python
pytest
pytest-asyncio
pyinstaller
ruff
Do not pin bleak==0.22.3 on Python 3.14.
Use bleak>=0.22.

3. Install and repair
Option A — PowerShell repair script
Run:

powershell
powershell -ExecutionPolicy Bypass -File .\install_and_repair.ps1
It should:

Detect Python

Verify Python version

Upgrade pip

Install requirements

Check Bluetooth

Check camera

Check Visual C++ runtime

Create logs folder

Run import checks

Option B — Manual
powershell
cd "D:\AymashTain LED Remote"
python -m pip install --upgrade pip
python -m pip install -r .\requirements.txt
Visual C++ Redistributable
If the app or OpenCV fails to load DLLs, install:

text
https://aka.ms/vs/17/release/vc_redist.x64.exe
Do not silently install it from a script without asking the user.

4. How to run
Normal launcher
Double-click:

text
Launch AymashTain LED RGB Remote.bat
From terminal
powershell
cd "D:\AymashTain LED Remote"
python .\main.py
Hardware test
powershell
cd "D:\AymashTain LED Remote"
python .\hardware_test.py
Do not run main.py and hardware_test.py at the same time.

5. Compile check
After replacing any Python file:

powershell
python -m py_compile .\main.py
python -m py_compile .\mrstar_protocol.py
python -m py_compile .\hardware_test.py
No output means success.

6. Logs
Logs are in:

text
D:\AymashTain LED Remote\logs\
Hardware test logs:

text
hardware_test_YYYYMMDD_HHMMSS.log
hardware_test_YYYYMMDD_HHMMSS.json
hardware_test_YYYYMMDD_HHMMSS.csv
Session logs later:

text
session_YYYYMMDD_HHMMSS.log
session_YYYYMMDD_HHMMSS.json
session_YYYYMMDD_HHMMSS.csv
Error log:

text
lumenforge_errors.log
Crash log later:

text
crash.log
Do not overwrite old logs.

7. Troubleshooting
No devices found
Turn Bluetooth on.

Close MR Star app on phone.

Turn off phone Bluetooth.

Power-cycle strips.

Run scan again.

Use scan2.py if needed.

Connected but no reaction
Confirm write characteristic is FFF3.

Confirm color command is BC0406....

Confirm brightness command is BC0506....

Do not use FFFF.

Confirm strip is not in Scroll/M1 mode.

Send BC04010055 to exit dynamic mode.

Try one strip only.

Far strip disconnects
Increase inter-device delay.

Use powered USB hub or separate power.

Do not send commands too fast.

Check signal distance.

Check power supply.

Colors pale or white
Check that brightness is separate.

Check that FFFF is not in color command.

Check mrstar_protocol.py is the updated version.

Check confidence decoder output.

Camera not working
Install opencv-python.

Close other apps using camera.

Try camera index 0, 1, 2.

Calibrate region.

Do not upload frames.

Audio not working
Check input device names.

Look for Line In, AUX, Stereo Mix, VoiceMeeter.

Use loopback only if available.

Do not call every input "Microphone".

8. AI update workflow
When asking an AI to update the project:

Give it the AI_SYNC_PACK folder.

Give it the current file.

Give it the latest conversation or log.

Paste the universal prompt from 02_UNIVERSAL_AI_PROMPT.md.

Ask for a full replacement file.

Replace the file.

Run python -m py_compile.

Save the new conversation into 06_CURRENT_CHAT.md or a new dated file.

9. Contact
Owner: aymashtain92
Email: ayman.attia.ab@gmail.com
GitHub: https://github.com/aymashtain92
Repo: https://github.com/aymashtain92/AymashTain-RGB-Universal-Remote

When contacting, include:

Windows version

Python version

File name

Exact error text

Log file from logs/

What you did before error