#!/usr/bin/env python3
"""Crypto-IT site tool. Plain Python 3, no dependencies.

    python3 scripts/site.py sync      regenerate shared/auto blocks in all pages + sitemap.xml
    python3 scripts/site.py check     report problems (exit code 1 on errors); changes nothing
    python3 scripts/site.py new TYPE EN_PATH PL_PATH
                                      create a new page pair from templates/pages/TYPE.{en,pl}.html

Pages are plain HTML in docs/. A page takes part if its <html> tag has data-type:

    <html lang="en" data-type="article" data-translation="/pl/proste/szyfr-playfair.html"
          data-published="2020-03-09" data-updated="2026-10-30">

Marked blocks are rewritten by `sync` (never edit their contents by hand):

    <!-- shared:NAME -->…<!-- /shared:NAME -->   copy of templates/partials/{lang}/NAME.html
                                                 (or templates/partials/NAME.html)
    <!-- auto:NAME -->…<!-- /auto:NAME -->       generated from the page and the section tree

auto blocks: meta, jsonld, breadcrumbs, dates, pager, share, index.
The section tree is the <ul> in templates/partials/{lang}/sidebar-SECTION.html; its order defines
breadcrumbs, previous/next links and the lists on section pages.
"""

import html
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit, unquote

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
PARTIALS = ROOT / 'templates' / 'partials'
PAGE_TEMPLATES = ROOT / 'templates' / 'pages'
SITE = 'https://www.crypto-it.net'
SITE_NAME = 'Crypto-IT'
AUTHOR = {'en': 'Chris Kowalczyk', 'pl': 'Krzysztof Kowalczyk'}
DEFAULT_IMAGE = '/assets/img/og-default.png'

LANG = {
    'en': {
        'dir': 'eng', 'locale': 'en_GB', 'home': 'Home', 'published': 'Published', 'updated': 'Updated',
        'prev': '← Previous', 'next': 'Next →', 'share': 'Share:', 'crumbs': 'Breadcrumbs',
        'pager': 'Previous and next article', 'about': '/eng/about/',
        'months': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                   'September', 'October', 'November', 'December'],
    },
    'pl': {
        'dir': 'pl', 'locale': 'pl_PL', 'home': 'Strona główna', 'published': 'Opublikowano',
        'updated': 'Zaktualizowano', 'prev': '← Poprzedni', 'next': 'Następny →', 'share': 'Udostępnij:',
        'crumbs': 'Ścieżka nawigacji', 'pager': 'Poprzedni i następny artykuł', 'about': '/pl/ostronie/',
        'months': ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca', 'lipca', 'sierpnia',
                   'września', 'października', 'listopada', 'grudnia'],
    },
}
TYPES = {'article', 'news', 'tool', 'section', 'home', 'page'}
BLOCK = re.compile(r'(?P<indent>[ \t]*)<!-- (?P<kind>shared|auto):(?P<name>[\w-]+) -->.*?<!-- /(?P=kind):(?P=name) -->', re.S)


# ---------- Pages ----------

class Page:
    def __init__(self, file):
        self.file = file
        self.text = file.read_text(encoding='utf-8')
        rel = file.relative_to(DOCS).as_posix()
        self.path = '/' + (rel[:-len('index.html')] if rel.endswith('index.html') else rel)
        m = re.search(r'<html\b([^>]*)>', self.text)
        self.attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1))) if m else {}
        self.lang = self.attrs.get('lang', '')
        self.type = self.attrs.get('data-type')
        self.translation = self.attrs.get('data-translation')
        self.published = self.attrs.get('data-published')
        self.updated = self.attrs.get('data-updated')
        parts = self.path.strip('/').split('/')
        self.section = self.attrs.get('data-section') or (parts[1] if len(parts) > 2 or self.path.endswith('/') and len(parts) == 2 else None)

    @property
    def url(self):
        return SITE + self.path

    def title(self):
        m = re.search(r'<title>(.*?)</title>', self.text, re.S)
        return html.unescape(m.group(1).strip()) if m else ''

    def short_title(self):
        return re.sub(r'\s*\|\s*Crypto-IT\s*$', '', self.title())

    def description(self):
        m = re.search(r'<meta name="description" content="([^"]*)"', self.text)
        return html.unescape(m.group(1)) if m else ''

    def h1(self):
        m = re.search(r'<h1[^>]*>(.*?)</h1>', self.text, re.S)
        return html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''


