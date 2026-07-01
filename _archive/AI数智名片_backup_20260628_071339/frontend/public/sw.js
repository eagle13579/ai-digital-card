/* ============================================================
   AI数智名片 Service Worker
   ============================================================
   策略: 网络优先, 离线时 fallback 到缓存
   ============================================================ */

const CACHE_NAME = 'aibizcard-v1';
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/manifest.json',
];

/* ---- 安装: 预缓存关键资源 ---- */
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

/* ---- 激活: 清理旧缓存 ---- */
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(names =>
      Promise.all(names.map(n => {
        if (n !== CACHE_NAME) return caches.delete(n);
      }))
    ).then(() => self.clients.claim())
  );
});

/* ---- 请求拦截: 网络优先, 离线降级到缓存 ---- */
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  if (!event.request.url.startsWith('http')) return;

  event.respondWith(
    fetch(event.request)
      .then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => {
        return caches.match(event.request).then(cached => {
          if (cached) return cached;
          return caches.match('/index.html') || caches.match('/');
        });
      })
  );
});
