from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import serializers

from .models import Category, Community, cover_url, covers_for

# Members shown on the community page (the rest are just counted).
MEMBERS_PREVIEW = 12


def category_choices():
    """[{value, label}] for the category picker."""
    return [{'value': value, 'label': label} for value, label in Category.choices]


def cover_choices():
    """{category: [{value, label, url}]} for the cover picker."""
    return {
        category: [{'value': key, 'label': label, 'url': cover_url(key)} for key, label in covers_for(category)]
        for category in Category.values
    }


class CommunitySerializer(serializers.ModelSerializer):
    """`category` is the key (e.g. "sports"); show `category_label`.
    `cover` is the key of its picture (see models.COVERS); `image` is its URL."""

    category_label = serializers.CharField(source='get_category_display', read_only=True)
    cover = serializers.CharField(source='cover_key', read_only=True)
    image = serializers.CharField(source='cover_url', read_only=True)
    members_count = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = (
            'id', 'name', 'description', 'category', 'category_label', 'location', 'latitude', 'longitude',
            'cover', 'image', 'members_count', 'url',
        )

    def get_members_count(self, obj):
        return obj.members.count()

    def get_url(self, obj):
        return reverse('community-detail', args=[obj.pk])


class DiscoverCommunitySerializer(CommunitySerializer):
    """A community in the Discover list. Expects the annotations and
    `distance_km` added by CommunityListCreateAPIView."""

    members_count = serializers.IntegerField(source='members_total', read_only=True)
    is_member = serializers.BooleanField(read_only=True)
    distance_km = serializers.FloatField(read_only=True, allow_null=True)

    class Meta(CommunitySerializer.Meta):
        fields = CommunitySerializer.Meta.fields + ('is_member', 'distance_km')


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'name', 'profile_picture')


class CommunityDetailSerializer(CommunitySerializer):
    """Everything the community page shows. Also used to create a community
    (the creator joins it straight away) and to edit it.

    The category must be one of `Category` and is required when creating;
    after that it can't be changed. Everything else can be edited, including
    the `cover`, which must be one of the category's (default: its first).
    """

    category = serializers.ChoiceField(
        choices=Category.choices,
        error_messages={'required': 'Pick a category.', 'invalid_choice': 'Pick one of the listed categories.'},
    )
    cover = serializers.CharField(required=False)

    created_by = MemberSerializer(read_only=True)
    members = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()

    class Meta(CommunitySerializer.Meta):
        fields = CommunitySerializer.Meta.fields + (
            'created_by', 'created_at', 'members', 'posts_count', 'is_member', 'is_creator',
        )
        read_only_fields = ('created_at',)

    def _user(self):
        request = self.context.get('request')
        return request.user if request else None

    def get_members(self, obj):
        return MemberSerializer(obj.members.order_by('username')[:MEMBERS_PREVIEW], many=True,
                                context=self.context).data

    def get_posts_count(self, obj):
        return obj.posts.count()

    def get_is_member(self, obj):
        user = self._user()
        return bool(user and obj.members.filter(pk=user.pk).exists())

    def get_is_creator(self, obj):
        user = self._user()
        return bool(user and obj.created_by_id == user.pk)

    def validate_name(self, value):
        value = ' '.join(value.split())
        if not value:
            raise serializers.ValidationError('Give your community a name.')
        taken = Community.objects.filter(name__iexact=value)
        if self.instance is not None:
            taken = taken.exclude(pk=self.instance.pk)
        if taken.exists():
            raise serializers.ValidationError('A community with this name already exists.')
        return value

    def validate_category(self, value):
        if self.instance is not None and value != self.instance.category:
            raise serializers.ValidationError("The category can't be changed once the community is created.")
        return value

    def validate(self, attrs):
        # A map point needs both halves.
        lat, lng = attrs.get('latitude', ...), attrs.get('longitude', ...)
        if (lat is ...) != (lng is ...) or (lat is None) != (lng is None):
            raise serializers.ValidationError({'location': 'Send latitude and longitude together.'})
        category = attrs.get('category') or self.instance.category
        cover = attrs.get('cover')
        if cover is not None and cover not in [key for key, _ in covers_for(category)]:
            raise serializers.ValidationError({'cover': 'Pick one of the pictures for this category.'})
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['cover'] = instance.cover_key
        return data

    def create(self, validated_data):
        user = self._user()
        community = super().create({**validated_data, 'created_by': user})
        community.members.add(user)
        return community
