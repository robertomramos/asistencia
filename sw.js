/* Service worker del escáner de asistencia · OAD 2026
   Guarda la página y la librería de lectura de QR en el celular
   para que el escáner abra aunque no haya señal. */

const CACHE = 'oad-2026-v1';

const ARCHIVOS = [
  './',
  './index.html',
  './tablero.html',
  './manifest.json',
  './logo-oad.png',
  './logo-carrera.png',
  'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js'
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(ARCHIVOS); })
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
  const url = e.request.url;

  // Las llamadas a Apps Script nunca se guardan en caché: siempre
  // deben ir a la red o fallar, para que la cola reintente.
  if (url.indexOf('script.google.com') > -1 ||
      url.indexOf('googleusercontent') > -1 ||
      url.indexOf('qrserver.com') > -1) return;

  e.respondWith(
    caches.match(e.request).then(function (guardado) {
      if (guardado) return guardado;
      return fetch(e.request).then(function (resp) {
        if (resp && resp.status === 200 && e.request.method === 'GET') {
          const copia = resp.clone();
          caches.open(CACHE).then(function (c) { c.put(e.request, copia); });
        }
        return resp;
      }).catch(function () { return caches.match('./index.html'); });
    })
  );
});
