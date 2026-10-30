#!/usr/bin/env python3
"""One-time conversion of the old crypto-it.net pages (crypto-old/) into docs/.

    python3 scripts/convert.py OLD_SITE_DIR      e.g. ../crypto-old/www.crypto-it.net

Writes the section trees (templates/partials/{en,pl}/sidebar-*.html), every article and section
page, and the images. Pages listed in KEEP (edited by hand) are not overwritten.
Run `python3 scripts/site.py sync` afterwards. Kept in the repository for reference only.
"""

import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
PARTIALS = ROOT / 'templates' / 'partials'

LANGS = {'eng': 'en', 'pl': 'pl'}
SECTIONS = {  # old folder -> section label used in the sidebar heading
    'eng': {'theory': 'Theory', 'simple': 'Simple ciphers', 'symmetric': 'Symmetric ciphers',
            'asymmetric': 'Asymmetric ciphers', 'attacks': 'Attacks', 'tools': 'Software', 'news': 'News'},
    'pl': {'teoria': 'Teoria', 'proste': 'Proste szyfry', 'symetryczne': 'Szyfry symetryczne',
           'asymetryczne': 'Szyfry asymetryczne', 'ataki': 'Ataki', 'narzedzia': 'Oprogramowanie',
           'aktualnosci': 'Aktualności'},
}
NEWS = {'news', 'aktualnosci'}
# Pages rewritten by hand – never overwritten
KEEP = {'/eng/simple/playfair-cipher.html', '/pl/proste/szyfr-playfair.html'}
# Old online. tools -> article anchors
ONLINE = {
    'eng/playfair.html': '/eng/simple/playfair-cipher.html#online',
    'eng/two-square.html': '/eng/simple/two-square.html#online',
    'eng/four-square.html': '/eng/simple/four-square.html#online',
    'eng/rail-fence.html': '/eng/simple/rail-fence-cipher.html#online',
    'eng/route.html': '/eng/simple/route-cipher.html#online',
    'eng/utf-8-converter.html': '/eng/theory/utf-8.html',
    'pl/playfair.html': '/pl/proste/szyfr-playfair.html#online',
    'pl/dwukwadratowy.html': '/pl/proste/dwukwadratowy.html#online',
    'pl/czterokwadratowy.html': '/pl/proste/czterokwadratowy.html#online',
    'pl/plotkowy.html': '/pl/proste/szyfr-plotkowy.html#online',
    'pl/sciezkowy.html': '/pl/proste/szyfr-sciezkowy.html#online',
    'pl/konwerter-utf-8.html': '/pl/teoria/utf-8.html',
}
# Articles with an embedded tool (templates/tools/NAME.{lang}.html), inserted before the 3rd <h2>
EMBED = {
    '/eng/simple/two-square.html': ('two-square', 'Try the two-square cipher online'),
    '/eng/simple/four-square.html': ('four-square', 'Try the four-square cipher online'),
    '/eng/simple/rail-fence-cipher.html': ('rail-fence', 'Try the rail fence cipher online'),
    '/eng/simple/route-cipher.html': ('route', 'Try the route cipher online'),
    '/pl/proste/dwukwadratowy.html': ('two-square', 'Wypróbuj szyfr dwukwadratowy online'),
    '/pl/proste/czterokwadratowy.html': ('four-square', 'Wypróbuj szyfr czterokwadratowy online'),
    '/pl/proste/szyfr-plotkowy.html': ('rail-fence', 'Wypróbuj szyfr płotkowy online'),
    '/pl/proste/szyfr-sciezkowy.html': ('route', 'Wypróbuj szyfr ścieżkowy online'),
}
# Polish genitive of foreign names was written with an apostrophe ("Kerckhoffs'a"); correct forms
PL_NAMES = [("Kerckhoffs'a", 'Kerckhoffsa'), ("Trithemius'a", 'Trithemiusa'), ("Beaufort'a", 'Beauforta'),
            ("Hebern'a", 'Heberna'), ("Lorenz'a", 'Lorenza'), ("Playfair'a", 'Playfaira'),
            ("Lyon'a", 'Lyona'), ("Vigenère'a", 'Vigenère’a'), ("Merkle'a", 'Merkle’a'),
            ("Diffie'go", 'Diffiego'), ("Hellman'a", 'Hellmana'), ("Myszkowski'ego", 'Myszkowskiego'),
            ("Rijndael'a", 'Rijndaela'), ("Friedman'a", 'Friedmana'), ("Kasiski'ego", 'Kasiskiego'),
            ("S-Box'ach", 'S-boksach'), ("S-Box'ów", 'S-boksów'), ("Feistel'a", 'Feistela'), ("Shannon'a", 'Shannona'),
            ("Vernam'a", 'Vernama'), ("Euler'a", 'Eulera'), ("Fermat'a", 'Fermata'), ("Bacon'a", 'Bacona')]

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
BLOCKS = {'p', 'div', 'ul', 'ol', 'table', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'section', 'pre', 'figure', 'object'}
INLINE_TAGS = {'a', 'span', 'sub', 'sup', 'b', 'strong', 'i', 'em', 'code', 'var', 'q', 'button', 'abbr', 'small', 'br', 'img', 'dfn', 'kbd'}

