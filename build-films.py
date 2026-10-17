#!/usr/bin/env python3
"""
Show Me Türkiye - Films page builder (Films 2.0)

Same pattern as build-footer.py: a build script in the repo root, data under data/films/,
and a --check mode for the GitHub Action.

    python3 build-films.py              render projects.html from data/films/*.json
    python3 build-films.py --check      report only; exit 1 if projects.html is out of date
    python3 build-films.py catalog      refresh data/films/film_catalog.json from the three
                                        public playlist RSS feeds (merge, never delete)

Data (all under data/films/, all version controlled):
    film_catalog.json   facts from YouTube: id, series playlist, title, uploadDate, duration,
                        raw description, pages on this site that embed the film
    film_places.json    curated film -> place registry + optional per-film overrides
                        (description, poster). Every mapping is verified by an embed on the
                        target page or by the film's own title. Nothing is guessed.
    film_series.json    the three series (key, playlist, name, label, description)

The page: projects.html is both template and output. Generated regions sit between markers
and everything outside them (head SEO tags, nav, footer, search, consent) is left untouched:
    <!-- FILMS:BODY:START --> ... <!-- FILMS:BODY:END -->
    <style id="smt-films2-css">, <script id="smt-films2-js">, <script id="smt-films2-ld">
The first run converts the legacy page (series cards + JS video panel) into marker form.

No network access is needed to render. `catalog` is the only subcommand that goes online.
"""
import argparse, html, json, os, re, ssl, sys, urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://showmeturkiye.com"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
MOBILE_INITIAL = 8   # cards shown on phones before "Show all"


# ── helpers ───────────────────────────────────────────────────────────────────
def esc(s):
    return html.escape(str(s), quote=True)


def read(path):
    return open(path, encoding="utf-8").read()


def load(data_dir, name):
    return json.load(open(os.path.join(data_dir, name), encoding="utf-8"))


def page_title(site, rel):
    """Visible H1 of a page, used for link labels."""
    p = os.path.join(site, rel)
    if not rel or not os.path.isfile(p):
        return rel
    m = re.search(r"<h1[^>]*>(.*?)</h1>", read(p), re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(m.group(1)))).strip() if m else rel


def og_image(site, rel):
    p = os.path.join(site, rel)
    if not rel or not os.path.isfile(p):
        return ""
    m = re.search(r'property="og:image" content="([^"]+)"', read(p))
    return m.group(1) if m else ""


def route_stops(site):
    out = {}
    d = os.path.join(site, "routes")
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".html"):
                out["routes/" + f] = set(re.findall(r'href="\.\./cities/([a-z-]+)', read(os.path.join(d, f))))
    return out


def href(rel):
    return rel[:-5] if rel.endswith(".html") else rel


