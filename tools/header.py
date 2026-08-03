#!/usr/bin/env python3
"""Single source of truth for the site header.

Run:  python3 tools/header.py            # apply to root + v18
      python3 tools/header.py --check    # verify all pages carry identical header

Every page gets the SAME markup and the SAME self-contained CSS. The block uses its
own hardcoded values (not page tokens) so it renders identically no matter which
stylesheet lineage a page came from.
"""
import re, sys, hashlib, pathlib

CSS = """
/* ===== canonical site header (tools/header.py — do not edit per page) ===== */
.site-nav { position: sticky; top: 0; z-index: 40;
  background: rgba(14,15,17,.9);
  -webkit-backdrop-filter: blur(14px) saturate(1.4); backdrop-filter: blur(14px) saturate(1.4);
  border-bottom: 1px solid rgba(255,255,255,.09); }
.site-nav .nav-inner { max-width: 1040px; margin: 0 auto; padding: 0 24px;
  display: flex; align-items: center; justify-content: space-between; height: 56px; }
.site-nav .nav-logo { font-family: ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  font-size: 16px; font-weight: 700; letter-spacing: -.01em; color: #EDEEF0;
  text-decoration: none; padding: 13px 6px; margin: -13px -6px; margin-right: auto; }
.site-nav .nav-logo i { font-style: normal; color: #FFB454; }
.site-nav .nav-set { display: flex; gap: 4px; align-items: center; margin-left: 16px; flex: 0 0 auto; }
.site-nav .nav-set a:not(.nav-cta) { color: #9DA1A8; text-decoration: none;
  font-family: -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Inter,Roboto,sans-serif;
  font-size: 14px; font-weight: 500; white-space: nowrap; padding: 8px 12px; border-radius: 8px; }
.site-nav .nav-set a:not(.nav-cta):hover { color: #EDEEF0; background: rgba(255,255,255,.05); }
.site-nav .nav-cta { display: inline-flex; align-items: center; justify-content: center;
  margin-left: 10px; padding: 9px 16px; border-radius: 8px; border: 1px solid transparent;
  background: #FFB454; color: #1A1204; text-decoration: none;
  font-family: -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Inter,Roboto,sans-serif;
  font-size: 14px; font-weight: 600; letter-spacing: -.01em; white-space: nowrap; flex-shrink: 0; }
.site-nav .nav-cta:hover { background: #FFC276; color: #1A1204; }
.site-nav .nav-set a[aria-current="page"] { color: #EDEEF0; font-weight: 700; }
.site-menu a[aria-current="page"] { font-weight: 700; }
.site-nav a:focus-visible { outline: 2px solid #FFB454; outline-offset: 2px; }
.site-nav .nav-burger { display: none; background: none; border: 1px solid rgba(255,255,255,.14);
  border-radius: 8px; width: 44px; height: 44px; cursor: pointer; padding: 0;
  align-items: center; justify-content: center; margin-right: 14px; flex: 0 0 auto; }
.site-nav .nav-burger span { display: block; width: 16px; height: 1.5px; background: #EDEEF0;
  position: relative; transition: background .15s ease; }
.site-nav .nav-burger span::before, .site-nav .nav-burger span::after {
  content: ""; position: absolute; left: 0; width: 16px; height: 1.5px; background: #EDEEF0;
  transition: transform .18s ease, top .18s ease; }
.site-nav .nav-burger span::before { top: -5px; }
.site-nav .nav-burger span::after { top: 5px; }
.site-nav .nav-burger[aria-expanded="true"] span { background: transparent; }
.site-nav .nav-burger[aria-expanded="true"] span::before { top: 0; transform: rotate(45deg); }
.site-nav .nav-burger[aria-expanded="true"] span::after { top: 0; transform: rotate(-45deg); }
.site-menu { display: none; border-bottom: 1px solid rgba(255,255,255,.09); background: #0E0F11; }
.site-menu.open { display: block; }
.site-menu a { display: block; padding: 14px 24px; color: #EDEEF0; text-decoration: none;
  font-family: -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Inter,Roboto,sans-serif;
  font-size: 16px; border-top: 1px solid rgba(255,255,255,.06); }
.site-menu a:first-child { border-top: 0; }
@media (max-width: 800px) {
  .site-nav { position: fixed; top: 0; left: 0; right: 0;
    -webkit-backdrop-filter: none; backdrop-filter: none; background: #0E0F11; }
  body { padding-top: 56px; }
  .site-nav .nav-set a:not(.nav-cta) { display: none; }
  .site-nav .nav-burger { display: flex; }
  .site-menu { position: fixed; top: 56px; left: 0; right: 0; z-index: 39;
    max-height: calc(100vh - 56px); overflow-y: auto; }
}
@media (min-width: 801px) { .site-menu { display: none !important; } }
.site-foot { border-top: 1px solid rgba(255,255,255,.09); margin-top: 64px; padding: 40px 0 48px; }
.site-foot .foot-inner { max-width: 1040px; margin: 0 auto; padding: 0 24px; }
.site-foot .foot-map { display: grid; grid-template-columns: repeat(4, 1fr); gap: 28px; }
.site-foot h4 { font-family: ui-monospace,"SF Mono",Menlo,monospace; font-size: 11.5px;
  letter-spacing: .1em; text-transform: uppercase; color: #6E7278; font-weight: 600; margin-bottom: 10px; }
.site-foot a { display: block; color: #9DA1A8; text-decoration: none; font-size: 14px; padding: 11px 0;
  font-family: -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Inter,Roboto,sans-serif; }
.site-foot a:hover { color: #EDEEF0; }
.site-foot .foot-base { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;
  margin-top: 34px; padding-top: 18px; border-top: 1px solid rgba(255,255,255,.06);
  font-family: ui-monospace,"SF Mono",Menlo,monospace; font-size: 12.5px; color: #6E7278; }
.site-foot .foot-base a { display: inline; color: inherit; font-family: inherit; font-size: inherit; }
@media (max-width: 700px) { .site-foot .foot-map { grid-template-columns: 1fr 1fr; gap: 20px; } }
@media (prefers-color-scheme: light) {
  .site-menu { background: #FAFAF9; }
  .site-menu a { color: #16181D; border-top-color: rgba(20,22,26,.08); }
  .site-nav .nav-burger { border-color: rgba(20,22,26,.18); }
  .site-nav .nav-burger span, .site-nav .nav-burger span::before, .site-nav .nav-burger span::after { background: #16181D; }
  .site-nav .nav-burger[aria-expanded="true"] span { background: transparent; }
  .site-foot { border-top-color: rgba(20,22,26,.1); }
  .site-foot h4 { color: #83888F; }
  .site-foot a { color: #555A63; }
  .site-foot a:hover { color: #16181D; }
  .site-foot .foot-base { color: #83888F; border-top-color: rgba(20,22,26,.08); }
}
@media (prefers-color-scheme: light) {
  .site-nav { background: rgba(250,250,249,.92); border-bottom-color: rgba(20,22,26,.1); }
  .site-nav .nav-logo { color: #16181D; }
  .site-nav .nav-logo i { color: #B05C00; }
  .site-nav .nav-set a:not(.nav-cta) { color: #555A63; }
  .site-nav .nav-set a[aria-current="page"] { color: #16181D; }
  .site-nav .nav-set a:not(.nav-cta):hover { color: #16181D; background: rgba(20,22,26,.05); }
  .site-nav .nav-cta { background: #B05C00; color: #fff; }
  .site-nav .nav-cta:hover { background: #C96A02; color: #fff; }
  @media (max-width: 800px) { .site-nav { background: #FAFAF9; } }
}
/* ===== end canonical site header ===== */
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
    ('Evidence', [('/demo', 'Live demo'), ('/#evidence', 'What it caught')]),
    ('How it works', [('/#how', 'The loop'), ('/#world', 'What it emulates'),
                      ('/#compare', 'Against other methods')]),
    ('Contact',  [('mailto:pooyamn@gmail.com?subject=Oracova%20Augur%20One', 'Request a quote'),
                  ('mailto:pooyamn@gmail.com', 'Email us')]),
]

def markup(page):
    here = SELF[page]
    def mark(u):
        return ' aria-current="page"' if u == here else ''
    links = '\n'.join('      <a href="%s"%s>%s</a>' % (u, mark(u), t) for u, t in NAV)
    menu = '\n'.join('    <a href="%s"%s>%s</a>' % (u, mark(u), t) for u, t in MENU)
    return ('<nav class="site-nav">\n  <div class="nav-inner">\n'
            '    <button class="nav-burger" id="nav-burger" type="button"'
            ' aria-label="Menu" aria-expanded="false" aria-controls="site-menu">'
            '<span></span></button>\n'
            '    <a class="nav-logo" href="/">oracova<i>_</i></a>\n'
            '    <div class="nav-set">\n%s\n'
            '    </div>\n  </div>\n</nav>\n'
            '<div class="site-menu" id="site-menu">\n%s\n</div>' % (links, menu))

def footer_markup():
    cols = []
    for title, items in SITEMAP:
        rows = '\n'.join('        <a href="%s">%s</a>' % (u, t) for u, t in items)
        cols.append('      <div>\n        <h4>%s</h4>\n%s\n      </div>' % (title, rows))
    return ('<footer class="site-foot">\n  <div class="foot-inner">\n'
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
  function set(open) { b.setAttribute('aria-expanded', String(open)); m.classList.toggle('open', open); }
  b.addEventListener('click', function () { set(b.getAttribute('aria-expanded') !== 'true'); });
  m.addEventListener('click', function (e) { if (e.target.tagName === 'A') set(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') set(false); });
  window.addEventListener('resize', function () { if (window.innerWidth > 800) set(false); });
})();
</script>"""

