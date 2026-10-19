from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


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
    image = models.ImageField(upload_to='community_images/', blank=True, null=True)
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
