# crypto-it.net

Static website, served by GitHub Pages from the `docs/` folder. Plain HTML/CSS/JS, no build step.

- `docs/` – the website (exactly what is published)
- `tests/` – tests of the online tools, run in a browser
- `../PLAN.md` – migration plan (outside the repository)

## Preview locally

```sh
cd docs && python3 -m http.server 8000
# http://localhost:8000/eng/simple/playfair-cipher.html
```

Links are root-relative (`/eng/...`), so the server must be started in `docs/`.

## Tests

```sh
python3 -m http.server 8001          # in the repository root
# open http://localhost:8001/tests/playfair.test.html – shows "ALL PASSED"
```
