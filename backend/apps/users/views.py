from django.shortcuts import render
import requests
from rest_framework import status, generics, serializers, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
from .models import User, EmailVerificationToken, Watchlist, UserFavoriteGenre, PasswordResetToken, UserFavoriteMovie, WatchlistItem
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserStatsSerializer,
    UserWatchlistSerializer,
    UserWatchlistItemSerializer,
    UserFavoriteGenreSerializer,
    UserFavoriteMovieSerializer,
    GoogleAuthSerializer,
    ProfileUpdateSerializer,
    LocationDetectionSerializer,
    ProfileChoicesSerializer

)
from .services import send_verification_email, send_password_reset_email
from rest_framework.views import APIView
import logging
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.users.permissions import IsAdmin, IsModerator, IsModeratorOrAdmin, is_admin, is_moderator
from apps.movies.models import MovieReview, Movie
from apps.users.models import  SearchHistory
from apps.movies.serializers import MovieReviewSerializer
from django.db import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg, Q
from apps.movies.models import Movie, ProductionMetrics
from apps.movies.services.user_data_collection_service import UserDataCollectionService
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class RegisterView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email
        try:
            send_verification_email(user)
        except Exception as e:
            # Log the error but don't fail the registration
            print(f"Failed to send verification email: {e}")

        return Response({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        }, status=status.HTTP_201_CREATED)

