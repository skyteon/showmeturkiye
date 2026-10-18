#!/usr/bin/env python3
"""
Show Me Türkiye - Journal page builder (Journal 2.0)

Same pattern as build-films.py: a build script in the repo root, data under data/journal/,
and a --check mode for the GitHub Action.

    python3 build-blog.py            render blog.html from data/journal/journal.json + blog/*.html
    python3 build-blog.py --check    report only; exit 1 if blog.html is out of date

Data (data/journal/journal.json, version controlled):
    masthead, cover, picks, regions, topics, keep_going   editorial curation (titles, kickers,
                                                          excerpts, images - all editorial text)
    articles                                              one record per Journal card, in display
                                                          order: slug, kicker, title, excerpt,
                                                          read, date, author, topic, region,
                                                          image, alt

Listing rules:
  * every blog/<slug>.html that is not a noindex draft is listed;
  * an article that is in the data file uses the data file's card text;
  * an article that is NOT in the data file yet is listed automatically, newest first, from
    the article's own <h1>, meta description, read time, eyebrow and datePublished (nothing is
    invented: fields the article does not state stay empty); a file with neither <h1> nor
    <title> is skipped with a warning;
  * data-file records whose article no longer exists are skipped with a warning;
  * story counts, region counts and "last updated" are computed, never typed.

The page: blog.html is both template and output. Generated regions sit between markers and
everything outside them (head SEO tags, CSS, JS, nav, footer, search, consent) is left as is:
    <!-- JOURNAL:BODY:START --> ... <!-- JOURNAL:BODY:END -->
    <script type="application/ld+json" id="smt-journal-ld">, <link id="smt-journal-preload">
"""
import argparse, glob, html, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://showmeturkiye.com"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
TOPIC_FALLBACK = [("city guide", "city"), ("planning", "planning"), ("outdoors", "outdoors"),
                  ("winter", "outdoors"), ("events", "events")]
REGION_FALLBACK = {"marmara": "marmara", "aegean": "aegean", "mediterranean": "mediterranean",
                   "central anatolia": "central-anatolia", "central taurus": "central-anatolia",
                   "black sea": "black-sea", "northeast": "black-sea", "eastern anatolia": "eastern-anatolia",
                   "far southeast": "eastern-anatolia", "southeast": "southeast"}


def esc(s):
    return html.escape(str(s), quote=True)


def read(path):
    return open(path, encoding="utf-8").read()


def text_of(fragment):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(fragment or ""))).strip()


def month_year(iso):
    m = re.match(r"^(\d{4})-(\d{2})", iso or "")
    return f"{MONTHS[int(m.group(2)) - 1]} {m.group(1)}" if m else ""


def find(h, *patterns):
    for p in patterns:
        m = re.search(p, h, re.S)
        if m:
            return html.unescape(m.group(1)).strip()
    return ""


def article_facts(path):
    """What the article itself states. Used for auto-listing and for the computed stats."""
    h = read(path)
    if re.search(r'<meta name="robots" content="[^"]*noindex', h):
        return None
    eyebrow = text_of(find(h, r'class="hero-eyebrow"[^>]*>(.*?)</(?:div|p|span)>'))
    read_m = re.search(r"(\d+)\s*min read", h)
    return {
        "title": text_of(find(h, r"<title>([^<]*)</title>")),
        "h1": text_of(find(h, r"<h1[^>]*>(.*?)</h1>")),
        "description": find(h, r'<meta name="description" content="([^"]*)"'),
        "og_image": find(h, r'<meta property="og:image" content="([^"]*)"'),
        "published": find(h, r'"datePublished"\s*:\s*"([^"]*)"'),
        "modified": find(h, r'"dateModified"\s*:\s*"([^"]*)"'),
        "read": f"{read_m.group(1)} min read" if read_m else "",
        "eyebrow": eyebrow,
    }


