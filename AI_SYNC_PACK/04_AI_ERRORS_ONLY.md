# AI ERRORS ONLY — Do Not Repeat These Mistakes

This file is for AI assistants. Do not show it to normal users.

---

## Project structure errors

1. Do not treat this as a single-file `main.py` project. It is a package under `aymashtain/`.
2. Do not replace the package with a flat `main.py`. The package is better and already works.
3. Do not add new top-level scripts. Keep code inside `aymashtain/`.
4. Do not delete `aymashtain/ble/manager.py`. The serialized queue lives there.
5. Do not remove `BleManager.set_color()`. It sends colour then brightness in order.
6. Do not remove the `EventBus` / `SessionLogger` flow in `events.py`.
7. Do not change the SQLite schema without a migration.

## Protocol errors

8. Do not mix MR Star BC commands with Classic 56/CC commands.
9. Do not put brightness inside `BC0406`.
10. Do not use `FFFF` as a white field.
11. Do not assume every `BC04` packet is a normal colour command.
12. Do not treat Scroll data as static colour.
13. Do not use `BC0401RRGGBB0055` as documented MR Star colour.
14. Do not use `7E...EF` outside the experimental lab.
15. Do not guess the white/neutral command. It is not fully verified.

## BLE errors

16. Do not use hardcoded handle 13 or 19. Use the FFF3 UUID.
17. Do not send colour and brightness as separate `create_task()` calls.
18. Do not bypass the `BleManager` queue.
19. Do not use `asyncio.gather` across devices in `send_hex_all` — the current code sends sequentially with an inter-device delay on purpose.
20. Do not assume BLE write success means the LEDs changed.
21. Do not claim readback exists. It does not.
22. Do not use `response=True` by default for these strips.

## Logging errors

23. Do not overwrite previous session logs.
24. Do not log only successful sends. Log failures too.
25. Do not remove the per-device result fields.

## UI errors

26. Do not claim the strip preview shows real LED state. It shows last-sent colour.
27. Do not force a large window size.
28. Do not break the profile / button / macro system.
29. Do not auto-elevate to administrator.
30. Do not use LumenForge branding.
31. Do not claim a feature exists if it does not.

## Camera errors

32. Do not upload camera frames.
33. Do not use cloud processing.
34. Do not treat `(0.3, 0.35, 0.7, 0.65)` as a final calibration. It is a default.
35. Do not judge colour without calibration.
36. Do not assume all three strips are in one camera frame.

## Audio errors

37. Do not call every input "Microphone".
38. Do not assume AUX is named AUX.
39. Do not assume loopback works on every machine.
40. Do not leave lights off after a song ends.

## Workflow errors

41. Do not give many steps back to back.
42. Do not ask a non-developer to merge fragments by hand.
43. Do not provide partial patches unless asked.
44. Do not forget `python -m py_compile`.
45. Do not use `py -3.12`. The machine has Python 3.14.7.
46. Do not edit files outside the project folder.
47. Do not delete logs.
48. Do not delete the DB without backup.
49. Do not claim something is done if it is not implemented.
50. Do not assume the current version is `1.0.0`. Release name is `v0.51 Alpha`.