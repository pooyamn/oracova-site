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
  text-decoration: none; padding: 12px 0; margin: -12px 0; }
.site-nav .nav-logo i { font-style: normal; color: #FFB454; }
.site-nav .nav-set { display: flex; gap: 4px; align-items: center; margin-left: 16px; }
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
.site-nav a:focus-visible { outline: 2px solid #FFB454; outline-offset: 2px; }
@media (max-width: 800px) {
  .site-nav { position: fixed; top: 0; left: 0; right: 0;
    -webkit-backdrop-filter: none; backdrop-filter: none; background: #0E0F11; }
  body { padding-top: 56px; }
  .site-nav .nav-set a:not(.nav-cta) { display: none; }
}
@media (prefers-color-scheme: light) {
  .site-nav { background: rgba(250,250,249,.92); border-bottom-color: rgba(20,22,26,.1); }
  .site-nav .nav-logo { color: #16181D; }
  .site-nav .nav-logo i { color: #B05C00; }
  .site-nav .nav-set a:not(.nav-cta) { color: #555A63; }
  .site-nav .nav-set a:not(.nav-cta):hover { color: #16181D; background: rgba(20,22,26,.05); }
  .site-nav .nav-cta { background: #B05C00; color: #fff; }
  .site-nav .nav-cta:hover { background: #C96A02; color: #fff; }
  @media (max-width: 800px) { .site-nav { background: #FAFAF9; } }
}
/* ===== end canonical site header ===== */
"""

CTA = ('<a class="nav-cta" href="mailto:pooyamn@gmail.com'
       '?subject=Oracova%20%E2%80%94%2015%20minutes">Book 15 minutes</a>')

# page -> its link set (self-link always omitted)
LINKS = {
    'index.html':                    [('/product', 'Product'), ('/demo', 'Demo'), ('#evidence', 'Evidence'), ('/onboarding', 'Board bring-up')],
    'product.html':                  [('/', 'Home'), ('/demo', 'Demo'), ('/onboarding', 'Board bring-up')],
    'onboarding.html':               [('/', 'Home'), ('/product', 'Product'), ('/demo', 'Demo')],
    'demo.html':                     [('/', 'Home'), ('/product', 'Product'), ('/onboarding', 'Board bring-up')],
    'runs/bldc-hall-fault-demo.html':[('/', 'Home'), ('/product', 'Product'), ('/demo', 'Demo')],
}

def markup(page):
    links = '\n'.join('      <a href="%s">%s</a>' % (u, t) for u, t in LINKS[page])
    return ('<nav class="site-nav">\n  <div class="nav-inner">\n'
            '    <a class="nav-logo" href="/">oracova<i>_</i></a>\n'
            '    <div class="nav-set">\n%s\n      %s\n    </div>\n'
            '  </div>\n</nav>' % (links, CTA))

NAV_RE = re.compile(r'<nav[^>]*>.*?</nav>', re.S)

def apply(path, page):
    s = pathlib.Path(path).read_text()
    # 1. one canonical CSS block, always last in the stylesheet so it wins
    s = re.sub(r'\n/\* ===== canonical site header.*?end canonical site header ===== \*/\n', '\n', s, flags=re.S)
    s = s.replace('</style>', CSS + '</style>', 1)
    # 2. one canonical markup
    if not NAV_RE.search(s):
        raise SystemExit('no <nav> found in ' + path)
    s = NAV_RE.sub(lambda m: markup(page), s, count=1)
    pathlib.Path(path).write_text(s)
    return hashlib.sha256((CSS + markup(page)).encode()).hexdigest()[:12]

def header_of(path):
    s = pathlib.Path(path).read_text()
    css = re.search(r'/\* ===== canonical site header.*?end canonical site header ===== \*/', s, re.S)
    nav = NAV_RE.search(s)
    if not css or not nav:
        return None
    # compare CSS exactly; markup minus the link set (which is intentionally per-page)
    skeleton = re.sub(r'<a href="[^"]*">[^<]*</a>', '', nav.group(0))
    skeleton = re.sub(r'\s+', ' ', skeleton).strip()   # link count is per-page by design
    return hashlib.sha256((css.group(0) + skeleton).encode()).hexdigest()[:12]

if __name__ == '__main__':
    roots = ['v19']   # staging only; add '.'/'v18' deliberately when promoting
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