def load_pages():
    pages = {}
    for f in sorted(DOCS.rglob('*.html')):
        p = Page(f)
        if p.type:
            pages[p.path] = p
    return pages


# ---------- Partials and section trees ----------

def partial(lang, name):
    for f in (PARTIALS / lang / f'{name}.html', PARTIALS / f'{name}.html'):
        if f.exists():
            text = f.read_text(encoding='utf-8').strip('\n')
            return re.sub(r'\{\{include:([\w-]+)\}\}', lambda m: partial(lang, m.group(1)), text)
    raise SystemExit(f'Missing partial: templates/partials/{lang}/{name}.html')


class Node:
    def __init__(self, href, text, parent=None):
        self.href, self.text, self.parent, self.children = href, text, parent, []

    def walk(self):
        for c in self.children:
            yield c
            yield from c.walk()


class TreeParser(HTMLParser):
    """Reads <h2><a href=SECTION>Title</a></h2> and the nested <ul> of a sidebar partial."""

    def __init__(self):
        super().__init__()
        self.root = Node(None, '')
        self.stack = [self.root]
        self.current = None
        self.in_a = False
        self.in_h2 = False
        self.a_href = None
        self.a_text = ''
        self.depth = 0          # <ul> nesting; links outside the lists are ignored

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'h2':
            self.in_h2 = True
        elif tag == 'ul':
            self.depth += 1
            if self.depth > 1:
                self.stack.append(self.current)
        elif tag == 'a':
            self.in_a, self.a_href, self.a_text = True, a.get('href'), ''

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.in_h2 = False
        elif tag == 'ul':
            self.depth -= 1
            if self.depth >= 1:
                self.current = self.stack.pop()
        elif tag == 'a' and self.in_a:
            self.in_a = False
            text = ' '.join(self.a_text.split())
            if self.in_h2:
                self.root.href, self.root.text = self.a_href, text
            elif self.depth:
                self.current = Node(self.a_href, text, self.stack[-1])
                self.stack[-1].children.append(self.current)

    def handle_data(self, data):
        if self.in_a:
            self.a_text += data


_trees = {}


def tree(lang, section):
    key = (lang, section)
    if key not in _trees:
        f = PARTIALS / lang / f'sidebar-{section}.html'
        if not section or not f.exists():
            _trees[key] = None
        else:
            p = TreeParser()
            p.feed(partial(lang, f'sidebar-{section}'))
            _trees[key] = p.root
    return _trees[key]


def find(root, path):
    if root is None:
        return None
    if root.href == path:
        return root
    return next((n for n in root.walk() if n.href == path), None)


# ---------- Generated blocks ----------

def esc(s):
    return html.escape(s, quote=True)


def human_date(lang, iso):
    y, m, d = map(int, iso.split('-'))
    return f'{d} {LANG[lang]["months"][m - 1]} {y}'


def trail(page):
    """[(href, text)] from the homepage to the page's parent."""
    L = LANG[page.lang]
    items = [(f'/{L["dir"]}/', L['home'])]
    root = tree(page.lang, page.section)
    if root is None or page.type == 'home':
        return items if page.type != 'home' else []
    node = find(root, page.path)
    if node is root:
        return items
    items.append((root.href, root.text))
    ancestors = []
    n = node.parent if node else None
    while n is not None and n is not root:
        ancestors.append((n.href, n.text))
        n = n.parent
    return items + ancestors[::-1]


