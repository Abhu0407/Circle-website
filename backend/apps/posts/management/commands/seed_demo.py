"""Demo data: users, one community per category, posts, likes and
nested comments, so every page has something to show.

    python manage.py seed_demo                  # add the demo data (once)
    python manage.py seed_demo --join alice     # ...and make alice a member of every demo community
    python manage.py seed_demo --reset          # remove the demo data, then add it again
    python manage.py seed_demo --clear          # only remove the demo data

Demo users have emails ending in @demo.circle and the password "demo-pass-123".
Removing them also removes their communities, posts and comments.
"""

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.communities.models import Category, Community
from apps.posts.models import Comment, Post

User = get_user_model()

DEMO_DOMAIN = 'demo.circle'
DEMO_PASSWORD = 'demo-pass-123'

# (label, lat, lng) around Mumbai.
PLACES = [
    ('Bandra West, Mumbai', 19.0596, 72.8295),
    ('Andheri East, Mumbai', 19.1136, 72.8697),
    ('Powai, Mumbai', 19.1176, 72.9060),
    ('Thane West, Thane', 19.2183, 72.9781),
    ('Goregaon East, Mumbai', 19.1663, 72.8526),
    ('Colaba, Mumbai', 18.9067, 72.8147),
    ('Dadar West, Mumbai', 19.0178, 72.8478),
    ('Malad West, Mumbai', 19.1874, 72.8484),
    ('Borivali West, Mumbai', 19.2307, 72.8567),
    ('Vashi, Navi Mumbai', 19.0771, 72.9986),
    ('Juhu, Mumbai', 19.1075, 72.8263),
    ('Lower Parel, Mumbai', 18.9953, 72.8302),
]

# (username, name, place index, interests)
USERS = [
    ('demo_aarav', 'Aarav Sharma', 0, ['sports', 'tech', 'games']),
    ('demo_priya', 'Priya Nair', 1, ['wellness', 'food', 'arts']),
    ('demo_rohan', 'Rohan Mehta', 2, ['tech', 'networking', 'learning']),
    ('demo_ananya', 'Ananya Iyer', 3, ['outdoors', 'adventure', 'fitness']),
    ('demo_kabir', 'Kabir Singh', 4, ['music', 'drinks', 'social']),
    ('demo_meera', 'Meera Joshi', 5, ['culture', 'arts', 'learning']),
    ('demo_vikram', 'Vikram Rao', 6, ['sports', 'fitness', 'health']),
    ('demo_sana', 'Sana Khan', 7, ['food', 'drinks', 'social']),
    ('demo_arjun', 'Arjun Patel', 8, ['education', 'tech', 'games']),
    ('demo_isha', 'Isha Desai', 10, ['wellness', 'health', 'other']),
]

