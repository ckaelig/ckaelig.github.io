#!/usr/bin/env python3
"""One-off migration (2026-11-23): live index.htm -> clean index.html.

Kept for traceability: it documents every structural change made to the
homepage. Do not re-run it on the new index.html (it expects the old file).

Usage:  python3 tools/migrations/m2026_11_homepage.py index.htm index.html
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
html = open(src, encoding="utf-8").read()
report = []


def sub(pattern, repl, text, count=0, flags=re.S, expect=None, label=""):
    new, n = re.subn(pattern, repl, text, count=count, flags=flags)
    if expect is not None and n != expect:
        raise SystemExit(f"[{label or pattern[:50]}] expected {expect} replacement(s), got {n}")
    report.append(f"{n:4d}  {label or pattern[:70]}")
    return new


def replace(old, new, text, expect=1, label=""):
    n = text.count(old)
    if expect is not None and n != expect:
        raise SystemExit(f"[{label or old[:50]}] expected {expect} occurrence(s), got {n}")
    report.append(f"{n:4d}  {label or old[:70]}")
    return text.replace(old, new)


# --------------------------------------------------------------------------
# 1. New <head>: shared CSS/JS, fonts actually used, SEO/social metadata.
# --------------------------------------------------------------------------
HEAD = """<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kaëlig CASTOR | Technical Project Manager &amp; Senior Scientist</title>
    <meta name="description" content="Kaëlig CASTOR — Technical Project Manager &amp; Senior Research Scientist. Acoustics, NVH, signal processing, data science and machine learning. 20+ years of industrial R&amp;D (CGG, CEA, Scripps/UCSD).">
    <meta name="author" content="Kaëlig CASTOR">
    <link rel="canonical" href="https://ckaelig.github.io/">
    <link rel="alternate" hreflang="fr" href="https://ckaelig.github.io/?lang=fr">
    <link rel="alternate" hreflang="en" href="https://ckaelig.github.io/?lang=en">
    <link rel="alternate" hreflang="x-default" href="https://ckaelig.github.io/">

    <meta property="og:type" content="profile">
    <meta property="og:title" content="Kaëlig CASTOR | Technical Project Manager &amp; Senior Scientist">
    <meta property="og:description" content="Acoustics, NVH, signal processing &amp; data science — 20+ years of industrial innovation and research.">
    <meta property="og:url" content="https://ckaelig.github.io/">
    <meta property="og:image" content="https://ckaelig.github.io/photo-profil.jpg">
    <meta name="twitter:card" content="summary">

    <link rel="icon" type="image/x-icon" href="assets/img/favicon.ico">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800&amp;family=Public+Sans:wght@600;800&amp;display=swap" rel="stylesheet">
    <link rel="stylesheet" href="assets/css/site.css">
    <script src="assets/js/site.js"></script>

    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Kaëlig Castor",
        "jobTitle": "Technical Project Manager & Senior Research Scientist",
        "url": "https://ckaelig.github.io/",
        "image": "https://ckaelig.github.io/photo-profil.jpg",
        "alumniOf": ["Le Mans Université", "Télécom Paris", "Université Paris-Saclay"],
        "knowsAbout": ["Acoustics", "NVH", "Signal processing", "Machine learning", "Seismic acquisition", "Underwater acoustics"],
        "sameAs": [
            "https://www.linkedin.com/in/KaeligCastor",
            "https://www.researchgate.net/profile/Kaelig-Castor",
            "https://scholar.google.com/citations?user=VQMKOqgAAAAJ",
            "https://github.com/ckaelig"
        ]
    }
    </script>
