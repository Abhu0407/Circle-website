from django.urls import path

from . import views

urlpatterns = [
    path('maps/tiles/<int:z>/<int:x>/<int:y>.png', views.tile, name='map-tile'),
    path('api/maps/search/', views.search, name='api-map-search'),
    path('api/maps/reverse/', views.reverse, name='api-map-reverse'),
]
