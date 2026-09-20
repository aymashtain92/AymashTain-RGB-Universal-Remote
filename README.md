# AymashTain LED RGB Remote

Free, ad-free desktop controller for **MR Star / Magic Home style BLE RGB LED
strips**. Controls several strips at once, keeps colour and brightness as
separate frames (the fix for washed-out colours), and includes the tooling used
to reverse-engineer the protocol: a hex console, a frame lab, automated sweeps
and webcam verification of what the strip actually emitted.

## Quick start (Windows)

```bat
run.bat
```

`run.bat` creates `.venv`, installs `requirements.txt` on first run, and starts
the app. Manual equivalent on any OS:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Python 3.10+ and a Bluetooth LE adapter are required. On Windows 10/11 pair
nothing by hand — just use the **Connect** tab.

## Tabs

| Tab | What it does |
| --- | --- |
| **Connect** | Scan, filter LED-looking devices, connect/remember/forget strips, blink to identify, auto-reconnect |
| **Remote** | Colour wheel, presets, brightness, effects, power, plus fully custom remote profiles with grouped buttons and multi-frame macros |
| **Music & Media** | Playlist + player, and dancing lights driven by microphone, system loopback audio, or the playing file |
| **Sweep** | Step hue / saturation / brightness / effect bytes automatically, optionally scoring each step with the camera |
| **Camera** | Webcam preview, sample region, per-command averaging, white-contamination scoring |
| **Console** | Send raw hex frames (with comments), loop them, decode without sending |
| **Lab** | Command history, byte-level diffing of two frames, promote a finding into a remote button or macro |
| **Events** | Live filterable log of everything, exportable to CSV/JSON |

## Protocol

```
Power       BC 01 01 XX 55            XX = 01 on, 00 off
Static      BC 04 01 00 55
Colour      BC 04 06 HHHH SSSS 0000 55  hue 0..359, saturation 0..1000
Brightness  BC 05 06 BBBB 00000000 55   value 0..1024
Effect      BC 06 02 XX 0000 55
```

Classic Magic Home / Triones clones are also supported (`CC2333` / `CC2433`
power, `56RRGGBB00F0AA` colour).

**Colour and brightness are always two frames.** Packing the value channel into
`BC0406` is what made earlier builds look pale or white-tinted; the controller
treats those trailing bytes as reserved. `frames_for_rgb()` encodes the correct
order and everything in the UI goes through it.

Confidence levels are attached to every decode: `documented`, `captured`
(sniffed from the vendor app) or `unconfirmed` — so the Lab tab never presents a
guess as fact.

## Where your data lives

| OS | Path |
| --- | --- |
| Windows | `%LOCALAPPDATA%\AymashTain` |
| macOS | `~/Library/Application Support/AymashTain` |
| Linux | `~/.local/share/aymashtain` |

Contains `config.json`, `aymashtain.db` (profiles, buttons, history, devices)
and `logs/session_<timestamp>.{log,json,csv}`, pruned after
`log_retention_days`. Override with the `AYMASHTAIN_DATA_DIR` environment
variable.

## Development

```bash
python -m pytest -q      # unit tests (protocol, storage, vision, audio maths)
python -m ruff check .   # lint
```

The protocol, storage, vision and audio layers have no Qt dependency, so they
are testable headlessly. Build a Windows executable with:

```bat
build_exe.bat
```

## Troubleshooting

* **No devices found** — turn Bluetooth on, close the vendor phone app (a strip
  only accepts one connection), then rescan with the filter disabled.
* **Colours look white/pale** — something is sending brightness inside the
  colour frame; check the Console decode of the last frames in the Lab tab.
* **Dancing lights do nothing** — pick the right source; "system audio
  (loopback)" needs a WASAPI loopback device on Windows or a monitor source on
  Linux.
* **Strips lag behind** — raise *Inter-device delay* if you drive many strips,
  or lower the reactive update rate.
