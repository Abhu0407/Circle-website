from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views import View
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.fileserve import serve_file

from . import services
from .models import Kind, Message


def _int_param(request, name):
    value = request.query_params.get(name)
    if value in (None, ''):
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError({name: 'Must be a number.'})


class ChatListAPIView(APIView):
    """GET: your communities' chats, latest first, with `unread_count`."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(services.chat_list(request.user))


class ChatMessagesAPIView(APIView):
    """GET ?before=<id> | ?after=<id> -> {messages (oldest first), has_more}.
    POST {body} sends a text message (the page normally sends those over the
    socket); POST multipart {file, body?} sends a photo, video or file."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        return Response(services.messages_page(
            request.user, pk, before=_int_param(request, 'before'), after=_int_param(request, 'after'),
        ))

    def post(self, request, pk):
        message = services.create_message(request.user, pk, request.data.get('body'), request.FILES.get('file'))
        services.broadcast(services.community_group(pk), {'type': 'chat.message', 'message': message})
        return Response(message, status=status.HTTP_201_CREATED)


class ChatReadAPIView(APIView):
    """POST {last_id?} marks the chat read up to that message (default: all)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        last_id = services.mark_read(request.user, pk, request.data.get('last_id'))
        services.broadcast(
            services.user_group(request.user.pk), {'type': 'chat.read', 'community': pk, 'last_id': last_id},
        )
        return Response({'last_id': last_id})


class ChatFileView(View):
    """GET a message's file, only for members of its community (others get
    404, so they can't even tell it exists). Photos and videos are shown in
    the page; other files (or ?download=1) are downloaded. Videos can be
    skipped through (Range requests, see apps/fileserve.py)."""

    def get(self, request, pk):
        if not request.user.is_authenticated:
            raise Http404
        message = get_object_or_404(Message.objects.exclude(attachment=''), pk=pk)
        if not request.user.join_community.filter(pk=message.community_id).exists():
            raise Http404
        inline = message.attachment_kind in (Kind.IMAGE, Kind.VIDEO) and not request.GET.get('download')
        content_type = message.attachment_type if inline else 'application/octet-stream'
        return serve_file(request, message.attachment, content_type, message.attachment_name, inline)
