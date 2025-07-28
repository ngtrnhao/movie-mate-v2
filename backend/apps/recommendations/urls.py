from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'recommendations', views.RecommendationViewSet, basename='recommendations')

app_name = 'recommendations'

urlpatterns = [
    # Include viewset URLs
    path('', include(router.urls)),

    # Additional standalone endpoints
    path('stats/', views.recommendation_stats, name='recommendation-stats'),
    path('health/', views.system_health_check, name='system-health-check'),
    path('task-status/', views.RecommendationViewSet.as_view({'get': 'check_task_status'}), name='task-status'),

    # Alternative URL patterns for better API structure
    path('collaborative/',
         views.RecommendationViewSet.as_view({'get': 'collaborative'}),
         name='collaborative-recommendations'),

    path('demographic/',
         views.RecommendationViewSet.as_view({'get': 'demographic'}),
         name='demographic-recommendations'),

    path('hybrid/',
         views.RecommendationViewSet.as_view({'get': 'hybrid'}),
         name='hybrid-recommendations'),

    path('personalized/',
         views.RecommendationViewSet.as_view({'get': 'personalized'}),
         name='personalized-recommendations'),

    path('feedback/',
         views.RecommendationViewSet.as_view({'post': 'feedback'}),
         name='recommendation-feedback'),

    path('profile/',
         views.RecommendationViewSet.as_view({'get': 'user_profile'}),
         name='user-recommendation-profile'),
]
