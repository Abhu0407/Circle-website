"""The For You page: which posts to show, in what order, and which
communities to suggest.

Both lean on the user's *taste*: how much they care about each category,
from the interests they picked on Profile plus what they do (communities
joined, posts written, liked and commented on).

Posts are scored (see `post_score`) and shown best first, so the top of the
feed is what the user most likely wants. Every page load brings a new seed
that nudges each score a little, so a refresh doesn't show the very same
posts in the very same order; and one community isn't shown many times in
a row.
"""
import hashlib
import heapq
import math
from collections import Counter, defaultdict

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from apps.communities.models import Community
from apps.communities.views import distance_km

from .models import Comment, Post

# Only this many of the newest posts are ranked into the feed.
FEED_POOL = 1000

# What raises a post's score (they add up, on top of a base of 1).
JOINED_BOOST = 5     # from a community the user joined
INTEREST_BOOST = 4   # in a category picked as an interest
ACTIVITY_BOOST = 3   # times how active the user is in its category (0..1)
AUTHOR_BOOST = 2     # times how much the user engages with its author (0..1)
NEARBY_BOOST = 1.5   # from a community near the user (fades out by NEARBY_KM)
NEARBY_KM = 50
# Likes and comments make a post better, but only slowly (log scale).
ENGAGEMENT_WEIGHT = 0.4
# A post's score halves every this many days...
HALF_LIFE_DAYS = 2
# ...but never drops below this share, so good older posts can still show.
MIN_FRESHNESS = 0.1
# Posts the user already liked or commented on have been seen: push them down.
SEEN_FACTOR = 0.3
# How much a refresh can move a score: a random factor between e^-NOISE and
# e^NOISE. Bigger = more variety, smaller = stricter best-first order.
NOISE = 0.35
# Each post already shown from a community lowers the next one from it by this.
REPEAT_FACTOR = 0.85

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


def author_affinity(user):
    """{author id: 0..1}: how much `user` engages with each author's posts
    (likes, and comments counting double), relative to their favourite."""
    points = Counter()
    for author_id in user.liked_posts.values_list('author_id', flat=True):
        points[author_id] += 1
    for author_id in Comment.objects.filter(author=user).values_list('post__author_id', flat=True):
        points[author_id] += 2
    points.pop(None, None)
    points.pop(user.pk, None)
    top = max(points.values(), default=0)
    return {author: p / top for author, p in points.items()} if top else {}


def _noise(seed, pk):
    """A random factor around 1 for this post. It comes from a hash, so the
    same seed always gives the same order (pages follow on) and a new seed
    a slightly different one."""
    digest = hashlib.blake2b(f'{seed}:{pk}'.encode(), digest_size=8).digest()
    u = int.from_bytes(digest, 'big') / 2 ** 64  # 0 <= u < 1
    return math.exp(NOISE * (2 * u - 1))


def post_score(*, joined, interest, activity, author, distance, likes, comments, age_days, seen):
    """How much the user should want to see a post; higher goes first."""
    relevance = (
        1
        + JOINED_BOOST * joined
        + INTEREST_BOOST * interest
        + ACTIVITY_BOOST * activity
        + AUTHOR_BOOST * author
        + (NEARBY_BOOST * max(0, 1 - distance / NEARBY_KM) if distance is not None else 0)
    )
    quality = 1 + ENGAGEMENT_WEIGHT * math.log1p(likes + 2 * comments)
    freshness = max(0.5 ** (age_days / HALF_LIFE_DAYS), MIN_FRESHNESS)
    return relevance * quality * freshness * (SEEN_FACTOR if seen else 1)


def _spread_communities(scored):
    """[(score, pk, community id)] -> pks, best first, except that each post
    already taken from a community makes its next one count for less, so one
    busy community doesn't fill the screen."""
    queues = defaultdict(list)
    for score, pk, community in sorted(scored, reverse=True):
        queues[community].append((score, pk))
    heap = [(-q[0][0], community, 0) for community, q in queues.items()]
    heapq.heapify(heap)
    order = []
    while heap:
        _, community, i = heapq.heappop(heap)
        order.append(queues[community][i][1])
        if i + 1 < len(queues[community]):
            score = queues[community][i + 1][0] * REPEAT_FACTOR ** (i + 1)
            heapq.heappush(heap, (-score, community, i + 1))
    return order


def ranked_post_ids(user, seed):
    """Ids of other people's posts (the newest FEED_POOL of them), best
    match for `user` first, varied a little by `seed`."""
    interests = set(user.interested_category or [])
    activity = activity_by_category(user)
    authors = author_affinity(user)
    joined = set(user.join_community.values_list('id', flat=True))
    seen = set(user.liked_posts.values_list('id', flat=True))
    seen.update(Comment.objects.filter(author=user).values_list('post_id', flat=True))
    here = (user.latitude, user.longitude) if user.latitude is not None and user.longitude is not None else None
    now = timezone.now()
    rows = (
        Post.objects.exclude(author=user)
        .order_by('-created_at', '-id')
        .annotate(
            n_likes=Count('likes', distinct=True),
            n_comments=Count('comments', filter=Q(comments__is_deleted=False), distinct=True),
        )
        .values_list('id', 'community_id', 'community__category', 'community__latitude',
                     'community__longitude', 'author_id', 'created_at', 'n_likes', 'n_comments')
        [:FEED_POOL]
    )
    scored = []
    for pk, community, category, lat, lng, author, created_at, likes, comments in rows:
        has_point = here is not None and lat is not None and lng is not None
        score = post_score(
            joined=community in joined,
            interest=category in interests,
            activity=activity.get(category, 0),
            author=authors.get(author, 0),
            distance=distance_km(*here, lat, lng) if has_point else None,
            likes=likes,
            comments=comments,
            age_days=max((now - created_at).total_seconds(), 0) / 86400,
            seen=pk in seen,
        )
        scored.append((score * _noise(seed, pk), pk, community))
    return _spread_communities(scored)


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
