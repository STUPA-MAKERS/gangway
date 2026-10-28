/**
  nginx in front of the app.

  # Defines
  - `services.nginx.virtualHosts.gangway` — the default server on port 80,
    as `nginx/gangway.nginx.conf` on the old install:
    - `/` goes to the web UI on 127.0.0.1:8083
    - `/api/` goes to the backend on 127.0.0.1:8082
    - `/live` goes to the live scene of the Xovis sensor at 10.0.0.250, with
      the sensor's HTTP basic credentials. The backend reads the camera
      image for the homography view from here
*/
{ ... }:

{
  flake.modules.nixos.gangway-services =
    { ... }:
    {
      services.nginx = {
        enable = true;
        virtualHosts.gangway = {
          default = true;
          locations = {
            "/".proxyPass = "http://127.0.0.1:8083/";
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
