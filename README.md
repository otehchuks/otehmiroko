# Oteh Miroko Aluminum — company website

A fast, accessible static site for an aluminium and glass fabrication contractor:
windows, doors, glass partitions, curtain walls, balustrades and custom fabrication.
The marketing homepage is a single page, with separate Insights article pages.

Built as **static HTML, CSS and vanilla JavaScript** — no framework, no build step, no
runtime dependencies. You can hand the folder to any host and it works.

```
Live preview (local dev):   http://localhost:8080
```

---

## 1. What's included

| Requirement | Where it lives |
|---|---|
| Home / hero with trust metrics | `index.html` → `#home` |
| About Us | `#about` |
| Services (7 scoped offerings) | `#services` |
| Projects / Portfolio with category filter + lightbox | `#projects` |
| Process & differentiators | `#process` |
| Testimonials (accessible carousel) | `#testimonials` |
| Blog / Insights (3 linked articles + listing page) | `#blog`, `insights/` |
| Contact with details + consent-gated embedded map | `#contact` |
| Quote request form (validation, file upload, honeypot) | `#quote` |
| Sticky header, scroll progress, scroll-spy nav | `js/main.js` (modules 02–03) |

**Interactive elements:** quote form with live inline validation and async submit,
filterable image gallery with a keyboard-and-swipe lightbox, testimonial carousel,
animated counters, reveal-on-scroll, lazy map loader, WhatsApp/back-to-top floaters,
smooth scrolling that respects `prefers-reduced-motion`.

---

## 2. Project structure

```
oteh-miroko-aluminum/
├── index.html              Marketing homepage (semantic, SEO + schema.org ready)
├── insights/                Listing page + three linked article pages
├── privacy.html            Draft privacy notice (noindex until approved)
├── terms.html              Draft terms page (noindex until approved)
├── 404.html                Branded not-found page (self-contained)
├── robots.txt              Crawl rules + sitemap pointer
├── sitemap.xml             Homepage + Insights URLs
├── css/
│   └── styles.css          Design tokens → components → responsive ladder
├── js/
│   └── main.js             12 commented modules, IIFE-scoped, zero dependencies
├── images/
│   ├── thumbs/            640w grid thumbnails (what the gallery actually loads)
│   ├── *.jpg              1920w hero + 1200w lightbox-size project images
│   ├── apple-touch-icon.png
│   └── logo.png
├── single-file.html        Generated standalone homepage; supporting pages remain separate
├── tools/
│   ├── make_assets.py      Reproducible image pipeline (resize, compress, tiles)
│   └── build_single_file.py  Builds single-file.html (inlines CSS/JS/images)
├── netlify.toml            Security + cache headers for Netlify
├── vercel.json             Same for Vercel
├── DEPLOYMENT.md           Host-by-host deployment instructions
├── LICENSE                 Proprietary — all rights reserved (edit for your client)
└── README.md               This file
```

---

## 3. Design choices

### Brand identity
The brief asked for "silver, blue, white — clean lines, industrial yet sleek". That's
interpreted as a **deep navy structure with a single bright engineering-blue accent and
brushed-silver neutrals**, rather than a flat silver/blue wash:

| Token | Value | Role |
|---|---|---|
| `--navy-800` | `#0B1D2E` | Primary dark surface — hero, dark sections, footer |
| `--blue-600` | `#1B6FBF` | Single action colour: buttons, links, active states |
| `--blue-500` | `#2E86C1` | Brand mark + dark-surface accents |
| `--silver-100/300` | `#F4F7FA` / `#D8E0E8` | Page tint and hairline borders |

Two type families carry the personality: **Barlow Condensed** (condensed industrial
grotesque) for headings and numerals — it reads like stencilled shop signage — and
**Inter** for body copy, chosen for screen legibility at small sizes.

### Structural ideas
- **The mullion grid.** The hero carries a faint 96 px CSS grid, masked at top and
  bottom — a direct visual quote of a curtain-wall mullion layout. It costs zero bytes
  because it's `background-image: linear-gradient(...)`, not an asset.
