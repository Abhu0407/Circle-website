from django.urls import path

from . import views

urlpatterns = [
    path('special/', views.SpecialPageView.as_view(), name='special'),
]
