#!/usr/bin/env python3
"""One-time: hand-written pages that did not exist on the old site (or were merged).
Creates them only if missing – after that, edit the HTML files directly."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
TOOLS = ROOT / 'templates' / 'tools'

# Same obfuscated address as on the old site (HTML entities)
EMAIL_HREF = ('&#109;&#097;&#105;&#108;&#116;&#111;:&#x63;&#x68;&#x72;&#x69;&#x73;&#x2e;&#x73;&#x72;&#x40;'
              '&#x68;&#x6f;&#x74;&#x6d;&#x61;&#x69;&#x6c;&#x2e;&#x63;&#x6f;&#x2e;&#x75;&#x6b;')


def page(lang, kind, translation, title, desc, main, extra='', dates='', section_attr=''):
    return f'''<!doctype html>
<html lang="{lang}" data-type="{kind}" data-translation="{translation}"{dates}{section_attr}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <!-- auto:meta -->
  <!-- /auto:meta -->
  <!-- shared:head -->
  <!-- /shared:head -->
{extra}  <!-- auto:jsonld -->
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


def wide(inner):
    return f'''  <div class="layout layout--wide">
    <main id="main">
{inner}
    </main>
  </div>'''


def prose(inner):
    return f'''  <div class="layout layout--wide">
    <main id="main" class="article__body page">
{inner}
    </main>
  </div>'''


def card(href, title, text, badge=''):
    b = f' <span class="badge">{badge}</span>' if badge else ''
    return f'''        <li class="card">
          <div class="card__body">
            <h3><a href="{href}">{title}</a>{b}</h3>
            <p>{text}</p>
          </div>
        </li>'''


def cards(items):
    return '      <ul class="cards">\n' + '\n'.join(card(*i) for i in items) + '\n      </ul>'


def indent(text, n):
    return '\n'.join((' ' * n + l) if l.strip() else '' for l in text.split('\n'))


PAGES = {}

# ---------- Homepages ----------
PAGES['eng/index.html'] = page('en', 'home', '/pl/', 'Crypto-IT – Cryptography Explained, Ciphers and Online Tools',
    'Learn cryptography: classical ciphers, AES, RSA, attacks and the theory behind them. Clear explanations, history, code and online cipher tools.',
    wide('''      <section class="hero">
        <h1 class="hero__title">Cryptography, explained</h1>
        <p class="hero__lead">From the Caesar cipher to AES and RSA: how ciphers work, how they are broken, and how to use them – with examples, code and tools you can try online.</p>
        <p class="hero__actions">
          <a class="button button--solid" href="/eng/theory/introduction.html">Start with the basics</a>
          <a class="button" href="/eng/online-tools.html">Online tools</a>
        </p>
      </section>
      <h2>Sections</h2>
''' + cards([
        ('/eng/theory/', 'Theory', 'Kerckhoffs’s principle, modular arithmetic, block cipher modes, MAC, one-way functions and more.'),
        ('/eng/simple/', 'Simple ciphers', 'Classical ciphers you can do by hand: Caesar, Playfair, Vigenère, transposition, Enigma.'),
        ('/eng/symmetric/', 'Symmetric ciphers', 'Stream and block ciphers: OTP, RC4, Salsa20, DES, AES, Blowfish, Camellia.'),
        ('/eng/asymmetric/', 'Asymmetric ciphers', 'Public-key cryptography: Merkle’s puzzles, Diffie–Hellman, RSA.'),
        ('/eng/attacks/', 'Attacks', 'Brute force, frequency analysis, man-in-the-middle, replay, KRACK and other attacks.'),
        ('/eng/tools/', 'Software', 'Cryptography in practice: JCA/JCE, security tokens, key-based authentication, Docker.'),
    ]) + '''
      <h2>Try it online</h2>
''' + cards([
        ('/eng/simple/playfair-cipher.html#online', 'Playfair cipher', 'Encrypt and decrypt with a 5×5 key table.', 'online'),
        ('/eng/simple/rail-fence-cipher.html#online', 'Rail fence cipher', 'Zigzag transposition with any number of rails.', 'online'),
        ('/eng/theory/utf-8.html#online', 'UTF-8 converter', 'Text to UTF-8 bytes (hex, binary, decimal) and back.', 'online'),
    ]) + '''
      <h2>News</h2>
      <ul class="link-list">
        <li><a href="/eng/news/top-10-vulnerabilities.html">Top 10 vulnerabilities</a></li>
        <li><a href="/eng/news/private-zoom-chats.html">Private Zoom chats are public</a></li>
        <li><a href="/eng/news/how-is-kernel-tested.html">How is the Linux kernel tested?</a></li>
        <li><a href="/eng/news/new-look.html">Crypto-IT new look</a></li>
      </ul>'''))

PAGES['pl/index.html'] = page('pl', 'home', '/eng/', 'Crypto-IT – kryptografia, szyfry i narzędzia online',
    'Kryptografia od podstaw: szyfry klasyczne, AES, RSA, ataki i teoria. Przystępne opisy, historia, kod i narzędzia do szyfrowania online.',
    wide('''      <section class="hero">
        <h1 class="hero__title">Kryptografia bez tajemnic</h1>
        <p class="hero__lead">Od szyfru Cezara do AES i RSA: jak działają szyfry, jak się je łamie i jak ich używać – z przykładami, kodem i narzędziami online.</p>
        <p class="hero__actions">
          <a class="button button--solid" href="/pl/teoria/wprowadzenie.html">Zacznij od podstaw</a>
          <a class="button" href="/pl/narzedzia-online.html">Narzędzia online</a>
        </p>
      </section>
      <h2>Działy</h2>
''' + cards([
        ('/pl/teoria/', 'Teoria', 'Zasada Kerckhoffsa, arytmetyka modularna, tryby szyfrów blokowych, MAC, funkcje jednokierunkowe i więcej.'),
        ('/pl/proste/', 'Proste szyfry', 'Szyfry klasyczne do użycia na kartce: Cezar, Playfair, Vigenère, szyfry przestawieniowe, Enigma.'),
        ('/pl/symetryczne/', 'Szyfry symetryczne', 'Szyfry strumieniowe i blokowe: OTP, RC4, Salsa20, DES, AES, Blowfish, Camellia.'),
        ('/pl/asymetryczne/', 'Szyfry asymetryczne', 'Kryptografia klucza publicznego: puzzle Merkle’a, Diffie–Hellman, RSA.'),
        ('/pl/ataki/', 'Ataki', 'Atak siłowy, analiza częstości, man-in-the-middle, metoda powtórzenia, KRACK i inne.'),
        ('/pl/narzedzia/', 'Oprogramowanie', 'Kryptografia w praktyce: JCA/JCE, tokeny, uwierzytelnianie kluczem, Docker.'),
    ]) + '''
      <h2>Wypróbuj online</h2>
''' + cards([
        ('/pl/proste/szyfr-playfair.html#online', 'Szyfr Playfair', 'Szyfrowanie i odszyfrowywanie z tabelą 5×5.', 'online'),
        ('/pl/proste/szyfr-plotkowy.html#online', 'Szyfr płotkowy', 'Przestawienie zygzakiem z dowolną liczbą wierszy.', 'online'),
        ('/pl/teoria/utf-8.html#online', 'Konwerter UTF-8', 'Tekst na bajty UTF-8 (hex, binarnie, dziesiętnie) i z powrotem.', 'online'),
    ]) + '''
      <h2>Aktualności</h2>
      <ul class="link-list">
        <li><a href="/pl/aktualnosci/10-najpopularniejszych-podatnosci.html">10 najpopularniejszych podatności</a></li>
        <li><a href="/pl/aktualnosci/prywatne-wiadomosci-w-zoom.html">Prywatne wiadomości w Zoom są publiczne</a></li>
        <li><a href="/pl/aktualnosci/jak-testuje-sie-kernel-linuxa.html">Jak testuje się kernel Linuxa?</a></li>
        <li><a href="/pl/aktualnosci/nowy-wyglad.html">Nowy wygląd Crypto-IT</a></li>
      </ul>'''))

# ---------- Online tools hub ----------
TOOLS_EN = [
    ('/eng/simple/playfair-cipher.html#online', 'Playfair cipher', 'Digraph substitution with a 5×5 table built from a keyword.'),
    ('/eng/simple/two-square.html#online', 'Two-square cipher', 'Two key tables, horizontal or vertical layout.'),
    ('/eng/simple/four-square.html#online', 'Four-square cipher', 'Four 5×5 tables, two of them built from keywords.'),
    ('/eng/simple/rail-fence-cipher.html#online', 'Rail fence cipher', 'Zigzag transposition with a chosen number of rails and offset.'),
    ('/eng/simple/route-cipher.html#online', 'Route cipher', 'Text written into a grid and read along a spiral.'),
    ('/eng/theory/utf-8.html#online', 'UTF-8 converter', 'Text ↔ UTF-8 bytes as hex, binary, decimal or HTML entities.'),
]
TOOLS_PL = [
    ('/pl/proste/szyfr-playfair.html#online', 'Szyfr Playfair', 'Podstawienie par liter z tabelą 5×5 utworzoną z klucza.'),
    ('/pl/proste/dwukwadratowy.html#online', 'Szyfr dwukwadratowy', 'Dwie tabele kluczy, układ poziomy lub pionowy.'),
    ('/pl/proste/czterokwadratowy.html#online', 'Szyfr czterokwadratowy', 'Cztery tabele 5×5, dwie utworzone z kluczy.'),
    ('/pl/proste/szyfr-plotkowy.html#online', 'Szyfr płotkowy', 'Przestawienie zygzakiem z wybraną liczbą wierszy i przesunięciem.'),
    ('/pl/proste/szyfr-sciezkowy.html#online', 'Szyfr ścieżkowy', 'Tekst wpisany w siatkę i odczytany po spirali.'),
    ('/pl/teoria/utf-8.html#online', 'Konwerter UTF-8', 'Tekst ↔ bajty UTF-8 jako hex, binarnie, dziesiętnie lub encje HTML.'),
]
PAGES['eng/online-tools.html'] = page('en', 'page', '/pl/narzedzia-online.html', 'Online Cipher Tools – Encrypt and Decrypt | Crypto-IT',
    'Free online tools: Playfair, two-square, four-square, rail fence and route ciphers, and a UTF-8 converter. Everything runs in your browser.',
    wide('''      <h1 class="article__title">Online cipher tools</h1>
      <p class="article__lead">Encrypt and decrypt classical ciphers or convert text to UTF-8. Each tool sits next to an explanation of the algorithm. Everything runs in your browser – the text you enter is not sent anywhere.</p>
''' + cards([(*t, 'online') for t in TOOLS_EN])))
PAGES['pl/narzedzia-online.html'] = page('pl', 'page', '/eng/online-tools.html', 'Szyfrowanie online – narzędzia | Crypto-IT',
    'Darmowe narzędzia online: szyfr Playfair, dwukwadratowy, czterokwadratowy, płotkowy i ścieżkowy oraz konwerter UTF-8. Działają w przeglądarce.',
    wide('''      <h1 class="article__title">Narzędzia online</h1>
      <p class="article__lead">Szyfruj i odszyfrowuj szyframi klasycznymi albo zamieniaj tekst na UTF-8. Każde narzędzie znajduje się obok opisu algorytmu. Wszystko działa w&nbsp;przeglądarce – wpisany tekst nie jest nigdzie wysyłany.</p>
''' + cards([(*t, 'online') for t in TOOLS_PL])))

# ---------- UTF-8 ----------
def utf8_article(lang):
    tool = indent((TOOLS / f'utf-8.{lang}.html').read_text(encoding='utf-8').strip('\n'), 10)
    if lang == 'en':
        h1, sub, body = 'UTF-8 Encoding', 'How text becomes bytes', f'''          <p class="article__lead">UTF-8 is the character encoding used by almost every web page, file format and network protocol today. It stores each Unicode character as one to four bytes, and plain ASCII text stays exactly the same.</p>
          <p><a href="#online">Convert text to UTF-8 online ↓</a></p>
          <!-- shared:toc -->
          <!-- /shared:toc -->
          <h2 id="unicode">Unicode and encodings</h2>
          <p>Unicode assigns a number, called a <em>code point</em>, to every character: <span class="term">A</span> is U+0041, <span class="term">ł</span> is U+0142, <span class="term">€</span> is U+20AC and the emoji 😀 is U+1F600. An <em>encoding</em> defines how these numbers are stored as bytes. UTF-8, designed by Ken Thompson and Rob Pike in 1992, is the most common one; others are UTF-16 and UTF-32.</p>
          <h2 id="algorithm">How UTF-8 works</h2>
          <p>The number of bytes depends on the size of the code point. The first byte says how many bytes follow; every following byte starts with the bits <span class="term">10</span>:</p>
          <div class="table-wrap">
            <table class="table">
              <thead><tr><th>Code points</th><th>Bytes</th><th>Bit pattern</th></tr></thead>
              <tbody>
                <tr><td>U+0000 – U+007F</td><td>1</td><td><code>0xxxxxxx</code></td></tr>
                <tr><td>U+0080 – U+07FF</td><td>2</td><td><code>110xxxxx 10xxxxxx</code></td></tr>
                <tr><td>U+0800 – U+FFFF</td><td>3</td><td><code>1110xxxx 10xxxxxx 10xxxxxx</code></td></tr>
                <tr><td>U+10000 – U+10FFFF</td><td>4</td><td><code>11110xxx 10xxxxxx 10xxxxxx 10xxxxxx</code></td></tr>
              </tbody>
            </table>
          </div>
          <p>For example, <span class="term">ł</span> (U+0142, binary <span class="term">101 0100 0010</span>) needs two bytes: the bits are split into <span class="term">00101</span> and <span class="term">000010</span>, giving <span class="term">11000101 10000010</span>, that is <span class="term">C5 82</span> in hexadecimal. The euro sign is <span class="term">E2 82 AC</span> and 😀 is <span class="term">F0 9F 98 80</span>.</p>
          <h2 id="properties">Why UTF-8 won</h2>
          <ul>
            <li><strong>ASCII compatible:</strong> English text and source code look the same as in ASCII.</li>
            <li><strong>Self-synchronising:</strong> a reader can find the start of the next character from any position, because continuation bytes always start with <span class="term">10</span>.</li>
            <li><strong>No byte order problems:</strong> unlike UTF-16, UTF-8 is a sequence of single bytes, so no byte order mark (BOM) is needed.</li>
          </ul>
          <p>Not every byte sequence is valid UTF-8. Decoders must reject, for example, a lone continuation byte, a truncated sequence or an "overlong" encoding (such as <span class="term">C0 AF</span> for <span class="term">/</span>). Accepting overlong forms has led to real security holes, because filters checking for <span class="term">/</span> or <span class="term">..</span> did not recognise them.</p>
{tool}
          <h2 id="in-practice">UTF-8 in practice</h2>
          <p>HTML pages declare it with <code>&lt;meta charset="utf-8"&gt;</code>. In JavaScript, <code>new TextEncoder().encode(text)</code> returns the UTF-8 bytes of a string and <code>new TextDecoder('utf-8', {{ fatal: true }})</code> decodes them, throwing an error on invalid input – the tool above works this way. Python offers <code>text.encode('utf-8')</code> and <code>data.decode('utf-8')</code>.</p>
          <p>Encodings matter in cryptography too: ciphers and <a href="/eng/theory/one-way-function.html">hash functions</a> work on bytes, not characters, so the same text encoded differently gives a different ciphertext or hash. See also <a href="/eng/theory/binary-numbers.html">binary numbers</a> and <a href="/eng/theory/notation-of-numbers.html">notation of numbers</a>.</p>'''
    else:
        h1, sub, body = 'Kodowanie UTF-8', 'Jak tekst staje się bajtami', f'''          <p class="article__lead">UTF-8 to kodowanie znaków używane dziś przez niemal wszystkie strony internetowe, formaty plików i protokoły sieciowe. Każdy znak Unicode zapisuje jako od jednego do czterech bajtów, a&nbsp;zwykły tekst ASCII pozostaje bez zmian.</p>
          <p><a href="#online">Zamień tekst na UTF-8 online ↓</a></p>
          <!-- shared:toc -->
          <!-- /shared:toc -->
          <h2 id="unicode">Unicode i kodowania</h2>
          <p>Unicode przypisuje każdemu znakowi liczbę, tzw. <em>punkt kodowy</em>: <span class="term">A</span> to U+0041, <span class="term">ł</span> to U+0142, <span class="term">€</span> to U+20AC, a&nbsp;emoji 😀 to U+1F600. <em>Kodowanie</em> określa, jak te liczby zapisać w&nbsp;bajtach. Najpopularniejszym kodowaniem jest UTF-8, opracowane przez Kena Thompsona i&nbsp;Roba Pike’a w&nbsp;1992 roku; inne to UTF-16 i&nbsp;UTF-32.</p>
          <h2 id="algorytm">Jak działa UTF-8</h2>
          <p>Liczba bajtów zależy od wielkości punktu kodowego. Pierwszy bajt informuje, ile bajtów następuje po nim; każdy kolejny bajt zaczyna się od bitów <span class="term">10</span>:</p>
          <div class="table-wrap">
            <table class="table">
              <thead><tr><th>Punkty kodowe</th><th>Bajty</th><th>Układ bitów</th></tr></thead>
              <tbody>
                <tr><td>U+0000 – U+007F</td><td>1</td><td><code>0xxxxxxx</code></td></tr>
                <tr><td>U+0080 – U+07FF</td><td>2</td><td><code>110xxxxx 10xxxxxx</code></td></tr>
                <tr><td>U+0800 – U+FFFF</td><td>3</td><td><code>1110xxxx 10xxxxxx 10xxxxxx</code></td></tr>
                <tr><td>U+10000 – U+10FFFF</td><td>4</td><td><code>11110xxx 10xxxxxx 10xxxxxx 10xxxxxx</code></td></tr>
              </tbody>
            </table>
          </div>
          <p>Na przykład <span class="term">ł</span> (U+0142, binarnie <span class="term">101 0100 0010</span>) wymaga dwóch bajtów: bity dzieli się na <span class="term">00101</span> i&nbsp;<span class="term">000010</span>, co daje <span class="term">11000101 10000010</span>, czyli szesnastkowo <span class="term">C5 82</span>. Znak euro to <span class="term">E2 82 AC</span>, a&nbsp;😀 to <span class="term">F0 9F 98 80</span>.</p>
          <h2 id="zalety">Dlaczego UTF-8 wygrało</h2>
          <ul>
            <li><strong>Zgodność z&nbsp;ASCII:</strong> tekst angielski i&nbsp;kod źródłowy wyglądają tak samo jak w&nbsp;ASCII.</li>
            <li><strong>Samosynchronizacja:</strong> z&nbsp;dowolnego miejsca można znaleźć początek następnego znaku, bo bajty kontynuacji zawsze zaczynają się od <span class="term">10</span>.</li>
            <li><strong>Brak problemu kolejności bajtów:</strong> w&nbsp;przeciwieństwie do UTF-16, UTF-8 to ciąg pojedynczych bajtów, więc znacznik BOM nie jest potrzebny.</li>
          </ul>
          <p>Nie każdy ciąg bajtów jest poprawnym UTF-8. Dekoder musi odrzucić np. samotny bajt kontynuacji, urwaną sekwencję lub zapis „nadmiarowy” (np. <span class="term">C0 AF</span> zamiast <span class="term">/</span>). Akceptowanie zapisów nadmiarowych prowadziło do prawdziwych luk bezpieczeństwa, bo filtry szukające <span class="term">/</span> lub <span class="term">..</span> ich nie rozpoznawały.</p>
{tool}
          <h2 id="w-praktyce">UTF-8 w praktyce</h2>
          <p>Strony HTML deklarują kodowanie znacznikiem <code>&lt;meta charset="utf-8"&gt;</code>. W&nbsp;JavaScripcie <code>new TextEncoder().encode(text)</code> zwraca bajty UTF-8 tekstu, a&nbsp;<code>new TextDecoder('utf-8', {{ fatal: true }})</code> je dekoduje i&nbsp;zgłasza błąd przy niepoprawnych danych – tak działa narzędzie powyżej. W&nbsp;Pythonie służą do tego <code>text.encode('utf-8')</code> i&nbsp;<code>data.decode('utf-8')</code>.</p>
          <p>Kodowanie ma znaczenie także w&nbsp;kryptografii: szyfry i&nbsp;<a href="/pl/teoria/funkcja-jednokierunkowa.html">funkcje skrótu</a> działają na bajtach, a&nbsp;nie na znakach, więc ten sam tekst zakodowany inaczej da inny szyfrogram lub skrót. Zobacz też <a href="/pl/teoria/liczby-binarne.html">liczby binarne</a> i&nbsp;<a href="/pl/teoria/zapis-liczb.html">zapis liczb</a>.</p>'''
    section = 'theory' if lang == 'en' else 'teoria'
    other = '/pl/teoria/utf-8.html' if lang == 'en' else '/eng/theory/utf-8.html'
    title = 'UTF-8 Encoding Explained + Online Converter | Crypto-IT' if lang == 'en' else 'Kodowanie UTF-8 – jak działa + konwerter online | Crypto-IT'
    desc = ('How UTF-8 stores Unicode characters in 1–4 bytes, with examples and pitfalls. Convert text to UTF-8 hex, binary or decimal online.'
            if lang == 'en' else 'Jak UTF-8 zapisuje znaki Unicode w 1–4 bajtach – przykłady i pułapki. Zamień tekst na UTF-8 (hex, binarnie, dziesiętnie) online.')
    main = f'''  <div class="layout">
    <main id="main">
      <article>
        <!-- auto:breadcrumbs -->
        <!-- /auto:breadcrumbs -->
        <header>
          <h1 class="article__title">{h1}</h1>
          <p class="article__subtitle">{sub}</p>
          <!-- auto:dates -->
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
    return page(lang, 'tool', other, title, desc, main,
                extra='  <script src="/assets/js/tools/utf-8.js" type="module"></script>\n', dates=' data-published="2026-10-30"')


PAGES['eng/theory/utf-8.html'] = utf8_article('en')
PAGES['pl/teoria/utf-8.html'] = utf8_article('pl')

# ---------- About ----------
PAGES['eng/about/index.html'] = page('en', 'page', '/pl/ostronie/', 'About Crypto-IT and the Author | Crypto-IT',
    'Crypto-IT is a free knowledge base about cryptography and IT security, written by Chris Kowalczyk, a software developer.',
    prose(f'''      <h1 class="article__title">About Crypto-IT</h1>
      <p class="article__lead">Crypto-IT is for everyone looking for information about cryptography and security in IT. Such knowledge is often hard to find and usually requires understanding related subjects, such as networking or mathematics. The goal of Crypto-IT is to be a comprehensive, freely available knowledge base on creating, breaking and using ciphers.</p>
      <p>The site is updated regularly: new topics are added and errors are corrected. Next to many articles you will find online tools that let you try the ciphers in your browser, without installing anything. Before 2026 they were a separate site, Crypto-Online.</p>
      <h2 id="author">About the author</h2>
      <p>My name is Chris Kowalczyk. I work as a software developer and I am passionate about cryptography, ciphers and IT security in general. I wrote the articles and implemented the online tools myself.</p>
      <p>I will be glad to hear about inaccuracies in the descriptions, errors in the tools, or topics you would like to read about. You can contact me by <a href="{EMAIL_HREF}">e-mail</a>. I will reply as quickly as I can.</p>
      <p>Thank you for your interest!</p>'''))
PAGES['pl/ostronie/index.html'] = page('pl', 'page', '/eng/about/', 'O stronie Crypto-IT i autorze | Crypto-IT',
    'Crypto-IT to bezpłatna baza wiedzy o kryptografii i bezpieczeństwie IT, tworzona przez programistę Krzysztofa Kowalczyka.',
    prose(f'''      <h1 class="article__title">O stronie Crypto-IT</h1>
      <p class="article__lead">Strona Crypto-IT powstała z&nbsp;myślą o&nbsp;wszystkich, którzy szukają informacji o&nbsp;kryptografii i&nbsp;bezpieczeństwie w&nbsp;IT. Wiedza na te tematy jest często trudno dostępna i&nbsp;wymaga znajomości pokrewnych zagadnień, takich jak matematyka czy sieci komputerowe. Crypto-IT ma być kompleksową, bezpłatną bazą wiedzy o&nbsp;budowie szyfrów, ich łamaniu i&nbsp;wykorzystaniu.</p>
      <p>Strona jest stale rozwijana: dochodzą nowe artykuły, a&nbsp;zauważone błędy są poprawiane. Przy wielu artykułach znajdziesz narzędzia online, które pozwalają wypróbować szyfry w&nbsp;przeglądarce, bez instalowania czegokolwiek. Do 2026 roku tworzyły one osobną stronę Crypto-Online.</p>
      <h2 id="autor">O autorze</h2>
      <p>Nazywam się Krzysztof Kowalczyk. Od lat zawodowo zajmuję się programowaniem i&nbsp;elektroniką, a&nbsp;szczególnie pasjonuję się szyframi, kryptografią i&nbsp;bezpieczeństwem w&nbsp;IT. Artykuły napisałem i&nbsp;narzędzia online zaimplementowałem sam.</p>
      <p>Chętnie dowiem się o&nbsp;nieścisłościach w&nbsp;opisach, błędach w&nbsp;działaniu narzędzi i&nbsp;tematach, które warto opisać. Można się ze mną skontaktować <a href="{EMAIL_HREF}">e-mailem</a>. Postaram się odpowiedzieć jak najszybciej.</p>
      <p>Dziękuję za zainteresowanie!</p>
      {{{{include:promo}}}}'''.replace('{{include:promo}}', '<!-- shared:promo -->\n      <!-- /shared:promo -->')))

# ---------- Privacy ----------
PAGES['eng/privacy.html'] = page('en', 'page', '/pl/prywatnosc.html', 'Privacy Policy | Crypto-IT',
    'How Crypto-IT handles personal data: Google AdSense advertising and cookies, consent, hosting on GitHub Pages and your rights under GDPR.',
    prose(f'''      <h1 class="article__title">Privacy policy</h1>
      <p class="article__meta">Last updated <time datetime="2026-10-30">30 October 2026</time></p>
      <h2 id="controller">Who is responsible</h2>
      <p>This website is run by Chris Kowalczyk (contact: <a href="{EMAIL_HREF}">e-mail</a>). Crypto-IT has no user accounts, comments or contact forms and does not use its own analytics.</p>
      <h2 id="ads">Advertising (Google AdSense)</h2>
      <p>The site shows ads provided by Google AdSense. Google and its partners may use cookies and similar technologies to show ads, limit how often you see them, measure their effectiveness and – if you agree – personalise them based on your previous visits to this and other websites.</p>
      <p>Visitors from the European Economic Area, the United Kingdom and Switzerland are asked for consent by Google’s consent message (a certified consent management platform). Without consent you see only non-personalised or limited ads. You can change your choice at any time with the “Privacy and cookie settings” link that Google displays on the page.</p>
      <p>More information: <a href="https://policies.google.com/technologies/partner-sites" rel="noopener" target="_blank">How Google uses information from sites that use its services</a>, <a href="https://adssettings.google.com/" rel="noopener" target="_blank">Google ad settings</a>, and the list of advertising partners on <a href="https://www.youronlinechoices.eu/" rel="noopener" target="_blank">Your Online Choices</a>.</p>
      <h2 id="hosting">Hosting</h2>
      <p>The site is hosted on GitHub Pages (GitHub, Inc.). To deliver the pages and protect the service, GitHub processes technical data such as your IP address. See the <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener" target="_blank">GitHub privacy statement</a>.</p>
      <h2 id="tools">Online tools</h2>
      <p>The cipher tools run entirely in your browser. The text and keys you enter are not sent to any server.</p>
      <h2 id="links">External links and sharing</h2>
      <p>Share links (LinkedIn, X, Facebook) are plain links: nothing is loaded from these services until you click them. After clicking, their privacy policies apply. Polish pages contain a link to a bookshop (Empik).</p>
      <h2 id="rights">Your rights</h2>
      <p>Under the GDPR you have the right to access, rectify and erase your data, to restrict or object to processing, to data portability, and to withdraw consent. For data processed by Google, use the links above. You can also lodge a complaint with a supervisory authority; in Poland this is the President of the Personal Data Protection Office (UODO).</p>'''))
PAGES['pl/prywatnosc.html'] = page('pl', 'page', '/eng/privacy.html', 'Polityka prywatności | Crypto-IT',
    'Jak Crypto-IT przetwarza dane osobowe: reklamy Google AdSense i pliki cookie, zgoda, hosting w GitHub Pages oraz Twoje prawa wynikające z RODO.',
    prose(f'''      <h1 class="article__title">Polityka prywatności</h1>
      <p class="article__meta">Ostatnia aktualizacja <time datetime="2026-10-30">30 października 2026</time></p>
      <h2 id="administrator">Administrator</h2>
      <p>Stronę prowadzi Krzysztof Kowalczyk (kontakt: <a href="{EMAIL_HREF}">e-mail</a>). Crypto-IT nie ma kont użytkowników, komentarzy ani formularzy kontaktowych i&nbsp;nie używa własnych narzędzi analitycznych.</p>
      <h2 id="reklamy">Reklamy (Google AdSense)</h2>
      <p>Na stronie wyświetlane są reklamy Google AdSense. Google i&nbsp;jego partnerzy mogą używać plików cookie i&nbsp;podobnych technologii, aby wyświetlać reklamy, ograniczać częstotliwość ich pokazywania, mierzyć ich skuteczność oraz – jeśli wyrazisz zgodę – dopasowywać je na podstawie Twoich wcześniejszych wizyt na tej i&nbsp;innych stronach.</p>
      <p>Odwiedzający z&nbsp;Europejskiego Obszaru Gospodarczego, Wielkiej Brytanii i&nbsp;Szwajcarii są proszeni o&nbsp;zgodę w&nbsp;komunikacie Google (certyfikowanej platformie do zarządzania zgodami). Bez zgody wyświetlane są tylko reklamy niespersonalizowane lub ograniczone. Wybór można w&nbsp;każdej chwili zmienić za pomocą linku „Ustawienia prywatności i&nbsp;plików cookie”, który Google wyświetla na stronie.</p>
      <p>Więcej informacji: <a href="https://policies.google.com/technologies/partner-sites?hl=pl" rel="noopener" target="_blank">Jak Google wykorzystuje informacje z&nbsp;witryn korzystających z&nbsp;jego usług</a>, <a href="https://adssettings.google.com/" rel="noopener" target="_blank">ustawienia reklam Google</a> oraz lista partnerów reklamowych na stronie <a href="https://www.youronlinechoices.eu/" rel="noopener" target="_blank">Your Online Choices</a>.</p>
      <h2 id="hosting">Hosting</h2>
      <p>Strona jest utrzymywana w&nbsp;serwisie GitHub Pages (GitHub, Inc.). Aby dostarczać strony i&nbsp;chronić usługę, GitHub przetwarza dane techniczne, takie jak adres IP. Zobacz <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener" target="_blank">oświadczenie o&nbsp;prywatności GitHub</a>.</p>
      <h2 id="narzedzia">Narzędzia online</h2>
      <p>Narzędzia do szyfrowania działają w&nbsp;całości w&nbsp;przeglądarce. Wpisany tekst i&nbsp;klucze nie są wysyłane na żaden serwer.</p>
      <h2 id="linki">Linki zewnętrzne i&nbsp;udostępnianie</h2>
      <p>Linki do udostępniania (LinkedIn, X, Facebook) to zwykłe odnośniki: nic nie jest pobierane z&nbsp;tych serwisów, dopóki ich nie klikniesz. Po kliknięciu obowiązują ich polityki prywatności. Polskie strony zawierają link do księgarni (Empik).</p>
      <h2 id="prawa">Twoje prawa</h2>
      <p>Zgodnie z&nbsp;RODO masz prawo dostępu do danych, ich sprostowania i&nbsp;usunięcia, ograniczenia przetwarzania, sprzeciwu, przenoszenia danych oraz wycofania zgody. W&nbsp;przypadku danych przetwarzanych przez Google skorzystaj z&nbsp;linków powyżej. Przysługuje Ci także prawo wniesienia skargi do Prezesa Urzędu Ochrony Danych Osobowych (UODO).</p>'''))

# ---------- Root and 404 (outside the page system: no data-type) ----------
ROOT_PAGE = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Crypto-IT</title>
  <link rel="canonical" href="https://www.crypto-it.net/eng/">
  <link rel="alternate" hreflang="en" href="https://www.crypto-it.net/eng/">
  <link rel="alternate" hreflang="pl" href="https://www.crypto-it.net/pl/">
  <link rel="alternate" hreflang="x-default" href="https://www.crypto-it.net/eng/">
  <script>
    // Polish browsers go to /pl/, everyone else to /eng/ (like the old .htaccess)
    location.replace(/^pl\\b/i.test(navigator.language || '') ? '/pl/' : '/eng/');
  </script>
  <noscript><meta http-equiv="refresh" content="0; url=/eng/"></noscript>
</head>
<body>
  <p><a href="/eng/">Crypto-IT in English</a> · <a href="/pl/" lang="pl">Crypto-IT po polsku</a></p>
</body>
</html>
'''
NOT_FOUND = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Page not found | Crypto-IT</title>
  <meta name="robots" content="noindex">
  <link rel="icon" href="/assets/img/favicon-32.png" sizes="32x32">
  <link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>
  <header class="site-header">
    <div class="site-header__inner">
      <a class="logo" href="/eng/">Crypto<span>-IT</span></a>
    </div>
  </header>
  <div class="layout layout--wide">
    <main id="main" class="page">
      <h1 class="article__title">Page not found</h1>
      <p class="article__lead">The page you are looking for does not exist or has moved.</p>
      <p><a class="button" href="/eng/">Go to the homepage</a> <a class="button" href="/eng/online-tools.html">Online tools</a></p>
      <section lang="pl">
        <h2>Nie znaleziono strony</h2>
        <p>Strona, której szukasz, nie istnieje lub została przeniesiona.</p>
        <p><a class="button" href="/pl/">Przejdź do strony głównej</a> <a class="button" href="/pl/narzedzia-online.html">Narzędzia online</a></p>
      </section>
    </main>
  </div>
</body>
</html>
'''
PAGES['index.html'] = ROOT_PAGE
PAGES['404.html'] = NOT_FOUND

for rel, text in PAGES.items():
    f = DOCS / rel
    if f.exists():
        print('exists, skipped:', rel)
        continue
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding='utf-8')
    print('created', rel)
