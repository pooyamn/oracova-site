#!/usr/bin/env python3
"""Single source of truth for the site header.

Run:  python3 tools/header.py            # apply to root + v18
      python3 tools/header.py --check    # verify all pages carry identical header

Every page gets the SAME markup and the SAME self-contained CSS. The block uses its
own hardcoded values (not page tokens) so it renders identically no matter which
stylesheet lineage a page came from.
"""
import re, sys, hashlib, pathlib

TOKENS = """/* ===== oracova shared stylesheet (tools/header.py -- do not edit by hand) =====
   One palette, one type scale, one button, one instrument, one set of chrome.
   Page stylesheets load AFTER this and may extend it; they must not restate it.
   Four rounds of review found the same bug shape every time: a rule written in
   one file and silently outranked by a near-identical rule in another. */

:root {
  /* page palette */
  --bg: #0E0F11;
  --surface: #15161A;
  --surface-2: #191B20;
  --border: rgba(255,255,255,.07);
  --border-strong: rgba(255,255,255,.14);
  --text: #EDEEF0;
  --text-dim: #9DA1A8;
  --text-faint: #83888F;
  --brand: #FFB454;
  --brand-ink: #1A1204;
  --brand-hover: #FFC276;
  --pass: #4ADE80;
  --fail: #F87171;
  --glow: rgba(255,180,84,.10);
  --nav-bg: rgba(14,15,17,.9);
  --board-rim: rgba(255,255,255,.45);
  --select: rgba(255,180,84,.25);

  /* type */
  --sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Inter, Roboto, sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  --h1-hero: clamp(31px, 4.4vw, 48px);
  --h1: clamp(28px, 3.4vw, 40px);
  --h1-sm: clamp(24px, 2.6vw, 30px);
  --h2: clamp(21px, 1.9vw, 24px);
  --h3: 17px;
  --body: 15.5px;

  /* rail: every page sits on the same one */
  --rail: 1040px;
  --pad: 24px;

  /* legacy names kept as aliases so page CSS predating this sheet still works */
  --accent: var(--brand);
  --dim: var(--text-dim);
  --line: var(--border);
  --bg-panel: var(--surface-2);
  --bg-card: var(--surface);
}

@media (prefers-color-scheme: light) {
  :root {
    --bg: #FAFAF9;
    --surface: #FFFFFF;
    --surface-2: #F5F5F3;
    --border: rgba(20,22,26,.09);
    --border-strong: rgba(20,22,26,.18);
    --text: #16181D;
    --text-dim: #555A63;
    --text-faint: #6B7078;
    --brand: #B05C00;
    --brand-ink: #FFFFFF;
    --brand-hover: #C96A02;
    --pass: #15803D;
    --fail: #DC2626;
    --glow: rgba(176,92,0,.07);
    --nav-bg: rgba(250,250,249,.92);
    --board-rim: rgba(20,22,26,.30);
    --select: rgba(176,92,0,.18);
  }
}

/* An instrument is a readout, not page furniture, so it keeps the dark palette in
   both themes. Every token it consumes is re-pinned here: the previous version
   re-pinned two of them and light mode leaked in through the rest, dropping the
   homepage verdict line to 3.74:1 while the ticks above it stayed at 10.76. */
.instrument {
  --bg: #0E0F11;
  --surface: #15171C;
  --surface-2: #101216;
  --border: rgba(255,255,255,.09);
  --border-strong: rgba(255,255,255,.16);
  --text: #E6EAEF;
  --text-dim: #8E97A3;
  --text-faint: #8E97A3;
  --brand: #FFB454;
  --accent: #FFB454;
  --pass: #4ADE80;
  --fail: #F87171;
  --line: rgba(255,255,255,.09);
  --bg-panel: #101216;
  --bg-card: #15171C;
  color: var(--text);
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 68px; }
body { background: var(--bg); color: var(--text); font-family: var(--sans);
  font-size: var(--body); line-height: 1.6; -webkit-font-smoothing: antialiased; }
::selection { background: var(--select); }
img { max-width: 100%; }
a:focus-visible, button:focus-visible, summary:focus-visible {
  outline: 2px solid var(--brand); outline-offset: 2px; border-radius: 4px; }

h1, h2, h3 { font-weight: 600; letter-spacing: -.02em; line-height: 1.15; }
h1 { font-size: var(--h1); }
h2 { font-size: var(--h2); }
h3 { font-size: var(--h3); }
p { text-wrap: pretty; }
.kicker { font-family: var(--mono); font-size: 11.5px; font-weight: 600;
  letter-spacing: .12em; text-transform: uppercase; color: var(--text-faint);
  margin-bottom: 14px; }

.btn { display: inline-flex; align-items: center; justify-content: center;
  min-height: 44px; padding: 9px 18px; border-radius: 8px;
  font-family: var(--sans); font-size: 14px; font-weight: 600; letter-spacing: -.01em;
  text-decoration: none; border: 1px solid transparent; cursor: pointer;
  transition: background-color .15s ease, border-color .15s ease, color .15s ease; }
.btn-primary { background: var(--brand); color: var(--brand-ink); }
.btn-primary:hover { background: var(--brand-hover); color: var(--brand-ink); }
.btn-ghost { background: none; border-color: var(--border-strong); color: var(--text); }
.btn-ghost:hover { border-color: var(--text-dim); background: rgba(127,127,127,.06); }
.btn-sm { min-height: 38px; padding: 7px 14px; font-size: 13.5px; }

/* The homepage replay and the /demo replay are the same artifact. They used to
   render at two densities, 29px pitch against 22px, with the denser one in
   larger type. One definition, both pages. */
.bench-log, .term-log { display: flex; flex-direction: column; gap: 8px;
  overflow: hidden; padding: 20px 18px;
  font-family: var(--mono); font-size: 13px; line-height: 1.6; }
.bench-log .bl, .term-log .ln { white-space: pre-wrap;
  padding-left: 9ch; text-indent: -9ch; color: var(--text-dim); }
@media (max-width: 560px) { .bench-log, .term-log { font-size: 11.5px; padding: 14px; } }
"""

