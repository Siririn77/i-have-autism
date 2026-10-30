#!/usr/bin/env bash
# Installs the packaged opencode plugin: one self-contained file, no dependencies.
#
#   bash opencode/install.sh                     # global: ~/.config/opencode/plugins/
#   bash opencode/install.sh --project /path     # project: /path/.opencode/plugins/
#   bash opencode/install.sh --always            # also turn the always-on hook on
#   bash opencode/install.sh --remove            # take back the plugin and the flag
#
# Why a built file instead of the repository tree: opencode loads single files
# from its plugin directory. The packaged plugin carries the ruleset inside it,
# so it works when copied alone — no skills/ or command/ neighbours required.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/dist/opencode-plugin/i-have-autism.js"

scope="global"
target=""
always=0
remove=0

while [ $# -gt 0 ]; do
  case "$1" in
    --global) scope="global"; shift ;;
    --project)
      [ $# -ge 2 ] || { echo "Error: --project needs a directory" >&2; exit 1; }
      scope="project"; target="$2"; shift 2 ;;
    --always) always=1; shift ;;
    --remove) remove=1; shift ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Error: unknown argument '$1'" >&2; exit 1 ;;
  esac
done

config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
flag="$config_home/opencode/.i-have-autism-always"

if [ "$scope" = "project" ]; then
  [ -n "$target" ] || { echo "Error: --project needs a directory" >&2; exit 1; }
  [ -d "$target" ] || { echo "Error: '$target' is not a directory" >&2; exit 1; }
  dest_dir="$target/.opencode/plugins"
else
  dest_dir="$config_home/opencode/plugins"
fi

if [ "$remove" -eq 1 ]; then
  removed=0
  for d in "$dest_dir" "$config_home/opencode/plugins"; do
    if [ -f "$d/i-have-autism.js" ]; then
      rm -f "$d/i-have-autism.js"
      echo "removed $d/i-have-autism.js"
      removed=1
    fi
  done
  if [ -f "$flag" ]; then
    rm -f "$flag"
    echo "removed $flag (always-on is off)"
    removed=1
  fi
  [ "$removed" -eq 1 ] || echo "Nothing to remove: plugin is not installed."
  exit 0
fi

[ -f "$SRC" ] || { echo "Error: $SRC is missing. Run tools/build_opencode_plugin.py first." >&2; exit 1; }

mkdir -p "$dest_dir"
cp "$SRC" "$dest_dir/i-have-autism.js"
echo "installed $dest_dir/i-have-autism.js"

if [ "$always" -eq 1 ]; then
  mkdir -p "$(dirname "$flag")"
  : > "$flag"
  echo "always-on enabled: $flag"
else
  echo "always-on is off; enable with --always or 'touch $flag'"
fi

echo "Restart opencode to load the plugin."
