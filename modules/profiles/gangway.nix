/**
  Gangway profile. This is the module set that the Pi host uses.

  # Defines
  - `flake.modules.nixos.gangway` — every system module the host composes
*/
{ config, ... }:

{
  flake.modules.nixos.gangway.imports = with config.flake.modules.nixos; [
    nix
    gc
    locale
    users
    base
    sudo
    zram
    secrets
    gangway-host
    gangway-networking
    gangway-wireguard
    gangway-services
    gangway-app
  ];
}
