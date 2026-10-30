#!/usr/bin/env bash
# Push a theme (a folder with config.json, and optionally a wallpaper.jpg or a wallpapers/ collection) to the
# launcher on the TV and restart Home so it picks it up. The launcher reads the files from its external files
# directory and overlays config.json on its built-in config.xml; see themes/README.md for the keys.
#
# Usage: TV_HOST=192.168.1.50 tools/theme.sh themes/aurora
#        TV_HOST=192.168.1.50 tools/theme.sh --as japan themes/japan   # store a bundle, not active
#        TV_HOST=192.168.1.50 tools/theme.sh --list                    # the bundles on the TV
#        TV_HOST=192.168.1.50 tools/theme.sh --remove japan            # drop one bundle
#        TV_HOST=192.168.1.50 tools/theme.sh --reset                   # remove the root overlay, back to config.xml
#
# A folder replaces the theme Home shows. --as stores the same files one folder deeper, under files/themes/<name>/,
# where Home's long-press Settings menu lists it (Themes) beside the root theme, called Default. A bundle stays
# until --remove, and --reset leaves the bundles alone. Exit status: 0 the theme is on the TV, the bundle was
# stored or removed, or the list/reset ran; 1 the theme could not be pushed; 2 the command line is not one of the
# shapes above, so nothing was sent.
set -euo pipefail
# What the caller asked for, read before TV_HOST is required: a line this script cannot read must not reach a TV.
# A second word used to be dropped, and `--reset themes/aurora` removed the theme the reader named instead of
# pushing it, so every shape is listed and anything else is refused.
USAGE="usage: theme.sh <theme folder> | --as <name> <theme folder> | --list | --remove <name> | --reset"
MODE=push
THEME_ARG=""
BUNDLE=""
case "${1:-}" in
  --reset)
    [ "$#" -eq 1 ] || { echo "theme.sh --reset takes no other argument: $* . Nothing was sent to the TV." >&2; exit 2; }
    MODE=reset ;;
  --list)
    [ "$#" -eq 1 ] || { echo "theme.sh --list takes no other argument: $* . Nothing was sent to the TV." >&2; exit 2; }
    MODE=list ;;
  --remove)
    [ "$#" -eq 2 ] || { echo "$USAGE" >&2; echo "theme.sh --remove takes one bundle name: $* . Nothing was sent to the TV." >&2; exit 2; }
    MODE=remove
    BUNDLE="$2" ;;
  --as)
    [ "$#" -eq 3 ] || { echo "$USAGE" >&2; echo "theme.sh --as takes a name and one theme folder: $* . Nothing was sent to the TV." >&2; exit 2; }
    MODE=store
    BUNDLE="$2"
    THEME_ARG="$3" ;;
  "")
    echo "$USAGE" >&2
    exit 2 ;;
  *)
    [ "$#" -eq 1 ] || { echo "theme.sh takes one theme folder, or one of --as, --list, --remove, --reset: $* would" \
      "not have been used. Nothing was sent to the TV." >&2; exit 2; }
    THEME_ARG="$1" ;;
esac
# A bundle name becomes a folder under files/themes/ and a path inside the provider's URI, so it keeps to the
# characters a theme folder can use here: no dots (no "..", no hidden names) and no spaces.
if [ "$MODE" = store ] || [ "$MODE" = remove ]; then
  [[ "$BUNDLE" =~ ^[A-Za-z0-9_-]{1,40}$ ]] || { echo "unsupported bundle name: $BUNDLE (letters, digits, _ and -," \
    "up to 40). Nothing was sent to the TV." >&2; exit 2; }
