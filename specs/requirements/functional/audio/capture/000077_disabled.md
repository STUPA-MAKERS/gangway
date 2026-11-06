---
id: "000077"
title: A disabled capture does not open the microphone
kind: functional
status: approved
owner: frederikbeimgraben
updated: 2026-11-06
implementation:
  - main.py
scope:
  - main.py
---

# A disabled capture does not open the microphone

With `audio.enabled: false`, the application must not start the capture process. The audio
animations must get `SILENT_AUDIO`.

Test: Review.