def auto_record(slug, f):
    topic = "destinations"
    region = "turkiye"
    low = f["eyebrow"].lower()
    for needle, key in TOPIC_FALLBACK:
        if needle in low:
            topic = key
            break
    for needle, key in REGION_FALLBACK.items():
        if needle in low:
            region = key
            break
    title = f["h1"] or re.split(r"\s*[|·]\s*Show Me", f["title"])[0].strip()
    return {"slug": slug, "kicker": f["eyebrow"].split("·")[0].strip() or "Journal", "title": title,
            "excerpt": f["description"], "read": f["read"], "date": month_year(f["published"]),
            "author": "", "topic": topic, "region": region, "image": f["og_image"], "alt": title,
            "_auto": True, "_sort": f["published"]}


REQUIRED = ("slug", "kicker", "title", "excerpt", "read", "date", "author", "topic", "region", "image", "alt")


def collect(data, site):
    files = {os.path.basename(p)[:-5]: p for p in glob.glob(os.path.join(site, "blog", "*.html"))}
    facts, warnings = {}, []
    for slug, p in files.items():
        f = article_facts(p)
        if f is None:
            continue
        if not f["h1"] and not f["title"]:
            warnings.append(f"skipped blog/{slug}.html: no <h1> or <title>, not listed")
            continue
        facts[slug] = f
    for i, a in enumerate(data["articles"]):
        missing = [k for k in REQUIRED if k not in a]
        if missing:
            sys.exit(f"data/journal/journal.json: articles[{i}] ({a.get('slug', '?')}) is missing {', '.join(missing)}")
    listed = []
    known = set()
    for a in data["articles"]:
        if a["slug"] not in facts:
            warnings.append(f"skipped {a['slug']}: no published blog/{a['slug']}.html")
            continue
        known.add(a["slug"])
        listed.append(dict(a))
    auto = [auto_record(s, facts[s]) for s in facts if s not in known]
    auto.sort(key=lambda r: r["_sort"], reverse=True)
    for r in auto:
        warnings.append(f"auto-listed {r['slug']} (not in data/journal/journal.json)")
    return auto + listed, facts, warnings


def meta_line(parts):
    parts = [p for p in parts if p]
    return '<span class="jr-dot" aria-hidden="true"></span>'.join(f"<span>{esc(p)}</span>" for p in parts)


def img(src, alt, w=None, h=None, lazy=True, priority=False):
    attrs = [f'src="{esc(src)}"', f'alt="{esc(alt)}"']
    if w and h:
        attrs += [f'width="{w}"', f'height="{h}"']
    if priority:
        attrs += ['fetchpriority="high"', 'decoding="async"']
    elif lazy:
        attrs += ['loading="lazy"', 'decoding="async"']
    return "<img " + " ".join(attrs) + ">"


