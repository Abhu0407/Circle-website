from django.conf import settings
from django.db import models

MAX_POST_LENGTH = 5000
MAX_COMMENT_LENGTH = 2000


class Post(models.Model):
    """Something a member published in a community. The community is what
    the post is shown under; the author is tagged on it."""

    community = models.ForeignKey(
        'communities.Community', on_delete=models.CASCADE, related_name='posts',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='posts',
    )
    body = models.TextField(max_length=MAX_POST_LENGTH, blank=True)
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_posts', blank=True)
    # How many times the Share button was used.
    shares_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at', '-id')

    def __str__(self):
        return self.body[:50] or f'Post {self.pk}'


class Comment(models.Model):
    """A comment on a post, or a reply to another comment (`parent`).
    Replies can be nested to any depth."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='comments',
    )
    body = models.TextField(max_length=MAX_COMMENT_LENGTH, blank=True)
    # Deleted comments that still have replies are kept, blanked, so the
    # thread under them doesn't disappear.
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', 'id')

    def __str__(self):
        return self.body[:50] or f'Comment {self.pk}'

    def remove(self):
        """Delete this comment. One with replies is blanked instead; blanked
        comments left without any replies are then deleted too."""
        if self.replies.exists():
            self.is_deleted = True
            self.body = ''
            self.author = None
            self.save(update_fields=('is_deleted', 'body', 'author'))
            return
        parent = self.parent
        self.delete()
        while parent is not None and parent.is_deleted and not parent.replies.exists():
            grandparent = parent.parent
            parent.delete()
            parent = grandparent