CSS = """
/* ===== canonical site chrome (tools/header.py -- do not edit per page) =====
   Now built from the shared tokens above, so the two hand-maintained light-mode
   blocks this used to carry collapse into nothing. */
.site-nav { position: sticky; top: 0; z-index: 40; background: var(--nav-bg);
  -webkit-backdrop-filter: blur(14px) saturate(1.4); backdrop-filter: blur(14px) saturate(1.4);
  border-bottom: 1px solid var(--border-strong); }
.site-nav .nav-inner { max-width: var(--rail); margin: 0 auto; padding: 0 var(--pad);
  display: flex; align-items: center; justify-content: space-between; height: 56px; }
.site-nav .nav-logo { font-family: var(--mono);
  font-size: 16px; font-weight: 700; letter-spacing: -.01em; color: var(--text);
  text-decoration: none; padding: 13px 6px; margin: -13px -6px; margin-right: auto; }
.site-nav .nav-logo i { font-style: normal; color: var(--brand); }
.site-nav .nav-set { display: flex; gap: 4px; align-items: center; margin-left: 16px; flex: 0 0 auto; }
.site-nav .nav-set a:not(.nav-cta) { color: var(--text-dim); text-decoration: none;
  display: inline-flex; align-items: center; min-height: 44px; font-family: var(--sans);
  font-size: 14px; font-weight: 500; white-space: nowrap; padding: 0 12px; border-radius: 8px; }
.site-nav .nav-set a:not(.nav-cta):hover { color: var(--text); background: rgba(127,127,127,.09); }
.site-nav .nav-cta { display: inline-flex; align-items: center; justify-content: center;
  min-height: 44px; margin-left: 10px; padding: 9px 16px; border-radius: 8px;
  border: 1px solid transparent; background: var(--brand); color: var(--brand-ink);
  text-decoration: none; font-family: var(--sans);
  font-size: 14px; font-weight: 600; letter-spacing: -.01em; white-space: nowrap; flex-shrink: 0; }
.site-nav .nav-cta:hover { background: var(--brand-hover); color: var(--brand-ink); }
.site-nav .nav-set a[aria-current="page"] { color: var(--text); font-weight: 700; }
.site-menu a[aria-current="page"] { font-weight: 700; }
.site-nav a:focus-visible { outline: 2px solid var(--brand); outline-offset: 2px; }
.site-nav .nav-burger { display: none; background: none; border: 1px solid var(--border-strong);
  border-radius: 8px; width: 44px; height: 44px; cursor: pointer; padding: 0;
  align-items: center; justify-content: center; margin-right: 14px; flex: 0 0 auto; }
.site-nav .nav-burger span { display: block; width: 16px; height: 1.5px; background: var(--text);
  position: relative; transition: background .15s ease; }
.site-nav .nav-burger span::before, .site-nav .nav-burger span::after {
  content: ""; position: absolute; left: 0; width: 16px; height: 1.5px; background: var(--text);
  transition: transform .18s ease, top .18s ease; }
.site-nav .nav-burger span::before { top: -5px; }
.site-nav .nav-burger span::after { top: 5px; }
.site-nav .nav-burger[aria-expanded="true"] span { background: transparent; }
.site-nav .nav-burger[aria-expanded="true"] span::before { top: 0; transform: rotate(45deg); }
.site-nav .nav-burger[aria-expanded="true"] span::after { top: 0; transform: rotate(-45deg); }
.site-menu { display: none; border-bottom: 1px solid var(--border-strong); background: var(--surface);
  box-shadow: 0 14px 28px rgba(0,0,0,.45); }
.site-menu.open { display: block; }
.site-menu a { display: block; padding: 14px var(--pad); color: var(--text); text-decoration: none;
  font-family: var(--sans); font-size: 16px; border-top: 1px solid var(--border); }
.site-menu a:first-child { border-top: 0; }
@media (max-width: 800px) {
  .site-nav { position: fixed; top: 0; left: 0; right: 0;
    -webkit-backdrop-filter: none; backdrop-filter: none; background: var(--bg); }
  body { padding-top: 56px; }
  .site-nav .nav-set a:not(.nav-cta) { display: none; }
  .site-nav .nav-burger { display: flex; }
  .site-menu { position: fixed; top: 56px; left: 0; right: 0; z-index: 39;
    max-height: calc(100vh - 56px); overflow-y: auto; }
}
@media (min-width: 801px) { .site-menu { display: none !important; } }
/* burger + logo + CTA do not fit a 320px viewport at the default metrics */
@media (max-width: 400px) {
  .site-nav .nav-inner { padding: 0 16px; }
  .site-nav .nav-burger { margin-right: 10px; }
  .site-nav .nav-cta { margin-left: 8px; padding: 9px 12px; font-size: 13px; }
}
.site-foot { border-top: 1px solid var(--border); margin-top: 64px; padding: 40px 0 48px; }
.site-foot .foot-inner { max-width: var(--rail); margin: 0 auto; padding: 0 var(--pad); }
.site-foot .foot-sr { position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap; }
.site-foot .foot-map { display: grid; grid-template-columns: repeat(4, 1fr); gap: 28px; }
.site-foot h3 { font-family: var(--mono); font-size: 11.5px; letter-spacing: .1em;
  text-transform: uppercase; color: var(--text-faint); font-weight: 600; margin-bottom: 10px; }
.site-foot a { display: block; color: var(--text-dim); text-decoration: none; font-size: 14px;
  line-height: 1.5; padding: 11px 0; min-height: 44px; font-family: var(--sans); }
.site-foot a:hover { color: var(--text); }
.site-foot .foot-base { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;
  margin-top: 34px; padding-top: 18px; border-top: 1px solid var(--border);
  font-family: var(--mono); font-size: 12.5px; color: var(--text-faint); }
.site-foot .foot-base a { display: inline-block; padding: 11px 0; margin: -11px 0; min-height: 44px;
  color: inherit; font-family: inherit; font-size: inherit; }
@media (max-width: 700px) { .site-foot .foot-map { grid-template-columns: 1fr 1fr; gap: 20px; } }
@media (prefers-color-scheme: light) {
  .site-menu { box-shadow: 0 14px 28px rgba(20,22,26,.12); }
}
/* ===== end canonical site chrome ===== */
"""

