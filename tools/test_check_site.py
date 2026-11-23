#!/usr/bin/env python3
"""Regression tests for tools/check_site.py: every bug fixed in Nov. 2026 must
stay detectable. Builds tiny throw-away sites and asserts on the output.

    python3 tools/test_check_site.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_site.py")

GOOD_HEAD = """<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><title>t</title>
<link rel="stylesheet" href="assets/css/site.css"><script src="assets/js/site.js"></script></head>"""


def run(files):
    with tempfile.TemporaryDirectory() as d:
        for rel, content in files.items():
            p = os.path.join(d, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as fh:
                fh.write(content.encode("utf-8") if isinstance(content, str) else content)
        env = dict(os.environ, SITE_ROOT=d)
        r = subprocess.run([sys.executable, "-I", CHECK], env=env, capture_output=True, text=True)
        return r.returncode, r.stdout


def site(body, extra=None):
    files = {
        "assets/css/site.css": "",
        "assets/js/site.js": "",
        "index.html": GOOD_HEAD + "<body>" + body + "</body></html>",
    }
    files.update(extra or {})
    return files


class CheckSiteTests(unittest.TestCase):
    def test_clean_site_passes(self):
        code, out = run(site('<p class="lang-fr">a</p><p class="lang-en">b</p>'))
        self.assertEqual(code, 0, out)

    def test_case_mismatch_is_an_error(self):  # plasloud_v4_2col.PDF bug
        code, out = run(site('<a href="paper.pdf">x</a>', {"paper.PDF": b"%PDF"}))
        self.assertEqual(code, 1)
        self.assertIn("different letter case", out)

    def test_hardcoded_body_lang_is_an_error(self):  # phd.htm always English bug
        files = site("")
        files["phd.htm"] = GOOD_HEAD + '<body lang="en"><a href="index.html">b</a></body></html>'
        code, out = run(files)
        self.assertEqual(code, 1)
        self.assertIn("hard-coded", out)

    def test_page_without_site_js_is_an_error(self):
        files = site('<a href="x.htm">x</a>', {"x.htm": '<html><head><meta charset="UTF-8"></head><body></body></html>'})
        code, out = run(files)
        self.assertEqual(code, 1)
        self.assertIn("site.js", out)

    def test_polyfill_io_is_banned(self):
        code, out = run(site('<script src="https://polyfill.io/v3/polyfill.min.js"></script>'))
        self.assertEqual(code, 1)
        self.assertIn("banned host", out)

    def test_unpinned_cdn_is_an_error(self):
        code, out = run(site('<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>'))
        self.assertEqual(code, 1)
        self.assertIn("pin an exact version", out)

    def test_phone_number_is_an_error(self):
        code, out = run(site("<p>Cell: (+33) 6 63 22 41 95</p>"))
        self.assertEqual(code, 1)
        self.assertIn("phone", out)

    def test_private_folder_is_an_error(self):
        code, out = run(site('<a href="achat_immo/x.pdf">x</a>', {"achat_immo/x.pdf": b"%PDF"}))
        self.assertEqual(code, 1)
        self.assertIn("looks private", out)

    def test_missing_translation_warns(self):
        code, out = run(site('<p class="lang-fr">seulement en français</p>'))
        self.assertEqual(code, 0)
        self.assertIn("translation may be missing", out)

    def test_internal_page_in_new_tab_warns(self):  # thesis link opened a bare new tab
        code, out = run(site('<a href="phd.htm" target="_blank" rel="noopener">t</a>',
                             {"phd.htm": GOOD_HEAD + "<body><a href=\"index.html\">b</a></body></html>"}))
        self.assertIn("opens in a new tab", out)

    def test_latin1_file_is_an_error(self):
        code, out = run(site("", {"old.css": "caf\xe9".encode("latin-1")}))
        self.assertEqual(code, 1)
        self.assertIn("UTF-8", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
