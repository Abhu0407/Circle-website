"""
ASGI config for config project.

Serves normal pages (HTTP) and the live chat sockets (/ws/chat/).
`runserver` uses this too, because `daphne` is in INSTALLED_APPS.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Load Django before anything that imports models.
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from apps.chat.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    # Sockets are signed in with the session cookie. The chat consumer only
    # accepts ones opened by pages on our own site (ALLOWED_HOSTS), so other
    # sites can't open one with a visitor's cookie.
    'websocket': AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
