// Four-square cipher: pure functions (tested in tests/four-square.test.html) + page widget.
//
// Four 5×5 tables arranged in a 2×2 block:
//   upper-left  = plain alphabet        upper-right = keyword 1
//   lower-left  = keyword 2             lower-right = plain alphabet
//
// Encryption: the first plaintext letter is found in the upper-left square and the second
// in the lower-right square; they mark two corners of a rectangle. The ciphertext letters
// are read from the upper-right and lower-left squares at the other two corners.
// Decryption reverses the roles of the plain and keyword squares.
//
// Modes – which letter is left out so the alphabet fits into a 5×5 table:
//   'j-as-i'  J is written as I (classic)
//   'no-q'    Q is dropped
//   'no-x'    X is dropped

const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const OMITTED = { 'j-as-i': 'J', 'no-q': 'Q', 'no-x': 'X' };

export class FourSquareError extends Error {
  constructor(code) { super(code); this.code = code; }
}

/** Upper-case Latin letters only; diacritics removed (ą→A, ł→L), omitted letter handled. */
export function normalize(text, mode = 'j-as-i') {
  const omitted = OMITTED[mode];
  if (!omitted) throw new FourSquareError('mode');
  let s = text.replace(/ł/g, 'l').replace(/Ł/g, 'L')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toUpperCase().replace(/[^A-Z]/g, '');
  s = mode === 'j-as-i' ? s.replaceAll('J', 'I') : s.replaceAll(omitted, '');
  return s;
}

/** Plain 25-letter alphabet square (row by row) for the current mode. */
export function plainSquare(mode = 'j-as-i') {
  return [...new Set(normalize(ALPHABET, mode))].join('');
}

/** 25-letter keyword square: keyword letters (no repeats), then the rest of the alphabet. */
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

/**
 * Transform one pair. `srcA`/`srcB` are the squares the letters are looked up in,
 * `dstA`/`dstB` are the squares the result is read from (at the swapped columns).
 */
function transform(srcA, srcB, dstA, dstB, pair) {
  const i1 = srcA.indexOf(pair[0]);
  const i2 = srcB.indexOf(pair[1]);
  const [r1, c1, r2, c2] = [Math.floor(i1 / 5), i1 % 5, Math.floor(i2 / 5), i2 % 5];
  return dstA[r1 * 5 + c2] + dstB[r2 * 5 + c1];
}

export function encrypt(text, keyword1, keyword2, mode = 'j-as-i') {
  const plain = plainSquare(mode);
  const upperRight = buildTable(keyword1, mode);
  const lowerLeft = buildTable(keyword2, mode);
  const digraphs = toDigraphs(normalize(text, mode), mode);
  // look up in plain (UL) + plain (LR), read from UR + LL
  const output = digraphs.map((p) => transform(plain, plain, upperRight, lowerLeft, p)).join('');
  return { plain, upperRight, lowerLeft, digraphs, output };
}

export function decrypt(text, keyword1, keyword2, mode = 'j-as-i') {
  const plain = plainSquare(mode);
  const upperRight = buildTable(keyword1, mode);
  const lowerLeft = buildTable(keyword2, mode);
  const digraphs = toDigraphs(normalize(text, mode), mode);
  // look up in UR + LL, read from plain (UL) + plain (LR)
  const output = digraphs.map((p) => transform(upperRight, lowerLeft, plain, plain, p)).join('');
  return { plain, upperRight, lowerLeft, digraphs, output };
}

// ---------- Page widget ----------

export function mount(root) {
  const $ = (role) => root.querySelector(`[data-role="${role}"]`);
  const keyword1 = $('keyword1');
  const keyword2 = $('keyword2');
  const input = $('input');
  const output = $('output');
  const digraphs = $('digraphs');
  const grids = {
    ul: $('table-ul'), ur: $('table-ur'), ll: $('table-ll'), lr: $('table-lr'),
  };
  const error = $('error');
  const value = (name) => root.querySelector(`input[name="${name}"]:checked`).value;

  const update = () => {
    const mode = value('mode');
    const direction = value('direction');
    error.textContent = '';
    try {
      const fn = direction === 'encrypt' ? encrypt : decrypt;
      const result = fn(input.value, keyword1.value, keyword2.value, mode);
      output.value = result.output.replace(/(.{5})(?=.)/g, '$1 ');
      digraphs.textContent = result.digraphs.join(' ');
      renderTable(grids.ul, result.plain);
      renderTable(grids.ur, result.upperRight);
      renderTable(grids.ll, result.lowerLeft);
      renderTable(grids.lr, result.plain);
    } catch (e) {
      if (!(e instanceof FourSquareError)) throw e;
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
    const other = root.querySelector('input[name="direction"]:not(:checked)');
    other.checked = true;
    update();
  });

  update();
}

function renderTable(grid, table) {
  const cells = [...table].map((ch) => `<td>${ch}</td>`);
  const rows = [0, 1, 2, 3, 4].map((r) => `<tr>${cells.slice(r * 5, r * 5 + 5).join('')}</tr>`);
  grid.innerHTML = `<tbody>${rows.join('')}</tbody>`;
}

document.querySelectorAll('[data-tool="four-square"]').forEach(mount);
