from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


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
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return self.username
