/**
  sudo for the admin account.

  # Defines
  - `security.sudo.wheelNeedsPassword` — off. SSH accepts a key and nothing
    else, so the password prompt guards nothing that the key did not already
    open. It only blocks an unattended `nixos-rebuild switch` over SSH. The
    trade is that anybody who holds the key holds root
*/
{ ... }:

{
  flake.modules.nixos.sudo =
    { ... }:
    {
      security.sudo.wheelNeedsPassword = false;
    };
}