def render_body(data, articles, facts):
    regions = {r["key"]: r for r in data["regions"]["items"]}
    region_counts = {}
    for a in articles:
        region_counts[a["region"]] = region_counts.get(a["region"], 0) + 1
    topic_counts = {}
    for a in articles:
        topic_counts[a["topic"]] = topic_counts.get(a["topic"], 0) + 1
    topics = [t for t in data["topics"] if topic_counts.get(t["key"])]
    extra_topics = sorted(k for k in topic_counts if k not in {t["key"] for t in data["topics"]})
    topics += [{"key": k, "label": k.replace("-", " ").title()} for k in extra_topics]
    region_items = [r for r in data["regions"]["items"] if region_counts.get(r["key"])]
    regions_with_stories = [k for k in region_counts if k != "turkiye" and k in regions]
    stamps = [f["modified"] or f["published"] for f in facts.values() if f["modified"] or f["published"]]
    last_updated = month_year(max(stamps)) if stamps else ""

    m = data["masthead"]
    c = data["cover"]
    out = []
    out.append(f'''<header class="jr-masthead">
  <div class="jr-masthead-inner">
    <p class="jr-eyebrow jr-eyebrow-box">{m["eyebrow"]}</p>
    <h1 class="jr-title">{m["title"]}</h1>
    <p class="jr-sub">{m["sub"]}</p>
    <dl class="jr-stats">
      <div><dt>Stories</dt><dd>{len(articles)}</dd></div>
      <div><dt>Regions</dt><dd>{len(regions_with_stories)}</dd></div>''' + (f'''
      <div><dt>Last updated</dt><dd>{esc(last_updated)}</dd></div>''' if last_updated else "") + '''
    </dl>
  </div>
</header>''')

    byline = meta_line([c["author"], c["read"], c["updated"]])
    out.append(f'''
<section class="jr-cover" aria-labelledby="coverTitle">
  <a class="jr-cover-link" href="blog/{esc(c["slug"])}">
    <div class="jr-cover-media">{img(c["image"], c["alt"], c.get("width"), c.get("height"), lazy=False, priority=True)}</div>
    <div class="jr-cover-scrim" aria-hidden="true"></div>
    <div class="jr-cover-body">
      <p class="jr-cover-eyebrow">{esc(c["eyebrow"])}</p>
      <h2 id="coverTitle" class="jr-cover-title">{c["title"]}</h2>
      <p class="jr-cover-excerpt">{c["excerpt"]}</p>
      <p class="jr-cover-byline">{byline}</p>
      <span class="jr-cover-cta">{esc(c["cta"])} <span class="arr" aria-hidden="true">→</span></span>
    </div>
  </a>
</section>''')

    p = data["picks"]
    picks = [x for x in p["items"] if x["slug"] != c["slug"]]
    if picks:
        items = []
        for i, x in enumerate(picks, 1):
            items.append(f'''    <li class="jr-pick">
      <a href="blog/{esc(x["slug"])}" class="jr-pick-link">
        <span class="jr-pick-num" aria-hidden="true">{i:02d}</span>
        <span class="jr-pick-media">{img(x["image"], x["alt"], x.get("width"), x.get("height"))}</span>
        <div class="jr-pick-body">
          <span class="jr-meta">{meta_line(x["meta"])}</span>
          <h3 class="jr-pick-title">{x["title"]}</h3>
          <span class="jr-pick-excerpt">{x["excerpt"]}</span>
        </div>
      </a>
    </li>''')
        out.append(f'''
<section class="jr-picks" aria-labelledby="picksTitle">
  <div class="jr-wrap">
    <div class="jr-section-head">
      <p class="jr-eyebrow">{esc(p["eyebrow"])}</p>
      <h2 id="picksTitle" class="jr-h2">{p["title"]}</h2>
    </div>
    <ol class="jr-picks-list">
{chr(10).join(items)}
    </ol>
  </div>
</section>''')

    r = data["regions"]
    tiles = []
    for x in region_items:
        n = region_counts[x["key"]]
        tiles.append(f'''      <li><a class="jr-region" href="?region={esc(x["key"])}#archive" data-region="{esc(x["key"])}">
        <span class="jr-region-media">{img(x["image"], x["alt"])}</span>
        <span class="jr-region-name">{esc(x["label"])}</span>
        <span class="jr-region-count">{n} {"story" if n == 1 else "stories"}</span>
      </a></li>''')
    out.append(f'''
<section class="jr-regions" aria-labelledby="regionsTitle">
  <div class="jr-wrap">
    <div class="jr-section-head jr-section-head-split">
      <div>
        <p class="jr-eyebrow">{esc(r["eyebrow"])}</p>
        <h2 id="regionsTitle" class="jr-h2">{r["title"]}</h2>
      </div>
      <p class="jr-section-sub">{esc(r["sub"])}</p>
    </div>
    <ul class="jr-region-list" aria-label="Browse stories by region">
{chr(10).join(tiles)}
    </ul>
  </div>
</section>''')

    ar = data["archive"]
    pills = [f'''        <button type="button" class="jr-pill is-active" data-topic="all" aria-pressed="true">All stories <span class="jr-pill-n">{len(articles)}</span></button>''']
    for t in topics:
        pills.append(f'''        <button type="button" class="jr-pill" data-topic="{esc(t["key"])}" aria-pressed="false">{esc(t["label"])} <span class="jr-pill-n">{topic_counts[t["key"]]}</span></button>''')
    opts = ['        <option value="">All regions</option>']
    for x in region_items:
        opts.append(f'        <option value="{esc(x["key"])}">{esc(x["label"])}</option>')
    cards = []
    for a in articles:
        region_label = regions.get(a["region"], {}).get("label", "")
        haystack = " ".join([a["title"], a["excerpt"], a["kicker"], region_label, a["slug"].replace("-", " "),
                             facts[a["slug"]]["description"]])
        haystack = text_of(haystack).lower()
        meta = meta_line([a["read"], a["date"], a["author"]])
        cards.append(f'''    <a href="blog/{esc(a["slug"])}" class="card jr-card" data-topic="{esc(a["topic"])}" data-region="{esc(a["region"])}" data-search="{esc(haystack)}">
      <span class="jr-card-media">{img(a["image"], a["alt"])}</span>
      <div class="jr-card-body">
        <span class="jr-kicker">{a["kicker"]}</span>
        <h3 class="jr-card-title">{a["title"]}</h3>
        <span class="jr-card-excerpt">{a["excerpt"]}</span>
        <span class="jr-meta">{meta}</span>
      </div>
    </a>''')
    out.append(f'''
<section class="jr-archive" id="archive" aria-labelledby="archiveTitle" data-initial="{int(ar.get("initial", 12))}">
  <div class="jr-wrap">
    <div class="jr-section-head">
      <p class="jr-eyebrow">{esc(ar["eyebrow"])}</p>
      <h2 id="archiveTitle" class="jr-h2">{ar["title"]}</h2>
    </div>
    <form class="jr-toolbar" id="archiveTools" role="search" aria-label="Find a story" action="#archive">
      <div class="jr-pills" role="group" aria-label="Filter by topic">
{chr(10).join(pills)}
      </div>
      <label class="jr-search">
        <span class="visually-hidden">Search stories</span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input type="search" name="q" id="archiveSearch" placeholder="Search stories, regions, cities…" autocomplete="off" enterkeyhint="search">
      </label>
      <label class="jr-select">
        <span class="visually-hidden">Region</span>
        <select name="region" id="archiveRegion">
{chr(10).join(opts)}
        </select>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>
      </label>
    </form>
    <div class="jr-status-row">
      <p class="jr-status" id="archiveStatus" aria-live="polite">{len(articles)} stories</p>
      <button type="button" class="jr-reset" id="archiveReset" hidden>Clear filters <span aria-hidden="true">×</span></button>
    </div>
    <div class="jr-grid" id="archiveGrid">
{chr(10).join(cards)}
    </div>
    <div class="jr-empty" id="archiveEmpty" hidden>
      <p class="jr-empty-title">No stories match that yet.</p>
      <p class="jr-empty-sub">Try another word, a region, or clear the filters to see every dispatch.</p>
      <button type="button" class="jr-btn" data-reset>Show all stories</button>
    </div>
    <div class="jr-more" id="archiveMoreWrap" hidden>
      <button type="button" class="jr-btn" id="archiveMore">Show more stories</button>
    </div>
  </div>
</section>''')

    kg = data.get("keep_going", [])
    if kg:
        links = "\n".join(f'''      <a href="{esc(k["href"])}" class="jr-keep-link"><span class="jr-keep-label">{esc(k["label"])}</span><span class="jr-keep-sub">{esc(k["sub"])}</span><span class="jr-keep-arr" aria-hidden="true">→</span></a>''' for k in kg)
        out.append(f'''
<nav class="jr-keep" aria-label="Keep exploring Show Me Türkiye">
  <div class="jr-wrap">
    <p class="jr-eyebrow">Keep exploring</p>
    <div class="jr-keep-grid">
{links}
    </div>
  </div>
</nav>''')
    return "<!-- JOURNAL:BODY:START -->\n" + "\n".join(out) + "\n<!-- JOURNAL:BODY:END -->"


