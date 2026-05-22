# Search index — how to keep it updated

The site search reads from a generated list inside `assets/search.js`.
You never edit that list by hand. The `build-search.py` script reads every
page under `cities/`, `routes/`, and `blog/` and rebuilds the list for you.

## When you add or rename a page

**Option 1 — run it yourself (one command)**

    python build-search.py

That scans the folders, regenerates the search list inside `assets/search.js`,
and prints a short report. Commit the changed `assets/search.js` with your
new page. Done.

**Option 2 — let GitHub do it automatically**

The workflow at `.github/workflows/build-search.yml` runs the script every
time you push a changed page to `main`. It rebuilds the index and commits it
back for you. You add the page, push, and the search updates itself. You can
also trigger it manually from the repo's **Actions** tab.

## What the script reads from each page

- title  → from `<title>` (the " | Show Me Turkiye" part is stripped)
- excerpt → from `<meta name="description">` (falls back to og:description)
- image  → first real photo on img.showmeturkiye.com (the logo is ignored)
- category → from the folder: cities/ → City, routes/ → Route, blog/ → Journal

So as long as a new page has a `<title>` and a meta description, it will be
indexed correctly with no extra work.

## Pages that are intentionally left out

Policy and listing pages are skipped on purpose: index, about, blog, explore,
contact, press, projects, cookies, privacy, terms, first-guide. To change that
list, edit the `SKIP` set at the top of `build-search.py`.

## If a route page has no search image

Route pages load their hero image via CSS/JS, so the script can't read it from
the HTML — those results show a coloured placeholder instead of a photo. If you
want real thumbnails for routes, add a normal `<meta property="og:image">` tag
with an img.showmeturkiye.com URL to each route page, then rebuild.
