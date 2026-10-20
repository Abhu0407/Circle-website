from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.templatetags.static import static


class Category(models.TextChoices):
    """The categories a community can be in. Picked when it is created and
    fixed after that."""

    SPORTS = 'sports', 'Sports'
    FITNESS = 'fitness', 'Fitness'
    OUTDOORS = 'outdoors', 'Outdoors'
    ADVENTURE = 'adventure', 'Adventure'
    TECH = 'tech', 'Technology'
    ARTS = 'arts', 'Arts'
    CULTURE = 'culture', 'Culture'
    MUSIC = 'music', 'Music'
    FOOD = 'food', 'Food'
    DRINKS = 'drinks', 'Drinks'
    GAMES = 'games', 'Games'
    LEARNING = 'learning', 'Learning'
    EDUCATION = 'education', 'Education'
    SOCIAL = 'social', 'Social'
    NETWORKING = 'networking', 'Networking'
    HEALTH = 'health', 'Health'
    WELLNESS = 'wellness', 'Wellness'
    OTHER = 'other', 'Other'


# The pictures a community can use: drawings that ship with the site
# (frontend/covers/<key>.svg), a few per category. Used as both its cover
# and its round picture. The first one of a category is the default.
COVERS = {
    Category.SPORTS: [
        ('sports-football', 'Football'), ('sports-cricket', 'Cricket'), ('sports-basketball', 'Basketball'),
        ('sports-tennis', 'Tennis'), ('sports-badminton', 'Badminton'), ('sports-running', 'Running'),
    ],
    Category.FITNESS: [('fitness-dumbbell', 'Dumbbells'), ('fitness-kettlebell', 'Kettlebell'), ('fitness-cycling', 'Cycling')],
    Category.OUTDOORS: [('outdoors-mountains', 'Mountains'), ('outdoors-forest', 'Forest'), ('outdoors-lake', 'Lake')],
    Category.ADVENTURE: [('adventure-tent', 'Camping'), ('adventure-balloon', 'Hot-air balloon'), ('adventure-compass', 'Compass')],
    Category.TECH: [('tech-code', 'Code'), ('tech-circuit', 'Circuit'), ('tech-laptop', 'Laptop')],
    Category.ARTS: [('arts-palette', 'Palette'), ('arts-brush', 'Brush strokes'), ('arts-shapes', 'Shapes')],
    Category.CULTURE: [('culture-masks', 'Theatre'), ('culture-lanterns', 'Lanterns'), ('culture-museum', 'Museum')],
    Category.MUSIC: [('music-guitar', 'Guitar'), ('music-notes', 'Notes'), ('music-vinyl', 'Vinyl')],
    Category.FOOD: [('food-pizza', 'Pizza'), ('food-noodles', 'Noodles'), ('food-cupcake', 'Cupcake')],
    Category.DRINKS: [('drinks-coffee', 'Coffee'), ('drinks-tea', 'Tea'), ('drinks-smoothie', 'Smoothie')],
    Category.GAMES: [('games-chess', 'Chess'), ('games-dice', 'Dice'), ('games-gamepad', 'Video games')],
    Category.LEARNING: [('learning-books', 'Books'), ('learning-bulb', 'Ideas'), ('learning-pencil', 'Notebook')],
    Category.EDUCATION: [('education-cap', 'Graduation'), ('education-board', 'Chalkboard'), ('education-globe', 'Globe')],
    Category.SOCIAL: [('social-chat', 'Chat'), ('social-confetti', 'Party'), ('social-people', 'People')],
    Category.NETWORKING: [('networking-nodes', 'Network'), ('networking-cards', 'Business cards'), ('networking-skyline', 'City')],
    Category.HEALTH: [('health-heart', 'Heartbeat'), ('health-firstaid', 'First aid'), ('health-apple', 'Apple')],
    Category.WELLNESS: [('wellness-lotus', 'Lotus'), ('wellness-leaves', 'Leaves'), ('wellness-moon', 'Moon')],
    Category.OTHER: [('other-circles', 'Circles'), ('other-waves', 'Waves'), ('other-stars', 'Stars')],
}


def covers_for(category):
    """[(key, label)] a community in `category` can pick from."""
    return COVERS.get(category, COVERS[Category.OTHER])


def cover_url(key):
    return static(f'covers/{key}.svg')


class Community(models.Model):
    """A group people can join. Members are linked through
    `User.join_community` (reverse name: `community.members`)."""

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, choices=Category.choices)
    location = models.CharField(max_length=255, blank=True)
    # Point picked on the map for `location` (empty if typed by hand).
    latitude = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    # A key from covers_for(category); blank means that category's default.
    cover = models.CharField(max_length=50, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_communities',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'communities'

    def __str__(self):
        return self.name

    @property
    def cover_key(self):
        keys = [key for key, _ in covers_for(self.category)]
        return self.cover if self.cover in keys else keys[0]

    @property
    def cover_url(self):
        return cover_url(self.cover_key)
