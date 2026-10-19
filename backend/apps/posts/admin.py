from django.contrib import admin

from .models import Comment, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'community', 'author', 'like_count', 'shares_count', 'created_at')
    search_fields = ('body', 'community__name', 'author__username')
    list_filter = ('community',)
    raw_id_fields = ('author',)
    filter_horizontal = ('likes',)

    @admin.display(description='Likes')
    def like_count(self, obj):
        return obj.likes.count()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'post', 'author', 'parent', 'is_deleted', 'created_at')
    search_fields = ('body', 'author__username')
    list_filter = ('is_deleted',)
    raw_id_fields = ('post', 'parent', 'author')