CTA = ('<a class="nav-cta" href="mailto:pooyamn@gmail.com'
       '?subject=Oracova%3A%2015%20minutes">Book 15 minutes</a>')

# page -> its link set (self-link always omitted)
# One nav for every page. The current page is marked, never removed.
NAV = [('/', 'Home'), ('/product', 'Augur One'), ('/onboarding', 'Board bring-up'),
       ('/demo', 'Demo')]

# page -> the href that represents it, so we can mark "you are here"
SELF = {
    'index.html':      '/',
    'product.html':    '/product',
    'onboarding.html': '/onboarding',
    'demo.html':       '/demo',
    # The 404 carries the chrome too: it is the one page a lost visitor is guaranteed to
    # hit, and it used to be the only page with no way to navigate anywhere.
    '404.html':        None,
}
LINKS = SELF   # apply()/check iterate over the page list

MENU = [('/', 'Home'), ('/product', 'Augur One'), ('/onboarding', 'Board bring-up'),
        ('/demo', 'Demo')]

SITEMAP = [
    ('Product',  [('/product', 'Augur One'), ('/onboarding', 'Board bring-up')]),
    ('Evidence', [('/demo', 'Watch a run'), ('/#evidence', 'What it caught')]),
    ('How it works', [('/#how', 'The loop'), ('/#world', 'What it emulates'),
                      ('/#compare', 'Against other methods')]),
    ('Contact',  [('mailto:pooyamn@gmail.com?subject=Oracova%3A%2015%20minutes', 'Book 15 minutes'),
                  ('mailto:pooyamn@gmail.com', 'Email us')]),
]