def iso_minutes(d):
    m = re.match(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$", d or "")
    if not m:
        return ""
    h, mi, s = (int(x or 0) for x in m.groups())
    total = h * 60 + mi + (1 if s >= 30 else 0)
    return f"{total} min" if total else "1 min"


def month_year(iso):
    return f"{MONTHS[int(iso[5:7]) - 1]} {iso[:4]}"


BOILERPLATE = ("love discovering", "explore türkiye through my films", "hello there", "hello fellas", "merhaba",
               "subscribe", "leave a comment", "let me know in the comments", "instagram:", "chapters")
TURKISH = re.compile(r"\b(ve|bir|için|ile|bu|olan|olarak|çok|daha|değil)\b")


def film_description(raw, override=None):
    """One editorial paragraph per film, taken from the film's own YouTube description.

    Priority: owner override > the paragraph the owner marks with a leading "─" (the hook that
    follows the channel boilerplate) > the first English paragraph that is not boilerplate,
    a link, a timestamp list or a greeting. Turkish-only descriptions return "" (the page is
    English; nothing is translated or invented).
    """
    if override:
        return override.strip()
    if not raw:
        return ""
    text = raw.replace("\r", "")
    # the "─ " marker may sit on the same line as the site URL; split it out
    text = re.sub(r"\n─\s*", "\n\n─ ", text)
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    cands = []
    for p in paras:
        if p.startswith("─"):
            cands.insert(0, p.lstrip("─ ").strip())
        else:
            cands.append(p)
    for p in cands:
        low = p.lower()
        if "http" in low or re.match(r"\d\d:\d\d", p) or len(p) < 60:
            continue
        if any(b in low for b in BOILERPLATE):
            continue
        if len(TURKISH.findall(low)) >= 3:
            continue
        # cut at a sentence boundary around 220 chars
        if len(p) > 230:
            cut = p[:230]
            i = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
            p = cut[:i + 1] if i > 80 else cut.rsplit(" ", 1)[0] + "…"
        return p.strip()
    return ""


# ── catalog ───────────────────────────────────────────────────────────────────
EMBED_RE = re.compile(r"openVideo\('([A-Za-z0-9_-]{11})'|youtube(?:-nocookie)?\.com/embed/([A-Za-z0-9_-]{11})")


def fetch(url):
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
    with urllib.request.urlopen(url, context=ctx, timeout=20) as r:
        return r.read().decode("utf-8")


def site_embeds(site):
    found = defaultdict(list)
    for root, dirs, files in os.walk(site):
        dirs[:] = [d for d in dirs if d not in (".git", "assets", ".github", "gpx", "node_modules", "data", "drafts")]
        for f in files:
            if f.endswith(".html") and f != "404.html":
                rel = os.path.relpath(os.path.join(root, f), site)
                if rel == "projects.html":
                    continue
                for m in EMBED_RE.finditer(read(os.path.join(root, f))):
                    vid = m.group(1) or m.group(2)
                    if rel not in found[vid]:
                        found[vid].append(rel)
    return found


def build_catalog(data_dir, site, offline=False):
    series = load(data_dir, "film_series.json")["series"]
    cat_path = os.path.join(data_dir, "film_catalog.json")
    merged = {f["id"]: f for f in json.load(open(cat_path, encoding="utf-8"))} if os.path.exists(cat_path) else {}
    cache = os.path.join(data_dir, "rss")
    os.makedirs(cache, exist_ok=True)
    for s in series:
        path = os.path.join(cache, s["playlist"] + ".xml")
        if not offline:
            try:
                open(path, "w", encoding="utf-8").write(fetch(f"https://www.youtube.com/feeds/videos.xml?playlist_id={s['playlist']}"))
            except Exception as e:
                print(f"warn: RSS fetch failed for {s['name']}: {e}; using cached copy")
        if not os.path.exists(path):
            continue
        for e in re.findall(r"<entry>(.*?)</entry>", read(path), re.S):
            vid = re.search(r"<yt:videoId>(.*?)<", e).group(1)
            desc = re.search(r"<media:description>(.*?)</media:description>", e, re.S)
            cur = merged.setdefault(vid, {"id": vid})
            cur.update({
                "series": s["key"], "playlist": s["playlist"],
                "title": html.unescape(re.search(r"<title>(.*?)</title>", e).group(1)),
                "uploadDate": re.search(r"<published>(.*?)<", e).group(1),
                "rawDescription": html.unescape(desc.group(1)).strip() if desc else cur.get("rawDescription", ""),
            })
    # optional one-off API snapshot (durations, full playlists beyond the RSS window)
    snap = os.path.join(data_dir, "yt_api_snapshot.json")
    if os.path.exists(snap):
        by_pl = {s["playlist"]: s["key"] for s in series}
        for pl, vids in json.load(open(snap, encoding="utf-8")).items():
            for v in vids:
                cur = merged.setdefault(v["id"], {"id": v["id"]})
                cur.setdefault("series", by_pl.get(pl, ""))
                cur.setdefault("playlist", pl)
                cur.setdefault("title", v["title"])
                cur.setdefault("uploadDate", v["publishedAt"])
                if v.get("duration"):
                    cur["duration"] = v["duration"]
                if not cur.get("rawDescription"):
                    cur["rawDescription"] = v.get("description", "")
    emb = site_embeds(site)
    films = []
    for vid, f in merged.items():
        f.pop("description", None); f.pop("place", None); f.pop("thumbnailUrl", None)
        f.pop("embedUrl", None); f.pop("watchUrl", None)
        f["pages"] = emb.get(vid, [])
        films.append(f)
    films.sort(key=lambda f: f["uploadDate"], reverse=True)
    json.dump(films, open(cat_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    places = load(data_dir, "film_places.json")["films"]
    print(f"catalog: {len(films)} films, {sum(1 for f in films if f.get('duration'))} with duration, "
          f"{sum(1 for f in films if f['pages'])} embedded on a page")
    for f in films:
        if f["id"] not in places:
            print(f"  not in film_places.json (renders without a place): {f['id']} {f['title']}")


# ── page assets ───────────────────────────────────────────────────────────────
CSS = r"""
/* ═══ FILMS 2.0 (generated by build-films.py; edit the script, not this block) ═══ */
[hidden]{display:none!important}
.films-wrap{max-width:1320px;margin:0 auto;padding:0 48px}
.films-eyebrow{font-family:var(--sans);font-size:11px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:var(--text-muted)}
.films-link{display:inline-flex;align-items:center;gap:10px;font-family:var(--sans);font-size:11px;font-weight:500;letter-spacing:.2em;text-transform:uppercase;color:var(--text);text-decoration:none;padding-bottom:5px;border-bottom:1px solid var(--gold);transition:gap .3s ease,color .3s ease,border-color .3s ease;white-space:nowrap}
.films-link:hover{gap:14px;color:var(--brown);border-color:var(--brown)}
.films-link .arr{transition:transform .3s ease}
.films-link:hover .arr{transform:translateX(2px)}
.films-link.ext{border-color:rgba(42,20,16,.18)}
.films-chip:focus-visible,.films-link:focus-visible,.film-play:focus-visible,.film-place-link:focus-visible,.films-series-tile:focus-visible,.films-select:focus-visible,.films-more:focus-visible{outline:2px solid var(--brown);outline-offset:3px;border-radius:4px}

/* Player (lead + cards): poster -> iframe in place */
.film-player{position:relative;aspect-ratio:16/9;border-radius:12px;overflow:hidden;background:#1C1814;box-shadow:inset 0 0 0 1px rgba(42,20,16,.06),0 1px 2px rgba(42,20,16,.05),0 8px 24px rgba(42,20,16,.07),0 24px 56px rgba(42,20,16,.05)}
.film-player picture{display:block;width:100%;height:100%}
.film-player img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .7s cubic-bezier(.4,0,.2,1)}
.film-play{position:absolute;inset:0;width:100%;height:100%;margin:0;padding:0;border:0;cursor:pointer;display:flex;align-items:center;justify-content:center;background:linear-gradient(180deg,rgba(10,10,10,0) 55%,rgba(10,10,10,.45) 100%);color:var(--cream);text-decoration:none}
.film-play-btn{width:64px;height:64px;border-radius:999px;background:rgba(192,57,43,.92);display:flex;align-items:center;justify-content:center;transition:transform .35s ease,background .3s ease;box-shadow:0 8px 24px rgba(10,10,10,.25)}
.film-play-btn svg{width:22px;height:22px;margin-left:3px;fill:var(--cream)}
.film-play:hover .film-play-btn{transform:scale(1.08);background:var(--brown)}
.film-player:hover img{transform:scale(1.04)}
.film-duration{position:absolute;right:12px;bottom:12px;background:rgba(10,10,10,.82);color:var(--cream);font-family:var(--sans);font-size:11px;font-weight:500;letter-spacing:.04em;padding:4px 9px;border-radius:4px;pointer-events:none}
.film-player iframe{position:absolute;inset:0;width:100%;height:100%;border:0;background:#000}
.film-player.playing .film-play,.film-player.playing .film-duration,.film-player.playing img{display:none}
.film-yt-link{display:inline-block;margin-top:10px;font-family:var(--sans);font-size:11px;font-weight:500;letter-spacing:.18em;text-transform:uppercase;color:var(--text-muted);text-decoration:none;border-bottom:1px solid var(--gold);padding-bottom:2px}
.film-yt-link:hover{color:var(--brown);border-color:var(--brown)}

/* Collection head */
.films-index{padding:88px 0 130px}
.films-index-head{display:flex;align-items:flex-end;justify-content:space-between;gap:40px;margin-bottom:48px}
.films-index-head .films-eyebrow{margin-bottom:18px}
.films-index-title{font-family:var(--serif);font-size:clamp(32px,4vw,52px);font-weight:500;line-height:1.06;letter-spacing:-.012em;color:var(--text);margin:0 0 14px}
.films-index-title em{font-style:italic;color:var(--brown);letter-spacing:.015em;white-space:nowrap}
.films-index-sub{font-family:var(--sans);font-size:15px;line-height:1.65;color:var(--text-muted);margin:0;max-width:52ch}
.films-count{font-family:var(--sans);font-size:11px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:var(--text-muted);white-space:nowrap;padding-bottom:6px}

/* Lead card (newest film) */
.film-card.film-card-lead{display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:56px;align-items:center;margin:0 0 72px}
.film-card-lead .film-player{border-radius:12px}
.film-card-lead .film-card-body{padding:0}
.film-card-lead .film-rule{margin-bottom:18px}
.film-card-lead .film-title{font-size:clamp(26px,2.7vw,38px);line-height:1.12;letter-spacing:-.012em;-webkit-line-clamp:3;margin-bottom:14px}
.film-card-lead .film-meta{margin-bottom:14px}
.film-card-lead .film-desc{font-size:15px;line-height:1.7;-webkit-line-clamp:unset;display:block;margin:0 0 26px;max-width:46ch}
.film-lead-links{display:flex;flex-wrap:wrap;gap:16px 32px;margin-top:4px}
.film-card-lead .film-play-btn{width:64px;height:64px;transform:none}

/* Series strip: the three series as compact tiles that also filter */
.films-series{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;padding-top:36px;border-top:1px solid rgba(42,20,16,.1)}
.films-series-tile{display:flex;align-items:center;gap:16px;text-align:left;padding:12px 16px 12px 12px;background:var(--white);border:1px solid rgba(42,20,16,.08);border-radius:12px;cursor:pointer;color:var(--text);font:inherit;transition:border-color .25s ease,box-shadow .25s ease,transform .4s cubic-bezier(.22,.61,.36,1);box-shadow:0 1px 2px rgba(42,20,16,.04),0 6px 18px rgba(42,20,16,.05)}
.films-series-tile:hover{border-color:rgba(192,57,43,.4);transform:translateY(-2px);box-shadow:0 2px 4px rgba(42,20,16,.06),0 14px 32px rgba(42,20,16,.1)}
.films-series-tile[aria-pressed="true"]{border-color:var(--brown);box-shadow:inset 0 0 0 1px var(--brown),0 14px 32px rgba(192,57,43,.14)}
.films-series-thumb{flex:0 0 96px;aspect-ratio:16/9;border-radius:6px;overflow:hidden;background:#1C1814}
.films-series-thumb picture,.films-context-img picture{display:block;width:100%;height:100%}
.films-series-thumb img{width:100%;height:100%;object-fit:cover;display:block}
.films-series-text{min-width:0;display:block}
.films-series-label,.films-series-name,.films-series-count{display:block}
.films-series-label{font-family:var(--sans);font-size:10px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:var(--text-muted);margin-bottom:5px}
.films-series-name{font-family:var(--serif);font-size:17px;font-weight:500;line-height:1.2;color:var(--text);letter-spacing:-.005em}
.films-series-count{font-family:var(--sans);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--text-muted);margin-top:5px}
.films-series-tile[aria-pressed="true"] .films-series-name{color:var(--brown)}

/* Place filter: chips on wide screens, a native select on phones */
.films-filters{display:flex;flex-direction:column;gap:14px;margin:28px 0 40px}
.films-filter-row{display:flex;align-items:center;gap:18px}
.films-filter-label{font-family:var(--sans);font-size:10.5px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:var(--text-muted);flex:0 0 84px}
.films-chips{display:flex;flex-wrap:wrap;gap:8px;min-width:0}
.films-chip{font-family:var(--sans);font-size:11px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;line-height:1;padding:11px 16px;border-radius:999px;border:1px solid rgba(42,20,16,.18);background:transparent;color:var(--text);cursor:pointer;transition:background .25s ease,color .25s ease,border-color .25s ease;white-space:nowrap}
.films-chip small{font-size:10px;font-weight:400;letter-spacing:.06em;opacity:.6;margin-left:6px}
.films-chip:hover{border-color:var(--brown);color:var(--brown)}
.films-chip[aria-pressed="true"]{background:var(--text);color:var(--cream);border-color:var(--text)}
.films-chip[aria-pressed="true"]:hover{background:var(--brown);border-color:var(--brown);color:var(--cream)}
.films-select-wrap{display:none;position:relative;flex:1;min-width:0}
.films-select{appearance:none;-webkit-appearance:none;width:100%;font-family:var(--sans);font-size:12px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:var(--text);background:var(--white);border:1px solid rgba(42,20,16,.18);border-radius:999px;padding:13px 44px 13px 18px;cursor:pointer}
.films-select-wrap::after{content:"";position:absolute;right:18px;top:50%;width:8px;height:8px;border-right:1.5px solid var(--text-muted);border-bottom:1.5px solid var(--text-muted);transform:translateY(-70%) rotate(45deg);pointer-events:none}
.films-clear{display:inline-flex;align-items:center;gap:8px;font-family:var(--sans);font-size:11px;font-weight:500;letter-spacing:.16em;text-transform:uppercase;color:var(--text-muted);background:none;border:0;padding:8px 0;cursor:pointer}
.films-clear:hover{color:var(--brown)}
html:not(.js) .films-filters,html:not(.js) .films-context,html:not(.js) .films-series,html:not(.js) .films-more{display:none}

/* Context panel: what a chosen place or series connects to */
.films-context{display:grid;grid-template-columns:220px minmax(0,1fr);gap:36px;align-items:center;padding:28px;margin-bottom:44px;background:var(--white);border-radius:12px;box-shadow:inset 0 0 0 1px rgba(42,20,16,.06),0 1px 2px rgba(42,20,16,.05),0 8px 24px rgba(42,20,16,.07)}
.films-context-img{aspect-ratio:3/2;border-radius:8px;overflow:hidden;background:#1C1814}
.films-context-img img{width:100%;height:100%;object-fit:cover;display:block}
.films-context .films-eyebrow{margin-bottom:12px}
.films-context-name{font-family:var(--serif);font-size:28px;font-weight:500;line-height:1.15;letter-spacing:-.01em;margin:0 0 10px;color:var(--text)}
.films-context-desc{font-family:var(--sans);font-size:14px;line-height:1.7;color:var(--text-muted);margin:0 0 20px;max-width:60ch}
.films-context-links{display:flex;flex-wrap:wrap;gap:14px 28px}

/* Film grid */
.films-grid{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:52px 32px}
.film-card{display:flex;flex-direction:column;min-width:0}
.film-card .film-player{border-radius:8px;box-shadow:0 6px 18px rgba(42,20,16,.10);transition:box-shadow .4s ease}
.film-card:hover .film-player{box-shadow:0 14px 32px rgba(42,20,16,.18)}
.film-card .film-play-btn{width:56px;height:56px;transform:scale(.9)}
.film-card .film-play:hover .film-play-btn{transform:scale(1)}
.film-card-body{padding:18px 4px 0}
.film-rule{display:flex;align-items:center;gap:12px;font-family:var(--sans);font-size:10.5px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:var(--text-muted);margin-bottom:12px}
.film-rule::after{content:"";flex:1;height:1px;background:rgba(42,20,16,.12)}
.film-title{font-family:var(--serif);font-size:18px;font-weight:500;line-height:1.35;letter-spacing:-.005em;color:var(--text);margin:0 0 8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;text-wrap:pretty}
.film-player.playing + .film-card-body .film-title{color:var(--brown)}
.film-desc{font-family:var(--sans);font-size:13px;line-height:1.6;color:var(--text-muted);margin:0 0 10px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.film-meta{font-family:var(--sans);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--text-muted);line-height:1.6}
.film-place-link,.film-place{display:inline-flex;align-items:center;gap:8px;margin-top:12px;font-family:var(--sans);font-size:11px;font-weight:500;letter-spacing:.18em;text-transform:uppercase;line-height:1.3}
.film-place-link{color:var(--text);text-decoration:none;border-bottom:1px solid var(--gold);padding:6px 0 3px;align-self:flex-start;transition:color .25s ease,border-color .25s ease,gap .25s ease}
.film-place-link:hover{color:var(--brown);border-color:var(--brown);gap:12px}
.film-place{color:var(--text-muted)}
.films-empty{grid-column:1/-1;text-align:center;padding:64px 24px;font-family:var(--sans);font-size:14px;color:var(--text-muted)}
.films-more{display:none;margin:36px auto 0;font-family:var(--sans);font-size:12px;font-weight:500;letter-spacing:.3em;text-transform:uppercase;color:var(--text);background:transparent;border:1px solid var(--text);border-radius:999px;padding:16px 36px;cursor:pointer;transition:background .25s ease,color .25s ease,border-color .25s ease}
.films-more:hover{background:var(--brown);color:var(--cream);border-color:var(--brown)}
.films-cta{margin-top:80px;display:flex;justify-content:center}
.films-live{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap}

@media (max-width:1080px){
  .films-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:44px 24px}
  .film-card.film-card-lead{gap:40px}
  .films-context{grid-template-columns:180px minmax(0,1fr);gap:28px}
  .films-series{gap:12px}
  .films-series-tile{gap:12px;padding:10px 12px 10px 10px}
  .films-series-thumb{flex-basis:72px}
  .films-series-name{font-size:15px}
}
@media (max-width:768px){
  .films-wrap{padding:0 20px}
  .film-card.film-card-lead{grid-template-columns:1fr;gap:22px;margin-bottom:48px}
  .film-card-lead .film-rule{margin-bottom:12px}
  .film-card-lead .film-desc{margin-bottom:20px}
  .films-index{padding:44px 0 88px}
  .films-index-head{flex-direction:column;align-items:flex-start;gap:12px;margin-bottom:24px}
  .films-count{padding-bottom:0}
  .films-series{grid-template-columns:1fr;gap:8px;padding-top:26px}
  .films-series-tile{padding:8px 12px 8px 8px;gap:12px;border-radius:10px}
  .films-series-tile:hover{transform:none}
  .films-series-thumb{flex-basis:80px}
  .films-series-label{margin-bottom:3px}
  .films-series-name{font-size:16px}
  .films-series-count{margin-top:3px}
  .films-filters{gap:12px;margin:22px 0 30px}
  .films-filter-row{gap:12px}
  .films-filter-label{flex:0 0 72px}
  .films-chips{display:none}
  .films-select-wrap{display:block}
  .films-grid{gap:36px 20px}
  .film-player:hover img,.film-card:hover .film-player{transform:none;box-shadow:0 6px 18px rgba(42,20,16,.10)}
  .film-play{background:linear-gradient(180deg,rgba(10,10,10,0) 55%,rgba(10,10,10,.35) 100%)}
  .films-cta{margin-top:48px}
}
@media (max-width:640px){
  .films-grid{grid-template-columns:1fr;gap:34px}
  .films-grid.is-collapsed .film-card[data-over="1"]{display:none}
  .films-more.is-visible{display:block}
  .films-context{grid-template-columns:1fr;gap:18px;padding:18px;margin-bottom:32px}
  .films-context-img{aspect-ratio:16/9}
  .films-context-name{font-size:24px}
}
@media (max-width:480px){
  .films-wrap{padding:0 16px}
  .film-title{font-size:17px}
  .film-card-lead .film-title{font-size:26px}
}
"""

JS = r"""
/* ═══ FILMS 2.0: filters, mobile pagination, inline playback. No network calls, no API key. ═══ */
(function(){
  var grid=document.getElementById('filmsGrid'); if(!grid) return;
  var cards=[].slice.call(grid.querySelectorAll('.film-card'));  // the featured card above the grid is never filtered
  var chips=[].slice.call(document.querySelectorAll('.films-chip'));
  var tiles=[].slice.call(document.querySelectorAll('.films-series-tile'));
  var panels=[].slice.call(document.querySelectorAll('.films-context'));
  var sel=document.getElementById('filmsPlaceSelect'), clear=document.getElementById('filmsClear');
  var empty=document.getElementById('filmsEmpty'), live=document.getElementById('filmsLive'), count=document.getElementById('filmsCount');
  var more=document.getElementById('filmsMore'), INITIAL=parseInt(grid.getAttribute('data-initial')||'8',10);
  var state={series:'',place:'',expanded:false};

  function apply(){
    var n=0, over=0;
    cards.forEach(function(c){
      var ok=(!state.series||c.getAttribute('data-series')===state.series)&&(!state.place||c.getAttribute('data-place')===state.place);
      c.hidden=!ok;
      if(ok){ n++; var isOver=(n>INITIAL); c.setAttribute('data-over', isOver?'1':'0'); if(isOver) over++; }
    });
    chips.forEach(function(ch){ ch.setAttribute('aria-pressed', String(state.place===ch.getAttribute('data-value'))); });
    tiles.forEach(function(t){ t.setAttribute('aria-pressed', String(state.series===t.getAttribute('data-value'))); });
    if(sel) sel.value=state.place;
    if(clear) clear.hidden=!(state.series||state.place);
    panels.forEach(function(p){
      var pl=p.getAttribute('data-place'), se=p.getAttribute('data-series');
      p.hidden=!((pl&&pl===state.place)||(se&&!state.place&&se===state.series));
    });
    empty.hidden=n>0;
    grid.classList.toggle('is-collapsed', !state.expanded && over>0);
    if(more){ more.classList.toggle('is-visible', !state.expanded && over>0); more.textContent='Show all '+n+' films'; }
    var label=n===1?'1 film':n+' films';
    if(count) count.textContent=label;
    if(live) live.textContent=label+' shown';
    var h=[state.series?'series='+state.series:'', state.place?'place='+state.place:''].filter(Boolean).join('&');
    if(history.replaceState) history.replaceState(null,'', h?'#'+h:location.pathname+location.search);
  }
  function setPlace(v){ state.place=v; state.expanded=false; apply(); }
  function setSeries(v){ state.series=(state.series===v)?'':v; state.expanded=false; apply(); }
  chips.forEach(function(ch){ ch.addEventListener('click', function(){ var v=ch.getAttribute('data-value'); setPlace(state.place===v?'':v); }); });
  tiles.forEach(function(t){ t.addEventListener('click', function(){ setSeries(t.getAttribute('data-value')); }); });
  if(sel) sel.addEventListener('change', function(){ setPlace(sel.value); });
  if(clear) clear.addEventListener('click', function(){ state.series=''; state.place=''; state.expanded=false; apply(); });
  if(more) more.addEventListener('click', function(){
    state.expanded=true; var first=cards.filter(function(c){ return !c.hidden && c.getAttribute('data-over')==='1'; })[0];
    apply(); if(first){ var a=first.querySelector('.film-play'); if(a) a.focus({preventScroll:true}); first.scrollIntoView({block:'start'}); }
  });
  (function(){ // deep links: projects#place=rize, #series=skies-of-turkiye
    var hit=false;
    location.hash.replace(/^#/,'').split('&').forEach(function(kv){ var p=kv.split('='); if((p[0]==='series'||p[0]==='place')&&p[1]){ state[p[0]]=decodeURIComponent(p[1]); hit=true; } });
    apply();
    if(hit){ var s=document.getElementById('films'); if(s) s.scrollIntoView(); }
  })();

  var playing=null;
  function stop(){
    if(!playing) return;
    var f=playing.querySelector('iframe'); if(f) f.remove();
    playing.classList.remove('playing');
    var l=playing.parentNode.querySelector('.film-yt-link'); if(l) l.remove();
    playing=null;
  }
  document.addEventListener('click', function(e){
    var btn=e.target.closest('.film-play'); if(!btn) return;
    e.preventDefault();
    var player=btn.closest('.film-player'); if(!player||player===playing) return;
    stop();
    var id=player.getAttribute('data-video-id'), title=player.getAttribute('data-video-title')||'';
    var f=document.createElement('iframe');
    f.src='https://www.youtube-nocookie.com/embed/'+id+'?autoplay=1&rel=0&modestbranding=1';
    f.title=title; f.allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen'; f.setAttribute('allowfullscreen','');
    player.appendChild(f); player.classList.add('playing'); playing=player;
    var body=player.parentNode.querySelector('.film-card-body');
    if(body && !body.querySelector('.film-yt-link')){
      var a=document.createElement('a'); a.className='film-yt-link'; a.href='https://www.youtube.com/watch?v='+id; a.target='_blank'; a.rel='noopener'; a.textContent='Watch on YouTube ↗';
      body.appendChild(a);
    }
  });
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') stop(); });
})();
"""

LAZY = ' loading="lazy" decoding="async"'
PLAY_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><polygon points="6,3 20,12 6,21"></polygon></svg>'


def poster_urls(f):
    """YouTube's own poster set for the film: (jpg, small jpg, webp, small webp). The `poster`
    override in film_places.json may name one of YouTube's generated frames (maxres1/2/3) or an
    absolute image URL (then no small/webp variants)."""
    vid = f["id"]
    p = f.get("poster")
    if p and p.startswith("http"):
        return p, p, "", ""
    key = p if p in ("maxres1", "maxres2", "maxres3") else "maxresdefault"
    small = {"maxresdefault": "mqdefault", "maxres1": "mq1", "maxres2": "mq2", "maxres3": "mq3"}[key]
    return (f"https://i.ytimg.com/vi/{vid}/{key}.jpg", f"https://i.ytimg.com/vi/{vid}/{small}.jpg",
            f"https://i.ytimg.com/vi_webp/{vid}/{key}.webp", f"https://i.ytimg.com/vi_webp/{vid}/{small}.webp")


def picture(f, sizes, attrs, w=1280, h=720):
    big, small, webp, webp_small = poster_urls(f)
    if not webp:
        return f'<img src="{big}" width="{w}" height="{h}" alt=""{attrs}>'
    return (f'<picture><source type="image/webp" srcset="{webp_small} 320w, {webp} 1280w" sizes="{sizes}">'
            f'<img src="{big}" srcset="{small} 320w, {big} 1280w" sizes="{sizes}" width="{w}" height="{h}" alt=""{attrs}></picture>')


def player(f, eager=False):
    img_attrs = ' fetchpriority="high" decoding="async"' if eager else ' loading="lazy" decoding="async"'
    sizes = "(max-width: 768px) 100vw, 58vw" if eager else "(max-width: 640px) 100vw, (max-width: 1080px) 50vw, 33vw"
    dur = iso_minutes(f.get("duration"))
    return (
        f'<div class="film-player" data-video-id="{f["id"]}" data-video-title="{esc(f["title"])}">'
        + picture(f, sizes, img_attrs)
        + f'<a class="film-play" href="https://www.youtube.com/watch?v={f["id"]}" target="_blank" rel="noopener" aria-label="Play: {esc(f["title"])}">'
        f'<span class="film-play-btn">{PLAY_SVG}</span></a>'
        + (f'<span class="film-duration" aria-hidden="true">{dur}</span>' if dur else "")
        + "</div>"
    )


# ── render ────────────────────────────────────────────────────────────────────
def render(data_dir, site, template):
    films = load(data_dir, "film_catalog.json")
    reg = load(data_dir, "film_places.json")
    series_cfg = load(data_dir, "film_series.json")
    series = series_cfg["series"]
    by_key = {s["key"]: s for s in series}
    places, fmap = reg["places"], reg["films"]
    stops = route_stops(site)
    films.sort(key=lambda f: f["uploadDate"], reverse=True)

    for f in films:
        m = fmap.get(f["id"], {})
        f["place"] = m.get("place")
        f["scope"] = m.get("scope", "")
        f["poster"] = m.get("poster")
        f["s"] = by_key[f["series"]]
        f["desc"] = film_description(f.get("rawDescription", ""), m.get("description"))
    for s in series:  # series cover = newest film of that series
        s["count"] = sum(1 for f in films if f["series"] == s["key"])
        newest = next((f for f in films if f["series"] == s["key"]), None)
        s["newest"] = newest
        s["image"] = poster_urls(newest)[0] if newest else ""

    by_place = defaultdict(list)
    for f in films:
        if f["place"]:
            by_place[f["place"]].append(f)
    ctx = {}
    for key, p in places.items():
        if key not in by_place:
            continue
        links = []
        if p.get("guide"):
            links.append((f'{page_title(site, p["guide"])} city guide', href(p["guide"])))
        if p.get("journal"):
            links.append((f'Journal: {page_title(site, p["journal"])}', href(p["journal"])))
        city = p.get("guide", "").replace("cities/", "").replace(".html", "")
        for r, cities in stops.items():
            if city and city in cities:
                links.append((f'Route: {page_title(site, r)}', href(r)))
        img = og_image(site, p.get("guide") or p.get("journal") or "")
        ctx[key] = {"label": p["label"], "links": links, "image": img, "films": by_place[key]}

    def place_link(f):
        if f["place"]:
            p = places[f["place"]]
            target = p.get("guide") or p.get("journal")
            if target:
                return f'<a class="film-place-link" href="{href(target)}">Filmed in {esc(p["label"])} <span class="arr" aria-hidden="true">→</span></a>'
            return f'<span class="film-place">Filmed in {esc(p["label"])}</span>'
        return f'<span class="film-place">{esc(f["scope"])}</span>' if f["scope"] else ""

    total = len(films)
    # featured (pinned) film: always visible, not part of the filterable grid
    feat = next((f for f in films if f["id"] == series_cfg.get("featured")), films[0])
    feat_num = total - films.index(feat)
    lead_links = ""
    if feat["place"]:
        t = places[feat["place"]].get("guide") or places[feat["place"]].get("journal")
        if t:
            lead_links += f'<a class="films-link" href="{href(t)}">{esc(page_title(site, t))} guide <span class="arr" aria-hidden="true">→</span></a>'
    lead_links += f'<a class="films-link ext" href="https://www.youtube.com/watch?v={feat["id"]}" target="_blank" rel="noopener">Watch on YouTube <span class="arr" aria-hidden="true">↗</span></a>'
    where = f' · Filmed in {esc(places[feat["place"]]["label"])}' if feat["place"] else ""
    lead = f'''
    <div class="film-card film-card-lead">
      {player(feat, eager=True)}
      <div class="film-card-body">
        <div class="film-rule">Featured film · No. {feat_num:02d}</div>
        <h3 class="film-title">{esc(feat["title"])}</h3>
        <div class="film-meta">{month_year(feat["uploadDate"])} · {iso_minutes(feat.get("duration"))} · {esc(feat["s"]["name"])}{where}</div>
        {f'<p class="film-desc">{esc(feat["desc"])}</p>' if feat["desc"] else ""}
        <div class="film-lead-links">{lead_links}</div>
      </div>
    </div>'''

    # series strip
    strip = '<div class="films-series" role="group" aria-label="Filter by series">' + "".join(
        f'<button type="button" class="films-series-tile" data-value="{s["key"]}" aria-pressed="false">'
        f'<span class="films-series-thumb">{picture(s["newest"], "96px", LAZY, 320, 180)}</span>'
        f'<span class="films-series-text"><span class="films-series-label">{esc(s["label"])}</span>'
        f'<span class="films-series-name">{esc(s["name"])}</span>'
        f'<span class="films-series-count">{s["count"]} film{"s" if s["count"] != 1 else ""}</span></span></button>'
        for s in series) + "</div>"

    # place filter
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")
    place_keys = sorted(ctx, key=lambda k: ctx[k]["label"].translate(tr).lower())

    def chip(value, label, n=None):
        c = f' <small>{n}</small>' if n is not None else ""
        return f'<button type="button" class="films-chip" data-value="{esc(value)}" aria-pressed="{"true" if value == "" else "false"}">{esc(label)}{c}</button>'
    chips = [chip("", "All places")] + [chip(k, ctx[k]["label"], len(ctx[k]["films"])) for k in place_keys]
    options = '<option value="">All places</option>' + "".join(
        f'<option value="{k}">{esc(ctx[k]["label"])} ({len(ctx[k]["films"])})</option>' for k in place_keys)
    filters = f'''
    <div class="films-filters">
      <div class="films-filter-row"><span class="films-filter-label" id="lblPlace">Filmed in</span>
        <div class="films-chips" role="group" aria-labelledby="lblPlace">{"".join(chips)}</div>
        <div class="films-select-wrap"><select class="films-select" id="filmsPlaceSelect" aria-labelledby="lblPlace">{options}</select></div>
      </div>
      <button type="button" class="films-clear" id="filmsClear" hidden>Clear filters <span aria-hidden="true">×</span></button>
    </div>'''

    # context panels
    panels = []
    for s in series:
        panels.append(f'''
    <div class="films-context" data-series="{s["key"]}" hidden>
      <div class="films-context-img">{picture(s["newest"], "(max-width: 640px) 100vw, 220px", LAZY, 640, 360)}</div>
      <div>
        <div class="films-eyebrow">{esc(s["label"])} · {s["count"]} film{"s" if s["count"] != 1 else ""}</div>
        <div class="films-context-name">{esc(s["name"])}</div>
        <p class="films-context-desc">{esc(s["description"])}</p>
        <div class="films-context-links"><a class="films-link ext" href="https://www.youtube.com/playlist?list={s["playlist"]}" target="_blank" rel="noopener">View playlist on YouTube <span class="arr" aria-hidden="true">↗</span></a></div>
      </div>
    </div>''')
    for k in place_keys:
        c = ctx[k]
        n = len(c["films"])
        links = "".join(f'<a class="films-link" href="{u}">{esc(t)} <span class="arr" aria-hidden="true">→</span></a>' for t, u in c["links"]) \
            or '<span class="films-eyebrow">No guide for this place yet</span>'
        img = f'<div class="films-context-img"><img src="{c["image"]}" alt="" loading="lazy" width="600" height="400"></div>' if c["image"] else '<div class="films-context-img"></div>'
        panels.append(f'''
    <div class="films-context" data-place="{k}" hidden>
      {img}
      <div>
        <div class="films-eyebrow">Filmed in · {n} film{"s" if n != 1 else ""}</div>
        <div class="films-context-name">{esc(c["label"])}</div>
        <div class="films-context-links">{links}</div>
      </div>
    </div>''')

    # grid
    items = []
    for i, f in enumerate(films):
        meta = " · ".join(x for x in (f["uploadDate"][:4], iso_minutes(f.get("duration")), f["s"]["name"]) if x)
        items.append(f'''
      <li class="film-card" data-series="{f["s"]["key"]}" data-place="{f["place"] or ""}">
        {player(f)}
        <div class="film-card-body">
          <div class="film-rule">No. {total - i:02d}</div>
          <h3 class="film-title">{esc(f["title"])}</h3>
          {f'<p class="film-desc">{esc(f["desc"])}</p>' if f["desc"] else ""}
          <div class="film-meta">{meta}</div>
          {place_link(f)}
        </div>
      </li>''')
    years = f'{films[-1]["uploadDate"][:4]} to {films[0]["uploadDate"][:4]}'
    body = f'''<!-- FILMS:BODY:START (generated by build-films.py from data/films/) -->
<section class="films-index" id="films" aria-labelledby="filmsTitle">
  <div class="films-wrap">
    <div class="films-index-head">
      <div>
        <div class="films-eyebrow">The collection · {years}</div>
        <h2 class="films-index-title" id="filmsTitle">Every film, <em>by place.</em></h2>
        <p class="films-index-sub">Newest first. Each film links to the guide for the place where it was shot, so you can keep going from the frame to the road.</p>
      </div>
      <div class="films-count" id="filmsCount">{total} films</div>
    </div>
    {lead}
    {strip}
    {filters}
    {"".join(panels)}
    <ol class="films-grid" id="filmsGrid" data-initial="{MOBILE_INITIAL}">{"".join(items)}
    </ol>
    <p class="films-empty" id="filmsEmpty" hidden>No film matches this combination yet.</p>
    <button type="button" class="films-more" id="filmsMore">Show all films</button>
    <div class="films-live" id="filmsLive" aria-live="polite"></div>
    <div class="films-cta"><a class="films-link ext" href="{series_cfg["channel"]}" target="_blank" rel="noopener">New films on YouTube <span class="arr" aria-hidden="true">↗</span></a></div>
  </div>
</section>
<!-- FILMS:BODY:END -->'''

    # structured data (mirrors the visible cards: title, poster, date, duration, description, place)
    def vo(f):
        o = {"@type": "VideoObject", "@id": f"{BASE}/projects#video-{f['id']}", "name": f["title"],
             "thumbnailUrl": [u for u in poster_urls(f)[:3:2] if u], "uploadDate": f["uploadDate"],
             "embedUrl": f"https://www.youtube-nocookie.com/embed/{f['id']}",
             "url": f"https://www.youtube.com/watch?v={f['id']}",
             "isPartOf": {"@type": "CreativeWorkSeries", "name": f["s"]["name"]},
             "publisher": {"@type": "Organization", "name": "Show Me Türkiye", "url": BASE + "/"}}
        if f["desc"]:
            o["description"] = f["desc"]
        if f.get("duration"):
            o["duration"] = f["duration"]
        if f["place"]:
            o["contentLocation"] = {"@type": "Place", "name": places[f["place"]]["label"]}
        return o
    ld = {"@context": "https://schema.org", "@type": "ItemList", "@id": BASE + "/projects#films",
          "name": "Show Me Türkiye films", "numberOfItems": total,
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": vo(f)} for i, f in enumerate(films)]}
    ld_tag = '<script type="application/ld+json" id="smt-films2-ld">' + json.dumps(ld, ensure_ascii=False, separators=(",", ":")) + "</script>"

    out = template
    legacy = "<!-- FILMS:BODY:START" not in out
    if legacy:
        out = convert_legacy(out)
    out = replace_between(out, "<!-- FILMS:BODY:START", "<!-- FILMS:BODY:END -->", body)
    out = replace_between(out, '<style id="smt-films2-css">', "</style>", '<style id="smt-films2-css">' + CSS + "</style>")
    out = replace_between(out, '<script id="smt-films2-js">', "</script>", '<script id="smt-films2-js">' + JS + "</script>")
    out = replace_between(out, '<script type="application/ld+json" id="smt-films2-ld">', "</script>", ld_tag)
    lb, ls, lw, lws = poster_urls(feat)
    preload = (f'<link id="smt-films2-preload" rel="preload" as="image" type="image/webp" imagesrcset="{lws} 320w, {lw} 1280w" imagesizes="(max-width: 768px) 100vw, 58vw">'
               if lw else f'<link id="smt-films2-preload" rel="preload" as="image" href="{lb}">')
    out = replace_between(out, '<link id="smt-films2-preload"', ">", preload)
    assert "AIzaSy" not in out, "YouTube API key must not survive in the output"
    stats = {"films": total, "places": len(ctx), "described": sum(1 for f in films if f["desc"]),
             "unplaced": [f["title"] for f in films if not f["place"]],
             "undescribed": [f["title"] for f in films if not f["desc"]], "legacy_converted": legacy}
    return out, stats


def replace_between(s, start, end, new):
    i = s.index(start)
    j = s.index(end, i) + len(end)
    return s[:i] + new + s[j:]


def convert_legacy(out):
    """One-time conversion of the live page (series cards + JS panel) into marker form."""
    a = out.index('<section class="projects-section">')
    b = out.index("<script>\nconst hamburgerBtn", a)
    out = out[:a] + "<!-- FILMS:BODY:START -->\n<!-- FILMS:BODY:END -->\n\n" + out[b:]
    a = out.index("/* ═══════════════════════════════════════\n   PROJECT VIDEOS")
    b = out.index("// Close menu when clicking any nav link", a)
    out = out[:a] + out[b:]
    marker = "</script>\n<!-- ═══════════════════════════════════════\n     FOOTER"
    assert marker in out
    out = out.replace(marker, '</script>\n<script id="smt-films2-js"></script>\n<!-- ═══════════════════════════════════════\n     FOOTER', 1)
    a = out.index("/* ─────────── PROJECTS GRID ─────────── */")
    b = out.index("/* ─────────── FOOTER ─────────── */", a)
    out = out[:a] + out[b:]
    a = out.index("/* ─────────── PROJECT CARD ACTIVE STATE ─────────── */")
    b = out.index("</style>", a)
    out = out[:a] + out[b:]
    out = re.sub(r"\n  \.(projects-section|projects-grid|project-card-body|project-card-title|project-card:hover)\s*\{[^}]*\}", "", out)
    out = out.replace('<style id="smt-search-css">', '<style id="smt-films2-css"></style>\n<style id="smt-search-css">', 1)
    out = out.replace('<meta name="author" content="Halil Bekar">',
                      '<script type="application/ld+json" id="smt-films2-ld"></script>\n<link rel="preconnect" href="https://i.ytimg.com">\n<link id="smt-films2-preload">\n<meta name="author" content="Halil Bekar">', 1)
    return out


PROTECTED = [  # regions that must be byte-identical before and after a render
    ("head SEO", "<title>", '<script type="application/ld+json">'),
    ("nav", '<nav class="site-nav"', '<main id="main"'),
    ("page header", '<section class="page-header">', "</section>"),
    ("footer", '<footer class="footer', "<!-- ═══ SITE SEARCH"),
    ("search", "<!-- ═══ SITE SEARCH", "<!-- SMT-CONSENT-START -->"),
    ("consent", "<!-- SMT-CONSENT-START -->", "</body>"),
]


def seg(s, start, end):
    i = s.index(start)
    return s[i:s.index(end, i)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="render", choices=["render", "catalog"])
    ap.add_argument("--check", action="store_true", help="render in memory and compare with the page; exit 1 on drift")
    ap.add_argument("--offline", action="store_true", help="catalog: use cached RSS files only")
    ap.add_argument("--data", default=os.path.join(ROOT, "data", "films"), help="data directory (default data/films)")
    ap.add_argument("--site", default=ROOT, help="site root used to read page titles, OG images, route stops, embeds")
    ap.add_argument("--page", default=os.path.join(ROOT, "projects.html"), help="template page")
    ap.add_argument("--out", default=None, help="output page (default: overwrite --page)")
    a = ap.parse_args()
    if a.cmd == "catalog":
        build_catalog(a.data, a.site, a.offline)
        return
    template = read(a.page)
    out, stats = render(a.data, a.site, template)
    for name, s0, s1 in PROTECTED:
        assert seg(template, s0, s1) == seg(out, s0, s1), f"protected block changed: {name}"
    target = a.out or a.page
    if a.check:
        current = read(target) if os.path.exists(target) else ""
        if current == out:
            print(f"FILMS PAGE: PASS ({stats['films']} films, {stats['places']} places, in sync with data/films)")
            sys.exit(0)
        print("FILMS PAGE: BLOCKED (projects.html differs from data/films; run python3 build-films.py)")
        sys.exit(1)
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
    open(target, "w", encoding="utf-8").write(out)
    print(f"wrote {target}: {stats['films']} films, {stats['places']} places, {stats['described']} with description"
          + (", converted from legacy page" if stats["legacy_converted"] else ""))
    if stats["unplaced"]:
        print("  no verified place:", "; ".join(stats["unplaced"]))
    if stats["undescribed"]:
        print("  no English description (none invented):", "; ".join(stats["undescribed"]))


if __name__ == "__main__":
    main()