- **Zero corner rounding on structure, generous rounding on controls.** Cards and
  sections use 12–18 px radii; buttons are full pills. That contrast is what separates
  "industrial" from "generic SaaS".
- **Numbers over adjectives.** The hero leads with 850+ projects, 16+ years, 5-year
  warranty, 98% satisfaction — animated in so they're noticed without shouting.
- **Motion budget.** One 620 ms fade-up for reveals, one 480 ms slide for the carousel,
  one 2 px lift on card hover. Everything collapses to instant under
  `prefers-reduced-motion: reduce`.

### Deliberate decisions worth flagging to the client
- **Single-page marketing homepage, focused supporting articles.** For an SME contractor,
  the main services and conversion journey stay on one scannable page. The three Insights
  previews link to focused static articles, while the main navigation remains anchor-based.
- **Map is click-to-load.** A Google Maps embed pulls ~700 KB, third-party JS and
  tracking cookies. It's behind a poster + "Load interactive map" button so it costs
  nothing until the visitor wants it.
- **`₦` pricing bands, Nigerian context throughout** — locations, phone formats,
  harmattan/dust maintenance content, and material brand names a local buyer knows.

---

## 4. Technology

| Layer | Choice | Why |
|---|---|---|
| Markup | Hand-written semantic HTML5 | Best possible Lighthouse/SEO ceiling; no hydration tax |
| Styling | Modern CSS: custom properties, `clamp()` fluid type, Grid, Flexbox, logical properties | One stylesheet, no preprocessor, themeable by editing tokens |
| Behaviour | ES2020 vanilla JS in a single IIFE, 12 modules | No framework bytes, no build step, no dependency rot |
| Icons | Inline SVG | Zero requests, inherits `currentColor`, scales perfectly |
| Fonts | Google Fonts with `preconnect` + `display=swap` | Non-blocking; system fallback renders instantly |
| Images | JPEG pipeline via `tools/make_assets.py`; optional single-file bundle via `tools/build_single_file.py` | `srcset`/`sizes` + lazy loading from one script |

**No build step is a feature, not a shortcut.** There's nothing to `npm install`,
nothing to break in six months, and no toolchain for the client's web person to learn.
If the site later grows into a real blog, the same CSS/JS drop straight into
Astro, Eleventy or Next.js.

---

## 5. Responsive strategy

Mobile-first with three upward breakpoints, then a small set of downward overrides for
the navigation drawer.

| Breakpoint | Width | Layout |
|---|---|---|
| Base | 320px+ | Single column, drawer nav, 2-up stats |
| `40em` | 640px+ | 2-up services/gallery/posts, 4-up stats, 2-col form rows |
| `56.25em` | 900px+ | 3-up services, 3-up process, 2-col About/Contact, desktop nav |
| `75em` | 1200px+ | 3-up gallery, wider About media |

Typography is fluid via `clamp()` rather than stepped, so nothing ever looks cramped
between breakpoints. Touch targets are ≥44×44 px throughout.

---

## 6. Accessibility (target: WCAG 2.1 AA)

Implemented, not aspirational:

- **Structure:** one `<h1>`, ordered heading levels, landmark elements
  (`header`, `nav`, `main`, `footer`, `section[aria-labelledby]`), `skip-link`.
- **Colour:** body text `#5B6B7A` on `#FFFFFF` ≈ 5.6:1; headings and button text far
  higher. Every link and button is distinguishable without relying on colour alone.
- **Focus:** a 3 px `:focus-visible` ring on every interactive element, switched to a
  light blue on dark surfaces so it never disappears.
- **Modals:** the lightbox is a proper `role="dialog" aria-modal="true"` with a focus
  trap, `Esc` to close, arrow/Home/End keys, and focus returned to the thumbnail that
  opened it.
- **Forms:** `label` on every control, `aria-describedby` wired to error slots,
  `aria-invalid` toggled on error, an `aria-live` status banner, errors conveyed by
  icon + text + colour, consent unticked by default, `autocomplete` tokens throughout.
