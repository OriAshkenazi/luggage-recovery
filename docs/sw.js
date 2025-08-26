/**
 * Service Worker for Lost Luggage Recovery System
 * Provides offline functionality and fast loading
 */

const CACHE_NAME = 'luggage-recovery-v1.0.0';
const STATIC_CACHE_NAME = 'static-v1.0.0';
const RUNTIME_CACHE_NAME = 'runtime-v1.0.0';

// Files to cache immediately
const STATIC_FILES = [
    '/',
    '/index.html',
    '/style.css',
    '/script.js',
    // Add any additional assets here
];

// Runtime caching patterns
const RUNTIME_PATTERNS = [
    /^https:\/\/wa\.me\//,
    /^https:\/\/formspree\.io\//
];

/**
 * Install event - cache static files
 */
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then(cache => {
                return cache.addAll(STATIC_FILES);
            })
            .then(() => {
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Service Worker install failed:', error);
            })
    );
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames
                        .filter(cacheName => {
                            return cacheName !== STATIC_CACHE_NAME && 
                                   cacheName !== RUNTIME_CACHE_NAME;
                        })
                        .map(cacheName => {
                            return caches.delete(cacheName);
                        })
                );
            })
            .then(() => {
                return self.clients.claim();
            })
            .catch(error => {
                console.error('Service Worker activation failed:', error);
            })
    );
});

/**
 * Fetch event - serve cached files or fetch from network
 */
self.addEventListener('fetch', event => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    // Skip external requests that we don't want to cache
    if (!event.request.url.startsWith(self.location.origin) && 
        !RUNTIME_PATTERNS.some(pattern => pattern.test(event.request.url))) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                if (cachedResponse) {
                    // Return cached version
                    return cachedResponse;
                }

                // Not in cache, fetch from network
                return fetch(event.request)
                    .then(response => {
                        // Only cache successful responses
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone the response
                        const responseToCache = response.clone();

                        // Add to runtime cache
                        caches.open(RUNTIME_CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    })
                    .catch(error => {
                        console.error('Fetch failed:', error);
                        
                        // Return offline fallback if available
                        if (event.request.destination === 'document') {
                            return caches.match('/index.html');
                        }
                        
                        throw error;
                    });
            })
    );
});

/**
 * Background sync for form submissions (if supported)
 */
if ('sync' in self.registration) {
    self.addEventListener('sync', event => {
        if (event.tag === 'contact-form') {
            event.waitUntil(syncContactForm());
        }
    });
}

/**
 * Sync contact form submissions when back online
 */
async function syncContactForm() {
    try {
        // Get pending form data from IndexedDB or localStorage
        const pendingForms = await getPendingFormSubmissions();
        
        for (const formData of pendingForms) {
            try {
                const response = await fetch(formData.url, {
                    method: 'POST',
                    body: formData.data,
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                
                if (response.ok) {
                    // Remove from pending queue
                    await removePendingFormSubmission(formData.id);
                    
                    // Notify user of successful sync
                    self.registration.showNotification('Message Sent!', {
                        body: 'Your message was sent successfully.',
                        icon: '/icon-192.png',
                        badge: '/icon-72.png',
                        tag: 'form-success'
                    });
                }
            } catch (error) {
                console.error('Failed to sync form:', error);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

/**
 * Get pending form submissions (placeholder)
 */
async function getPendingFormSubmissions() {
    // In a real implementation, this would read from IndexedDB
    return [];
}

/**
 * Remove pending form submission (placeholder)
 */
async function removePendingFormSubmission(id) {
    // In a real implementation, this would remove from IndexedDB
    return true;
}

/**
 * Push notifications (if needed in future)
 */
self.addEventListener('push', event => {
    if (!event.data) {
        return;
    }

    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/icon-192.png',
        badge: '/icon-72.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/'
        },
        actions: [
            {
                action: 'open',
                title: 'Open'
            },
            {
                action: 'close',
                title: 'Close'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

/**
 * Handle notification clicks
 */
self.addEventListener('notificationclick', event => {
    event.notification.close();

    if (event.action === 'open' || !event.action) {
        const urlToOpen = event.notification.data?.url || '/';
        
        event.waitUntil(
            self.clients.matchAll({ type: 'window' })
                .then(clients => {
                    // Check if there's already a window/tab open with this URL
                    for (const client of clients) {
                        if (client.url === urlToOpen && 'focus' in client) {
                            return client.focus();
                        }
                    }
                    
                    // If not, open a new window
                    if (self.clients.openWindow) {
                        return self.clients.openWindow(urlToOpen);
                    }
                })
        );
    }
});

/**
 * Handle messages from main thread
 */
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

console.log('Lost Luggage Recovery Service Worker loaded');