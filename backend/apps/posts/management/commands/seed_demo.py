"""Demo data: 120 users, 36 communities (two per category), posts with
photos, likes, shares and nested comments, so every page has something to show.

    python manage.py seed_demo                  # add the demo data (once)
    python manage.py seed_demo --users 200      # ...with a different number of users
    python manage.py seed_demo --join alice     # ...and make alice a member of every demo community
    python manage.py seed_demo --reset          # remove the demo data, then add it again
    python manage.py seed_demo --clear          # only remove the demo data

Demo users have emails ending in @demo.circle and the password "Abcd@1234".
Users only join communities that match their interests (plus the odd one
outside them), so nobody is in every community.

About half the posts get a photo. Photos are downloaded from picsum.photos;
without internet, simple drawn pictures are used instead. They are saved
under MEDIA_ROOT/post_images/ and removed again with --clear / --reset.
"""

import colorsys
import io
import random
import urllib.request
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from apps.accounts.models import AVATARS
from apps.communities.models import Category, Community, covers_for
from apps.posts.models import Comment, Post

User = get_user_model()

DEMO_DOMAIN = 'demo.circle'
DEMO_PASSWORD = 'Abcd@1234'
DEFAULT_USERS = 120
PHOTO_POOL = 40          # distinct photos downloaded, reused across posts
PHOTO_CHANCE = 0.5       # share of posts that get a photo

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
    ('Chembur, Mumbai', 19.0522, 72.9005),
    ('Kurla West, Mumbai', 19.0726, 72.8845),
    ('Santacruz East, Mumbai', 19.0806, 72.8550),
    ('Worli, Mumbai', 19.0176, 72.8172),
    ('Kandivali East, Mumbai', 19.2058, 72.8697),
    ('Mulund West, Mumbai', 19.1726, 72.9425),
    ('Ghatkopar East, Mumbai', 19.0790, 72.9080),
    ('Kharghar, Navi Mumbai', 19.0473, 73.0699),
    ('Matunga, Mumbai', 19.0272, 72.8570),
    ('Vile Parle East, Mumbai', 19.0990, 72.8486),
    ('Mira Road, Thane', 19.2813, 72.8686),
    ('Fort, Mumbai', 18.9345, 72.8352),
]

FIRST_NAMES = [
    'Aarav', 'Priya', 'Rohan', 'Ananya', 'Kabir', 'Meera', 'Vikram', 'Sana', 'Arjun', 'Isha',
    'Aditya', 'Diya', 'Karan', 'Neha', 'Rahul', 'Pooja', 'Siddharth', 'Riya', 'Aman', 'Kavya',
    'Nikhil', 'Tanvi', 'Yash', 'Shreya', 'Varun', 'Aisha', 'Dev', 'Nisha', 'Harsh', 'Zara',
    'Manish', 'Sneha', 'Ishaan', 'Anjali', 'Farhan', 'Gauri', 'Omkar', 'Ritika', 'Sahil', 'Lavanya',
    'Tejas', 'Mira', 'Kunal', 'Pallavi', 'Vivek', 'Divya', 'Aryan', 'Simran', 'Rehan', 'Bhavna',
]
LAST_NAMES = [
    'Sharma', 'Nair', 'Mehta', 'Iyer', 'Singh', 'Joshi', 'Rao', 'Khan', 'Patel', 'Desai',
    'Kulkarni', 'Gupta', 'Reddy', 'Menon', 'Shah', 'Pillai', 'Chopra', 'Bose', 'Verma', 'Fernandes',
    'Kapoor', 'Malhotra', 'Pawar', 'Gaikwad', "D'Souza", 'Banerjee', 'Shetty', 'Jain', 'Bhat', 'Thakur',
]

