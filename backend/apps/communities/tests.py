from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Community

User = get_user_model()


class CommunityTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', 'alice@example.com', 'S3cure-pass!')
        self.bob = User.objects.create_user('bob', 'bob@example.com', 'S3cure-pass!')
        self.client.force_login(self.alice)

    def create(self, **data):
        return self.client.post(reverse('api-communities'), {'name': 'Hikers', 'category': 'outdoors', **data},
                                content_type='application/json')

    def test_create_makes_creator_a_member(self):
        response = self.create(description='Weekend trails', location='Pune')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual((data['members_count'], data['is_member'], data['is_creator']), (1, True, True))
        self.assertEqual(data['posts_count'], 0)
        self.assertEqual((data['category'], data['category_label']), ('outdoors', 'Outdoors'))
        self.assertEqual(data['created_by']['username'], 'alice')
        self.assertEqual(data['url'], reverse('community-detail', args=[data['id']]))
        self.assertTrue(self.alice.join_community.filter(pk=data['id']).exists())

    def test_name_required_and_unique(self):
        self.assertIn('name', self.create(name='   ').json())
        self.create()
        response = self.create(name=' hikers ')
        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.json())

    def test_join_and_leave(self):
        community = Community.objects.create(name='Coders', created_by=self.bob)
        url = reverse('api-community-join', args=[community.pk])
        self.assertEqual(self.client.post(url).json(), {'is_member': True, 'members_count': 1})
        self.assertEqual(self.client.delete(url).json(), {'is_member': False, 'members_count': 0})

    def test_category_required_and_from_list(self):
        response = self.create(category='')
        self.assertEqual(response.status_code, 400)
        self.assertIn('category', response.json())
        response = self.create(category='Knitting')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.create(category='other').status_code, 201)

    def test_creator_can_edit_but_not_change_category(self):
        community_id = self.create().json()['id']
        url = reverse('api-community', args=[community_id])
        response = self.client.patch(url, {'name': 'Trail Friends', 'description': 'New text', 'location': 'Mumbai'},
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual((response.json()['name'], response.json()['description']), ('Trail Friends', 'New text'))
        # Sending the same category is fine; a different one is refused.
        self.assertEqual(self.client.patch(url, {'category': 'outdoors'}, content_type='application/json').status_code, 200)
        response = self.client.patch(url, {'category': 'tech'}, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('category', response.json())
        self.assertEqual(Community.objects.get(pk=community_id).category, 'outdoors')

    def test_location_point(self):
        response = self.create(location='Pune', latitude=18.5204, longitude=73.8567)
        self.assertEqual((response.json()['latitude'], response.json()['longitude']), (18.5204, 73.8567))
        response = self.create(name='Half', latitude=18.5)
        self.assertEqual(response.status_code, 400)
        self.assertIn('location', response.json())

    def test_page_shows_members_on_map(self):
        community = Community.objects.create(name='Coders', category='tech', created_by=self.bob)
        self.bob.latitude, self.bob.longitude = 19.07612, 72.87765
        self.bob.save()
        community.members.add(self.bob, self.alice)
        stranger = User.objects.create_user('carol', 'carol@example.com', 'S3cure-pass!', latitude=1, longitude=2)
        response = self.client.get(reverse('community-detail', args=[community.pk]))
        points = response.context['page_props']['memberPoints']
        self.assertEqual(points, [{'id': self.bob.pk, 'username': 'bob', 'lat': 19.08, 'lng': 72.88}])
        self.assertNotIn(stranger.username, str(points))

    def test_only_creator_can_edit(self):
        community = Community.objects.create(name='Coders', category='tech', created_by=self.bob)
        response = self.client.patch(reverse('api-community', args=[community.pk]), {'name': 'Mine now'},
                                     content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_discover_list_distance_and_membership(self):
        self.alice.latitude, self.alice.longitude = 19.0596, 72.8295  # Bandra
        self.alice.save()
        near = Community.objects.create(name='Near', category='music', latitude=19.1075, longitude=72.8263)  # Juhu
        Community.objects.create(name='Far', category='music', latitude=18.5204, longitude=73.8567)  # Pune
        Community.objects.create(name='Nowhere', category='music')
        near.members.add(self.alice, self.bob)

        data = self.client.get(reverse('api-communities')).json()
        self.assertEqual([c['name'] for c in data], ['Near', 'Far', 'Nowhere'])
        self.assertEqual((data[0]['is_member'], data[0]['members_count']), (True, 2))
        self.assertAlmostEqual(data[0]['distance_km'], 5.4, delta=0.3)
        self.assertGreater(data[1]['distance_km'], 100)
        self.assertIsNone(data[2]['distance_km'])
        self.assertFalse(data[1]['is_member'])

        names = [c['name'] for c in self.client.get(reverse('api-communities'), {'within': 10}).json()]
        self.assertEqual(names, ['Near'])

    def test_within_needs_your_location(self):
        response = self.client.get(reverse('api-communities'), {'within': 10})
        self.assertEqual(response.status_code, 400)

    def test_search_any_field_and_several_categories(self):
        Community.objects.create(name='Chess', category='games', description='Blitz on Sundays')
        Community.objects.create(name='Yoga', category='wellness')
        Community.objects.create(name='Coders', category='tech')

        def get(**params):
            return sorted(c['name'] for c in self.client.get(reverse('api-communities'), params).json())

        self.assertEqual(get(q='blitz'), ['Chess'])
        self.assertEqual(get(q='wellness'), ['Yoga'])  # category label
        self.assertEqual(get(category=['games', 'tech']), ['Chess', 'Coders'])

    def test_search(self):
        Community.objects.create(name='Hikers', category='outdoors', location='Pune')
        Community.objects.create(name='Coders', category='tech')
        get = lambda **params: [c['name'] for c in self.client.get(reverse('api-communities'), params).json()]
        self.assertEqual(get(category='tech'), ['Coders'])
        self.assertEqual(get(q='pune'), ['Hikers'])

    def test_page_renders(self):
        community = Community.objects.create(name='Coders', description='We write code', created_by=self.bob)
        response = self.client.get(reverse('community-detail', args=[community.pk]))
        self.assertContains(response, 'pages/community/main.vue')
        self.assertContains(response, 'We write code')
        self.assertEqual(self.client.get(reverse('community-detail', args=[999])).status_code, 404)

    def test_home_passes_communities_api_and_categories(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, reverse('api-communities'))
        self.assertContains(response, '"value": "learning"')
