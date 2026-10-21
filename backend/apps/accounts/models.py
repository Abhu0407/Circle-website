from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.templatetags.static import static

# The avatars a user can pick for their profile picture: drawings that ship
# with the site (frontend/avatars/<key>.svg). No avatar = their initial.
AVATARS = [
    ('person-short', 'Short hair'), ('person-long', 'Long hair'), ('person-bun', 'Bun'),
    ('person-curly', 'Curly hair'), ('person-beard', 'Beard'), ('person-hijab', 'Hijab'),
    ('person-cap', 'Cap'), ('person-glasses', 'Glasses'),
    ('animal-fox', 'Fox'), ('animal-cat', 'Cat'), ('animal-dog', 'Dog'), ('animal-panda', 'Panda'),
    ('animal-owl', 'Owl'), ('animal-bear', 'Bear'), ('animal-rabbit', 'Rabbit'), ('animal-penguin', 'Penguin'),
]


def avatar_url(key):
    return static(f'avatars/{key}.svg')


class User(AbstractUser):
    """Custom user model. Users can sign in with either username or email."""

    # `username` is inherited from AbstractUser.
    name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    # Interests: community category keys (communities.models.Category),
    # e.g. ["sports", "music"].
    interested_category = models.JSONField(default=list, blank=True)
    # The communities this user has joined.
    join_community = models.ManyToManyField(
        'communities.Community', related_name='members', blank=True,
    )
    location = models.CharField(max_length=255, blank=True)
    # Point picked on the map for `location` (empty if typed by hand).
    latitude = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    # A key from AVATARS, or blank for none.
    avatar = models.CharField(max_length=50, blank=True, choices=AVATARS)
    # When the Notifications page was last opened; newer posts and
    # communities count as new (see apps/notifications/services.py).
    notifications_seen_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username

    @property
    def profile_picture(self):
        """URL of the avatar, or None (show the initial instead)."""
        return avatar_url(self.avatar) if self.avatar else None
