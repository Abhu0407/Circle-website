from django.conf import settings
from django.db import models


class Community(models.Model):
    """A group people can join. Members are linked through
    `User.join_community` (reverse name: `community.members`)."""

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)
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
