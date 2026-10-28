/**
  Flake-parts wiring: the module aggregator, target systems, and formatter.

  # Inputs
  - `inputs.flake-parts` — flakeModules.modules, the aggregator behind
    `flake.modules.*`

  # Defines
  - `systems` — aarch64-linux is the Pi, and x86_64-linux lets the formatter
    run on the build machine
  - `perSystem.formatter` — nixfmt over the Nix files only. `nix fmt` hands
    every file to the formatter, and this repo also holds Python and JavaScript
*/
{ inputs, ... }:

{
  imports = [ inputs.flake-parts.flakeModules.modules ];

  systems = [
    "aarch64-linux"
    "x86_64-linux"
  ];

  perSystem =
    { pkgs, ... }:
    {
      formatter = pkgs.writeShellApplication {
        name = "fmt-nix";
        runtimeInputs = [
          pkgs.findutils
          pkgs.nixfmt
        ];
        text = ''
          find "''${@:-.}" -name '*.nix' -type f -print0 | xargs -0 -r nixfmt
        '';
      };
    };
}
