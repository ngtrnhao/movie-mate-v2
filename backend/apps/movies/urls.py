from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    MovieViewSet,
    MovieReviewViewSet
)

router = DefaultRouter()
router.register(r'movies', views.MovieViewSet, basename='movie')
router.register(r'reviews', MovieReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
    # Custom URL patterns for specific actions
    path('movies/featured/', views.MovieViewSet.as_view({'get': 'featured'}), name='featured-movies'),
    path('movies/trending/', views.MovieViewSet.as_view({'get': 'trending'}), name='trending-movies'),
    path('movies/top_rated/', views.MovieViewSet.as_view({'get': 'top_rated'}), name='top-rated-movies'),
    path('movies/upcoming/', views.MovieViewSet.as_view({'get': 'upcoming'}), name='upcoming-movies'),
    path('movies/search/', views.MovieViewSet.as_view({'get': 'search'}), name='search-movies'),

    # Movie reviews endpoints
    path('movies/<int:pk>/reviews/', views.MovieViewSet.as_view({'get': 'reviews', 'post': 'reviews'}), name='movie-reviews'),

    # Review reply endpoints
    path('reviews/<int:pk>/reply/', views.MovieReviewViewSet.as_view({'post': 'reply'}), name='review-reply'),
    path('reviews/<int:pk>/replies/', views.MovieReviewViewSet.as_view({'get': 'replies'}), name='review-replies'),

    # Spoiler detection endpoints
    path('reviews/detect_spoilers/', views.MovieReviewViewSet.as_view({'post': 'detect_spoilers'}), name='detect-spoilers'),
    path('reviews/<int:pk>/analyze_spoiler/', views.MovieReviewViewSet.as_view({'post': 'analyze_spoiler'}), name='analyze-spoiler'),
    path('reviews/spoiler_statistics/', views.MovieReviewViewSet.as_view({'get': 'spoiler_statistics'}), name='spoiler-statistics'),

    # Movie detail by slug
    re_path(r'^movies/(?P<slug>[\w-]+)/$', views.MovieViewSet.as_view({'get': 'retrieve'}), name='movie-detail'),
    re_path(r'^movies/(?P<slug>[\w-]+)/cast/$', views.MovieViewSet.as_view({'get': 'cast'}), name='movie-cast'),
    re_path(r'^movies/(?P<slug>[\w-]+)/details_complete/$', views.MovieViewSet.as_view({'get': 'details_complete'}), name='movie-details-complete'),
    re_path(r'^movies/(?P<slug>[\w-]+)/reviews/$', views.MovieViewSet.as_view({'get': 'reviews', 'post': 'reviews'}), name='movie-reviews-slug'),
]