# One community per category: (name, description, place index, two posts).
COMMUNITIES = {
    Category.SPORTS: (
        'Sunday Cricket Club',
        'Tennis-ball cricket every Sunday morning at Shivaji Park. All skill levels welcome; we split teams on the spot.',
        6,
        ['Match this Sunday at 7am! We need two more players for a full 8-a-side.',
         'Who has a spare bat? Mine finally cracked after last week’s sixes.'],
    ),
    Category.FITNESS: (
        'Morning Run Crew',
        'Easy 5k runs along Carter Road, three mornings a week. No one gets left behind.',
        0,
        ['New route idea: Carter Road to Bandstand and back is almost exactly 5k.',
         'Hit a personal best today, 26:40! Thanks for the pacing, everyone.'],
    ),
    Category.OUTDOORS: (
        'Sahyadri Trekkers',
        'Monsoon and winter treks in the Sahyadris. We share transport from Thane and plan beginner-friendly routes.',
        3,
        ['Planning Kalsubai for the first weekend of next month. Who is in?',
         'Photos from Rajmachi are up! The fireflies were unreal this year.'],
    ),
    Category.ADVENTURE: (
        'Weekend Road Trippers',
        'Spontaneous weekend drives out of the city: Lonavala, Alibaug, Igatpuri and beyond. Car-pooling sorted in the group.',
        9,
        ['Konkan coast drive this Saturday, leaving Vashi at 5am. Two seats free.',
         'Tip: the old Mumbai–Pune highway is way more scenic than the expressway.'],
    ),
    Category.TECH: (
        'Mumbai JS Meetup',
        'Monthly meetups on JavaScript, Vue, React and Node. Talks, lightning demos and plenty of chai.',
        2,
        ['Next meetup: "Vue 3 without a build step". Looking for one more lightning talk!',
         'Slides from last month’s talk on web performance are linked in the thread below.'],
    ),
    Category.ARTS: (
        'Sketch & Chai',
        'Urban sketching around the city followed by chai and a look at everyone’s pages.',
        5,
        ['Sketching the Gateway of India this Saturday, 4pm. Bring whatever you draw with.',
         'Watercolour or ink for quick street scenes? Curious what everyone prefers.'],
    ),
    Category.CULTURE: (
        'Heritage Walks Mumbai',
        'Guided walks through the Fort precinct, Kala Ghoda and old Bombay neighbourhoods.',
        5,
        ['Fort precinct art deco walk on Sunday. Meet at Flora Fountain at 8am.',
         'Did you know Kala Ghoda is named after a statue that hasn’t been there since 1965?'],
    ),
    Category.MUSIC: (
        'Open Mic Nights',
        'Friendly open mics for singers, poets and comics. First-timers get the first slot.',
        0,
        ['Open mic this Friday! Sign-ups close Thursday night.',
         'Anyone want to form a little acoustic band for the next one?'],
    ),
    Category.FOOD: (
        'Street Food Hunters',
        'We eat our way through Mumbai one khau galli at a time.',
        7,
        ['Mohammed Ali Road food walk this weekend. Come hungry!',
         'Best vada pav in the western suburbs: go. Defend your answer.'],
    ),
    Category.DRINKS: (
        'Third Wave Coffee Club',
        'Cafe hopping, home brewing and cupping sessions for coffee nerds.',
        11,
        ['Cupping session at a Lower Parel roastery on Saturday. Six spots left.',
         'Switched from French press to AeroPress. Never going back.'],
    ),
    Category.GAMES: (
        'Board Game Fridays',
        'Catan, Codenames, Ticket to Ride and more, every Friday evening. Games provided.',
        1,
        ['This Friday: Wingspan tournament! Teaching session at 7pm for new players.',
         'Just got Azul. Who wants to try it with me?'],
    ),
    Category.LEARNING: (
        'Book Circle',
        'One book a month, discussed over coffee. Fiction and non-fiction alternate.',
        8,
        ['This month we’re reading "Sapiens". Discussion on the last Sunday.',
         'Vote for next month’s pick in the comments!'],
    ),
    Category.EDUCATION: (
        'Weekend Python Classes',
        'Free beginner Python sessions run by volunteers, every Saturday afternoon.',
        2,
        ['Week 3: loops and lists. Bring a laptop with Python installed.',
         'Homework solutions are in the comments, try it yourself first!'],
    ),
    Category.SOCIAL: (
        'New in Mumbai',
        'Just moved to the city? Meet other newcomers, swap tips and make friends.',
        4,
        ['Welcome drinks for newcomers next Saturday in Goregaon!',
         'What’s one thing you wish you knew when you moved to Mumbai?'],
    ),
    Category.NETWORKING: (
        'Startup Founders Breakfast',
        'A small breakfast for founders and early employees to share what’s working.',
        11,
        ['Breakfast this Thursday at 8:30. Topic: hiring your first five.',
         'Looking for a co-founder with ops experience. Happy to chat over coffee.'],
    ),
    Category.HEALTH: (
        'Healthy Habits Club',
        'Small weekly challenges for better sleep, food and screen time, with lots of encouragement.',
        10,
        ['This week’s challenge: 8 glasses of water a day. Check in below!',
         'Swapped my evening scroll for a 20-minute walk. Sleeping so much better.'],
    ),
    Category.WELLNESS: (
        'Sunrise Yoga Juhu',
        'Free yoga on Juhu beach at sunrise. Bring a mat and water.',
        10,
        ['Tomorrow’s session focuses on breathing. See you at 6:15!',
         'Beach was perfect today. Thank you for the energy, everyone.'],
    ),
    Category.OTHER: (
        'Pet Parents Mumbai',
        'Dog walks, pet-friendly cafes and advice for pet parents across the city.',
        0,
        ['Dog meetup at Joggers Park on Sunday morning. Leashes on, please!',
         'Any recommendations for a good vet near Bandra?'],
    ),
}

COMMENTS = [
    'Count me in!',
    'What time does it start?',
    'This sounds great, will try to make it.',
    'Can I bring a friend along?',
    'Thanks for organising this!',
    'Love this idea 🙌',
    'I’m new here, is this beginner friendly?',
    'Missed the last one, not missing this!',
]
REPLIES = [
    'Yes, absolutely!',
    'Same here, see you there.',
    'Sure, the more the merrier.',
    'It’s very beginner friendly, don’t worry.',
    'Agreed!',
    'Haha, true.',
    'I can give you a lift if you need one.',
]


