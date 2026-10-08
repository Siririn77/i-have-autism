#!/usr/bin/env bash
# Substitutes the GitHub login into every REPLACE_USERNAME placeholder.
# In this repository the login has already been filled in, so this script is
# only needed if you fork it and want the links to point at your own account.
# Usage: ./setup.sh <your-github-login>
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <your-github-login>"
  echo "Example: $0 octocat"
  exit 1
fi

USER="$1"
if ! printf '%s' "$USER" | grep -Eq '^[A-Za-z0-9]([A-Za-z0-9-]{0,37}[A-Za-z0-9])?$'; then
  echo "Error: '$USER' is not a valid GitHub login (letters, digits, hyphens; no leading or trailing hyphen)."
  exit 1
fi

files=$(grep -rl 'REPLACE_USERNAME' . --exclude-dir=.git 2>/dev/null || true)
if [ -z "$files" ]; then
  echo "No REPLACE_USERNAME placeholders found — the links already point somewhere."
else
  for f in $files; do
    sed -i "s/REPLACE_USERNAME/${USER}/g" "$f"
    echo "  updated: $f"
  done
fi

echo ""
echo "Done. Check:"
grep -rn "github.com/${USER}/i-have-autism" . --exclude-dir=.git || echo "  (nothing found — verify by hand)"
