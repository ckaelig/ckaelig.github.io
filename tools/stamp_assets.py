#!/usr/bin/env python3
"""Cache-busting: append ?v=<content hash> to every link to assets/css/site.css
and assets/js/site.js, so browsers fetch the new files right after a deploy
(otherwise a stale cached site.js can break the language button).

    python3 tools/stamp_assets.py          # rewrite pages
    python3 tools/stamp_assets.py --check  # exit 1 if a page is out of date

check_site.py runs the --check logic; run this script after editing site.css/site.js.
"""
import glob
import hashlib
import os
import re
import sys

ROOT = os.path.abspath(os.environ.get("SITE_ROOT") or os.path.join(os.path.dirname(__file__), ".."))
ASSETS = ["assets/css/site.css", "assets/js/site.js"]


def digest(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:10]


def pages():
    out = []
    for pat in ("*.htm", "*.html", "*/*.html", "*/*.htm"):
        out += glob.glob(os.path.join(ROOT, pat))
    return sorted(p for p in out if "/tools/" not in p and "/dist/" not in p)


def stamp(text):
    for rel in ASSETS:
        if not os.path.exists(os.path.join(ROOT, rel)):
            continue
        v = digest(rel)
        text = re.sub(r'((?:href|src)="/?' + re.escape(rel) + r')(?:\?v=[0-9a-f]+)?"', r'\1?v=' + v + '"', text)
    return text


def stale_pages():
    bad = []
    for p in pages():
        t = open(p, encoding="utf-8").read()
        if stamp(t) != t:
            bad.append(os.path.relpath(p, ROOT))
    return bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        bad = stale_pages()
        for b in bad:
            print(f"stale asset version in {b} (run python3 tools/stamp_assets.py)")
        sys.exit(1 if bad else 0)
    n = 0
    for p in pages():
        t = open(p, encoding="utf-8").read()
        s = stamp(t)
        if s != t:
            open(p, "w", encoding="utf-8").write(s)
            n += 1
    print(f"{n} page(s) stamped: " + ", ".join(f"{a}?v={digest(a)}" for a in ASSETS))
