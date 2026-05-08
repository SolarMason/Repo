# Solar Mason Repo Dashboard

Live: **https://repo.nepa-pro.com**
Source: **https://github.com/SolarMason/Repo**

A self-updating macOS-style dashboard that tracks every public repo on the SolarMason GitHub account. Installable as a fully-branded iOS / Android / desktop PWA with offline support, custom icon, and OG share card.

---

## Files in this repo

| File                       | Purpose                                                      |
|----------------------------|--------------------------------------------------------------|
| `index.html`               | The dashboard. Served at the root URL.                       |
| `service-worker.js`        | Caches app shell + GitHub API for instant + offline loads.   |
| `manifest.webmanifest`     | PWA manifest. Defines name, icons, theme, install behavior.  |
| `icon-180.png`             | Apple touch icon (180×180). iPhone / iPad home screen.       |
| `icon-192.png`             | Android / Chrome icon (192×192).                             |
| `icon-512.png`             | Large PWA icon (512×512). Splash screens, app drawers.       |
| `icon-maskable-512.png`    | Android adaptive icon (512×512, full-bleed, 80% safe zone).  |
| `favicon-32.png`           | Browser tab favicon (32×32).                                 |
| `favicon.ico`              | Multi-size legacy favicon (16/32/48).                        |
| `og-image.png`             | 1200×630 social share card (Twitter / iMessage / LinkedIn).  |
| `build-assets.py`          | Regenerates all icons + OG card from a single design spec.   |
| `CNAME`                    | Tells GitHub Pages which custom domain to serve.             |
| `.nojekyll`                | Tells GitHub Pages to skip Jekyll processing (faster).       |
| `README.md`                | This file.                                                   |

---

## One-time deployment

### 1. Push these files to `main`

```bash
git clone https://github.com/SolarMason/Repo.git
cd Repo
# copy all files from this folder into here, including .nojekyll
git add .
git commit -m "Initial dashboard deploy with branded PWA assets"
git push origin main
```

### 2. Enable GitHub Pages

In the repo: **Settings → Pages**

- **Source:** Deploy from a branch
- **Branch:** `main`  /  **Folder:** `/ (root)`
- Click **Save**

### 3. Add the DNS record

At your DNS provider for `nepa-pro.com`:

| Type    | Name (host) | Value                  | TTL   | Proxy/Cloud |
|---------|-------------|------------------------|-------|-------------|
| `CNAME` | `repo`      | `solarmason.github.io` | Auto  | DNS only*   |

\* If using **Cloudflare**, set the record to **DNS only** (gray cloud), not Proxied (orange cloud) — Cloudflare proxying breaks GitHub Pages' Let's Encrypt cert provisioning. You can flip it back to Proxied *after* HTTPS is enforced.

### 4. Confirm in GitHub Pages settings

Back in **Settings → Pages**:

- The custom domain field should already say `repo.nepa-pro.com` (the `CNAME` file populates it).
- Wait for the green checkmark next to "DNS check successful" — usually 1–10 minutes.
- Once green, check **Enforce HTTPS**.

### 5. Visit the site

Go to **https://repo.nepa-pro.com**. First load fetches the GitHub API; after that the service worker takes over and subsequent loads are instant — even offline.

---

## Brand assets

The Solar Mason mark is a stylized sun rising over three solar-panel slats, set on a gradient from warm orange (`#ff9f0a`) to deep red (`#ff3b30`). All icons and the OG card are generated from a single Python script — running it again produces the full set in pixel-perfect form.

To regenerate after design changes:

```bash
python3 build-assets.py
```

This rewrites all `icon-*.png`, `favicon-*`, and `og-image.png` files. Commit them.

### What goes where on which device

| Surface                        | File                       |
|--------------------------------|----------------------------|
| iPhone home screen             | `icon-180.png`             |
| Android home screen            | `icon-maskable-512.png`    |
| Android Chrome PWA install     | `icon-192.png` / `icon-512.png` |
| macOS / Windows / Linux PWA    | `icon-512.png`             |
| Browser tab                    | `favicon-32.png` + `favicon.ico` |
| iMessage / Slack / Twitter / LinkedIn link preview | `og-image.png` |

### How the OG share card looks

When `https://repo.nepa-pro.com` is pasted into iMessage, Slack, Twitter, LinkedIn, Discord, or any other app that reads Open Graph tags, the recipient sees the 1200×630 branded card with the Solar Mason logo, the title, the tagline ("Live · Auto-updating · 5-minute refresh"), and the URL pill — instead of a plain text link.

