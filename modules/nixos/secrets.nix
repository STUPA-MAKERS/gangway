/**
  sops-nix, and the secrets that secrets/gangway.yaml holds.

  The file is encrypted to two recipients, see .sops.yaml: the GPG key of the
  admin, to edit it, and the age key of the Pi, which sops-nix derives from the
  SSH host key at activation. Each module that uses a secret declares it next
  to its use, with the owner and the units to restart.

  # Inputs
  - `inputs.sops-nix.nixosModules.sops`

  # Defines
  - `sops.defaultSopsFile` — secrets/gangway.yaml
  - `sops.age.sshKeyPaths` — the ed25519 host key. The default derives it
    from `services.openssh.hostKeys` as well, and this names it explicitly so
    that a change to the host keys cannot remove it silently
  - `sops.gnupg.sshKeyPaths` — empty, so that sops-nix does not also try to
    use the host key as a GPG key
*/
{ inputs, ... }:

{
  flake.modules.nixos.secrets =
    { ... }:
    {
      imports = [ inputs.sops-nix.nixosModules.sops ];

      sops = {
        defaultSopsFile = ../../secrets/gangway.yaml;
        age.sshKeyPaths = [ "/etc/ssh/ssh_host_ed25519_key" ];
        gnupg.sshKeyPaths = [ ];
      };
    };
}
