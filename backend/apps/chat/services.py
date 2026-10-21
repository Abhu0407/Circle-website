"""Chat logic shared by the JSON API (views.py) and the live socket
(consumers.py). Every function checks that the user is a member of the
community, so nobody else can read or write its chat."""

from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Count, F, Max, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, Throttled, ValidationError

from apps.communities.models import Community

from .attachments import check_upload
from .models import MAX_MESSAGE_LENGTH, ChatRead, Message

# How fast one person can send: at most this many messages per window (seconds).
RATE_LIMIT = (10, 10)


# Channel-layer group names (letters, digits, - _ . only).
def community_group(community_id):
    return f'chat.community.{community_id}'


def user_group(user_id):
    return f'chat.user.{user_id}'


def broadcast(group, event):
    """Send `event` to every open socket in `group` (from normal, non-async code)."""
    layer = get_channel_layer()
    if layer is not None:
        async_to_sync(layer.group_send)(group, event)


def member_community(user, community_id):
    """The community, if `user` belongs to it; else PermissionDenied."""
    try:
        community_id = int(community_id)
    except (TypeError, ValueError):
        raise PermissionDenied('Unknown community.')
    community = user.join_community.filter(pk=community_id).first() if user.is_authenticated else None
    if community is None:
        raise PermissionDenied('Join this community to see and send messages.')
    return community


def serialize_author(user):
    if user is None:
        return None
    return {'id': user.pk, 'username': user.username, 'name': user.name, 'profile_picture': user.profile_picture}


def serialize_attachment(message):
    """{url, name, size, kind (image|video|file), type, width, height} or None."""
    if not message.attachment:
        return None
    return {
        'url': message.attachment_url,
        'name': message.attachment_name,
        'size': message.attachment_size,
        'kind': message.attachment_kind,
        'type': message.attachment_type,
        'width': message.width,
        'height': message.height,
    }


def serialize_message(message):
    return {
        'id': message.pk,
        'community': message.community_id,
        'author': serialize_author(message.author),
        'body': message.body,
        'attachment': serialize_attachment(message),
        'created_at': message.created_at.isoformat(),
    }


def clean_body(body, required=True):
    if body is None:
        body = ''
    if not isinstance(body, str):
        raise ValidationError({'body': 'Write a message.'})
    body = body.strip()
    if not body and required:
        raise ValidationError({'body': 'Write a message.'})
    if len(body) > MAX_MESSAGE_LENGTH:
        raise ValidationError({'body': f'Messages can be at most {MAX_MESSAGE_LENGTH} characters.'})
    return body


def check_rate(user):
    """Refuse when the user sent too many messages just now."""
    limit, window = RATE_LIMIT
    since = timezone.now() - timedelta(seconds=window)
    if Message.objects.filter(author=user, created_at__gte=since).count() >= limit:
        raise Throttled(detail='You are sending messages too fast. Wait a moment.')


def create_message(user, community_id, body, upload=None):
    """Save a message (text, a file with an optional caption, or both) and
    return it serialized. The sender has read it."""
    community = member_community(user, community_id)
    body = clean_body(body, required=upload is None)
    check_rate(user)
    message = Message(community=community, author=user, body=body)
    if upload is not None:
        file = check_upload(upload)
        message.attachment_name = file.name
        message.attachment_size = file.size
        message.attachment_kind = file.kind
        message.attachment_type = file.content_type
        message.width, message.height = file.width, file.height
        message.attachment.save(file.name, file.content, save=False)
    message.save()
    _set_read(user, community.pk, message.pk)
    return serialize_message(message)


def messages_page(user, community_id, before=None, after=None, limit=50):
    """Up to `limit` messages, oldest first: the latest ones, those before
    message id `before` (older history), or those after `after` (catching
    up after a lost connection)."""
    community = member_community(user, community_id)
    qs = Message.objects.filter(community=community).select_related('author')
    if after is not None:
        rows = list(qs.filter(id__gt=after).order_by('id')[:limit + 1])
        has_more = len(rows) > limit
        rows = rows[:limit]
    else:
        if before is not None:
            qs = qs.filter(id__lt=before)
        rows = list(qs.order_by('-id')[:limit + 1])
        has_more = len(rows) > limit
        rows = rows[:limit][::-1]
    return {'messages': [serialize_message(m) for m in rows], 'has_more': has_more}


def _set_read(user, community_id, last_id):
    """Move the read marker forward (never back)."""
    read, created = ChatRead.objects.get_or_create(
        user=user, community_id=community_id, defaults={'last_read_id': last_id},
    )
    if not created and last_id > read.last_read_id:
        ChatRead.objects.filter(pk=read.pk, last_read_id__lt=last_id).update(last_read_id=last_id)


def mark_read(user, community_id, last_id=None):
    """Mark the chat read up to message `last_id` (default: all of it).
    Returns the id it was marked up to."""
    community = member_community(user, community_id)
    latest = Message.objects.filter(community=community).aggregate(m=Max('id'))['m'] or 0
    try:
        last_id = latest if last_id is None else min(int(last_id), latest)
    except (TypeError, ValueError):
        raise ValidationError({'last_id': 'Must be a message id.'})
    if last_id > 0:
        _set_read(user, community.pk, last_id)
    return last_id


def start_reading_from_now(user_ids, community_ids):
    """New members don't start with the whole history as unread."""
    for community_id in community_ids:
        latest = Message.objects.filter(community_id=community_id).aggregate(m=Max('id'))['m'] or 0
        for user_id in user_ids:
            ChatRead.objects.update_or_create(
                user_id=user_id, community_id=community_id, defaults={'last_read_id': latest},
            )


def chat_list(user):
    """The user's communities for the Chats page, latest activity first:
    [{id, name, image, category_label, url, members_count, unread_count, last_message}]."""
    last_read = ChatRead.objects.filter(user=user, community=OuterRef('pk')).values('last_read_id')[:1]
    members = (
        Community.members.through.objects.filter(community=OuterRef('pk'))
        .values('community').annotate(n=Count('*')).values('n')
    )
    communities = (
        user.join_community.all()
        .annotate(last_read=Coalesce(Subquery(last_read), Value(0)))
        .annotate(
            unread_count=Count(
                'messages',
                filter=Q(messages__id__gt=F('last_read')) & (Q(messages__author__isnull=True) | ~Q(messages__author=user)),
            ),
            last_message_id=Max('messages__id'),
            members_count=Coalesce(Subquery(members), Value(0)),
        )
    )
    communities = list(communities)
    last = Message.objects.select_related('author').in_bulk([c.last_message_id for c in communities if c.last_message_id])
    rows = [
        {
            'id': c.pk,
            'name': c.name,
            'image': c.cover_url,
            'category_label': c.get_category_display(),
            'url': reverse('community-detail', args=[c.pk]),
            'members_count': c.members_count,
            'unread_count': c.unread_count,
            'last_message': serialize_message(last[c.last_message_id]) if c.last_message_id else None,
        }
        for c in communities
    ]
    # Latest message first; quiet chats after, by name.
    rows.sort(key=lambda r: r['name'].lower())
    rows.sort(key=lambda r: r['last_message']['id'] if r['last_message'] else 0, reverse=True)
    return rows
