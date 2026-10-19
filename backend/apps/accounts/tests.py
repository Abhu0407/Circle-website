from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

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
