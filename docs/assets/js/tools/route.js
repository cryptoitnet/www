// Route cipher: pure functions (tested in tests/route.test.html) + page widget.
//
// The plaintext is written into a grid of a fixed number of columns, row by row, padding
// the last row with filler letters. The ciphertext is then read by following a spiral
// path that starts in the top-right corner and winds inward, either clockwise or
// anticlockwise. Decryption writes the ciphertext back along the spiral and reads the
// grid row by row.
//
// Options:
//   columns   – grid width (>= 2)
//   direction – 'clockwise' or 'anticlockwise'
//   filler    – letter used to pad the last row (default X)

export class RouteError extends Error {
  constructor(code) { super(code); this.code = code; }
}

/** Upper-case Latin letters only; diacritics removed (ą→A, ł→L). */
export function normalize(text) {
  return text.replace(/ł/g, 'l').replace(/Ł/g, 'L')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toUpperCase().replace(/[^A-Z]/g, '');
}

/**
 * Ordered list of [row, col] cells along the spiral: start top-right, move down the right
 * edge first (clockwise) or left along the top (anticlockwise), shrinking the borders.
 * This mirrors the original tool's path exactly.
 */
export function spiralPath(rows, cols, direction) {
  const path = [];
  let posR = 0;
  let posC = cols - 1;
  let left = 0;
  let top = 0;
  let right = cols - 1;
  let bottom = rows - 1;
  let dirR = direction === 'clockwise' ? 1 : 0;
  let dirC = direction === 'clockwise' ? 0 : -1;

  for (let n = 0; n < rows * cols; n += 1) {
    path.push([posR, posC]);
    // vertical move
    if (posR + dirR >= top && posR + dirR <= bottom) {
      posR += dirR;
    } else if (dirR === 1) {
      if (direction === 'clockwise') { dirR = 0; dirC = -1; right -= 1; }
      else { dirR = 0; dirC = 1; left += 1; }
    } else {
      if (direction === 'clockwise') { dirR = 0; dirC = 1; left += 1; }
      else { dirR = 0; dirC = -1; right -= 1; }
    }
    // horizontal move
    if (posC + dirC >= left && posC + dirC <= right) {
      posC += dirC;
    } else {
      if (dirC === 1) {
        if (direction === 'clockwise') { dirR = 1; dirC = 0; top += 1; }
        else { dirR = -1; dirC = 0; bottom -= 1; }
      } else if (direction === 'clockwise') { dirR = -1; dirC = 0; bottom -= 1; }
      else { dirR = 1; dirC = 0; top += 1; }
      posR += dirR;
    }
  }
  return path;
}

function gridDimensions(length, cols) {
  if (!Number.isInteger(cols) || cols < 2) throw new RouteError('columns');
  const rows = Math.ceil(length / cols);
  return { rows: Math.max(rows, 1), cols };
}

export function encrypt(text, cols = 5, direction = 'clockwise', fillerLetter = 'X') {
  const letters = normalize(text);
  if (!letters.length) return { grid: [], output: '', rows: 0, cols };
  const { rows } = gridDimensions(letters.length, cols);
  // Fill row by row, padding with the filler letter.
  const grid = Array.from({ length: rows }, (_, r) =>
    Array.from({ length: cols }, (_, c) => letters[r * cols + c] ?? fillerLetter));
  const path = spiralPath(rows, cols, direction);
  const output = path.map(([r, c]) => grid[r][c]).join('');
  return { grid, output, rows, cols };
}

export function decrypt(text, cols = 5, direction = 'clockwise') {
  const letters = normalize(text);
  if (!letters.length) return { grid: [], output: '', rows: 0, cols };
  if (!Number.isInteger(cols) || cols < 2) throw new RouteError('columns');
  if (letters.length % cols !== 0) throw new RouteError('length');
  const rows = letters.length / cols;
  const grid = Array.from({ length: rows }, () => Array(cols).fill(''));
  const path = spiralPath(rows, cols, direction);
  path.forEach(([r, c], i) => { grid[r][c] = letters[i]; });
  const output = grid.map((row) => row.join('')).join('');
  return { grid, output, rows, cols };
}

// ---------- Page widget ----------

export function mount(root) {
  const $ = (role) => root.querySelector(`[data-role="${role}"]`);
  const input = $('input');
  const output = $('output');
  const columns = $('columns');
  const gridEl = $('grid');
  const error = $('error');
  const value = (name) => root.querySelector(`input[name="${name}"]:checked`).value;

  const update = () => {
    const direction = value('direction');
    const path = value('path');
    error.textContent = '';
    try {
      const cols = parseInt(columns.value, 10);
      const result = direction === 'encrypt'
        ? encrypt(input.value, cols, path)
        : decrypt(input.value, cols, path);
      output.value = result.output;
      renderGrid(gridEl, result);
    } catch (e) {
      if (!(e instanceof RouteError)) throw e;
      output.value = '';
      gridEl.innerHTML = '';
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

function renderGrid(container, result) {
  if (!result.grid.length) { container.innerHTML = ''; return; }
  const rows = result.grid.map((row) =>
    `<tr>${row.map((ch) => `<td>${ch || '.'}</td>`).join('')}</tr>`).join('');
  container.innerHTML = `<tbody>${rows}</tbody>`;
}

document.querySelectorAll('[data-tool="route"]').forEach(mount);
