from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'movies', views.MovieViewSet, basename='movie')

urlpatterns = [
    path('', include(router.urls)),
    # Custom URL patterns for specific actions
    path('movies/featured/', views.MovieViewSet.as_view({'get': 'featured'}), name='featured-movies'),
    path('movies/trending/', views.MovieViewSet.as_view({'get': 'trending'}), name='trending-movies'),
    path('movies/top_rated/', views.MovieViewSet.as_view({'get': 'top_rated'}), name='top-rated-movies'),
    path('movies/upcoming/', views.MovieViewSet.as_view({'get': 'upcoming'}), name='upcoming-movies'),
    path('movies/search/', views.MovieViewSet.as_view({'get': 'search'}), name='search-movies'),
    # Movie detail by slug
    re_path(r'^movies/(?P<slug>[\w-]+)/$', views.MovieViewSet.as_view({'get': 'retrieve'}), name='movie-detail'),
    re_path(r'^movies/(?P<slug>[\w-]+)/cast/$', views.MovieViewSet.as_view({'get': 'cast'}), name='movie-cast'),
    re_path(r'^movies/(?P<slug>[\w-]+)/details_complete/$', views.MovieViewSet.as_view({'get': 'details_complete'}), name='movie-details-complete'),
]
