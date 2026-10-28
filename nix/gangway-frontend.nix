/**
  The gangway web UI, a Next.js app packaged from `frontend/`.

  # Inputs
  - `frontend/` — the app and its package-lock.json. `npmDepsHash` pins the
    npm dependencies. Change it after every change to package-lock.json
  - `inter` — the Inter font. `next/font/google` downloads the font at build
    time, and the build sandbox has no network, so `app/layout.js` uses
    `next/font/local`, and `preBuild` copies the font file into place

  # Defines
  - the `gangway-frontend` derivation — `next build`, then the build output,
    `public/` and the run-time `node_modules` in `lib/gangway-frontend`.
    `bin/gangway-frontend` runs `next start` in that directory. It binds the
    address in `GANGWAY_FRONTEND_HOST` and the port in
    `GANGWAY_FRONTEND_PORT`, which default to 127.0.0.1 and 8083, because
    nginx is the only client. The wrapper expands both at run time
*/
{
  lib,
  buildNpmPackage,
  makeWrapper,
  nodejs,
  inter,
}:

buildNpmPackage {
  pname = "gangway-frontend";
  version = "0.1.0";

  src = lib.fileset.toSource {
    root = ../frontend;
    fileset = lib.fileset.difference ../frontend (
      lib.fileset.maybeMissing ../frontend/app/fonts/InterVariable.ttf
    );
  };

  npmDepsHash = "sha256-le9vg0bF5uFRD5YxW7qbHiTqXg1xmK8AFdLOPAzEwOo=";

  nativeBuildInputs = [ makeWrapper ];

  env.NEXT_TELEMETRY_DISABLED = "1";

  preBuild = ''
    mkdir -p app/fonts
    cp ${inter}/share/fonts/truetype/InterVariable.ttf app/fonts/
  '';

  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/gangway-frontend
    cp -r .next public node_modules package.json next.config.js $out/lib/gangway-frontend/

    makeWrapper ${lib.getExe nodejs} $out/bin/gangway-frontend \
      --chdir $out/lib/gangway-frontend \
      --set-default NODE_ENV production \
      --set-default GANGWAY_FRONTEND_HOST 127.0.0.1 \
      --set-default GANGWAY_FRONTEND_PORT 8083 \
      --add-flags "$out/lib/gangway-frontend/node_modules/next/dist/bin/next start" \
      --add-flags '-H "$GANGWAY_FRONTEND_HOST" -p "$GANGWAY_FRONTEND_PORT"'

    runHook postInstall
  '';

  meta = {
    description = "Web UI for the gangway LED controller";
    mainProgram = "gangway-frontend";
    license = lib.licenses.gpl3Plus;
    platforms = lib.platforms.linux;
  };
}
