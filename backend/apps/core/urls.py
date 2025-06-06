from django.urls import path
from .views import RunMigrationsView

urlpatterns = [
    path('run-migrations/', RunMigrationsView.as_view(), name='run-migrations'),
]
