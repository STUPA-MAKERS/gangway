# Gangway Project

This project controls a lighting installation consisting of WS2805 LED strips using a Raspberry Pi 4B. It includes a custom driver implementation and a projection mapping system for complex visual effects that react to people walking through the area.

## Hardware Setup

The system is built around a Raspberry Pi 4B and a large array of LED strips suspended from the ceiling.

### Components
- **Controller**: Raspberry Pi 4B
- **Power System**:
  - Three 24V 300W Power Supplies
  - Step-Down Converter (24V to 5V) to power the Raspberry Pi
- **Lighting**: WS2805 LED strips
- **Mounting**: The strips are mounted on aluminum profiles, arranged in 3 groups of 3, each 2 meters long.
- **Sensor**: XOVIS PC2-L Person Counter

### Wiring and Connectivity
- **Data Signal**: The control signal originates from **GPIO 18** on the Raspberry Pi.
- **Signal Conditioning**: A level shifter is employed between the Raspberry Pi and the LED strips to convert the 3.3V logic to the required level for the LEDs.
- **Topology**: The strips are wired in a daisy-chain configuration.

![Setup Photo](docs/setup_photo.jpg)

## Person Detection & Data Flow

To enable interactive lighting effects, the system uses a **XOVIS PC2-L** person counter.

### Data Flow Pipeline
1.  **Acquisition**: The XOVIS sensor detects people in its field of view.
2.  **Push**: The sensor pushes event data (JSON) via HTTP POST to a lightweight web server running within the application (`XOVISServer`) on port 8081.
3.  **Processing**:
    *   The server parses the incoming JSON into event objects.
    *   **Projection Mapping**: Raw coordinates from the sensor are transformed using a homographic projection to match the physical floor plan. This ensures that a person standing at a specific location on the floor triggers the LED strip directly above them.
4.  **Distribution**: The processed coordinates are published to subscribers, primarily the `LEDController`, which updates the rendering state.

## Software

### Custom WS2805 Driver
This project uses a modified version of the `rp-ws281x` library to support the WS2805 protocol. The source code for this modified library can be found in the `rpi-ws2805-python` directory. The license has been updated to reflect these modifications.

### Configuration
The physical layout and logical mapping of the LEDs are defined in `config.yaml`. The system manages 9 distinct strip segments.

**Strip Layout:**

| Index | Length (LEDs) |
|-------|---------------|
| 1     | 24            |
| 25    | 24            |
| 49    | 23            |
| 71    | 24            |
| 97    | 24            |
| 121   | 24            |
| 145   | 24            |
| 169   | 24            |
| 193   | 24            |

The configuration also handles projection mapping parameters (`src_points`, `dst_points`) and defines cutout zones within the projection area.

## Animation System

The animation engine is designed to be procedural and responsive.

### How Animations Work
Animations are defined as Python functions that determine the color of a specific LED at a specific point in time.

*   **Input**:
    *   `time`: Current system time.
    *   `ctx`: Scene context (floor dimensions, LED positions, sound analysis).
    *   `led`: The specific LED being rendered.
    *   `objects`: A list of currently detected people (coordinates).
*   **Output**: An `RGBCCT` color value.

### Rendering Loop
The `LEDController` runs a continuous loop:
1.  It iterates through every LED in the system.
2.  It calls the active animation function for that LED.
3.  It updates the physical strip with the calculated colors.

### Interactive Animations
Responsive animations (e.g., `paint`, `dot`) utilize the `objects` list to calculate distance-based effects. For example, the `paint` animation maintains a history of positions to create trailing light effects that follow people as they move through the gangway.

### Recursive Composition & Meta-Animations

A powerful feature of the system is the ability to nest animations recursively. "Meta-animations" are animations that take other animations as input arguments instead of just colors.

**Benefits:**
*   **Modularity**: Complex behaviors can be built by combining simple building blocks. For example, `blend(rainbow(), sparkle())` creates a sparkly rainbow effect without writing a new dedicated function.
*   **Logic Abstraction**: Control logic is decoupled from visual logic.
    *   `schedule(day_anim, night_anim)`: Switches behavior based on time of day.
    *   `proximity(active_anim, idle_anim)`: Smoothly transitions between effects based on how close a person is to a specific point.
