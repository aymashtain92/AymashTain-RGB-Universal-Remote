# AI ERRORS ONLY — Do Not Repeat These Mistakes

This file is for AI assistants.  
Do not show this to normal users.

---

## Protocol errors

1. Do not mix MR Star BC commands with Classic 56/CC commands.
2. Do not put brightness inside `BC0406`.
3. Do not use `FFFF` as a white field.
4. Do not assume every `BC04` packet is a normal color command.
5. Do not assume `BC0F`/`BC11` are normal color commands.
6. Do not treat Scroll data as static color.
7. Do not assume white command is known. It is not fully verified.
8. Do not use `BC0401RRGGBB0055` as MR Star documented color.
9. Do not use `7E...EF` in normal mode.
10. Do not use `CC2333` or `56...` on MR Star strips unless user confirms.

## BLE errors

11. Do not use hardcoded handle 13 or 19. Use FFF3 UUID.
12. Do not send color and brightness as separate `create_task`.
13. Do not send to multiple devices with `asyncio.gather` without serialization.
14. Do not allow Music Sync to flood BLE.
15. Do not allow two Scroll macros to run at once.
16. Do not assume BLE write success means physical LED changed.
17. Do not claim readback exists unless proven.
18. Do not ignore disconnects.
19. Do not retry forever without delay.
20. Do not use `response=True` by default for these strips.

## Logging errors

21. Do not overwrite previous session logs.
22. Do not rely on manual Save.
23. Do not separate BLE/audio/camera logs if user wants unified.
24. Do not log only successful sends. Log failures too.
25. Do not forget per-device results.

## UI errors

26. Do not claim the preview shows real LED state.
27. Do not use `BRIGHTNESS_MIN = 100`.
28. Do not force 1400×920 startup.
29. Do not hide profiles in a tab only.
30. Do not remove existing useful tabs.
31. Do not break remote buttons.
32. Do not break macros.
33. Do not auto-elevate to admin.
34. Do not use LumenForge branding.
35. Do not use v1.3. Use v0.41.

## Camera errors

36. Do not upload camera frames.
37. Do not use cloud processing.
38. Do not assume camera region is correct.
39. Do not use `(0,0,640,480)` as final calibration.
40. Do not judge color without calibration.
41. Do not assume all three strips are in frame.
42. Do not assume one strip represents all three unless user says so.

## Audio errors

43. Do not call every input “Microphone”.
44. Do not assume AUX is named AUX.
45. Do not assume loopback works on every machine.
46. Do not use phone mic over BLE.
47. Do not send audio over BLE.
48. Do not use real-time FFT without rate limiting.
49. Do not leave lights off after song.
50. Do not use same algorithm for pulse and strobe.

## Workflow errors

51. Do not give many steps back to back.
52. Do not ask a non-developer to manually merge fragments.
53. Do not provide partial patches unless asked.
54. Do not forget to run `python -m py_compile`.
55. Do not assume Python 3.12.
56. Do not ignore the user’s backup folder.
57. Do not modify files outside the project unless asked.
58. Do not delete logs.
59. Do not delete DB without backup.
60. Do not claim something is done if it is not implemented.
61. Do not assume `main.py` is fixed because it compiles.
62. Do not run hidden-command sweeps before queue, camera, and emergency stop exist.
63. Do not claim the hardware test has not been run — it has.
64. Do not claim the camera works — it is disabled.
65. Do not use `py -3.12`; the machine has Python 3.14.7.
66. Do not hardcode brightness strings in tests; use `encode_mrstar_brightness()`.
67. Do not ignore the latest log evidence: overlapping Music Sync and duplicate macro starts.