from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('apps.users.urls')),
    path('', include('apps.core.urls')),
    path('', include('apps.movies.urls')),
]
