from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    MovieViewSet,
    MovieReviewViewSet,
    ReviewReportViewSet,
    ModerationConfigViewSet,
    ModerationFeedbackViewSet,
    AdminMovieViewSet
)

router = DefaultRouter()
router.register(r'movies', views.MovieViewSet, basename='movie')
router.register(r'reviews', MovieReviewViewSet, basename='review')
router.register(r'review-reports', ReviewReportViewSet, basename='review-report')

router.register(r'moderation-config', ModerationConfigViewSet, basename='moderation-config')
router.register(r'moderation-feedback', ModerationFeedbackViewSet, basename='moderation-feedback')

# Admin-only endpoints
router.register(r'admin/movies', AdminMovieViewSet, basename='admin-movie')

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

    # OPTIMIZED Spoiler detection endpoints
    path('reviews/spoiler_statistics_optimized/', views.MovieReviewViewSet.as_view({'get': 'spoiler_statistics_optimized'}), name='spoiler-statistics-optimized'),

    # Moderation endpoints
    path('reviews/moderation_stats/', views.MovieReviewViewSet.as_view({'get': 'moderation_stats'}), name='moderation-stats'),
    path('reviews/moderation_queue/', views.MovieReviewViewSet.as_view({'get': 'moderation_queue'}), name='moderation-queue'),
    
    # OPTIMIZED Moderation endpoints
    path('reviews/moderation_queue_optimized/', views.MovieReviewViewSet.as_view({'get': 'moderation_queue_optimized'}), name='moderation-queue-optimized'),

    path('reviews/unified_moderation_queue/', views.MovieReviewViewSet.as_view({'get': 'unified_moderation_queue'}), name='unified-moderation-queue'),
    path('reviews/<int:pk>/moderate/', views.MovieReviewViewSet.as_view({'post': 'moderate'}), name='moderate-review'),
    path('reviews/bulk_moderate/', views.MovieReviewViewSet.as_view({'post': 'bulk_moderate'}), name='bulk-moderate'),
    path('reviews/update_task_status/', views.MovieReviewViewSet.as_view({'post': 'update_task_status'}), name='update-task-status'),

    # Enhanced moderation endpoints
    path('reviews/auto_marked_reviews/', views.MovieReviewViewSet.as_view({'get': 'auto_marked_reviews'}), name='auto-marked-reviews'),
    path('reviews/<int:pk>/submit_feedback/', views.MovieReviewViewSet.as_view({'post': 'submit_feedback'}), name='submit-feedback'),
    path('reviews/moderation_analytics/', views.MovieReviewViewSet.as_view({'get': 'moderation_analytics'}), name='moderation-analytics'),

    # Movie detail by slug
    re_path(r'^movies/(?P<slug>[\w-]+)/$', views.MovieViewSet.as_view({'get': 'retrieve'}), name='movie-detail'),
    re_path(r'^movies/(?P<slug>[\w-]+)/cast/$', views.MovieViewSet.as_view({'get': 'cast'}), name='movie-cast'),
    re_path(r'^movies/(?P<slug>[\w-]+)/details_complete/$', views.MovieViewSet.as_view({'get': 'details_complete'}), name='movie-details-complete'),
    re_path(r'^movies/(?P<slug>[\w-]+)/reviews/$', views.MovieViewSet.as_view({'get': 'reviews', 'post': 'reviews'}), name='movie-reviews-slug'),

    # Testing endpoints for calculated metrics
    path('test/calculation-metrics/', views.test_calculation_metrics, name='test_calculation_metrics'),
    path('test/calculate-sample/', views.calculate_sample_metrics, name='calculate_sample_metrics'),
]
