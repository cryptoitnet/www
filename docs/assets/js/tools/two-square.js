// Two-square cipher (double Playfair): pure functions (tested in tests/two-square.test.html)
// + page widget.
//
// Two 5×5 tables are built from two keywords. Each plaintext pair is replaced using both
// tables. Two layouts exist:
//   'vertical'   – tables stacked one above the other (columns aligned); a pair that shares
//                  a column is left unchanged, otherwise each letter keeps its row and takes
//                  the other letter's column.
//   'horizontal' – tables side by side (rows aligned); a pair that shares a row is left
//                  unchanged, otherwise each letter keeps its column and takes the other's row.
// Both layouts are their own inverse, so the same routine encrypts and decrypts.
//
// Modes – which letter is left out so the alphabet fits into a 5×5 table:
//   'j-as-i'  J is written as I (classic)
//   'no-q'    Q is dropped
//   'no-x'    X is dropped

const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const OMITTED = { 'j-as-i': 'J', 'no-q': 'Q', 'no-x': 'X' };

export class TwoSquareError extends Error {
  constructor(code) { super(code); this.code = code; }
}

/** Upper-case Latin letters only; diacritics removed (ą→A, ł→L), omitted letter handled. */
export function normalize(text, mode = 'j-as-i') {
  const omitted = OMITTED[mode];
  if (!omitted) throw new TwoSquareError('mode');
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

/** Filler for a lone last letter (keeps text length even). */
function filler(mode) {
  return mode === 'no-x' ? 'Z' : 'X';
}

/** Split normalized letters into pairs, padding the last lone letter. */
export function toDigraphs(letters, mode = 'j-as-i') {
  const padded = letters.length % 2 ? letters + filler(mode) : letters;
  return padded.match(/../g) ?? [];
}

/** Transform one pair with the two tables and the chosen layout (self-inverse). */
function transform(t0, t1, pair, layout) {
  const i1 = t0.indexOf(pair[0]);
  const i2 = t1.indexOf(pair[1]);
  const [r1, c1, r2, c2] = [Math.floor(i1 / 5), i1 % 5, Math.floor(i2 / 5), i2 % 5];
  if (layout === 'vertical') {                      // stacked: columns aligned
    if (c1 === c2) return pair;                     // same column: unchanged
    return t0[r1 * 5 + c2] + t1[r2 * 5 + c1];
  }
  if (r1 === r2) return pair;                       // side by side: same row unchanged
  return t0[r2 * 5 + c1] + t1[r1 * 5 + c2];
}

/** Encrypt or decrypt (identical operation for this cipher). */
export function convert(text, keyword1, keyword2, mode = 'j-as-i', layout = 'vertical') {
  const table1 = buildTable(keyword1, mode);
  const table2 = buildTable(keyword2, mode);
  const digraphs = toDigraphs(normalize(text, mode), mode);
  const output = digraphs.map((p) => transform(table1, table2, p, layout)).join('');
  return { table1, table2, digraphs, output };
}

export const encrypt = convert;
export const decrypt = convert;

// ---------- Page widget ----------

export function mount(root) {
  const $ = (role) => root.querySelector(`[data-role="${role}"]`);
  const keyword1 = $('keyword1');
  const keyword2 = $('keyword2');
  const input = $('input');
  const output = $('output');
  const digraphs = $('digraphs');
  const grid1 = $('table1');
  const grid2 = $('table2');
  const error = $('error');
  const value = (name) => root.querySelector(`input[name="${name}"]:checked`).value;

  const update = () => {
    const mode = value('mode');
    const layout = value('layout');
    error.textContent = '';
    try {
      const result = convert(input.value, keyword1.value, keyword2.value, mode, layout);
      output.value = result.output.replace(/(.{5})(?=.)/g, '$1 ');
      digraphs.textContent = result.digraphs.join(' ');
      renderTable(grid1, result.table1);
      renderTable(grid2, result.table2);
    } catch (e) {
      if (!(e instanceof TwoSquareError)) throw e;
      output.value = '';
      digraphs.textContent = '';
      error.textContent = root.dataset[`msg${e.code[0].toUpperCase()}${e.code.slice(1)}`] ?? e.code;
    }
  };

  root.addEventListener('input', update);

  $('copy').addEventListener('click', async () => {
    await navigator.clipboard.writeText(output.value);
    const button = $('copy');
    const label = button.textContent;
    button.textContent = root.dataset.msgCopied;
    setTimeout(() => { button.textContent = label; }, 1500);
  });

  $('swap').addEventListener('click', () => {
    input.value = output.value;
    update();
  });

  update();
}

function renderTable(grid, table) {
  const cells = [...table].map((ch) => `<td>${ch}</td>`);
  const rows = [0, 1, 2, 3, 4].map((r) => `<tr>${cells.slice(r * 5, r * 5 + 5).join('')}</tr>`);
  grid.innerHTML = `<tbody>${rows.join('')}</tbody>`;
}

document.querySelectorAll('[data-tool="two-square"]').forEach(mount);