class VerifyEmailView(generics.GenericAPIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        token = request.query_params.get('token')
        try:
            verification = EmailVerificationToken.objects.get(token=token)
            if not verification.is_valid():
                return Response(
                    {"error": "Verification link has expired."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = verification.user
            user.is_email_verified = True
            user.save()

            # Delete the used token
            verification.delete()

            return Response({
                "message": "Email verified successfully. You can now login."
            })
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"error": "Invalid verification link."},
                status=status.HTTP_400_BAD_REQUEST
            )

class LoginView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user = User.objects.get(email=serializer.validated_data['email'])
            logger.info(f"User found: {user.email}")

            # Check if user is a Google account
            if user.is_google_account:
                # If it's a Google account, check if they have set a password
                if not user.has_usable_password():
                    logger.warning(f"Google account without password: {user.email}")
                    return Response(
                        {
                            "error": "Google account",
                            "message": "This is a Google account. Please use Google login.",
                            "code": "google_account"
                        },
                        status=status.HTTP_401_UNAUTHORIZED
                    )

            # Bypass email verification for admin users
            is_admin = user.groups.filter(name='Administrators').exists() or user.is_superuser
            if not user.is_email_verified and not is_admin:
                logger.warning(f"Email not verified for user: {user.email}")
                return Response(
                    {
                        "error": "Email not verified",
                        "message": "Please verify your email before logging in.",
                        "code": "email_not_verified"
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if not user.check_password(serializer.validated_data['password']):
                logger.warning(f"Password check failed for user: {user.email}")
                return Response(
                    {
                        "error": "Invalid password",
                        "message": "The password you entered is incorrect.",
                        "code": "invalid_password"
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            logger.info(f"Password check passed for user: {user.email}")

            try:
                refresh = RefreshToken.for_user(user)
                logger.info(f"JWT token generated successfully for user: {user.email}")
            except Exception as jwt_error:
                logger.error(f"JWT token generation failed for user {user.email}: {str(jwt_error)}")
                raise jwt_error

            # Use UserSerializer to return consistent user data
            user_data = UserSerializer(user).data

            return Response({
                'user': user_data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })

        except serializers.ValidationError as e:
            logger.error(f"Validation error during login: {str(e)}")
            return Response(
                {
                    "error": "Validation error",
                    "message": e.detail,
                    "code": "validation_error"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Login failed for email {serializer.validated_data.get('email', 'unknown')}: {str(e)}")
            return Response(
                {
                    "error": "Login failed",
                    "message": "An unexpected error occurred. Please try again.",
                    "code": "server_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ForgotPasswordView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ForgotPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)

            # Send password reset email
            try:
                send_password_reset_email(user)
                return Response(
                    {
                        "message": "Password reset email has been sent.",
                        "code": "email_sent"
                    },
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {
                        "error": "Failed to send reset email",
                        "message": "An error occurred while sending the reset email. Please try again.",
                        "code": "email_send_failed"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except User.DoesNotExist:
            # Return success even if user doesn't exist for security
            return Response(
                {
                    "message": "If an account exists with this email, you will receive a password reset link.",
                    "code": "email_sent"
                },
                status=status.HTTP_200_OK
            )

class ResetPasswordView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            token = serializer.validated_data['token']
            password = serializer.validated_data['password']

            try:
                reset_token = PasswordResetToken.objects.get(token=token)
                user = reset_token.user

                # Update user's password
                user.set_password(password)
                if user.is_google_account:
                    user.is_google_account = False
                user.save()

                # Delete used token
                reset_token.delete()

                logger.info(f"Password reset successful for user {user.email}")
                return Response(
                    {
                        "message": "Password has been reset successfully.",
                        "code": "password_reset_success"
                    },
                    status=status.HTTP_200_OK
                )

            except PasswordResetToken.DoesNotExist:
                logger.warning(f"Invalid reset token attempted: {token}")
                return Response(
                    {
                        "error": "Invalid token",
                        "message": "Invalid password reset link.",
                        "code": "invalid_token"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except serializers.ValidationError as e:
            logger.warning(f"Validation error during password reset: {str(e)}")
            return Response(
                {
                    "error": "Validation error",
                    "message": e.detail,
                    "code": "validation_error"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error during password reset: {str(e)}")
            return Response(
                {
                    "error": "Reset failed",
                    "message": "An error occurred while resetting your password. Please try again.",
                    "code": "reset_failed"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('userId')
        try:
            user = User.objects.get(id=user_id)
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, *args, **kwargs):
        user_id = kwargs.get('userId')
        try:
            user = User.objects.get(id=user_id)
            if user != request.user:
                return Response(
                    {"error": "You can only update your own profile"},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class UploadAvatarView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def put(self, request, *args, **kwargs):
        user_id = kwargs.get('userId')
        try:
            user = User.objects.get(id=user_id)
            if user != request.user:
                return Response(
                    {"error": "You can only update your own avatar"},
                    status=status.HTTP_403_FORBIDDEN
                )

            if 'avatar' not in request.FILES:
                return Response(
                    {"error": "No avatar file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Handle avatar upload logic here
            # You might want to use a storage service like AWS S3
            # For now, we'll just store the URL
            user.avatar_url = request.FILES['avatar'].name
            user.save()

            serializer = self.get_serializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class UserStatsView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserStatsSerializer

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('userId')
        try:
            user = User.objects.get(id=user_id)

            # Import required models
            from apps.movies.models import MovieReview, ReviewVote
            from django.db.models import Avg, Count, Max, Min, Q
            from django.utils import timezone
            from datetime import timedelta

            # Calculate basic counts
            watched_movies_count = WatchlistItem.objects.filter(
                watchlist__user=user,
                status='WATCHED'
            ).count()
            reviews_count = MovieReview.objects.filter(user=user, review_type='USER').count()
            ratings_count = MovieReview.objects.filter(user=user, review_type='USER', rating__isnull=False).count()

            # Use UserFavoriteMovie for favorites count
            favorites_count = UserFavoriteMovie.objects.filter(user=user).count()

            # Placeholder for social features
            followers_count = 0
            following_count = 0

            # Calculate rating statistics
            user_ratings = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            )

            rating_stats = user_ratings.aggregate(
                avg_rating=Avg('rating'),
                total_ratings=Count('id'),
                highest_rating=Max('rating'),
                lowest_rating=Min('rating')
            )

            average_rating = float(rating_stats['avg_rating']) if rating_stats['avg_rating'] else 0.0
            total_ratings = rating_stats['total_ratings']
            highest_rating = float(rating_stats['highest_rating']) if rating_stats['highest_rating'] else 0.0
            lowest_rating = float(rating_stats['lowest_rating']) if rating_stats['lowest_rating'] else 0.0

            # Calculate rating distribution
            rating_distribution = {}
            for i in range(1, 6):  # 1 to 5 stars
                count = user_ratings.filter(
                    rating__gte=i,
                    rating__lt=i + 1
                ).count()
                rating_distribution[f"{i}_star"] = count

            # Calculate activity statistics
            # Streak calculation (consecutive days with activity)
            streak_days = self.calculate_streak_days(user)

            # Days since last activity
            last_activity = MovieReview.objects.filter(
                user=user,
                review_type='USER'
            ).order_by('-created_at').first()

            days_since_last_activity = 0
            if last_activity:
                days_since_last_activity = (timezone.now() - last_activity.created_at).days

            # Total watch time (estimate based on watched movies runtime)
            # total_watch_time = self.calculate_total_watch_time(user)

            # Recent activity
            week_ago = timezone.now() - timedelta(days=7)
            month_ago = timezone.now() - timedelta(days=30)

            reviews_this_week = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                created_at__gte=week_ago
            ).count()

            reviews_this_month = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                created_at__gte=month_ago
            ).count()

            ratings_this_week = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False,
                created_at__gte=week_ago
            ).count()

            ratings_this_month = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False,
                created_at__gte=month_ago
            ).count()

            # Community stats (votes received on user's reviews)
            user_reviews = MovieReview.objects.filter(user=user, review_type='USER')
            helpful_votes_received = user_reviews.aggregate(
                total=Count('votes', filter=Q(votes__vote_type='helpful'))
            )['total'] or 0

            total_votes_received = user_reviews.aggregate(
                total=Count('votes')
            )['total'] or 0

            helpfulness_ratio = 0.0
            if total_votes_received > 0:
                helpfulness_ratio = round(helpful_votes_received / total_votes_received, 2)

            stats = {
                'watched_movies_count': watched_movies_count,
                'reviews_count': reviews_count,
                'ratings_count': ratings_count,
                'favorites_count': favorites_count,
                'followers_count': followers_count,
                'following_count': following_count,
                'average_rating': average_rating,
                'total_ratings': total_ratings,
                'highest_rating': highest_rating,
                'lowest_rating': lowest_rating,
                'streak_days': streak_days,
                'days_since_last_activity': days_since_last_activity,
                # 'total_watch_time': total_w atch_time,
                'rating_distribution': rating_distribution,
                'reviews_this_week': reviews_this_week,
                'reviews_this_month': reviews_this_month,
                'ratings_this_week': ratings_this_week,
                'ratings_this_month': ratings_this_month,
                'helpful_votes_received': helpful_votes_received,
                'total_votes_received': total_votes_received,
                'helpfulness_ratio': helpfulness_ratio,
            }

            serializer = self.get_serializer(stats)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def calculate_streak_days(self, user):
        """Calculate consecutive days with activity"""
        from apps.movies.models import MovieReview
        from django.utils import timezone
        from datetime import timedelta

        # Get all user activity dates
        activity_dates = MovieReview.objects.filter(
            user=user,
            review_type='USER'
        ).values_list('created_at__date', flat=True).distinct().order_by('-created_at__date')

        if not activity_dates:
            return 0

        # Convert to list and reverse to get chronological order
        dates = list(activity_dates)[::-1]

        # Calculate streak
        streak = 0
        current_date = timezone.now().date()

        for i, activity_date in enumerate(dates):
            if i == 0:
                # Check if first activity is today or yesterday
                if activity_date == current_date or activity_date == current_date - timedelta(days=1):
                    streak = 1
                    current_date = activity_date
                else:
                    break
            else:
                # Check if consecutive
                if activity_date == current_date - timedelta(days=1):
                    streak += 1
                    current_date = activity_date
                else:
                    break

        return streak

    # def calculate_total_watch_time(self, user):
    #     """Calculate total watch time based on watched movies runtime"""
    #     from apps.movies.models import Movie

    #     # Get watched movies with runtime
    #     watched_movies = Movie.objects.filter(
    #         watchlistitem__watchlist__user=user,
    #         watchlistitem__status='WATCHED',
    #         runtime__isnull=False
    #     ).values_list('runtime', flat=True)

    #     # Sum up runtime (convert to minutes if needed)
    #     total_minutes = sum(watched_movies) if watched_movies else 0
    #     return total_minutes

class UserReviewsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from apps.movies.models import MovieReview
        user_id = self.kwargs.get('userId')
        return MovieReview.objects.filter(
            user_id=user_id,
            review_type='USER',
            parent_review__isnull=True  # Only main reviews, exclude replies
        ).select_related('user', 'movie')

    def get_serializer_class(self):
        from apps.movies.serializers import UnifiedMovieReviewSerializer
        return UnifiedMovieReviewSerializer

class UserRatingsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        from apps.movies.models import MovieReview
        user_id = self.kwargs.get('userId')
        language = self.request.query_params.get('language', 'vi')  # Default to Vietnamese

        return MovieReview.objects.filter(
            user_id=user_id,
            review_type='USER',
            parent_review__isnull=True  # Only main reviews, exclude replies
        ).select_related(
            'user',
            'movie'
        ).prefetch_related(
            'movie__genres',
            'movie__cast'
        ).order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['language'] = self.request.query_params.get('language', 'vi')
        return context

    def get_serializer_class(self):
        from apps.movies.serializers import UnifiedMovieReviewWithDetailsSerializer
        return UnifiedMovieReviewWithDetailsSerializer

class UserFavoriteGenresView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserFavoriteGenreSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('userId')
        return UserFavoriteGenre.objects.filter(user_id=user_id).select_related('genre')

class UserFavoriteMoviesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserFavoriteMovieSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('userId')
        return UserFavoriteMovie.objects.filter(user_id=user_id).select_related('movie')

class GoogleAuthView(APIView):
    permission_classes = []  # Allow unauthenticated access

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            # Use UserSerializer to return consistent user data
            user_data = UserSerializer(user).data

            return Response({
                'user': user_data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.all()

    def get_permissions(self):
        if self.action in ['create', 'list']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_object(self):
        return self.request.user

# UserRatingViewSet has been deprecated
# Use movies app API endpoints for user reviews:
# - GET/POST /api/movies/{id}/reviews/ for movie-specific reviews
# - GET /api/auth/profile/{userId}/reviews/ for user's reviews list

class UserWatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = UserWatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def movies(self, request, pk=None):
        """Add a movie to a specific watchlist"""
        watchlist = self.get_object()
        # Create a mutable copy of the data and add the watchlist
        data = request.data.copy()
        data['watchlist'] = watchlist.id

        serializer = UserWatchlistItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserWatchlistItemViewSet(viewsets.ModelViewSet):
    serializer_class = UserWatchlistItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WatchlistItem.objects.filter(watchlist__user=self.request.user)

    def perform_create(self, serializer):
        watchlist = serializer.validated_data['watchlist']
        if watchlist.user != self.request.user:
            raise PermissionDenied("You can only add items to your own watchlist")
        serializer.save()

class UserFavoriteGenreViewSet(viewsets.ModelViewSet):
    serializer_class = UserFavoriteGenreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserFavoriteGenre.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserFavoriteMovieViewSet(viewsets.ModelViewSet):
    serializer_class = UserFavoriteMovieSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserFavoriteMovie.objects.filter(user=self.request.user).select_related('movie')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CustomTokenRefreshView(TokenRefreshView):
    """Custom token refresh view with better error handling"""

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return Response(
                {
                    'error': 'Token refresh failed',
                    'message': 'Invalid or expired refresh token. Please login again.',
                    'code': 'token_refresh_failed'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

class AdminDashboardViewSet(viewsets.ViewSet):
    """
    Admin dashboard views for system management
    """
    permission_classes = [IsAdmin]

    @action(detail=False, methods=['get'])
    def system_overview(self, request):
        """Get system overview statistics"""
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)

        # User statistics
        total_users = User.objects.count()
        new_users_30d = User.objects.filter(created_at__gte=last_30_days).count()
        new_users_7d = User.objects.filter(created_at__gte=last_7_days).count()

        # Content statistics
        total_reviews = MovieReview.objects.filter(review_type='USER').count()
        new_reviews_30d = MovieReview.objects.filter(
            review_type='USER',
            created_at__gte=last_30_days
        ).count()
        new_reviews_7d = MovieReview.objects.filter(
            review_type='USER',
            created_at__gte=last_7_days
        ).count()

        # Movie statistics
        total_movies = Movie.objects.count()

        # User type distribution
        user_types = User.objects.values('user_type').annotate(
            count=Count('id')
        ).order_by('-count')

        # Group statistics
        admin_count = User.objects.filter(groups__name='Administrators').count()
        moderator_count = User.objects.filter(groups__name='Moderators').count()

        return Response({
            'users': {
                'total': total_users,
                'new_30d': new_users_30d,
                'new_7d': new_users_7d,
                'types': user_types,
                'admins': admin_count,
                'moderators': moderator_count
            },
            'content': {
                'total_reviews': total_reviews,
                'new_reviews_30d': new_reviews_30d,
                'new_reviews_7d': new_reviews_7d,
                'total_movies': total_movies
            }
        })

    @action(detail=False, methods=['get'])
    def user_analytics(self, request):
        """Get detailed user analytics"""
        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        # User growth over time
        daily_signups = User.objects.filter(
            created_at__gte=last_30_days
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # User activity - Commented out as UserActivityLog is not used
        # active_users_30d = UserActivityLog.objects.filter(
        #     created_at__gte=last_30_days
        # ).values('user').distinct().count()

        # Top users by activity - Commented out as UserActivityLog is not used
        # top_active_users = UserActivityLog.objects.filter(
        #     created_at__gte=last_30_days
        # ).values('user__username').annotate(
        #     activity_count=Count('id')
        # ).order_by('-activity_count')[:10]

        # Alternative: Use User model for basic stats
        active_users_30d = User.objects.filter(
            last_login__gte=last_30_days
        ).count()

        # Top users by login activity
        top_active_users = User.objects.filter(
            last_login__gte=last_30_days
        ).values('username').annotate(
            login_count=Count('id')
        ).order_by('-login_count')[:10]

        # Group distribution
        group_stats = User.objects.values('groups__name').annotate(
            count=Count('id')
        ).filter(groups__name__isnull=False).order_by('-count')

        return Response({
            'daily_signups': daily_signups,
            'active_users_30d': active_users_30d,
            'top_active_users': top_active_users,
            'group_stats': group_stats
        })

    @action(detail=False, methods=['get'])
    def content_analytics(self, request):
        """Get content analytics"""
        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        # Review statistics
        reviews_by_rating = MovieReview.objects.filter(
            review_type='USER'
        ).values('rating').annotate(
            count=Count('id')
        ).order_by('rating')

        # Reviews over time
        daily_reviews = MovieReview.objects.filter(
            review_type='USER',
            created_at__gte=last_30_days
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # Top reviewed movies
        top_reviewed_movies = MovieReview.objects.filter(
            review_type='USER'
        ).values('movie__title').annotate(
            review_count=Count('id')
        ).order_by('-review_count')[:10]

        # Language distribution
        language_stats = MovieReview.objects.filter(
            review_type='USER'
        ).values('language').annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'reviews_by_rating': reviews_by_rating,
            'daily_reviews': daily_reviews,
            'top_reviewed_movies': top_reviewed_movies,
            'language_stats': language_stats
        })

class ModeratorDashboardViewSet(viewsets.ViewSet):
    """
    Moderator dashboard views for content moderation
    """
    permission_classes = [IsModeratorOrAdmin]

    @action(detail=False, methods=['get'])
    def moderation_queue(self, request):
        """Get reviews pending moderation"""
        # Get recent reviews that might need attention
        recent_reviews = MovieReview.objects.filter(
            review_type='USER',
            created_at__gte=timezone.now() - timedelta(days=7)
        ).select_related('user', 'movie').order_by('-created_at')[:50]

        return Response({
            'reviews': MovieReviewSerializer(recent_reviews, many=True).data
        })

    @action(detail=False, methods=['get'])
    def reported_content(self, request):
        """Get reported content (placeholder for future implementation)"""
        # This would integrate with a reporting system
        return Response({
            'reports': [],
            'message': 'Reporting system not yet implemented'
        })

    @action(detail=False, methods=['get'])
    def moderation_stats(self, request):
        """Get moderation statistics"""
        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        # Reviews created in last 30 days
        new_reviews = MovieReview.objects.filter(
            review_type='USER',
            created_at__gte=last_30_days
        ).count()

        # Reviews with low helpfulness (potential spam)
        low_helpful_reviews = MovieReview.objects.filter(
            review_type='USER',
            total_votes__gte=5,  # At least 5 votes
            helpful_votes__lt=models.F('total_votes') * 0.3  # Less than 30% helpful
        ).count()

        # Reviews by language
        reviews_by_language = MovieReview.objects.filter(
            review_type='USER',
            created_at__gte=last_30_days
        ).values('language').annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'new_reviews_30d': new_reviews,
            'low_helpful_reviews': low_helpful_reviews,
            'reviews_by_language': reviews_by_language,
            'moderation_actions': 0  # Placeholder for future implementation
        })

    @action(detail=False, methods=['get'])
    def flagged_users(self, request):
        """
        Get users flagged for moderation attention
        Replaces mock data in UserManagement component
        """
        try:
            # Get filter parameters
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 100)
            status_filter = request.query_params.get('status', 'all')  # all, active, warning, banned
            sort_by = request.query_params.get('sort_by', 'report_count')  # report_count, last_activity

            from datetime import timedelta
            now = timezone.now()
            last_30_days = now - timedelta(days=30)

            # Get users with reports in the last 30 days
            flagged_users_query = User.objects.filter(
                review_reports__created_at__gte=last_30_days
            ).annotate(
                total_reports=Count('review_reports', distinct=True),
                total_reviews=Count('moviereview', filter=Q(moviereview__review_type='USER'), distinct=True),
                rejected_reviews=Count('moviereview', filter=Q(
                    moviereview__review_type='USER',
                    moviereview__is_approved=False
                ), distinct=True),
                last_review_date=models.Max('moviereview__created_at'),
                last_report_date=models.Max('review_reports__created_at')
            ).filter(
                total_reports__gt=0
            ).distinct()

            # Apply status filter (for now, we'll simulate this)
            if status_filter == 'warning':
                flagged_users_query = flagged_users_query.filter(total_reports__gte=3)
            elif status_filter == 'banned':
                flagged_users_query = flagged_users_query.filter(is_active=False)

            # Apply sorting
            if sort_by == 'report_count':
                flagged_users_query = flagged_users_query.order_by('-total_reports')
            else:
                flagged_users_query = flagged_users_query.order_by('-last_report_date')

            # Pagination
            start = (page - 1) * page_size
            end = start + page_size
            total_count = flagged_users_query.count()
            flagged_users = flagged_users_query[start:end]

            # Format response
            users_data = []
            for user in flagged_users:
                # Simulate warning status based on report count
                warning_status = 'none'
                if user.total_reports >= 5:
                    warning_status = 'severe'
                elif user.total_reports >= 3:
                    warning_status = 'warning'
                elif user.total_reports >= 1:
                    warning_status = 'flagged'

                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'avatar_url': user.avatar_url,
                    'join_date': user.date_joined.isoformat(),
                    'last_activity': user.last_review_date.isoformat() if user.last_review_date else None,
                    'total_reports': user.total_reports,
                    'total_reviews': user.total_reviews,
                    'rejected_reviews': user.rejected_reviews,
                    'warning_status': warning_status,
                    'is_active': user.is_active,
                    'reputation_score': max(100 - (user.total_reports * 10), 0),  # Simple calculation
                    'flags': [
                        'Multiple Reports' if user.total_reports >= 3 else None,
                        'High Rejection Rate' if user.rejected_reviews > user.total_reviews * 0.5 else None,
                        'Spam Patterns' if user.total_reports >= 5 else None
                    ]
                })

            return Response({
                'status': 'success',
                'data': {
                    'users': users_data,
                    'pagination': {
                        'current_page': page,
                        'page_size': page_size,
                        'total_count': total_count,
                        'total_pages': (total_count + page_size - 1) // page_size,
                        'has_next': end < total_count,
                        'has_previous': page > 1
                    },
                    'summary': {
                        'total_flagged': total_count,
                        'warning_users': flagged_users_query.filter(total_reports__gte=3).count(),
                        'severe_users': flagged_users_query.filter(total_reports__gte=5).count(),
                        'banned_users': flagged_users_query.filter(is_active=False).count()
                    }
                }
            })

        except Exception as e:
            logger.error(f"Error fetching flagged users: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def moderate_user(self, request, pk=None):
        """
        Take moderation action on a user (warning, temporary ban, permanent ban)
        """
        try:
            user = User.objects.get(pk=pk)
            action = request.data.get('action')  # warning, temp_ban, permanent_ban, reactivate
            reason = request.data.get('reason', '')
            duration_days = request.data.get('duration_days', 0)

            # For now, we'll simulate these actions since we don't have warning/ban fields
            # In a real implementation, you'd add these fields to the User model

            response_data = {
                'user_id': user.id,
                'action': action,
                'reason': reason,
                'moderator': request.user.username,
                'timestamp': timezone.now().isoformat()
            }

            if action == 'warning':
                # Log warning - in real implementation, save to UserWarning model
                response_data['message'] = f"Warning issued to user {user.username}"

            elif action == 'temp_ban':
                # Temporary ban - in real implementation, set ban_until field
                response_data['message'] = f"User {user.username} temporarily banned for {duration_days} days"
                response_data['ban_until'] = (timezone.now() + timedelta(days=duration_days)).isoformat()

            elif action == 'permanent_ban':
                user.is_active = False
                user.save()
                response_data['message'] = f"User {user.username} permanently banned"

            elif action == 'reactivate':
                user.is_active = True
                user.save()
                response_data['message'] = f"User {user.username} reactivated"

            return Response({
                'status': 'success',
                'data': response_data
            })

        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error moderating user {pk}: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def system_notifications(self, request):
        """
        Get system notifications for moderator dashboard
        Replaces hardcoded notifications in frontend
        """
        try:
            # Simulate notifications based on current system state
            notifications = []

            # Check for high priority issues
            from apps.movies.models import MovieReview, ReviewReport

            pending_high_priority = MovieReview.objects.filter(
                review_type='USER',
                is_approved__isnull=True,
                is_spoiler=True
            ).count()

            if pending_high_priority > 10:
                notifications.append({
                    'id': f'high_priority_{timezone.now().timestamp()}',
                    'type': 'warning',
                    'title': 'High Priority Queue Alert',
                    'message': f'{pending_high_priority} high-priority reviews pending moderation',
                    'timestamp': timezone.now().isoformat(),
                    'action_url': '/moderator/queue?priority=high',
                    'is_read': False
                })

            # Check for reports accumulation
            total_reports = ReviewReport.objects.filter(
                review__is_approved__isnull=True
            ).count()

            if total_reports > 20:
                notifications.append({
                    'id': f'reports_{timezone.now().timestamp()}',
                    'type': 'alert',
                    'title': 'Content Reports Accumulating',
                    'message': f'{total_reports} user reports need attention',
                    'timestamp': timezone.now().isoformat(),
                    'action_url': '/moderator/reports',
                    'is_read': False
                })

            # System health notification
            total_pending = MovieReview.objects.filter(
                review_type='USER',
                is_approved__isnull=True
            ).count()

            if total_pending > 100:
                notifications.append({
                    'id': f'queue_health_{timezone.now().timestamp()}',
                    'type': 'info',
                    'title': 'Queue Health Status',
                    'message': f'Moderation queue has {total_pending} pending items',
                    'timestamp': timezone.now().isoformat(),
                    'action_url': '/moderator/queue',
                    'is_read': False
                })

            # Recent auto-moderation summary
            from datetime import timedelta
            last_24h = timezone.now() - timedelta(hours=24)
            auto_marked_24h = MovieReview.objects.filter(
                auto_marked=True,
                created_at__gte=last_24h
            ).count()

            if auto_marked_24h > 0:
                notifications.append({
                    'id': f'auto_mod_{timezone.now().timestamp()}',
                    'type': 'success',
                    'title': 'Auto-Moderation Update',
                    'message': f'{auto_marked_24h} reviews auto-marked in the last 24 hours',
                    'timestamp': timezone.now().isoformat(),
                    'action_url': '/moderator/auto-marked',
                    'is_read': True
                })

            return Response({
                'status': 'success',
                'data': {
                    'notifications': notifications,
                    'unread_count': len([n for n in notifications if not n['is_read']]),
                    'last_updated': timezone.now().isoformat()
                }
            })

        except Exception as e:
            logger.error(f"Error fetching system notifications: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserUsageStatsView(generics.RetrieveAPIView):
    """Get user usage statistics and limits"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from apps.users.services.user_limits_service import UserLimitsService

        usage_stats = UserLimitsService.get_user_usage_stats(request.user)

        return Response({
            'status': 'success',
            'data': usage_stats
        }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_interactions(request):
    """
    API endpoint to receive user interactions from frontend
    ✅ Requires authentication to track user interactions
    """
    try:
        interactions = request.data.get('interactions', [])

        if not interactions:
            return Response({
                'status': 'error',
                'message': 'No interactions provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Initialize user data collection service
        user_data_service = UserDataCollectionService()

        processed_count = 0
        error_count = 0

        for interaction in interactions:
            try:
                movie_id = interaction.get('movie_id')
                action = interaction.get('action')
                user_id = interaction.get('user_id')
                session_id = interaction.get('session_id')
                metadata = interaction.get('metadata', {})

                # Validate required fields
                if not action:
                    error_count += 1
                    continue

                # Track search history if action is 'search' and user_id is present (but not for admin users)
                if action == 'search' and user_id:
                    search_query = metadata.get('search_query')
                    result_count = metadata.get('result_count', 0)
                    try:
                        user = User.objects.get(id=user_id)
                        # Không track search history cho admin users
                        if search_query and not user.is_staff and not user.is_superuser:
                            SearchHistory.objects.create(
                                user=user,
                                search_query=search_query,
                                search_results_count=result_count
                            )
                    except User.DoesNotExist:
                        logger.warning(f"User {user_id} not found for search history tracking.")

                # Some actions don't require movie_id (like search)
                if not movie_id and action not in ['search']:
                    error_count += 1
                    continue

                # Collect the interaction (but not for admin users)
                try:
                    user = User.objects.get(id=user_id)
                    # Không track user interaction cho admin users
                    if not user.is_staff and not user.is_superuser:
                        user_data_service.collect_movie_interactions(
                            movie_id=movie_id,
                            action=action,
                            user_id=user_id,
                            session_id=session_id,
                            metadata=metadata
                        )
                except User.DoesNotExist:
                    # Nếu không tìm thấy user, vẫn track interaction
                    user_data_service.collect_movie_interactions(
                        movie_id=movie_id,
                        action=action,
                        user_id=user_id,
                        session_id=session_id,
                        metadata=metadata
                    )

                processed_count += 1

            except Exception as e:
                error_count += 1
                logger.error(f"Error processing interaction: {str(e)}")
                continue

        return Response({
            'status': 'success',
            'message': f'Processed {processed_count} interactions, {error_count} errors',
            'data': {
                'processed': processed_count,
                'errors': error_count,
                'total': len(interactions)
            }
        })

    except Exception as e:
        logger.error(f"Error in user_interactions: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Error processing user interactions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_interaction_stats(request):
    """
    🔥 ENHANCED: API endpoint to get user interaction statistics from UserInteraction model
    For admin dashboard and monitoring with real data
    """
    try:
        from apps.movies.models import UserInteraction
        from apps.movies.services.user_data_collection_service import UserDataCollectionService
        from datetime import timedelta
        from django.db import models

        user_data_service = UserDataCollectionService()

        # Get time ranges
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)

        # REAL INTERACTION STATISTICS

        # Today's interactions
        today_interactions = UserInteraction.objects.filter(timestamp__gte=today_start)
        today_count = today_interactions.count()
        today_unique_users = today_interactions.filter(user__isnull=False).values('user').distinct().count()
        today_unique_sessions = today_interactions.filter(session_id__isnull=False).values('session_id').distinct().count()

        # Yesterday's interactions for comparison
        yesterday_interactions = UserInteraction.objects.filter(
            timestamp__gte=yesterday_start,
            timestamp__lt=today_start
        )
        yesterday_count = yesterday_interactions.count()

        # Last 7 days interactions
        week_interactions = UserInteraction.objects.filter(timestamp__gte=last_7_days)

        # Top actions today
        top_actions_today = today_interactions.values('action').annotate(
            count=models.Count('id')
        ).order_by('-count')[:5]

        # Top actions this week
        top_actions_week = week_interactions.values('action').annotate(
            count=models.Count('id')
        ).order_by('-count')[:10]

        # Device breakdown (today)
        device_stats = {
            'mobile': today_interactions.filter(user_agent__icontains='Mobile').count(),
            'tablet': today_interactions.filter(user_agent__icontains='Tablet').count(),
        }
        device_stats['desktop'] = today_count - device_stats['mobile'] - device_stats['tablet']

        # Hourly distribution (today)
        hourly_stats = []
        for hour in range(24):
            hour_start = today_start.replace(hour=hour)
            hour_end = hour_start + timedelta(hours=1)
            hour_count = today_interactions.filter(
                timestamp__gte=hour_start,
                timestamp__lt=hour_end
            ).count()
            hourly_stats.append({
                'hour': hour,
                'count': hour_count
            })

        # Daily trends (last 7 days)
        daily_trends = []
        for i in range(7):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            day_count = UserInteraction.objects.filter(
                timestamp__gte=day_start,
                timestamp__lt=day_end
            ).count()
            daily_trends.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'count': day_count
            })

        # Most active movies (this week)
        top_movies = week_interactions.values('movie__id', 'movie__title').annotate(
            interaction_count=models.Count('id')
        ).order_by('-interaction_count')[:10]

        # Average session duration
        avg_duration = today_interactions.filter(
            duration_seconds__isnull=False
        ).aggregate(avg_duration=models.Avg('duration_seconds'))['avg_duration'] or 0

        # Change percentage calculation
        change_percentage = 0
        if yesterday_count > 0:
            change_percentage = ((today_count - yesterday_count) / yesterday_count) * 100

        # Get overall production metrics statistics
        total_movies = Movie.objects.count()
        movies_with_production = ProductionMetrics.objects.count()

        production_stats = ProductionMetrics.objects.aggregate(
            avg_homepage_views=models.Avg('homepage_views'),
            avg_detail_views=models.Avg('detail_page_views'),
            avg_engagement=models.Avg('engagement_rate'),
            total_views=models.Count('id')
        )

        # Trending categories
        trending_distribution = ProductionMetrics.objects.values('trending_category').annotate(
            count=models.Count('id')
        ).order_by('-count')

        return Response({
            'status': 'success',
            'message': '🔥 Real user interaction statistics retrieved successfully',
            'data': {
                'overview': {
                    'total_movies': total_movies,
                    'movies_with_production': movies_with_production,
                    'production_coverage': round((movies_with_production / total_movies) * 100, 2) if total_movies > 0 else 0
                },
                'today_stats': {
                    'total_interactions': today_count,
                    'unique_users': today_unique_users,
                    'unique_sessions': today_unique_sessions,
                    'change_from_yesterday': round(change_percentage, 1),
                    'avg_session_duration': round(float(avg_duration), 2)
                },
                'recent_interactions': {
                    'today': today_count,
                    'yesterday': yesterday_count,
                    'last_7_days': week_interactions.count(),
                    'top_actions_today': list(top_actions_today),
                    'top_actions_week': list(top_actions_week)
                },
                'device_breakdown': device_stats,
                'hourly_distribution': hourly_stats,
                'daily_trends': daily_trends,
                'top_movies_this_week': [
                    {
                        'movie_id': movie['movie__id'],
                        'movie_title': movie['movie__title'],
                        'interaction_count': movie['interaction_count']
                    }
                    for movie in top_movies
                ],
                'production_stats': {
                    'avg_homepage_views': round(production_stats['avg_homepage_views'] or 0, 2),
                    'avg_detail_views': round(production_stats['avg_detail_views'] or 0, 2),
                    'avg_engagement': round(production_stats['avg_engagement'] or 0, 4),
                    'total_movies_tracked': production_stats['total_views'] or 0
                },
                'trending_distribution': list(trending_distribution)
            }
        })

    except Exception as e:
        logger.error(f"Error in enhanced user_interaction_stats: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Error getting user interaction stats: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Profile Update and Location Detection Views

class ProfileUpdateView(APIView):
    """
    API view for updating user profile information
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user profile data"""
        from .serializers import UserProfileSerializer
        serializer = UserProfileSerializer(request.user)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    def patch(self, request):
        """Update user profile"""
        from .serializers import ProfileUpdateSerializer

        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            # Check if profile was incomplete before update
            was_incomplete_before = not request.user.is_profile_complete

            updated_user = serializer.save()

            # Check if profile is now complete after update
            is_complete_after = updated_user.is_profile_complete

            # If profile just became complete, trigger recommendation generation
            if was_incomplete_before and is_complete_after:
                logger.info(f"User {updated_user.id} has complete profile - generating new recommendations")

                # Clear any existing recommendations to force regeneration
                from apps.recommendations.models import RecommendationResult
                RecommendationResult.objects.filter(
                    user=updated_user,
                    context='homepage'
                ).delete()

                # Trigger recommendation generation in background
                try:
                    from apps.recommendations.tasks import generate_user_recommendations_async
                    generate_user_recommendations_async.delay(updated_user.id, 'homepage')
                except Exception as e:
                    logger.warning(f"Failed to trigger recommendation generation for user {updated_user.id}: {str(e)}")

            # Return updated user data
            response_serializer = UserProfileSerializer(updated_user)

            return Response({
                'status': 'success',
                'message': 'Profile updated successfully',
                'data': response_serializer.data,
                'profile_completed': was_incomplete_before and is_complete_after
            })

        return Response({
            'status': 'error',
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class ProfileChoicesView(APIView):
    """
    API view for getting profile field choices
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Get all choices for profile fields"""
        from .serializers import ProfileChoicesSerializer

        # We don't need an actual object, just return choices
        serializer = ProfileChoicesSerializer({})

        return Response({
            'status': 'success',
            'data': {
                'occupation_choices': serializer.get_occupation_choices(None),
                'gender_choices': serializer.get_gender_choices(None),
                'age_group_choices': serializer.get_age_group_choices(None),
                'user_type_choices': serializer.get_user_type_choices(None),
            }
        })

class LocationDetectionView(APIView):
    """
    API view for detecting and updating user location
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Detect location from IP or coordinates"""
        from .serializers import LocationDetectionSerializer
        import requests

        serializer = LocationDetectionSerializer(data=request.data)

        if serializer.is_valid():
            location_data = serializer.validated_data

            # Try to get location from different sources
            detected_location = None

            # Method 1: Use provided coordinates
            if 'latitude' in location_data and 'longitude' in location_data:
                detected_location = self._get_location_from_coordinates(
                    location_data['latitude'],
                    location_data['longitude']
                )

            # Method 2: Use IP address
            elif 'ip_address' in location_data:
                detected_location = self._get_location_from_ip(location_data['ip_address'])

            # Method 3: Use client IP
            else:
                client_ip = self._get_client_ip(request)
                if client_ip:
                    detected_location = self._get_location_from_ip(client_ip)

            if detected_location:
                # Update user location
                user = request.user
                if detected_location.get('city') and detected_location.get('country'):
                    location_string = f"{detected_location['city']}, {detected_location['country']}"
                    user.location = location_string

                if detected_location.get('zip_code'):
                    user.zip_code = detected_location['zip_code']

                user.save()

                return Response({
                    'status': 'success',
                    'message': 'Location detected and updated successfully',
                    'data': {
                        'location': user.location,
                        'zip_code': user.zip_code,
                        'detected_data': detected_location
                    }
                })

            return Response({
                'status': 'error',
                'message': 'Could not detect location'
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'error',
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _get_location_from_ip(self, ip_address):
        """Get location data from IP address using ip-api.com (free service)"""
        try:
            # Skip local/private IPs
            if ip_address in ['127.0.0.1', '::1'] or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
                return None

            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 'success':
                    return {
                        'country': data.get('country'),
                        'region': data.get('regionName'),
                        'city': data.get('city'),
                        'zip_code': data.get('zip'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                    }
        except Exception as e:
            logger.error(f"Error getting location from IP {ip_address}: {str(e)}")

        return None

    def _get_location_from_coordinates(self, latitude, longitude):
        """Get location data from coordinates using reverse geocoding"""
        try:
            # Using OpenStreetMap Nominatim service (free, no API key required)
            url = f'https://nominatim.openstreetmap.org/reverse'
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'addressdetails': 1,
            }

            headers = {
                'User-Agent': 'MovieMate/1.0'  # Required by Nominatim
            }

            response = requests.get(url, params=params, headers=headers, timeout=5)

            if response.status_code == 200:
                data = response.json()
                address = data.get('address', {})

                return {
                    'country': address.get('country'),
                    'region': address.get('state') or address.get('region'),
                    'city': address.get('city') or address.get('town') or address.get('village'),
                    'zip_code': address.get('postcode'),
                    'latitude': latitude,
                    'longitude': longitude,
                }
        except Exception as e:
            logger.error(f"Error getting location from coordinates ({latitude}, {longitude}): {str(e)}")

        return None

class ProfileCompletionStatusView(APIView):
    """
    API view for checking profile completion status
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get profile completion status for current user"""
        user = request.user

        return Response({
            'status': 'success',
            'data': {
                'is_complete': user.is_profile_complete,
                'completion_percentage': user.profile_completion_percentage,
                'missing_fields': self._get_missing_fields(user),
                'required_fields': ['birth_date', 'gender', 'occupation'],
                'optional_fields': ['location', 'bio', 'first_name', 'last_name', 'avatar_url', 'zip_code']
            }
        })

    def _get_missing_fields(self, user):
        """Get list of missing fields"""
        missing = []

        required_fields = {
            'birth_date': user.birth_date,
            'gender': user.gender,
            'occupation': user.occupation,
        }

        optional_fields = {
            'location': user.location,
            'bio': user.bio,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'avatar_url': user.avatar_url,
            'zip_code': user.zip_code,
        }

        # Check required fields
        for field_name, field_value in required_fields.items():
            if not field_value or str(field_value).strip() == '':
                missing.append({
                    'field': field_name,
                    'type': 'required',
                    'label': field_name.replace('_', ' ').title()
                })

        # Check optional fields
        for field_name, field_value in optional_fields.items():
            if not field_value or str(field_value).strip() == '':
                missing.append({
                    'field': field_name,
                    'type': 'optional',
                    'label': field_name.replace('_', ' ').title()
                })

        return missing
