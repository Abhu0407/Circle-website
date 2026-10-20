from urllib.parse import urlencode

from django.db.models import Count, Exists, F, OuterRef, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.views import AppPageView

from .feed import ranked_post_ids, suggested_communities
from .models import Comment, Post
from .serializers import (
    CommentSerializer, PostSerializer, SuggestedCommunitySerializer, comment_node, comment_tree,
)


def posts_for(user):
    """Posts with the counts their cards show, and whether `user` liked each."""
    return (
        Post.objects
        .select_related('community', 'author')
        .annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', filter=Q(comments__is_deleted=False), distinct=True),
            liked=Exists(Post.likes.through.objects.filter(post=OuterRef('pk'), user=user)),
        )
    )


# ---------------------------------------------------------------------------
# Page view
# ---------------------------------------------------------------------------

class PostPageView(AppPageView):
    """One post with its comments open; this is the link the Share button gives."""

    vue_component = 'pages/post/main.vue'

    @cached_property
    def post(self):
        return get_object_or_404(posts_for(self.request.user), pk=self.kwargs['pk'])

    @property
    def page_title(self):
        return self.post.community.name

    def get_page_props(self):
        return {
            **super().get_page_props(),
            'post': PostSerializer(self.post, context={'request': self.request}).data,
            'postsApi': reverse('api-posts'),
        }


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------

class PostPagination(CursorPagination):
    page_size = 10
    ordering = ('-created_at', '-id')


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.author_id == request.user.pk


class PostListCreateAPIView(generics.ListCreateAPIView):
    """GET: newest posts from the communities you joined, or from one
    community with ?community=<id>. Paged: follow `next`.
    POST: publish in a community you are a member of (JSON, or multipart
    with an `image`)."""

    serializer_class = PostSerializer
    pagination_class = PostPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        posts = posts_for(self.request.user)
        community = self.request.query_params.get('community', '')
        if community:
            return posts.filter(community_id=community) if community.isdigit() else posts.none()
        return posts.filter(community__in=self.request.user.join_community.all())

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
        # Re-read it so the counts are included.
        data = self.get_serializer(posts_for(request.user).get(pk=post.pk)).data
        return Response(data, status=status.HTTP_201_CREATED)


class ForYouFeedAPIView(APIView):
    """GET ?seed=<text>&offset=<n> -> {results, next}: the For You feed.
    Other people's posts from every community, in a random order that
    favours the user's interests and activity (see feed.py). The same seed
    gives the same order, so pages follow on; a new seed reshuffles."""

    permission_classes = [permissions.IsAuthenticated]
    page_size = 10

    def get(self, request):
        seed = request.query_params.get('seed', '')[:64] or 'default'
        offset = request.query_params.get('offset', '')
        offset = int(offset) if offset.isdigit() else 0

        ids = ranked_post_ids(request.user, seed)
        page = ids[offset:offset + self.page_size]
        found = posts_for(request.user).in_bulk(page)
        posts = [found[pk] for pk in page if pk in found]

        next_url = None
        if offset + self.page_size < len(ids):
            next_url = request.build_absolute_uri(
                f"{reverse('api-feed')}?{urlencode({'seed': seed, 'offset': offset + self.page_size})}"
            )
        return Response({
            'results': PostSerializer(posts, many=True, context={'request': request}).data,
            'next': next_url,
        })


class SuggestedCommunitiesAPIView(APIView):
    """GET -> communities to suggest on For You: ones the user hasn't
    joined, best match first, each with a short `reason`."""

    permission_classes = [permissions.IsAuthenticated]
    limit = 16

    def get(self, request):
        communities = suggested_communities(request.user, self.limit)
        return Response(SuggestedCommunitySerializer(communities, many=True).data)


class PostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Anyone signed in can read a post; only its author can edit or delete it."""

    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return posts_for(self.request.user)

    def perform_destroy(self, instance):
        if instance.image:
            instance.image.delete(save=False)
        instance.delete()


class PostLikeAPIView(APIView):
    """POST likes the post, DELETE takes the like back -> {liked, likes_count}."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        post.likes.add(request.user)
        return Response({'liked': True, 'likes_count': post.likes.count()})

    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        post.likes.remove(request.user)
        return Response({'liked': False, 'likes_count': post.likes.count()})


class PostShareAPIView(APIView):
    """Counts a share -> {shares_count, url} (the full link to the post)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not Post.objects.filter(pk=pk).update(shares_count=F('shares_count') + 1):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'shares_count': Post.objects.values_list('shares_count', flat=True).get(pk=pk),
            'url': request.build_absolute_uri(reverse('post-detail', args=[pk])),
        })


class CommentListCreateAPIView(APIView):
    """GET: the post's comments as a nested tree (each with `replies`).
    POST {body, parent?}: comment, or reply to the comment `parent`."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        return Response(comment_tree(post, request.user))

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        serializer = CommentSerializer(data=request.data, context={'post': post})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(post=post, author=request.user)
        return Response(comment_node(comment, request.user), status=status.HTTP_201_CREATED)


class CommentDetailAPIView(APIView):
    """PATCH {body} edits, DELETE removes your own comment. A deleted comment
    that has replies stays in the tree as "deleted" so the replies remain."""

    permission_classes = [permissions.IsAuthenticated]

    def get_comment(self, request, pk, comment_pk):
        comment = get_object_or_404(Comment, pk=comment_pk, post_id=pk, is_deleted=False)
        if comment.author_id != request.user.pk:
            raise PermissionDenied('You can only change your own comments.')
        return comment

    def patch(self, request, pk, comment_pk):
        comment = self.get_comment(request, pk, comment_pk)
        serializer = CommentSerializer(comment, data={'body': request.data.get('body', '')},
                                       partial=True, context={'post': comment.post})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(comment_node(comment, request.user))

    def delete(self, request, pk, comment_pk):
        self.get_comment(request, pk, comment_pk).remove()
        return Response(status=status.HTTP_204_NO_CONTENT)