IMG_MAP = {}   # old Images/... path -> (new site path, width, height)


# ---------- Minimal DOM ----------

class El:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs or {}), parent, []

    def cls(self):
        return self.attrs.get('class', '').split()

    def has(self, c):
        return c in self.cls()

    def text(self):
        return ''.join(c if isinstance(c, str) else c.text() for c in self.children)

    def iter(self):
        for c in self.children:
            if isinstance(c, El):
                yield c
                yield from c.iter()

    def find(self, pred):
        return next((e for e in self.iter() if pred(e)), None)

    def findall(self, pred):
        return [e for e in self.iter() if pred(e)]

    def replace_with(self, *nodes):
        i = self.parent.children.index(self)
        for n in nodes:
            if isinstance(n, El):
                n.parent = self.parent
        self.parent.children[i:i + 1] = list(nodes)

    def unwrap(self):
        self.replace_with(*self.children)

    def remove(self):
        self.parent.children.remove(self)

    def append(self, n):
        if isinstance(n, El):
            n.parent = self
        self.children.append(n)


class Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = El('#root')
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        if tag in BLOCKS and self.cur.tag == 'p':   # implicit </p>
            self.cur = self.cur.parent
        if tag == 'li' and self.cur.tag == 'li':
            self.cur = self.cur.parent
        el = El(tag, [(k, v if v is not None else '') for k, v in attrs], self.cur)
        self.cur.children.append(el)
        if tag not in VOID:
            self.cur = el

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.cur = self.cur.parent

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, d):
        self.cur.children.append(d)

    def handle_entityref(self, name):
        self.cur.children.append(f'&{name};')

    def handle_charref(self, name):
        self.cur.children.append(f'&#{name};')

    def handle_comment(self, data):
        pass


def parse(text):
    b = Builder()
    b.feed(text)
    return b.root


def entity_text(s):
    """Normalise entities in a text node: decode everything except &, <, > and nbsp."""
    s = html.unescape(s)
    return html.escape(s, quote=False).replace('\xa0', '&nbsp;')


CONTAINERS = {'#root', 'div', 'section', 'aside', 'figure', 'ul', 'ol', 'table', 'thead', 'tbody', 'tfoot', 'tr', 'nav', 'header', 'dl'}


def attrs_html(el):
    return ''.join(f' {k}' if v == '' and k in ('hidden', 'popover', 'open', 'checked') else
                   f' {k}="{html.escape(html.unescape(v), quote=True)}"' for k, v in el.attrs.items())


def inline(node):
    """Element content on one line (whitespace collapsed)."""
    out = []
    for c in node.children:
        if isinstance(c, str):
            out.append(re.sub(r'\s+', ' ', c))
        elif c.tag in VOID:
            out.append(f'<{c.tag}{attrs_html(c)}>')
        elif c.tag == 'pre':
            out.append(serialize_pre(c))
        else:
            out.append(f'<{c.tag}{attrs_html(c)}>{inline(c).strip() if c.tag not in INLINE_TAGS else inline(c)}</{c.tag}>')
    return ''.join(out)


def serialize_pre(el):
    def raw(n):
        return ''.join(c if isinstance(c, str) else f'<{c.tag}{attrs_html(c)}>{raw(c)}</{c.tag}>' for c in n.children)
    return f'<pre{attrs_html(el)}>{raw(el)}</pre>'


def serialize(node, depth=0):
    """Block containers: one child per line, indented by two spaces per level."""
    pad = '  ' * depth
    lines = []
    run = []   # consecutive inline content directly inside a container (wrapped as one line)

    def flush():
        text = ''.join(run).strip()
        if text:
            lines.append(pad + text)
        run.clear()

    for c in node.children:
        if isinstance(c, str):
            run.append(re.sub(r'\s+', ' ', c))
        elif c.tag in INLINE_TAGS or c.tag in VOID:
            run.append(inline_wrap(c))
        else:
            flush()
            if c.tag == '#raw':
                lines += [pad + l for l in c.attrs['html'].split('\n')]
            elif c.tag == 'pre':
                lines.append(pad + serialize_pre(c))
            elif c.tag in CONTAINERS and any(isinstance(x, El) and x.tag not in INLINE_TAGS for x in c.children):
                lines.append(f'{pad}<{c.tag}{attrs_html(c)}>')
                lines.append(serialize(c, depth + 1))
                lines.append(f'{pad}</{c.tag}>')
            elif c.tag == 'li' and any(isinstance(x, El) and x.tag in CONTAINERS | {'p', 'pre'} for x in c.children):
                lines.append(f'{pad}<li{attrs_html(c)}>')
                lines.append(serialize(c, depth + 1))
                lines.append(f'{pad}</li>')
            else:
                lines.append(f'{pad}<{c.tag}{attrs_html(c)}>{inline(c).strip()}</{c.tag}>')
    flush()
    return '\n'.join(l for l in lines if l.strip())


def inline_wrap(el):
    holder = El('#x')
    holder.children = [el]
    return inline(holder)


# ---------- Paths ----------