# Two communities per category: (name, description, place index).
COMMUNITIES = {
    Category.SPORTS: [
        ('Sunday Cricket Club', 'Tennis-ball cricket every Sunday morning at Shivaji Park. All skill levels welcome; we split teams on the spot.', 6),
        ('Andheri Football League', 'Five-a-side football on turf, Tuesday and Thursday nights. Bring shin guards.', 1),
    ],
    Category.FITNESS: [
        ('Morning Run Crew', 'Easy 5k runs along Carter Road, three mornings a week. No one gets left behind.', 0),
        ('Powai Cycling Club', 'Early-morning rides around Powai lake and weekend rides out to Aarey.', 2),
    ],
    Category.OUTDOORS: [
        ('Sahyadri Trekkers', 'Monsoon and winter treks in the Sahyadris. We share transport from Thane and plan beginner-friendly routes.', 3),
        ('Sanjay Gandhi Park Walkers', 'Nature walks, bird spotting and butterfly trails in the national park.', 8),
    ],
    Category.ADVENTURE: [
        ('Weekend Road Trippers', 'Spontaneous weekend drives out of the city: Lonavala, Alibaug, Igatpuri and beyond.', 9),
        ('Konkan Campers', 'Beach camping trips down the Konkan coast, gear shared within the group.', 19),
    ],
    Category.TECH: [
        ('Mumbai JS Meetup', 'Monthly meetups on JavaScript, Vue, React and Node. Talks, lightning demos and plenty of chai.', 2),
        ('Python & Data Mumbai', 'Pandas, Django, machine learning and everything Python. Meetups every second Saturday.', 11),
    ],
    Category.ARTS: [
        ('Sketch & Chai', 'Urban sketching around the city followed by chai and a look at everyone’s pages.', 5),
        ('Pottery Weekends', 'Hands-on pottery sessions for beginners in a small Bandra studio.', 0),
    ],
    Category.CULTURE: [
        ('Heritage Walks Mumbai', 'Guided walks through the Fort precinct, Kala Ghoda and old Bombay neighbourhoods.', 23),
        ('Theatre Lovers Mumbai', 'We watch plays together at Prithvi and NCPA, then argue about them over dinner.', 10),
    ],
    Category.MUSIC: [
        ('Open Mic Nights', 'Friendly open mics for singers, poets and comics. First-timers get the first slot.', 0),
        ('Indie Jam Sessions', 'Bring an instrument and jam with other musicians every Saturday evening.', 4),
    ],
    Category.FOOD: [
        ('Street Food Hunters', 'We eat our way through Mumbai one khau galli at a time.', 7),
        ('Home Bakers Circle', 'Sourdough, cakes and cookies. Share recipes, fails and wins.', 12),
    ],
    Category.DRINKS: [
        ('Third Wave Coffee Club', 'Cafe hopping, home brewing and cupping sessions for coffee nerds.', 11),
        ('Chai Adda', 'Tea tastings, masala chai experiments and long conversations.', 20),
    ],
    Category.GAMES: [
        ('Board Game Fridays', 'Catan, Codenames, Ticket to Ride and more, every Friday evening. Games provided.', 1),
        ('Chess in the Park', 'Casual and rapid chess games every Sunday at Joggers Park.', 0),
    ],
    Category.LEARNING: [
        ('Book Circle', 'One book a month, discussed over coffee. Fiction and non-fiction alternate.', 8),
        ('Language Exchange Mumbai', 'Practice French, German, Japanese or Spanish with native speakers.', 14),
    ],
    Category.EDUCATION: [
        ('Weekend Python Classes', 'Free beginner Python sessions run by volunteers, every Saturday afternoon.', 2),
        ('Teach for Kurla', 'Volunteers tutoring school kids in maths and English on weekends.', 13),
    ],
    Category.SOCIAL: [
        ('New in Mumbai', 'Just moved to the city? Meet other newcomers, swap tips and make friends.', 4),
        ('Navi Mumbai Hangouts', 'Movies, picnics and potlucks for people living in Navi Mumbai.', 9),
    ],
    Category.NETWORKING: [
        ('Startup Founders Breakfast', 'A small breakfast for founders and early employees to share what’s working.', 11),
        ('Women in Tech Mumbai', 'Mentorship, talks and career conversations for women in technology.', 15),
    ],
    Category.HEALTH: [
        ('Healthy Habits Club', 'Small weekly challenges for better sleep, food and screen time, with lots of encouragement.', 10),
        ('Mindful Eating Mumbai', 'Nutrition talks, meal prep ideas and healthy restaurant finds.', 17),
    ],
    Category.WELLNESS: [
        ('Sunrise Yoga Juhu', 'Free yoga on Juhu beach at sunrise. Bring a mat and water.', 10),
        ('Meditation Mondays', 'Guided meditation every Monday evening, followed by herbal tea.', 18),
    ],
    Category.OTHER: [
        ('Pet Parents Mumbai', 'Dog walks, pet-friendly cafes and advice for pet parents across the city.', 0),
        ('Plant Swap Mumbai', 'Swap cuttings, seeds and tips for balcony gardens.', 21),
    ],
}

