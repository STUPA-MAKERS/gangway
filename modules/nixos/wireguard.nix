/**
  The two WireGuard tunnels, as systemd-networkd netdevs. Both come from the
  wg-quick files on the old install, `beimgraben.net.conf` and
  `vpn.stupa.conf`.

  # Defines
  - `systemd.network.netdevs."30-beimgraben.net"` — 10.66.66.200/24, to the
    peer at 167.235.148.67:55700. The old file said
    `AllowedIPs = 10.66.66.0/0`, which is the whole IPv4 space. The /24 here
    is what the address and the route make clear was meant. A /0 would send
    all traffic, the WiFi uplink included, into the tunnel
  - `systemd.network.netdevs."31-vpn.stupa"` — 10.0.2.3/32, to
    vpn.reutlingen.university:51820, for 10.0.2.0/24 and 192.168.200.0/24.
    MTU 1420, as the portal file sets
  - `sops.secrets.wg-*` — the private and preshared keys. systemd-networkd
    reads them as the `systemd-network` user, so that user owns them
*/
{ ... }:

{
  flake.modules.nixos.gangway-wireguard =
    { config, lib, ... }:
    let
      networkdSecret = {
        owner = "systemd-network";
        group = "systemd-network";
        mode = "0400";
        restartUnits = [ "systemd-networkd.service" ];
      };

      secret = name: config.sops.secrets.${name}.path;
    in
    {
      sops.secrets = lib.genAttrs [
        "wg-beimgraben-private-key"
        "wg-beimgraben-preshared-key"
        "wg-stupa-private-key"
        "wg-stupa-preshared-key"
      ] (_: networkdSecret);

      systemd.network.netdevs = {
        "30-beimgraben.net" = {
          netdevConfig = {
            Name = "beimgraben.net";
            Kind = "wireguard";
          };
          wireguardConfig.PrivateKeyFile = secret "wg-beimgraben-private-key";
          wireguardPeers = [
            {
              PublicKey = "suRh4nSdq3AsC1P7j5rJdbjo03eyFs8+2ASyn6hNxXw=";
              PresharedKeyFile = secret "wg-beimgraben-preshared-key";
              Endpoint = "167.235.148.67:55700";
              AllowedIPs = [ "10.66.66.0/24" ];
              PersistentKeepalive = 30;
            }
          ];
        };

        "31-vpn.stupa" = {
          netdevConfig = {
            Name = "vpn.stupa";
            Kind = "wireguard";
            MTUBytes = "1420";
          };
          wireguardConfig.PrivateKeyFile = secret "wg-stupa-private-key";
          wireguardPeers = [
            {
              PublicKey = "ZdND+2k1kP5V9ZLiGP4MXtEUd1sZ/RAwLmOPX4HTyzc=";
              PresharedKeyFile = secret "wg-stupa-preshared-key";
              Endpoint = "vpn.reutlingen.university:51820";
              AllowedIPs = [
                "10.0.2.0/24"
                "192.168.200.0/24"
              ];
              PersistentKeepalive = 16;
            }
          ];
        };
      };

      systemd.network.networks = {
        "30-beimgraben.net" = {
          matchConfig.Name = "beimgraben.net";
          address = [ "10.66.66.200/24" ];
          linkConfig.RequiredForOnline = "no";
        };

        "31-vpn.stupa" = {
          matchConfig.Name = "vpn.stupa";
          address = [ "10.0.2.3/32" ];
          routes = [
            { Destination = "10.0.2.0/24"; }
            { Destination = "192.168.200.0/24"; }
          ];
          linkConfig.RequiredForOnline = "no";
        };
      };
    };
}
