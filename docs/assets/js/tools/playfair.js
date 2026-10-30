// Playfair cipher: pure functions (tested in tests/playfair.test.html) + page widget.
//
// Modes – which letter is left out so the alphabet fits into a 5×5 table:
//   'j-as-i'  J is written as I (classic)
//   'no-q'    Q is dropped
//   'no-x'    X is dropped

const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const OMITTED = { 'j-as-i': 'J', 'no-q': 'Q', 'no-x': 'X' };

export class PlayfairError extends Error {
  constructor(code) { super(code); this.code = code; }
}

/** Upper-case Latin letters only; diacritics removed (ą→A, ł→L), omitted letter handled. */
export function normalize(text, mode = 'j-as-i') {
  const omitted = OMITTED[mode];
  if (!omitted) throw new PlayfairError('mode');
  let s = text.replace(/ł/g, 'l').replace(/Ł/g, 'L')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toUpperCase().replace(/[^A-Z]/g, '');
  s = mode === 'j-as-i' ? s.replaceAll('J', 'I') : s.replaceAll(omitted, '');
  return s;
}

/** 25-letter table, row by row: keyword letters (no repeats), then the rest of the alphabet. */
export function buildTable(keyword, mode = 'j-as-i') {
  return [...new Set(normalize(keyword + ALPHABET, mode))].join('');
}

/** Filler inserted between doubled letters and after a lone last letter. */
function filler(letter, mode) {
  const primary = mode === 'no-x' ? 'Q' : 'X';
  const secondary = mode === 'no-q' || primary === 'Q' ? 'Z' : 'Q';
  return letter === primary ? secondary : primary;
}

/** Split prepared letters into pairs: "BALLOON" → BA LX LO ON. */
export function toDigraphs(letters, mode = 'j-as-i') {
  const pairs = [];
  for (let i = 0; i < letters.length;) {
    const a = letters[i];
    const b = letters[i + 1];
    if (b === undefined || b === a) { pairs.push(a + filler(a, mode)); i += 1; }
    else { pairs.push(a + b); i += 2; }
  }
  return pairs;
}

/** Same row: shift right (dir 1) / left (dir -1); same column: down / up; otherwise rectangle. */
function transform(table, pair, dir) {
  const i1 = table.indexOf(pair[0]);
  const i2 = table.indexOf(pair[1]);
  const [r1, c1, r2, c2] = [Math.floor(i1 / 5), i1 % 5, Math.floor(i2 / 5), i2 % 5];
  const at = (r, c) => table[((r + 5) % 5) * 5 + ((c + 5) % 5)];
  if (r1 === r2) return at(r1, c1 + dir) + at(r2, c2 + dir);
  if (c1 === c2) return at(r1 + dir, c1) + at(r2 + dir, c2);
  return at(r1, c2) + at(r2, c1);
}

export function encrypt(text, keyword, mode = 'j-as-i') {
  const table = buildTable(keyword, mode);
  const digraphs = toDigraphs(normalize(text, mode), mode);
  return { table, digraphs, output: digraphs.map((p) => transform(table, p, 1)).join('') };
}

export function decrypt(text, keyword, mode = 'j-as-i') {
  const table = buildTable(keyword, mode);
  const letters = normalize(text, mode);
  if (letters.length % 2) throw new PlayfairError('odd');
  const digraphs = letters.match(/../g) ?? [];
  if (digraphs.some((p) => p[0] === p[1])) throw new PlayfairError('double');
  return { table, digraphs, output: digraphs.map((p) => transform(table, p, -1)).join('') };
}

// ---------- Page widget ----------
// Markup: an element with data-tool="playfair" containing elements with data-role=…
// (see the article pages). Texts such as error messages come from data-msg-* attributes,
// so the same script works for every language.

export function mount(root) {
  const $ = (role) => root.querySelector(`[data-role="${role}"]`);
  const keyword = $('keyword');
  const input = $('input');
  const output = $('output');
  const digraphs = $('digraphs');
  const grid = $('table');
  const error = $('error');

  const value = (name) => root.querySelector(`input[name="${name}"]:checked`).value;

  const update = () => {
    const mode = value('mode');
    const direction = value('direction');
    error.textContent = '';
    try {
      const result = (direction === 'encrypt' ? encrypt : decrypt)(input.value, keyword.value, mode);
      output.value = result.output.replace(/(.{5})(?=.)/g, '$1 ');   // groups of 5 letters
      digraphs.textContent = result.digraphs.join(' ');
      renderTable(grid, result.table);
    } catch (e) {
      if (!(e instanceof PlayfairError)) throw e;
      output.value = '';
      digraphs.textContent = '';
      renderTable(grid, buildTable(keyword.value, mode));
      error.textContent = root.dataset[`msg${e.code[0].toUpperCase()}${e.code.slice(1)}`] ?? e.code;
    }
  };

  root.addEventListener('input', update);

  $('swap').addEventListener('click', () => {
    input.value = output.value;
    const other = root.querySelector(`input[name="direction"]:not(:checked)`);
    other.checked = true;
    update();
  });

  $('copy').addEventListener('click', async () => {
    await navigator.clipboard.writeText(output.value);
    const button = $('copy');
    const label = button.textContent;
    button.textContent = root.dataset.msgCopied;
    setTimeout(() => { button.textContent = label; }, 1500);
  });

  update();
}

function renderTable(grid, table) {
  const cells = [...table].map((ch) => `<td>${ch}</td>`);
  const rows = [0, 1, 2, 3, 4].map((r) => `<tr>${cells.slice(r * 5, r * 5 + 5).join('')}</tr>`);
  grid.innerHTML = `<tbody>${rows.join('')}</tbody>`;
}

document.querySelectorAll('[data-tool="playfair"]').forEach(mount);
