#!/bin/sh
# Dated copy of the whole project (including .git) next to it:
#   ../<YYYYMMDD>_ckaelig.github.io/
set -e
here="$(cd "$(dirname "$0")/.." && pwd)"
dest="$(dirname "$here")/$(date +%Y%m%d)_$(basename "$here")"
[ -e "$dest" ] && { echo "exists: $dest"; exit 1; }
rsync -rt "$here/" "$dest/"
echo "backup: $dest ($(find "$dest" -type f | wc -l) files)"
