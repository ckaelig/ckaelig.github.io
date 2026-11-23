#!/bin/sh
# Preview the site exactly as GitHub Pages serves it: http://localhost:8000/
cd "$(dirname "$0")/.." && exec python3 -m http.server "${1:-8000}" --bind 127.0.0.1
