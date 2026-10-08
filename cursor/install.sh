#!/usr/bin/env bash
# Install the Cursor rules from this repo into a project.
#
#   bash cursor/install.sh /path/to/your/project
#
# With no argument, installs into the current directory.
set -euo pipefail

target="${1:-.}"
src="$(cd "$(dirname "$0")" && pwd)/rules"

if [ ! -d "$src" ]; then
  echo "error: rules/ not found next to this script ($src)" >&2
  exit 1
fi

dest="$target/.cursor/rules"
mkdir -p "$dest"

for f in "$src"/*.mdc; do
  cp "$f" "$dest/"
  echo "installed $(basename "$f") -> $dest/"
done

echo
echo "Done. Open Cursor -> Customize -> Rules to confirm they loaded."
echo "Note: rules apply to Agent/Chat, not to Cursor Tab."
