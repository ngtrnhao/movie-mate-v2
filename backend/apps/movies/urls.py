from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MovieViewSet

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename='movies')

urlpatterns = [
    path('', include(router.urls)),
    # Custom URL patterns for specific actions
    path('movies/featured/', MovieViewSet.as_view({'get': 'featured'}), name='featured-movies'),
    path('movies/trending/', MovieViewSet.as_view({'get': 'trending'}), name='trending-movies'),
    path('movies/top_rated/', MovieViewSet.as_view({'get': 'top_rated'}), name='top-rated-movies'),
    path('movies/upcoming/', MovieViewSet.as_view({'get': 'upcoming'}), name='upcoming-movies'),
]
