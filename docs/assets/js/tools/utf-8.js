// UTF-8 converter: pure functions (tested in tests/utf-8.test.html) + page widget.
//
// Converts between text and its UTF-8 byte sequence shown in several formats. The old tool
// produced HTML numeric entities of the UTF-8 bytes (e.g. &#196;&#133; for "ą"); that
// format is kept as "entities", alongside plain hex, decimal and binary byte lists.
//
// Encoding/decoding uses TextEncoder/TextDecoder with fatal:true so invalid byte
// sequences raise an error instead of yielding replacement characters.

export class Utf8Error extends Error {
  constructor(code) { super(code); this.code = code; }
}

const encoder = new TextEncoder();

/** Format a byte (0–255) in the chosen base. */
function formatByte(b, format) {
  switch (format) {
    case 'hex': return b.toString(16).toUpperCase().padStart(2, '0');
    case 'binary': return b.toString(2).padStart(8, '0');
    case 'decimal': return String(b);
    case 'entities': return `&#${b};`;
    default: throw new Utf8Error('format');
  }
}

/** Encode text → list of UTF-8 bytes in the chosen format. */
export function encode(text, format = 'hex') {
  const bytes = [...encoder.encode(text)];
  const parts = bytes.map((b) => formatByte(b, format));
  // Entities run together; the others are space-separated for readability.
  return format === 'entities' ? parts.join('') : parts.join(' ');
}

/** Parse a formatted byte list back into an array of byte values. */
export function parseBytes(input, format) {
  const radix = { hex: 16, binary: 2, decimal: 10 }[format];
  let tokens;
  if (format === 'entities') {
    tokens = [...input.matchAll(/&#(\d+);/g)].map((m) => m[1]);
    if (input.replace(/&#\d+;/g, '').trim() !== '') throw new Utf8Error('parse');
  } else {
    tokens = input.trim().split(/[\s,]+/).filter(Boolean);
  }
  const bytes = tokens.map((tok) => {
    const value = format === 'entities' ? parseInt(tok, 10) : parseInt(tok, radix);
    const pattern = { hex: /^[0-9a-fA-F]+$/, binary: /^[01]+$/, decimal: /^\d+$/, entities: /^\d+$/ }[format];
    if (!pattern.test(tok) || Number.isNaN(value) || value < 0 || value > 255) {
      throw new Utf8Error('parse');
    }
    return value;
  });
  return bytes;
}

/** Decode a formatted UTF-8 byte list → text (fatal: invalid sequences throw). */
export function decode(input, format = 'hex') {
  const bytes = parseBytes(input, format);
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(new Uint8Array(bytes));
  } catch {
    throw new Utf8Error('invalid');
  }
}

// ---------- Page widget ----------

export function mount(root) {
  const $ = (role) => root.querySelector(`[data-role="${role}"]`);
  const input = $('input');
  const output = $('output');
  const error = $('error');
  const value = (name) => root.querySelector(`input[name="${name}"]:checked`).value;

  const update = () => {
    const direction = value('direction');
    const format = value('format');
    error.textContent = '';
    try {
      output.value = direction === 'encode'
        ? encode(input.value, format)
        : decode(input.value, format);
    } catch (e) {
      if (!(e instanceof Utf8Error)) throw e;
      output.value = '';
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

document.querySelectorAll('[data-tool="utf-8"]').forEach(mount);
