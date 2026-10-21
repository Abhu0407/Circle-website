"""The live chat socket (ws://<site>/ws/chat/).

One socket per open browser tab. It is signed in with the normal Django
session cookie, refuses anyone not signed in or on a page from another site,
and only listens to the chats of communities the user belongs to.

A refused socket is accepted and then closed with a reason code (4401 not
signed in, 4403 page from another site), because a socket refused during
the handshake reaches the browser without any reason, and the page would
keep retrying. No data is sent before the close.

Browser -> server:
  {"type": "send", "community": 3, "body": "Hi", "client_id": "abc"}
  {"type": "read", "community": 3, "last_id": 120}
Server -> browser:
  {"type": "message", "message": {...}, "client_id": "abc"}   new message
  {"type": "read", "community": 3, "last_id": 120}            read in another tab
  {"type": "chats_changed"}                                   joined/left a community
  {"type": "error", "detail": "...", "client_id": "abc"}
"""

import logging
from urllib.parse import urlsplit

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.http.request import validate_host
from rest_framework.exceptions import APIException

from . import services

logger = logging.getLogger(__name__)

# Close codes (4000-4999 are free for apps).
CLOSE_NOT_SIGNED_IN = 4401
CLOSE_BAD_ORIGIN = 4403


def origin_allowed(scope):
    """True if the page that opened the socket is on this site (its host is
    in ALLOWED_HOSTS), so other sites can't open one with a visitor's cookie."""
    origin = dict(scope.get('headers', [])).get(b'origin', b'').decode('latin1')
    host = urlsplit(origin).hostname if origin else None
    allowed = settings.ALLOWED_HOSTS
    if not allowed and settings.DEBUG:  # what Django itself allows then
        allowed = ['.localhost', '127.0.0.1', '[::1]']
    return bool(host) and validate_host(host, allowed)


def _error_text(exc):
    detail = exc.detail
    if isinstance(detail, dict):
        detail = next(iter(detail.values()), '')
    if isinstance(detail, list):
        detail = detail[0] if detail else ''
    return str(detail)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not origin_allowed(self.scope):
            return await self.refuse(CLOSE_BAD_ORIGIN, 'the page is not on this site (check ALLOWED_HOSTS)')
        if user is None or not user.is_authenticated or not user.is_active:
            return await self.refuse(CLOSE_NOT_SIGNED_IN, 'not signed in')
        self.user = user
        self.community_groups = set()
        await self.channel_layer.group_add(services.user_group(user.pk), self.channel_name)
        await self.sync_groups()
        await self.accept()

    async def refuse(self, code, reason):
        logger.warning('Chat socket refused: %s.', reason)
        await self.accept()
        await self.close(code=code)

    async def disconnect(self, code):
        if not hasattr(self, 'user'):
            return
        await self.channel_layer.group_discard(services.user_group(self.user.pk), self.channel_name)
        for group in self.community_groups:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def sync_groups(self):
        """Listen to exactly the communities the user is in now."""
        ids = await database_sync_to_async(
            lambda: list(self.user.join_community.values_list('pk', flat=True))
        )()
        wanted = {services.community_group(pk) for pk in ids}
        for group in wanted - self.community_groups:
            await self.channel_layer.group_add(group, self.channel_name)
        for group in self.community_groups - wanted:
            await self.channel_layer.group_discard(group, self.channel_name)
        self.community_groups = wanted

    # ---------- from the browser ----------

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict):
            return
        kind = content.get('type')
        client_id = str(content.get('client_id', ''))[:64]
        try:
            if kind == 'send':
                await self.on_send(content, client_id)
            elif kind == 'read':
                await self.on_read(content)
        except APIException as exc:
            await self.send_json({'type': 'error', 'detail': _error_text(exc), 'client_id': client_id})

    async def on_send(self, content, client_id):
        # Text only; files are uploaded with POST /api/chats/<id>/messages/.
        message = await database_sync_to_async(services.create_message)(
            self.user, content.get('community'), content.get('body'),
        )
        await self.channel_layer.group_send(
            services.community_group(message['community']),
            {'type': 'chat.message', 'message': message, 'client_id': client_id},
        )

    async def on_read(self, content):
        community = content.get('community')
        last_id = await database_sync_to_async(services.mark_read)(self.user, community, content.get('last_id'))
        # Other tabs of the same user clear their unread count too.
        await self.channel_layer.group_send(
            services.user_group(self.user.pk),
            {'type': 'chat.read', 'community': int(community), 'last_id': last_id},
        )

    # ---------- from the channel layer ----------

    async def chat_message(self, event):
        # Only forward chats this socket still listens to (in case a leave
        # and a message cross each other).
        if services.community_group(event['message']['community']) in self.community_groups:
            await self.send_json({'type': 'message', 'message': event['message'], 'client_id': event.get('client_id', '')})

    async def chat_read(self, event):
        await self.send_json({'type': 'read', 'community': event['community'], 'last_id': event['last_id']})

    async def chat_membership(self, event):
        await self.sync_groups()
        await self.send_json({'type': 'chats_changed'})