def gen_meta(page, pages):
    L = LANG[page.lang]
    lines = [f'<link rel="canonical" href="{page.url}">']
    if page.translation:
        en, pl = (page.path, page.translation) if page.lang == 'en' else (page.translation, page.path)
        lines += [f'<link rel="alternate" hreflang="en" href="{SITE}{en}">',
                  f'<link rel="alternate" hreflang="pl" href="{SITE}{pl}">',
                  f'<link rel="alternate" hreflang="x-default" href="{SITE}{en}">']
    image = page.attrs.get('data-image', DEFAULT_IMAGE)
    og_type = 'article' if page.type in ('article', 'news', 'tool') else 'website'
    lines += [f'<meta property="og:type" content="{og_type}">',
              f'<meta property="og:site_name" content="{SITE_NAME}">',
              f'<meta property="og:title" content="{esc(page.short_title())}">',
              f'<meta property="og:description" content="{esc(page.description())}">',
              f'<meta property="og:url" content="{page.url}">',
              f'<meta property="og:image" content="{SITE}{image}">',
              f'<meta property="og:locale" content="{L["locale"]}">',
              '<meta name="twitter:card" content="summary">']
    return '\n'.join(lines)


def gen_jsonld(page, pages):
    graph = []
    crumbs = trail(page)
    if page.type in ('article', 'news', 'tool'):
        art = {'@type': 'NewsArticle' if page.type == 'news' else 'TechArticle',
               'headline': page.h1(), 'description': page.description(), 'inLanguage': page.lang}
        if page.published:
            art['datePublished'] = page.published
        if page.updated or page.published:
            art['dateModified'] = page.updated or page.published
        art['author'] = {'@type': 'Person', 'name': AUTHOR[page.lang], 'url': SITE + LANG[page.lang]['about']}
        art['publisher'] = {'@type': 'Organization', 'name': SITE_NAME, 'url': SITE + '/'}
        art['mainEntityOfPage'] = page.url
        graph.append(art)
    if page.type == 'home':
        graph.append({'@type': 'WebSite', 'name': SITE_NAME, 'url': page.url, 'inLanguage': page.lang})
    if crumbs:
        items = [{'@type': 'ListItem', 'position': i + 1, 'name': t, 'item': SITE + h} for i, (h, t) in enumerate(crumbs)]
        items.append({'@type': 'ListItem', 'position': len(items) + 1, 'name': page.h1()})
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': items})
    if not graph:
        return ''
    data = {'@context': 'https://schema.org', '@graph': graph}
    body = json.dumps(data, ensure_ascii=False, indent=2).replace('</', '<\\/')
    return f'<script type="application/ld+json">\n{body}\n</script>'


def gen_breadcrumbs(page, pages):
    crumbs = trail(page)
    if not crumbs:
        return ''
    items = '\n'.join(f'    <li><a href="{h}">{esc(t)}</a></li>' for h, t in crumbs)
    return f'<nav class="breadcrumbs" aria-label="{LANG[page.lang]["crumbs"]}">\n  <ol>\n{items}\n  </ol>\n</nav>'


def gen_dates(page, pages):
    L = LANG[page.lang]
    parts = []
    if page.published:
        parts.append(f'{L["published"]} <time datetime="{page.published}">{human_date(page.lang, page.published)}</time>')
    if page.updated and page.updated != page.published:
        parts.append(f'{L["updated"]} <time datetime="{page.updated}">{human_date(page.lang, page.updated)}</time>')
    return f'<p class="article__meta">{" · ".join(parts)}</p>' if parts else ''


