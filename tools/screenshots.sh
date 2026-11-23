#!/bin/sh
# Headless-Chrome screenshots for a visual check (desktop + phone, FR + EN).
#   tools/screenshots.sh [page] [outdir]      default: index.html  /tmp/site-shots
page="${1:-index.html}"; out="${2:-/tmp/site-shots}"; mkdir -p "$out"
root="$(cd "$(dirname "$0")/.." && pwd)"
chrome="$(command -v google-chrome || command -v chromium || command -v chromium-browser)"
[ -n "$chrome" ] || { echo "Chrome/Chromium not found"; exit 1; }
for spec in desktop:1366,900 laptop:1280,800 phone:390,844; do
  name="${spec%%:*}"; size="${spec#*:}"
  for lang in fr en; do
    "$chrome" --headless=new --disable-gpu --no-sandbox --hide-scrollbars --virtual-time-budget=4000 \
      --user-data-dir="$out/.profile" --window-size="$size" \
      --screenshot="$out/${page%.*}_${name}_${lang}.png" "file://$root/$page?lang=$lang" >/dev/null 2>&1
  done
done
echo "screenshots in $out"
