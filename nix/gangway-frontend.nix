/**
  The gangway web UI, an Angular single-page app packaged from `frontend/`.

  # Inputs
  - `frontend/` — the app and its package-lock.json. `npmDepsHash` pins the
    npm dependencies. Change it after every change to package-lock.json
  - `ui-kit` — the sources of @stupa-makers/ui-kit, the flake input `ui-kit`.
    The tsconfig path of the app points into frontend/vendor/ui-kit, a git
    submodule. A flake source does not hold the submodule, so `preBuild`
    copies the input into its place. Keep the input on the commit of the
    submodule

  # Defines
  - the `gangway-frontend` derivation — `ng build`, then the static files of
    `dist/gangway/browser` at the top of `$out`. nginx serves them as `/`
    (modules/nixos/services.nix). There is no server process
*/
{
  lib,
  buildNpmPackage,
  nodejs,
  ui-kit,
}:

buildNpmPackage {
  pname = "gangway-frontend";
  version = "0.2.0";

  src = lib.fileset.toSource {
    root = ../frontend;
    fileset = lib.fileset.difference ../frontend (
      lib.fileset.unions [
        (lib.fileset.maybeMissing ../frontend/node_modules)
        (lib.fileset.maybeMissing ../frontend/dist)
        (lib.fileset.maybeMissing ../frontend/.angular)
        (lib.fileset.maybeMissing ../frontend/vendor)
      ]
    );
  };

  inherit nodejs;
  npmDepsHash = "sha256-W+U1YKN1hRpqFUz7stEFQ6IDWYsGQTBEbOY1A3FeXcA=";
  npmBuildScript = "build";

  env = {
    NG_CLI_ANALYTICS = "false";
    CI = "true";
  };

  preBuild = ''
    mkdir -p vendor
    cp -r ${ui-kit} vendor/ui-kit
    chmod -R u+w vendor/ui-kit
  '';

  installPhase = ''
    runHook preInstall
    mkdir -p $out
    cp -r dist/gangway/browser/. $out/
    runHook postInstall
  '';

  meta = {
    description = "Web UI for the gangway LED controller";
    license = lib.licenses.gpl3Plus;
    platforms = lib.platforms.all;
  };
}
