from django.urls import path, include
from . import views
from .api_urls import api_patterns

urlpatterns = [
    path('', views.index, name='index'),
    path('api/', include(api_patterns)),
]
