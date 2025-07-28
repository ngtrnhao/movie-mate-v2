from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'recommendations', views.RecommendationViewSet, basename='recommendations')

app_name = 'recommendations'

urlpatterns = [
    # Include viewset URLs
    path('api/', include(router.urls)),

    # Additional standalone endpoints
    path('api/stats/', views.recommendation_stats, name='recommendation-stats'),

    # Alternative URL patterns for better API structure
    path('api/collaborative/',
         views.RecommendationViewSet.as_view({'get': 'collaborative'}),
         name='collaborative-recommendations'),

    path('api/demographic/',
         views.RecommendationViewSet.as_view({'get': 'demographic'}),
         name='demographic-recommendations'),

    path('api/hybrid/',
         views.RecommendationViewSet.as_view({'get': 'hybrid'}),
         name='hybrid-recommendations'),

    path('api/personalized/',
         views.RecommendationViewSet.as_view({'get': 'personalized'}),
         name='personalized-recommendations'),

    path('api/feedback/',
         views.RecommendationViewSet.as_view({'post': 'feedback'}),
         name='recommendation-feedback'),

    path('api/profile/',
         views.RecommendationViewSet.as_view({'get': 'user_profile'}),
         name='user-recommendation-profile'),
]
