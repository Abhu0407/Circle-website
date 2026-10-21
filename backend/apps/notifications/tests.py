from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.communities.models import Category, Community
from apps.posts.models import Post

from . import services

User = get_user_model()


class NotificationTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', 'alice@example.com', 'S3cure-pass!')
        self.bob = User.objects.create_user('bob', 'bob@example.com', 'S3cure-pass!')
        # Accounts start with nothing new: put alice's join date in the past.
        User.objects.filter(pk=self.alice.pk).update(date_joined=timezone.now() - timedelta(days=1))
        self.alice.refresh_from_db()
        self.hikers = Community.objects.create(name='Hikers', category=Category.OUTDOORS, created_by=self.bob)
        self.client.force_login(self.alice)

    def fetch(self, **params):
        response = self.client.get(reverse('api-notifications'), params)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_lists_others_posts_and_communities_newest_first(self):
        Post.objects.create(community=self.hikers, author=self.bob, body='Trail on Sunday?')
        Post.objects.create(community=self.hikers, author=self.alice, body='My own post')
        Community.objects.create(name='Alice club', category=Category.SOCIAL, created_by=self.alice)

        items = self.fetch()['notifications']
        self.assertEqual([n['type'] for n in items], ['post', 'community'])
        self.assertEqual(items[0]['text'], 'Trail on Sunday?')
        self.assertEqual(items[0]['actor']['username'], 'bob')
        self.assertEqual(items[0]['community']['name'], 'Hikers')
        self.assertEqual(items[1]['community']['name'], 'Hikers')
        self.assertEqual(items[1]['category'], 'Outdoors')

    def test_filter_by_kind(self):
        Post.objects.create(community=self.hikers, author=self.bob, body='Hi')
        self.assertEqual([n['type'] for n in self.fetch(kind='posts')['notifications']], ['post'])
        self.assertEqual([n['type'] for n in self.fetch(kind='communities')['notifications']], ['community'])
        response = self.client.get(reverse('api-notifications'), {'kind': 'nope'})
        self.assertEqual(response.status_code, 400)

    def test_pages_follow_on_without_repeats(self):
        for i in range(services.PAGE_SIZE + 5):
            Post.objects.create(community=self.hikers, author=self.bob, body=f'Post {i}')
        first = self.fetch()
        self.assertEqual(len(first['notifications']), services.PAGE_SIZE)
        self.assertTrue(first['has_more'])
        second = self.fetch(before=first['next'])
        self.assertFalse(second['has_more'])
        keys = [n['key'] for n in first['notifications'] + second['notifications']]
        self.assertEqual(len(keys), services.PAGE_SIZE + 6)  # + the community
        self.assertEqual(len(set(keys)), len(keys))

    def test_unread_badge_resets_when_page_is_opened(self):
        Post.objects.create(community=self.hikers, author=self.bob, body='Hi')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(services.unread_count(self.alice), 2)  # the post and the community

        self.client.get(reverse('notifications'))
        self.alice.refresh_from_db()
        self.assertEqual(services.unread_count(self.alice), 0)

        Community.objects.create(name='Coders', category=Category.TECH, created_by=self.bob)
        self.assertEqual(services.unread_count(self.alice), 1)

    def test_requires_sign_in(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('api-notifications')).status_code, 403)
        self.assertEqual(self.client.get(reverse('notifications')).status_code, 302)
