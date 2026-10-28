/**
  Baseline services and system-wide CLI essentials. sudo has sudo.nix.

  # Defines
  - `services.openssh` — the only way in, because the box has no display. A
    key is the only accepted credential: `PasswordAuthentication` and
    `KbdInteractiveAuthentication` are both off, so a guessed password cannot
    open a session. The box can sit on a campus guest network, where anybody
    can reach port 22
  - `services.openssh.settings.PermitRootLogin` — `prohibit-password`. Root
    can log in with the admin key from users.nix, and never with a password
  - `services.openssh.hostKeys` — ed25519 only. sops-nix derives the age key of
    the host from this file, so it must exist before the first boot. See the
    README for how it gets onto the card
  - `services.avahi` — publishes gangway.local, as the old install did
  - `environment.systemPackages` — git, vim, wget, curl, tcpdump and
    wireguard-tools
*/
{ ... }:

{
  flake.modules.nixos.base =
    { pkgs, ... }:
    {
      services.openssh = {
        enable = true;
        settings = {
          PasswordAuthentication = false;
          KbdInteractiveAuthentication = false;
          PermitRootLogin = "prohibit-password";
        };
        hostKeys = [
          {
            path = "/etc/ssh/ssh_host_ed25519_key";
            type = "ed25519";
          }
        ];
      };

      services.avahi = {
        enable = true;
        nssmdns4 = true;
        publish = {
          enable = true;
          addresses = true;
        };
      };

      environment.systemPackages = with pkgs; [
        git
        vim
        wget
        curl
        tcpdump
        wireguard-tools
      ];
    };
}