</head>"""
html = sub(r"<head>.*?</head>", lambda m: HEAD, html, expect=1, label="replace <head> (inline CSS -> assets/css/site.css)")
html = replace('<html lang="fr">', '<html lang="fr">', html, label="<html lang> (now synced by site.js)")

# --------------------------------------------------------------------------
# 2. Dead code: commented-out sections, old scripts at the end.
# --------------------------------------------------------------------------
html = sub(r"<!--.*?-->", "", html, label="remove HTML comments / dead commented-out sections")
html = sub(r"\s*<script>\s*// Gestion du menu mobile.*?</script>", "", html, expect=1, label="remove inline menu/lang script")
html = sub(r"\s*<script type=\"text/javascript\">\s*// Configuration Statcounter.*?</script>", "", html, expect=1, label="remove inline statcounter script")

COOKIE = """<div id="cookie-banner" class="cookie-banner" role="dialog" aria-live="polite" aria-label="Cookies" data-sc-project="11378260" data-sc-security="21f54ad3" hidden>
        <p class="lang-fr">Ce site utilise des cookies (Statcounter) pour mesurer l'audience. Aucun autre suivi.</p>
        <p class="lang-en">This website uses cookies (Statcounter) to measure traffic. No other tracking.</p>
        <div class="cookie-actions">
            <button type="button" class="cookie-accept" data-consent="accept"><span class="lang-fr">Accepter</span><span class="lang-en">Accept</span></button>
            <button type="button" class="cookie-decline" data-consent="decline"><span class="lang-fr">Refuser</span><span class="lang-en">Decline</span></button>
        </div>
    </div>"""
html = sub(r"<div id=\"cookie-banner\".*?</button>\s*</div>\s*</div>", lambda m: COOKIE, html, expect=1, label="cookie banner -> classes + data-consent (handled by site.js)")

# --------------------------------------------------------------------------
# 3. Page skeleton: nav, header, main, footer, language switch.
# --------------------------------------------------------------------------
html = replace('<body lang="fr">', '<body class="has-fixed-nav">\n    <a class="skip-link" href="#main"><span class="lang-fr">Aller au contenu</span><span class="lang-en">Skip to content</span></a>', html, label="body: drop static lang, add skip link")
html = replace("    <nav>\n", '    <nav class="site-nav" aria-label="Navigation">\n', html, label="nav class")
html = replace('<a href="#" class="nav-profile">', '<a href="#top" class="nav-profile">', html, label="nav profile link")
html = sub(r' onclick="closeMenu\(\)"', "", html, label="menu links: drop inline onclick (site.js closes menu)")
html = replace('<button class="menu-toggle" onclick="toggleMenu()" aria-label="Menu">',
               '<button type="button" class="menu-toggle" data-action="toggle-menu" aria-label="Menu" aria-controls="nav-menu" aria-expanded="false">', html, label="menu toggle a11y")
html = replace('<img src="photo-profil.jpg" alt="Kaëlig CASTOR" class="profile-img">',
               '<img src="photo-profil.jpg" alt="" class="profile-img" width="44" height="44">', html, label="nav photo (decorative)")

html = replace("    <header>\n", '    <header class="hero" id="top">\n', html, label="header.hero")
html = replace('<div style="display: flex; align-items: center; gap: 2.5rem; flex-wrap: wrap;">', '<div class="hero-top">', html, label="hero layout class")
html = sub(r'<img src="photo-profil.jpg" alt="Kaëlig CASTOR" style="[^"]*">',
           '<img src="photo-profil.jpg" alt="Kaëlig CASTOR" class="hero-photo" width="150" height="150">', html, expect=1, label="hero photo class")

LANG_BTN = """<button type="button" id="lang-switch" class="lang-switch" data-action="toggle-lang" aria-label="Changer de langue / Switch language">
        <span class="lang-fr" lang="en">English</span>
        <span class="lang-en" lang="fr">Français</span>
    </button>"""
html = sub(r'<button id="lang-switch" onclick="toggleLang\(\)">.*?</button>', lambda m: LANG_BTN, html, expect=1, label="language switch button")

html = sub(r'(<!-- Experience -->\s*)?<div class="container">\s*<section id="experience">',
           '<main id="main" class="container">\n        <section id="experience">', html, expect=1, label="<div.container> -> <main>")
html = sub(r"</section>\s*</div>\s*<footer>\s*<p>Kaëlig CASTOR \| 2026</p>\s*</footer>",
           """</section>
    </main>

    <footer class="site-footer">
        <p>Kaëlig CASTOR · <span data-year>2026</span> ·
            <a href="http://kaelig.castor.free.fr/" class="lang-fr">ancienne adresse : kaelig.castor.free.fr</a><a href="http://kaelig.castor.free.fr/" class="lang-en">former address: kaelig.castor.free.fr</a></p>
    </footer>""", html, expect=1, label="footer (dynamic year, link to old address)")

# --------------------------------------------------------------------------
# 4. Inline styles -> semantic classes (see assets/css/site.css).
# --------------------------------------------------------------------------
STYLE_TO_CLASS = {
    "display: block; opacity: 0.6; margin-bottom: 0.2rem;": "meta-label",
    "font-size: 0.65rem; padding: 0.2rem 0.6rem; background: #f3f4f6; color: #4b5563; border-radius: 4px; font-weight: 700; text-transform: uppercase;": "kw",
    "color: var(--slate);": "t-slate",
    "font-size: 0.9rem; color: var(--text-muted); line-height: 1.6; text-align: justify; margin: 0;": "abstract",
    "font-size: 0.6rem; font-weight: 800; color: var(--accent); border: 1px solid var(--accent); padding: 0.1rem 0.4rem;": "chip",
    "font-size: 0.6rem; font-weight: 800; color: var(--accent); text-transform: uppercase; border: 1px solid var(--accent); padding: 0.2rem 0.5rem;": "chip",
    "font-size: 0.65rem; font-weight: 800; color: var(--accent); text-transform: uppercase; border: 1px solid var(--accent); padding: 0.1rem 0.4rem;": "chip",
    "max-width: 850px;": "pub-body",
    "margin: 0.5rem 0 1rem 0; font-size: 1.4rem; line-height: 1.2; font-weight: 800;": "pub-title",
    "font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;": "pub-h4",
    "font-size: 0.7rem; font-weight: 800; color: var(--accent); text-transform: uppercase; letter-spacing: 1px;": "pub-kicker",
    "display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem; font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: var(--text-muted);": "pub-meta",
    "border-top: 1px solid var(--border); padding-top: 1.5rem;": "pub-abstract",
    "font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: var(--slate); border-bottom: 2px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 1rem;": "subhead",
    "font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: var(--slate); margin-bottom: 1rem;": "subhead subhead--plain",
    "border: 1px solid var(--border); padding: 2rem; background: var(--white); position: relative; margin-top: 2rem;": "pub-card",
    "border: 1px solid var(--border); padding: 2rem; background: var(--white); position: relative;": "pub-card",
    "margin-top: 1.5rem; display: flex; flex-wrap: wrap; gap: 0.5rem;": "kw-list",
    "font-size: 0.55rem; background: var(--slate); color: var(--white); padding: 0.1rem 0.3rem; border-radius: 2px; margin-left: 0.2rem;": "filetype",
    "font-size: 0.55rem; background: var(--accent); color: white; padding: 0.1rem 0.3rem; border-radius: 2px; margin-left: 0.2rem;": "filetype",
    "font-size: 0.55rem; background: var(--accent); color: var(--white); padding: 0.1rem 0.3rem; border-radius: 2px; margin-left: 0.2rem;": "filetype",
    "position: absolute; top: 1.5rem; right: 1.5rem; font-size: 0.6rem; font-weight: 800; background: #fef3c7; color: #92400e; padding: 0.3rem 0.8rem; border-radius: 100px; text-transform: uppercase; letter-spacing: 0.5px;": "badge badge-conf",
    "position: absolute; top: 1.5rem; right: 1.5rem; font-size: 0.6rem; font-weight: 800; background: #e0f2fe; color: #0369a1; padding: 0.3rem 0.8rem; border-radius: 100px; text-transform: uppercase; letter-spacing: 0.5px;": "badge badge-wipo",
    "position: absolute; top: 1.5rem; right: 1.5rem; font-size: 0.6rem; font-weight: 800; background: #dcfce7; color: #166534; padding: 0.3rem 0.8rem; border-radius: 100px; text-transform: uppercase; letter-spacing: 0.5px;": "badge badge-granted",
    "background: #f9fafb; padding: 1.2rem; border-radius: 4px; border: 1px solid var(--border);": "subcard",
    "background: #fdfcfb; padding: 1.2rem; border-radius: 4px; border: 1px solid var(--border); border-left: 4px solid var(--accent);": "subcard subcard-accent",
    "display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem;": "grid-2",
    "display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem;": "grid-2",
    "display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem; background: #f9fafb; padding: 1.5rem; border-radius: 4px; border: 1px solid var(--border);": "panel-grid",
    "display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 1rem;": "chip-list",
    "display: flex; gap: 0.4rem; flex-wrap: wrap;": "chip-list",
    "margin-top: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap;": "chip-list",
    "font-size: 0.85rem; color: var(--text-muted); line-height: 1.6; margin-bottom: 1rem;": "desc",
    "font-size: 0.85rem; color: var(--text-muted); line-height: 1.6; margin-bottom: 0.8rem;": "desc",
    "font-size: 0.85rem; color: var(--text-muted); line-height: 1.6;": "desc",
    "font-size: 0.8rem; border-top: 1px solid #eee; pt: 0.5rem;": "card-foot",  # 'pt:' was invalid CSS
    "display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 1.5rem;": "doc-links",
}
DOC_LINK = re.compile(r"display: inline-flex; align-items: center; gap: 0\.5rem;(?P<mt> margin-top: 1\.5rem;)?(?P<ml> margin-left: 1\.5rem;)? font-size: 0\.7rem; font-weight: 800; color: var\(--(?P<color>accent|slate)\); text-decoration: none; text-transform: uppercase; border-bottom: 1px solid var\(--(?:accent|border)\);(?: padding-bottom: 2px;)?")


def norm(style):
    style = " ".join(style.split()).strip()
    return style if style.endswith(";") else style + ";"


counts = {}


def fix_tag(m):
    tag = m.group(0)
    sm = re.search(r'\sstyle="([^"]*)"', tag)
    if not sm:
        return tag
    style = norm(sm.group(1))
    cls = STYLE_TO_CLASS.get(style)
    if cls is None:
        dm = DOC_LINK.fullmatch(style)
        if dm:
            cls = "doc-link" + (" doc-link--primary" if dm.group("color") == "accent" else "") + (" doc-link--spaced" if dm.group("mt") else "")
    if cls is None:
        # keep the inline style, but make every grid column phone-safe
        fixed = re.sub(r"minmax\((\d+)px", r"minmax(min(100%, \1px)", sm.group(1))
        return tag.replace(sm.group(0), f' style="{fixed}"')
    counts[cls] = counts.get(cls, 0) + 1
    tag = tag.replace(sm.group(0), "")
    cm = re.search(r'\sclass="([^"]*)"', tag)
    if cm:
        return tag.replace(cm.group(0), f' class="{cm.group(1)} {cls}"')
    return re.sub(r"^<(\w+)", lambda t: f'<{t.group(1)} class="{cls}"', tag)


before = html.count('style="')
html = re.sub(r"<\w+\b[^>]*\sstyle=\"[^\"]*\"[^>]*>", fix_tag, html)
report.append(f"{before - html.count('style=\"'):4d}  inline styles -> classes ({before} before, {html.count('style=\"')} left)")

# --------------------------------------------------------------------------
# 5. Links: thesis/detail pages in the same tab; safe external links.
# --------------------------------------------------------------------------
html = sub(r'(href="[^"#:]+\.htm")\s+target="_blank"', r"\1", html, label="internal .htm links open in the same tab (was target=_blank)")
html = sub(r'target="_blank"(?![^>]*\brel=)', 'target="_blank" rel="noopener"', html, label="target=_blank -> rel=noopener")
html = replace('href="plasloud_v4_2col.pdf"', 'href="plasloud_v4_2col.pdf"', html, label="plasloud pdf (file now present with lowercase .pdf)")
html = replace('href="CGG_Marketing_A game changer for onshore broadband seismic_15FY-AL-249-V1_CleanSweep_D2.pdf"',
               'href="CGG_Marketing_A%20game%20changer%20for%20onshore%20broadband%20seismic_15FY-AL-249-V1_CleanSweep_D2.pdf"', html, label="URL-encode spaces in CleanSweep flyer link")

# --------------------------------------------------------------------------
# 6. Content fixes (mixed languages, untranslated strings, typos).
# --------------------------------------------------------------------------
F = [
    # Arquus block had a duplicated <div class="exp-content"> wrapper and a stray <br>
    (r'<div class="exp-content">\s*<div class="exp-content">(.*?)</div>\s*<br>\s*</div>', r'<div class="exp-content">\1</div>', 1, "Arquus: remove duplicated wrapper + <br>"),
]
for pat, rep, n, label in F:
    html = sub(pat, rep, html, expect=n, label=label)

T = [  # (old, new, expected count, label)
    ('<li>• Ingénierie : ', '<li>• <span class="lang-fr">Ingénierie :</span><span class="lang-en">Engineering:</span> ', 1, "Avnir: FR-only 'Ingénierie'"),
    ('<li>• Supervision d\'essais : ', '<li>• <span class="lang-fr">Supervision d\'essais :</span><span class="lang-en">Test supervision:</span> ', 1, "Avnir: FR-only 'Supervision d'essais'"),
    ('<li>• R&D SMR : Méthodes d\'inspection pour ', '<li>• <span class="lang-fr">R&amp;D SMR : méthodes d\'inspection pour</span><span class="lang-en">SMR R&amp;D: inspection methods for</span> ', 1, "Avnir: FR-only 'R&D SMR'"),
    ('<li>• Vibration : <a href="https://www.jst-transformers.eu/" target="_blank" rel="noopener" class="externallink">JST Transformers</a> chez ',
     '<li>• <span class="lang-fr">Vibration :</span><span class="lang-en">Vibration:</span> <a href="https://www.jst-transformers.eu/" target="_blank" rel="noopener" class="externallink">JST Transformers</a> <span class="lang-fr">chez</span><span class="lang-en">at</span> ', 1, "Avnir: FR-only 'chez'"),
    ('🤝 <span class="lang-fr">Collab:</span><span class="lang-en">Collab:</span>', '🤝 <span class="lang-fr">Collaboration :</span><span class="lang-en">Collaboration:</span>', 1, "Collab label"),
    ('<span>2021 (6 months)</span>', '<span><span class="lang-fr">2021 (6 mois)</span><span class="lang-en">2021 (6 months)</span></span>', 1, "Praexo duration FR"),
    ('<span>1997 (4 months)</span>', '<span><span class="lang-fr">1997 (4 mois)</span><span class="lang-en">1997 (4 months)</span></span>', 1, "LOA duration FR"),
    ('<span>1995 (1 month)</span>', '<span><span class="lang-fr">1995 (1 mois)</span><span class="lang-en">1995 (1 month)</span></span>', 1, "LPNHE duration FR"),
    ('Professeur Émérite, auteur de référence en acoustique</span>', '<span class="lang-fr">Professeur émérite, auteur de référence en acoustique</span><span class="lang-en">Professor Emeritus, leading author in acoustics</span></span>', 1, "Bruneau: FR-only description"),
    ('Professeur des Universités, expert en acoustique physique et milieux complexes.</span>', '<span class="lang-fr">Professeur des universités, expert en acoustique physique et milieux complexes.</span><span class="lang-en">Full Professor, expert in physical acoustics and complex media.</span></span>', 1, "Gibiat: FR-only description"),
    ('Physicien chercheur, spécialiste des rayons gamma et de l\'astronomie de haute énergie.</span>', '<span class="lang-fr">Physicien chercheur, spécialiste des rayons gamma et de l\'astronomie de haute énergie.</span><span class="lang-en">Research physicist, specialist in gamma rays and high-energy astronomy.</span></span>', 1, "Urban: FR-only description"),
    ('Maître de Conférences, LAUM</span>', '<span class="lang-fr">Maître de conférences, LAUM</span><span class="lang-en">Associate Professor, LAUM</span></span>', 1, "Béquin: FR-only title"),
    ('class="externallink">Technical Paper (JCA 2006)</a>', 'class="externallink"><span class="lang-fr">Article technique (JCA 2006)</span><span class="lang-en">Technical Paper (JCA 2006)</span></a>', 1, "EN-only 'Technical Paper'"),
    ('class="externallink">Propagation Simulations</a>', 'class="externallink"><span class="lang-fr">Simulations de propagation</span><span class="lang-en">Propagation Simulations</span></a>', 1, "EN-only 'Propagation Simulations'"),
    ('class="externallink">Technical details</a>', 'class="externallink"><span class="lang-fr">Détails techniques</span><span class="lang-en">Technical details</span></a>', 1, "EN-only 'Technical details' (waveguide)"),
    ('style="font-size: 0.75rem;">Marketing Flyer</a>', 'style="font-size: 0.75rem;"><span class="lang-fr">Plaquette commerciale</span><span class="lang-en">Marketing Flyer</span></a>', 1, "EN-only 'Marketing Flyer'"),
    ('style="font-size: 0.75rem;">Technical Details</a>', 'style="font-size: 0.75rem;"><span class="lang-fr">Détails techniques</span><span class="lang-en">Technical Details</span></a>', 1, "EN-only 'Technical Details' (CleanSweep)"),
    ('Congrès Français d\'Acoustique (CFA) — Lausanne, Suisse', '<span class="lang-fr">Congrès Français d\'Acoustique (CFA) — Lausanne, Suisse</span><span class="lang-en">French Acoustics Congress (CFA) — Lausanne, Switzerland</span>', 1, "CFA Lausanne heading bilingual"),
    ('8ème Congrès Français d\'Acoustique (CFA) — Tours, France', '<span class="lang-fr">8ᵉ Congrès Français d\'Acoustique (CFA) — Tours, France</span><span class="lang-en">8th French Acoustics Congress (CFA) — Tours, France</span>', 1, "CFA Tours heading bilingual"),
    ('Attaché d\'Enseignement (Ater / Monitorat)', 'Moniteur / ATER (Attaché Temporaire d\'Enseignement et de Recherche)', 1, "ATER spelled out"),
    ('Mention Très Honorable.', 'Mention Très Honorable.', 1, "(check) PhD honours FR"),
    ('Thesis on numerical and experimental modeling of plasma transducers. Fundamental', 'Thesis on numerical and experimental modeling of plasma transducers, awarded with highest honours (<i lang="fr">mention Très Honorable</i>). Fundamental', 1, "PhD honours missing in EN"),
]
for old, new, n, label in T:
    if new is None:
        continue
    html = replace(old, new, html, expect=n, label=label)

# French month names were shown in the English version
MONTHS = {"Janvier": "January", "Février": "February", "Mars": "March", "Avril": "April", "Mai": "May", "Juin": "June",
          "Juillet": "July", "Août": "August", "Septembre": "September", "Octobre": "October", "Novembre": "November", "Décembre": "December"}
EN2FR = {v: k for k, v in MONTHS.items()}
EN2FR["Aug"] = "Août"; EN2FR["July"] = "Juillet"; EN2FR["Dec"] = "Décembre"


def bilingual_date(m):
    word, rest = m.group(2), m.group(3).strip()
    fr_month = word.lower() if word in MONTHS else EN2FR[word].lower()
    en_month = MONTHS.get(word, word)
    dm = re.fullmatch(r"(\d{1,2}), (\d{4})", rest)
    if dm:  # "Aug 2, 2016" -> "2 août 2016"
        fr, en = f"{dm.group(1)} {fr_month} {dm.group(2)}", f"{en_month} {rest}"
    else:   # "Septembre 2000" -> "September 2000"
        fr, en = f"{fr_month} {rest}", f"{en_month} {rest}"
    return f'{m.group(1)}<span class="lang-fr">{fr}</span><span class="lang-en">{en}</span></span>'


html = sub(r'(<span class="t-slate">)(Janvier|Février|Mars|Avril|Mai|Juin|Juillet|Août|Septembre|Octobre|Novembre|Décembre|January|February|March|April|May|June|July|August|September|October|November|December|Aug|Dec)\s+([^<]+)</span>',
           bilingual_date, html, label="publication dates: bilingual month names")

# --------------------------------------------------------------------------
# 7. Credentials: link the diplomas and recommendation letters.
# --------------------------------------------------------------------------
CREDS = """
            <div class="grid-2" style="margin-top: 3rem;">
                <div class="subcard">
                    <h3 class="subhead"><span class="lang-fr">Diplômes</span><span class="lang-en">Diplomas</span></h3>
                    <ul class="cred-list">
                        <li><a class="externallink" href="credentials/diplomas/MS_BGD_Promo_2020_CASTOR_Kaelig.pdf" target="_blank" rel="noopener"><span class="lang-fr">Mastère Spécialisé Big Data — Télécom Paris (2020)</span><span class="lang-en">Post-Master in Big Data — Télécom Paris (2020)</span></a></li>
                        <li><a class="externallink" href="credentials/diplomas/Kaelig_Castor_diplome_Doctorat.jpg" target="_blank" rel="noopener"><span class="lang-fr">Diplôme de Doctorat en Acoustique (2001)</span><span class="lang-en">PhD diploma in Acoustics (2001)</span></a></li>
                        <li><a class="externallink" href="credentials/diplomas/diplome_de_these_CASTOR_kaelig__.pdf" target="_blank" rel="noopener"><span class="lang-fr">Attestation de diplôme de thèse</span><span class="lang-en">PhD degree certificate</span></a></li>
                        <li><a class="externallink" href="credentials/diplomas/Castor_Kaelig_PhD_Certificate_of_Accreditation.pdf" target="_blank" rel="noopener"><span class="lang-fr">Certificat d'accréditation du doctorat (EN)</span><span class="lang-en">PhD Certificate of Accreditation</span></a></li>
                        <li><a class="externallink" href="credentials/diplomas/20010909_French_Certification_PhD_in_Acoustics.pdf" target="_blank" rel="noopener"><span class="lang-fr">Certification du doctorat</span><span class="lang-en">French certification of the PhD</span></a></li>
                        <li><a class="externallink" href="credentials/diplomas/20010919_Proces_Verbal_de_Soutenance_de_These.pdf" target="_blank" rel="noopener"><span class="lang-fr">Procès-verbal de soutenance de thèse</span><span class="lang-en">PhD defence report</span></a></li>
                        <li><a class="externallink" href="credentials/diplomas/Kaelig_Castor_diplome_DEA.jpg" target="_blank" rel="noopener"><span class="lang-fr">Diplôme de DEA d'Acoustique Appliquée (1997)</span><span class="lang-en">DEA diploma in Applied Acoustics (1997)</span></a></li>
                    </ul>
                </div>
                <div class="subcard">
                    <h3 class="subhead"><span class="lang-fr">Lettres de recommandation</span><span class="lang-en">Recommendation letters</span></h3>
                    <ul class="cred-list">
                        <li><a class="externallink" href="credentials/letters/20190524_Philipe_Feugere_VP_Technology_CGG.pdf" target="_blank" rel="noopener">Philippe Feugère — VP Technology, CGG (2019)</a></li>
                        <li><a class="externallink" href="credentials/letters/20030905_William_Kuperman_Director_MPL_SIO_UCSD.pdf" target="_blank" rel="noopener">William A. Kuperman — Director MPL, Scripps / UCSD (2003)</a></li>
                        <li><a class="externallink" href="credentials/letters/20030730_Philippe_Roux_Collegue_CNRS_durant_postdoc_au_MPL_ScrippsInstOcean_UCSD.pdf" target="_blank" rel="noopener">Philippe Roux — CNRS, Scripps / UCSD (2003)</a></li>
                        <li><a class="externallink" href="credentials/letters/20021231_Attestation_Postdoc_Bill_Kuperman_MPL_SIO_UCSD.pdf" target="_blank" rel="noopener"><span class="lang-fr">Attestation de post-doctorat — W. A. Kuperman (2002)</span><span class="lang-en">Postdoc certificate — W. A. Kuperman (2002)</span></a></li>
                        <li><a class="externallink" href="credentials/letters/20011004_Michel_Bruneau_Directeur_de_Thèse_Acoustique_IAM_Le_Mans.pdf" target="_blank" rel="noopener">Michel Bruneau — <span class="lang-fr">directeur de thèse</span><span class="lang-en">PhD supervisor</span> (2001)</a></li>
                        <li><a class="externallink" href="credentials/letters/20011005_Philippe_Bequin_Directeur_de_Thèse_Acoustique_IAM_Le_Mans.pdf" target="_blank" rel="noopener">Philippe Béquin — <span class="lang-fr">directeur de thèse</span><span class="lang-en">PhD supervisor</span> (2001)</a></li>
                        <li><a class="externallink" href="credentials/letters/20011006_Vincent_Gibiat_Directeur_de_Stage_de_DEA_Acoustique_a_l_ESPCI.pdf" target="_blank" rel="noopener">Vincent Gibiat — <span class="lang-fr">directeur de stage de DEA</span><span class="lang-en">Master's internship supervisor</span> (2001)</a></li>
                    </ul>
                </div>
            </div>
"""
html = sub(r'(<section id="certification">.*?)(\s*</section>)', lambda m: m.group(1) + CREDS + m.group(2), html, expect=1, label="certifications: add diplomas & letters")

open(dst, "w", encoding="utf-8").write(html)
print("\n".join(report))
print("classes:", ", ".join(f"{k}×{v}" for k, v in sorted(counts.items(), key=lambda x: -x[1])))