def site_path(old_rel):
    """'eng/simple/index.html' -> '/eng/simple/'"""
    p = '/' + old_rel
    return p[:-len('index.html')] if p.endswith('/index.html') else p


def resolve_link(href, page_rel, lang):
    """Old link (relative or absolute) -> new root-relative link, or the original external URL."""
    href = href.strip()
    m = re.match(r'https?://(?:www\.)?online\.crypto-it\.net/?(.*)$', href)
    if m:
        target = ONLINE.get(m.group(1))
        return target or f'/{"eng" if lang == "en" else "pl"}/online-tools.html' if lang else target
    m = re.match(r'https?://(?:www\.)?crypto-it\.net(/.*)?$', href)
    if m:
        href = m.group(1) or '/'
        if href == '/':
            return f'/{"eng" if lang == "en" else "pl"}/'
    elif re.match(r'^[a-z]+:|^//|^#', href):
        return href
    path, _, frag = href.partition('#')
    path = path.split('?')[0]
    if not path.startswith('/'):
        base = page_rel.rsplit('/', 1)[0].split('/')
        for part in path.split('/'):
            if part == '..':
                base.pop()
            elif part not in ('.', ''):
                base.append(part)
        path = '/' + '/'.join(base)
    if path.startswith('/Images/'):
        return image(path[1:])[0] if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else file_copy(path[1:])
    if path.endswith('/index.html'):
        path = path[:-len('index.html')]
    return path + (f'#{frag}' if frag else '')


OLD = None   # set in main: Path of the old site


def image(old, max_width=1600):
    """Convert an old image once; returns (new path, width, height)."""
    if old in IMG_MAP:
        return IMG_MAP[old]
    from PIL import Image
    src = OLD / old
    if not src.exists():
        IMG_MAP[old] = ('/' + old, None, None)
        return IMG_MAP[old]
    rel = old[len('Images/'):].replace('_', '-').lower()
    stem = rel.rsplit('.', 1)[0]
    im = Image.open(src)
    if im.width > max_width:
        im = im.resize((max_width, round(im.height * max_width / im.width)), Image.LANCZOS)
    dst = DOCS / 'assets' / 'img' / (stem + '.webp')
    dst.parent.mkdir(parents=True, exist_ok=True)
    if im.mode == 'P':
        im = im.convert('RGBA')
    lossless = src.suffix.lower() in ('.png', '.gif')
    im.save(dst, 'WEBP', lossless=lossless, quality=82 if not lossless else 90, method=6)
    if lossless and dst.stat().st_size > 1.1 * src.stat().st_size:   # keep PNG when WebP is not smaller
        dst.unlink()
        dst = dst.with_suffix(src.suffix.lower())
        im.save(dst, optimize=True)
    IMG_MAP[old] = ('/' + dst.relative_to(DOCS).as_posix(), im.width, im.height)
    return IMG_MAP[old]


def file_copy(old):
    src = OLD / old
    dst = DOCS / 'assets' / 'files' / Path(old).name.replace('_', '-').lower()
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        dst.write_bytes(src.read_bytes())
    return '/' + dst.relative_to(DOCS).as_posix()


# ---------- Content transformation ----------

def slug(text):
    import unicodedata
    s = unicodedata.normalize('NFD', text.replace('ł', 'l').replace('Ł', 'L'))
    s = re.sub(r'[\u0300-\u036f]', '', s).lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:60] or 'section'


def code_text(el):
    """Old code blocks: text with <br> and &nbsp; -> plain text."""
    parts = []

    def walk(n):
        for c in n.children:
            if isinstance(c, str):
                parts.append(html.unescape(re.sub(r'[\r\n\t]+', '', c)))
            elif c.tag == 'br':
                parts.append('\n')
            else:
                walk(c)
    walk(el)
    text = ''.join(parts).replace('\xa0', ' ')
    lines = [l.rstrip() for l in text.split('\n')]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return html.escape('\n'.join(lines), quote=False)


SPAN_MAP = {  # old class -> new element (tag, class)
    'typed_in_text': ('span', 'term'), 'symbol_in_text': ('var', None), 'math_letter': ('span', 'math'),
    'translate': ('i', None), 'important': ('strong', None), 'inportant': ('strong', None),
    'highlighted': ('em', None), 'title': ('em', None), 'quote': ('em', None), 'institution': (None, None),
    'math_arrow': ('span', 'math'),
}