def render_ld(data, articles):
    items = []
    for i, a in enumerate(articles, 1):
        items.append({"@type": "ListItem", "position": i, "url": f"{BASE}/blog/{a['slug']}", "name": text_of(a["title"])})
    ld = {"@context": "https://schema.org", "@type": "ItemList", "@id": f"{BASE}/blog#stories",
          "name": "Show Me Türkiye Journal stories", "numberOfItems": len(items), "itemListElement": items}
    return '<script type="application/ld+json" id="smt-journal-ld">' + json.dumps(ld, ensure_ascii=False, separators=(",", ":")) + "</script>"


def replace_between(s, start, end, new):
    i = s.index(start)
    j = s.index(end, i) + len(end)
    return s[:i] + new + s[j:]


PROTECTED = [  # regions that must be byte-identical before and after a render
    ("head SEO", "<title>", '<script type="application/ld+json">'),
    ("nav", '<nav class="site-nav"', '<main id="main"'),
    ("footer", "<footer class=\"footer", "<!-- ═══ SITE SEARCH"),
    ("search", "<!-- ═══ SITE SEARCH", "<!-- SMT-CONSENT-START -->"),
    ("consent", "<!-- SMT-CONSENT-START -->", "</body>"),
]


def seg(s, start, end):
    i = s.index(start)
    return s[i:s.index(end, i)]