fi
# Resolve the theme folder against the caller's directory before moving into tools/.
# Git Bash's pwd says /c/Users/..., which the Windows Python cannot open; pwd -W gives C:/Users/... (as in disable.sh).
# An absolute argument needs the same: /c/Users/... passed through as typed reached the JSON check below, which
# could not open it and called the file "not valid JSON". A folder that does not exist keeps the path as typed,
# so the "no config.json" message names what the caller gave.
if [ "$MODE" = push ] || [ "$MODE" = store ]; then
  case "$THEME_ARG" in
    /*|[A-Za-z]:[\\/]*) THEME_ARG="$(cd "$THEME_ARG" 2>/dev/null && { pwd -W 2>/dev/null || pwd; } || printf '%s' "$THEME_ARG")" ;;
    *) THEME_ARG="$(pwd -W 2>/dev/null || pwd)/$THEME_ARG" ;;
  esac
fi
cd "$(dirname "$0")"
: "${TV_HOST:?set TV_HOST to the TV IP address, e.g. TV_HOST=192.168.1.50 $0 themes/aurora}"
PY=venv/bin/python
[ -x "$PY" ] || PY=venv/Scripts/python.exe
[ -x "$PY" ] || { echo "run: python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt" >&2; exit 1; }
export MSYS_NO_PATHCONV=1
PKG=com.gathin.tvhome
DIR=/sdcard/Android/data/$PKG/files
# A unique marker lets the launcher clear on-TV layout/motion choices after every theme push,
# including a push of identical config.json bytes and --reset.
REVISION="$("$PY" -I -c 'import uuid; print(uuid.uuid4().hex)')"
tv() { "$PY" -I tv.py "$@"; }
# One shared recovery path verifies the helpers after Home restarts.


# Some firmware (TCL G07, Android 11) locks the shell out of Android/data. Files are staged in
# /data/local/tmp and copied in, or written through the launcher's ThemeProvider when that is refused.
# The provider has to be tried first: on Android 14 the shell can write into Android/data, so cp "succeeds",
# but the file it creates belongs to the shell (uid 2000) and the launcher then gets EACCES opening it, which
# silently ignores the theme whenever the file did not exist yet - a fresh install, or after a reinstall.
# A provider write creates the file as the launcher, and it cannot truncate a file the shell owns either, so
# remove our copy first. cp stays as the fallback for firmware without the provider.
URI=content://$PKG.theme
TMP=/data/local/tmp/cyt-theme
# A file's staging path; wallpapers/a.jpg is staged as $TMP-wallpapers-a.jpg.
stage() { echo "$TMP-${1//\//-}"; }
# Android 8 and 9 have no `content write`: they print the usage and "[ERROR] Unsupported operation: write" but
# exit 0, so the exit status alone would skip cp and leave the file deleted. Treat that message as a failure.
put() { echo "rm -f $DIR/$1 2>/dev/null; { o=\$(content write --uri $URI/$1 < $(stage "$1") 2>&1) && case \"\$o\" in *'Unsupported operation'*) false ;; esac; } || cp $(stage "$1") $DIR/$1 2>/dev/null; rm -f $(stage "$1")"; }
del() { echo "rm -f $DIR/$1 2>/dev/null; content delete --uri $URI/$1 2>/dev/null"; }

# The collection a theme can push. A push empties it before writing the theme's own pictures, and --reset has to
# empty it too: the launcher's wallpaper picker (LauncherSettingsActivity.showWallpaperPicker) lists that folder
# itself, and an on-TV pick of one of its pictures is read back from it (WallpaperRotation.chosen), so a reset
# that left the pictures behind still shows the theme it just removed. $1 is the prefix under files/, "" for the
# root theme and "themes/<name>/" for a bundle.
clear_wallpapers() { echo "mkdir -p $DIR/$1wallpapers 2>/dev/null; rm -f $DIR/$1wallpapers/*.[jJ][pP][gG] $DIR/$1wallpapers/*.[jJ][pP][eE][gG] $DIR/$1wallpapers/*.[pP][nN][gG] $DIR/$1wallpapers/*.[wW][eE][bB][pP] 2>/dev/null; content delete --uri $URI/$1wallpapers 2>/dev/null"; }

if [ "$MODE" = list ]; then
  # Only a folder with a config.json is a bundle the picker can show, which is also what ThemeDir.bundles reads.
  LIST=$(tv "for d in $DIR/themes/*/; do [ -f \"\$d/config.json\" ] && basename \"\$d\"; done 2>/dev/null" || true)
  if [ -z "$LIST" ]; then
    echo "no theme bundles on the TV (store one with: theme.sh --as <name> <theme folder>)"
  else
    echo "theme bundles on the TV:"
    printf '%s\n' "$LIST" | sed 's/^/  /'
  fi
  exit 0
fi
if [ "$MODE" = remove ]; then
  tv "rm -rf $DIR/themes/$BUNDLE 2>/dev/null; content delete --uri $URI/themes/$BUNDLE 2>/dev/null" >/dev/null
  "$PY" -I theme_restart.py
  echo removed
  echo "Bundle $BUNDLE is off the TV. If it was the theme Home showed, Home falls back to the root theme (Default)."
  exit 0
fi
if [ "$MODE" = reset ]; then
  tv "mkdir -p $DIR 2>/dev/null; $(del config.json); $(del wallpaper.jpg); $(del wallpapers/captions.txt); $(clear_wallpapers ""); printf '%s' '$REVISION' > $TMP-theme_revision; $(put theme_revision)" >/dev/null
  "$PY" -I theme_restart.py
  echo reset
  echo "The root theme is off the TV. Bundles stored with --as are still there, and a bundle Home is showing"
  echo "stays until you pick Default in the Themes menu."
  exit 0
