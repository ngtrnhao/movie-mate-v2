from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'recommendations', views.RecommendationViewSet, basename='recommendation')

app_name = 'recommendations'

urlpatterns = [
    path('', include(router.urls)),
    path('analytics/', views.RecommendationAnalyticsView.as_view(), name='recommendation-analytics'),
]
