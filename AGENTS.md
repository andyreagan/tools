# AGENTS.md — Conventions for tools.andyreagan.com

This file describes the conventions for adding tools to this repo so that AI
agents (and humans) can follow them consistently.

---

## Style philosophy

Inspired by [bettermotherfuckingwebsite.com](http://bettermotherfuckingwebsite.com/):
keep it simple, load nothing you don't need.

- **No web fonts.** Use the system font stack: `system-ui, sans-serif` (or
  `Georgia, serif` if a serif feel is wanted). Zero font network requests.
- **Minimal CSS.** A handful of rules for readable line length, comfortable
  padding, and legible font size. No frameworks, no resets beyond `box-sizing`.
- **No CDN scripts unless the tool genuinely requires them.** Don't pull in
  libraries for things that can be done in 10 lines of vanilla JS.
- **No tracking, no analytics, no cookies.**

The goal is a page that loads in one round-trip (the HTML file itself) for
self-contained tools, and two (HTML + `footer.js`) for any tool that links
back to source.

---

## Tool formats

There are two supported layouts. Choose the simplest one that works.

### Option 1 — single file: `tool-name.html`

A self-contained HTML file at the repo root. No build step, no dependencies
beyond what is fetched at runtime (CDNs are fine). This is the preferred
format for tools that can be written in one file.

```
tools/
  my-calculator.html   ← the whole tool
  index.html           ← add a card linking to my-calculator.html
```

### Option 2 — directory: `tool-name/index.html`

A directory containing an `index.html` plus any local assets. Use this when
the tool needs supporting files (e.g. a JSON data file, a local JS module, or
an Observable notebook iframe wrapper). Each directory is isolated — assets
inside it don't clash with other tools.

```
tools/
  my-calculator/
    index.html         ← entry point
    data.json          ← local asset (optional)
  index.html           ← add a card linking to my-calculator/
```

Observable notebooks that can't be made self-contained use this format: the
`index.html` is a thin iframe wrapper pointing to the live Observable embed
URL (`https://observablehq.com/embed/@andyreagan/<notebook>?cell=*`).

---

## Standard footer

Every tool page must include a footer linking back to its source on GitHub.
The footer should be injected by a shared script so it stays consistent.

### Shared script: `footer.js`

Include this at the bottom of `<body>`:

```html
<script src="/footer.js"></script>
```

`footer.js` (at the repo root) auto-detects the current page path and injects
a footer with:

- **Home** → `/`
- **View source** → `https://github.com/andyreagan/tools/blob/main/<file>`
- **Changes** → `https://github.com/andyreagan/tools/commits/main/<file>`

For a single-file tool the `<file>` is `tool-name.html`. For a directory tool
it is `tool-name/index.html`.

### `footer.js` implementation

```js
(function () {
  // Derive the GitHub file path from the current URL
  let path = window.location.pathname.replace(/^\//, '') || 'index.html';
  if (path.endsWith('/')) path += 'index.html';
  if (!path.includes('.')) path += '.html'; // bare slug → .html

  const base = 'https://github.com/andyreagan/tools/blob/main/';
  const hist = 'https://github.com/andyreagan/tools/commits/main/';

  const footer = document.createElement('footer');
  footer.style.cssText =
    'width:100%;box-sizing:border-box;font-family:system-ui,sans-serif;' +
    'font-size:12px;text-align:center;padding:1.5rem 1rem;' +
    'border-top:1px solid currentColor;margin-top:2rem;opacity:0.6;';
  footer.innerHTML =
    `<a href="/">Home</a> &nbsp;·&nbsp; ` +
    `<a href="${base}${path}">View source</a> &nbsp;·&nbsp; ` +
    `<a href="${hist}${path}">Changes</a>`;

  document.body.appendChild(footer);
})();
```

Place this file at `tools/footer.js` and commit it. Tools served from a
subdirectory (`tool-name/index.html`) still reference `/footer.js` (absolute
path) so the same file is used everywhere.

---

## index.html cards

Every tool must have a card in the root `index.html` grid. Copy an existing
card and update the `href`, tag, name, and description. Keep descriptions to
one sentence (≤ 15 words).

---

## Checklist for a new tool

- [ ] Create `tool-name.html` or `tool-name/index.html`
- [ ] Add `<script src="/footer.js"></script>` before `</body>`
- [ ] Add a card to `index.html`
- [ ] Commit everything (no build step needed)
