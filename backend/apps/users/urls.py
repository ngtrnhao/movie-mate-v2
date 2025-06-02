from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    ForgotPasswordView,
    ResetPasswordView,
    VerifyEmailView,
    ProfileView,
    UploadAvatarView,
    UserStatsView,
    UserReviewsView,
    UserRatingsView,
    UserFavoriteGenresView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/<int:userId>/', ProfileView.as_view(), name='profile'),
    path('profile/<int:userId>/avatar/', UploadAvatarView.as_view(), name='upload-avatar'),
    path('profile/<int:userId>/stats/', UserStatsView.as_view(), name='user-stats'),
    path('profile/<int:userId>/reviews/', UserReviewsView.as_view(), name='user-reviews'),
    path('profile/<int:userId>/ratings/', UserRatingsView.as_view(), name='user-ratings'),
    path('profile/<int:userId>/favorite-genres/', UserFavoriteGenresView.as_view(), name='user-favorite-genres'),
]
