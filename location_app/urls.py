from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/predict/', views.predict_location, name='predict_location'),
    path('api/city-search/', views.search_cities, name='search_cities'),
    path('api/world-cities/', views.world_city_points, name='world_city_points'),
    path('api/resolve-tweet/', views.resolve_tweet_url, name='resolve_tweet_url'),
]
