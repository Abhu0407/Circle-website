import math

from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.views import AppPageView, map_people

from .models import Category, Community
from .serializers import CommunityDetailSerializer, DiscoverCommunitySerializer

EARTH_RADIUS_KM = 6371.0


def distance_km(lat1, lng1, lat2, lng2):
    """Great-circle (haversine) distance between two points, in km."""
    lat1, lng1, lat2, lng2 = map(math.radians, (lat1, lng1, lat2, lng2))
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))

# ---------------------------------------------------------------------------
# Page view
# ---------------------------------------------------------------------------


class CommunityPageView(AppPageView):
    """A community's information, Join/Leave, and its posts."""

    vue_component = 'pages/community/main.vue'

    @cached_property
    def community(self):
        return get_object_or_404(Community.objects.select_related('created_by'), pk=self.kwargs['pk'])

    @property
    def page_title(self):
        return self.community.name

    def get_page_props(self):
        return {
            **super().get_page_props(),
            'community': CommunityDetailSerializer(self.community, context={'request': self.request}).data,
            'communityApi': reverse('api-community', args=[self.community.pk]),
            # Members' map pins (about 1 km precise), not counting you.
            'memberPoints': map_people(exclude=self.request.user, users=self.community.members.all()),
            'joinApi': reverse('api-community-join', args=[self.community.pk]),
            'postsApi': reverse('api-posts'),
        }


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------

class CommunityListCreateAPIView(generics.ListCreateAPIView):
    """GET (Discover): every community, nearest to you first, each with
    `is_member` and `distance_km` (null when you or it has no map point).
      ?q=        words found in the name, description, location or category
      ?category= a Category key; repeat it to allow several
      ?within=   km from your Profile location (needs one, else 400)
    POST: create one (JSON, or multipart with an `image`); you join it."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return CommunityDetailSerializer if self.request.method == 'POST' else DiscoverCommunitySerializer

    def get_queryset(self):
        memberships = get_user_model().join_community.through.objects
        communities = Community.objects.annotate(
            members_total=Count('members', distinct=True),
            is_member=Exists(memberships.filter(community=OuterRef('pk'), user=self.request.user)),
        )
        params = self.request.query_params
        q = params.get('q', '').strip()
        if q:
            labels = [value for value, label in Category.choices if q.lower() in label.lower()]
            communities = communities.filter(
                Q(name__icontains=q) | Q(description__icontains=q) | Q(location__icontains=q)
                | Q(category__in=labels)
            )
        categories = [c for c in params.getlist('category') if c in Category.values]
        if categories:
            communities = communities.filter(category__in=categories)
        return communities

    def list(self, request, *args, **kwargs):
        try:
            within = float(request.query_params.get('within', '') or 0)
        except ValueError:
            within = 0
        user = request.user
        here = (user.latitude, user.longitude) if user.latitude is not None and user.longitude is not None else None
        if within > 0 and here is None:
            return Response({'detail': 'Set your location on your profile to filter by distance.'},
                            status=status.HTTP_400_BAD_REQUEST)

        communities = list(self.get_queryset())
        for c in communities:
            has_point = here is not None and c.latitude is not None and c.longitude is not None
            c.distance_km = round(distance_km(*here, c.latitude, c.longitude), 1) if has_point else None
        if within > 0:
            communities = [c for c in communities if c.distance_km is not None and c.distance_km <= within]
        # Nearest first; ones without a distance after, by name.
        communities.sort(key=lambda c: (c.distance_km is None, c.distance_km or 0, c.name.lower()))
        return Response(self.get_serializer(communities, many=True).data)


class IsCreatorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.created_by_id == request.user.pk


class CommunityDetailAPIView(generics.RetrieveUpdateAPIView):
    """GET a community. PATCH (its creator only) edits name, description,
    location and image (JSON, or multipart with an `image`); not the category."""

    serializer_class = CommunityDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsCreatorOrReadOnly]
    queryset = Community.objects.select_related('created_by')
    http_method_names = ['get', 'patch', 'head', 'options']


class CommunityJoinAPIView(APIView):
    """POST joins, DELETE leaves -> {is_member, members_count}."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        community = get_object_or_404(Community, pk=pk)
        community.members.add(request.user)
        return self.state(community, True)

    def delete(self, request, pk):
        community = get_object_or_404(Community, pk=pk)
        community.members.remove(request.user)
        return self.state(community, False)

    def state(self, community, is_member):
        return Response({'is_member': is_member, 'members_count': community.members.count()},
                        status=status.HTTP_200_OK)
