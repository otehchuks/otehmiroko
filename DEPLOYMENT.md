# Deployment guide — Oteh Miroko Aluminum

The site is **pure static files**. There is no build command, no environment variable
and no server-side runtime. If a host can serve a folder over HTTP, it can host this
site.

- **Build command:** *(none — leave blank)*
- **Publish / output directory:** `.` (the repository root)
- **Entry point:** `index.html`

---

## Before you deploy: go-live checklist

| # | Task | File |
|---|---|---|
| 1 | Confirm the supplied phone/WhatsApp number `+234 816 785 9034` is correct everywhere | `index.html`, `404.html`, `js/main.js` |
| 2 | Replace `hello@` / `projects@otehmirokoaluminum.com` | `index.html` |
| 3 | Replace the Ikeja address + opening hours | `index.html` (`#contact`) |
| 4 | Update `LocalBusiness` JSON-LD: phone, email, geo, `aggregateRating` | `index.html` `<head>` |
| 5 | Point the quote form at a real endpoint | `index.html` `action="…"` |
| 6 | Set the real Google Maps embed URL | `js/main.js` `MAP_EMBED_SRC` |
| 7 | Swap the 5 labelled placeholder tiles for real photos, then re-run the pipeline | `images/`, `tools/make_assets.py` |
| 8 | Replace `https://www.otehmirokoaluminum.com/` with the live domain | `index.html`, `robots.txt`, `sitemap.xml` |
| 9 | Add the platform verification files you need (Search Console, analytics) | root |
| 10 | Test the form, WhatsApp link and phone links on a real phone | — |
| 11 | Review the Privacy and Terms drafts; remove `noindex` only after approval | `privacy.html`, `terms.html` |

Verify locally first:

```bash
python3 -m http.server 8080     # http://localhost:8080
```

> **Never open `index.html` by double-clicking it.** Under the `file://` protocol most
> browsers block the `css/` and `js/` folders for security reasons and you'll see an
> unstyled page. Always serve it over HTTP.

---

## Option A — Netlify (recommended for this project)

Fastest path, free tier includes HTTPS, a global CDN, form handling and deploy previews.

**Via the dashboard**
1. Push this repository to GitHub.
2. Netlify → **Add new site** → **Import an existing project** → GitHub → pick the repo.
3. Build command: *(leave empty)* · Publish directory: `.`
4. **Deploy.** `netlify.toml` in this repo applies security headers, long-lived
   immutable caching for `css/` `js/` `images/` and a `404.html` fallback automatically.

**Via CLI**
```bash
npm i -g netlify-cli
netlify login
netlify deploy --dir . --prod
```

**Custom domain:** Site settings → Domain management → Add domain → follow the DNS
instructions → Netlify provisions a Let's Encrypt certificate automatically.

**Netlify Forms** (no backend): the quote form in this repo is already configured with
`name="quote"`, `data-netlify="true"`, a hidden `form-name` value and the
`company_url` honeypot. It posts to `/` asynchronously; deploy to Netlify so the form is
picked up during the build. Submissions appear in the Netlify dashboard and can be
forwarded by email from the site settings.

---

## Option B — Vercel

```bash
npm i -g vercel
vercel          # preview deployment
vercel --prod   # production
```

Or import the GitHub repo at vercel.com/new. Framework preset: **Other**; leave the
build command empty and set the output directory to `.`. `vercel.json` supplies the
security and cache headers.

---

## Option C — GitHub Pages (free, repo-hosted)

1. Push to GitHub, then **Settings → Pages**.
2. Source: *Deploy from a branch* → branch `main` → folder `/ (root)` → **Save**.
3. The site appears at `https://<user>.github.io/<repo>/` within a minute or two.

This repo already includes **`.nojekyll`**, which stops Jekyll from ignoring folders
that begin with an underscore or dot.

**Custom domain:** add a file named `CNAME` at the root containing the bare domain
(e.g. `otehmirokoaluminum.com`), then in your DNS provider create:

| Type | Name | Value |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `<user>.github.io` |

Tick **Enforce HTTPS** once the certificate is issued.

---

## Option D — Cloudflare Pages

1. Dashboard → **Workers & Pages** → **Create** → **Pages** → connect the Git repo.
2. Framework preset: **None** · Build command: *(empty)* · Build output directory: `/`.
3. Free unlimited bandwidth, global CDN, automatic HTTPS. Cloudflare also gives you
   Web Analytics and Bot Fight Mode at no cost.

---

