/**
  nginx in front of the app.

  # Defines
  - `services.nginx.virtualHosts.gangway` — the default server on port 80,
    as `nginx/gangway.nginx.conf` on the old install:
    - `/` serves the static files of the web UI
      (`services.gangway.frontendPackage`). An unknown path gets
      index.html, so the routes of the single-page app work on a reload
    - `/api/` goes to the backend on 127.0.0.1:8082
    - `/live` goes to the live scene of the Xovis sensor at 10.0.0.250, with
      the sensor's HTTP basic credentials. The backend reads the camera
      image for the homography view from here
*/
{ ... }:

{
  flake.modules.nixos.gangway-services =
    { config, ... }:
    {
      services.nginx = {
        enable = true;
        virtualHosts.gangway = {
          default = true;
          locations = {
            "/" = {
              root = config.services.gangway.frontendPackage;
              tryFiles = "$uri $uri/ /index.html";
            };
            "/api/".proxyPass = "http://127.0.0.1:8082/api/";
            "/live" = {
              proxyPass = "http://10.0.0.250:80/api/scene/rectr";
              extraConfig = ''
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header Authorization "Basic YWRtaW46cGFzcw==";
              '';
            };
          };
        };
      };
    };
}