NAV_RE = re.compile(r'<nav[^>]*>.*?</nav>', re.S)

def apply(path, page):
    s = pathlib.Path(path).read_text()
    # 1. one canonical CSS block, always last in the stylesheet so it wins
    s = re.sub(r'\n/\* ===== canonical site header.*?end canonical site header ===== \*/\n', '\n', s, flags=re.S)
    s = s.replace('</style>', CSS + '</style>', 1)
    # 2. one canonical markup
    if not NAV_RE.search(s):
        raise SystemExit('no <nav> found in ' + path)
    # drop any menu blocks a previous run left behind, else they accumulate
    s = re.sub(r'<div class="site-menu"[^>]*>.*?</div>\n?', '', s, flags=re.S)
    s = NAV_RE.sub(lambda m: markup(page), s, count=1)
    s = re.sub(r'<footer[^>]*>.*?</footer>', lambda m: footer_markup(), s, count=1, flags=re.S)
    s = re.sub(r'<script>\n\(function \(\) \{\n  var b = document\.getElementById\(.nav-burger.\).*?</script>\n', '', s, flags=re.S)
    s = s.replace('</body>', SCRIPT + '\n</body>', 1)
    pathlib.Path(path).write_text(s)
    return hashlib.sha256((CSS + markup(page)).encode()).hexdigest()[:12]

def header_of(path):
    s = pathlib.Path(path).read_text()
    css = re.search(r'/\* ===== canonical site header.*?end canonical site header ===== \*/', s, re.S)
    nav = NAV_RE.search(s)
    if not css or not nav:
        return None
    # compare CSS exactly; markup minus the link set (which is intentionally per-page)
    skeleton = re.sub(r' aria-current="page"', '', nav.group(0))   # only the marker varies
    skeleton = re.sub(r'\s+', ' ', skeleton).strip()
    return hashlib.sha256((css.group(0) + skeleton).encode()).hexdigest()[:12]

if __name__ == '__main__':
    roots = ['.', 'v19']   # v19 promoted to production 2026-08-03; both stay in sync
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
        print('CONSISTENT' if len(seen) == 1 and None not in seen else 'DRIFT DETECTED')
    else:
        for r in roots:
            for p in pages:
                f = pathlib.Path(r) / p
                if f.exists():
                    print('applied', apply(f, p), f)
