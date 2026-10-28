/**
  Generation cleanup.

  # Defines
  - `nix.gc` — each week, delete store paths and system generations more than
    30 days old. Each host limits its boot entries with `configurationLimit`
*/
{ ... }:

{
  flake.modules.nixos.gc =
    { ... }:
    {
      nix.gc = {
        automatic = true;
        dates = "weekly";
        options = "--delete-older-than 30d";
        persistent = true; # catch up if the machine was off at the scheduled time
      };
    };
}
