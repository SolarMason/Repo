/* ============================================================================
   Solar Mason Repository Dashboard — Service Worker
   Deploys to: https://repo.nepa-pro.com/
   ============================================================================ */

const CACHE_VERSION = 'v7';
const SHELL_CACHE   = `solarmason-shell-${CACHE_VERSION}`;
const API_CACHE     = `solarmason-api-${CACHE_VERSION}`;
const FONT_CACHE    = `solarmason-fonts-${CACHE_VERSION}`;
const ALL_CACHES    = [SHELL_CACHE, API_CACHE, FONT_CACHE];

const SHELL_FILES = [
  './',
  './index.html',
  './manifest.webmanifest',
  './favicon.ico',
  './favicon-32.png',
  './icon-180.png',
  './icon-192.png',
  './icon-512.png',
  './icon-maskable-512.png',
  './og-image.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then((cache) => cache.addAll(SHELL_FILES).catch((err) => {
        console.warn('[SW] Shell precache partial failure:', err);
      }))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names
          .filter((name) => name.startsWith('solarmason-') && !ALL_CACHES.includes(name))
          .map((name) => caches.delete(name))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  let url;
  try { url = new URL(req.url); } catch { return; }

  if (url.hostname === 'api.github.com') {
    event.respondWith(staleWhileRevalidate(req, API_CACHE));
    return;
  }
  if (url.hostname === 'fonts.googleapis.com') {
    event.respondWith(staleWhileRevalidate(req, FONT_CACHE));
    return;
  }
  if (url.hostname === 'fonts.gstatic.com') {
    event.respondWith(cacheFirst(req, FONT_CACHE));
    return;
  }
  if (url.origin === self.location.origin) {
    event.respondWith(networkFirstWithCacheFallback(req, SHELL_CACHE));
    return;
  }
});

async function staleWhileRevalidate(request, cacheName) {
  const cache  = await caches.open(cacheName);
  const cached = await cache.match(request);
  const networkPromise = fetch(request)
    .then((response) => {
      if (response && response.status === 200 && response.type !== 'opaque') {
        cache.put(request, response.clone()).catch(() => {});
      }
      return response;
    })
    .catch(() => cached);
  return cached || networkPromise;
}

async function cacheFirst(request, cacheName) {
  const cache  = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      cache.put(request, response.clone()).catch(() => {});
    }
    return response;
  } catch (err) { throw err; }
}

async function networkFirstWithCacheFallback(request, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      cache.put(request, response.clone()).catch(() => {});
    }
    return response;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return cached;
    if (request.mode === 'navigate') {
      const fallback = await cache.match('./index.html') || await cache.match('./');
      if (fallback) return fallback;
    }
    throw err;
  }
}

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});
