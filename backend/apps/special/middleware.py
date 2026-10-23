import re

from django.shortcuts import redirect
from django.urls import reverse

from .services import SESSION_KEY

# Requests that are not pages: let them through untouched.
SKIP = re.compile(r'^/(api|static|media|admin|maps|ws)\b')


class ShowSpecialPageMiddleware:
    """After the special person signs in, the next page they open is the
    special page (whatever page the sign in form was going to)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method == 'GET'
            and request.session.get(SESSION_KEY)
            and not SKIP.match(request.path)
            and request.path != reverse('special')
        ):
            return redirect('special')
        return self.get_response(request)