# Post texts per category, picked at random for that category's communities.
POSTS = {
    Category.SPORTS: [
        'Match this Sunday at 7am! We need two more players for a full side.',
        'Who has a spare bat? Mine finally cracked last week.',
        'Great game today, everyone. That last over was something else!',
        'Anyone up for a practice session on Wednesday evening?',
        'Booked the turf for next month, details in the comments.',
        'Pics from today’s match. What a finish!',
    ],
    Category.FITNESS: [
        'New route idea: Carter Road to Bandstand and back is almost exactly 5k.',
        'Hit a personal best today, 26:40! Thanks for the pacing, everyone.',
        'Rest day tips? My legs are done after this week.',
        'Who’s joining the 10k on Sunday?',
        'Sunrise ride this morning, totally worth waking up at 5.',
        'What do you all eat before a long run?',
    ],
    Category.OUTDOORS: [
        'Planning Kalsubai for the first weekend of next month. Who is in?',
        'Photos from Rajmachi are up! The fireflies were unreal this year.',
        'Spotted a kingfisher on the trail today.',
        'Rain gear recommendations for the monsoon treks?',
        'Easy trail for beginners this Saturday, perfect if you’re new.',
        'The view from the top made the climb worth it.',
    ],
    Category.ADVENTURE: [
        'Konkan coast drive this Saturday, leaving at 5am. Two seats free.',
        'Tip: the old Mumbai–Pune highway is way more scenic than the expressway.',
        'Camping under the stars at the beach, best night of the year.',
        'Anyone have a spare tent for the weekend?',
        'Road trip playlist suggestions, go!',
        'Back from Igatpuri, sharing a few photos.',
    ],
    Category.TECH: [
        'Next meetup: "Vue 3 without a build step". Looking for one more lightning talk!',
        'Slides from last month’s talk are linked in the comments.',
        'What’s everyone’s favourite VS Code extension right now?',
        'Hiring? Post your openings here for the community.',
        'Hack night this Friday, bring your side projects.',
        'Our meetup venue for this month, thanks to the hosts!',
    ],
    Category.ARTS: [
        'Sketching at the Gateway of India this Saturday, 4pm.',
        'Watercolour or ink for quick street scenes? Curious what everyone prefers.',
        'Finished my first bowl on the wheel!',
        'Sharing today’s sketch, still learning perspective.',
        'Art supplies sale at Kala Ghoda this weekend.',
        'Who wants to do a portrait session next week?',
    ],
    Category.CULTURE: [
        'Fort precinct art deco walk on Sunday. Meet at Flora Fountain at 8am.',
        'Did you know Kala Ghoda is named after a statue that hasn’t been there since 1965?',
        'Tickets for this weekend’s play are going fast.',
        'Loved the museum visit today, sharing some photos.',
        'Any recommendations for Marathi theatre with subtitles?',
        'Next walk: the old mills of Lower Parel.',
    ],
    Category.MUSIC: [
        'Open mic this Friday! Sign-ups close Thursday night.',
        'Anyone want to form a little acoustic band?',
        'Jam session recording is up, we sounded great!',
        'Looking for a drummer for Saturday’s session.',
        'Best place in the city to buy a used guitar?',
        'What a night! Thanks to everyone who performed.',
    ],
    Category.FOOD: [
        'Mohammed Ali Road food walk this weekend. Come hungry!',
        'Best vada pav in the western suburbs: go. Defend your answer.',
        'My sourdough finally rose properly!',
        'Recipe swap thread: share your favourite weeknight dinner.',
        'Tried the new place in Bandra, the pav bhaji was amazing.',
        'Baked these for the potluck, recipe in comments.',
    ],
    Category.DRINKS: [
        'Cupping session at a Lower Parel roastery on Saturday. Six spots left.',
        'Switched from French press to AeroPress. Never going back.',
        'Masala chai recipe that changed my mornings, sharing below.',
        'Found a tiny cafe in Matunga with the best filter coffee.',
        'Cold brew or iced latte for this weather?',
        'Today’s pour-over, pretty happy with it.',
    ],
    Category.GAMES: [
        'This Friday: Wingspan tournament! Teaching session at 7pm.',
        'Just got Azul. Who wants to try it with me?',
        'Chess puzzle of the day, can you find mate in 3?',
        'Game night photos, what a crowd!',
        'Looking for Catan players this weekend.',
        'Who won the rapid tournament? Congrats!',
    ],
    Category.LEARNING: [
        'This month we’re reading "Sapiens". Discussion on the last Sunday.',
        'Vote for next month’s pick in the comments!',
        'Looking for a French conversation partner.',
        'Our reading corner for this month’s meetup.',
        'Finished the book in two days, couldn’t put it down.',
        'Any good podcasts for learning Spanish?',
    ],
    Category.EDUCATION: [
        'Week 3: loops and lists. Bring a laptop with Python installed.',
        'Homework solutions are in the comments, try it yourself first!',
        'We need two more volunteers for Saturday’s class.',
        'The kids aced their maths test this week!',
        'Sharing some free resources for beginners.',
        'Thanks to everyone who donated books.',
    ],
    Category.SOCIAL: [
        'Welcome drinks for newcomers next Saturday!',
        'What’s one thing you wish you knew when you moved to Mumbai?',
        'Potluck picnic this Sunday, bring a dish!',
        'Movie night: vote for what we watch.',
        'Great turnout yesterday, so many new faces.',
        'Anyone want to explore the flea market this weekend?',
    ],
    Category.NETWORKING: [
        'Breakfast this Thursday at 8:30. Topic: hiring your first five.',
        'Looking for a co-founder with ops experience. Happy to chat over coffee.',
        'Mentorship sign-ups are open for this quarter.',
        'Great talk on fundraising today, notes in the comments.',
        'Who’s going to the startup expo next week?',
        'Resume review session this Saturday, bring a printout.',
    ],
    Category.HEALTH: [
        'This week’s challenge: 8 glasses of water a day. Check in below!',
        'Swapped my evening scroll for a 20-minute walk. Sleeping so much better.',
        'Meal prep Sunday, here’s what I made.',
        'Any tips to cut down on sugar?',
        'Day 10 of the no-junk-food challenge!',
        'Healthy lunch spots near Lower Parel?',
    ],
    Category.WELLNESS: [
        'Tomorrow’s session focuses on breathing. See you at 6:15!',
        'Beach was perfect today. Thank you for the energy, everyone.',
        'Guided meditation recording from Monday is up.',
        'How do you keep a daily meditation habit?',
        'Sunrise session this morning was magical.',
        'New to yoga, which mat should I buy?',
    ],
    Category.OTHER: [
        'Dog meetup at Joggers Park on Sunday morning. Leashes on, please!',
        'Any recommendations for a good vet near Bandra?',
        'My balcony garden finally has tomatoes!',
        'Swapping money plant cuttings, who wants some?',
        'Meet the newest member of my family 🐶',
        'Pet-friendly cafes in Andheri?',
    ],
}