def gen_pager(page, pages):
    root = tree(page.lang, page.section)
    order = [n for n in root.walk()] if root else []
    idx = next((i for i, n in enumerate(order) if n.href == page.path), None)
    if idx is None:
        return ''
    L = LANG[page.lang]
    links = []
    if idx > 0:
        n = order[idx - 1]
        links.append(f'  <a href="{n.href}" rel="prev"><small>{L["prev"]}</small>{esc(n.text)}</a>')
    if idx + 1 < len(order):
        n = order[idx + 1]
        links.append(f'  <a class="pager__next" href="{n.href}" rel="next"><small>{L["next"]}</small>{esc(n.text)}</a>')
    return f'<nav class="pager" aria-label="{L["pager"]}">\n' + '\n'.join(links) + '\n</nav>'


def gen_share(page, pages):
    u = quote(page.url, safe='')
    return (f'<p class="share">{LANG[page.lang]["share"]}\n'
            f'  <a href="https://www.linkedin.com/sharing/share-offsite/?url={u}" rel="noopener" target="_blank">LinkedIn</a>\n'
            f'  <a href="https://x.com/intent/post?url={u}" rel="noopener" target="_blank">X</a>\n'
            f'  <a href="https://www.facebook.com/sharer/sharer.php?u={u}" rel="noopener" target="_blank">Facebook</a>\n'
            '</p>')


def gen_index(page, pages):
    """Nested list of the articles below this page in the section tree."""
    node = find(tree(page.lang, page.section), page.path)
    if node is None or not node.children:
        return ''

    def render(n, depth):
        pad = '  ' * depth
        out = [f'{pad}<ul>']
        for c in n.children:
            badge = ' <span class="badge">online</span>' if c.href in pages and 'data-tool=' in pages[c.href].text else ''
            if c.children:
                out += [f'{pad}  <li><a href="{c.href}">{esc(c.text)}</a>{badge}', render(c, depth + 2), f'{pad}  </li>']
            else:
                out.append(f'{pad}  <li><a href="{c.href}">{esc(c.text)}</a>{badge}</li>')
        out.append(f'{pad}</ul>')
        return '\n'.join(out)

    return f'<div class="section-index">\n{render(node, 1)}\n</div>'


AUTO = {'meta': gen_meta, 'jsonld': gen_jsonld, 'breadcrumbs': gen_breadcrumbs, 'dates': gen_dates,
        'pager': gen_pager, 'share': gen_share, 'index': gen_index}


def gen_shared(page, name):
    text = partial(page.lang, name)
    other = 'pl' if page.lang == 'en' else 'en'
    text = text.replace('{{translation}}', page.translation or f'/{LANG[other]["dir"]}/')

    def mark(m):
        href = m.group(1)
        if 'site-nav' in text and name == 'header' and href != f'/{LANG[page.lang]["dir"]}/':
            current = page.path.startswith(href) if href.endswith('/') else page.path == href
            if current:
                return f'<a href="{href}" aria-current="true"'
        if name.startswith('sidebar-') and href == page.path:
            return f'<a href="{href}" aria-current="page"'
        return m.group(0)

    # Only links inside <nav class="site-nav"> or the sidebar list get marked
    return re.sub(r'<a href="([^"]+)"(?! hreflang)', mark, text)


def render(page, pages):
    def repl(m):
        indent, kind, name = m.group('indent'), m.group('kind'), m.group('name')
        if kind == 'shared':
            content = gen_shared(page, name)
        elif name in AUTO:
            content = AUTO[name](page, pages)
        else:
            raise SystemExit(f'{page.path}: unknown block auto:{name}')
        body = '\n'.join((indent + line) if line.strip() else '' for line in content.split('\n')) if content else ''
        return f'{indent}<!-- {kind}:{name} -->\n' + (body + '\n' if body else '') + f'{indent}<!-- /{kind}:{name} -->'

    return BLOCK.sub(repl, page.text)


# ---------- Sitemap ----------

