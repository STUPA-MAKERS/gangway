/**
  The gangway packages, and the shell to develop them in.

  # Inputs
  - `inputs.ui-kit` — the sources of @stupa-makers/ui-kit for the web UI

  # Defines
  - `perSystem.packages.gangway` — the backend, from `nix/gangway.nix`
  - `perSystem.packages.gangway-frontend` — the static files of the web UI,
    from `nix/gangway-frontend.nix`
  - `perSystem.packages.rpi-ws2805` — the LED driver, from
    `nix/rpi-ws2805.nix`
  - `perSystem.devShells.default` — the run-time Python dependencies of the
    backend plus pytest and httpx, ruff and basedpyright, Node.js and npm for
    the frontend, and sops and ssh-to-age for secrets/.

    The shellHook builds a .venv that points at the dev environment. Editors
    then use the language servers from there in place of the ones they
    download, which are linked against a generic Linux and do not run on
    NixOS. The same .venv tells basedpyright which interpreter holds the
    dependencies
*/
{ inputs, ... }:

{
  perSystem =
    { pkgs, ... }:
    let
      rpi-ws2805 = pkgs.callPackage ../../nix/rpi-ws2805.nix { };
      gangway = pkgs.callPackage ../../nix/gangway.nix { inherit rpi-ws2805; };

      pythonEnv = pkgs.python3.withPackages (
        ps:
        gangway.pythonDeps ps
        ++ [
          ps.httpx
          ps.pytest
        ]
      );

      devEnv = pkgs.buildEnv {
        name = "gangway-dev-env";
        paths = [
          pythonEnv
          pkgs.ruff
          pkgs.basedpyright
        ];
      };
    in
    {
      packages = {
        inherit gangway rpi-ws2805;
        gangway-frontend = pkgs.callPackage ../../nix/gangway-frontend.nix {
          inherit (inputs) ui-kit;
        };
      };

      devShells.default = pkgs.mkShell {
        packages = [
          devEnv
          pkgs.nodejs
          pkgs.sops
          pkgs.ssh-to-age
        ];

        shellHook = ''
          root=$(${pkgs.git}/bin/git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")

          mkdir -p "$root/.venv"
          ln -sfn ${devEnv}/bin "$root/.venv/bin"
          ln -sfn ${devEnv}/lib "$root/.venv/lib"
          cat > "$root/.venv/pyvenv.cfg" <<VENV
          home = ${pythonEnv}/bin
          executable = ${pythonEnv}/bin/python3
          version = ${pkgs.python3.version}
          include-system-site-packages = false
          VENV
        '';
      };
    };
}
