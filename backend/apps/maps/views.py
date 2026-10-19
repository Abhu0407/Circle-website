"""Map tiles and place lookups, fetched by Django on the browser's behalf.

The browser only ever talks to our own site, so third-party rules about
Referer headers, CORS or ad blockers can't stop the map from showing.
Tiles are cached on disk, as OpenStreetMap's tile usage policy asks.
Only signed-in users can use these, so they don't become an open proxy.
"""

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

# Identify the app to the upstream services, as their usage policies require.
HEADERS = {'User-Agent': settings.MAPS_USER_AGENT}
TIMEOUT = 10
TILE_MAX_AGE = 7 * 24 * 60 * 60  # seconds the browser may reuse a tile


def _signed_in(view):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'detail': 'Sign in required.'}, status=403)
        return view(request, *args, **kwargs)
    return wrapper


@require_GET
@_signed_in
def tile(request, z, x, y):
    if not (0 <= z <= 19 and 0 <= x < 2 ** z and 0 <= y < 2 ** z):
        return HttpResponse(status=404)

    path = settings.MAP_TILE_CACHE_DIR / str(z) / str(x) / f'{y}.png'
    if path.exists():
        data = path.read_bytes()
    else:
        try:
            upstream = requests.get(
                settings.MAP_TILE_URL.format(z=z, x=x, y=y), headers=HEADERS, timeout=TIMEOUT,
            )
        except requests.RequestException:
            return HttpResponse(status=502)
        if upstream.status_code != 200 or not upstream.headers.get('Content-Type', '').startswith('image/'):
            return HttpResponse(status=502)
        data = upstream.content
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    response = HttpResponse(data, content_type='image/png')
    response['Cache-Control'] = f'private, max-age={TILE_MAX_AGE}'
    return response


def _photon(path, params):
    try:
        upstream = requests.get(f'{settings.PHOTON_URL}{path}', params=params, headers=HEADERS, timeout=TIMEOUT)
        upstream.raise_for_status()
        return JsonResponse(upstream.json())
    except (requests.RequestException, ValueError):
        return JsonResponse({'detail': 'Place lookup failed. Please try again.'}, status=502)


def _coord(value, limit):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if -limit <= number <= limit else None


@require_GET
@_signed_in
def search(request):
    """?q=Bandra[&lat=..&lon=..] -> Photon GeoJSON (results near lat/lon first)."""
    q = request.GET.get('q', '').strip()[:200]
    if not q:
        return JsonResponse({'features': []})
    params = {'q': q, 'limit': 5}
    lat, lon = _coord(request.GET.get('lat'), 90), _coord(request.GET.get('lon'), 180)
    if lat is not None and lon is not None:
        params.update(lat=lat, lon=lon)
    return _photon('/api/', params)


@require_GET
@_signed_in
def reverse(request):
    """?lat=..&lon=.. -> Photon GeoJSON with the place at that point."""
    lat, lon = _coord(request.GET.get('lat'), 90), _coord(request.GET.get('lon'), 180)
    if lat is None or lon is None:
        return JsonResponse({'detail': 'lat and lon are required.'}, status=400)
    return _photon('/reverse', {'lat': lat, 'lon': lon})