class Command(BaseCommand):
    help = 'Add demo users, communities (one per category), posts, likes and nested comments.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Remove the demo data first, then add it again.')
        parser.add_argument('--clear', action='store_true', help='Only remove the demo data.')
        parser.add_argument('--join', metavar='USERNAME', action='append', default=[],
                            help='Also make this (real) user a member of every demo community. Repeatable.')

    def handle(self, *args, **options):
        demo_users = User.objects.filter(email__endswith=f'@{DEMO_DOMAIN}')
        if options['clear'] or options['reset']:
            self.clear(demo_users)
            if options['clear']:
                return
        elif demo_users.exists():
            self.stdout.write('Demo data already exists. Use --reset to recreate it.')
            communities = Community.objects.filter(created_by__in=demo_users)
            self.join(options['join'], communities)
            return

        with transaction.atomic():
            communities = self.seed()
            self.join(options['join'], communities)

    def clear(self, demo_users):
        communities = Community.objects.filter(created_by__in=demo_users)
        n_communities = communities.count()
        for community in communities:
            if community.image:
                community.image.delete(save=False)
        communities.delete()
        n_users = demo_users.count()
        demo_users.delete()
        self.stdout.write(f'Removed {n_users} demo users and {n_communities} demo communities.')

    def join(self, usernames, communities):
        for username in usernames:
            user = User.objects.filter(username__iexact=username).first()
            if user is None:
                raise CommandError(f'No user named "{username}".')
            user.join_community.add(*communities)
            self.stdout.write(f'{user.username} is now a member of {len(communities)} demo communities.')

    def seed(self):
        rng = random.Random(42)
        now = timezone.now()

        users = []
        for username, name, place, interests in USERS:
            label, lat, lng = PLACES[place]
            user = User(
                username=username, email=f'{username}@{DEMO_DOMAIN}', name=name,
                first_name=name.split()[0], last_name=name.split()[-1],
                location=label, latitude=lat, longitude=lng, interested_category=interests,
            )
            user.set_password(DEMO_PASSWORD)
            user.save()
            users.append(user)

        communities = []
        n_posts = n_comments = 0
        for category, (name, description, place, posts) in COMMUNITIES.items():
            label, lat, lng = PLACES[place]
            # People interested in this category join it first; a few others too.
            fans = [u for u in users if category in u.interested_category]
            others = [u for u in users if u not in fans]
            members = fans + rng.sample(others, rng.randint(2, 4))
            creator = members[0]

            community = Community.objects.create(
                name=name, description=description, category=category,
                location=label, latitude=lat, longitude=lng, created_by=creator,
            )
            community.members.add(*members)
            communities.append(community)

            for i, body in enumerate(posts):
                author = creator if i == 0 else rng.choice(members)
                post = Post.objects.create(community=community, author=author, body=body)
                created = now - timedelta(days=rng.randint(0, 20), hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
                post.likes.add(*rng.sample(members, rng.randint(0, len(members))))
                post.shares_count = rng.randint(0, 6)
                post.save(update_fields=['shares_count'])
                n_posts += 1
                n_comments += self.add_thread(rng, post, members, created)
                Post.objects.filter(pk=post.pk).update(created_at=created, updated_at=created)

        self.stdout.write(self.style.SUCCESS(
            f'Added {len(users)} users, {len(communities)} communities (one per category), '
            f'{n_posts} posts and {n_comments} comments.\n'
            f'Sign in as any demo user (e.g. demo_aarav) with the password "{DEMO_PASSWORD}".'
        ))
        return communities

    def add_thread(self, rng, post, members, posted_at):
        """1-3 comments, each with up to 2 replies, some replies replied to again."""
        count = 0
        at = posted_at

        def comment(body, parent=None):
            nonlocal count, at
            at = min(at + timedelta(minutes=rng.randint(5, 180)), timezone.now())
            c = Comment.objects.create(post=post, parent=parent, author=rng.choice(members), body=body)
            Comment.objects.filter(pk=c.pk).update(created_at=at)
            count += 1
            return c

        for top_body in rng.sample(COMMENTS, rng.randint(1, 3)):
            top = comment(top_body)
            for _ in range(rng.randint(0, 2)):
                reply = comment(rng.choice(REPLIES), top)
                if rng.random() < 0.4:
                    comment(rng.choice(REPLIES), reply)
        return count
