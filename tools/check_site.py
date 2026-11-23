#!/usr/bin/env python3
"""Site validator: run before every commit / deploy (CI runs it too).

    python3 tools/check_site.py              # local checks (fast, offline)
    python3 tools/check_site.py --external   # + check external URLs (slow)

Exit code 1 if any ERROR. WARNings are printed but do not fail.

Checks
  links      every internal href/src resolves to a real file, with exact case
             (GitHub Pages is case-sensitive: "x.PDF" != "x.pdf")
  i18n       each page has as many .lang-fr as .lang-en elements; no page
             hard-codes <body lang>; pages load the shared site.js/site.css
  security   no polyfill.io / unpinned CDN scripts; target=_blank has rel=noopener
  privacy    no phone number, home address, birth date, or private folder
             names anywhere in published text files
  ux         internal pages do not open in a new tab (target=_blank)
  size       files > 50 MB warn, > 100 MB fail (GitHub hard limit)
  hygiene    UTF-8 everywhere, <meta charset>, unreferenced files (warning)
"""
import argparse
import html.parser
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.environ.get("SITE_ROOT") or os.path.join(os.path.dirname(__file__), ".."))

# Folders/files that are not part of the published site
IGNORE_DIRS = {".git", ".github", ".githooks", "tools", "dist", "node_modules", "__pycache__"}
IGNORE_FILES = {"README.md", "CLAUDE.md", ".gitignore", ".nojekyll", "CNAME", "LICENSE"}

# Redirect stubs: tiny pages that only forward to another URL
STUBS = {"index.htm", "these.htm", "en/index.html", "fr/index.html"}

# --- privacy rules: anything matching must never be published -------------
PRIVACY_PATTERNS = [
    (r"(?:\+33|0033)[\s.()-]*6[\s.-]*63[\s.-]*22", "mobile phone number"),
    (r"\b0?6[\s.-]?63[\s.-]?22[\s.-]?41[\s.-]?95\b", "mobile phone number"),
    (r"\b0?1[\s.-]?64[\s.-]?09[\s.-]?46[\s.-]?36\b", "family phone/fax number"),
    (r"saint[\s-]maur", "home street address"),
    (r"27(?:th|\s+novembre|\s+november)\s+1974|november\s+27(?:th)?,?\s+1974|27/11/1974", "date of birth"),
]
PRIVATE_PATH_WORDS = ["achat_immo", "succession", "vaccin", "impot", "salaire", "bank", "macif",
                      "natixis", "mutuelle", "credentials", "diplom", "lettre", "letters", "passport", "passeport", "carte_identite", "rib", "mamy", "yvonne"]

# Classes used only as semantic hooks (never styled on purpose)
UNSTYLED_OK = {"experience-section", "location", "patent-item", "publication-item", "teaching-section", "nav-footer"}

ALLOWED_SCRIPT_HOSTS = {"cdn.jsdelivr.net", "www.statcounter.com"}
BANNED_HOSTS = {"polyfill.io", "cdn.polyfill.io"}

TEXT_EXT = {".html", ".htm", ".css", ".js", ".json", ".txt", ".md", ".xml", ".svg"}


class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []          # (attr, url, line, tag, attrs)
        self.n_fr = self.n_en = 0
        self.body_lang = None
        self.scripts = []
        self.stylesheets = []
        self.has_charset = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        self.n_fr += "lang-fr" in cls
        self.n_en += "lang-en" in cls
        if tag == "body" and "lang" in a:
            self.body_lang = a["lang"]
        if tag == "meta" and ("charset" in a or (a.get("http-equiv", "").lower() == "content-type" and "utf-8" in (a.get("content") or "").lower())):
            self.has_charset = True
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])
        if tag == "link" and "stylesheet" in (a.get("rel") or ""):
            self.stylesheets.append(a.get("href", ""))
        for attr in ("href", "src", "data-href"):
            if a.get(attr):
                self.refs.append((attr, a[attr], self.getpos()[0], tag, a))


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, where, msg):
        self.errors.append(f"ERROR  {where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"WARN   {where}: {msg}")


def published_files():
    out = []
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(x for x in dirs if x not in IGNORE_DIRS)
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(d, f), ROOT).replace(os.sep, "/")
            if rel in IGNORE_FILES:
                continue
            out.append(rel)
    return out


