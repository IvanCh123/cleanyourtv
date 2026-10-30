# Handoff: TCL G08 cleanup (27 October 2026)

For the next agent working on this TV from another computer. Read `AGENTS.md` and `PROMPT.md` first; the
safety rules there still apply.

## The TV
- TCL Smart TV Pro, device `G08`, product `G08_4K_GB`, Android 14 (Google TV), firmware `UTT2.250416.001 AU02`,
  MediaTek tcl9618, 32-bit userspace (armeabi-v7a), SDK 34.
- On **Ethernet** (`eth0`), LAN address `192.168.68.100`. No saved Wi-Fi networks. Nothing plugged into USB.
- Signed in to a Google account. The closest repo lists are `examples/tcl-g08-us-google-tv` (same Android 14 build
  family) and `examples/tcl-g08-au-android12`.

## Current state
- **ADB is closed.** USB debugging is off, authorisations were revoked, the TV was rebooted, and
  `tools/adb-closed.py 192.168.68.100` reported 5555 closed. Wireless debugging was never on. To work on the
  TV again, the owner has to turn USB debugging (Developer options) back on and accept the prompt for the new
  computer's ADB key.
- **32 packages disabled** with `pm disable-user --user 0`, in batches with screenshots in between. All stayed
  disabled after two reboots:
  - Batch 1, TCL promo/demo: `com.tcl.messagebox`, `com.tcl.esticker`, `com.tcl.hotelmenu`, `com.tcl.exhibit`,
    `com.tcl.tv.tclhome_passive`, `com.tcl.dashboard`
  - Batch 2, telemetry/ads: `com.tcl.logkit`, `com.google.android.feedback`, `com.android.tv.feedbackconsent`,
    `com.android.adservices.api`, `com.android.ondevicepersonalization.services`, `com.android.federatedcompute.services`
  - Batch 3, extras: `com.tcl.ocean.instructions`, `com.tcl.hearaid`, `com.tcl.t_solo`, `com.tcl.repairguide`,
    `com.tcl.usercenter`, `com.tcl.channelplus`, `com.tcl.waterfall.overseas`, `com.tcl.smartalexa`, `com.tcl.magiconnectfree`
  - Batch 4: `com.tcl.android.webview`, `com.mediatek.support.webview`, `com.mediatek.backgrounddetection`,
    `com.mediatek.network`, `com.android.printspooler`, `com.google.android.syncadapters.calendar`,
    `com.google.android.onetimeinitializer`, `com.tcl.gamebar`, `com.google.android.play.games`
  - Batch 5: `com.google.android.tungsten.setupwraith` (with `FORCE_SETUPWRAITH=1`, owner agreed: Ethernet, no
    saved Wi-Fi), then `com.google.android.apps.tv.launcherx` (disabled by `launcher/build-and-install.ps1`)
- **Kept by the owner's choice:** every streaming app (Netflix, YouTube, Prime Video, Disney+, Apple TV, Spotify,
  Crunchyroll, Twitch), Chromecast (`mediashell`), AirPlay (`com.tcl.airplay2`, `com.mediatek.AirplayAPK`,
  `com.mediatek.airplaydaemon`), Miracast (`com.tcl.miracast`), Google Assistant (`katniss`), YouTube Music.
- **Kept on purpose (load-bearing or unclear):** `com.tcl.suspension`, `com.tcl.interactive`, `com.tcl.ttvs`
  (Input key panel / TIAS chain), `com.tcl.autopair`, `com.tcl.guard` (retries every 5 s when disabled),
  `com.tcl.UpdatePeripheral`, `com.tcl.eva`, `com.google.android.tts`, `dreamx`, `com.tpa.kb` (unknown, no components).
- **Launcher** `com.gathin.tvhome` is Home (`mFocusedApp` confirmed, also after a reboot), installed with
  `launcher\build-and-install.ps1 -HomeKeyService`. The TV boots straight to it; the firmware does not open
  Live TV by itself, so neither `power_on_home` nor `boot_to_live_tv` is set.
- **Private DNS** is `dns.adguard-dns.com` (mode `hostname`; before that it was unset). Undo:
  `settings put global private_dns_mode opportunistic`.

## Launcher config (committed)
`launcher/app/src/main/res/values/config.xml`, changed from the repo default:
- `dock_apps`: Netflix, YouTube, Disney+, Apple TV; `columns` 4 (default)
- `hidden_apps`: `com.tcl.tv`, `com.tcl.suspension`, `com.tcl.partnercustomizer`
- `live_tv_package`: `com.tcl.tv`
- `settings_key_keycodes`: `83` (the gear button)
- `app_keys`: `4062` Netflix, `190` YouTube, `4099` Prime Video, `4020` (TCL Channel button) to Crunchyroll,
  `4001` (TV button) to Twitch. All checked by the owner with the real remote.

Theme `themes/japan/` (committed): Hokusai's Great Wave (public domain). `81g0zmaqeevh1.jpeg` is the owner's
original and `wallpaper.jpg` the 1920x1080 crop of it. `config.json` sets: wallpaper on, dim 50, `ambient_glow`
false, dock opacity 70, `reorder_button` and `tile_menu` true. Push it with
`tools\theme.ps1 -TvHost <tv ip> themes\japan`. It has no `screenshot.jpg`, so it is a personal theme and not
ready for an upstream PR.

## Known trade-off
With HomeKeyService bound, holding volume steps once per press instead of ramping. The owner tested it both
ways and chose the buttons. This matches the 75Q7CXB on AU02 in `docs/devices/tcl-55p71b-g09-key-repeat.md`.
To get the ramp back and lose the app buttons, set `key_filter` false and reinstall.

