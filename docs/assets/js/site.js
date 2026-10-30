// Crypto-IT – the only general script on every page.
//   1. Table of contents: <nav data-toc> is filled with links to the article's <h2> headings
//   2. Copy buttons on code samples (<pre><code>)
// Pages work without JavaScript; these are only conveniences.
// (The current menu item and sidebar link are marked by scripts/site.py sync.)

const lang = document.documentElement.lang;
const t = {
  en: { copy: 'Copy', copied: 'Copied' },
  pl: { copy: 'Kopiuj', copied: 'Skopiowano' },
}[lang] ?? { copy: 'Copy', copied: 'Copied' };

// ---------- 1. Table of contents ----------
const toc = document.querySelector('[data-toc]');
if (toc) {
  const headings = [...document.querySelectorAll('.article__body h2[id]')]
    .filter((h) => !toc.contains(h) && !h.closest('[popover]'));
  if (headings.length >= 3) {
    const list = document.createElement('ol');
    headings.forEach((h) => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = `#${h.id}`;
      a.textContent = h.textContent;
      li.append(a);
      list.append(li);
    });
    toc.append(list);
    toc.hidden = false;
  }
}

// ---------- 2. Copy buttons ----------
document.querySelectorAll('pre > code').forEach((code) => {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'code-copy';
  button.textContent = t.copy;
  button.addEventListener('click', async () => {
    await navigator.clipboard.writeText(code.textContent);
    button.textContent = t.copied;
    setTimeout(() => { button.textContent = t.copy; }, 1500);
  });
  code.parentElement.prepend(button);
});
