from django.contrib import admin

from .models import Community


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'location', 'member_count', 'created_at')
    search_fields = ('name', 'category', 'location')
    list_filter = ('category',)

    @admin.display(description='Members')
    def member_count(self, obj):
        return obj.members.count()
