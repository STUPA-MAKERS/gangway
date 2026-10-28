/**
  Timezone, locale, and German console keyboard layout.

  # Defines
  - `time.timeZone`, `i18n` and `console.keyMap`
*/
{ ... }:

{
  flake.modules.nixos.locale =
    { ... }:
    {
      time.timeZone = "Europe/Berlin";
      i18n.defaultLocale = "en_GB.UTF-8";
      console.keyMap = "de";
    };
}
