# Adding and editing pages

Rules for people and AI agents. The site is plain HTML in `docs/`, published by GitHub Pages as-is.
One Python script (`scripts/site.py`, no dependencies) keeps the repeated parts consistent.

## The three commands

```sh
python3 scripts/site.py new TYPE /eng/PATH.html /pl/PATH.html   # create an EN + PL page pair
python3 scripts/site.py sync                                     # regenerate shared/auto blocks + sitemap.xml
python3 scripts/site.py check                                    # must end with "0 errors" before every commit
```

Preview: `cd docs && python3 -m http.server 8000`, open http://localhost:8000/eng/.

## Page types

| TYPE | Use for | Sidebar |
|---|---|---|
| `article` | an article in a section (`/eng/simple/…`) | yes |
| `news` | a news post in `/eng/news/`, `/pl/aktualnosci/` | yes |
| `tool` | an article with an online tool | yes |
| `section` | a section index (`/eng/NAME/`) – lists its articles automatically | no |
| `page` | about, privacy, hubs – no section | no |

The type and metadata are attributes of `<html>`:

```html
<html lang="en" data-type="article" data-translation="/pl/proste/szyfr-cezara.html"
      data-published="2020-03-09" data-updated="2026-11-02">
```

- `data-translation` – path of the other-language page. Both pages must point at each other.
- `data-published` – first publication date (`YYYY-MM-DD`). Never change it.
- `data-updated` – set to today's date when the content changes meaningfully (not for typos).

## Adding an article (step by step)

1. Create the pair, e.g. a new simple cipher:
   ```sh
   python3 scripts/site.py new article /eng/simple/atbash-cipher.html /pl/proste/szyfr-atbash.html
   ```
2. In both files replace every `TODO`:
   - `<title>`: `Name – what it is | Crypto-IT`, at most ~60 characters. Put the term people search for first.
   - `<meta name="description">`: 50–160 characters, a summary that makes people click.
   - `<h1>`: the name of the topic (exactly one `<h1>` per page).
   - `shared:sidebar-TODO-…`: the section's sidebar name (both the opening and closing comment),
     e.g. `sidebar-simple` / `sidebar-proste`. Sections: see `templates/partials/{en,pl}/sidebar-*.html`.
3. Add the page to the section tree in **both** languages, at the right place:
   `templates/partials/en/sidebar-simple.html` and `templates/partials/pl/sidebar-proste.html`.
   The tree's order defines breadcrumbs, previous/next links and the section page lists.
4. `python3 scripts/site.py sync`, then `python3 scripts/site.py check` until there are 0 errors.
5. Look at both pages in the browser (desktop and a narrow window).

A new section needs a `sidebar-NAME.html` in both languages, a `section` page pair, and a menu
entry in `templates/partials/{en,pl}/header.html`.

## Writing the content

- Headings inside the article: `<h2 id="…">` for main parts, `<h3 id="…">` below. Give every
  heading a short, unique, lower-case `id` (used by the table of contents and links).
  The table of contents appears automatically when there are 3 or more `<h2>`.
- Typical structure: lead paragraph (`class="article__lead"`), history/usage, algorithm, example,
  security, implementation.
- Links to other pages are root-relative: `<a href="/eng/attacks/brute-force.html">`.
  Never `../`, never `https://www.crypto-it.net/…`. External links: add `rel="noopener" target="_blank"`.
- Inline markup:
  - `<span class="term">ABC</span>` – letters, keys, ciphertext fragments
  - `<span class="math">E(x) = (x + n) mod 26</span>` or `<var>n</var>` – formulas and variables
  - `<code>…</code>` – code in text; code blocks: `<pre><code>…</code></pre>` (escape `<`, `>`, `&`).
    A copy button is added automatically.
  - `<i lang="la">…</i>` – foreign words
- Blocks:
  - Table: `<div class="table-wrap"><table class="table">…</table></div>`; letter grids: add
    `table--matrix`, or use `<table class="matrix">` for a 5×5 key table.
  - Matrix equation (one row, wraps on mobile): `<div class="equation"><span>K =</span><table class="eq-matrix"><tbody><tr><td>3</td><td>3</td></tr>…</tbody></table><span>×</span>…</div>`
    (example: `/eng/simple/hill-cipher.html`).
  - Image: `<figure class="figure"><img src="/assets/img/SECTION/name.webp" alt="…" width="…" height="…" loading="lazy"><figcaption>…</figcaption></figure>`.
    Every image needs a meaningful `alt` and its real `width`/`height`. Prefer WebP, max 1600 px wide.
  - Definition: `<aside class="definition"><p class="definition__title">Definition</p>…</aside>`
  - Side note: `<button type="button" class="note-ref" popovertarget="note-x">term</button>` in the text
    and `<div class="note" id="note-x" popover>…</div>` at the end of the article body.
- Polish: correct diacritics, sentence case in headings ("Szyfr płotkowy", not "Szyfr Płotkowy"),
  foreign names declined without an apostrophe after a consonant ("Kerckhoffsa", "Vigenère’a").
- Technical accuracy matters more than length. Check every example by computing it (or with the tool).

## Online tools

Each tool is an ES module in `docs/assets/js/tools/NAME.js` (pure functions + `mount()`), with
a test page `tests/NAME.test.html` and the HTML block in `templates/tools/NAME.{en,pl}.html`.

1. Write the module following `playfair.js` (exported pure functions, error class with codes,
   `data-role` elements, texts from `data-msg-*` attributes so one script serves both languages).
2. Write `tests/NAME.test.html` with known test vectors and add it to `tests/index.html`.
   Run: `python3 -m http.server 8001` in the repository root, open `/tests/NAME.test.html`
   – it must show `ALL PASSED`.
3. Create the article with `site.py new tool …`, paste the block from `templates/tools/` into the
   article (before the "Security" heading), set the script name in `<head>`.
4. Add the tool to `/eng/online-tools.html` and `/pl/narzedzia-online.html`.

## What not to do

- Don't edit inside `<!-- shared:… -->` or `<!-- auto:… -->` blocks – `sync` overwrites them.
  Change `templates/partials/` instead.
- Don't rename or move existing pages: their URLs are indexed by Google. GitHub Pages can't redirect.
- Don't add third-party scripts (analytics, widgets, fonts). AdSense is already in `shared:head`.
- Don't edit `docs/sitemap.xml` by hand.
- `scripts/convert.py` and `scripts/extra_pages.py` were used once for the migration; don't run them again
  (they would overwrite edited pages).
