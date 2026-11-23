# ckaelig.github.io

Personal portfolio / CV of Kaëlig CASTOR, in French and English.
Live at **https://ckaelig.github.io/**. The former address http://kaelig.castor.free.fr redirects here.

## Everyday use

| Task | Command |
|---|---|
| Preview locally | `tools/serve.sh` then open http://localhost:8000/ |
| Check everything (links, translations, privacy, security, sizes) | `python3 tools/check_site.py` |
| Also test external links (slow) | `python3 tools/check_site.py --external` |
| Screenshots desktop/phone, FR/EN | `tools/screenshots.sh index.html` |
| Publish | `git add -A && git commit -m "…" && git push` (GitHub Pages updates in ~1 min) |
| Dated backup of the project | `tools/backup.sh` |
| Rebuild the free.fr redirect package | `python3 tools/build_freefr.py` |

After cloning, run `git config core.hooksPath .githooks` once. Commits with site errors are then refused.

## Editing content

- Text always comes in pairs: `<span class="lang-fr">Bonjour</span><span class="lang-en">Hello</span>`.
  The checker warns when a page has more French than English pieces (or the reverse).
- Shared look and feel: `assets/css/site.css` (colours at the top). Behaviour: `assets/js/site.js`.
- A link to another page of the site keeps the visitor's language automatically.
- More conventions: see `CLAUDE.md`.

## First publication on GitHub (once)

1. On github.com, create a **public** repository named exactly `ckaelig.github.io` (no README).
2. In this folder:
   ```sh
   git remote add origin https://github.com/ckaelig/ckaelig.github.io.git
   git push -u origin main
   ```
3. On GitHub: *Settings → Pages → Build and deployment → Source: Deploy from a branch → `main` / `(root)`*.
   Tick **Enforce HTTPS**.
4. A few minutes later, https://ckaelig.github.io/ is online.

## free.fr

`python3 tools/build_freefr.py` creates `dist/freefr/`. Upload its content by FTP (FileZilla, `ftpperso.free.fr`)
to the root of the free.fr space, overwriting existing files. Then follow `dist/FREEFR_CLEANUP.md` to delete the
private files that are still publicly downloadable there.
