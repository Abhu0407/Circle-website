"""The For You page: which posts to show, in what order, and which
communities to suggest.

Both lean on the user's *taste*: how much they care about each category,
from the interests they picked on Profile plus what they do (communities
joined, posts written, liked and commented on).
"""
import hashlib
import math
from collections import Counter

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from apps.communities.models import Community
from apps.communities.views import distance_km

from .models import Comment, Post

# Only this many of the newest posts are shuffled into the feed.
FEED_POOL = 1000
# Weight of a post: 1, plus these for its category.
INTEREST_BOOST = 4  # a category picked as an interest
ACTIVITY_BOOST = 3  # times how active the user is in it (0..1)
# Posts newer than about this many days get up to twice the weight.
FRESH_DAYS = 3

# How much each kind of activity says about a category.
ACTIVITY_POINTS = {'joined': 2, 'posted': 1.5, 'commented': 1, 'liked': 0.5}


def activity_by_category(user):
    """{category: 0..1}: how active `user` is in each category, relative to
    their most active one. Interests aren't counted here."""
    points = Counter()
    sources = {
        'joined': user.join_community.values_list('category', flat=True),
        'posted': Post.objects.filter(author=user).values_list('community__category', flat=True),
        'commented': Comment.objects.filter(author=user).values_list('post__community__category', flat=True),
        'liked': user.liked_posts.values_list('community__category', flat=True),
    }
    for kind, categories in sources.items():
        for category in categories:
            points[category] += ACTIVITY_POINTS[kind]
    top = max(points.values(), default=0)
    return {category: p / top for category, p in points.items()} if top else {}


def _shuffle_key(seed, pk, weight):
    """Weighted random order (Efraimidis-Spirakis): sorting by u ** (1/w),
    largest first, puts heavier posts earlier more often. `u` comes from a
    hash so the same seed always gives the same order, page after page."""
    digest = hashlib.blake2b(f'{seed}:{pk}'.encode(), digest_size=8).digest()
    u = (int.from_bytes(digest, 'big') + 1) / (2 ** 64 + 1)  # 0 < u < 1
    return u ** (1 / weight)


def ranked_post_ids(user, seed):
    """Ids of other people's posts, newest FEED_POOL of them, shuffled with
    `seed`; posts in categories the user likes come up much more often."""
    interests = set(user.interested_category or [])
    activity = activity_by_category(user)
    now = timezone.now()
    rows = (
        Post.objects.exclude(author=user)
        .order_by('-created_at', '-id')
        .values_list('id', 'community__category', 'created_at')[:FEED_POOL]
    )
    keyed = []
    for pk, category, created_at in rows:
        age_days = max((now - created_at).total_seconds(), 0) / 86400
        weight = (
            (1 + INTEREST_BOOST * (category in interests) + ACTIVITY_BOOST * activity.get(category, 0))
            * (1 + 1 / (1 + age_days / FRESH_DAYS))
        )
        keyed.append((_shuffle_key(seed, pk, weight), pk))
    keyed.sort(reverse=True)
    return [pk for _, pk in keyed]


def suggested_communities(user, limit):
    """Up to `limit` communities `user` hasn't joined, best first, each
    with `members_total`, `is_member` (False), `distance_km` and `reason`
    (a short "why this one") set, as DiscoverCommunitySerializer expects."""
    interests = set(user.interested_category or [])
    activity = activity_by_category(user)
    labels = dict(Community._meta.get_field('category').choices)

    # People who share a community with the user.
    circle = (
        get_user_model().objects
        .filter(join_community__in=user.join_community.all())
        .exclude(pk=user.pk)
        .distinct()
    )
    communities = (
        Community.objects
        .exclude(members=user)
        .annotate(
            members_total=Count('members', distinct=True),
            # Members from the user's own communities.
            circle_count=Count('members', filter=Q(members__in=circle), distinct=True),
            # Posts here the user liked or commented on without joining.
            engaged=Count('posts', filter=Q(posts__likes=user) | Q(posts__comments__author=user), distinct=True),
        )
    )
    here = (user.latitude, user.longitude) if user.latitude is not None and user.longitude is not None else None
    hour = f'{timezone.now():%Y%m%d%H}'

    scored = []
    for c in communities:
        c.is_member = False
        has_point = here is not None and c.latitude is not None and c.longitude is not None
        c.distance_km = round(distance_km(*here, c.latitude, c.longitude), 1) if has_point else None

        reasons = []  # (score, text): the biggest one is shown
        if c.category in interests:
            reasons.append((4, f'You like {labels[c.category]}'))
        if activity.get(c.category):
            reasons.append((3 * activity[c.category], f'Active in {labels[c.category]}'))
        if c.engaged:
            reasons.append((min(3, 1.5 * c.engaged), 'You liked or commented on its posts'))
        if c.circle_count:
            n = c.circle_count
            reasons.append((min(2, 0.5 * n), f'{n} {"person" if n == 1 else "people"} from your communities'))
        if c.distance_km is not None and c.distance_km <= 50:
            reasons.append((2 / (1 + c.distance_km / 10), 'Near you'))
        popularity = 0.5 * math.log1p(c.members_total)
        # A little randomness (changing every hour) so the list doesn't sit still.
        jitter = int.from_bytes(hashlib.blake2b(f'{hour}:{user.pk}:{c.pk}'.encode(), digest_size=4).digest(),
                                'big') / 2 ** 32
        score = sum(s for s, _ in reasons) + popularity + jitter
        if c.members_total >= 5:
            reasons.append((popularity, 'Popular'))
        c.reason = max(reasons)[1] if reasons else 'New to you'
        scored.append((score, c))

    scored.sort(key=lambda sc: sc[0], reverse=True)
    return [c for _, c in scored[:limit]]
