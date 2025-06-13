from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MovieViewSet

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename='movies')

urlpatterns = [
    path('', include(router.urls)),
    path('movies/popular/', MovieViewSet.as_view({'get':'get_popular_movies'}),name='popular-movies'),
    path('movies/top-rated/', MovieViewSet.as_view({'get':'get_top_rated_movies'}),name='top-rated-movies'),
    path('movies/upcoming/', MovieViewSet.as_view({'get':'get_upcoming_movies'}),name='upcoming-movies'),
]