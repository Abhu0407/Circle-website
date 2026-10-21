from django.urls import path

from . import views

urlpatterns = [
    # Pages (Django TemplateView -> Vue component)
    path('discover/', views.DiscoverPageView.as_view(), name='discover'),
    path('communities/', views.MyCommunitiesPageView.as_view(), name='my-communities'),
    path('create/', views.CreateCommunityPageView.as_view(), name='create-community'),
    path('communities/<int:pk>/', views.CommunityPageView.as_view(), name='community-detail'),

    # JSON API
    path('api/communities/', views.CommunityListCreateAPIView.as_view(), name='api-communities'),
    path('api/communities/<int:pk>/', views.CommunityDetailAPIView.as_view(), name='api-community'),
    path('api/communities/<int:pk>/join/', views.CommunityJoinAPIView.as_view(), name='api-community-join'),
]