To re-test the share card after changes, use [opengraph.xyz](https://www.opengraph.xyz/) — paste the URL and it shows you exactly what each platform renders.

---

## Updating the dashboard

Just push new commits to `main`. GitHub Pages redeploys within ~30 seconds. Open tabs see the "A new version is available — Reload" toast on the next focus check (within 30 minutes), or you can hard-refresh.

When you change `service-worker.js` itself, bump `CACHE_VERSION` at the top of the file (`v5` → `v6`). This wipes all old caches on every visitor's next load, guaranteeing a clean update.

---

## How auto-updating works

The dashboard pulls live from `https://api.github.com/users/SolarMason/repos`:

- **On open:** instant render from `localStorage` cache, then background refresh.
- **Every 5 minutes** while the tab is open.
- **When the tab regains focus** if the data is older than 60 seconds.
- **Pull-to-refresh** on mobile.
- **Manual refresh button** or `Cmd/Ctrl+R` on desktop.

When you create a new repo, it appears in the dashboard within 5 minutes — no config change needed.

---

## Installing as a branded app

### iPhone / iPad

1. Open `https://repo.nepa-pro.com` in **Safari** (Safari only — iOS doesn't let other browsers install PWAs).
2. Tap **Share** → **Add to Home Screen** → **Add**.
3. Launches fullscreen with the Solar Mason icon, no Safari chrome.

### Android

Chrome offers an "Install app" prompt automatically once the manifest loads. Or: menu (⋮) → **Install app**. The Solar Mason icon appears in the app drawer with the proper adaptive shape.

### macOS / Windows / Linux

Chrome/Edge: click the install icon (⊕) in the address bar, or menu → **Install Solar Mason**. Opens as a standalone window with the Solar Mason icon in the dock/taskbar.

---

## GitHub API rate limit

Unauthenticated GitHub API: 60 requests/hour per IP. Each refresh = 1 request. At 5-min intervals that's 12/hour — well under the limit. Cache layers (localStorage + service worker) mean a rate-limit error never breaks the UI; users keep seeing cached data until the limit resets.

If you ever exceed it (multiple users on same network, or you add more refresh sources), wire in a fine-grained Personal Access Token: 5,000 requests/hour. Ping me and I'll add the auth flow.

---

## Troubleshooting

**OG card doesn't appear in iMessage / Slack / Twitter previews**
Social platforms aggressively cache OG data. After deploying, force a re-scrape:
- Twitter/X: paste the URL into [Card Validator](https://cards-dev.twitter.com/validator)
- Facebook/iMessage (uses FB scraper): [Sharing Debugger](https://developers.facebook.com/tools/debug/) → "Scrape Again"
- LinkedIn: [Post Inspector](https://www.linkedin.com/post-inspector/)
- Generic test: [opengraph.xyz](https://www.opengraph.xyz/)

**iPhone home screen icon shows a generic screenshot instead of the branded icon**
You likely added the site to the home screen *before* the icons were deployed. Remove the icon, hard-refresh the page in Safari, and add to home screen again.

**"DNS check unsuccessful" in GitHub Pages settings**
DNS hasn't propagated. Run `dig repo.nepa-pro.com CNAME +short` — should return `solarmason.github.io.`. If it doesn't, the record isn't live yet, or you set an A record instead of CNAME.

**Site loads but service worker doesn't register**
SW requires HTTPS. Wait for Let's Encrypt provisioning (up to 24 hours). Cloudflare users: ensure the record is on DNS only (gray cloud) until HTTPS is enforced.

**Old version stuck after deploy**
SW takes one full reload to swap in. The "Reload" toast handles this. To force-clear: DevTools → Application → Service Workers → Unregister, then hard-reload. Bumping `CACHE_VERSION` does this for everyone automatically.

**Custom domain disappeared after a push**
The `CNAME` file got deleted. Restore it with the single line `repo.nepa-pro.com` and push.

---

## Local development

Service workers and PWA install require HTTPS or `localhost` (not `file://`). Easiest local test:

```bash
cd Repo
python3 -m http.server 8000
# open http://localhost:8000
```

`localhost` is exempt from the HTTPS requirement — full PWA experience including service worker, install prompts, and offline mode all work locally.