fi
THEME="${THEME_ARG:?usage: theme.sh <theme folder> | --as <name> <theme folder>}"
[ -f "$THEME/config.json" ] || { echo "no config.json in $THEME" >&2; exit 1; }
# What the launcher makes of the file: Config.read() answers "no overlay" for anything that is not a JSON
# object, so an array, a number or a string is a theme the TV drops - and it replaces the theme the set had,
# which puts the built-in config.xml back. Reading the shape here, before anything is pushed, keeps a run
# that ends "is on the TV" from meaning the opposite.
theme_json_kind() {
  "$PY" -I -c '
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8-sig") as handle:
        theme = json.load(handle)
except (OSError, ValueError):
    print("invalid")
else:
    print("object" if isinstance(theme, dict) else "not an object")
' "$1" 2>/dev/null
}
case "$(theme_json_kind "$THEME/config.json")" in
  object) ;;
  "not an object") echo "$THEME/config.json is not a JSON object of theme keys, so the launcher would ignore" \
    "it and the TV would go back to its built-in config (themes/README.md). Nothing was sent to the TV." >&2
    exit 1 ;;
  *) echo "$THEME/config.json is not valid JSON" >&2; exit 1 ;;
esac
# Every collection name is checked before anything changes on the TV: a name refused halfway through the push
# left the new config.json and part of the collection behind. b64push.py refuses a path with '..' in it, so
# such a name (sunset..jpg) is refused here too. The names that pass have no spaces, so NAMES splits on them.
NAMES=""
if [ -d "$THEME/wallpapers" ]; then
  for IMAGE in "$THEME"/wallpapers/*; do
    [ -f "$IMAGE" ] || continue
    case "$IMAGE" in
      *.[jJ][pP][gG]|*.[jJ][pP][eE][gG]|*.[pP][nN][gG]|*.[wW][eE][bB][pP])
        NAME=$(basename "$IMAGE")
        [[ "$NAME" =~ ^[A-Za-z0-9_.-]+$ && "$NAME" != *..* ]] || { echo "unsupported wallpaper filename: $NAME" >&2; exit 1; }
        NAMES="$NAMES $NAME" ;;
    esac
  done
fi

# A bundle is the same files one folder deeper. The root push keeps its order; a store writes the pictures
# first and config.json last, so a half-finished --as leaves a folder ThemeDir.bundles does not list.
PREFIX=""
[ "$MODE" = store ] && PREFIX="themes/$BUNDLE/"
push_config() {
  tv --push "$THEME/config.json" "$(stage "${PREFIX}config.json")" >/dev/null
  tv "$(put "${PREFIX}config.json")"
}
push_pictures() {
  if [ -f "$THEME/wallpaper.jpg" ]; then
    "$PY" -I b64push.py "$THEME/wallpaper.jpg" "$(stage "${PREFIX}wallpaper.jpg")"
    tv "$(put "${PREFIX}wallpaper.jpg")" >/dev/null
  else
    tv "$(del "${PREFIX}wallpaper.jpg")" >/dev/null
  fi
  tv "$(clear_wallpapers "$PREFIX")" >/dev/null
  for NAME in $NAMES; do
    "$PY" -I b64push.py "$THEME/wallpapers/$NAME" "$(stage "${PREFIX}wallpapers/$NAME")"
    tv "$(put "${PREFIX}wallpapers/$NAME")" >/dev/null
  done
  # The collection's names (wallpaper_captions); a theme without them leaves no stale names behind.
  if [ -f "$THEME/wallpapers/captions.txt" ]; then
    "$PY" -I b64push.py "$THEME/wallpapers/captions.txt" "$(stage "${PREFIX}wallpapers/captions.txt")"
    tv "$(put "${PREFIX}wallpapers/captions.txt")" >/dev/null
  else
    tv "$(del "${PREFIX}wallpapers/captions.txt")" >/dev/null
  fi
}
push_revision() {
  tv "printf '%s' '$REVISION' > $(stage "${PREFIX}theme_revision"); $(put "${PREFIX}theme_revision")" >/dev/null
}

tv "mkdir -p $DIR/${PREFIX}" >/dev/null 2>&1 || true
if [ "$MODE" = store ]; then
  push_pictures
  push_config
  push_revision
  echo stored
  echo "Theme $(basename "$THEME") is on the TV as bundle $BUNDLE. Pick it on Home: hold Settings, then Themes."
  exit 0
fi
push_config
push_pictures
push_revision
"$PY" -I theme_restart.py
echo applied
echo "Theme $(basename "$THEME") is on the TV. Undo with: tools/theme.sh --reset"
