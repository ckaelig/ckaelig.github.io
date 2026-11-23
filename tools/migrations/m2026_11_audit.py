#!/usr/bin/env python3
"""One-off migration (2026-11-23, after the site audit). Kept for traceability.
Rollback point: git tag `avant-audit-2026-11-23`.

index.html:
  * Arquus: "2024" -> "Apr.–Sep. 2024 (6 months)" (owner's information)
  * publication/patent abstracts collapsed by default (<details>), so the page
    can be scanned in seconds; site.js opens them all before printing
  * frozen citation counts removed (they go stale; Google Scholar is linked)
  * "Patent …" kicker translated in the French view ("Brevet …")
"""
import re
import sys

p = sys.argv[1] if len(sys.argv) > 1 else "index.html"
t = open(p, encoding="utf-8").read()


def must(n, expected, label):
    if n != expected:
        raise SystemExit(f"[{label}] expected {expected}, got {n}")
    print(f"{n:3d}  {label}")


# 1. Arquus dates ------------------------------------------------------------
old = '<a href="https://primeengineering.fr/" target="_blank" rel="noopener" class="company">(Prime Engineering)</a>\n                                    <span>2024</span>'
must(t.count(old), 1, "Arquus date")
t = t.replace(old, old.replace(
    "<span>2024</span>",
    '<span><span class="lang-fr">avr. — sept. 2024 (6 mois)</span><span class="lang-en">Apr. — Sep. 2024 (6 months)</span></span>'))

# 2. Collapsible abstracts ---------------------------------------------------
SUMMARY = ('<summary class="pub-h4"><span class="lang-fr">Lire le résumé</span>'
           '<span class="lang-en">Read the abstract</span></summary>')
out, pos, n = [], 0, 0
for m in re.finditer(r'<div class="pub-abstract">\s*<h4 class="pub-h4">[^<]*</h4>', t):
    start = m.start()
    if start < pos:
        continue
    depth, end = 0, None
    for d in re.finditer(r"<div\b|</div>", t[start:]):
        depth += 1 if d.group(0) == "<div" else -1
        if depth == 0:
            end = start + d.start()  # position of the closing </div>
            break
    out.append(t[pos:start])
    out.append('<details class="pub-abstract">\n                        ' + SUMMARY)
    out.append(t[m.end():end])
    out.append("</details>")
    pos = end + len("</div>")
    n += 1
out.append(t[pos:])
t = "".join(out)
must(n, 17, "abstracts -> <details>")

# 3. Frozen citation counts --------------------------------------------------
t, n = re.subn(r'\n\s*<div>\s*<span class="lang-fr meta-label">Citations</span>\s*'
               r'<span class="lang-en meta-label">Citations</span>\s*<span class="t-slate">[^<]*</span>\s*</div>', "", t)
must(n, 5, "citation counts removed")

# 4. "Patent" kicker bilingual -----------------------------------------------
t, n = re.subn(r'<span class="pub-kicker">Patent ',
               '<span class="pub-kicker"><span class="lang-fr">Brevet</span><span class="lang-en">Patent</span> ', t)
must(n, 3, "Patent -> Brevet (FR)")

open(p, "w", encoding="utf-8").write(t)
