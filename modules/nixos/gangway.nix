/**
  The gangway backend as a systemd service, and the package of the web UI.

  The backend and the UI both write their state at run time: the active
  animation goes into config.yaml, and the presets go into presets/ next to
  it. Both live in /var/lib/gangway, outside the Nix store.

  # Inputs
  - `withSystem "x86_64-linux"` — the web UI package of the build machine.
    The web UI is static files with no store references, so the same files
    work on the Pi. An x86_64 build takes about a minute; an aarch64 build
    under binfmt emulation takes many minutes

  # Defines
  - `services.gangway` — `enable`, `package`, `frontendPackage` and
    `stateDir`. `frontendPackage` holds the static files of the web UI,
    which nginx serves (modules/nixos/services.nix)
  - `systemd.services.gangway` — the LED controller, the Xovis receiver on
    8081 and the API on 8082. It runs as root, because the WS2805 driver
    maps /dev/mem to drive PWM0 through DMA. `preStart` copies the packaged
    config.yaml and each packaged preset into the state directory if it is
    not there yet. It never overwrites a file, so the changes from the web
    UI stay. `cp --update=none` skips with exit code 0, where `cp -n` fails
    on newer coreutils. `GANGWAY_CONFIG` points the app at that copy.
    The `gangway-env` secret holds `API_KEY=…`, the key the web UI asks for
*/
{ withSystem, ... }:

{
  flake.modules.nixos.gangway-app =
    {
      config,
      lib,
      pkgs,
      ...
    }:
    let
      cfg = config.services.gangway;
    in
    {
      options.services.gangway = {
        enable = lib.mkEnableOption "the gangway LED controller" // {
          default = true;
        };

        package = lib.mkOption {
          type = lib.types.package;
          default = pkgs.callPackage ../../nix/gangway.nix { };
          defaultText = lib.literalExpression "pkgs.callPackage ../../nix/gangway.nix { }";
          description = "The backend package to run.";
        };

        frontendPackage = lib.mkOption {
          type = lib.types.package;
          default = withSystem "x86_64-linux" ({ config, ... }: config.packages.gangway-frontend);
          defaultText = lib.literalExpression "the gangway-frontend package of x86_64-linux";
          description = "The static files of the web UI, which nginx serves.";
        };

        stateDir = lib.mkOption {
          type = lib.types.path;
          default = "/var/lib/gangway";
          description = ''
            The directory that holds config.yaml and presets/. The backend
            unit creates it through StateDirectory, so it must stay below
            /var/lib.
          '';
        };
      };

      config = lib.mkIf cfg.enable {
        sops.secrets.gangway-env.restartUnits = [ "gangway.service" ];

        systemd.services.gangway = {
          description = "Gangway LED controller";
          wantedBy = [ "multi-user.target" ];
          after = [ "network.target" ];
          environment.GANGWAY_CONFIG = "${cfg.stateDir}/config.yaml";
          preStart = ''
            if [ ! -e ${cfg.stateDir}/config.yaml ]; then
              install -m 644 ${cfg.package}/share/gangway/config.yaml ${cfg.stateDir}/config.yaml
            fi
            mkdir -p ${cfg.stateDir}/presets
            cp --update=none --no-preserve=mode ${cfg.package}/share/gangway/presets/*.yaml ${cfg.stateDir}/presets/
          '';
          serviceConfig = {
            ExecStart = lib.getExe cfg.package;
            WorkingDirectory = cfg.stateDir;
            StateDirectory = lib.removePrefix "/var/lib/" cfg.stateDir;
            EnvironmentFile = config.sops.secrets.gangway-env.path;
            Restart = "always";
            RestartSec = 2;
          };
        };
      };
    };
}
