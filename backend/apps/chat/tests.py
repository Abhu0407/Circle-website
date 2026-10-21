import shutil
import tempfile
from pathlib import Path

from asgiref.sync import async_to_sync, sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from PIL import Image

from apps.communities.models import Community

from .models import Message
from .routing import websocket_urlpatterns

User = get_user_model()


def make_user(name):
    return User.objects.create_user(username=name, email=f'{name}@example.com', password='pw-12345-long')


class ChatApiTests(TestCase):
    def setUp(self):
        self.alice = make_user('alice')
        self.bob = make_user('bob')
        self.eve = make_user('eve')
        self.club = Community.objects.create(name='Chess club', category='games')
        self.alice.join_community.add(self.club)
        self.bob.join_community.add(self.club)

    def test_non_members_cannot_read_or_send(self):
        self.client.force_login(self.eve)
        messages_url = reverse('api-chat-messages', args=[self.club.pk])
        self.assertEqual(self.client.get(messages_url).status_code, 403)
        self.assertEqual(self.client.post(messages_url, {'body': 'hi'}, content_type='application/json').status_code, 403)
        self.assertFalse(Message.objects.exists())

    def test_signed_out_cannot_read(self):
        res = self.client.get(reverse('api-chat-messages', args=[self.club.pk]))
        self.assertIn(res.status_code, (401, 403))

    def test_unread_counts(self):
        self.client.force_login(self.alice)
        url = reverse('api-chat-messages', args=[self.club.pk])
        for text in ('one', 'two', 'three'):
            self.assertEqual(self.client.post(url, {'body': text}, content_type='application/json').status_code, 201)

        # Your own messages are never unread.
        alice_row = self.client.get(reverse('api-chats')).json()[0]
        self.assertEqual(alice_row['unread_count'], 0)
        self.assertEqual(alice_row['last_message']['body'], 'three')

        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(reverse('api-chats')).json()[0]['unread_count'], 3)
        self.client.post(reverse('api-chat-read', args=[self.club.pk]), {}, content_type='application/json')
        self.assertEqual(self.client.get(reverse('api-chats')).json()[0]['unread_count'], 0)

    def test_new_members_start_with_nothing_unread(self):
        Message.objects.create(community=self.club, author=self.alice, body='old news')
        self.eve.join_community.add(self.club)
        self.client.force_login(self.eve)
        self.assertEqual(self.client.get(reverse('api-chats')).json()[0]['unread_count'], 0)

    def test_message_validation(self):
        self.client.force_login(self.alice)
        url = reverse('api-chat-messages', args=[self.club.pk])
        self.assertEqual(self.client.post(url, {'body': '   '}, content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post(url, {'body': 'x' * 2001}, content_type='application/json').status_code, 400)

    def test_history_paging(self):
        msgs = [Message.objects.create(community=self.club, author=self.alice, body=str(i)) for i in range(60)]
        self.client.force_login(self.bob)
        url = reverse('api-chat-messages', args=[self.club.pk])
        page = self.client.get(url).json()
        self.assertEqual(len(page['messages']), 50)
        self.assertTrue(page['has_more'])
        self.assertEqual(page['messages'][-1]['id'], msgs[-1].pk)
        older = self.client.get(url, {'before': page['messages'][0]['id']}).json()
        self.assertEqual(len(older['messages']), 10)
        self.assertFalse(older['has_more'])
        newer = self.client.get(url, {'after': msgs[-3].pk}).json()
        self.assertEqual([m['body'] for m in newer['messages']], ['58', '59'])


class ChatSocketTests(TransactionTestCase):
    def setUp(self):
        self.alice = make_user('alice')
        self.bob = make_user('bob')
        self.eve = make_user('eve')
        self.club = Community.objects.create(name='Chess club', category='games')
        self.alice.join_community.add(self.club)
        self.bob.join_community.add(self.club)

    async def connect(self, user, origin='http://127.0.0.1:8000'):
        app = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(app, '/ws/chat/', headers=[(b'origin', origin.encode())])
        communicator.scope['user'] = user
        connected, code = await communicator.connect()
        return communicator, connected, code

    def test_messages_reach_members_only(self):
        async def run():
            alice, ok, _ = await self.connect(self.alice)
            self.assertTrue(ok)
            bob, _, _ = await self.connect(self.bob)
            eve, _, _ = await self.connect(self.eve)

            await alice.send_json_to({'type': 'send', 'community': self.club.pk, 'body': 'Hello!', 'client_id': 'c1'})
            for ws in (alice, bob):
                event = await ws.receive_json_from(timeout=2)
                self.assertEqual(event['type'], 'message')
                self.assertEqual(event['message']['body'], 'Hello!')
                self.assertEqual(event['message']['author']['username'], 'alice')
            self.assertTrue(await eve.receive_nothing(timeout=0.3))

            # Eve can't send into a community she isn't in.
            await eve.send_json_to({'type': 'send', 'community': self.club.pk, 'body': 'sneaky', 'client_id': 'e1'})
            event = await eve.receive_json_from(timeout=2)
            self.assertEqual(event['type'], 'error')
            self.assertTrue(await bob.receive_nothing(timeout=0.3))

            for ws in (alice, bob, eve):
                await ws.disconnect()

        async_to_sync(run)()
        self.assertEqual(list(Message.objects.values_list('body', flat=True)), ['Hello!'])

    def test_signed_out_socket_is_refused(self):
        from django.contrib.auth.models import AnonymousUser

        async def run():
            # Closed with a reason, so the page knows to stop retrying.
            ws, _, _ = await self.connect(AnonymousUser())
            self.assertEqual(await ws.receive_output(timeout=2), {'type': 'websocket.close', 'code': 4401})

        with self.assertLogs('apps.chat.consumers', 'WARNING'):
            async_to_sync(run)()

    def test_other_sites_are_refused(self):
        async def run():
            ws, _, _ = await self.connect(self.alice, origin='http://evil.example')
            self.assertEqual(await ws.receive_output(timeout=2), {'type': 'websocket.close', 'code': 4403})
            ws, _, _ = await self.connect(self.alice, origin='')
            self.assertEqual(await ws.receive_output(timeout=2), {'type': 'websocket.close', 'code': 4403})

        with self.assertLogs('apps.chat.consumers', 'WARNING'):
            async_to_sync(run)()

    def test_leaving_stops_messages(self):
        async def run():
            bob, _, _ = await self.connect(self.bob)
            alice, _, _ = await self.connect(self.alice)
            await sync_to_async(self.bob.join_community.remove)(self.club)
            self.assertEqual((await bob.receive_json_from(timeout=2))['type'], 'chats_changed')

            await alice.send_json_to({'type': 'send', 'community': self.club.pk, 'body': 'after you left'})
            await alice.receive_json_from(timeout=2)
            self.assertTrue(await bob.receive_nothing(timeout=0.3))
            await alice.disconnect()
            await bob.disconnect()

        async_to_sync(run)()


def jpeg_with_gps(size=(64, 48)):
    """A small JPEG carrying EXIF GPS data, like a phone photo."""
    import io

    from PIL import Image

    img = Image.new('RGB', size, (200, 30, 30))
    exif = Image.Exif()
    exif[0x8825] = {1: 'N', 2: (19.0, 4.0, 30.0), 3: 'E', 4: (72.0, 52.0, 10.0)}  # GPSInfo
    exif[0x010F] = 'PhoneMaker'
    out = io.BytesIO()
    img.save(out, 'JPEG', exif=exif)
    return out.getvalue()


@override_settings(CHAT_FILES_ROOT=Path(tempfile.mkdtemp(prefix='chat-files-test-')), CHAT_MAX_FILE_MB=1)
class ChatAttachmentTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.CHAT_FILES_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.alice = make_user('alice')
        self.bob = make_user('bob')
        self.eve = make_user('eve')
        self.club = Community.objects.create(name='Chess club', category='games')
        self.alice.join_community.add(self.club)
        self.bob.join_community.add(self.club)
        self.url = reverse('api-chat-messages', args=[self.club.pk])

    def upload(self, user, name, data, body=''):
        self.client.force_login(user)
        return self.client.post(self.url, {'file': SimpleUploadedFile(name, data), 'body': body})

    def test_photo_is_cleaned_and_shown_to_members(self):
        res = self.upload(self.alice, 'beach.jpg', jpeg_with_gps(), body='Look!')
        self.assertEqual(res.status_code, 201, res.content)
        att = res.json()['attachment']
        self.assertEqual((att['kind'], att['type'], att['name']), ('image', 'image/jpeg', 'beach.jpg'))
        self.assertEqual((att['width'], att['height']), (64, 48))
        self.assertEqual(res.json()['body'], 'Look!')

        # The saved copy has no EXIF (so no GPS location).
        message = Message.objects.get()
        with message.attachment.open('rb') as f, Image.open(f) as img:
            self.assertEqual(len(img.getexif()), 0)
        # Stored under a random name, not the uploaded one.
        self.assertNotIn('beach', message.attachment.name)

        self.client.force_login(self.bob)
        res = self.client.get(att['url'])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'image/jpeg')
        self.assertTrue(res['Content-Disposition'].startswith('inline'))
        self.assertEqual(res['X-Content-Type-Options'], 'nosniff')
        self.assertIn('sandbox', res['Content-Security-Policy'])
        self.assertTrue(b''.join(res.streaming_content).startswith(b'\xff\xd8'))
        res = self.client.get(att['url'], {'download': 1})
        self.assertTrue(res['Content-Disposition'].startswith('attachment'))

    def test_non_members_cannot_get_files(self):
        url = self.upload(self.alice, 'beach.jpg', jpeg_with_gps()).json()['attachment']['url']
        self.client.force_login(self.eve)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 404)
        # A member who leaves loses access too.
        self.bob.join_community.remove(self.club)
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_non_members_cannot_upload(self):
        self.assertEqual(self.upload(self.eve, 'a.txt', b'hello').status_code, 403)
        self.assertFalse(Message.objects.exists())

    def test_other_files_are_download_only(self):
        res = self.upload(self.alice, 'notes.pdf', b'%PDF-1.4 fake')
        self.assertEqual(res.status_code, 201)
        att = res.json()['attachment']
        self.assertEqual((att['kind'], att['size']), ('file', 13))
        res = self.client.get(att['url'])
        self.assertEqual(res['Content-Type'], 'application/octet-stream')
        self.assertTrue(res['Content-Disposition'].startswith('attachment'))

    def test_fake_photo_and_video_are_treated_as_files(self):
        res = self.upload(self.alice, 'evil.png', b'<html><script>alert(1)</script></html>')
        self.assertEqual(res.json()['attachment']['kind'], 'file')
        res = self.upload(self.alice, 'clip.mp4', b'not really a video at all')
        self.assertEqual(res.json()['attachment']['kind'], 'file')

    def test_video(self):
        mp4 = b'\x00\x00\x00\x18ftypmp42' + b'\x00' * 2000
        res = self.upload(self.alice, 'clip.mp4', mp4)
        att = res.json()['attachment']
        self.assertEqual((att['kind'], att['type']), ('video', 'video/mp4'))
        # Range requests let the player skip ahead.
        res = self.client.get(att['url'], HTTP_RANGE='bytes=4-11')
        self.assertEqual(res.status_code, 206)
        self.assertEqual(res['Content-Range'], f'bytes 4-11/{len(mp4)}')
        self.assertEqual(b''.join(res.streaming_content), b'ftypmp42')

    def test_blocked_too_big_and_empty(self):
        res = self.upload(self.alice, 'setup.exe', b'MZ...')
        self.assertEqual(res.status_code, 400)
        self.assertIn('.exe', res.json()['file'])
        self.assertEqual(self.upload(self.alice, 'big.bin', b'x' * (1024 * 1024 + 1)).status_code, 400)
        self.assertEqual(self.upload(self.alice, 'empty.txt', b'').status_code, 400)
        self.assertFalse(Message.objects.exists())

    def test_file_name_is_cleaned(self):
        res = self.upload(self.alice, '../../etc/pass"wd.txt', b'hi')
        self.assertEqual(res.json()['attachment']['name'], 'passwd.txt')

    def test_file_removed_with_message(self):
        self.upload(self.alice, 'a.txt', b'hello')
        message = Message.objects.get()
        path = Path(message.attachment.path)
        self.assertTrue(path.exists())
        with self.captureOnCommitCallbacks(execute=True):
            self.club.delete()
        self.assertFalse(path.exists())

    def test_attachment_shows_in_chat_list(self):
        self.upload(self.alice, 'a.txt', b'hello')
        self.client.force_login(self.bob)
        row = self.client.get(reverse('api-chats')).json()[0]
        self.assertEqual(row['unread_count'], 1)
        self.assertEqual(row['last_message']['attachment']['name'], 'a.txt')

    def test_rate_limit(self):
        for i in range(10):
            self.assertEqual(self.upload(self.alice, f'{i}.txt', b'x').status_code, 201)
        self.assertEqual(self.upload(self.alice, 'one-too-many.txt', b'x').status_code, 429)
