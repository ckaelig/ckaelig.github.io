#!/usr/bin/env python3
"""Build the package that turns http://kaelig.castor.free.fr into a pointer
to the secure site https://ckaelig.github.io (free.fr has no HTTPS).

    python3 tools/build_freefr.py [LEGACY_DIR]

LEGACY_DIR = local copy of what was uploaded to free.fr over the years
(default: ../kaelig.castor.free.fr). Every *.htm / *.html found at its top
level gets a same-name redirect stub, so:
  * every old URL (Google, CVs sent years ago, LinkedIn…) still lands on
    the right page of the new site, in the right language;
  * uploading the stubs OVERWRITES the old pages that still show the phone
    number, home address and date of birth (cv.htm, cvang.htm, index_*.htm…).

Output: dist/freefr/   (upload its content to the free.fr FTP root)
        dist/freefr/../FREEFR_CLEANUP.md   (what to delete by FTP, and why)
Nothing is uploaded or deleted by this script.
"""
import html
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NEW = "https://ckaelig.github.io/"
LEGACY = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "..", "kaelig.castor.free.fr"))
OUT = os.path.join(ROOT, "dist", "freefr")

# old page -> (new path, forced language or None, anchor)
EXPLICIT = {
    "index.htm": ("", None, ""), "index.html": ("", None, ""),
    "indexfr.htm": ("", "fr", ""), "sommaire.htm": ("", "fr", ""), "cv.htm": ("", "fr", ""),
    "indexang.htm": ("", "en", ""), "sommaireang.htm": ("", "en", ""), "cvang.htm": ("", "en", ""),
    "castor_kaelig_resume.htm": ("", "en", ""),
    "phd.htm": ("phd.htm", None, ""), "these.htm": ("phd.htm", "fr", ""),
    "principe.htm": ("phd.htm", "fr", ""), "principle.htm": ("phd.htm", "en", ""),
    "gap.htm": ("phd.htm", None, ""), "acmodel.htm": ("phd.htm", None, ""), "decharge.htm": ("phd.htm", "fr", ""),
    "descrgap.htm": ("phd.htm", "fr", ""), "directiv.htm": ("phd.htm", None, ""),
    "mesald.htm": ("phd.htm", "fr", ""), "mesald_ang.htm": ("phd.htm", "en", ""), "abstract_corona.htm": ("phd.htm", None, ""),
    "waveguid.htm": ("waveguid.htm", None, ""), "antimatter.htm": ("antimatter.htm", None, ""),
    "dea.htm": ("", "fr", "#education"), "maitrise.htm": ("", "fr", "#education"), "licence.htm": ("", "fr", "#education"),
    "enseig.htm": ("", "fr", "#teaching"), "teaching.htm": ("", "en", "#teaching"),
    "cnrs.htm": ("", None, "#experience"), "CleanSweep.htm": ("", None, "#experience"),
    "music.htm": ("", "fr", ""), "musicang.htm": ("", "en", ""),
}
for n in ["hydroacoustics", "infrasound"]:
    for s in ["", "_2", "_3", "_4", "_5"]:
        EXPLICIT[f"{n}{s}.htm"] = (f"{n}{s}.htm", None, "")

STUB = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, follow">
<title>Kaëlig CASTOR — {title}</title>
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url={url}">
<script>
  // keep the visitor's #anchor and ?lang= when the old URL had them
  (function () {{
    var u = "{url_js}";
    var m = /[?&]lang=(fr|en)/.exec(location.search);
    if (m && u.indexOf("lang=") < 0) u += (u.indexOf("?") < 0 ? "?" : "&") + "lang=" + m[1];
    if (location.hash && u.indexOf("#") < 0) u += location.hash;
    location.replace(u);
  }})();
