from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'movies', views.MovieViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Custom URL patterns for specific actions
    path('movies/featured/', views.MovieViewSet.as_view({'get': 'featured'}), name='featured-movies'),
    path('movies/trending/', views.MovieViewSet.as_view({'get': 'trending'}), name='trending-movies'),
    path('movies/top_rated/', views.MovieViewSet.as_view({'get': 'top_rated'}), name='top-rated-movies'),
    path('movies/upcoming/', views.MovieViewSet.as_view({'get': 'upcoming'}), name='upcoming-movies'),
    path('movies/search/', views.MovieViewSet.as_view({'get': 'search'}), name='search-movies'),
]
