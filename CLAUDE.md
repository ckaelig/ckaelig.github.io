# Kaëlig CASTOR — personal portfolio

Static bilingual (FR/EN) CV site. Published by GitHub Pages at https://ckaelig.github.io/
from the `main` branch of the `ckaelig/ckaelig.github.io` repo. No build step, no framework.
The old host http://kaelig.castor.free.fr (HTTP only) just redirects here (see "free.fr").

## Layout
- `index.html`: homepage (single long page: experience, publications, skills, education, teaching, certifications).
- `phd.htm`, `waveguid.htm`, `antimatter.htm`, `hydroacoustics*.htm`, `infrasound*.htm`: detail pages.
  Keep these file names: old links and Google results point to them.
- `index.htm`, `these.htm`: redirect stubs (old URLs). `404.html`: GitHub Pages 404 page.
- `assets/css/site.css`: the ONLY place for design tokens (colours, fonts) and shared components.
- `assets/js/site.js`: language switch, mobile menu, cookie consent / Statcounter. Loaded in `<head>` without defer.
- PDFs, slides and images sit at the root or in `praexo/`, `rapport_these/`, `hydroacoustics/`, `infrasound_propagation/`.
- `tools/`: validator, tests, free.fr package builder, preview/backup/screenshot scripts. `tools/migrations/`: one-off scripts, history only, never re-run.

## Language system (the source of past bugs, so read this first)
- Every translatable piece exists twice: `<span class="lang-fr">…</span><span class="lang-en">…</span>`.
  CSS hides the other language using `html[lang]`. Never set `lang` on `<body>`.
- `site.js` picks the language from: `?lang=fr|en` → localStorage `pref-lang` → English (default; browser language ignored).
  Short links: https://ckaelig.github.io/en/ and /fr/ (`en/index.html`, `fr/index.html` redirect stubs).
  It rewrites internal `.htm/.html` links to carry `?lang=`, so the choice follows the visitor.
- Language switch: two real links `<a class="lang-switch lang-fr" href="?lang=en" data-action="toggle-lang">English</a>` /
  `<a class="lang-switch lang-en" href="?lang=fr" …>Français</a>` (copy from any page). They work even if a stale or
  blocked site.js does not run; site.js intercepts them and switches in place. Pages carry `translate="no"` +
  `<meta name="google" content="notranslate">` so browser auto-translation cannot fight the switch.
- After editing `site.css` or `site.js`, run `python3 tools/stamp_assets.py` (updates the `?v=` cache-busting hash in
  every page; check_site.py fails when a stamp is stale).
- Detail pages can set `data-title-fr` / `data-title-en` on `<html>` for a translated `<title>`.

## Rules
- Run `python3 tools/check_site.py` after every change. It must report 0 errors (CI and the pre-commit hook enforce this).
  If you fix a new class of bug, add a test to `tools/test_check_site.py`.
- New page = copy the `<head>` of an existing detail page (fonts, `site.css`, `site.js`, `<meta charset="UTF-8">`), add the
  `page-bar` back link and the language button. UTF-8 only.
- Styling: use the classes in `site.css` (`subcard`, `chip`, `pub-card`, `doc-link`, …). No new inline colours; only tokens (`var(--accent)`).
- Internal pages open in the same tab (no `target="_blank"`); external links use `target="_blank" rel="noopener"`.
- Third-party scripts: only `cdn.jsdelivr.net` (exact version pinned, e.g. `mathjax@3.2.2`) and Statcounter (after consent).
  Never polyfill.io (compromised in 2024).
- File names are case-sensitive on GitHub Pages; keep extensions lowercase. No file over 100 MB (warning over 50 MB).
- Fonts are self-hosted (`assets/fonts/`, declared at the top of `site.css`): never link Google Fonts again (GDPR).
- Check visually with `tools/screenshots.sh <page>` (desktop 1366, laptop 1280, phone 390; FR + EN).

## Privacy (hard rules: the repo is public and git history is permanent)
- Never publish phone number, home address or date of birth (the validator blocks the known values).
- Never add anything from the legacy folder `../kaelig.castor.free.fr/` without an explicit request:
  it mixes the site with personal, financial, family, employer and client documents.
- Diplomas and recommendation letters are "available upon request" only: never publish the files (the validator blocks such paths).
- Scanned PDFs/JPGs cannot be text-checked: look at them before publishing.

## free.fr
- `python3 tools/build_freefr.py` writes `dist/freefr/` (one redirect stub per old page name, same file names) and
  `dist/FREEFR_CLEANUP.md` (what to delete on the server). The owner uploads and deletes by FTP. Never automate deletion.

## Backups
- `tools/backup.sh` → `../YYYYMMDD_ckaelig.github.io/`. Full legacy backups live in `../YYYYMMDD_kaeligcastorfreefr/`.