## Remote button codes (with launcherx disabled)
| Button | Keycode | HID usage | Without a helper |
|---|---|---|---|
| Settings (gear) | 83 | | reaches Home |
| Netflix | 4062 | 0x000c0051 | reaches the focused window |
| YouTube | 190 | 0x000c0057 | global key for launcherx |
| Prime Video | 4099 | 0x000c005f | swallowed by TclShortCutKeyManager |
| TCL Channel | 4020 | 0x000c0053 | TCL starts `com.tcl.waterfall.overseas` (disabled), fails |
| TV | 4001 | 0x000c005b | TCL GlobalKeyService tries the EPG (then sends GUIDE 172) |
| Input | 178 | 0x000c0049 | TCL QuickPanel, works |
| Media | 4159 | 0x000c029c | opens `com.tcl.ui_mediaCenter` |
| unknown app button | 4514 | 0x000c0050 | partnercustomizer, then a Play Store page |

## Not in git (local zip on the work PC)
`backup/` (package lists, getprop, all settings, display, old Home: taken before any change), `work/` (the
batch lists, combined `debloat.txt`, `restore-tv.ps1`, `build-and-install-launcher.ps1`, owner README, key
logs) and `shots/` (screenshots, some with account names). These are gitignored on purpose and travel as
`cleanyourtv-private.zip`. Unzip it into the repo root on the new computer. `tools/adbkey/` is left out: those
authorisations were revoked, and the new computer makes its own key.

## Setting up on the new computer
1. `python -m venv tools/venv`, then `tools/venv/bin/pip install -r tools/requirements.txt`
   (Windows: `tools\venv\Scripts\...`).
2. To rebuild the launcher: JDK 17, Android SDK platform 34 and build-tools 34.0.0, then
   `launcher/build-and-install.sh` with `HOME_KEY_SERVICE=1` (Windows: `-HomeKeyService`).
3. `TV_HOST=<tv ip> tools/tv.py --probe` after the owner turns USB debugging on and accepts the prompt.
4. When finished, close ADB again as `PROMPT.md` describes and confirm with `tools/adb-closed.py`.

## Undo
`tools/restore.sh my-list` with the combined list from `work/debloat.txt`, `-Stock`/stock launcher
`com.google.android.apps.tv.launcherx`. The recovery record from `disable.ps1` is in `~/.cleanyourtv/` on the
work PC only, so on another computer restore falls back to enabling the whole list. That is fine here: nothing
was disabled before. Or use `work/restore-tv.ps1`, which also switches off the key helper and resets DNS.

## 29 October 2026, second session (Windows PC)

Reviewed `977f6935` (theme picker, done on the Mac): complete. Unit tests, lint and the release build pass. The
shell-driven Python suites (`test_theme_one_argument`, `test_theme_push_ownership`, ...) need symlinks and a POSIX
shell, so they only run on macOS/Linux or in CI.

Then, on the owner's request:
- **Christmas skin** (`seasonal_skin: "christmas"`, built into the launcher like Halloween): a Christmas tree on the
  network pill whose lights are on while online and off when the connection drops (the pumpkin's `JackOLanternDrawable`
  with two new pictures), a gift for Inputs that hops and a snowflake for Settings that turns (`SpookyIconDrawable`
  kinds `GIFT` and `SNOWFLAKE`), snow over the first Home of the day (`PetalShowerView.setSnow`), "Merry Christmas"
  in the 12 languages that have the Halloween greeting, holly-red accent `#E8433A` (`Festival.CHRISTMAS`, `HOLLY`).
  Icons are Fluent Emoji 3D (MIT), 72 px WebP, noted in `launcher/ICONS-LICENSE-FLUENT-EMOJI.txt`.
- **`themes/christmas/`**: 8 Wikimedia Commons photos (PD, CC BY, CC BY-SA; `CREDITS.md`), a new one every 30 min,
  frosted dock, skin until 2027-01-02. Screenshot from this TV.
- **Themes chooser** is now the same glass menu as the Settings long-press menu (under the Settings pill), with a
  green check on the current theme, instead of an Android AlertDialog. `ThemePicker` holds only the logic now.
- **Reorder button** off in `themes/japan/config.json` (Reorder apps stays in the Settings long-press menu).
- `themes/japan/` got its `screenshot.jpg` and a row in `themes/README.md`; front-page theme counts are 14.
  `docs/switches/theme_picker.jpg` shows the new chooser.
- APK 586,445 B of the 589,824 B gate: about 3.3 KB left for any further launcher change.

**Signing key, read this before installing from the Mac.** Release builds are signed with each computer's
`~/.android/debug.keystore`. The Mac's build was on the TV, so this PC could not update it; with the owner's OK the
launcher was uninstalled and reinstalled from this PC (Google TV's launcher re-enabled as a safety net in between,
then disabled again by `build-and-install`). Its TV-side settings were reset; the themes were pushed back: japan as
the root theme, bundles `christmas`, `halloween`, `japan`; Default is selected. **The TV's launcher is now signed
with the Windows PC's key**, so a Mac build will fail with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`. Copy the PC's
`C:\Users\<user>\.android\debug.keystore` to the Mac's `~/.android/debug.keystore` (back up the Mac's first) so both
can install.

ADB note: this PC's key had been revoked; Google's `adb connect` brought up the authorisation (`TV_ADB_BINARY`
works too, but `theme.ps1` picture uploads fail through it with "shell command too long", so use `tv.py`'s own client
once the key is authorised). USB/network debugging is on at the end of this session.

Not verified: the tree going dark offline (needs the network to drop), and the gift/snowflake focus motion on a
real remote press (injected keys only).
