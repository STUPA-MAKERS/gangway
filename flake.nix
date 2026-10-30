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
  - `ui-kit` — the sources of @stupa-makers/ui-kit for the web UI. The
    frontend holds the kit as the submodule frontend/vendor/ui-kit, and a
    flake source does not hold a submodule. Pin this input to the commit of
    the submodule

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

    ui-kit = {
      url = "github:STUPA-MAKERS/ui-kit/4fec590edfbf76b2c20ae07dc39e36b75c32e87d";
      flake = false;
    };
  };

  outputs = inputs: inputs.flake-parts.lib.mkFlake { inherit inputs; } (inputs.import-tree ./modules);
}
