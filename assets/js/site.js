/* ==========================================================================
   Kaëlig CASTOR — shared behaviour for every page.
   Load it in <head> WITHOUT defer/async: it sets <html lang> before the
   first paint, so the wrong language never flashes on screen.

   Language resolution order:
     1. ?lang=fr|en in the URL (shareable links, survives blocked storage)
     2. the visitor's last choice (localStorage "pref-lang")
     3. English (site default; the browser language is NOT used)
   Internal links (.htm/.html) get ?lang=… so the choice follows the
   visitor from page to page, even when storage is unavailable.
   ========================================================================== */
(function () {
    'use strict';

    var KEY = 'pref-lang';
    var LANGS = ['fr', 'en'];

    function storageGet(k) {
        try { return window.localStorage.getItem(k); } catch (e) { return null; }
    }
    function storageSet(k, v) {
        try { window.localStorage.setItem(k, v); } catch (e) { /* private mode, file:// … */ }
    }

    function langFromUrl() {
        var m = /[?&]lang=(fr|en)(?:&|$)/.exec(window.location.search);
        return m ? m[1] : null;
    }

    function detectLang() {
        var fromUrl = langFromUrl();
        if (fromUrl) return fromUrl;
        var saved = storageGet(KEY);
        if (LANGS.indexOf(saved) !== -1) return saved;
        return 'en';  // default language of the site (owner's choice, Nov. 2026)
    }

    var lang = detectLang();
    document.documentElement.lang = lang;
    if (langFromUrl()) storageSet(KEY, lang);

    function isInternalPage(href) {
        return href && !/^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(href) && /\.html?(?:[?#]|$)/i.test(href);
    }

    function withLang(href, l) {
        var hashAt = href.indexOf('#');
        var hash = hashAt >= 0 ? href.slice(hashAt) : '';
        var base = hashAt >= 0 ? href.slice(0, hashAt) : href;
        base = base.replace(/([?&])lang=(?:fr|en)(&|$)/, function (_, pre, post) {
            return post ? pre : '';
        }).replace(/[?&]$/, '');
        return base + (base.indexOf('?') >= 0 ? '&' : '?') + 'lang=' + l + hash;
    }

    function updateLinks() {
        var links = document.querySelectorAll('a[href]');
        for (var i = 0; i < links.length; i++) {
            var a = links[i];
            var orig = a.getAttribute('data-href') || a.getAttribute('href');
            if (!isInternalPage(orig)) continue;
            a.setAttribute('data-href', orig);
            a.setAttribute('href', withLang(orig, lang));
        }
    }

    function updateTitle() {
        var t = document.documentElement.getAttribute('data-title-' + lang);
        if (t) document.title = t;
    }

    function syncUrl() {
        if (!langFromUrl() || !window.history || !history.replaceState) return;
        history.replaceState(null, '', withLang(location.pathname.split('/').pop() + location.search + location.hash, lang));
    }

    function setLang(l) {
        if (LANGS.indexOf(l) === -1) return;
        lang = l;
        document.documentElement.lang = l;
        storageSet(KEY, l);
        syncUrl();
        updateLinks();
        updateTitle();
    }

    // Public API (kept for inline onclick handlers in older markup)
    window.toggleLang = function () { setLang(lang === 'fr' ? 'en' : 'fr'); };
    window.setLang = setLang;

    /* --- Mobile menu ------------------------------------------------------ */
    function menu() { return document.getElementById('nav-menu'); }
    function toggleBtn() { return document.querySelector('[data-action="toggle-menu"]'); }

    window.toggleMenu = function () {
        var m = menu(); if (!m) return;
        var open = m.classList.toggle('active');
        var b = toggleBtn(); if (b) b.setAttribute('aria-expanded', String(open));
    };
    window.closeMenu = function () {
        var m = menu(); if (!m) return;
        m.classList.remove('active');
        var b = toggleBtn(); if (b) b.setAttribute('aria-expanded', 'false');
    };

    /* --- Audience measurement (Statcounter), only after consent ---------- */
    function loadStatcounter(banner) {
        window.sc_project = Number(banner.getAttribute('data-sc-project'));
        window.sc_invisible = 1;
        window.sc_security = banner.getAttribute('data-sc-security');
        var s = document.createElement('script');
        s.src = 'https://www.statcounter.com/counter/counter.js';
        s.async = true;
        document.body.appendChild(s);
    }

    function initConsent() {
        var banner = document.getElementById('cookie-banner');
        if (!banner) return;
        var consent = storageGet('cookieConsent');
        if (consent === 'accepted') { loadStatcounter(banner); return; }
        if (consent === null) banner.hidden = false;
        banner.addEventListener('click', function (e) {
            var btn = e.target.closest('[data-consent]');
            if (!btn) return;
            var accepted = btn.getAttribute('data-consent') === 'accept';
            storageSet('cookieConsent', accepted ? 'accepted' : 'declined');
            banner.hidden = true;
            if (accepted) loadStatcounter(banner);
        });
    }

    /* --- Wiring ----------------------------------------------------------- */
    document.addEventListener('click', function (e) {
        var el = e.target.closest('[data-action]');
        if (!el) {
            // close the mobile menu after choosing an entry
            if (e.target.closest('#nav-menu a')) window.closeMenu();
            return;
        }
        var action = el.getAttribute('data-action');
        if (action === 'toggle-lang') {
            // The switch is a real link (?lang=xx) so it still works if this script
            // is stale or blocked; when the script runs, switch in place instead.
            e.preventDefault();
            window.toggleLang();
        }
        else if (action === 'toggle-menu') window.toggleMenu();
    });

    // Printing / saving as PDF: show every collapsed abstract
    window.addEventListener('beforeprint', function () {
        var d = document.querySelectorAll('details:not([open])');
        for (var i = 0; i < d.length; i++) { d[i].setAttribute('open', ''); d[i].setAttribute('data-print-open', ''); }
    });
    window.addEventListener('afterprint', function () {
        var d = document.querySelectorAll('details[data-print-open]');
        for (var i = 0; i < d.length; i++) { d[i].removeAttribute('open'); d[i].removeAttribute('data-print-open'); }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') window.closeMenu();
    });

    document.addEventListener('DOMContentLoaded', function () {
        updateLinks();
        updateTitle();
        initConsent();
        var y = document.querySelectorAll('[data-year]');
        for (var i = 0; i < y.length; i++) y[i].textContent = String(new Date().getFullYear());
    });
})();
