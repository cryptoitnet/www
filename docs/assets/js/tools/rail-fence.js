// Rail fence cipher: pure functions (tested in tests/rail-fence.test.html) + page widget.
//
// The plaintext is written in a zig-zag across a number of rails (rows), then read off
// rail by rail. An optional offset skips some positions on the zig-zag before the first
// letter is placed, which shifts where the text starts on the fence.
//
// Options:
//   rails   – number of rails (>= 2)
//   offset  – how many zig-zag steps to skip before the first letter (>= 0)

export class RailFenceError extends Error {
  constructor(code) { super(code); this.code = code; }
}

/** Upper-case Latin letters only; diacritics removed (ą→A, ł→L). */
export function normalize(text) {
  return text.replace(/ł/g, 'l').replace(/Ł/g, 'L')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toUpperCase().replace(/[^A-Z]/g, '');
}

/**
 * Rail index for every position of the zig-zag, starting `offset` steps in.
 * For rails = 3 the pattern of rails is 0,1,2,1,0,1,2,1,…
 */
function railPattern(length, rails, offset) {
  const period = rails > 1 ? 2 * (rails - 1) : 1;
  const out = [];
  for (let i = 0; i < length; i += 1) {
    const phase = (i + offset) % period;
    out.push(phase < rails ? phase : period - phase);
  }
  return out;
}

function checkOptions(rails, offset) {
  if (!Number.isInteger(rails) || rails < 2) throw new RailFenceError('rails');
  if (!Number.isInteger(offset) || offset < 0) throw new RailFenceError('offset');
}

export function encrypt(text, rails = 3, offset = 0) {
  checkOptions(rails, offset);
  const letters = normalize(text);
  const pattern = railPattern(letters.length, rails, offset);
  const rows = Array.from({ length: rails }, () => []);
  letters.split('').forEach((ch, i) => rows[pattern[i]].push(ch));
  const grid = rows.map((row) => row.join(''));
  return { output: rows.map((row) => row.join('')).join(''), grid, pattern };
}

export function decrypt(text, rails = 3, offset = 0) {
  checkOptions(rails, offset);
  const letters = normalize(text);
  const pattern = railPattern(letters.length, rails, offset);
  // Count how many letters land on each rail, then slice the ciphertext per rail.
  const counts = Array.from({ length: rails }, () => 0);
  pattern.forEach((r) => { counts[r] += 1; });
  const rails2 = [];
  let pos = 0;
  for (let r = 0; r < rails; r += 1) { rails2.push(letters.slice(pos, pos + counts[r]).split('')); pos += counts[r]; }
  // Walk the zig-zag again, taking the next letter from the matching rail.
  const idx = Array.from({ length: rails }, () => 0);
  const out = pattern.map((r) => rails2[r][idx[r]++]);
  const grid = rails2.map((row) => row.join(''));
  return { output: out.join(''), grid, pattern };
}

// ---------- Page widget ----------

export function mount(root) {
  const $ = (role) => root.querySelector(`[data-role="${role}"]`);
  const input = $('input');
  const output = $('output');
  const rails = $('rails');
  const offset = $('offset');
  const fence = $('fence');
  const error = $('error');
  const value = (name) => root.querySelector(`input[name="${name}"]:checked`).value;

  const update = () => {
    const direction = value('direction');
    error.textContent = '';
    try {
      const n = parseInt(rails.value, 10);
      const off = parseInt(offset.value, 10) || 0;
      const fn = direction === 'encrypt' ? encrypt : decrypt;
      const result = fn(input.value, n, off);
      output.value = result.output;
      renderFence(fence, result, n, off);
    } catch (e) {
      if (!(e instanceof RailFenceError)) throw e;
      output.value = '';
      fence.innerHTML = '';
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

/** Draw the zig-zag: each column holds one letter on its rail, dots elsewhere. */
function renderFence(container, result, rails, offset) {
  const letters = result.grid.join('');          // all fence letters
  const length = result.pattern.length;
  if (!length) { container.innerHTML = ''; return; }
  // Rebuild the full plaintext/ciphertext laid out on the zig-zag for display.
  const layout = Array.from({ length: rails }, () => Array(length).fill(''));
  // Reconstruct which letter sits in each column from the rail counts.
  const perRail = Array.from({ length: rails }, () => 0);
  result.pattern.forEach((r) => { perRail[r] += 1; });
  const slices = [];
  let p = 0;
  for (let r = 0; r < rails; r += 1) { slices.push(letters.slice(p, p + perRail[r])); p += perRail[r]; }
  const idx = Array.from({ length: rails }, () => 0);
  result.pattern.forEach((r, col) => { layout[r][col] = slices[r][idx[r]++] ?? ''; });
  const rows = layout.map((row) =>
    `<tr>${row.map((ch) => `<td>${ch || '.'}</td>`).join('')}</tr>`).join('');
  container.innerHTML = `<tbody>${rows}</tbody>`;
}

document.querySelectorAll('[data-tool="rail-fence"]').forEach(mount);
