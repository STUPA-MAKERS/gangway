/**
  Host-level settings: firmware config, kernel modules, logging and the image.

  # Defines
  - `hardware.raspberry-pi.config.all.base-dt-params.audio` — off, and
    `boot.blacklistedKernelModules` keeps `snd_bcm2835` out. The analog audio
    uses PWM0, and the LED data line on GPIO 18 is PWM0 as well. Two users of
    one PWM block garble the LED signal
  - `boot.kernelParams` — `iomem=relaxed`. The kernel has
    `CONFIG_IO_STRICT_DEVMEM`, which stops an mmap of /dev/mem for register
    ranges that a kernel driver claims. The WS2805 driver maps the GPIO,
    clock, PWM and DMA registers that way, so it cannot start without this
    parameter. Raspberry Pi OS does not set the option, which is why the
    same driver ran there. The parameter avoids a kernel build, so the
    prebuilt kernel from the binary cache stays
  - `services.journald` — logs on the card, at most 64 MB. The old install
    appended its output to a file on the SD card without a limit, which
    helped wear the card out. The limit keeps the writes small, and the
    logs survive a power cut, so a failed boot can be read from the card
    on another computer
  - `system.nixos.tags` — the board variant, the bootloader and the kernel
    version, so that the boot menu names what a generation holds
  - `boot.supportedFilesystems.zfs` — off. The sd-image profile pulls it in,
    ZFS does not build against the vendor kernel, and this host has no use
    for it
  - `sdImage.compressImage` — off, so that dd can write the image directly.
    `sdImage.expandOnBoot` stays on, which is the default, so the root
    partition grows to fill the card on the first boot
*/
{ ... }:

{
  flake.modules.nixos.gangway-host =
    { config, lib, ... }:
    {
      hardware.raspberry-pi.config.all.base-dt-params.audio.enable = false;
      boot.blacklistedKernelModules = [ "snd_bcm2835" ];
      boot.kernelParams = [ "iomem=relaxed" ];

      services.journald.extraConfig = ''
        Storage=persistent
        SystemMaxUse=64M
      '';

      system.nixos.tags =
        let
          cfg = config.boot.loader.raspberry-pi;
        in
        [
          "raspberry-pi-${cfg.variant}"
          cfg.bootloader
          config.boot.kernelPackages.kernel.version
        ];

      boot.supportedFilesystems.zfs = lib.mkForce false;

      sdImage.compressImage = false;

      system.stateVersion = "26.05";
    };
}
