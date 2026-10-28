/**
  Nix daemon settings. Generation cleanup is in gc.nix.

  # Defines
  - `nix.settings` — flakes, the trusted users, and store optimisation
*/
{ ... }:

{
  flake.modules.nixos.nix =
    { ... }:
    {
      nix.settings = {
        experimental-features = [
          "nix-command"
          "flakes"
        ];
        trusted-users = [
          "root"
          "gangway"
          "fsi"
        ];
        auto-optimise-store = true;
      };
    };
}
