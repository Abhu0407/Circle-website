from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.communities.serializers import category_choices

from .serializers import (
    GoogleSignInSerializer, ProfileSerializer, SignInSerializer, SignUpSerializer, UserSerializer,
    username_taken,
)


# ---------------------------------------------------------------------------
# Page views: Django renders templates/base.html, which mounts a .vue file
# from the frontend/ folder.
# ---------------------------------------------------------------------------

@method_decorator(ensure_csrf_cookie, name='dispatch')
class VuePageView(TemplateView):
    """Render base.html and mount `vue_component` (a path inside frontend/).

    Whatever `get_page_props()` returns is passed to the component as props.
    """

    template_name = 'base.html'
    vue_component = None
    page_title = ''

    def get_page_props(self):
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vue_component'] = self.vue_component
        context['page_title'] = self.page_title
        context['page_props'] = self.get_page_props()
        # Changes whenever main.js or global.css is edited, so browsers fetch
        # the new copy instead of a cached one (.vue files: see main.js).
        context['asset_version'] = int(max(
            (settings.FRONTEND_DIR / name).stat().st_mtime for name in ('main.js', 'styles/global.css')
        ))
        return context


class GuestOnlyMixin:
    """Send already signed-in users to the home page."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class AuthPageView(GuestOnlyMixin, VuePageView):
    """Sign in and sign up share one page; the Vue side switches between
    them without a reload. `mode` picks which form is shown first."""

    vue_component = 'pages/auth/main.vue'
    mode = 'signin'

    @property
    def page_title(self):
        return 'Sign up' if self.mode == 'signup' else 'Sign in'

    def get_page_props(self):
        next_url = self.request.GET.get('next', '')
        if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={self.request.get_host()}):
            next_url = reverse('home')
        return {
            'mode': self.mode,
            'signinApi': reverse('api-signin'),
            'signupApi': reverse('api-signup'),
            'googleApi': reverse('api-google'),
            'googleClientId': settings.GOOGLE_CLIENT_ID,
            'signinUrl': reverse('signin'),
            'signupUrl': reverse('signup'),
            'nextUrl': next_url,
        }


# Decimal places kept when showing other people on the map (~1 km), so
# their exact address isn't shared with everyone.
MAP_PEOPLE_PRECISION = 2


def map_people(exclude, users=None):
    """Everyone else (or else in `users`) who has set a map point:
    [{id, username, lat, lng}]."""
    if users is None:
        users = get_user_model().objects.all()
    users = (
        users
        .filter(is_active=True, latitude__isnull=False, longitude__isnull=False)
        .exclude(pk=exclude.pk)
        .values('id', 'username', 'latitude', 'longitude')
    )
    return [
        {
            'id': u['id'],
            'username': u['username'],
            'lat': round(u['latitude'], MAP_PEOPLE_PRECISION),
            'lng': round(u['longitude'], MAP_PEOPLE_PRECISION),
        }
        for u in users
    ]


class AppPageView(LoginRequiredMixin, VuePageView):
    """A signed-in page. Its .vue file wraps its content in
    components/BaseLayout.vue (sidebar, header band, right panel), which
    needs the props below; subclasses add their own."""

    def get_page_props(self):
        return {
            'user': UserSerializer(self.request.user).data,
            'homeUrl': reverse('home'),
            'profileUrl': reverse('profile'),
            'signoutApi': reverse('api-signout'),
            'signinUrl': reverse('signin'),
            # Leaflet URL template, e.g. /maps/tiles/{z}/{x}/{y}.png
            'mapTileUrl': reverse('map-tile', args=[0, 0, 0]).replace('0/0/0', '{z}/{x}/{y}'),
            # Pins on the Quick Activity Map.
            'mapPeople': map_people(exclude=self.request.user),
            # [{value, label}]: community categories, also used as interests.
            'communityCategories': category_choices(),
            # Place search for location pickers.
            'mapSearchApi': reverse('api-map-search'),
            'mapReverseApi': reverse('api-map-reverse'),
        }


class HomePageView(AppPageView):
    """Discover, plus the sections still to be built. /?tab=chats opens
    on that section; the page switches sections without reloading."""

    vue_component = 'pages/home/main.vue'
    page_title = 'Home'
    tabs = ('discover', 'communities', 'chats', 'create')

    def get_page_props(self):
        tab = self.request.GET.get('tab', '')
        return {
            **super().get_page_props(),
            'tab': tab if tab in self.tabs else 'discover',
            # Posts feed on the My Communities tab.
            'postsApi': reverse('api-posts'),
            # Create Community tab.
            'communitiesApi': reverse('api-communities'),
        }


class ProfilePageView(AppPageView):
    vue_component = 'pages/profile/main.vue'
    page_title = 'Profile'

    def get_page_props(self):
        return {
            **super().get_page_props(),
            'meApi': reverse('api-me'),
            'usernameCheckApi': reverse('api-username-check'),
        }


# ---------------------------------------------------------------------------
# JSON API views called by the .vue components
# ---------------------------------------------------------------------------

class SignUpAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class SignInAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignInSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response(UserSerializer(user).data)


class GoogleSignInAPIView(APIView):
    """Sign in with Google, creating the account on first use."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleSignInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        code = status.HTTP_201_CREATED if serializer.created else status.HTTP_200_OK
        return Response(UserSerializer(user).data, status=code)


class SignOutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        """Update the profile. Accepts JSON, or multipart when a picture is sent."""
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)


class UsernameCheckAPIView(APIView):
    """GET ?username=x -> {available, message}. Your own username counts as available."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        username = request.query_params.get('username', '').strip()
        message = ''
        if not username:
            message = 'Username is required.'
        elif len(username) > 150:
            message = 'Username must be 150 characters or fewer.'
        else:
            try:
                UnicodeUsernameValidator()(username)
            except ValidationError:
                message = 'Use only letters, numbers and @ . + - _'
            else:
                if username_taken(username, exclude=request.user):
                    message = 'This username is already taken.'
        return Response({'available': not message, 'message': message})
