"""Notifications: every post uploaded and every community created by other
people, newest first. Nothing is stored for them; they are read straight
from Post and Community. `User.notifications_seen_at` marks which are new."""

from django.db.models import Q
from django.urls import reverse
from django.utils.dateparse import parse_datetime

from apps.communities.models import Community
from apps.posts.models import Post

PAGE_SIZE = 20
KINDS = ('all', 'posts', 'communities')
# Ties on created_at are common (coarse clocks), so the order is
# (created_at, type, id), newest first, and pages continue from a cursor
# holding all three.
TYPE_RANK = {'post': 1, 'community': 0}


def _person(user):
    if user is None:
        return None
    return {'id': user.pk, 'username': user.username, 'name': user.name, 'profile_picture': user.profile_picture}


def _post_item(post):
    return {
        'type': 'post',
        'id': post.pk,
        'key': f'post-{post.pk}',
        'created_at': post.created_at,
        'actor': _person(post.author),
        'community': {'id': post.community_id, 'name': post.community.name, 'image': post.community.cover_url},
        'text': post.body[:160],
        'media': 'video' if post.video else 'image' if post.image else '',
        'image': post.image.url if post.image else None,
        'url': reverse('post-detail', args=[post.pk]),
    }


def _community_item(community):
    return {
        'type': 'community',
        'id': community.pk,
        'key': f'community-{community.pk}',
        'created_at': community.created_at,
        'actor': _person(community.created_by),
        'community': {'id': community.pk, 'name': community.name, 'image': community.cover_url},
        'text': community.description[:160],
        'category': community.get_category_display(),
        'location': community.location,
        'url': reverse('community-detail', args=[community.pk]),
    }


def _posts(user):
    return Post.objects.exclude(author=user).select_related('author', 'community')


def _communities(user):
    return Community.objects.exclude(created_by=user).select_related('created_by')


def seen_at(user):
    """Things created after this are new (a new account starts with nothing new)."""
    return user.notifications_seen_at or user.date_joined


def _sort_key(item):
    return item['created_at'], TYPE_RANK[item['type']], item['id']


def make_cursor(item):
    return f"{item['created_at'].isoformat()}|{item['type']}|{item['id']}"


def parse_cursor(value):
    """(created_at, type rank, id) from make_cursor(), or None if it isn't one."""
    try:
        when, kind, pk = value.split('|')
        when, rank, pk = parse_datetime(when), TYPE_RANK[kind], int(pk)
    except (ValueError, KeyError):
        return None
    return (when, rank, pk) if when else None


def _before(queryset, rank, cursor):
    """Rows of type `rank` that come after `cursor` in the newest-first order."""
    when, cursor_rank, pk = cursor
    q = Q(created_at__lt=when)
    if rank < cursor_rank:
        q |= Q(created_at=when)
    elif rank == cursor_rank:
        q |= Q(created_at=when, pk__lt=pk)
    return queryset.filter(q)


def notifications_page(user, kind='all', before=None, limit=PAGE_SIZE):
    """{notifications (newest first), has_more, next}. `before`: a cursor from
    parse_cursor(); pass the previous page's `next` to continue."""
    posts, communities = _posts(user), _communities(user)
    if before is not None:
        posts = _before(posts, TYPE_RANK['post'], before)
        communities = _before(communities, TYPE_RANK['community'], before)

    items = []
    if kind in ('all', 'posts'):
        items += [_post_item(p) for p in posts.order_by('-created_at', '-id')[:limit + 1]]
    if kind in ('all', 'communities'):
        items += [_community_item(c) for c in communities.order_by('-created_at', '-id')[:limit + 1]]
    items.sort(key=_sort_key, reverse=True)
    page, has_more = items[:limit], len(items) > limit
    return {'notifications': page, 'has_more': has_more, 'next': make_cursor(page[-1]) if has_more else None}


def unread_count(user):
    """How many posts and communities appeared since the user last opened Notifications."""
    since = seen_at(user)
    return _posts(user).filter(created_at__gt=since).count() + _communities(user).filter(created_at__gt=since).count()
