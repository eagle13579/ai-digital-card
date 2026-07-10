/* AI数智名片 SW — 网络优先 + API缓存 + 离线回退 */
const STATIC_CACHE = 'aibizcard-static-v1';
const API_CACHE = 'aibizcard-api-v1';
const PRECACHE = ['/', '/index.html', '/manifest.json', '/offline.html'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(STATIC_CACHE).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(names =>
      Promise.all(names.filter(n => n !== STATIC_CACHE && n !== API_CACHE).map(caches.delete))
    ).then(() => self.clients.claim())
  );
});

function isApi(url) {
  try { return new URL(url).pathname.startsWith('/api/'); } catch { return false; }
}

function isStatic(url) {
  try {
    const ext = new URL(url).pathname.split('.').pop();
    return ['js','css','png','jpg','jpeg','gif','svg','webp','woff','woff2','ico'].includes(ext);
  } catch { return false; }
}

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const u = e.request.url;
  if (!u.startsWith('http')) return;

  /* API: 网络优先，缓存后备 */
  if (isApi(u)) {
    e.respondWith(
      fetch(e.request).then(r => (r.ok && caches.open(API_CACHE).then(c => c.put(e.request, r.clone())), r))
        .catch(() => caches.match(e.request))
    );
    return;
  }

  /* 静态资源: 缓存优先，网络补充 */
  if (isStatic(u)) {
    e.respondWith(
      caches.match(e.request).then(cached => {
        const net = fetch(e.request).then(r =>
          (r.ok && caches.open(STATIC_CACHE).then(c => c.put(e.request, r.clone())), r)
        ).catch(() => cached);
        return cached || net;
      })
    );
    return;
  }

  /* 其他: 网络优先，离线降级 */
  e.respondWith(
    fetch(e.request).then(r =>
      (r.ok && caches.open(STATIC_CACHE).then(c => c.put(e.request, r.clone())), r)
    ).catch(() =>
      caches.match(e.request).then(c => c || caches.match('/offline.html') || caches.match('/'))
    )
  );
});