def render(data_path, site, template):
    data = json.load(open(data_path, encoding="utf-8"))
    articles, facts, warnings = collect(data, site)
    out = template
    out = replace_between(out, "<!-- JOURNAL:BODY:START", "<!-- JOURNAL:BODY:END -->", render_body(data, articles, facts))
    out = replace_between(out, '<script type="application/ld+json" id="smt-journal-ld">', "</script>", render_ld(data, articles))
    c = data["cover"]
    out = replace_between(out, '<link id="smt-journal-preload"', ">",
                          f'<link id="smt-journal-preload" rel="preload" as="image" href="{esc(c["image"])}" fetchpriority="high">')
    return out, {"stories": len(articles), "auto": sum(1 for a in articles if a.get("_auto")), "warnings": warnings}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="render in memory and compare with the page; exit 1 on drift")
    ap.add_argument("--data", default=os.path.join(ROOT, "data", "journal", "journal.json"))
    ap.add_argument("--site", default=ROOT, help="site root that holds blog/*.html")
    ap.add_argument("--page", default=os.path.join(ROOT, "blog.html"), help="template page")
    ap.add_argument("--out", default=None, help="output page (default: overwrite --page)")
    a = ap.parse_args()
    template = read(a.page)
    out, stats = render(a.data, a.site, template)
    for name, s0, s1 in PROTECTED:
        assert seg(template, s0, s1) == seg(out, s0, s1), f"protected block changed: {name}"
    target = a.out or a.page
    for w in stats["warnings"]:
        print("  !", w)
    if a.check:
        current = read(target) if os.path.exists(target) else ""
        if current == out:
            print(f"JOURNAL PAGE: PASS ({stats['stories']} stories, in sync with data/journal and blog/)")
            sys.exit(0)
        print("JOURNAL PAGE: BLOCKED (blog.html differs from data/journal + blog/; run python3 build-blog.py)")
        sys.exit(1)
    open(target, "w", encoding="utf-8").write(out)
    print(f"wrote {target}: {stats['stories']} stories" + (f", {stats['auto']} auto-listed" if stats["auto"] else ""))


if __name__ == "__main__":
    main()
