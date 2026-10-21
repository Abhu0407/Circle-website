from django.urls import path

from . import views

urlpatterns = [
    # Page (Django TemplateView -> Vue component)
    path('posts/<int:pk>/', views.PostPageView.as_view(), name='post-detail'),

    # JSON API
    path('api/feed/', views.ForYouFeedAPIView.as_view(), name='api-feed'),
    path('api/feed/communities/', views.SuggestedCommunitiesAPIView.as_view(), name='api-feed-communities'),
    path('api/posts/', views.PostListCreateAPIView.as_view(), name='api-posts'),
    path('api/posts/<int:pk>/', views.PostDetailAPIView.as_view(), name='api-post'),
    path('api/posts/<int:pk>/video/', views.PostVideoView.as_view(), name='api-post-video'),
    path('api/posts/<int:pk>/like/', views.PostLikeAPIView.as_view(), name='api-post-like'),
    path('api/posts/<int:pk>/share/', views.PostShareAPIView.as_view(), name='api-post-share'),
    path('api/posts/<int:pk>/comments/', views.CommentListCreateAPIView.as_view(), name='api-post-comments'),
    path('api/posts/<int:pk>/comments/<int:comment_pk>/', views.CommentDetailAPIView.as_view(),
         name='api-post-comment'),
]
