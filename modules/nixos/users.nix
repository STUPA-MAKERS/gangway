/**
  The admin account `gangway`, `fsi` as an alias of it, and the admin key
  for root. No account has a password: the SSH key is the only way in.

  # Defines
  - `users.users.gangway` — the admin account for remote debug and deploy, in
    wheel. `adminKeys` holds the keys of frederik, of jf (from the admin
    list of nixos-stupa, site/trust.nix) and of thies. `gpio`, `spi` and `i2c` are not here: NixOS has no
    such groups, and the LED service runs as root because the driver maps
    /dev/mem
  - `users.users.fsi` — a second name for the same account. It has the same
    UID, the same home, the same groups and the same key, so `ssh fsi@…`
    lands in the same session as `ssh gangway@…`. A lookup by UID returns
    the first entry, so `ls -l` and `id` show `gangway`
  - `users.enforceIdUniqueness` — off, because the alias shares the UID.
    This turns off the duplicate check for all accounts, so give every other
    account a unique UID
  - `users.groups.gangway` — the primary group of both names
  - `hashedPassword = "!"` on every account — a locked password, so no
    password login works, on SSH or on the console. Key login still works,
    because sshd checks the account through PAM. sudo works because
    sudo.nix asks no password. To recover a box with no working key, mount
    the SD card on another computer
  - `users.mutableUsers` — off, so `passwd` cannot set a password that
    survives the next activation
  - `users.users.root.openssh.authorizedKeys.keys` — the same keys, so a
    deploy or a repair can log in as root directly. base.nix allows root
    over SSH with a key only
*/
{ ... }:

let
  uid = 1000;

  adminKeys = [
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJYsQKoL4csVY7qyJn7rXskjAZECwihK0BVoNGbVbEFv frederik@beimgraben.net"
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCdhqti0d/tt3PGhmfqE2D2F2A1tl83cGagqPJ1abUzdCPDx2Sy3cbqBjitFuYT/847lwj1jblZ6H6LUjpp8iySHv+Tziykeil5bEmo+6gpyHgcrSmJ4hbfPEKZr3/FMqJACVQ0V5SxqsjtJwqN5h2l2Fspb0vdJa3nW+Fnuthec8CVgzVJQzzNGCXJJdzEstJtuS+/kgJ8c433k9XSgAz/13XNvfqKlFjO/9q6mJs+gb726WJaok6Z67j6Uqr67CH/NbUtssuya0lIbWWlMFhdQZfbrQEsphFTOsSdl0bxRQxpCiRIb3aHrG2gaHbuxBCzBd743lKh8SVYmpDe6ilWNbUV3tBgT4WV2mToIf5cUigo0PhJoRyztV5w7E7u2y9/b3j8TryKAosIuuoIxOzZwTLAGgJeRFecxohrsS3/SBV4kN/km0qXYWW8bFzV6Vlg5X/+qZ4ZBGtzoIW61tvJLAc41qn329hQEOD6m3FpPWa6poIJBq/eADyC2EWGmZc= jf@jfrey.de"
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAoYzQl2cSQCl2NEWY0/dt8LkHre11guZ7HQOtUKPBpL thies@mcds.moe"
  ];

  account = {
    inherit uid;
    isNormalUser = true;
    group = "gangway";
    home = "/home/gangway";
    hashedPassword = "!";
    extraGroups = [
      "wheel"
      "dialout"
      "video"
    ];
    openssh.authorizedKeys.keys = adminKeys;
  };
in

{
  flake.modules.nixos.users =
    { ... }:
    {
      users.mutableUsers = false;
      users.enforceIdUniqueness = false;

      users.groups.gangway.gid = uid;

      users.users.gangway = account // {
        description = "Admin user for remote debug and deploy";
      };

      users.users.fsi = account // {
        description = "Alias of gangway";
        createHome = false;
      };

      users.users.root = {
        hashedPassword = "!";
        openssh.authorizedKeys.keys = adminKeys;
      };
    };
}
