from django.urls import reverse
from django.utils import timezone
from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.views import AppPageView

from . import services


class NotificationsPageView(AppPageView):
    """Every post uploaded and community created by others, newest first.
    Opening the page marks them all seen (what was new stays highlighted
    on this visit)."""

    vue_component = 'pages/notifications/main.vue'
    page_title = 'Notifications'

    def get_page_props(self):
        user = self.request.user
        props = {
            **super().get_page_props(),
            'notificationsApi': reverse('api-notifications'),
            # Shown as new: created after this.
            'seenAt': services.seen_at(user).isoformat(),
            'notificationsUnread': 0,
        }
        user.notifications_seen_at = timezone.now()
        user.save(update_fields=('notifications_seen_at',))
        return props


class NotificationsAPIView(APIView):
    """GET ?kind=all|posts|communities&before=<next> -> {notifications, has_more, next}."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        kind = request.query_params.get('kind') or 'all'
        if kind not in services.KINDS:
            raise ValidationError({'kind': f'Must be one of: {", ".join(services.KINDS)}.'})
        before = request.query_params.get('before')
        if before:
            before = services.parse_cursor(before)
            if before is None:
                raise ValidationError({'before': 'Must be the `next` of the previous page.'})
        return Response(services.notifications_page(request.user, kind, before or None))