## Option E — Traditional hosting (cPanel / FTP / shared hosting)

1. Zip the project folder *(or upload the files as-is)*.
2. cPanel → **File Manager** → `public_html/` → **Upload** → extract.
3. Confirm the structure is `public_html/index.html` — **not**
   `public_html/oteh-miroko-aluminum/index.html`. Nested uploads are the single
   most common cause of "the site is a directory listing".
4. In cPanel → **SSL/TLS Status**, run AutoSSL so the site serves over HTTPS.
5. Add a `.htaccess` at the root for compression, caching and clean URLs:

```apache
# --- Force HTTPS -------------------------------------------------------------
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# --- Remove trailing www (pick ONE canonical host) ---------------------------
RewriteCond %{HTTP_HOST} ^www\.(.+)$ [NC]
RewriteRule ^ https://%1%{REQUEST_URI} [L,R=301]

# --- Compression -------------------------------------------------------------
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript image/svg+xml
</IfModule>

# --- Caching: version-bust by renaming, not by re-uploading ------------------
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/jpeg "access plus 1 year"
  ExpiresByType image/png  "access plus 1 year"
  ExpiresByType text/css   "access plus 1 year"
  ExpiresByType application/javascript "access plus 1 year"
  ExpiresByType text/html  "access plus 1 hour"
</IfModule>

# --- Custom error page -------------------------------------------------------
ErrorDocument 404 /404.html

# --- Basic hardening ---------------------------------------------------------
ServerTokens Prod
<FilesMatch "^\.">
  Require all denied
</FilesMatch>
```

> The 1-year CSS/JS cache above means **renaming the file is how you bust the cache**.
> After editing, change `styles.css` → `styles.v2.css` and update the `<link>` in
> `index.html`. (Modern hosts using `netlify.toml` / `vercel.json` handle this with
> content hashes automatically.)

---

## Option F — nginx / VPS

```nginx
server {
    listen 443 ssl http2;
    server_name otehmirokoaluminum.com www.otehmirokoaluminum.com;
    root /var/www/oteh-miroko-aluminum;
    index index.html;

    # Certificate managed by certbot: sudo certbot --nginx -d <domain>
    ssl_certificate     /etc/letsencrypt/live/otehmirokoaluminum.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/otehmirokoaluminum.com/privkey.pem;

    gzip on;
    gzip_types text/css application/javascript image/svg+xml text/html;
    gzip_min_length 1024;

    location ~* \.(jpg|jpeg|png|svg|webp|avif|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    location ~* \.(css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    location = /index.html {
        add_header Cache-Control "no-cache, must-revalidate";
    }

    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    error_page 404 /404.html;

    location / { try_files $uri $uri/ =404; }
}
```

Reload with `sudo nginx -t && sudo systemctl reload nginx`.

---

## Post-deployment verification

1. **HTTPS & redirects** — visit both `http://` and the `www` variant; both must 301 to
   the canonical HTTPS URL.
2. **Mobile pass** — thumb-test the drawer nav, gallery filter, lightbox swipe and the
   quote form on a real phone.
3. **Form test** — submit a real enquiry end-to-end and confirm it arrives. Check the
   honeypot: submit with `company_url` filled via dev tools and confirm it's dropped.
4. **Lighthouse** — Chrome DevTools → Lighthouse → Mobile + Desktop. Expect 95+ in
   Performance, Accessibility, Best Practices and SEO.
5. **Search Console** — add the property, submit
   `https://<domain>/sitemap.xml`, and request indexing of the homepage.
6. **Rich results** — test the homepage at
   [search.google.com/test/rich-results](https://search.google.com/test/rich-results) to
   confirm the `LocalBusiness` schema parses.
7. **Broken links** — run a crawl (Screaming Frog free tier, or `npx broken-link-checker`).
8. **Google Business Profile** — for a local contractor this drives more leads than the
   website itself. Claim it, match the name/address/phone to the JSON-LD exactly, and
   link to the site.

---

## Updating the site later

```bash
# Edit content, then:
python3 tools/make_assets.py                      # only if images changed
python3 -m http.server 8080                       # check locally

# Version-bust static assets if your host requires it (see Option E):
#   css/styles.css → css/styles.v2.css   (update the <link> in index.html)
#   js/main.js     → js/main.v2.js       (update the <script> in index.html)

git add -A && git commit -m "Update project portfolio" && git push
```

Git-connected hosts (Netlify, Vercel, Cloudflare Pages) redeploy automatically on push.
For cPanel hosts, upload the changed files only.
