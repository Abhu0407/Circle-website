import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart
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


# A 1x1 GIF, small enough to upload as a profile picture.
TINY_GIF = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00'
    b',\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


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
        self.assertContains(response, '"tab": "profile"')

    def test_update_profile_fields(self):
        response = self.patch({'name': 'Alice A', 'location': 'Pune', 'interested_category': ['Tech', 'Hiking']})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(
            (self.user.name, self.user.location, self.user.interested_category),
            ('Alice A', 'Pune', ['Tech', 'Hiking']),
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

    def test_interests_are_cleaned(self):
        response = self.patch({'interested_category': [' Tech ', 'tech', '', 'Board   games']})
        self.assertEqual(response.json()['interested_category'], ['Tech', 'Board games'])

    def test_interests_limit(self):
        response = self.patch({'interested_category': [f'Topic {i}' for i in range(21)]})
        self.assertEqual(response.status_code, 400)

    def test_joined_communities_listed_and_leavable(self):
        hikers = Community.objects.create(name='Hikers', category='Outdoors')
        coders = Community.objects.create(name='Coders', category='Tech')
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

    def test_upload_and_remove_picture(self):
        picture = SimpleUploadedFile('me.gif', TINY_GIF, content_type='image/gif')
        response = self.client.patch(
            reverse('api-me'),
            encode_multipart(BOUNDARY, {'profile_picture': picture}),
            content_type=MULTIPART_CONTENT,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['profile_picture'])

        response = self.patch({'remove_profile_picture': True})
        self.assertIsNone(response.json()['profile_picture'])

    def test_profile_requires_login(self):
        self.client.logout()
        self.assertEqual(self.patch({'name': 'x'}).status_code, 403)
