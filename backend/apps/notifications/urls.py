from django.urls import path

from . import views

urlpatterns = [
    # Page (Django TemplateView -> Vue component)
    path('notifications/', views.NotificationsPageView.as_view(), name='notifications'),

    # JSON API
    path('api/notifications/', views.NotificationsAPIView.as_view(), name='api-notifications'),
]
