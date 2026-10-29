/**
  The gangway backend, packaged from `main.py` and `gangway/`.

  The repo carries no pyproject, so this is not a Python package build. It
  copies the sources into `share/gangway` and wraps `main.py` with a Python
  environment that holds the run-time dependencies.

  # Inputs
  - `main.py`, `gangway/`, `config.yaml` and `presets/` — the only sources
    the fileset selects, so a change to the frontend or a README does not
    rebuild the backend
  - `rpi-ws2805` — the LED driver from ./rpi-ws2805.nix
  - `sounddevice` — reads the USB microphone for the audio animations

  # Defines
  - `passthru.pythonDeps` — the run-time dependencies as a function of a
    Python package set, so the dev shell can add its tools to the same list
  - the `gangway` derivation — `bin/gangway` starts the LED controller, the
    Xovis receiver on port 8081 and the API on port 8082.
    `share/gangway/config.yaml` and `share/gangway/presets/` are the seed
    that the NixOS module copies into the state directory
*/
{
  lib,
  stdenvNoCC,
  makeWrapper,
  python3,
  callPackage,
  rpi-ws2805 ? callPackage ./rpi-ws2805.nix { },
}:

let
  pythonDeps = ps: [
    ps.fastapi
    ps.numpy
    ps.opencv4
    ps.pydantic
    ps.python-dotenv
    ps.pyyaml
    ps.requests
    # nixpkgs patches the PortAudio path into sounddevice, so the library
    # resolves on NixOS without LD_LIBRARY_PATH. That PortAudio has ALSA.
    ps.sounddevice
    ps.uvicorn
    (rpi-ws2805.override { python3Packages = ps; })
  ];

  pythonEnv = python3.withPackages pythonDeps;
in

stdenvNoCC.mkDerivation {
  pname = "gangway";
  version = "0.1.0";

  src = lib.fileset.toSource {
    root = ../.;
    fileset = lib.fileset.unions [
      ../main.py
      ../config.yaml
      (lib.fileset.fileFilter (file: file.hasExt "yaml") ../presets)
      (lib.fileset.fileFilter (file: file.hasExt "py") ../gangway)
    ];
  };

  nativeBuildInputs = [ makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/gangway
    cp -r main.py config.yaml presets gangway $out/share/gangway/

    makeWrapper ${pythonEnv}/bin/python3 $out/bin/gangway \
      --add-flags $out/share/gangway/main.py \
      --set PYTHONDONTWRITEBYTECODE 1 \
      --set PYTHONUNBUFFERED 1

    runHook postInstall
  '';

  passthru = { inherit pythonDeps pythonEnv; };

  meta = {
    description = "LED controller for the gangway installation";
    mainProgram = "gangway";
    license = lib.licenses.gpl3Plus;
    platforms = lib.platforms.linux;
  };
}
