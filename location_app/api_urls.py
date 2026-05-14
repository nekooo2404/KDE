from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

# API routes with CSRF exemption
api_patterns = [
    path('predict', csrf_exempt(views.predict_location), name='api_predict_location'),
    path('predict/', csrf_exempt(views.predict_location), name='api_predict_location_slash'),
    path('predict-batch', csrf_exempt(views.predict_location_batch), name='api_predict_location_batch'),
    path('predict-batch/', csrf_exempt(views.predict_location_batch), name='api_predict_location_batch_slash'),
    path('extract-keywords', csrf_exempt(views.extract_keywords_view), name='api_extract_keywords'),
    path('extract-keywords/', csrf_exempt(views.extract_keywords_view), name='api_extract_keywords_slash'),
    path('city-search', csrf_exempt(views.search_cities), name='api_search_cities'),
    path('city-search/', csrf_exempt(views.search_cities), name='api_search_cities_slash'),
    path('world-cities', csrf_exempt(views.world_city_points), name='api_world_city_points'),
    path('world-cities/', csrf_exempt(views.world_city_points), name='api_world_city_points_slash'),
    path('resolve-tweet', csrf_exempt(views.resolve_tweet_url), name='api_resolve_tweet'),
    path('resolve-tweet/', csrf_exempt(views.resolve_tweet_url), name='api_resolve_tweet_slash'),
]
