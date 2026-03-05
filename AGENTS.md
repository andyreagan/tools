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

## Visual style guide

Every page uses a shared light, pastel color palette. The reference
implementation is `ftp-vo2max.html` — match its look and feel.

### Color tokens

Use CSS custom properties on `:root`:

```css
:root {
  --bg:      #f0ede8;   /* warm beige page background */
  --surface: #ffffff;   /* white card / panel fill */
  --dark:    #1a1a1a;   /* primary text, borders */
  --mid:     #666;      /* secondary text, labels */
  --muted:   #999;      /* tertiary text, hints */
  --border:  #ddd;      /* light dividers, input borders */
  --accent:  #e74c3c;   /* red accent — links, tags, highlights */
}
```

Tools may add extra semantic tokens (e.g. `--green`, `--gold`, `--danger`)
but the seven above must stay consistent across every page.

### Background

```css
body {
  background: var(--bg);          /* #f0ede8 */
}
body::before {
  content: ''; position: fixed; inset: 0; z-index: 0;
  background-image: repeating-linear-gradient(
    45deg, transparent, transparent 20px,
    rgba(0,0,0,0.02) 20px, rgba(0,0,0,0.02) 21px
  );
}
```

The subtle diagonal stripe overlay is used on every page. All page content
must sit above it with `position: relative; z-index: 1`.

### Cards

```css
.card {
  background: var(--surface);     /* white */
  border: 2px solid var(--dark);  /* strong dark border */
  border-radius: 4px;
  padding: 2rem;
}
```

### Inputs

```css
input, select, textarea {
  font-size: 1rem;
  padding: .4rem .6rem;
  border: 2px solid var(--border);
  border-radius: 3px;
  background: #fafafa;
  color: var(--dark);
}
input:focus, select:focus, textarea:focus {
  outline: none;
  border-color: var(--dark);
}
```

### Toggle / pill buttons

Active state: `background: var(--dark); color: #fff; border-color: var(--dark)`.
Inactive state: `background: transparent; color: var(--mid); border: 2px solid var(--border)`.

### Typography

- **Font family:** `system-ui, sans-serif` everywhere (monospace for
  chess timer is the one exception).
- **Headings:** `font-weight: 700`. Page titles use `text-transform: uppercase`.
- **Labels:** `font-size: .75rem; font-weight: 600; letter-spacing: .12em;
  text-transform: uppercase; color: var(--muted)`.
- **Body text:** `color: var(--dark)` with `line-height: 1.6`.

### Footer

The shared `footer.js` injects a footer with:
- Transparent background (no fill color)
- `border-top: 1px solid #ddd`
- Link color: `#666` (subdued gray, not the accent red)
- Text color: `#999`

### Do / Don't

| ✅ Do | ❌ Don't |
|-------|---------|
| Use `--bg` (#f0ede8) for page background | Use dark backgrounds (#0f0f0f, #111, etc.) |
| Use `--surface` (#fff) for cards | Use colored or dark card fills |
| Use 2px solid `--dark` for card borders | Use box-shadow-heavy card styles |
| Keep accent red for links and tags only | Use accent color for large areas |
| Use the diagonal stripe `body::before` | Use other background patterns |
| Scope Observable overrides to `.card` | Use unscoped `!important` overrides |

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

**Observable notebooks** are embedded as JS modules (not iframes) so we
control their styling. The HTML page imports the notebook's runtime and
renders named cells into `<div>` targets inside a `.card`. CSS overrides
scoped to `.card` force Observable's injected elements to use our dark-on-
light palette:

```css
.card h1,.card h2,.card h3,.card h4,.card h5,.card h6,
.card p,.card span,.card label,.card div,.card a,
.card strong,.card em,.card td,.card th,.card li {
  color: var(--dark) !important;
}
.card a { color: var(--accent) !important; }
```

Scope overrides to `.card` so they don't bleed into the footer.

If a directory tool grows to just one file with no local assets, flatten it
back to a single `tool-name.html` at the root.

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

The footer uses a transparent background with a light border, subdued gray
links (#666), and muted text (#999) — matching the visual style guide. It
also fetches the last commit date from the GitHub API.

See `footer.js` at the repo root for the current implementation.

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
