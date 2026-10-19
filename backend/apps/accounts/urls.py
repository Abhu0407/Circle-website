from django.urls import path

from . import views

urlpatterns = [
    # Pages (Django TemplateView -> Vue component)
    path('', views.HomePageView.as_view(), name='home'),
    path('signin/', views.AuthPageView.as_view(mode='signin'), name='signin'),
    path('signup/', views.AuthPageView.as_view(mode='signup'), name='signup'),

    # JSON API
    path('api/auth/signup/', views.SignUpAPIView.as_view(), name='api-signup'),
    path('api/auth/signin/', views.SignInAPIView.as_view(), name='api-signin'),
    path('api/auth/google/', views.GoogleSignInAPIView.as_view(), name='api-google'),
    path('api/auth/signout/', views.SignOutAPIView.as_view(), name='api-signout'),
    path('api/auth/me/', views.MeAPIView.as_view(), name='api-me'),
]