def exists_exact_case(rel):
    """True only if every path component matches on-disk case exactly."""
    cur = ROOT
    for part in rel.split("/"):
        if part in ("", "."):
            continue
        try:
            entries = os.listdir(cur)
        except (NotADirectoryError, FileNotFoundError):
            return False
        if part not in entries:
            return False
        cur = os.path.join(cur, part)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--external", action="store_true", help="also check external http(s) links")
    args = ap.parse_args()

    rep = Report()
    files = published_files()
    pages = [f for f in files if f.endswith((".html", ".htm"))]
    referenced = set()
    external = {}

    for rel in files:
        path = os.path.join(ROOT, rel)
        size = os.path.getsize(path)
        if size > 100 * 1024 * 1024:
            rep.err(rel, f"{size / 1e6:.0f} MB exceeds GitHub's 100 MB file limit")
        elif size > 50 * 1024 * 1024:
            rep.warn(rel, f"{size / 1e6:.0f} MB (GitHub warns above 50 MB; consider a release asset or a lighter export)")
        low = rel.lower()
        for w in PRIVATE_PATH_WORDS:
            if re.search(rf"(?:^|[/_\-.]){w}", low):
                rep.err(rel, f"path looks private ('{w}')")
        if os.path.splitext(rel)[1].lower() in TEXT_EXT:
            raw = open(path, "rb").read()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                rep.err(rel, "not valid UTF-8")
                text = raw.decode("latin-1")
            for pat, what in PRIVACY_PATTERNS:
                m = re.search(pat, text, re.I)
                if m:
                    line = text.count("\n", 0, m.start()) + 1
                    rep.err(f"{rel}:{line}", f"contains a {what} — never publish this")

    css_path = os.path.join(ROOT, "assets", "css", "site.css")
    shared_css = open(css_path, encoding="utf-8").read() if os.path.exists(css_path) else ""
    defined = set(re.findall(r"\.([A-Za-z][\w-]*)", re.sub(r"/\*.*?\*/", "", shared_css, flags=re.S)))

    for rel in pages:
        text = open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()
        # classes with no CSS anywhere = a design block silently lost (skills cards, Nov. 2026)
        live = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        page_defined = defined | set(re.findall(r"\.([A-Za-z][\w-]*)", " ".join(re.findall(r"<style>(.*?)</style>", live, re.S))))
        used = {c for cl in re.findall(r'class="([^"]*)"', live) for c in cl.split()}
        for c in sorted(used - page_defined - UNSTYLED_OK):
            if not c.startswith("lang-"):
                rep.warn(rel, f"class '{c}' is used but defined in no stylesheet")
        p = Page()
        p.feed(text)
        base_dir = os.path.dirname(rel)

        if not p.has_charset:
            rep.err(rel, "missing <meta charset=\"UTF-8\">")
        if rel not in STUBS:
            if p.body_lang:
                rep.err(rel, f'<body lang="{p.body_lang}"> is hard-coded: site.js owns the language (on <html>)')
            if not {"assets/js/site.js", "/assets/js/site.js"} & {s.split("?")[0] for s in p.scripts}:
                rep.err(rel, "does not load assets/js/site.js (language switch would not work)")
            if not {"assets/css/site.css", "/assets/css/site.css"} & {s.split("?")[0] for s in p.stylesheets}:
                rep.err(rel, "does not load assets/css/site.css")
            if p.n_fr != p.n_en:
                rep.warn(rel, f"{p.n_fr} .lang-fr vs {p.n_en} .lang-en elements — a translation may be missing")
            if re.search(r'onclick="toggleLang', text):
                rep.err(rel, "legacy onclick=toggleLang handler; use data-action=\"toggle-lang\"")

        for attr, url, line, tag, a in p.refs:
            where = f"{rel}:{line}"
            if url.startswith(("mailto:", "tel:", "javascript:", "data:", "#")):
                continue
            pu = urllib.parse.urlparse(url)
            if pu.scheme in ("http", "https") or url.startswith("//"):
                host = pu.netloc.lower()
                if host in BANNED_HOSTS:
                    rep.err(where, f"banned host {host} (compromised CDN)")
                if tag == "script":
                    if host not in ALLOWED_SCRIPT_HOSTS:
                        rep.err(where, f"script from non-allowlisted host {host}")
                    if host == "cdn.jsdelivr.net" and not re.search(r"@\d+\.\d+\.\d+/", url):
                        rep.err(where, "CDN script must pin an exact version (pkg@x.y.z)")
                if tag == "a" and a.get("target") == "_blank" and "noopener" not in (a.get("rel") or ""):
                    rep.warn(where, f"target=_blank without rel=noopener: {url}")
                if attr != "data-href" and "preconnect" not in (a.get("rel") or "") and host != "ckaelig.github.io":
                    external.setdefault(url, where)
                continue
            if pu.scheme:
                continue
            target = urllib.parse.unquote(pu.path)
            if not target:
                continue
            resolved = os.path.normpath(target.lstrip("/") if target.startswith("/") else os.path.join(base_dir, target)).replace(os.sep, "/")
            if resolved.startswith(".."):
                rep.err(where, f"link escapes the site root: {url}")
                continue
            referenced.add(resolved)
            if not exists_exact_case(resolved):
                hint = ""
                if os.path.exists(os.path.join(ROOT, resolved)) or any(f.lower() == resolved.lower() for f in files):
                    hint = " (exists with different letter case — breaks on GitHub Pages)"
                rep.err(where, f"broken link {url}{hint}")
            if tag == "a" and resolved.endswith((".htm", ".html")) and a.get("target") == "_blank":
                rep.warn(where, f"internal page {url} opens in a new tab")

    # files referenced from the shared stylesheet (fonts, background images)
    for u in re.findall(r"url\(['\"]?([^'\")]+)", shared_css):
        if not re.match(r"[a-z]+:", u):
            referenced.add(os.path.normpath(os.path.join("assets/css", u)).replace(os.sep, "/"))

    # Files nobody links to (the site's own plumbing excluded)
    plumbing = {"assets/img/favicon.ico", "index.html", "en/index.html", "fr/index.html", "index.htm", "these.htm", "robots.txt", "sitemap.xml", "404.html"}
    for rel in files:
        if rel not in referenced and rel not in plumbing:
            rep.warn(rel, "not linked from any page (orphan)")

    if args.external:
        print(f"Checking {len(external)} external links…", file=sys.stderr)
        for url, where in sorted(external.items()):
            u = "https:" + url if url.startswith("//") else url
            code = None
            for method in ("HEAD", "GET"):  # some servers reject HEAD (404/405) but serve GET
                try:
                    req = urllib.request.Request(u, method=method, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/130 Safari/537.36"})
                    code = urllib.request.urlopen(req, timeout=15).status
                except urllib.error.HTTPError as e:
                    code = e.code
                except Exception as e:  # noqa: BLE001
                    code = type(e).__name__
                if code in (200, 301, 302, 303, 307, 308):
                    break
            if code not in (200, 301, 302, 303, 307, 308, 403, 405, 429, 999):
                rep.warn(where, f"external link → {code}: {url}")

    # cache-busting stamps (?v=hash) must match the current site.css / site.js
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import stamp_assets
    for rel in stamp_assets.stale_pages():
        rep.err(rel, "stale ?v= stamp on site.css/site.js (run python3 tools/stamp_assets.py)")

    for line in rep.warnings:
        print(line)
    for line in rep.errors:
        print(line)
    print(f"\n{len(pages)} pages, {len(files)} files — {len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