def transform(body, page_rel, lang, notes):
    """Clean an old content element in place."""
    # Sidebar notes ("show on the right") -> popover buttons; note contents collected separately
    for el in body.findall(lambda e: e.tag == 'span' and (e.has('show_on_the_right') or e.has('show_on_the_right_smaller'))):
        a = el.find(lambda e: e.tag == 'a')
        m = re.search(r"toggleVisibleInSidebar2\('div_opis_(?:boczny_)?([\w]+)'\)", a.attrs.get('onclick', '')) if a else None
        if m and m.group(1) in notes:
            btn = El('button', {'type': 'button', 'class': 'note-ref', 'popovertarget': f'note-{m.group(1).replace("_", "-")}'})
            btn.children = a.children
            el.replace_with(btn)
        else:
            el.unwrap()

    for el in list(body.iter()):
        tag, cls = el.tag, el.cls()
        if el.parent is None:
            continue
        # Headings: drop <header> wrappers, shift levels (h2 is the page title -> h1)
        if tag == 'header':
            el.unwrap()
        elif tag in ('h3', 'h4', 'h5'):
            el.tag = 'h' + str(int(tag[1]) - 1)
            if el.children and isinstance(el.children[-1], str):
                el.children[-1] = re.sub(r'\s*:\s*$', '', el.children[-1])
            if lang == 'pl':
                el.children = [pl_case(c) if isinstance(c, str) else c for c in el.children]
            el.attrs = {k: v for k, v in el.attrs.items() if k == 'id'}
        elif tag == 'section':
            el.unwrap()
        elif tag == 'div' and 'div_source_code' in cls:
            pre = El('pre')
            code = El('code')
            code.append(code_text(el))
            pre.append(code)
            el.replace_with(pre)
        elif tag == 'span' and cls and cls[0] in SPAN_MAP:
            new_tag, new_cls = SPAN_MAP[cls[0]]
            if new_tag is None:
                el.unwrap()
                continue
            el.tag = new_tag
            el.attrs = {'class': new_cls} if new_cls else {}
            if 'math_arrow' in cls:
                el.children = [re.sub(r'-&gt;|->', '→', c) if isinstance(c, str) else c for c in el.children]
        elif tag == 'div' and 'vertical_text' in cls:
            el.tag, el.attrs = 'span', {'class': 'vertical'}
        elif tag == 'tr':
            el.attrs = {'class': 'row-vertical'} if 'row_for_vertical_text' in cls else (
                {'class': 'row-border'} if 'tr_border_bottom' in cls else {})
        elif tag == 'td' or tag == 'th':
            keep = {k: v for k, v in el.attrs.items() if k in ('colspan', 'rowspan', 'scope')}
            if 'td_border_bottom' in cls:
                keep['class'] = 'cell-border'
            el.attrs = keep
        elif tag == 'table':
            new = ['table']
            if 'table_matrix' in cls:
                new.append('table--matrix')
            if 'table_force_no_borders' in cls:
                new.append('table--plain')
            if 'table_force_bold_edges' in cls:
                new.append('table--bold')
            if 'table_big' in cls:
                new.append('table--big')
            title = el.attrs.get('title')
            el.attrs = {'class': ' '.join(new)}
            if title and not el.find(lambda e: e.tag == 'caption'):
                el.attrs['aria-label'] = html.unescape(title)
            wrap = El('div', {'class': 'table-wrap'})
            el.replace_with(wrap)
            wrap.append(el)
        elif tag in ('ul', 'ol'):
            el.attrs = {'class': 'steps'} if 'list_algo' in cls else {}
        elif tag == 'div' and 'definition_region' in cls:
            el.tag, el.attrs = 'aside', {'class': 'definition'}
        elif tag == 'span' and 'definition_region_head' in cls:
            el.tag, el.attrs = 'p', {'class': 'definition__title'}
        elif tag == 'div' and 'definition_region_note' in cls:
            el.attrs = {'class': 'definition__note'}
        elif tag == 'div' and ('image' in cls or 'div_in_the_center_no_borders' in cls):
            el.tag = 'figure'
            el.attrs = {'class': 'figure' + (' figure--right' if 'right' in cls else '')}
            for cap in el.findall(lambda e: e.has('img_caption') or e.has('img_title')):
                cap.tag, cap.attrs = 'figcaption', {}
                if cap.parent is el and el.children.index(cap) < len(el.children) - 1:   # caption above -> below
                    el.children.remove(cap)
                    el.append(cap)
        elif tag == 'div' and (el.has('img_caption') or el.has('img_title')):
            el.tag, el.attrs = 'p', {'class': 'caption'}
        elif tag == 'img':
            src = el.attrs.get('src', '')
            old_img = re.sub(r'^(https?://(www\.)?crypto-it\.net/|(\.\./)+|/)', '', src)
            new, w, h = image(old_img) if old_img.startswith('Images/') else (src, None, None)
            alt = html.unescape(el.attrs.get('alt', '')).strip()
            if not alt:   # empty alt on content images: use the caption, else the file name
                fig = el.parent
                cap = fig.find(lambda e: e.has('img_caption') or e.has('img_title') or e.tag == 'figcaption') if fig else None
                alt = ' '.join(html.unescape(cap.text()).split()) if cap else \
                    re.sub(r'[-_]+', ' ', re.sub(r'[-_](eng|pl|en)$', '', Path(old_img).stem)).strip().capitalize()
            declared = re.match(r'(\d+)', el.attrs.get('width', ''))
            attrs = {'src': new, 'alt': alt}
            if w and h:
                dw = min(int(declared.group(1)), w) if declared else w
                attrs['width'], attrs['height'] = str(dw), str(round(h * dw / w))
            attrs['loading'] = 'lazy'
            el.attrs = attrs
        elif tag == 'a':
            href = el.attrs.get('href', '')
            if href.startswith('#') and el.attrs.get('onclick'):
                el.unwrap()
                continue
            new = resolve_link(href, page_rel, lang) if href else ''
            attrs = {'href': new}
            if el.attrs.get('id'):
                attrs['id'] = el.attrs['id']
            if re.match(r'https?://', new):
                attrs['rel'] = 'noopener'
                attrs['target'] = '_blank'
            el.attrs = attrs
        elif tag == 'object':
            fallback = el.find(lambda e: e.tag == 'p')
            el.replace_with(*(fallback and [fallback] or []))
        elif tag == 'br':
            # <br> directly after a figure or at block level is spacing only
            sib = el.parent.children
            i = sib.index(el)
            if el.parent.tag in ('#root', 'div', 'aside', 'figure', 'li') and (
                    i == 0 or isinstance(sib[i - 1], El) and sib[i - 1].tag in ('figure', 'div', 'table', 'pre', 'ul', 'ol')):
                el.remove()
        elif tag == 'p' and 'list_footer' in cls:
            el.remove()
        else:
            if tag in ('div', 'span', 'p', 'li', 'strong', 'b', 'i', 'sub', 'sup', 'caption', 'figcaption', 'h1', 'h2', 'h3', 'h4'):
                el.attrs = {k: v for k, v in el.attrs.items() if k == 'id' or (k == 'class' and tag in ('div',) and False)}
                if tag == 'b':
                    el.tag = 'strong'
                if tag == 'div' and not el.attrs and el.parent.tag in ('#root', 'div'):
                    el.unwrap()
    # Remove paragraphs that pointed to the old online. tools (the tool is embedded now)
    for p in body.findall(lambda e: e.tag == 'p'):
        if any(isinstance(a, El) and a.tag == 'a' and '#online' in a.attrs.get('href', '') for a in p.iter()) \
                and re.search(r'Crypto-Online', p.text()):
            p.remove()
    # Empty paragraphs
    for p in body.findall(lambda e: e.tag == 'p'):
        if not p.text().replace('&nbsp;', '').strip() and not p.find(lambda e: e.tag == 'img'):
            p.remove()
    # Heading ids (for the table of contents) – unique per page
    used = set(e.attrs['id'] for e in body.iter() if e.attrs.get('id'))
    for h in body.findall(lambda e: e.tag in ('h2', 'h3')):
        if 'id' not in h.attrs:
            base = slug(html.unescape(h.text()))
            s, n = base, 2
            while s in used:
                s, n = f'{base}-{n}', n + 1
            used.add(s)
            h.attrs['id'] = s