- **Motion:** all animation is disabled under `prefers-reduced-motion: reduce`,
  including smooth scrolling and the carousel transition.
- **Non-JS:** content is visible and readable with JavaScript off. The reveal animation
  is only *armed* when JS is confirmed present (inline `js-ready` flag), so nothing can
  ever be stranded at `opacity: 0`.
- **Also handled:** `forced-colors` (Windows High Contrast), `@media print`, and
  `lang="en"` with real `<time>`, `<address>` and `<blockquote>` semantics.

---

## 7. Performance

| Technique | Effect |
|---|---|
| Two-variant hero `srcset` (960w / 1920w) | Phones download 117 KB instead of 286 KB |
| Gallery `srcset` 640w thumbnails → 1200w lightbox | Grid loads 34–83 KB per tile; full size only on open |
| `loading="lazy"` + `decoding="async"` on everything below the fold | Keeps the critical path to the hero |
| `fetchpriority="high"` on the hero only | LCP candidate starts downloading first |
| Explicit `width`/`height` on every image | Zero cumulative layout shift |
| Click-to-load map embed | Removes ~700 KB and all third-party JS from first paint |
| Inline SVG logo/favicon/icons | ~15 fewer HTTP requests |
| Pre-blurred hero JPEG | The CSS scrim sits at 72–92% opacity, so a 1.4 px pre-blur is invisible on screen but nearly halves the payload |
| Image pipeline (`tools/make_assets.py`) | Deterministic, repeatable, strips metadata |

Measured payload for the initial viewport: **≈ 190 KB** (HTML + CSS + JS + hero on
mobile), with the rest streamed in lazily.

Try it yourself: `npx lighthouse http://localhost:8080 --view` (Chrome required).

---

## 8. SEO

- Unique title/description, canonical, `theme-color`, Open Graph + Twitter cards.
- **schema.org `LocalBusiness`** JSON-LD with address, geo, opening hours, area served
  and an `OfferCatalog` of the seven services — the single biggest local-SEO win for a
  contractor. **Replace the placeholder phone, email, geo and review count.**
- All service, project and testimonial copy is real, keyword-relevant prose — not
  lorem ipsum — so the page has legitimate content to rank.
- Descriptive `alt` text on every content image; decorative images correctly `alt=""`.
- `robots.txt` + `sitemap.xml`; semantic headings crawlers can parse.

---

## 9. Customising it for the client

Everything brand-related is a token in `css/styles.css` §01:

```css
:root {
  --blue-600: #1b6fbf;   /* swap for the client's exact brand blue */
  --navy-800: #0b1d2e;   /* structural dark */
  --font-display: "Barlow Condensed", ...;
}
```

**Before going live, replace the placeholder content:**

1. **Business details** — confirm the phone number `+234 816 785 9034` in the site and schema,
   `hello@otehmirokoaluminum.com`, the Ikeja address, opening hours, and the
   `LocalBusiness` JSON-LD block (including `aggregateRating`, which must reflect real
   reviews).
2. **Form destination** — the form is configured for Netlify Forms in `index.html`.
   Deploy on Netlify to receive submissions; if you use another host, replace the
   Netlify attributes and set a real endpoint as described in §10.
3. **Map** — `js/main.js` → `MAP_EMBED_SRC` (Google Maps → Share → Embed a map).
4. **Photography** — 5 of the 15 images are drawn *technical-drawing placeholder tiles*
   (distinctly labelled `PLACEHOLDER — REPLACE WITH SITE PHOTOGRAPHY`):
   `project-netting.jpg`, `blog-glass-types.jpg`, `blog-maintenance.jpg`,
   `blog-cost-factors.jpg`, `map-poster.jpg`. Drop real photos over those filenames at
   the same dimensions, then run `python3 tools/make_assets.py`.
5. **Domain** — replace `https://www.otehmirokoaluminum.com/` in `index.html`
   (canonical + OG), `robots.txt` and `sitemap.xml`.
6. **Insights** — the homepage previews link to three static articles in `insights/`,
   with a listing at `insights/index.html`. Keep those links and `sitemap.xml` in sync
   when adding, removing or renaming articles.

