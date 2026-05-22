#!/usr/bin/env python3
"""
Show Me Turkiye - Search index builder (inline edition)
========================================================
Scans cities/, routes/, blog/ and rebuilds the SEARCH_DATA list that the
search uses. The search CSS and JS are embedded INLINE in every page (inside
<style id="smt-search-css"> and <script id="smt-search-js"> blocks), so the
search works everywhere - on the live site and when opening a file locally.

This script keeps every page's inline copy in sync. When you add a new page,
just run:   python build-search.py

It also keeps assets/search.js (the master copy) up to date for reference.
"""

import re, json, html as ihtml, sys
from pathlib import Path

SKIP = {"cookies","privacy","terms","contact","press","about",
        "first-guide","blog","explore","projects","index"}
FOLDER_CATEGORY = {"cities":"City","routes":"Route","blog":"Journal"}
ROUTE_SLUGS = {"aegean-coast-escape","black-sea-highlands","eastern-heritage",
    "family-adventure","first-time-turkey","foodie-anatolian-trail","grand-tour",
    "luxury-turkey","off-the-beaten-path","photographers-turkey","romantic-getaway","spiritual-anatolia"}
JOURNAL_SLUGS = {"aladaglar","top-10-places-to-visit-in-Turkey","when-is-the-best-time-to-visit-turkiye"}
META_LABEL = {"Route":"Itinerary","City":"City guide","Journal":"Journal"}
STOPWORDS = {"discover","turkey","turkiye","türkiye","this","that","with","from","your","their",
    "where","which","these","about","into","over","under","best","most","also","they","what",
    "when","will","here","there","some","very","just","travel","guide","things","place","places","visit"}

def fm(t,*ps):
    for p in ps:
        m=re.search(p,t)
        if m: return ihtml.unescape(m.group(1)).strip()
    return ""
def title_of(h):
    t=fm(h,r"<title>([^<]*)</title>")
    return re.split(r"\s*[|·]\s*Show Me",t)[0].strip() if t else ""
def img_of(h):
    imgs=re.findall(r"https://img\.showmeturkiye\.com/[^\"'\s)]+\.(?:jpg|jpeg|png|webp)",h)
    nl=[i for i in imgs if "logo" not in i.lower()]
    return nl[0] if nl else ""
def tags_of(title,desc,slug):
    words=re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]{4,}",(title+" "+desc).lower())
    out=[slug.replace("-"," ")]
    for w in words:
        if w not in STOPWORDS and w not in out: out.append(w)
    return out[:10]

def discover():
    root=Path(".")
    folders=[f for f in FOLDER_CATEGORY if (root/f).is_dir()]
    if folders:
        for folder in folders:
            cat=FOLDER_CATEGORY[folder]
            for p in sorted((root/folder).glob("*.html")):
                if p.stem in SKIP: continue
                yield p,p.stem,cat,f"/{folder}/{p.stem}.html"
    else:
        for p in sorted(root.glob("*.html")):
            if p.stem in SKIP: continue
            if p.stem in ROUTE_SLUGS: cat,folder="Route","routes"
            elif p.stem in JOURNAL_SLUGS: cat,folder="Journal","blog"
            else: cat,folder="City","cities"
            yield p,p.stem,cat,f"/{folder}/{p.stem}.html"

def build_records():
    recs=[]
    for path,slug,cat,url in discover():
        h=path.read_text(encoding="utf-8")
        title=title_of(h)
        if not title:
            print(f"  ! skipped (no <title>): {path}"); continue
        desc=fm(h,r'<meta name="description" content="([^"]*)"',r'<meta property="og:description" content="([^"]*)"')
        recs.append({"id":slug,"category":cat,"title":title,"excerpt":desc[:150],
            "meta":META_LABEL.get(cat,""),"tags":tags_of(title,desc,slug),"img":img_of(h),"url":url})
    recs.sort(key=lambda r:(r["category"],r["title"].lower()))
    return recs

def main():
    print("Building search index ...")
    recs=build_records()
    data_line="const SEARCH_DATA = "+json.dumps(recs,ensure_ascii=False)+";"

    # 1) update master copy in assets/search.js (reference)
    master=Path("assets/search.js")
    if master.exists():
        old=master.read_text(encoding="utf-8")
        master.write_text(re.sub(r"const SEARCH_DATA = \[.*?\];",lambda m:data_line,old,count=1,flags=re.DOTALL),encoding="utf-8")

    # 2) update the inline copy embedded in every HTML page
    pages=list(Path(".").glob("*.html"))+list(Path(".").glob("*/*.html"))
    updated=0
    for p in pages:
        h=p.read_text(encoding="utf-8")
        if 'id="smt-search-js"' not in h: continue
        new=re.sub(r"const SEARCH_DATA = \[.*?\];",lambda m:data_line,h,count=1,flags=re.DOTALL)
        if new!=h:
            p.write_text(new,encoding="utf-8"); updated+=1

    from collections import Counter
    bc=Counter(r["category"] for r in recs)
    print(f"  OK  {len(recs)} pages indexed ({', '.join(f'{v} {k}' for k,v in sorted(bc.items()))})")
    print(f"      inline copies updated in {updated} pages")

if __name__=="__main__":
    main()