EXTRA_TREE = {
    'eng/theory/index.html': [('/eng/theory/binary-numbers.html', '/eng/theory/utf-8.html', 'UTF-8 encoding')],
    'pl/teoria/index.html': [('/pl/teoria/liczby-binarne.html', '/pl/teoria/utf-8.html', 'Kodowanie UTF-8')],
}
FIXES = [   # (page, old, new) – errors in the old content
    ('pl/teoria/protokoly-aplikacji.html', 'href="#partHandshake"', 'href="#SSLTLSHandshake"'),
]


# Proper names (prefixes) that stay capitalised in Polish headings
PL_PROPER = tuple('''Cezar Hill Playfair Vigen Trithemius Beaufort Merkle Diffie Hellman Lorenz Hebern Enigm Myszkowsk
    Kerckhoffs Nihilist Linux Windows Docker Jav Zoom Camellia Blowfish Twofish Serpent Salsa Feistel Vernam Shannon
    Wheatstone Baudot Polsk Rejewsk Turing Euklides Fermat Euler Bacon Juliusz Rzym Europ Ameryk Google Microsoft Apple
    Unix Python Wikipedia Bob Alice Alicj Ewa Ew Rivest Shamir Adleman Rijndael Daemen Rijmen Bernstein Schneier IBM
    Hilla Cezara Lyon Vespasian Wespazjan Kasisk Friedman Babbage Gronsfeld Kocher Bleichenbacher Wiener Mallory Trent
    Viktor Hayhanen Fiodor Enigma Bletchley Vigenère'''.split())


PL_APOSTROPHE = re.compile(r"\b([A-Z][a-zè]*[b-df-hj-np-tv-xzłi])'(a|owi|em|u|ego|emu|ach|ów|om|ami)\b")


def pl_names(text):
    """Kerckhoffs'a -> Kerckhoffsa: no apostrophe after a pronounced consonant or i (but Bruce'a, Vigenère’a)."""
    for a, b in PL_NAMES:
        text = text.replace(a, b)
    return PL_APOSTROPHE.sub(r'\1\2', text).replace("e'a", 'e’a').replace("e'em", 'e’em').replace("e'owi", 'e’owi')


def pl_case(text):
    """Polish headings use sentence case: lower-case capitalised words after the first,
    except proper names, acronyms (DES, AES-128) and English names after "ang."."""
    text = pl_names(text)
    out, english = [], False
    for i, w in enumerate(text.split(' ')):
        core = w.lstrip('(„"')
        if '(ang.' in w or w == 'ang.':
            english = True
        if english or i == 0 or not re.fullmatch(r'[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźżè’\'-]+[),.:;?!"”]*', core) \
                or core.startswith(PL_PROPER) or re.search(r'-[A-Z]', core):
            out.append(w)
        else:
            out.append(w.replace(core, core[0].lower() + core[1:], 1))
        if w.endswith(')'):
            english = False
    return ' '.join(out)


