#!/usr/bin/env python3
"""One-off migration (2026-11-23): bring the 13 detail pages onto the shared
design + language system. Kept for traceability; do not re-run.

Fixes, per page:
  * <body lang="en"> was hard-coded and the toggle never saved the choice:
    a French visitor always landed in English (thesis link!) and every
    "next page" click reset the language.            -> assets/js/site.js
  * each page had its own palette (orange #D35400 / #E67E22, Manrope)
    unlike the homepage (steel blue, Archivo).        -> assets/css/site.css
  * polyfill.io (hijacked domain, served malware since June 2024) removed;
    MathJax pinned to an exact version.
  * no way back except a footer link: add a top bar "← Kaëlig CASTOR".
  * "Enlarge" links pointed at 1999-era wrapper pages: link the image.
"""
import html as htmllib
import re
import sys

PAGES = ["phd.htm", "waveguid.htm", "antimatter.htm",
         "hydroacoustics.htm", "hydroacoustics_2.htm", "hydroacoustics_3.htm", "hydroacoustics_4.htm", "hydroacoustics_5.htm",
         "infrasound.htm", "infrasound_2.htm", "infrasound_3.htm", "infrasound_4.htm", "infrasound_5.htm"]

IMAGE_WRAPPERS = {"principle.htm": "principle.jpg", "gap.htm": "gap.jpg", "acmodel.htm": "acmodel.jpg", "mesald_ang.htm": "mesald_ang.JPG"}

HEAD_SHARED = """    <link rel="icon" type="image/x-icon" href="assets/img/favicon.ico">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800&amp;family=Public+Sans:wght@600;800&amp;display=swap" rel="stylesheet">
    <link rel="stylesheet" href="assets/css/site.css">
    <script src="assets/js/site.js"></script>
"""

PAGE_BAR = """    <nav class="page-bar" aria-label="Navigation">
        <a href="index.html"><span class="lang-fr">← Kaëlig CASTOR · CV</span><span class="lang-en">← Kaëlig CASTOR · Resume</span></a>
    </nav>
"""

LANG_BTN = """    <button type="button" class="lang-switch" data-action="toggle-lang" aria-label="Changer de langue / Switch language">
        <span class="lang-fr" lang="en">English</span>
        <span class="lang-en" lang="fr">Français</span>
    </button>
"""


def must(pattern, text, label, flags=re.S):
    if not re.search(pattern, text, flags):
        raise SystemExit(f"{label}: pattern not found")


def migrate(name, src):
    t = src
    # --- head --------------------------------------------------------------
    t = re.sub(r'\s*<link href="https://fonts\.googleapis\.com/css2\?family=Manrope[^>]*>', "", t)
    t = re.sub(r'\s*<script src="https://polyfill\.io[^>]*></script>', "", t)
    t = t.replace("https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
                  "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js")
    must(r"</title>\n", t, name + " title")
    t = re.sub(r"(</title>\n)", lambda m: m.group(1) + HEAD_SHARED, t, count=1)

    # --- page <style>: drop what site.css now owns --------------------------
    def clean_style(m):
        css = m.group(0)
        css = re.sub(r"\s*:root\s*\{[^}]*\}", "", css)
        css = re.sub(r"\s*/\*\s*LOGIQUE DE LANGUE\s*\*/", "", css)
        css = re.sub(r"\s*body\[lang=\"(?:en|fr)\"\]\s*\.lang-(?:en|fr)\s*\{[^}]*\}", "", css)
        css = re.sub(r"\s*\.lang-switch\s*\{[^}]*\}", "", css)
        css = re.sub(r"\s*\.lang-btn(?::hover)?\s*\{[^}]*\}", "", css)
        css = re.sub(r"font-family:\s*'Manrope',\s*sans-serif;", "font-family: var(--font-body);", css)
        css = re.sub(r"\s*transition:\s*opacity 0\.3s ease;", "", css)
        css = re.sub(r"#(?:E67E22|D35400)\b", "var(--accent)", css, flags=re.I)
        return css
    t = re.sub(r"<style>.*?</style>", clean_style, t, count=1, flags=re.S)

    # --- body --------------------------------------------------------------
    must(r'<body lang="en">', t, name + " body")
    t = t.replace('<body lang="en">', "<body>", 1)
    t, n = re.subn(r'\s*<div class="lang-switch">\s*<button class="lang-btn" onclick="toggleLang\(\)"[^>]*>[^<]*</button>\s*</div>\n',
                   "\n" + PAGE_BAR + "\n" + LANG_BTN, t, count=1)
    if n != 1:
        raise SystemExit(name + ": language switch block not found")
    t, n = re.subn(r"\s*<script>\s*function toggleLang\(\).*?</script>", "", t, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(name + ": toggleLang script not found")

    # --- links -------------------------------------------------------------
    t = t.replace('href="index.htm#', 'href="index.html#').replace('href="index.htm"', 'href="index.html"')
    for wrapper, img in IMAGE_WRAPPERS.items():
        t = t.replace(f'href="{wrapper}"', f'href="{img}"')

    # --- bilingual <title> ---------------------------------------------------
    title = re.search(r"<title>(.*?)</title>", t, re.S).group(1).strip()
    h1_fr = re.search(r'<h1 class="lang-fr">(.*?)</h1>', t, re.S)
    if h1_fr:
        fr = "Kaëlig CASTOR | " + " ".join(re.sub(r"<[^>]+>", "", h1_fr.group(1)).split())
        t = t.replace('<html lang="en">',
                      f'<html lang="en" data-title-en="{htmllib.escape(title, quote=True)}" data-title-fr="{htmllib.escape(fr, quote=True)}">', 1)
    return t


root = sys.argv[1] if len(sys.argv) > 1 else "."
for p in PAGES:
    path = f"{root}/{p}"
    src = open(path, encoding="utf-8").read()
    if "assets/css/site.css" in src:
        print(f"skip {p} (already migrated)")
        continue
    out = migrate(p, src)
    open(path, "w", encoding="utf-8").write(out)
    print(f"migrated {p}")