</script>
<style>
  body {{ font: 16px/1.6 system-ui, sans-serif; color: #0f172a; background: #f8fafc; display: grid; place-items: center; min-height: 90vh; margin: 0; padding: 1rem; text-align: center; }}
  a {{ color: #3b4c61; font-weight: 700; }}
</style>
</head>
<body>
<main>
<p><strong>Ce site a déménagé</strong> vers une adresse sécurisée (HTTPS).<br>
<strong>This site has moved</strong> to a secure (HTTPS) address.</p>
<p><a href="{url}">{url_text}</a></p>
</main>
</body>
</html>
"""


def target(name):
    path, lang, anchor = EXPLICIT.get(name, ("", None, ""))
    url = NEW + path + (f"?lang={lang}" if lang else "") + anchor
    return url, lang


def main():
    if not os.path.isdir(LEGACY):
        sys.exit(f"Legacy folder not found: {LEGACY}")
    os.makedirs(OUT, exist_ok=True)
    legacy_pages = sorted(f for f in os.listdir(LEGACY)
                          if f.lower().endswith((".htm", ".html")) and os.path.isfile(os.path.join(LEGACY, f)))
    names = sorted(set(legacy_pages) | set(EXPLICIT))
    for name in names:
        url, lang = target(name)
        page = STUB.format(lang=lang or "fr", title="CV / Resume", url=html.escape(url, quote=True),
                           url_js=url.replace("\\", "\\\\").replace('"', '\\"'), url_text=html.escape(url))
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(page)
    write_cleanup(legacy_pages)
    print(f"{len(names)} redirect stubs -> {os.path.relpath(OUT, ROOT)}/")
    print(f"cleanup list -> {os.path.relpath(os.path.join(ROOT, 'dist', 'FREEFR_CLEANUP.md'), ROOT)}")


SENSITIVE = {  # folder -> why it must not stay public
    "achat_immo": "financial statements (situation financière)", "MACIF": "insurance documents",
    "natixis": "banking", "sg": "banking (Société Générale)", "mamy": "family documents",
    "vaccins": "health records", "CV": "old CVs with phone, address, date of birth",
    "job": "job applications", "les_echos": "personal subscriptions / press", "diplomes": "now published on GitHub under credentials/",
    "lettres_de_recommandation": "now published on GitHub under credentials/",
    "CGG": "employer material (confidentiality)", "sercel": "employer/client material (confidentiality)",
    "conoco": "client material", "conoco_envoi": "client material", "KHALDA": "client material", "PDO": "client material",
    "JSALLAS": "colleague's material", "Invention_Disclosure": "unpublished invention disclosures",
    "20190524_CastorKaelig_patents": "patent working files", "internal_training": "employer internal training",
    "livres": "copyrighted books", "MANUELS_MUSIQUE": "copyrighted music books", "latex": "drafts / sources",
    "photos": "private photos", "foto_berlin": "private photos", "tunisie": "private photos", "cancun": "private photos",
    "cedric": "third-party files", "celine": "third-party files", "fred": "third-party files", "jenein": "third-party files",
    "steph_walt": "third-party files", "2thomas": "third-party files", "2_yves": "third-party files", "2_cggv": "third-party files",
    "tklein": "third-party files", "vikter": "third-party files", "bouygues": "personal (telecom)", "altran": "job/employer documents",
    "aes": "conference material", "ParisTech": "school application file", "SES720_Economie": "course material", "SES721": "course material",
}


def write_cleanup(legacy_pages):
    dirs = sorted(d for d in os.listdir(LEGACY) if os.path.isdir(os.path.join(LEGACY, d)))
    files = sorted(f for f in os.listdir(LEGACY) if os.path.isfile(os.path.join(LEGACY, f)))
    non_html = [f for f in files if not f.lower().endswith((".htm", ".html"))]
    lines = [
        "# free.fr clean-up (to do by FTP, by you)",
        "",
        "Generated by `tools/build_freefr.py`. Nothing here is deleted automatically.",
        "",
        "Free.fr only hides folder *listings* (HTTP 403); every file inside stays downloadable by",
        "anyone who knows or guesses its URL. On 2026-11-23, one file from each of these folders",
        "was publicly downloadable (HTTP 200), e.g. `achat_immo/20100616_situation_financiere.pdf`.",
        "",
        "## Recommended: keep only the redirect stubs",
        "",
        "1. Connect with FileZilla to `ftpperso.free.fr` (login `kaelig.castor`).",
        "2. Upload the content of `dist/freefr/` to the root (overwrite). This alone scrubs the",
        "   old pages that still show phone / address / date of birth.",
        "3. Delete everything else on the server: every folder and every non-HTML file below.",
        "   All public documents (papers, patents, CVs, thesis) are now on https://ckaelig.github.io/",
        "   at the same paths.",
        "",
        "## Folders on the server (delete all)",
        "",
        "| Folder | Why |",
        "|---|---|",
    ]
    for d in dirs:
        lines.append(f"| `{d}/` | {SENSITIVE.get(d, 'not used by the new site')} |")
    lines += ["", "## Non-HTML files at the root (delete all; public ones are on GitHub)", ""]
    lines += [f"- `{f}`" for f in non_html]
    lines += ["", "## HTML pages replaced by redirect stubs (overwritten by step 2)", ""]
    lines += [f"- `{f}`" for f in legacy_pages]
    with open(os.path.join(ROOT, "dist", "FREEFR_CLEANUP.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