*   **Infinite Depth**: Since a meta-animation conforms to the standard animation interface, it can be wrapped in another meta-animation. You can have a `schedule` that switches between a `blend` and a `proximity` animation.

This functional approach allows for high flexibility and rapid experimentation with visual effects.

## Sound

A USB microphone lets the animations react to music. The microphone is an
AKM AK5371 (ALSA card `AK5371`). It records only. It supports 1 or 2
channels and the sample rates 8000, 11025, 22050, 44100 and 48000 Hz.

The onboard audio of the Pi stays off, because it uses PWM0, and PWM0 sends
the LED data. The USB microphone does not use PWM0.

### Data flow

1. The thread `gangway.audio.AudioCapture` reads blocks of 512 samples at
   22050 Hz from the microphone (about 43 blocks each second). It uses
   [sounddevice](https://python-sounddevice.readthedocs.io/) and PortAudio
   with ALSA.
2. For each block, the pure functions in `gangway/audio/dsp.py` calculate a
   new `AudioState` snapshot:
   *   `level`: the loudness (RMS) of the block.
   *   `bass` (40 to 150 Hz), `mid` (150 to 2000 Hz) and `treble` (2000 to
       8000 Hz): the energy of each band, from an FFT with a Hann window
       over the last 1024 samples.
   *   `spectrum`: 8 narrower bands from 40 to 8000 Hz.
   *   `beats`, `last_beat`, `beat_count` and `tempo`: the beat detection.
3. The LED controller puts the latest snapshot into the scene context of
   each frame (`ctx.audio`). It changes the beat times to the clock of the
   `time` argument of the animations.

All values are from 0 to 1. An automatic gain control divides each value by
its recent peak. The peak halves in 5 s when the sound gets quieter, so a
quiet room and a loud room both reach 1. A value at the noise floor or
below it gives 0.

A beat is a fast rise of the bass energy. The rise must be more than the
mean plus 1.5 standard deviations of the rises in the last second. It must
also be more than 10 % of the bass peak. After a beat, the next beat can
occur after 0.25 s or more.

If the microphone is missing or fails, the snapshot is silent. The thread
writes one message to the log and tries again every 5 s. The LEDs and the
API continue.

`GET /api/data/audio` shows the values of the latest snapshot. Use it to
tune the settings with music in the room.

### Settings

The `audio` section of `config.yaml` is optional. If it is not there, the
defaults apply:

```yaml
audio:
  enabled: true          # false: do not open the microphone
  device: AK5371         # a part of the device name, or the device index
  sample_rate: 22050     # the device must support this rate
  block_size: 512        # samples per block
  noise_floor: 0.01      # RMS that counts as silence (0.01 = -40 dBFS)
```

The device search prefers the `hw:` device of the card, because the other
ALSA devices resample or mix in software. The capture reads the settings
once, when the application starts. The web UI does not change this section.

### Audio animations

The animations are in `gangway/animations/audio/`. Without sound, each one
shows its background.

| Animation | Effect |
|-----------|--------|
| `beat_wave` | On each beat, a wave front moves from one side of the floor to the other. Parameters: `color`, `background`, `direction`, `reverse`, `speed` (floor units per second), `width` (length of the tail). |
| `beat_ripples` | On each beat, a ring grows from each person. Parameters: `color`, `background`, `speed`, `width`, `max_radius`. |
| `spectrum` | An equalizer along an axis: the bass at one end, the treble at the other end. Parameters: `colors` (the palette from bass to treble), `background`, `direction`, `reverse`, `min_brightness`. |
| `beat_pulse` | All LEDs flash on each beat and fade exponentially. Parameters: `color`, `background`, `decay` (time constant in seconds). |
| `level` | A VU meter along an axis, with a peak dot that falls slowly. Parameters: `color`, `peak_color`, `background`, `direction`, `reverse`, `source`, `peak_fall`, `peak_width`. |
| `audio_gain` | A meta-animation. It multiplies the brightness of an animation by an audio value. Parameters: `animation`, `source` (`level`, `bass`, `mid` or `treble`), `min_gain`, `max_gain`. |
| `beat_switch` | A meta-animation. It shows the next animation after each `beats_per_switch` beats. Parameters: `animations`, `beats_per_switch`. |

Example:

```yaml
animation:
  beat_switch:
    beats_per_switch: 16
    animations:
      - beat_wave:
          color: {r: 255, g: 0, b: 128}
          background:
            audio_gain:
              animation: {rainbow: {}}
              min_gain: 0.1
      - spectrum: {direction: y}
```

## User Interface

The web UI is an Angular single-page app in `frontend/`. It uses the
components and the design tokens of the STUPA-MAKERS
[ui-kit](https://github.com/STUPA-MAKERS/ui-kit), so it has the same look as
STUPA-Workflow and homebox-makers. It has a light and a dark theme.

The UI has four pages:

- **Live** shows the strips in their current colors and the detected
  persons. The mapped view draws on the floor plan. The raw view draws on
  the camera image. The sound meter shows the level, the bands, the beats
  and the tempo of the microphone.
- **Animation** edits the active animation. The backend gives the
  parameters of each animation (`GET /api/animations/`), so a new animation
  needs no change in the UI. Click **Save** to apply the change.
- **Presets** lists the presets. A preset opens in a sheet beside the
  list, with the editor of its animation. The sheet loads, renames and
  deletes the preset. The floating button saves the current animation as
  a new preset.
- **Statistics** shows the counts of the sensor: the persons that went in
  and out today, yesterday, this week, in the last 30 days and in all the
  history of the sensor, a chart for 24 hours, 7 days or 30 days, the
  estimate of the persons in the room, the heat map of the walked
  positions and the health of the sensor.

The sensor counts only the crossings of the entrance. The estimate of the
persons in the room adds the persons in and takes away the persons out,
hour by hour. It never goes below 0, and it starts at 0 each morning at
04:00, so a missed crossing does not stay.

The statistics come from the HTTP API of the sensor (`/api/stats/...` in
the backend, `gangway/xovis/sensor_api.py`). The sensor counts the persons
on its line 0 ("Ein-/Ausgang"). It keeps about 4 months of counts. It
clears the heat map when it starts. The backend reads only a fixed set of
paths, because some paths of the sensor change its state even on GET. The
variables `XOVIS_URL`, `XOVIS_USER` and `XOVIS_PASSWORD` override the
address and the login of the sensor.

The UI sends its requests with no API key first. Through the SSO tunnel
nginx adds the key. On the LAN the backend refuses the request, and the UI
asks for the key. The browser keeps the key in `localStorage`. A link can
also give the key as `?apiKey=…`.

![Live view](docs/ui_screenshot_1.png)
![Animation editor](docs/ui_screenshot_2.png)
![Presets](docs/ui_screenshot_3.png)

## System (NixOS)

This repo is also a Nix flake. The flake describes the complete Raspberry Pi:
the operating system, the network, the services and the app. The board
support comes from [nixos-raspberrypi](https://github.com/nvmd/nixos-raspberrypi).

| Path | Content |
|------|---------|
| `flake.nix` | The inputs. All outputs come from `modules/`. |
| `modules/hosts/gangway.nix` | The host `gangway` and its SD image. |
| `modules/nixos/` | The system modules: network, services, app. |
| `nix/` | The packages: backend, web UI and LED driver. The web UI is a set of static files that nginx serves. |
| `secrets/gangway.yaml` | The secrets, encrypted with sops. |

The admin account is `gangway`. `fsi` is an alias with the same UID, home
and SSH key, so `ssh fsi@gangway.local` also works.

### Network

| Interface | Address | Function |
|-----------|---------|----------|
| `eth0` | 10.0.0.1/24 | Private LAN for the Xovis sensor. dnsmasq gives DHCP leases from 10.0.0.2 to 10.0.0.254. The Xovis always gets 10.0.0.250. |
| `wlan0` | DHCP | Uplink over "Iphone Hotspot", the FRITZ!Box at the site. The Pi masquerades the sensor LAN through this link. |
| `wg-ext` | 10.44.0.2/24 | WireGuard tunnel to the StuPa gateway, which publishes the web UI as `gangway.reutlingen.university` behind an authentik login. |

| Port | Service | Reachable from |
|------|---------|----------------|
| 22 | SSH, key only | All interfaces |
| 80 | nginx: web UI, `/api/` and `/live` | All interfaces, `wg-ext` included |
| 8081 | Xovis receiver | `eth0` |
| 8082 | API | `eth0` |

Set the push target of the Xovis sensor to `http://10.0.0.1:8081/`. The
receiver accepts bodies with `Content-Length` and chunked bodies.

The app keeps its run-time state in `/var/lib/gangway`: `config.yaml` and
`presets/`. Each start copies the `config.yaml` and the presets of this repo
into that directory, but only the files that are not there yet. The service
never overwrites a file, so the changes from the web UI stay.

The `config.yaml` and the presets in this repo come from the old SD card:
the projection points, the cutout, the strip layout and the active animation.
Two presets on the old card were corrupted and are lost: "Off-at-Night" and
"Secret-Rave-Rainbow-Trails".

### Secrets

`secrets/gangway.yaml` holds the WiFi passwords and the `API_KEY` of the web
UI. sops encrypts the file for two recipients, see
`.sops.yaml`:

- The GPG key of the admin. Use it to edit the file.
- The age key of the Pi. sops-nix derives it from the SSH host key
  `/etc/ssh/ssh_host_ed25519_key` when the system activates.

To edit the secrets, do this step:

```sh
sops secrets/gangway.yaml
```

If the Pi gets a new SSH host key, do these steps:

1. Get the age key of the Pi: `ssh-keyscan -t ed25519 gangway.local | ssh-to-age`.
2. Replace the `gangway` key in `.sops.yaml` with this value.
3. Re-encrypt the file: `sops updatekeys secrets/gangway.yaml`.

### Install on a new SD card

The SD image contains no secrets and no SSH host key. You must copy the host
key onto the card before the first boot. If you do not do this, sops-nix
cannot decrypt the secrets, and the Pi has no WiFi.

1. Build the image: `nix build .#gangway.sd-image`.
2. Find the device of the card with `lsblk`, for example `/dev/sdX`.
3. Write the image. This erases the card:
   `sudo dd if=result/sd-image/*.img of=/dev/sdX bs=4M conv=fsync status=progress`.
4. Mount the root partition: `sudo mount /dev/sdX2 /mnt`.
5. Copy the host key:
   `sudo install -D -m 600 ssh_host_ed25519_key /mnt/etc/ssh/ssh_host_ed25519_key`.
6. Copy the public key:
   `sudo install -m 644 ssh_host_ed25519_key.pub /mnt/etc/ssh/ssh_host_ed25519_key.pub`.
7. Unmount the partition: `sudo umount /mnt`.
8. Put the card into the Pi and start the Pi.

On the first boot, the root partition grows to fill the card.

### Deploy a change

Build on your computer and activate on the Pi over SSH:

```sh
nixos-rebuild switch --flake .#gangway --target-host gangway@gangway.local --sudo
```

To build the system for aarch64 on an x86_64 computer, the computer must
emulate aarch64. On NixOS, set `boot.binfmt.emulatedSystems = [ "aarch64-linux" ];`.
The binary cache of nixos-raspberrypi holds the vendor kernel, so the kernel
does not compile under emulation.

## Development

`nix develop` opens a shell with Python 3.13, the dependencies of the app,
ruff, basedpyright, pytest, Node.js and npm. The shell also creates `.venv`,
so your editor finds the same interpreter.

```sh
nix develop
ruff check . && ruff format --check .
basedpyright
python -m pytest
```

### Web UI

The ui-kit is a git submodule in `frontend/vendor/ui-kit`. Get it before the
first build:

```sh
git submodule update --init
cd frontend
npm ci
npm start        # ng serve on http://localhost:4200, /api goes to port 8082
npm test         # jest
npm run lint     # eslint
npm run build    # the static files in dist/gangway/browser
```

`npm start` needs the backend on port 8082 (`python main.py`). The UI then
asks for the `API_KEY` of the backend.

The Nix build cannot read the submodule. It copies the flake input `ui-kit`
into `vendor/ui-kit`. If you move the submodule to a new commit, do these
steps:

1. Set the same commit in the `ui-kit` URL in `flake.nix`.
2. Run `nix flake lock`.
3. Run `nix build .#gangway-frontend`.

After a change to `frontend/package-lock.json`, set `npmDepsHash` in
`nix/gangway-frontend.nix` to the hash that the failed build shows.
