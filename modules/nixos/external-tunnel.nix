/**
  The WireGuard tunnel to the StuPa gateway, which publishes the web UI as
  gangway.reutlingen.university behind an authentik login.

  The gateway runs the login (an oauth2-proxy gate) and proxies to nginx on
  this Pi through the tunnel. The gateway side lives in the nixos-stupa
  repo. The tunnel uses the subnet for external services, 10.44.0.0/24: the
  gateway is 10.44.0.1, and this Pi is 10.44.0.2.

  The Pi is behind the NAT of the FRITZ!Box, so the gateway cannot open the
  tunnel. The Pi dials out to the public endpoint of the gateway, and the
  keepalive holds the NAT mapping open, so the gateway can reach the Pi at
  any time.

  # Defines
  - `systemd.network.netdevs."40-wg-ext"` — the interface `wg-ext` with one
    peer, the gateway. `AllowedIPs` is the gateway address only, so the
    tunnel carries traffic to and from the gateway and nothing else
  - `systemd.network.networks."40-wg-ext"` — 10.44.0.2/24 on `wg-ext`
  - `networking.firewall.interfaces.wg-ext` — port 80 only. The interface
    is not trusted, so the Xovis receiver on 8081 and the API on 8082 stay
    closed to the tunnel
  - the API key for requests through the tunnel. Only the gateway reaches
    10.44.0.2, and it forwards a request only after the authentik login, so
    nginx adds `X-API-Key` itself to such a request on `/api/`, and the web
    UI works with no key in the browser. Any other request keeps the header
    of the client, so the key stays necessary on the FRITZ!Box LAN
  - `systemd.services.gangway-nginx-api-key` — writes the snippet with the
    key from the `gangway-env` secret to /run/gangway-nginx, readable by
    nginx only, so the key never goes into the Nix store. The secret can
    give the value in quotes. systemd removes them for the backend, so the
    unit removes one pair of matching quotes as well; else the header holds
    the quotes, and the backend refuses the key.
    nginx reads the snippet only when it starts or reloads, so the unit
    reloads a running nginx after it writes a new snippet. `--no-block`
    keeps the reload from waiting on a switch that runs this unit nginx includes
    the snippet with a glob, because a glob that matches no file is valid:
    the check of the nginx config at build time then passes, and nginx
    still starts if the snippet is missing. The unit escapes the key for an
    nginx string: a backslash before `\` and `"`, and `''${gangway_dollar}`
    for `$`, because nginx has no escape for `$` and reads it as the start
    of a variable. `$gangway_dollar` is a `geo` variable whose value is `$`.
    It refuses a key with a control character, because one cannot be
    written into the snippet
  - `sops.secrets.wg-external-private-key` — the private key of the Pi.
    systemd-networkd reads it as the `systemd-network` user, so that user
    owns it
*/
{ ... }:

{
  flake.modules.nixos.gangway-external-tunnel =
    { config, ... }:
    {
      sops.secrets.wg-external-private-key = {
        owner = "systemd-network";
        group = "systemd-network";
        mode = "0400";
        restartUnits = [ "systemd-networkd.service" ];
      };

      systemd.network.netdevs."40-wg-ext" = {
        netdevConfig = {
          Name = "wg-ext";
          Kind = "wireguard";
        };
        wireguardConfig.PrivateKeyFile = config.sops.secrets.wg-external-private-key.path;
        wireguardPeers = [
          {
            PublicKey = "BzptXED3aFxLHcsJP8kot8eedlDRjKE350wwkbzK1gM=";
            Endpoint = "159.69.20.25:51821";
            AllowedIPs = [ "10.44.0.1/32" ];
            PersistentKeepalive = 25;
          }
        ];
      };

      systemd.network.networks."40-wg-ext" = {
        matchConfig.Name = "wg-ext";
        address = [ "10.44.0.2/24" ];
        linkConfig.RequiredForOnline = "no";
      };

      networking.firewall.interfaces.wg-ext.allowedTCPPorts = [ 80 ];

      services.nginx.appendHttpConfig = ''
        geo $gangway_dollar { default "$"; }
      '';

      services.nginx.virtualHosts.gangway.locations."/api/".extraConfig = ''
        set $gangway_api_key $http_x_api_key;
        include /run/gangway-nginx/*.conf;
        proxy_set_header X-API-Key $gangway_api_key;
      '';

      sops.secrets.gangway-env.restartUnits = [
        "gangway-nginx-api-key.service"
        "nginx.service"
      ];

      systemd.services.gangway-nginx-api-key = {
        description = "Write the API key snippet for nginx";
        wantedBy = [ "nginx.service" ];
        before = [ "nginx.service" ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          RuntimeDirectory = "gangway-nginx";
          RuntimeDirectoryMode = "0750";
          RuntimeDirectoryPreserve = true;
          Group = "nginx";
          UMask = "0027";
        };
        script = ''
          key=$(sed -n 's/^API_KEY=//p' ${config.sops.secrets.gangway-env.path})
          case "$key" in
            \"*\") key=''${key#\"}; key=''${key%\"} ;;
            \'*\') key=''${key#\'}; key=''${key%\'} ;;
          esac
          if [ -z "$key" ] || printf '%s' "$key" | grep -q '[[:cntrl:]]'; then
            echo "API_KEY is empty or holds a control character" >&2
            exit 1
          fi
          escaped=$(printf '%s' "$key" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\$/''${gangway_dollar}/g')
          printf 'if ($server_addr = 10.44.0.2) { set $gangway_api_key "%s"; }\n' "$escaped" \
            > /run/gangway-nginx/api-key.conf
        '';
        postStart = ''
          if systemctl is-active --quiet nginx.service; then
            systemctl reload --no-block nginx.service
          fi
        '';
      };
    };
}
