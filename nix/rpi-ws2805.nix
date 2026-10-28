/**
  The `rpi_ws2805` Python module, packaged from `rpi-ws2805-python/library`.

  # Inputs
  - `rpi-ws2805-python/library` — the patched rpi_ws281x driver with WS2805
    support. The SWIG wrapper `rpi_ws2805_wrap.c` is checked in, so the build
    needs no SWIG

  # Defines
  - the `rpi-ws2805` derivation — a setuptools build of the C extension
    `_rpi_ws2805` and the `rpi_ws2805` package. The driver touches /dev/mem
    and the PWM registers only when a strip starts, so `pythonImportsCheck`
    runs on the build machine without hardware
*/
{ lib, python3Packages }:

python3Packages.buildPythonPackage {
  pname = "rpi-ws2805";
  version = "5.0.0";
  pyproject = true;

  src = lib.fileset.toSource {
    root = ../rpi-ws2805-python/library;
    fileset = lib.fileset.unions [
      ../rpi-ws2805-python/library/pyproject.toml
      ../rpi-ws2805-python/library/setup.py
      ../rpi-ws2805-python/library/MANIFEST.in
      ../rpi-ws2805-python/library/README.rst
      ../rpi-ws2805-python/library/CHANGELOG.txt
      ../rpi-ws2805-python/library/LICENSE
      ../rpi-ws2805-python/library/version.h
      ../rpi-ws2805-python/library/rpi_ws2805_wrap.c
      ../rpi-ws2805-python/library/rpi_ws2805
      ../rpi-ws2805-python/library/lib
    ];
  };

  build-system = [ python3Packages.setuptools ];

  pythonImportsCheck = [ "rpi_ws2805" ];

  meta = {
    description = "Userspace Raspberry Pi PWM driver for WS2805 LED strips";
    license = lib.licenses.bsd2;
    platforms = lib.platforms.linux;
  };
}
