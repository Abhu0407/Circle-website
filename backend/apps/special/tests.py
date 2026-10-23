from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


@override_settings(SPECIAL_EMAIL='Love@Example.com', SPECIAL_NAME='Sweetheart')
class SpecialPageTests(TestCase):
    def setUp(self):
        self.her = User.objects.create_user('her', 'love@example.com', 'S3cure-pass!')
        self.other = User.objects.create_user('other', 'other@example.com', 'S3cure-pass!')

    def sign_in(self, identifier):
        response = self.client.post(
            reverse('api-signin'), {'identifier': identifier, 'password': 'S3cure-pass!'}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

    def test_hidden_from_everyone_else(self):
        self.assertEqual(self.client.get(reverse('special')).status_code, 404)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('special')).status_code, 404)

    def test_shown_once_after_sign_in(self):
        self.sign_in('her')
        self.assertRedirects(self.client.get(reverse('home')), reverse('special'))
        response = self.client.get(reverse('special'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sweetheart')
        # After that, Circle works as usual and the page can still be opened.
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('special')).status_code, 200)

    def test_shown_after_sign_up(self):
        self.her.delete()
        response = self.client.post(
            reverse('api-signup'),
            {'username': 'her2', 'email': 'LOVE@example.com', 'password': 'S3cure-pass!'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertRedirects(self.client.get(reverse('profile')), reverse('special'))

    def test_api_not_redirected(self):
        self.sign_in('love@example.com')
        self.assertEqual(self.client.get(reverse('api-me')).status_code, 200)

    def test_others_not_redirected(self):
        self.sign_in('other')
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)

    @override_settings(SPECIAL_EMAIL='')
    def test_nobody_when_not_set(self):
        self.client.force_login(self.her)
        self.assertEqual(self.client.get(reverse('special')).status_code, 404)
