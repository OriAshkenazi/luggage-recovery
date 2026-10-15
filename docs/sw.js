/**
 * Offline support for the recovery page. Paths are relative to this file, so it
 * works under the GitHub Pages project path (/luggage-recovery/).
 * The page and translations: network first, cache when offline (so copy edits show at once).
 * Other same-origin GETs (CSS, JS, font, icon): cache first, refreshed in the background.
 * Everything else (WhatsApp, Formspree, tel:, mailto:) goes straight to the network.
 */
const CACHE = 'luggage-recovery-v8';
const PRECACHE = [
    './',
    'index.html',
    'style.css?v=20261017',
    'script.js?v=20261017',
    'fonts/assistant.woff',
    'favicon.svg',
    'manifest.json',
    'i18n/en.json',
    'i18n/he.json',
    'trip.json',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        // cache: 'reload' skips the browser's HTTP cache (GitHub Pages sends max-age=600)
        caches.open(CACHE)
            .then((cache) => cache.addAll(PRECACHE.map((url) => new Request(url, { cache: 'reload' }))))
            .then(() => self.skipWaiting())
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
    const url = new URL(request.url);
    const fresh = request.mode === 'navigate' || url.pathname.endsWith('.json');
    event.respondWith(
        caches.open(CACHE).then(async (cache) => {
            // Fresh resources revalidate with the server every time (a 304 when unchanged)
            const network = (fresh ? fetch(request.url, { cache: 'no-cache', credentials: 'same-origin' }) : fetch(request)).then((response) => {
                if (response.ok) cache.put(request, response.clone());
                return response;
            });
            if (fresh) {
                return network.catch(async () => (await cache.match(request)) || cache.match('index.html'));
            }
            const cached = await cache.match(request);
            if (cached) {
                network.catch(() => {}); // background refresh; offline is fine
                return cached;
            }
            return network;
        })
    );
});
