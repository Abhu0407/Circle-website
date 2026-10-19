from django.urls import path

from . import views

urlpatterns = [
    # Page (Django TemplateView -> Vue component)
    path('communities/<int:pk>/', views.CommunityPageView.as_view(), name='community-detail'),

    # JSON API
    path('api/communities/', views.CommunityListCreateAPIView.as_view(), name='api-communities'),
    path('api/communities/<int:pk>/', views.CommunityDetailAPIView.as_view(), name='api-community'),
    path('api/communities/<int:pk>/join/', views.CommunityJoinAPIView.as_view(), name='api-community-join'),
]
