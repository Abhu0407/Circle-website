from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import serializers

from apps.communities.models import Community
from apps.communities.serializers import DiscoverCommunitySerializer

from .models import Comment, Post

User = get_user_model()

MAX_POST_IMAGE_SIZE = 5 * 1024 * 1024


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'name', 'profile_picture')


class PostCommunitySerializer(serializers.ModelSerializer):
    image = serializers.CharField(source='cover_url', read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = ('id', 'name', 'category', 'image', 'url')

    def get_url(self, obj):
        return reverse('community-detail', args=[obj.pk])


class PostSerializer(serializers.ModelSerializer):
    """A post with its community, tagged author and counts.

    `likes_count`, `comments_count` and `liked` come from the annotations
    added by views.posts_for(). Posting needs `community_id` of a community
    the user has joined; it can't be changed afterwards.
    """

    community = PostCommunitySerializer(read_only=True)
    community_id = serializers.PrimaryKeyRelatedField(
        source='community', queryset=Community.objects.all(), write_only=True,
    )
    author = AuthorSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True, default=0)
    comments_count = serializers.IntegerField(read_only=True, default=0)
    liked = serializers.BooleanField(read_only=True, default=False)
    is_author = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    remove_image = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Post
        fields = (
            'id', 'community', 'community_id', 'author', 'body', 'image', 'remove_image',
            'likes_count', 'comments_count', 'shares_count', 'liked', 'is_author', 'url',
            'created_at', 'updated_at',
        )
        read_only_fields = ('shares_count', 'created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['community_id'].required = False

    def get_is_author(self, obj):
        request = self.context.get('request')
        return bool(request and obj.author_id == request.user.pk)

    def get_url(self, obj):
        return reverse('post-detail', args=[obj.pk])

    def validate_body(self, value):
        return value.strip()

    def validate_image(self, value):
        if value and value.size > MAX_POST_IMAGE_SIZE:
            raise serializers.ValidationError('Photo must be 5 MB or smaller.')
        return value

    def validate(self, attrs):
        if self.instance is None:
            user = self.context['request'].user
            if not user.join_community.filter(pk=attrs['community'].pk).exists():
                raise serializers.ValidationError(
                    {'community_id': 'Only members of this community can post in it.'},
                )
        else:
            attrs.pop('community', None)

        body = attrs.get('body', self.instance.body if self.instance else '')
        has_image = attrs.get('image') or (
            self.instance is not None and self.instance.image and not attrs.get('remove_image')
        )
        if not body and not has_image:
            raise serializers.ValidationError({'body': 'Write something or add a photo.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('remove_image', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        remove = validated_data.pop('remove_image', False)
        new_image = validated_data.get('image')
        if (remove or new_image) and instance.image:
            instance.image.delete(save=False)
        if remove and not new_image:
            validated_data['image'] = None
        return super().update(instance, validated_data)


class SuggestedCommunitySerializer(DiscoverCommunitySerializer):
    """A community suggested on For You (see feed.suggested_communities),
    with `reason`: a short "why this one"."""

    reason = serializers.CharField(read_only=True)

    class Meta(DiscoverCommunitySerializer.Meta):
        fields = DiscoverCommunitySerializer.Meta.fields + ('reason',)


class CommentSerializer(serializers.ModelSerializer):
    """Writes a comment. `parent` (optional) is the comment being replied to,
    which must be on the same post (passed in context as `post`)."""

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), required=False, allow_null=True,
    )

    class Meta:
        model = Comment
        fields = ('body', 'parent')

    def validate_body(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Write a comment first.')
        return value

    def validate_parent(self, value):
        if value is not None:
            if value.post_id != self.context['post'].pk:
                raise serializers.ValidationError('That comment is on a different post.')
            if value.is_deleted:
                raise serializers.ValidationError('You can’t reply to a deleted comment.')
        return value


def comment_node(comment, user):
    """One comment as the frontend shows it, with an empty `replies` list."""
    deleted = comment.is_deleted
    return {
        'id': comment.pk,
        'parent': comment.parent_id,
        'body': '' if deleted else comment.body,
        'author': AuthorSerializer(comment.author).data if comment.author and not deleted else None,
        'is_deleted': deleted,
        'is_author': not deleted and comment.author_id == user.pk,
        'created_at': serializers.DateTimeField().to_representation(comment.created_at),
        'replies': [],
    }


def comment_tree(post, user):
    """All comments on `post` as a nested list: top-level comments, each
    with its `replies`, oldest first. Uses one query."""
    nodes, roots = {}, []
    for comment in post.comments.select_related('author'):
        nodes[comment.pk] = comment_node(comment, user)
    for node in nodes.values():
        parent = nodes.get(node['parent'])
        (parent['replies'] if parent else roots).append(node)
    return roots
