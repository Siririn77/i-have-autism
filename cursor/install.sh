#!/usr/bin/env bash
# Install the Cursor rules from this repo into a project.
#
#   bash cursor/install.sh /path/to/your/project            # the four rules, always-off
#   bash cursor/install.sh /path/to/your/project --always   # plus the always-on ruleset
#   bash cursor/install.sh /path/to/your/project --remove   # remove what this script installs
#
# With no target, installs into the current directory.
#
# Why "--always" is a flag and not the default: Cursor has no runtime hook, so
# its only always-on channel is a rule with `alwaysApply: true`. A rule file
# that sits in the project applies to every Agent/Chat request — including the
# ones where the human wants a quick answer. The flag is the opt-in.
set -euo pipefail

target=""
always=0
remove=0

for arg in "$@"; do
  case "$arg" in
    --always) always=1 ;;
    --remove) remove=1 ;;
    -*) echo "error: unknown option $arg" >&2; exit 2 ;;
    *) target="$arg" ;;
  esac
done

target="${target:-.}"
src="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$src/rules" ]; then
  echo "error: rules/ not found next to this script ($src)" >&2
  exit 1
fi

dest="$target/.cursor/rules"

if [ "$remove" -eq 1 ]; then
  if [ ! -d "$dest" ]; then
    echo "nothing to remove: $dest does not exist"
    exit 0
  fi
  for f in "$src"/rules/*.mdc "$src"/always-on/*.mdc; do
    name="$(basename "$f")"
    if [ -f "$dest/$name" ]; then
      rm -f "$dest/$name"
      echo "removed $dest/$name"
    fi
  done
  exit 0
fi

mkdir -p "$dest"

for f in "$src"/rules/*.mdc; do
  cp "$f" "$dest/"
  echo "installed $(basename "$f") -> $dest/"
done

if [ "$always" -eq 1 ]; then
  for f in "$src"/always-on/*.mdc; do
    cp "$f" "$dest/"
    echo "installed $(basename "$f") -> $dest/ (always on)"
  done
else
  echo
  echo "Always-on ruleset not installed. Add it with: bash cursor/install.sh $target --always"
fi

echo
echo "Done. Open Cursor -> Customize -> Rules to confirm they loaded."

if [ "$always" -eq 1 ]; then
  echo "Off again: bash cursor/install.sh $target --remove, then re-run without --always."
fi

echo "Note: rules apply to Agent/Chat, not to Cursor Tab."
echo "Global instead of per project: paste the body of cursor/always-on/i-have-autism.mdc into"
echo "Cursor Settings -> Rules -> User Rules. Cursor stores user rules in settings, not in a file."