def tidy_text(markup, lang):
    """Text-level fixes after serialisation."""
    def fix_text(seg):
        if lang == 'en':
            # English doesn't need non-breaking spaces after articles; keep them around numbers
            seg = re.sub(r'&nbsp;(?!\d)', ' ', seg)
            seg = re.sub(r'(?<![\d\s])&nbsp;', ' ', seg)
        else:
            seg = pl_names(seg)
        return re.sub(r'[ \t]{2,}', ' ', seg)

    out, pos = [], 0
    # don't touch <pre> blocks or tags
    for m in re.finditer(r'<pre>.*?</pre>|<[^>]+>', markup, re.S):
        out.append(fix_text(markup[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(fix_text(markup[pos:]))
    return ''.join(out)


def indent(markup, n):
    """Prefix every line with n spaces, except lines inside <pre>."""
    pad = ' ' * n
    lines, in_pre = [], False
    for line in markup.split('\n'):
        lines.append(line if in_pre else pad + line if line.strip() else '')
        opened, closed = line.count('<pre'), line.count('</pre>')
        if opened > closed:
            in_pre = True
        elif closed > opened:
            in_pre = False
    return '\n'.join(lines)


# ---------- Page templates ----------

PAGE = '''<!doctype html>
<html lang="{lang}" data-type="{type}"{attrs}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <!-- auto:meta -->
  <!-- /auto:meta -->
  <!-- shared:head -->
  <!-- /shared:head -->
{extra_head}  <!-- auto:jsonld -->
  <!-- /auto:jsonld -->
</head>
<body>
  <!-- shared:header -->
  <!-- /shared:header -->
{main}
  <!-- shared:footer -->
  <!-- /shared:footer -->
</body>
</html>
'''

ARTICLE = '''  <div class="layout">
    <main id="main">
      <article>
        <!-- auto:breadcrumbs -->
        <!-- /auto:breadcrumbs -->
        <header>
          <h1 class="article__title">{h1}</h1>
{subtitle}          <!-- auto:dates -->
          <!-- /auto:dates -->
        </header>
        <div class="article__body">
{body}
        </div>
        <!-- auto:pager -->
        <!-- /auto:pager -->
        <!-- auto:share -->
        <!-- /auto:share -->
      </article>
    </main>
    <!-- shared:sidebar-{section} -->
    <!-- /shared:sidebar-{section} -->
  </div>'''

SECTION = '''  <div class="layout layout--wide">
    <main id="main">
      <!-- auto:breadcrumbs -->
      <!-- /auto:breadcrumbs -->
      <h1 class="article__title">{h1}</h1>
{body}
      <h2>{all_heading}</h2>
      <!-- auto:index -->
      <!-- /auto:index -->
    </main>
  </div>'''


def attr_str(**kw):
    return ''.join(f' data-{k}="{v}"' for k, v in kw.items() if v)


# ---------- Old page reading ----------

def read(old_file):
    return old_file.read_text(encoding='utf-8', errors='replace')


def meta(text, name):
    m = re.search(rf'<meta name="{name}" content="([^"]*)"', text)
    return html.unescape(m.group(1)).strip() if m else ''


def translation_of(text, page_rel):
    f = text[text.index('<div id="footer"'):] if '<div id="footer"' in text else text
    for m in re.finditer(r'href="([^"]*(?:/pl/|/eng/)[^"]*)"', f):
        target = resolve_link(m.group(1), page_rel, None)
        if target.split('/')[1] != page_rel.split('/')[0]:
            return target
    return None


def section_tree(old_dir, folder):
    """Footer tree of a section index page -> sidebar partial."""
    lang = LANGS[old_dir]
    rel = f'{old_dir}/{folder}/index.html'
    text = read(OLD / rel)
    f = text[text.index('<div id="footer"'):]
    m = re.search(r'<ul class="list_footer">(.*?)</section>', f, re.S)
    root = parse('<ul>' + m.group(1))
    items = []

    def walk(ul, depth):
        for li in [c for c in ul.children if isinstance(c, El) and c.tag == 'li']:
            a = li.find(lambda e: e.tag == 'a')
            label = ' '.join(html.unescape(a.text()).replace('\xa0', ' ').split())
            if lang == 'pl':
                label = pl_names(label)
            href = resolve_link(a.attrs['href'], rel, lang)
            items.append((depth, href, label))
            sub = next((c for c in li.children if isinstance(c, El) and c.tag == 'ul'), None)
            if sub:
                walk(sub, depth + 1)
    walk(root.children[0], 0)
    for after, href, label in EXTRA_TREE.get(rel, []):   # new pages (not on the old site)
        i = next(i for i, it in enumerate(items) if it[1] == after)
        items.insert(i + 1, (items[i][0], href, label))
    # Old PL tree: the first top-level entry ("substitution ciphers") linked to the transposition page
    if rel == 'pl/proste/index.html' and items[0][1] == '/pl/proste/szyfry-przestawieniowe.html':
        items[0] = (0, '/pl/proste/szyfry-podstawieniowe.html', 'Szyfry podstawieniowe')

    out = ['<aside class="sidebar" aria-labelledby="sidebar-title">',
           '  <div class="sidebar__inner">',
           f'    <h2 id="sidebar-title"><a href="/{old_dir}/{folder}/">{html.escape(SECTIONS[old_dir][folder])}</a></h2>']

    def emit(i, depth, pad):
        lines = [f'{pad}<ul>']
        while i < len(items) and items[i][0] == depth:
            _, href, label = items[i]
            if i + 1 < len(items) and items[i + 1][0] > depth:
                lines.append(f'{pad}  <li><a href="{href}">{html.escape(label)}</a>')
                sub, i = emit(i + 1, depth + 1, pad + '    ')
                lines += sub
                lines.append(f'{pad}  </li>')
            else:
                lines.append(f'{pad}  <li><a href="{href}">{html.escape(label)}</a></li>')
                i += 1
        lines.append(f'{pad}</ul>')
        return lines, i

    lines, _ = emit(0, 0, '    ')
    out += lines
    out += ['    {{include:promo}}', '  </div>', '</aside>']
    dst = PARTIALS / lang / f'sidebar-{folder}.html'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text('\n'.join(out) + '\n', encoding='utf-8')
    return [h for _, h, _ in items]


def embed_tool(path, body, lang):
    """Insert the tool before the security heading (3rd <h2>) and a jump link after the first paragraph."""
    name, label = EMBED[path]
    tool = (ROOT / 'templates' / 'tools' / f'{name}.{lang}.html').read_text(encoding='utf-8').strip('\n')
    heads = [m.start() for m in re.finditer(r'^<h2 id=', body, re.M)]
    at = heads[2] if len(heads) > 2 else len(body)
    body = body[:at] + tool + '\n' + body[at:]
    return body.replace('<!-- shared:toc -->', f'<p><a href="#online">{label} ↓</a></p>\n<!-- shared:toc -->', 1), \
        f'  <script src="/assets/js/tools/{name}.js" type="module"></script>\n'


def convert_article(rel, text, lang, folder, translation):
    doc = parse(text)
    content = doc.find(lambda e: e.attrs.get('id') == 'content')
    # sidebar notes
    notes = {}
    for d in doc.findall(lambda e: e.tag == 'div' and e.has('div_opis_boczny')):
        bottom = d.find(lambda e: e.has('bottom')) or d
        notes[re.sub(r'^div_opis_(boczny_)?', '', d.attrs['id'])] = bottom
    sec = content.find(lambda e: e.tag == 'section') or content
    head = sec.find(lambda e: e.tag == 'header')
    h2 = head.find(lambda e: e.tag == 'h2')
    byline = head.find(lambda e: e.has('byline'))
    h1 = html.unescape(h2.text()).replace('\xa0', ' ').strip()
    subtitle = html.unescape(byline.text()).strip() if byline else ''
    if lang == 'pl':
        h1, subtitle = pl_case(h1), pl_case(subtitle)
    head.remove()
    transform(sec, rel, lang, notes)
    used_notes = {b.attrs['popovertarget'] for b in sec.findall(lambda e: e.tag == 'button')}
    first_p = next((c for c in sec.children if isinstance(c, El) and c.tag == 'p'), None)
    if first_p:   # table of contents after the first paragraph
        toc = El('#raw', {'html': '<!-- shared:toc -->\n<!-- /shared:toc -->'})
        sec.children.insert(sec.children.index(first_p) + 1, toc)
    body = serialize(sec)
    # popover notes at the end of the body
    for key, el in notes.items():
        nid = f'note-{key.replace("_", "-")}'
        if nid not in used_notes:
            continue
        transform(el, rel, lang, {})
        close = 'Close' if lang == 'en' else 'Zamknij'
        body += (f'\n<div class="note" id="{nid}" popover>\n{serialize(el, 1)}\n  '
                 f'<button type="button" class="note__close" popovertarget="{nid}" popovertargetaction="hide">{close}</button>\n</div>')
    body = tidy_text(body, lang)
    extra_head = ''
    if site_path(rel) in EMBED:
        body, extra_head = embed_tool(site_path(rel), body, lang)
    date = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', text)
    page_type = 'news' if folder in NEWS else 'article'
    main = ARTICLE.format(h1=html.escape(h1, quote=False), body=indent(body, 10), section=folder,
                          subtitle=f'          <p class="article__subtitle">{html.escape(subtitle, quote=False)}</p>\n' if subtitle else '')
    return PAGE.format(lang=lang, type=page_type, attrs=attr_str(translation=translation, published=date and date.group(1)),
                       title=title_of(text, lang), description=html.escape(description_of(text, h1, lang), quote=True),
                       extra_head=extra_head, main=main)


def convert_section(rel, text, lang, folder, translation):
    doc = parse(text)
    main_el = doc.find(lambda e: e.attrs.get('id') == 'main')
    container = main_el.find(lambda e: e.has('container')) or main_el
    h2 = container.find(lambda e: e.tag == 'h2')
    h1 = html.unescape(h2.text()).strip()
    if lang == 'pl':
        h1 = pl_case(h1)
    intro = [p for p in container.findall(lambda e: e.tag == 'p') if not p.find(lambda e: e.has('button'))
             and p.parent.tag == 'div' and p.parent.has('row')]
    cards = []
    for s in container.findall(lambda e: e.tag == 'section'):
        h3 = s.find(lambda e: e.tag == 'h3')
        a = s.find(lambda e: e.tag == 'a' and e.attrs.get('href'))
        img = s.find(lambda e: e.tag == 'img')
        p = s.find(lambda e: e.tag == 'p')
        if not (h3 and a):
            continue
        href = resolve_link(a.attrs['href'], rel, lang)
        src, w, h = image(re.sub(r'^(\.\./)+', '', img.attrs['src']), max_width=480) if img else (None, None, None)
        desc = tidy_text(inline(p).strip() if p else '', lang)
        desc = re.sub(r'</?span[^>]*>', '', desc)
        img_html = f'\n    <img src="{src}" width="{w}" height="{h}" alt="" loading="lazy">' if src else ''
        cards.append(f'  <li class="card">{img_html}\n    <div class="card__body">\n'
                     f'      <h2><a href="{href}">{html.escape(card_title(h3, lang), quote=False)}</a></h2>\n'
                     f'      <p>{desc}</p>\n    </div>\n  </li>')
    lead = ' '.join(tidy_text(inline(p).strip(), lang) for p in intro)
    lead = re.sub(r'</?span[^>]*>', '', lead)
    body = (f'<p class="article__lead">{lead}</p>\n' if lead else '') + '<ul class="cards">\n' + '\n'.join(cards) + '\n</ul>'
    date = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', text)
    main = SECTION.format(h1=html.escape(h1, quote=False), body=indent(body, 6),
                          all_heading='All articles' if lang == 'en' else 'Wszystkie artykuły')
    return PAGE.format(lang=lang, type='section', attrs=attr_str(translation=translation, published=date and date.group(1)),
                       title=title_of(text, lang), description=html.escape(description_of(text, h1, lang), quote=True),
                       extra_head='', main=main)


def card_title(h3, lang):
    t = ' '.join(html.unescape(h3.text()).split())
    return pl_case(t) if lang == 'pl' else t


def title_of(text, lang):
    t = html.unescape(re.search(r'<title>(.*?)</title>', text, re.S).group(1)).strip()
    parts = [p.strip() for p in t.split('|')]
    # "Caesar Cipher | Simple Substitution Ciphers | Crypto-IT" -> "Caesar Cipher | Crypto-IT"
    # (the middle part repeats the breadcrumbs and pushes the title over 60 characters)
    if len(parts) >= 3 and len(t) > 60:
        parts = [parts[0], parts[-1]]
    if lang == 'pl':
        parts = [pl_names(p) for p in parts]
    return html.escape(' | '.join(parts), quote=False)


def description_of(text, h1, lang='en'):
    d = meta(text, 'description')
    if lang == 'pl':
        d = pl_names(d)
    d = re.sub(r'\s+', ' ', d)
    d = d.replace('Caesarin', 'Caesar in')
    if len(d) > 160:   # cut at the last full sentence or word before 160 characters
        cut = d[:158]
        dot = cut.rfind('. ')
        d = cut[:dot + 1] if dot > 80 else cut[:cut.rfind(' ')].rstrip(',;:') + '…'
    return d


def main(argv):
    global OLD
    if len(argv) < 2 or (DOCS / 'eng' / 'theory' / 'introduction.html').exists() and '--force' not in argv:
        print(__doc__ + '\nPages already converted – this would overwrite edits. Add --force to run anyway.')
        return 2
    OLD = Path(argv[1]).resolve()
    for old_dir, folders in SECTIONS.items():
        for folder in folders:
            section_tree(old_dir, folder)
    # promo partials: Empik banner on Polish article pages only
    (PARTIALS / 'en' / 'promo.html').write_text('', encoding='utf-8')
    converted = 0
    for old_file in sorted(OLD.glob('*/**/*.html')):
        rel = old_file.relative_to(OLD).as_posix()
        old_dir = rel.split('/')[0]
        if old_dir not in LANGS or rel.count('/') < 2:
            continue   # homepages are written by hand
        lang = LANGS[old_dir]
        folder = rel.split('/')[1]
        path = site_path(rel)
        if path in KEEP:
            continue
        text = read(old_file)
        translation = translation_of(text, rel)
        if folder in ('about', 'ostronie'):
            continue   # merged with the online. author page by hand
        if '<div id="content"' in text:
            out = convert_article(rel, text, lang, folder, translation)
        else:
            out = convert_section(rel, text, lang, folder, translation)
        for page, a, b in FIXES:
            if page == rel:
                out = out.replace(a, b)
        dst = DOCS / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(out, encoding='utf-8')
        converted += 1
    print(f'{converted} pages converted, {len(IMG_MAP)} images')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
