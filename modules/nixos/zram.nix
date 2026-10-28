/**
  ZRAM swap. A rebuild on the device then does not swap to the SD card.

  # Defines
  - `zramSwap`
*/
{ ... }:

{
  flake.modules.nixos.zram =
    { ... }:
    {
      zramSwap = {
        enable = true;
        algorithm = "zstd";
        memoryPercent = 150;
      };

      boot.kernel.sysctl = {
        "vm.swappiness" = 180;
        "vm.watermark_boost_factor" = 0;
        "vm.watermark_scale_factor" = 125;
        "vm.page-cluster" = 0;
      };
    };
}
