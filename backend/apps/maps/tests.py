import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


def fake_response(status=200, content=b'PNG', content_type='image/png', json=None):
    response = mock.Mock(status_code=status, content=content, headers={'Content-Type': content_type})
    response.json.return_value = json or {}
    response.raise_for_status.return_value = None
    return response


@override_settings(MAP_TILE_CACHE_DIR=Path(tempfile.mkdtemp()))
class MapProxyTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user('alice', 'alice@example.com', 'S3cure-pass!'))

    @mock.patch('apps.maps.views.requests.get', return_value=fake_response())
    def test_tile_fetched_once_then_cached(self, get):
        url = reverse('map-tile', args=[12, 2884, 1849])
        for _ in range(2):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b'PNG')
        get.assert_called_once()
        self.assertIn('User-Agent', get.call_args.kwargs['headers'])

    def test_tile_out_of_range(self):
        self.assertEqual(self.client.get(reverse('map-tile', args=[2, 9, 0])).status_code, 404)

    @mock.patch('apps.maps.views.requests.get', return_value=fake_response(403, b'<html>', 'text/html'))
    def test_upstream_error_not_cached(self, get):
        url = reverse('map-tile', args=[3, 1, 1])
        self.assertEqual(self.client.get(url).status_code, 502)
        self.client.get(url)
        self.assertEqual(get.call_count, 2)

    @mock.patch('apps.maps.views.requests.get', return_value=fake_response(json={'features': [{'id': 1}]}))
    def test_search_and_reverse(self, get):
        response = self.client.get(reverse('api-map-search'), {'q': 'Bandra', 'lat': '19', 'lon': '72'})
        self.assertEqual(response.json(), {'features': [{'id': 1}]})
        self.assertEqual(get.call_args.kwargs['params'], {'q': 'Bandra', 'limit': 5, 'lat': 19.0, 'lon': 72.0})

        self.assertEqual(self.client.get(reverse('api-map-reverse'), {'lat': '19', 'lon': '72'}).status_code, 200)
        self.assertEqual(self.client.get(reverse('api-map-reverse'), {'lat': '99', 'lon': '72'}).status_code, 400)

    def test_requires_sign_in(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('map-tile', args=[1, 0, 0])).status_code, 403)
        self.assertEqual(self.client.get(reverse('api-map-search'), {'q': 'x'}).status_code, 403)
