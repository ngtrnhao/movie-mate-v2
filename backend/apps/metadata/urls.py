from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GenreViewSet

# Tạo router
router = DefaultRouter()
router.register('metadata/categories', GenreViewSet, basename='category')

# Định nghĩa urlpatterns
urlpatterns = [
    path('', include(router.urls)),
]
