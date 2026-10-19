from rest_framework import serializers

from .models import Community


class CommunitySerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = ('id', 'name', 'description', 'category', 'location', 'image', 'members_count')

    def get_members_count(self, obj):
        return obj.members.count()
