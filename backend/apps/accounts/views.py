from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import GoogleSignInSerializer, SignInSerializer, SignUpSerializer, UserSerializer


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


class HomePageView(LoginRequiredMixin, VuePageView):
    vue_component = 'pages/home/main.vue'
    page_title = 'Home'

    def get_page_props(self):
        return {
            'user': UserSerializer(self.request.user).data,
            'signoutApi': reverse('api-signout'),
            'signinUrl': reverse('signin'),
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
