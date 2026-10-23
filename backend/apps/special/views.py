from django.conf import settings
from django.http import Http404
from django.urls import reverse

from apps.accounts.views import VuePageView

from .services import SESSION_KEY, is_special


class SpecialPageView(VuePageView):
    """Only the SPECIAL_EMAIL account can see this page. Everyone else,
    signed in or not, gets "Page not found", as if it didn't exist."""

    vue_component = 'pages/special/main.vue'
    page_title = 'For you'

    def dispatch(self, request, *args, **kwargs):
        if not is_special(request.user):
            raise Http404
        request.session.pop(SESSION_KEY, None)
        return super().dispatch(request, *args, **kwargs)

    def get_page_props(self):
        user = self.request.user
        return {
            'name': settings.SPECIAL_NAME or user.first_name or user.username,
            'homeUrl': reverse('home'),
        }