def markup(page):
    here = SELF[page]
    def mark(u):
        return ' aria-current="page"' if u == here else ''
    links = '\n'.join('      <a href="%s"%s>%s</a>' % (u, mark(u), t) for u, t in NAV)
    menu = '\n'.join('    <a href="%s"%s>%s</a>' % (u, mark(u), t) for u, t in MENU)
    # Without JS the burger is inert and the inline links are hidden below 800px,
    # which leaves the whole site navigable only from the footer sitemap. Kept inside
    # <nav> so apply()'s NAV_RE still replaces it cleanly on re-run.
    return ('<nav class="site-nav">\n'
            '  <noscript><style>@media (max-width: 800px) {'
            ' .site-nav .nav-burger { display: none !important; }'
            ' .site-menu { display: block !important; position: static; max-height: none; }'
            ' }</style></noscript>\n'
            '  <div class="nav-inner">\n'
            '    <button class="nav-burger" id="nav-burger" type="button"'
            ' aria-label="Menu" aria-expanded="false" aria-controls="site-menu">'
            '<span></span></button>\n'
            '    <a class="nav-logo" href="/">oracova<i>_</i></a>\n'
            '    <div class="nav-set">\n%s\n      %s\n'
            '    </div>\n  </div>\n</nav>\n'
            '<div class="site-menu" id="site-menu">\n%s\n</div>' % (links, CTA, menu))

def footer_markup():
    cols = []
    for title, items in SITEMAP:
        rows = '\n'.join('        <a href="%s">%s</a>' % (u, t) for u, t in items)
        cols.append('      <div>\n        <h3>%s</h3>\n%s\n      </div>' % (title, rows))
    return ('<footer class="site-foot">\n  <div class="foot-inner">\n'
            # NOT <nav>: every page carries a bare `nav { position: sticky; top: 0 }`
            # rule for its own header, which would pin the footer map to the top.
            # The per-column <h2> headings already give the groups structure.
            '    <h2 class="foot-sr">Site map</h2>\n'
            '    <div class="foot-map">\n%s\n    </div>\n'
            '    <div class="foot-base">\n'
            '      <span>oracova_ &nbsp; AI agents test your firmware on real hardware.</span>\n'
            '      <span><a href="mailto:pooyamn@gmail.com">pooyamn@gmail.com</a>'
            ' &nbsp;&middot;&nbsp; &copy; 2026 Oracova</span>\n'
            '    </div>\n  </div>\n</footer>' % '\n'.join(cols))

SCRIPT = """<script>
(function () {
  var b = document.getElementById('nav-burger'), m = document.getElementById('site-menu');
  if (!b || !m) return;
  function set(open) { b.setAttribute('aria-expanded', String(open)); m.classList.toggle('open', open);
    // the panel floats over the page; without this a thumb flick scrolls content behind it
    document.body.style.overflow = open && window.innerWidth <= 800 ? 'hidden' : ''; }
  b.addEventListener('click', function () { set(b.getAttribute('aria-expanded') !== 'true'); });
  m.addEventListener('click', function (e) { if (e.target.tagName === 'A') set(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') set(false); });
  // tapping the page behind the open panel closes it, like every native menu
  document.addEventListener('pointerdown', function (e) {
    if (b.getAttribute('aria-expanded') === 'true'
        && !e.target.closest('.site-nav') && !e.target.closest('.site-menu')) {
      e.preventDefault(); set(false);
    }
  }, true);
  window.addEventListener('resize', function () { if (window.innerWidth > 800) set(false); });
})();
</script>"""

def page_css(text):
    i = text.find('<style>')
    return text[i + 7: text.find('</style>', i)] if i >= 0 else ''


def lint(path):
    """Two checks, both earned the hard way.

    balance  a strip that removes the first line of a two-line rule leaves an
             orphan '}' that closes the enclosing @media early and silently
             corrupts every rule after it.
    shadowed a selector declared inside any @media block and then redeclared
             unconditionally LATER wins at every width, so the mobile intent
             never ships. Found three times in one review round.
    """
    css = page_css(pathlib.Path(path).read_text())
    out = []
    depth = 0
    for ch in css:
        depth += (ch == '{') - (ch == '}')
        if depth < 0:
            break
    if depth != 0:
        out.append('unbalanced braces (%+d)' % depth)

    # selectors declared inside a max-width block, in source order
    guarded, pos = {}, 0
    for m in re.finditer(r'@media[^{]*\{', css):
        start = m.end()
        d, i = 1, start
        while i < len(css) and d:
            d += (css[i] == '{') - (css[i] == '}')
            i += 1
        for sm in re.finditer(r'(?m)^\s*([.#a-zA-Z][^{}@\n]*?)\s*\{', css[start:i - 1]):
            guarded.setdefault(sm.group(1).strip(), i)
    # the same selector, later, with no media guard around it
    for m in re.finditer(r'(?m)^  ([.#a-zA-Z][^{}@\n]*?)\s*\{', css):
        sel = m.group(1).strip()
        if sel in guarded and m.start() > guarded[sel]:
            out.append('"%s" is set inside a @media block and redeclared unguarded later' % sel)
    return out


