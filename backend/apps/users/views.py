from django.shortcuts import render
from rest_framework import status, generics, serializers, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
from .models import User, EmailVerificationToken, Watchlist, UserFavoriteGenre, PasswordResetToken, UserFavoriteMovie
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
    GoogleAuthSerializer
)
from .services import send_verification_email, send_password_reset_email
from rest_framework.views import APIView
import logging
from rest_framework.pagination import PageNumberPagination

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
                    return Response(
                        {
                            "error": "Google account",
                            "message": "This is a Google account. Please use Google login.",
                            "code": "google_account"
                        },
                        status=status.HTTP_401_UNAUTHORIZED
                    )

            if not user.is_email_verified:
                return Response(
                    {
                        "error": "Email not verified",
                        "message": "Please verify your email before logging in.",
                        "code": "email_not_verified"
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if not user.check_password(serializer.validated_data['password']):
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
            watched_movies_count = Watchlist.objects.filter(user=user, status='WATCHED').count()
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
            total_watch_time = self.calculate_total_watch_time(user)

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
                'total_watch_time': total_watch_time,
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

    def calculate_total_watch_time(self, user):
        """Calculate total watch time based on watched movies runtime"""
        from apps.movies.models import Movie

        # Get watched movies with runtime
        watched_movies = Movie.objects.filter(
            watchlist__user=user,
            watchlist__status='WATCHED',
            runtime__isnull=False
        ).values_list('runtime', flat=True)

        # Sum up runtime (convert to minutes if needed)
        total_minutes = sum(watched_movies)
        return total_minutes

class UserReviewsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from apps.movies.models import MovieReview
        user_id = self.kwargs.get('userId')
        return MovieReview.objects.filter(
            user_id=user_id,
            review_type='USER'
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
        return MovieReview.objects.filter(
            user_id=user_id,
            review_type='USER'
        ).select_related(
            'user',
            'movie'
        ).prefetch_related(
            'movie__genres',
            'movie__cast'
        ).order_by('-created_at')

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
class UserWatchlistItemViewSet(viewsets.ModelViewSet):
    serializer_class = UserWatchlistItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserWatchlistItemViewSet.objects.filter(watchlist__user=self.request.user)

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
