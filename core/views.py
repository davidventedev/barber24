from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET


def landing(request):
    return render(request, 'core/landing.html')


@require_GET
def manifest(request):
    return JsonResponse({
        'name': 'Barber24',
        'short_name': 'Barber24',
        'description': 'Gestión de reservas para barberías',
        'start_url': '/',
        'display': 'standalone',
        'background_color': '#000000',
        'theme_color': '#EAC452',
        'orientation': 'portrait-primary',
        'icons': [
            {
                'src': '/static/icons/icon-192.png',
                'sizes': '192x192',
                'type': 'image/png',
                'purpose': 'any',
            },
            {
                'src': '/static/icons/icon-512.png',
                'sizes': '512x512',
                'type': 'image/png',
                'purpose': 'any',
            },
        ],
    })


@require_GET
def service_worker(request):
    js = """
const CACHE = 'barber24-v2';
const ASSETS = [
  '/',
  '/static/css/app.css',
  '/static/js/app.js',
  '/static/img/logo.svg',
  '/static/img/icon.png',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];
self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});
self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).then((res) => {
      const copy = res.clone();
      if (res.ok && e.request.url.startsWith(self.location.origin) && e.request.url.includes('/static/')) {
        caches.open(CACHE).then((c) => c.put(e.request, copy));
      }
      return res;
    }).catch(() => caches.match(e.request))
  );
});
"""
    return HttpResponse(js.strip(), content_type='application/javascript')