NAV_RE = re.compile(r'<nav[^>]*>.*?</nav>', re.S)
LINK = '<link rel="stylesheet" href="/site.css">'
SHEET = TOKENS + CSS


def write_sheet(root):
    """The shared stylesheet is generated, never hand-edited: one place owns the
    palette, the type scale, the button, the instrument and the chrome."""
    f = pathlib.Path(root) / 'site.css'
    if not f.exists() or f.read_text() != SHEET:
        f.write_text(SHEET)
        return True
    return False


def apply(path, page):
    s = pathlib.Path(path).read_text()
    # 1. the chrome CSS now lives in site.css; strip any block a previous run inlined
    s = re.sub(r'\n/\* ===== canonical site (header|chrome).*?end canonical site (header|chrome) ===== \*/\n',
               '\n', s, flags=re.S)
    # 2. exactly one link to the shared sheet, before the page's own <style> so the
    #    page can extend it and the cascade order is never in doubt
    s = s.replace(LINK + '\n', '')
    if '<style>' not in s:
        raise SystemExit('no <style> found in ' + path)
    s = s.replace('<style>', LINK + '\n<style>', 1)
    # 3. one canonical markup
    if not NAV_RE.search(s):
        raise SystemExit('no <nav> found in ' + path)
    # drop any menu blocks a previous run left behind, else they accumulate
    s = re.sub(r'<div class="site-menu"[^>]*>.*?</div>\n?', '', s, flags=re.S)
    s = NAV_RE.sub(lambda m: markup(page), s, count=1)
    s = re.sub(r'<footer[^>]*>.*?</footer>', lambda m: footer_markup(), s, count=1, flags=re.S)
    s = re.sub(r'<script>\n\(function \(\) \{\n  var b = document\.getElementById\(.nav-burger.\).*?</script>\n',
               '', s, flags=re.S)
    s = s.replace('</body>', SCRIPT + '\n</body>', 1)
    pathlib.Path(path).write_text(s)
    return hashlib.sha256((SHEET + markup(page)).encode()).hexdigest()[:12]


def header_of(path):
    s = pathlib.Path(path).read_text()
    nav = NAV_RE.search(s)
    if not nav or LINK not in s:
        return None
    if re.search(r'canonical site (header|chrome)', s):      # inlined chrome came back
        return None
    sheet = pathlib.Path(path).parent / 'site.css'
    if not sheet.exists() or sheet.read_text() != SHEET:
        return None
    # compare markup minus the link set (which is intentionally per-page)
    skeleton = re.sub(r' aria-current="page"', '', nav.group(0))   # only the marker varies
    skeleton = re.sub(r'\s+', ' ', skeleton).strip()
    return hashlib.sha256((SHEET + skeleton).encode()).hexdigest()[:12]


if __name__ == '__main__':
    roots = ['.', 'v19']   # v19 promoted to production 2026-08-03; both stay in sync
    if '--check' not in sys.argv:
        for r in roots:
            if write_sheet(r):
                print('wrote', r + '/site.css')
    pages = list(LINKS)
    if '--check' in sys.argv:
        seen = {}
        for r in roots:
            for p in pages:
                f = pathlib.Path(r) / p
                if f.exists():
                    seen.setdefault(header_of(f), []).append(str(f))
        for h, files in seen.items():
            print(h, len(files), 'files')
        bad = 0
        for r in roots:
            for p in pages:
                f = pathlib.Path(r) / p
                if f.exists():
                    for msg in lint(f):
                        print('LINT %s: %s' % (f, msg)); bad += 1
        ok = len(seen) == 1 and None not in seen
        print('CONSISTENT' if ok and not bad else 'DRIFT DETECTED' if not ok else 'LINT FAILURES: %d' % bad)
    else:
        for r in roots:
            for p in pages:
                f = pathlib.Path(r) / p
                if f.exists():
                    print('applied', apply(f, p), f)