def sitemap(pages):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p in sorted(pages.values(), key=lambda p: p.path):
        if 'noindex' in p.text[:3000]:
            continue
        out.append('  <url>')
        out.append(f'    <loc>{p.url}</loc>')
        if p.updated or p.published:
            out.append(f'    <lastmod>{p.updated or p.published}</lastmod>')
        if p.translation:
            out.append(f'    <xhtml:link rel="alternate" hreflang="{p.lang}" href="{p.url}"/>')
            other = 'pl' if p.lang == 'en' else 'en'
            out.append(f'    <xhtml:link rel="alternate" hreflang="{other}" href="{SITE}{p.translation}"/>')
        out.append('  </url>')
    out.append('</urlset>')
    return '\n'.join(out) + '\n'


# ---------- Check ----------

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.imgs, self.ids, self.h1 = [], [], [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.append(a['id'])
        if tag == 'h1':
            self.h1 += 1
        if tag == 'a' and a.get('href') is not None:
            self.links.append(a['href'])
        if tag in ('link', 'script') and (a.get('href') or a.get('src')) and a.get('rel') not in ('canonical', 'alternate'):
            self.links.append(a.get('href') or a.get('src'))
        if tag == 'img':
            self.imgs.append(a)
            self.links.append(a.get('src', ''))


def resolve(path):
    """docs file for a site path, or None."""
    f = DOCS / unquote(path).lstrip('/')
    if path.endswith('/') or f.is_dir():
        f = f / 'index.html'
    return f if f.exists() else None


def check(pages):
    errors, warnings = [], []
    parsed = {}
    for p in pages.values():
        lp = LinkParser()
        lp.feed(p.text)
        parsed[p.path] = lp
    for p in pages.values():
        lp = parsed[p.path]
        E = lambda msg: errors.append(f'{p.path}: {msg}')
        W = lambda msg: warnings.append(f'{p.path}: {msg}')
        if p.type not in TYPES:
            E(f'unknown data-type "{p.type}"')
        if p.lang not in LANG:
            E(f'lang must be en or pl, not "{p.lang}"')
            continue
        if not p.path.startswith(f'/{LANG[p.lang]["dir"]}/'):
            E(f'lang="{p.lang}" page outside /{LANG[p.lang]["dir"]}/')
        if render(p, pages) != p.text:
            E('generated blocks are out of date – run: python3 scripts/site.py sync')
        for need in ('auto:meta', 'shared:head', 'shared:header', 'shared:footer'):
            if f'<!-- {need} -->' not in p.text:
                E(f'missing block <!-- {need} -->')
        t, d = p.title(), p.description()
        if not t:
            E('missing <title>')
        elif len(t) > 70:
            W(f'title is {len(t)} characters (Google shows ~60)')
        if not d:
            E('missing meta description')
        elif not 50 <= len(d) <= 160:
            W(f'description is {len(d)} characters (aim for 50–160)')
        if lp.h1 != 1:
            E(f'{lp.h1} <h1> elements (need exactly 1)')
        for attr in ('published', 'updated'):
            v = getattr(p, attr)
            if v and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', v):
                E(f'data-{attr}="{v}" is not YYYY-MM-DD')
        if p.translation:
            other = pages.get(p.translation)
            if other is None:
                E(f'translation {p.translation} does not exist')
            elif other.translation != p.path:
                E(f'translation {p.translation} points to {other.translation}, not back here')
            elif other.lang == p.lang:
                E(f'translation {p.translation} has the same language')
        elif p.type != 'page':
            W('no translation (data-translation)')
        if 'TODO' in re.sub(r'<!--.*?-->', '', p.text, flags=re.S):
            E('contains TODO')
        if p.type in ('article', 'news', 'tool', 'section') and find(tree(p.lang, p.section), p.path) is None:
            W(f'not in the section tree templates/partials/{p.lang}/sidebar-{p.section}.html (no breadcrumbs/pager)')
        dup = {i for i in lp.ids if lp.ids.count(i) > 1}
        if dup:
            E(f'duplicate ids: {", ".join(sorted(dup))}')
        for img in lp.imgs:
            if 'alt' not in img:
                E(f'image without alt: {img.get("src")}')
            if not (img.get('width') and img.get('height')):
                W(f'image without width/height: {img.get("src")}')
        for href in lp.links:
            u = urlsplit(href)
            if u.scheme or href.startswith('//') or href.startswith(('mailto:', 'tel:')):
                if u.netloc.endswith('crypto-it.net'):
                    E(f'absolute link to own site: {href} (use /path)')
                continue
            if not u.path:
                if u.fragment and u.fragment not in lp.ids:
                    E(f'anchor #{u.fragment} not found on this page')
                continue
            if not u.path.startswith('/'):
                E(f'relative link {href} (use root-relative /eng/… paths)')
                continue
            target = resolve(u.path)
            if target is None:
                E(f'broken link: {href}')
            elif u.fragment and target.suffix == '.html':
                tp = target.relative_to(DOCS).as_posix()
                tpath = '/' + (tp[:-len('index.html')] if tp.endswith('index.html') else tp)
                ids = parsed[tpath].ids if tpath in parsed else None
                if ids is not None and u.fragment not in ids:
                    E(f'anchor not found: {href}')
    # Every node in a section tree must be a real page
    for lang in LANG:
        for f in sorted((PARTIALS / lang).glob('sidebar-*.html')):
            root = tree(lang, f.stem[len('sidebar-'):])
            for n in [root, *root.walk()]:
                if n.href not in pages:
                    errors.append(f'templates/partials/{lang}/{f.name}: link to missing page {n.href}')
    sm = DOCS / 'sitemap.xml'
    if not sm.exists() or sm.read_text(encoding='utf-8') != sitemap(pages):
        errors.append('docs/sitemap.xml is out of date – run: python3 scripts/site.py sync')
    return errors, warnings


# ---------- New page ----------

def new(kind, en_path, pl_path):
    today = date.today().isoformat()
    for lang, path, other in (('en', en_path, pl_path), ('pl', pl_path, en_path)):
        tpl = PAGE_TEMPLATES / f'{kind}.{lang}.html'
        if not tpl.exists():
            raise SystemExit(f'No template {tpl.relative_to(ROOT)}')
        if not path.startswith(f'/{LANG[lang]["dir"]}/') or not path.endswith(('.html', '/')):
            raise SystemExit(f'{path}: must start with /{LANG[lang]["dir"]}/ and end with .html or /')
        target = DOCS / (path.lstrip('/') + ('index.html' if path.endswith('/') else ''))
        if target.exists():
            raise SystemExit(f'{target.relative_to(ROOT)} already exists')
        text = tpl.read_text(encoding='utf-8')
        text = text.replace('{{translation}}', other).replace('{{today}}', today)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        print(f'created {target.relative_to(ROOT)}')
    print('Now: fill in the TODOs, add the pages to the section tree '
          '(templates/partials/{en,pl}/sidebar-SECTION.html) and run: python3 scripts/site.py sync')


# ---------- Main ----------

def main(argv):
    cmd = argv[1] if len(argv) > 1 else ''
    if cmd == 'sync':
        pages = load_pages()
        changed = 0
        for p in pages.values():
            new_text = render(p, pages)
            if new_text != p.text:
                p.file.write_text(new_text, encoding='utf-8')
                p.text = new_text
                changed += 1
        (DOCS / 'sitemap.xml').write_text(sitemap(pages), encoding='utf-8')
        print(f'{len(pages)} pages, {changed} updated, sitemap.xml written')
    elif cmd == 'check':
        pages = load_pages()
        errors, warnings = check(pages)
        quiet = '--errors' in argv
        if not quiet:
            for w in warnings:
                print('warning:', w)
        for e in errors:
            print('ERROR:  ', e)
        print(f'{len(pages)} pages, {len(errors)} errors, {len(warnings)} warnings')
        return 1 if errors else 0
    elif cmd == 'new' and len(argv) == 5:
        new(argv[2], argv[3], argv[4])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
