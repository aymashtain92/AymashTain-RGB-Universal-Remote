# How to use AI updates and Sync — for absolute beginners

This is the easiest way to get help from any AI.  
Follow these steps exactly. Don’t skip.

---

## What you need

- The folder `AI_SYNC_PACK` with files `00` to `07`.
- The file you want the AI to change (for example `aymashtain/ui/tabs/lab_tab.py`).
- The prompt from `02_UNIVERSAL_AI_PROMPT.md`.

---

## Step‑by‑step

1. **Open the AI chat.**
2. **Upload the whole `AI_SYNC_PACK` folder.**
3. **Upload the file you want changed** (e.g. `main.py`).
4. **Copy the prompt** from `02_UNIVERSAL_AI_PROMPT.md` and paste it into the chat.
5. **Tell the AI exactly what to do.**  
   Example: “Add the hidden-feature laboratory to `aymashtain/ui/tabs/lab_tab.py`. Send the full file.”
6. **Wait for the AI to give you a full new file.**
7. **Replace the old file on your PC:**
   - Open the old file in Notepad.
   - Press `Ctrl+A`, then `Delete`.
   - Paste the new content.
   - Save.
8. **Check the file is not broken.**  
   Open PowerShell in the project folder and run:
   ```powershell
   python -m py_compile .\main.py
   ```
   No red errors = good.
9. **Save the chat summary** in `06_CURRENT_CHAT.md`.  
   Write: date, AI name, what you asked, what changed.

---

## After you test the app

Update these files:

- `00_MASTER_SUMMARY.md` — new facts, status, logs, problems.
- `01_WORKFLOW.md` — add the test with date and result.
- `03_TODO_USER_AND_AI.md` — tick done items, add new ones.
- `04_AI_ERRORS_ONLY.md` — only if the AI made a new mistake.
- `05_DEVELOPER_README.md` — only if environment or install changed.
- `06_CURRENT_CHAT.md` — always add a new section.

---

## FAQ

**Q: The AI gave me only part of the file. What do I do?**  
A: Say: “Send the FULL file. Do not send pieces.”

**Q: I ran the compile command and got an error.**  
A: Copy the whole red error and paste it to the AI. Ask: “Fix this error and send the full file.”

**Q: The file is not found when I run the command.**  
A: Make sure you are in the right folder. Run `cd "D:\Coding projects\aymashtain-led-remote-Source"` first.

**Q: The app does not open.**  
A: Open PowerShell, go to the project folder, and run `python .\main.py`. You will see the real error. Copy it to the AI.

**Q: The AI asks me to edit small pieces of code.**  
A: Say: “I am not a developer. Send the full file so I can copy‑paste and overwrite.”

**Q: Which file do I send to the AI?**  
A: Send the whole `AI_SYNC_PACK` folder and the one file you want changed.

---

## If something goes wrong (troubleshooting)

- **Bluetooth not connecting:** Turn off phone Bluetooth. Close MR Star app. Power‑cycle the strip.
- **Camera not working:** Install `opencv-python`. Close other apps using camera. Try camera index 0, 1, 2.
- **Audio not working:** Look for “Line In”, “AUX”, “Stereo Mix”, or “VoiceMeeter” in the device list.
- **Colors look pale:** Make sure brightness is sent as a separate command. Do not use `FFFF`.
- **Far strip disconnects:** Increase inter‑device delay in the app. Use a powered USB hub.

---

## Current release

**v0.51 Alpha** — comes as an `.exe` file plus a folder.  
Just double‑click the `.exe`. Keep the folder next to it.  
That’s it. Easy peasy.

---

## License

This project is released under the **MIT License**.  
See `LICENSE.txt` for the full text.  
Third‑party libraries have their own licenses.