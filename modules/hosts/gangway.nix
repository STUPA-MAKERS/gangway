/**
  The gangway Pi, and its image output.

  # Inputs
  - `inputs.nixos-raspberrypi.lib.nixosSystem` — a drop-in for
    `nixpkgs.lib.nixosSystem`. It injects the vendor overlays, sets the host
    platform, and makes the device trust the cachix of the flake
  - `inputs.nixos-raspberrypi.nixosModules.raspberry-pi-4.base` — the board
    support: the vendor kernel, the matched firmware, and the bootloader
  - `inputs.nixos-raspberrypi.nixosModules.sd-image` — the flashable image.
    The running system keeps it, because it defines the firmware partition

  # Defines
  - `flake.nixosConfigurations.gangway` — the gangway profile plus the board
    support
  - `flake.gangway.sd-image`, so that `nix build .#gangway.sd-image` writes
    the image. `perSystem.packages` cannot hold it, because its type takes a
    package and not a nested set
*/
{ inputs, config, ... }:

{
  flake = {
    nixosConfigurations.gangway = inputs.nixos-raspberrypi.lib.nixosSystem {
      specialArgs = { inherit inputs; };
      modules = [
        config.flake.modules.nixos.gangway
        inputs.nixos-raspberrypi.nixosModules.raspberry-pi-4.base
        inputs.nixos-raspberrypi.nixosModules.sd-image
        { networking.hostName = "gangway"; }
      ];
    };

    gangway.sd-image = config.flake.nixosConfigurations.gangway.config.system.build.sdImage;
  };
}
