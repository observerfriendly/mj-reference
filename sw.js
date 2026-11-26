/* MJ Reference service worker.
   Shell + data are precached so the app opens offline.
   Renders are cached as you view them, capped so the phone never fills up. */

var VERSION = 'v1';
var SHELL = 'mjref-shell-' + VERSION;
var IMGS = 'mjref-img-' + VERSION;
var IMG_CAP = 700;

var SHELL_FILES = [
  './',
  'index.html',
  'app.css',
  'app.js',
  'manifest.webmanifest',
  'data/index.json',
  'data/params.json',
  'icons/icon-192.png',
  'icons/icon-512.png',
  'icons/apple-touch-icon.png'
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(SHELL).then(function (c) {
      return Promise.all(SHELL_FILES.map(function (f) {
        return c.add(new Request(f, { cache: 'reload' })).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        if (k !== SHELL && k !== IMGS) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

function isRender(url) {
  if (url.hostname === "cdn.jsdelivr.net") return true;
  return url.hostname === 'wsrv.nl' ||
         url.hostname === 'raw.githubusercontent.com' ||
         url.hostname === 'images.weserv.nl';
}

/* Keep the image cache from growing without bound. Oldest-inserted go first,
   which for a browse-driven cache is close enough to least-recently-wanted. */
function trim(cache) {
  return cache.keys().then(function (keys) {
    if (keys.length <= IMG_CAP) return;
    return Promise.all(
      keys.slice(0, keys.length - IMG_CAP).map(function (k) { return cache.delete(k); })
    );
  });
}

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;

  var url;
  try { url = new URL(req.url); } catch (err) { return; }

  /* Renders: cache first, then network, then store. Opaque responses report
     status 0, so don't gate on response.ok here or nothing ever gets cached. */
  if (isRender(url)) {
    e.respondWith(
      caches.open(IMGS).then(function (cache) {
        return cache.match(req).then(function (hit) {
          if (hit) return hit;
          return fetch(req).then(function (res) {
            if (res && (res.ok || res.status === 0)) {
              cache.put(req, res.clone()).then(function () { trim(cache); }).catch(function () {});
            }
            return res;
          });
        });
      })
    );
    return;
  }

  if (url.origin !== self.location.origin) return;

  /* Shell and data: serve from cache, refresh in the background. */
  e.respondWith(
    caches.open(SHELL).then(function (cache) {
      return cache.match(req, { ignoreSearch: true }).then(function (hit) {
        var live = fetch(req).then(function (res) {
          if (res && res.ok) cache.put(req, res.clone()).catch(function () {});
          return res;
        }).catch(function () { return hit; });
        return hit || live;
      });
    }).then(function (res) {
      if (res) return res;
      if (req.mode === 'navigate') return caches.match('index.html');
      return new Response('', { status: 504, statusText: 'Offline' });
    })
  );
});
