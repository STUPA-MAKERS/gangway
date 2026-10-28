/**
  Addressing, the WiFi uplink, the sensor LAN, NAT and the firewall.

  eth0 is a private LAN for the Xovis sensor only. The Pi is its router at
  10.0.0.1, hands out leases with dnsmasq, and masquerades its traffic out
  through wlan0. The old Raspberry Pi OS install did the same with
  NetworkManager, dnsmasq and a hand-written nftables ruleset.

  # Defines
  - `networking.usePredictableInterfaceNames` — off, so the links keep the
    names eth0 and wlan0 that the NAT, dnsmasq and firewall rules name
  - `systemd.network.networks."10-sensor-lan"` — eth0 at the static
    10.0.0.1/24, with no DHCP client
  - `systemd.network.networks."20-wireless"` — DHCP on wlan0
  - `networking.wireless` — wpa_supplicant with the "Iphone Hotspot"
    network, which is the FRITZ!Box at the site. The password comes from
    the `wifi-env` secret in secrets/gangway.yaml, which holds one
    `name=password` line per network. wpa_supplicant then never writes a
    password into the Nix store. wpa_supplicant runs as its own user, so
    that user owns the secret. With the default owner root it cannot read
    the file, and it starts with no password
  - `hardware.wirelessRegulatoryDatabase`, `cfg80211.ieee80211_regdom` and
    `country=DE` — the German radio rules, as the old install set in
    cmdline.txt. Without them the WiFi chip uses the world rules, which
    leave out channels 12 and 13 and the DFS channels at 5 GHz. A FRITZ!Box
    on an automatic channel can use those channels, and the Pi then does
    not see the network
  - `services.dnsmasq` — DHCP and DNS on eth0 only. 10.0.0.2 to 10.0.0.254,
    with the Pi as router and DNS server. `resolveLocalQueries` is off, so
    the Pi itself keeps using systemd-resolved
  - `networking.nat` — masquerades eth0 out through wlan0, so the sensor
    reaches the internet
  - `networking.firewall` — SSH and HTTP from anywhere. eth0 is trusted,
    so the sensor push on 8081 and the API on 8082 answer there only
  - `systemd.network.wait-online.enable` — off. Nothing on the box needs the
    uplink to boot
*/
{ ... }:

{
  flake.modules.nixos.gangway-networking =
    { config, ... }:
    {
      networking.usePredictableInterfaceNames = false;
      networking.useDHCP = false;
      networking.useNetworkd = true;
      systemd.network.wait-online.enable = false;

      systemd.network.networks = {
        "10-sensor-lan" = {
          matchConfig.Name = "eth0";
          address = [ "10.0.0.1/24" ];
          networkConfig.ConfigureWithoutCarrier = true;
          linkConfig.RequiredForOnline = "no";
        };

        "20-wireless" = {
          matchConfig.Name = "wlan0";
          networkConfig.DHCP = "yes";
          linkConfig.RequiredForOnline = "no";
        };
      };

      sops.secrets.wifi-env = {
        owner = "wpa_supplicant";
        restartUnits = [ "wpa_supplicant-wlan0.service" ];
      };

      hardware.wirelessRegulatoryDatabase = true;
      boot.kernelParams = [ "cfg80211.ieee80211_regdom=DE" ];

      networking.wireless = {
        enable = true;
        extraConfig = "country=DE";
        interfaces = [ "wlan0" ];
        secretsFile = config.sops.secrets.wifi-env.path;
        networks."Iphone Hotspot".pskRaw = "ext:hotspot_psk";
      };

      services.dnsmasq = {
        enable = true;
        resolveLocalQueries = false;
        settings = {
          interface = "eth0";
          bind-interfaces = true;
          listen-address = "10.0.0.1";
          dhcp-range = [ "10.0.0.2,10.0.0.254,255.255.255.0,12h" ];
          dhcp-option = [
            "option:router,10.0.0.1"
            "option:dns-server,10.0.0.1"
          ];
          dhcp-authoritative = true;
          log-dhcp = true;
        };
      };

      networking.nat = {
        enable = true;
        internalInterfaces = [ "eth0" ];
        externalInterface = "wlan0";
      };

      networking.firewall = {
        allowedTCPPorts = [
          22
          80
        ];
        trustedInterfaces = [ "eth0" ];
      };
    };
}
