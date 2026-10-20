from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'name', 'email', 'location', 'is_staff')
    filter_horizontal = UserAdmin.filter_horizontal + ('join_community',)
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('name', 'interested_category', 'join_community', 'location', 'latitude', 'longitude', 'avatar')}),
    )
