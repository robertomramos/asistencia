/* Service worker · OAD 2026
   ───────────────────────────────────────────────────────────
   Las páginas se piden SIEMPRE a la red primero, para que una
   corrección subida a GitHub llegue al celular en la siguiente
   apertura. La copia guardada queda como respaldo, y es la que
   permite que el escáner abra sin señal.

   Las librerías y los logos sí van desde la caché: no cambian.
   ─────────────────────────────────────────────────────────── */

const CACHE = 'oad-2026-v4';

const PAGINAS = ['./', './index.html', './tablero.html'];
const FIJOS = [
  './manifest.json',
  './logo-oad.png',
  './logo-carrera.png',
  'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js'
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(PAGINAS.concat(FIJOS)); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (claves) {
      return Promise.all(claves.map(function (k) {
        if (k !== CACHE) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  const req = e.request;
  const url = req.url;

  // Nunca se cachean las llamadas al servidor ni los QR
  if (url.indexOf('script.google.com') > -1 ||
      url.indexOf('googleusercontent') > -1 ||
      url.indexOf('qrserver.com') > -1) return;

  if (req.method !== 'GET') return;

  const esPagina = req.mode === 'navigate' ||
                   url.indexOf('.html') > -1 ||
                   url.endsWith('/');

  if (esPagina) {
    // Red primero: así llegan las correcciones
    e.respondWith(
      fetch(req).then(function (resp) {
        if (resp && resp.status === 200) {
          const copia = resp.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copia); });
        }
        return resp;
      }).catch(function () {
        return caches.match(req).then(function (g) {
          return g || caches.match('./index.html');
        });
      })
    );
    return;
  }

  // Todo lo demás: caché primero
  e.respondWith(
    caches.match(req).then(function (g) {
      if (g) return g;
      return fetch(req).then(function (resp) {
        if (resp && resp.status === 200) {
          const copia = resp.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copia); });
        }
        return resp;
      });
    })
  );
});
