# Gangway Project Overview

Gangway is a Python-based lighting control system for an interactive art installation. It uses a Raspberry Pi 4B to drive WS2805 LED strips, reacting to people moving through the space using a Xovis PC2-L person counter.

## Key Components

### 1. Core Logic (`./gangway/`)
- **`main.py`**: Application entry point. Initializes config, LED controller, and Xovis server.
- **`led_controller.py`**: Runs the main render loop. It holds the current state, manages the `PixelStrip`, and calls the active animation function for every LED.
- **`types/`**: Defines the core data types, one module for each type: `Point`, `Rectangle`, `LED`, `SceneContext`, `AudioState`, the `Animation` callable signature, and the `StrEnum` types `Axis`, `AudioSource`, `BlendMode` and `SpeedMode`. The package exports all of them.
- **`config.py`**: Manages configuration loading from `config.yaml`.

### 2. Input Handling (`./gangway/xovis/`)
- **`server.py`**: Runs a simple HTTP server to receive JSON events from the Xovis sensor (Webhooks).
- **`model.py`**: Pydantic-style dataclasses for parsing Xovis events (ZoneEntry, ZoneExit, specific object coordinates).
- **`homographic_projection.py`**: Maps the camera coordinates from Xovis to the physical floor plan coordinates using a homography matrix.

### 2b. Sound Input (`./gangway/audio/`)
- **`capture.py`**: `AudioCapture`, a thread that reads the USB microphone (AK5371) with sounddevice. On an error it logs once, publishes `SILENT_AUDIO` and retries every 5 s.
- **`dsp.py`**: Pure functions that turn each block of samples into an `AudioState` snapshot: level, bass/mid/treble, 8 spectrum bands, beats (bass onset with an adaptive threshold) and tempo. Test them with synthetic signals, not with a device.
- **`settings.py`**: The optional `audio:` section of `config.yaml`.

### 3. Animation System (`./gangway/animations/`)
- **Procedural Approach**: Animations are functions that take `(time, context, led, objects)` and return a color (`RGBCCT`).
- **Layout**: `idle/`, `responsive/`, `meta/` and `audio/` are packages with one animation per module, or a small group of similar ones. The registry in `config.py` reads `__all__` of each package, so export a new animation there.
- **Meta-Animations (`meta/`)**: High-order functions that compose other animations. Examples include `blend`, `schedule`, `alternate`, and `proximity`.
- **Responsive**: Animations receive a list of detected objects (`Point`s) to react to presence.
- **Audio (`audio/`)**: Animations read `ctx.audio` (an `AudioState`). The beat times use the clock of the `time` argument. The closure runs once for each LED, so compute frame values once with `per_frame` from `audio/_frame.py`.

### 4. Hardware Driver
- Uses a custom `rpi_ws2805` library (located in `rpi-ws2805-python/library`) to communicate with the LED strips via PWM0 on GPIO 18. The analog audio also uses PWM0, so the system turns the onboard audio off. The USB microphone does not use PWM0.

### 5. Frontend (`./frontend/`)
The frontend is written in Next.js.

### 6. System (`./flake.nix`, `./modules/`, `./nix/`)
- The flake describes the whole Raspberry Pi with NixOS and nixos-raspberrypi. See the "System (NixOS)" section of README.md.
- `nix/` holds the packages, `modules/nixos/` the system modules, `modules/hosts/gangway.nix` the host and the SD image.
- Secrets are in `secrets/gangway.yaml`, encrypted with sops. Never commit a plaintext secret.
- The app state (`config.yaml`, `presets/`) lives in `/var/lib/gangway` on the Pi. `GANGWAY_CONFIG` points the app at it.
- Work in `nix develop`. Python is 3.13+, checked with ruff and basedpyright (strict).

## Data Flow
1. **Sensor**: Xovis detects a person -> HTTP POST to `server.py`.
2. **Server**: Parses JSON -> Updates internal state -> Projects coordinates to floor space.
3. **Controller**: `LEDController` pulls updated object positions.
4. **Sound**: `AudioCapture` analyzes each microphone block into an `AudioState`. For each frame, `LEDController` puts the latest snapshot into `SceneContext.audio`, with the beat times moved from `time.monotonic` to the animation time.
5. **Render**: In the loop, `LEDController` calls the current `Animation` function. All LEDs of a frame get the same time and context.
6. **Output**: Resulting colors are sent to the LED strip.
