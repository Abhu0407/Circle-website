from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('community', 'author', 'body', 'created_at')
    list_filter = ('community',)
    raw_id_fields = ('author',)
