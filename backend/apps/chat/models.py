import os
import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.urls import reverse

MAX_MESSAGE_LENGTH = 2000


class Kind(models.TextChoices):
    """How an attachment is shown: a picture, a video player, or a download."""

    IMAGE = 'image', 'Photo'
    VIDEO = 'video', 'Video'
    FILE = 'file', 'File'


class ChatFileStorage(FileSystemStorage):
    """Chat files are NOT in MEDIA_ROOT (which anyone can open by URL): they
    live in CHAT_FILES_ROOT (read when used, so tests can move it) and are
    only sent by views.ChatFileView, to members."""

    @property
    def base_location(self):
        return settings.CHAT_FILES_ROOT

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    @property
    def base_url(self):
        return None


def chat_storage():
    return ChatFileStorage()


def chat_file_path(message, filename):
    """<community id>/<random>.<ext> in CHAT_FILES_ROOT: the original name is never used
    on disk (kept in `attachment_name` for showing and downloading)."""
    ext = Path(filename).suffix.lower()[:10]
    return f'{message.community_id}/{uuid.uuid4().hex}{ext}'


class Message(models.Model):
    """A chat message in a community: text, a file, or both. Only its
    members can read or send."""

    community = models.ForeignKey(
        'communities.Community', on_delete=models.CASCADE, related_name='messages',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='chat_messages',
    )
    body = models.TextField(max_length=MAX_MESSAGE_LENGTH, blank=True)
    attachment = models.FileField(upload_to=chat_file_path, storage=chat_storage, blank=True)
    # The name it was uploaded with, its size in bytes, and how to show it.
    attachment_name = models.CharField(max_length=255, blank=True)
    attachment_size = models.PositiveBigIntegerField(default=0)
    attachment_kind = models.CharField(max_length=10, choices=Kind.choices, blank=True)
    attachment_type = models.CharField(max_length=100, blank=True)  # MIME type it is served with
    # Photos: their size in pixels, so the chat can save room before they load.
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('id',)
        indexes = [models.Index(fields=('community', 'id'))]

    def __str__(self):
        return self.body[:50] or self.attachment_name

    @property
    def attachment_url(self):
        return reverse('api-chat-file', args=[self.pk]) if self.attachment else None


class ChatRead(models.Model):
    """How far a user has read a community's chat. Messages with a higher
    id than `last_read_id` (and not written by them) are unread."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_reads')
    community = models.ForeignKey('communities.Community', on_delete=models.CASCADE, related_name='chat_reads')
    last_read_id = models.PositiveBigIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'community'), name='unique_chat_read')]
