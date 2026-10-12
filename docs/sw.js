/**
 * Offline support for the recovery page. Paths are relative to this file, so it
 * works under the GitHub Pages project path (/luggage-recovery/).
 * Same-origin GETs: served from cache, refreshed in the background.
 * Everything else (WhatsApp, Formspree, tel:, mailto:) goes straight to the network.
 */
const CACHE = 'luggage-recovery-v2';
const PRECACHE = [
    './',
    'index.html',
    'style.css?v=20261012',
    'script.js?v=20261012',
    'fonts/assistant.woff',
    'favicon.svg',
    'manifest.json',
    'i18n/en.json',
    'i18n/he.json',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    if (request.method !== 'GET' || new URL(request.url).origin !== self.location.origin) return;
    event.respondWith(
        caches.open(CACHE).then(async (cache) => {
            const cached = await cache.match(request);
            const network = fetch(request)
                .then((response) => {
                    if (response.ok) cache.put(request, response.clone());
                    return response;
                })
                .catch(() => cached);
            return cached || network;
        })
    );
});
