#!/usr/bin/env python3
"""
Show Me Turkiye - canonical footer sync / check
================================================
One footer for every page. The single source of truth is:

    assets/footer.html   markup ({{ROOT}} = "" for root pages, "../" one level down)
    assets/footer.css    styles (embedded inline as <style id="smt-footer-css">)

    python build-footer.py           sync every page to the canonical footer
    python build-footer.py --check   report only; exit 1 if any page drifts

Sync replaces each page's site footer (the last <footer> in the page) with the
canonical markup, embeds the canonical CSS before </head>, and deletes legacy
footer-only CSS rules (.footer, .footer-*, bare footer) from the page's other
inline <style> blocks and from deferred.css, so no competing footer styles
remain. Pages listed in assets/footer-exceptions.txt are skipped on purpose.
"""

import re, sys
from pathlib import Path

TEMPLATE = Path("assets/footer.html")
CSS_FILE = Path("assets/footer.css")
EXCEPTIONS = Path("assets/footer-exceptions.txt")
LOGO = "https://img.showmeturkiye.com/hero/logo-v2.png"
STYLE_ID = "smt-footer-css"
LEGACY_CSS_FILES = [Path("deferred.css")]
KEEP_STYLE_IDS = {STYLE_ID}

FOOTER_SEL = re.compile(r"(^|[\s,>+~(])\.footer(-[\w-]+)?\b|^footer\b")

def pages():
    found = list(Path(".").glob("*.html")) + list(Path(".").glob("*/*.html"))
    return sorted(p for p in found if p.parts[0] != "assets")

def root_of(p):
    return "../" * (len(p.parts) - 1)

def canonical_markup(p):
    return TEMPLATE.read_text(encoding="utf-8").strip().replace("{{ROOT}}", root_of(p))

def canonical_style():
    return f'<style id="{STYLE_ID}">\n' + CSS_FILE.read_text(encoding="utf-8").strip() + "\n</style>"

def exceptions():
    if not EXCEPTIONS.exists(): return set()
    return {l.split("#")[0].strip() for l in EXCEPTIONS.read_text(encoding="utf-8").splitlines() if l.split("#")[0].strip()}

# --- minimal CSS rule scanner (top level + one level of @media/@supports) ---
def css_rules(css):
    out = []
    def skip(i, end):
        while i < end:
            if css[i].isspace(): i += 1
            elif css.startswith("/*", i):
                j = css.find("*/", i + 2); i = end if j < 0 else j + 2
            else: break
        return i
    def block_end(b, end):
        depth, j = 1, b + 1
        while j < end and depth:
            if css.startswith("/*", j):
                k = css.find("*/", j + 2); j = end if k < 0 else k + 2; continue
            if css[j] == "{": depth += 1
            elif css[j] == "}": depth -= 1
            j += 1
        return j
    def walk(i, end, media):
        while True:
            i = skip(i, end)
            if i >= end: return
            b = css.find("{", i)
            if b < 0 or b >= end: return
            sel = css[i:b].strip()
            if sel.startswith("@"):
                j = block_end(b, end)
                if sel.startswith(("@media", "@supports")): walk(b + 1, j - 1, (sel, i, j))
                i = j; continue
            e = css.find("}", b)
            out.append({"sel": sel, "start": i, "end": e + 1, "media": media})
            i = e + 1
    walk(0, len(css), None)
    return out

def _is_footer_sel(s):
    return bool(FOOTER_SEL.search(" " + s) or FOOTER_SEL.search(s))

def _allowed_mixed(s):
    # text-selection colour only; never affects footer layout
    return "::selection" in s or "::-moz-selection" in s

def is_footer_rule(sel):
    parts = [s.strip() for s in sel.split(",") if s.strip()]
    return bool(parts) and all(_is_footer_sel(s) for s in parts)

def mixed_footer_parts(sel):
    """Footer selectors bundled into a rule that also styles other elements."""
    parts = [s.strip() for s in sel.split(",") if s.strip()]
    if all(_is_footer_sel(s) for s in parts): return []
    return [s for s in parts if _is_footer_sel(s) and not _allowed_mixed(s)]

def strip_footer_css(css):
    """Remove footer-only rules; drop @media blocks left empty."""
    rules = [r for r in css_rules(css) if is_footer_rule(r["sel"])]
    for r in sorted(rules, key=lambda r: r["start"], reverse=True):
        css = css[:r["start"]] + css[r["end"]:]
    # drop footer selectors from mixed selector lists, keep the rest of the rule
    for r in sorted(css_rules(css), key=lambda r: r["start"], reverse=True):
        drop = mixed_footer_parts(r["sel"])
        if not drop: continue
        b = css.find("{", r["start"])
        keep = [s.strip() for s in css[r["start"]:b].split(",") if s.strip() and s.strip() not in drop]
        css = css[:r["start"]] + ", ".join(keep) + " " + css[b:]
        rules.append(r)
    # remove now-empty @media/@supports blocks
    css = re.sub(r"@(media|supports)[^{]*\{\s*\}", "", css)
    return css, len(rules)

def legacy_rules_in(css):
    return [r["sel"] for r in css_rules(css) if is_footer_rule(r["sel"]) or mixed_footer_parts(r["sel"])]

STYLE_RE = re.compile(r'(<style\b[^>]*>)(.*?)(</style>)', re.S)

def style_id(open_tag):
    m = re.search(r'id="([^"]+)"', open_tag); return m.group(1) if m else ""

