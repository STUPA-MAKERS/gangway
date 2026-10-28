/**
  NixOS for the Raspberry Pi 4B that drives the gangway LED installation:
  flake-parts mkFlake over (import-tree ./modules), so every output comes from
  the modules tree (dendritic pattern).

  # Inputs
  - `nixos-raspberrypi` — the board support. It ships the vendor kernel, the
    matched firmware and device trees, and the `/boot/firmware` bootloader
    infrastructure. `nixConfig` adds its cachix, which holds the prebuilt
    vendor kernel. Without that cache the kernel compiles from source for
    hours under emulation
  - `nixpkgs` — follows `nixos-raspberrypi`, so the system, the cachix and the
    package set all agree on one nixpkgs
  - `sops-nix` — decrypts secrets/gangway.yaml on the Pi with its SSH host key
  - `import-tree` — imports every module under ./modules. It skips any path
    that holds `/_`, which is why the packages live in ./nix instead

  # Defines
  - `outputs` — flake-parts mkFlake over the modules tree
*/
{
  description = "NixOS configuration for the gangway LED installation on a Raspberry Pi 4B.";

  nixConfig = {
    extra-substituters = [ "https://nixos-raspberrypi.cachix.org" ];
    extra-trusted-public-keys = [
      "nixos-raspberrypi.cachix.org-1:4iMO9LXa8BqhU+Rpg6LQKiGa2lsNh/j2oiYLNOQ5sPI="
    ];
  };

  inputs = {
    nixos-raspberrypi.url = "github:nvmd/nixos-raspberrypi/main";
    nixpkgs.follows = "nixos-raspberrypi/nixpkgs";

    flake-parts.url = "github:hercules-ci/flake-parts";
    import-tree.url = "github:vic/import-tree";

    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs: inputs.flake-parts.lib.mkFlake { inherit inputs; } (inputs.import-tree ./modules);
}