COMMENTS = [
    'Count me in!', 'What time does it start?', 'This sounds great, will try to make it.',
    'Can I bring a friend along?', 'Thanks for organising this!', 'Love this idea 🙌',
    'I’m new here, is this beginner friendly?', 'Missed the last one, not missing this!',
    'Great photo!', 'So cool, thanks for sharing.', 'Where is this?', 'This made my day.',
]
REPLIES = [
    'Yes, absolutely!', 'Same here, see you there.', 'Sure, the more the merrier.',
    'It’s very beginner friendly, don’t worry.', 'Agreed!', 'Haha, true.',
    'I can give you a lift if you need one.', 'Thanks!', 'I’ll DM you the details.',
]


class Command(BaseCommand):
    help = 'Add demo users, communities, posts with photos, likes and nested comments.'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=DEFAULT_USERS, help=f'How many users to add (default {DEFAULT_USERS}).')
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

        photos = self.get_photos()
        with transaction.atomic():
            communities = self.seed(options['users'], photos)
            self.join(options['join'], communities)

    def clear(self, demo_users):
        communities = Community.objects.filter(created_by__in=demo_users)
        posts = Post.objects.filter(community__in=communities) | Post.objects.filter(author__in=demo_users)
        for post in posts.exclude(image='').exclude(image=None):
            post.image.delete(save=False)
        n_communities = communities.count()
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

    # Photos

    def get_photos(self):
        """JPEG bytes for PHOTO_POOL photos: downloaded, or drawn if offline."""
        photos = []
        self.stdout.write(f'Downloading {PHOTO_POOL} photos from picsum.photos...')
        failures = 0
        for i in range(PHOTO_POOL):
            data = None
            for _ in range(3):
                data = self.download(f'https://picsum.photos/seed/circle{i}/1000/700')
                if data is not None:
                    break
            if data is None:
                failures += 1
                if failures >= 3:
                    self.stdout.write(self.style.WARNING('Could not download photos; drawing the rest instead.'))
                    break
                continue
            photos.append(data)
        self.stdout.write(f'Got {len(photos)} photos.')
        while len(photos) < PHOTO_POOL:
            photos.append(self.draw_photo(len(photos)))
        return photos

    def download(self, url):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read(5_000_000)
            # Re-encode through Pillow so only a valid JPEG is ever saved.
            image = Image.open(io.BytesIO(data)).convert('RGB')
            out = io.BytesIO()
            image.save(out, 'JPEG', quality=85)
            return out.getvalue()
        except Exception:
            return None

    def draw_photo(self, i):
        """A simple landscape: gradient sky, sun and hills."""
        rng = random.Random(i)
        w, h = 1000, 700
        hue = rng.random()
        top = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue, 0.5, 0.95))
        bottom = tuple(int(c * 255) for c in colorsys.hsv_to_rgb((hue + 0.1) % 1, 0.7, 0.75))
        image = Image.new('RGB', (w, h))
        draw = ImageDraw.Draw(image)
        for y in range(h):
            t = y / h
            draw.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
        sx, sy, r = rng.randint(150, 850), rng.randint(100, 300), rng.randint(50, 90)
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 240, 200))
        for layer in range(3):
            shade = tuple(int(c * (0.6 - layer * 0.15)) for c in bottom)
            base = 420 + layer * 90
            points = [(0, h)] + [(x, base + rng.randint(-60, 60)) for x in range(0, w + 100, 100)] + [(w, h)]
            draw.polygon(points, fill=shade)
        out = io.BytesIO()
        image.save(out, 'JPEG', quality=85)
        return out.getvalue()

    # Data

    def seed(self, n_users, photos):
        rng = random.Random(42)
        now = timezone.now()
        categories = list(COMMUNITIES)

        users = []
        taken = set()
        for i in range(n_users):
            first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
            base = f"demo_{first}_{last}".lower().replace("'", '')
            username = base
            n = 2
            while username in taken:
                username = f'{base}{n}'
                n += 1
            taken.add(username)
            label, lat, lng = rng.choice(PLACES)
            user = User(
                username=username, email=f'{username}@{DEMO_DOMAIN}', name=f'{first} {last}',
                first_name=first, last_name=last, location=label,
                # Spread people around their area a little so map pins don't overlap.
                latitude=round(lat + rng.uniform(-0.01, 0.01), 6),
                longitude=round(lng + rng.uniform(-0.01, 0.01), 6),
                interested_category=rng.sample(categories, rng.randint(2, 4)),
                avatar=rng.choice(AVATARS)[0] if rng.random() < 0.85 else '',
            )
            user.set_password(DEMO_PASSWORD)
            users.append(user)
        User.objects.bulk_create(users)
        users = list(User.objects.filter(email__endswith=f'@{DEMO_DOMAIN}'))

        communities = []
        n_posts = n_comments = n_photos = 0
        for category, entries in COMMUNITIES.items():
            for name, description, place in entries:
                label, lat, lng = PLACES[place]
                # Most people who like this category join; a few others drop in.
                members = [
                    u for u in users
                    if rng.random() < (0.55 if category in u.interested_category else 0.04)
                ]
                if len(members) < 4:
                    members += rng.sample([u for u in users if u not in members], 4 - len(members))
                creator = rng.choice(members)

                community = Community.objects.create(
                    name=name, description=description, category=category,
                    location=label, latitude=lat, longitude=lng, created_by=creator,
                    cover=rng.choice(covers_for(category))[0],
                )
                community.members.add(*members)
                communities.append(community)

                bodies = rng.sample(POSTS[category], rng.randint(4, len(POSTS[category])))
                for i, body in enumerate(bodies):
                    author = creator if i == 0 else rng.choice(members)
                    post = Post(community=community, author=author, body=body,
                                shares_count=rng.randint(0, 12))
                    if rng.random() < PHOTO_CHANCE:
                        post.image.save(f'demo_{community.pk}_{i}.jpg', ContentFile(rng.choice(photos)), save=False)
                        n_photos += 1
                    post.save()
                    created = now - timedelta(days=rng.randint(0, 30), hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
                    post.likes.add(*rng.sample(members, rng.randint(0, min(len(members), 25))))
                    n_posts += 1
                    n_comments += self.add_thread(rng, post, members, created)
                    Post.objects.filter(pk=post.pk).update(created_at=created, updated_at=created)

        n_memberships = sum(u.join_community.count() for u in users)
        self.stdout.write(self.style.SUCCESS(
            f'Added {len(users)} users, {len(communities)} communities, {n_posts} posts '
            f'({n_photos} with photos) and {n_comments} comments.\n'
            f'Each user joined {n_memberships / len(users):.1f} communities on average.\n'
            f'Sign in as any demo user (e.g. {users[0].username}) with the password "{DEMO_PASSWORD}".'
        ))
        return communities

    def add_thread(self, rng, post, members, posted_at):
        """0-4 comments, each with up to 2 replies, some replies replied to again."""
        count = 0
        at = posted_at

        def comment(body, parent=None):
            nonlocal count, at
            at = min(at + timedelta(minutes=rng.randint(5, 180)), timezone.now())
            c = Comment.objects.create(post=post, parent=parent, author=rng.choice(members), body=body)
            Comment.objects.filter(pk=c.pk).update(created_at=at)
            count += 1
            return c

        for top_body in rng.sample(COMMENTS, rng.randint(0, 4)):
            top = comment(top_body)
            for _ in range(rng.randint(0, 2)):
                reply = comment(rng.choice(REPLIES), top)
                if rng.random() < 0.4:
                    comment(rng.choice(REPLIES), reply)
        return count