---

## 10. Making the quote form actually send

The form currently uses **Netlify Forms** and submits asynchronously with `fetch`, so
the visitor stays on the page. Netlify must detect the form during deployment; the form
has `name="quote"`, `data-netlify="true"`, a matching hidden `form-name` field and the
`company_url` honeypot. Keep `data-demo="false"` when using the live handler.

If you deploy somewhere other than Netlify, replace the Netlify attributes and set a
real service/API endpoint in the form's `action`. For example, Formspree provides a
URL such as `https://formspree.io/f/abcdwxyz`; file-upload support depends on the plan.
A custom endpoint should accept the form's multipart POST and return a successful HTTP
status. The client displays an error and direct-contact fallback if the request fails.

The honeypot silently swallows bot submissions. The client also rejects more than
three attachments, unsupported file types and files over 5 MB each before upload.

---

## 11. The single-file build (optional)

You asked whether the code should ship as one HTML file or as separate files. The
project is built as **separate files** — that's what you want to deploy, because
browsers cache the CSS, JS and each image independently and the lightbox can serve
full-resolution photos.

For the cases where a single file is genuinely better — previewing inside a sandboxed
pane, emailing a demo, or showing it on site from a phone or USB stick — there's a
generated build:

```bash
python3 tools/build_single_file.py     # → single-file.html (~1 MB)
```

It inlines the homepage stylesheet, script and images (as base64 data URIs), so the
homepage renders without its usual local asset requests. The separate Insights and
legal pages are not embedded; keep the site folder alongside the file if their links
need to work. Two deliberate trade-offs: base64 inflates bytes ~33% (so the multi-file
version always loads faster), and the lightbox uses 640 px thumbnails instead of the
1200 px originals to keep the file smaller.

`single-file.html` is a build artefact — edit `index.html`, `css/styles.css` or
`js/main.js` and re-run the script. Never edit it by hand.

---

## 12. Deployment

Full instructions for Netlify, Vercel, GitHub Pages, Cloudflare Pages, cPanel/FTP and
nginx are in **[DEPLOYMENT.md](DEPLOYMENT.md)**. The 60-second version:

```bash
# 1. Publish the repository to GitHub, then:
# Netlify → Add new site → Import from Git → pick the repo
#   Build command:     (leave empty)
#   Publish directory: .
# Done. netlify.toml in this repo supplies headers and caching automatically.
```

To run it locally at any time (CSS and JS are blocked under `file://` in some
browsers, so always use a server):

```bash
python3 -m http.server 8080      # then open http://localhost:8080
# or: npx serve .
```

---

## 13. Creating the GitHub repository

The repo is already initialised with a first commit:

```bash
cd oteh-miroko-aluminum
git log --oneline

# Create an empty repo on GitHub (no README, no .gitignore), then:
git remote add origin https://github.com/<your-org>/oteh-miroko-aluminum.git
git branch -M main
git push -u origin main
```

This sandbox has no access to your GitHub account, so the `git push` is yours to run —
everything else (commit history, config, docs) is prepared and waiting.

Two housekeeping notes for pushing the prepared commit from here:

1. `git/config` is excluded from workspace snapshots (it can hold credentials), so the
   local `user.name` / `user.email` set for the commit may not survive. If git complains,
   run `git config user.name "Your Name" && git config user.email "you@example.com"`
   before committing again.
2. The commit already exists and is ready to push as-is — `git log --oneline` should show
   `Initial commit: Oteh Miroko Aluminum marketing site`.

---

## 14. Browser support & licence

Chromium 88+, Firefox 85+, Safari 14.5+, Edge 88+ (2021 baseline). Older browsers get a
fully usable site: no `:has()` or container queries are used for anything essential, the
carousel and lightbox degrade to plain content, and `IntersectionObserver` fallbacks
render everything immediately.

Code is proprietary — see [LICENSE](LICENSE). The photography in this repository is
AI-generated/placeholder and carries no third-party licensing obligations; replace it
with the client's own project photography before launch.
