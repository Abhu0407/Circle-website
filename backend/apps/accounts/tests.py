import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.communities.models import Community

User = get_user_model()


class AuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', 'alice@example.com', 'S3cure-pass!')

    def test_pages_render(self):
        for name in ('signin', 'signup'):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'id="app"')

    def test_home_requires_login(self):
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, f"{reverse('signin')}?next=/")

    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(reverse('api-signup'), {
            'username': 'bob', 'email': 'Bob@Example.com', 'password': 'An0ther-pass!',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.get(username='bob').email, 'bob@example.com')
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)

    def test_signup_rejects_duplicate_email(self):
        response = self.client.post(reverse('api-signup'), {
            'username': 'carol', 'email': 'ALICE@example.com', 'password': 'An0ther-pass!',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json())

    def test_signup_requires_only_username_email_password(self):
        response = self.client.post(reverse('api-signup'), {}, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()), {'username', 'email', 'password'})

    def test_signin_and_signup_share_one_page(self):
        for name, mode in (('signin', 'signin'), ('signup', 'signup')):
            response = self.client.get(reverse(name))
            self.assertContains(response, 'pages/auth/main.vue')
            self.assertContains(response, f'"mode": "{mode}"')

    def test_signin_with_username_or_email(self):
        for identifier in ('alice', 'Alice@Example.com'):
            response = self.client.post(reverse('api-signin'), {
                'identifier': identifier, 'password': 'S3cure-pass!',
            }, content_type='application/json')
            self.assertEqual(response.status_code, 200, identifier)
            self.client.logout()

    def test_signin_wrong_password(self):
        response = self.client.post(reverse('api-signin'), {
            'identifier': 'alice', 'password': 'nope',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)


@override_settings(GOOGLE_CLIENT_ID='test-client-id')
class GoogleSignInTests(TestCase):
    """Google's token check is mocked; we test what happens with its result."""

    def post(self, info=None, error=None):
        target = 'apps.accounts.serializers.id_token.verify_oauth2_token'
        with mock.patch(target, return_value=info, side_effect=error) as verify:
            response = self.client.post(reverse('api-google'), {'credential': 'tok'},
                                        content_type='application/json')
        return response, verify

    def google_info(self, **extra):
        return {'email': 'Dana@Gmail.com', 'email_verified': True,
                'given_name': 'Dana', 'family_name': 'Lee', **extra}

    def test_new_user_is_created_and_signed_in(self):
        response, verify = self.post(self.google_info())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(verify.call_args.args[0], 'tok')
        self.assertEqual(verify.call_args.args[2], 'test-client-id')
        user = User.objects.get(email='dana@gmail.com')
        self.assertEqual((user.username, user.first_name, user.last_name), ('dana', 'Dana', 'Lee'))
        self.assertFalse(user.has_usable_password())
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)

    def test_existing_email_signs_in_same_account(self):
        alice = User.objects.create_user('alice', 'alice@example.com', 'S3cure-pass!')
        response, _ = self.post(self.google_info(email='ALICE@example.com'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], alice.id)
        self.assertEqual(User.objects.count(), 1)

    def test_username_is_made_unique(self):
        User.objects.create_user('dana', 'other@example.com', 'S3cure-pass!')
        self.post(self.google_info())
        self.assertEqual(User.objects.get(email='dana@gmail.com').username, 'dana2')

    def test_unverified_email_rejected(self):
        response, _ = self.post(self.google_info(email_verified=False))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.exists())

    def test_invalid_token_rejected(self):
        response, _ = self.post(error=ValueError('bad token'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('non_field_errors', response.json())

    def test_inactive_user_rejected(self):
        User.objects.create_user('erin', 'dana@gmail.com', 'S3cure-pass!', is_active=False)
        response, _ = self.post(self.google_info())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get(reverse('home')).status_code, 302)

    @override_settings(GOOGLE_CLIENT_ID='')
    def test_not_configured(self):
        response, verify = self.post(self.google_info())
        self.assertEqual(response.status_code, 400)
        verify.assert_not_called()

    def test_client_id_passed_to_page(self):
        self.assertContains(self.client.get(reverse('signin')), '"googleClientId": "test-client-id"')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', 'alice@example.com', 'S3cure-pass!')
        User.objects.create_user('bob', 'bob@example.com', 'S3cure-pass!')
        self.client.force_login(self.user)

    def patch(self, data):
        return self.client.patch(reverse('api-me'), data, content_type='application/json')

    def test_profile_page_renders(self):
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'pages/profile/main.vue')
        self.assertContains(response, '"meApi"')

    def test_map_shows_other_people_with_a_point(self):
        User.objects.filter(username='bob').update(latitude=19.07612, longitude=72.87765)
        User.objects.create_user('carol', 'carol@example.com', 'S3cure-pass!')  # no point
        self.user.latitude, self.user.longitude = 19.1, 72.9
        self.user.save()
        response = self.client.get(reverse('home'))
        people = response.context['page_props']['mapPeople']
        self.assertEqual([(p['username'], p['lat'], p['lng']) for p in people], [('bob', 19.08, 72.88)])

    def test_home_opens_on_requested_section(self):
        response = self.client.get(reverse('home') + '?tab=chats')
        self.assertContains(response, 'pages/home/main.vue')
        self.assertContains(response, '"tab": "chats"')
        response = self.client.get(reverse('home') + '?tab=nope')
        self.assertContains(response, '"tab": "foryou"')

    def test_update_profile_fields(self):
        response = self.patch({'name': 'Alice A', 'location': 'Pune', 'interested_category': ['tech', 'outdoors']})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(
            (self.user.name, self.user.location, self.user.interested_category),
            ('Alice A', 'Pune', ['tech', 'outdoors']),
        )

    def test_location_with_map_point(self):
        response = self.patch({'location': 'Bandra, Mumbai', 'latitude': 19.0596, 'longitude': 72.8295})
        self.assertEqual(response.status_code, 200)
        self.assertEqual((response.json()['latitude'], response.json()['longitude']), (19.0596, 72.8295))

        # Clearing the pin (location typed by hand).
        response = self.patch({'location': 'Pune', 'latitude': None, 'longitude': None})
        self.assertIsNone(response.json()['latitude'])

    def test_map_point_needs_both_halves_and_valid_range(self):
        self.assertEqual(self.patch({'latitude': 19.0}).status_code, 400)
        self.assertEqual(self.patch({'latitude': 19.0, 'longitude': None}).status_code, 400)
        self.assertEqual(self.patch({'latitude': 95, 'longitude': 72}).status_code, 400)

    def test_interests_deduplicated(self):
        response = self.patch({'interested_category': ['music', 'tech', 'music']})
        self.assertEqual(response.json()['interested_category'], ['music', 'tech'])

    def test_interests_only_from_categories(self):
        response = self.patch({'interested_category': ['music', 'Board games']})
        self.assertEqual(response.status_code, 400)
        self.assertIn('interested_category', response.json())

    def test_joined_communities_listed_and_leavable(self):
        hikers = Community.objects.create(name='Hikers', category='outdoors')
        coders = Community.objects.create(name='Coders', category='tech')
        self.user.join_community.add(hikers, coders)

        joined = self.client.get(reverse('api-me')).json()['join_community']
        self.assertEqual([c['name'] for c in joined], ['Coders', 'Hikers'])
        self.assertEqual(joined[0]['members_count'], 1)

        response = self.patch({'join_community': [hikers.id]})
        self.assertEqual([c['name'] for c in response.json()['join_community']], ['Hikers'])

        response = self.patch({'join_community': []})
        self.assertEqual(response.json()['join_community'], [])

    def test_email_cannot_be_changed(self):
        self.patch({'email': 'new@example.com'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'alice@example.com')

    def test_username_change(self):
        self.assertEqual(self.patch({'username': 'alice2'}).status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'alice2')

    def test_username_must_be_unique_ignoring_case(self):
        response = self.patch({'username': 'BOB'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.json())

    def test_keeping_own_username_is_allowed(self):
        self.assertEqual(self.patch({'username': 'alice', 'name': 'A'}).status_code, 200)

    def test_username_check(self):
        url = reverse('api-username-check')
        self.assertTrue(self.client.get(url, {'username': 'carol'}).json()['available'])
        self.assertTrue(self.client.get(url, {'username': 'Alice'}).json()['available'])
        self.assertFalse(self.client.get(url, {'username': 'Bob'}).json()['available'])
        self.assertFalse(self.client.get(url, {'username': 'bad name!'}).json()['available'])

    def test_pick_and_remove_avatar(self):
        response = self.patch({'avatar': 'animal-fox'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['avatar'], 'animal-fox')
        self.assertEqual(response.json()['profile_picture'], '/static/avatars/animal-fox.svg')

        # Only the site's own avatars.
        response = self.patch({'avatar': 'https://example.com/me.png'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('avatar', response.json())

        response = self.patch({'avatar': ''})
        self.assertIsNone(response.json()['profile_picture'])

    def test_profile_requires_login(self):
        self.client.logout()
        self.assertEqual(self.patch({'name': 'x'}).status_code, 403)
