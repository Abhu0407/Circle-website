import io
import os
import tempfile
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from PIL import Image

from apps.communities.models import Category, Community

from .models import Comment, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostTests(TestCase):
    def setUp(self):
        self.hikers = Community.objects.create(name='Hikers')
        self.coders = Community.objects.create(name='Coders')
        self.alice = User.objects.create_user('alice', 'alice@example.com', 'S3cure-pass!')
        self.bob = User.objects.create_user('bob', 'bob@example.com', 'S3cure-pass!')
        self.alice.join_community.add(self.hikers)
        self.client.force_login(self.alice)

    def publish(self, community, body='Trail on Sunday?'):
        return self.client.post(reverse('api-posts'), {'community_id': community.pk, 'body': body},
                                content_type='application/json')

    def test_member_can_post_and_post_shows_community_and_author(self):
        response = self.publish(self.hikers)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['community']['name'], 'Hikers')
        self.assertEqual(data['author']['username'], 'alice')
        self.assertEqual((data['likes_count'], data['comments_count'], data['liked']), (0, 0, False))
        self.assertTrue(data['is_author'])

    def test_non_member_cannot_post(self):
        response = self.publish(self.coders)
        self.assertEqual(response.status_code, 400)
        self.assertIn('community_id', response.json())
        self.assertFalse(Post.objects.exists())

    def test_empty_post_rejected(self):
        response = self.publish(self.hikers, body='   ')
        self.assertEqual(response.status_code, 400)
        self.assertIn('body', response.json())

    def test_feed_has_joined_communities_only(self):
        Post.objects.create(community=self.hikers, author=self.alice, body='mine')
        Post.objects.create(community=self.coders, author=self.bob, body='other')
        results = self.client.get(reverse('api-posts')).json()['results']
        self.assertEqual([p['body'] for p in results], ['mine'])
        results = self.client.get(reverse('api-posts'), {'community': self.coders.pk}).json()['results']
        self.assertEqual([p['body'] for p in results], ['other'])

    def test_only_author_can_edit_or_delete(self):
        post = Post.objects.create(community=self.hikers, author=self.bob, body='bob says')
        url = reverse('api-post', args=[post.pk])
        self.assertEqual(self.client.patch(url, {'body': 'x'}, content_type='application/json').status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.client.force_login(self.bob)
        self.assertEqual(self.client.patch(url, {'body': 'edited'}, content_type='application/json').json()['body'],
                         'edited')
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_like_and_unlike(self):
        post = Post.objects.create(community=self.hikers, author=self.bob, body='hi')
        url = reverse('api-post-like', args=[post.pk])
        self.assertEqual(self.client.post(url).json(), {'liked': True, 'likes_count': 1})
        self.assertEqual(self.client.post(url).json(), {'liked': True, 'likes_count': 1})  # idempotent
        detail = self.client.get(reverse('api-post', args=[post.pk])).json()
        self.assertTrue(detail['liked'])
        self.assertEqual(self.client.delete(url).json(), {'liked': False, 'likes_count': 0})

    def test_share_counts_and_returns_link(self):
        post = Post.objects.create(community=self.hikers, author=self.bob, body='hi')
        data = self.client.post(reverse('api-post-share', args=[post.pk])).json()
        self.assertEqual(data['shares_count'], 1)
        self.assertTrue(data['url'].endswith(reverse('post-detail', args=[post.pk])))

    def test_post_page_renders(self):
        post = Post.objects.create(community=self.hikers, author=self.bob, body='hi')
        response = self.client.get(reverse('post-detail', args=[post.pk]))
        self.assertContains(response, 'pages/post/main.vue')
        self.assertContains(response, 'Hikers')
        self.assertEqual(self.client.get(reverse('post-detail', args=[999])).status_code, 404)


class CommentTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', 'alice@example.com', 'S3cure-pass!')
        self.bob = User.objects.create_user('bob', 'bob@example.com', 'S3cure-pass!')
        community = Community.objects.create(name='Hikers')
        self.post = Post.objects.create(community=community, author=self.alice, body='hi')
        self.url = reverse('api-post-comments', args=[self.post.pk])
        self.client.force_login(self.alice)

    def comment(self, body, parent=None):
        response = self.client.post(self.url, {'body': body, 'parent': parent}, content_type='application/json')
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()['id']

    def test_nested_replies_come_back_as_a_tree(self):
        top = self.comment('top')
        reply = self.comment('reply', top)
        self.comment('reply to reply', reply)
        self.comment('second top')
        tree = self.client.get(self.url).json()
        self.assertEqual([c['body'] for c in tree], ['top', 'second top'])
        self.assertEqual(tree[0]['replies'][0]['body'], 'reply')
        self.assertEqual(tree[0]['replies'][0]['replies'][0]['body'], 'reply to reply')
        self.assertEqual(self.client.get(reverse('api-post', args=[self.post.pk])).json()['comments_count'], 4)

    def test_reply_to_comment_on_other_post_rejected(self):
        other = Post.objects.create(community=self.post.community, author=self.alice, body='x')
        stray = Comment.objects.create(post=other, author=self.alice, body='elsewhere')
        response = self.client.post(self.url, {'body': 'hi', 'parent': stray.pk}, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('parent', response.json())

    def test_deleting_comment_with_replies_keeps_thread(self):
        top = self.comment('top')
        self.client.force_login(self.bob)
        reply = self.comment('reply', top)
        self.client.force_login(self.alice)
        self.assertEqual(self.client.delete(reverse('api-post-comment', args=[self.post.pk, top])).status_code, 204)
        tree = self.client.get(self.url).json()
        self.assertTrue(tree[0]['is_deleted'])
        self.assertIsNone(tree[0]['author'])
        self.assertEqual(tree[0]['replies'][0]['body'], 'reply')

        # Once its last reply goes, the blanked comment goes too.
        self.client.force_login(self.bob)
        self.client.delete(reverse('api-post-comment', args=[self.post.pk, reply]))
        self.assertEqual(self.client.get(self.url).json(), [])

    def test_only_author_can_delete_or_edit_comment(self):
        top = self.comment('top')
        url = reverse('api-post-comment', args=[self.post.pk, top])
        self.client.force_login(self.bob)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.assertEqual(self.client.patch(url, {'body': 'x'}, content_type='application/json').status_code, 403)
        self.client.force_login(self.alice)
        response = self.client.patch(url, {'body': 'edited'}, content_type='application/json')
        self.assertEqual(response.json()['body'], 'edited')

    def test_api_requires_sign_in(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.get(reverse('api-posts')).status_code, 403)


class ForYouTests(TestCase):
    def setUp(self):
        self.sports = Community.objects.create(name='Footy', category=Category.SPORTS)
        self.music = Community.objects.create(name='Band', category=Category.MUSIC)
        self.food = Community.objects.create(name='Cooks', category=Category.FOOD)
        self.alice = User.objects.create_user('alice', 'alice@example.com', 'S3cure-pass!',
                                              interested_category=['sports'])
        self.bob = User.objects.create_user('bob', 'bob@example.com', 'S3cure-pass!')
        self.alice.join_community.add(self.food)
        self.client.force_login(self.alice)

    def feed(self, seed='s', offset=0):
        return self.client.get(reverse('api-feed'), {'seed': seed, 'offset': offset}).json()

    def test_feed_has_every_community_but_not_own_posts_and_pages_follow_on(self):
        for i in range(8):
            for c in (self.sports, self.music):
                Post.objects.create(community=c, author=self.bob, body=f'{c.name} {i}')
        Post.objects.create(community=self.food, author=self.alice, body='mine')

        first = self.feed()
        self.assertEqual(len(first['results']), 10)
        self.assertIn('offset=10', first['next'])
        second = self.client.get(first['next']).json()
        self.assertIsNone(second['next'])
        ids = [p['id'] for p in first['results'] + second['results']]
        self.assertEqual(len(ids), 16)
        self.assertEqual(len(set(ids)), 16)
        self.assertNotIn('mine', [p['body'] for p in first['results'] + second['results']])
        # Same seed, same order.
        self.assertEqual([p['id'] for p in self.feed()['results']], ids[:10])

    def test_feed_favours_interests(self):
        for i in range(30):
            Post.objects.create(community=self.sports, author=self.bob, body='s')
            Post.objects.create(community=self.music, author=self.bob, body='m')
        top = [p['community']['category'] for seed in 'abcde' for p in self.feed(seed)['results']]
        self.assertGreater(top.count('sports'), top.count('music') * 2)

    def test_feed_puts_best_matches_first(self):
        old = timezone.now() - timedelta(days=10)
        for i in range(5):
            Post.objects.create(community=self.music, author=self.bob, body='other')
            Post.objects.create(community=self.sports, author=self.bob, body='interest')
            Post.objects.create(community=self.food, author=self.bob, body='joined')
        stale = Post.objects.create(community=self.food, author=self.bob, body='stale')
        Post.objects.filter(pk=stale.pk).update(created_at=old)
        for seed in 'abc':
            bodies = [p['body'] for p in self.feed(seed)['results'] + self.feed(seed, 10)['results']]
            # Fresh joined and interest posts come before unrelated and stale ones.
            self.assertEqual(set(bodies[:10]), {'joined', 'interest'})
            self.assertIn('stale', bodies[10:])

    def test_new_seed_changes_order_and_one_community_does_not_crowd(self):
        self.alice.join_community.add(self.music)
        for i in range(10):
            Post.objects.create(community=self.food, author=self.bob, body='food')
            Post.objects.create(community=self.music, author=self.bob, body='music')
        orders = {tuple(p['id'] for p in self.feed(seed)['results']) for seed in 'abcdef'}
        self.assertGreater(len(orders), 1)
        # Equally good communities take turns instead of one filling the top.
        for seed in 'abcdef':
            self.assertEqual({p['body'] for p in self.feed(seed)['results'][:4]}, {'food', 'music'})

    def test_suggestions_skip_joined_and_rank_interests_first(self):
        data = self.client.get(reverse('api-feed-communities')).json()
        self.assertEqual([c['name'] for c in data][0], 'Footy')
        self.assertNotIn('Cooks', [c['name'] for c in data])
        self.assertEqual(data[0]['reason'], 'You like Sports')
        self.assertFalse(data[0]['is_member'])

    def test_home_opens_on_for_you(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'pages/home/main.vue')
        self.assertContains(response, reverse('api-feed'))


class SeedDemoTests(TestCase):
    def run_seed(self, *args):
        call_command('seed_demo', *args, stdout=StringIO())

    def test_seeds_every_category_and_can_be_cleared(self):
        me = User.objects.create_user('me', 'me@example.com', 'S3cure-pass!')
        self.run_seed('--join', 'me')
        self.assertEqual(set(Community.objects.values_list('category', flat=True)), set(Category.values))
        self.assertEqual(me.join_community.count(), len(Category.values))
        self.assertTrue(Post.objects.exists())
        # Some replies are nested under other comments.
        self.assertTrue(Comment.objects.filter(parent__isnull=False).exists())

        self.run_seed()  # second run doesn't duplicate
        self.assertEqual(Community.objects.count(), len(Category.values))

        self.run_seed('--clear')
        self.assertFalse(Community.objects.exists())
        self.assertEqual(list(User.objects.values_list('username', flat=True)), ['me'])


MP4 = b'\x00\x00\x00\x18ftypmp42' + b'\x00' * 3000


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), POST_MAX_VIDEO_MB=1)
class PostVideoTests(TestCase):
    def setUp(self):
        self.hikers = Community.objects.create(name='Hikers')
        self.alice = User.objects.create_user('alice', 'alice@example.com', 'S3cure-pass!')
        self.alice.join_community.add(self.hikers)
        self.client.force_login(self.alice)

    def post(self, **files):
        data = {'community_id': self.hikers.pk, 'body': ''}
        data.update({k: SimpleUploadedFile(name, content) for k, (name, content) in files.items()})
        return self.client.post(reverse('api-posts'), data)

    def test_video_post_plays_with_seeking(self):
        res = self.post(video=('trail.mov', MP4))
        self.assertEqual(res.status_code, 201, res.content)
        url = res.json()['video']
        self.assertEqual(url, reverse('api-post-video', args=[res.json()['id']]))
        self.assertIsNone(res.json()['image'])
        post = Post.objects.get()
        self.assertTrue(post.video.name.endswith('.mp4'))  # .mov stored as .mp4
        self.assertEqual(post.video_type, 'video/mp4')

        res = self.client.get(url, HTTP_RANGE='bytes=4-11')
        self.assertEqual(res.status_code, 206)
        self.assertEqual(b''.join(res.streaming_content), b'ftypmp42')
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_rejects_fake_big_and_both(self):
        self.assertEqual(self.post(video=('x.mp4', b'not a video, just text')).status_code, 400)
        self.assertEqual(self.post(video=('x.exe', MP4)).status_code, 400)
        self.assertEqual(self.post(video=('big.mp4', MP4 + b'\x00' * 1024 * 1024)).status_code, 400)
        out = io.BytesIO()
        Image.new('RGB', (4, 4)).save(out, 'PNG')
        res = self.post(video=('a.mp4', MP4), image=('a.png', out.getvalue()))
        self.assertEqual(res.status_code, 400)
        self.assertFalse(Post.objects.exists())

    def test_video_file_removed_with_post(self):
        res = self.post(video=('a.mp4', MP4))
        path = Post.objects.get().video.path
        self.client.delete(reverse('api-post', args=[res.json()['id']]))
        self.assertFalse(os.path.exists(path))