def head_end(h):
    """Index of the real </head> (the last one before <body>); comments inside
    <style> blocks can contain the literal text "</head>"."""
    b = h.find("<body")
    return h.rfind("</head>", 0, b if b >= 0 else len(h))

def site_footer_span(h):
    """(start, end) of the site footer = last <footer> in the page body."""
    ms = list(re.finditer(r"<footer\b.*?</footer>", h, re.S))
    return (ms[-1].start(), ms[-1].end()) if ms else None

# --- sync ---------------------------------------------------------------------
def sync_page(p):
    h = p.read_text(encoding="utf-8"); orig = h; removed = 0
    span = site_footer_span(h)
    if span: h = h[:span[0]] + canonical_markup(p) + h[span[1]:]
    def clean(m):
        nonlocal removed
        if style_id(m.group(1)) in KEEP_STYLE_IDS: return m.group(0)
        css, n = strip_footer_css(m.group(2)); removed += n
        return m.group(1) + css + m.group(3)
    h = STYLE_RE.sub(clean, h)
    block = canonical_style()
    if f'id="{STYLE_ID}"' in h:
        h = re.sub(r'<style id="%s">.*?</style>' % STYLE_ID, lambda m: block, h, count=1, flags=re.S)
    else:
        i = head_end(h)
        if i >= 0: h = h[:i] + block + "\n" + h[i:]
    if h != orig: p.write_text(h, encoding="utf-8")
    return h != orig, removed, bool(span)

def sync():
    skip = exceptions(); changed = []; total_removed = 0
    for p in pages():
        if str(p) in skip: print(f"  - exception (skipped): {p}"); continue
        ch, n, had = sync_page(p); total_removed += n
        if not had: print(f"  ! no <footer> found: {p}")
        if ch: changed.append(str(p))
    for f in LEGACY_CSS_FILES:
        if f.exists():
            css = f.read_text(encoding="utf-8"); new, n = strip_footer_css(css)
            if n: f.write_text(new, encoding="utf-8"); total_removed += n; changed.append(str(f))
    print(f"  OK  footer synced; {len(changed)} files updated, {total_removed} legacy footer CSS rules removed")

# --- check --------------------------------------------------------------------
REQUIRED_LINKS = [("explore", "Cities"), ("routes", "Routes"), ("blog", "Journal"), ("projects", "Films"),
                  ("about", "About us"), ("contact", "Contact"), ("press", "Press"),
                  ("privacy", "Privacy"), ("terms", "Terms"), ("cookies", "Cookies")]

def check_page(p):
    h = p.read_text(encoding="utf-8"); problems = []
    span = site_footer_span(h)
    if not span: return ["no <footer>"]
    ft = h[span[0]:span[1]]
    if ft.strip() != canonical_markup(p): problems.append("footer markup differs from assets/footer.html")
    if LOGO not in ft or "footer-logo" not in ft: problems.append("wrong or missing logo")
    root = root_of(p)
    for slug, label in REQUIRED_LINKS:
        if not re.search(r'href="%s"[^>]*>\s*%s\s*<' % (re.escape(root + slug), re.escape(label)), ft):
            problems.append(f"missing link {label} -> {root + slug}")
    heads = re.findall(r"<h3>([^<]+)</h3>", ft)
    if heads != ["Explore", "About", "Legal"]: problems.append(f"headings {heads}")
    if ft.count('class="footer-section"') != 4: problems.append("column structure (expected 4 footer-section)")
    blocks = re.findall(r'<style id="%s">(.*?)</style>' % STYLE_ID, h, re.S)
    if len(blocks) != 1 or blocks[0].strip() != CSS_FILE.read_text(encoding="utf-8").strip():
        problems.append("canonical footer CSS missing or edited")
    else:
        head = h[:head_end(h)]
        starts = [m.start() for m in STYLE_RE.finditer(head)]
        if not starts or 'id="%s"' % STYLE_ID not in head[starts[-1]:starts[-1] + 40]:
            problems.append("canonical footer CSS is not the last <style> in <head> (could be overridden)")
    legacy = []
    for m in STYLE_RE.finditer(h):
        if style_id(m.group(1)) in KEEP_STYLE_IDS: continue
        legacy += legacy_rules_in(m.group(2))
    if legacy: problems.append(f"{len(legacy)} legacy/override footer CSS rules (e.g. {legacy[0]})")
    if not re.search(r"Poppins[^\"']*500", h): problems.append("Poppins 500 not loaded")
    return problems

def check():
    skip = exceptions(); blocked = 0
    print(f"{'PAGE':42} FOOTER")
    for p in pages():
        if str(p) in skip: print(f"{str(p):42} EXCEPTION (approved)"); continue
        probs = check_page(p)
        print(f"{str(p):42} {'PASS' if not probs else 'BLOCKED: ' + '; '.join(probs)}")
        blocked += bool(probs)
    for f in LEGACY_CSS_FILES:
        if f.exists():
            lr = legacy_rules_in(f.read_text(encoding="utf-8"))
            if lr: print(f"{str(f):42} BLOCKED: {len(lr)} legacy footer CSS rules"); blocked += 1
    print(f"\nFOOTER CONSISTENCY: {'PASS' if not blocked else 'BLOCKED'}")
    return 0 if not blocked else 1

if __name__ == "__main__":
    if "--check" in sys.argv: sys.exit(check())
    print("Syncing canonical footer ..."); sync()
