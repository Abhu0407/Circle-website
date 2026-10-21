from django.urls import path

from . import views

urlpatterns = [
    # Page (Django TemplateView -> Vue component)
    path('chats/', views.ChatsPageView.as_view(), name='chats'),

    # JSON API
    path('api/chats/', views.ChatListAPIView.as_view(), name='api-chats'),
    path('api/chats/<int:pk>/messages/', views.ChatMessagesAPIView.as_view(), name='api-chat-messages'),
    path('api/chats/files/<int:pk>/', views.ChatFileView.as_view(), name='api-chat-file'),
    path('api/chats/<int:pk>/read/', views.ChatReadAPIView.as_view(), name='api-chat-read'),
]
