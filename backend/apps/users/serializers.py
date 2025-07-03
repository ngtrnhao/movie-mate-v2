from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import User, Watchlist,WatchlistItem, UserFavoriteGenre, PasswordResetToken, UserFavoriteMovie
# MovieSerializer import moved to lazy imports to avoid circular dependency
from django.conf import settings
import requests
from apps.movies.serializers import MovieSerializer

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            'required': 'Email is required',
            'invalid': 'Please enter a valid email address',
            'blank': 'Email cannot be blank'
        }
    )
    password = serializers.CharField(
        write_only=True,
        error_messages={
            'required': 'Password is required',
            'blank': 'Password cannot be blank'
        }
    )

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No account found with this email address.")
        return value

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            'required': 'Email is required',
            'invalid': 'Please enter a valid email address',
            'blank': 'Email cannot be blank'
        }
    )

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # Don't raise error here to prevent email enumeration
            pass
        return value

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        error_messages={
            'required': 'Password is required',
            'blank': 'Password cannot be blank',
            'invalid': 'Please enter a valid password'
        }
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            'required': 'Please confirm your password',
            'blank': 'Please confirm your password'
        }
    )

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match.",
                "password2": "Password fields didn't match."
            })
        return attrs

    def validate_token(self, value):
        try:
            token = PasswordResetToken.objects.get(token=value)
            if not token.is_valid():
                raise serializers.ValidationError("Password reset link has expired. Please request a new one.")
            return value
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid password reset link.")

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model, used for general user data responses.
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'avatar_url', 'bio', 'age', 'gender',
            'location', 'is_email_verified', 'created_at', 'updated_at', 'user_type',
        ]

class UserProfileSerializer(serializers.ModelSerializer):
    subscription_start_date = serializers.SerializerMethodField()
    subscription_end_date = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'avatar_url', 'bio', 'age', 'gender',
            'location', 'is_email_verified', 'created_at', 'updated_at', 'user_type',
            'subscription_start_date', 'subscription_end_date'
        ]
        read_only_fields = ['email', 'is_email_verified', 'created_at', 'updated_at', 'user_type', 'subscription_start_date', 'subscription_end_date']

    def get_subscription_start_date(self, obj):
        """Get the latest subscription start date from PaymentTransaction"""
        from apps.subscriptions.models import PaymentTransaction
        from django.utils import timezone

        latest_transaction = PaymentTransaction.objects.filter(
            user=obj,
            status='COMPLETED',
            end_date__gte=timezone.now()
        ).order_by('-end_date').first()

        return latest_transaction.start_date if latest_transaction else None

    def get_subscription_end_date(self, obj):
        """Get the latest subscription end date from PaymentTransaction"""
        from apps.subscriptions.models import PaymentTransaction
        from django.utils import timezone

        latest_transaction = PaymentTransaction.objects.filter(
            user=obj,
            status='COMPLETED',
            end_date__gte=timezone.now()
        ).order_by('-end_date').first()

        return latest_transaction.end_date if latest_transaction else None

class UserStatsSerializer(serializers.Serializer):
    # Basic counts
    # watched_movies_count = serializers.IntegerField()
    reviews_count = serializers.IntegerField()
    ratings_count = serializers.IntegerField()
    favorites_count = serializers.IntegerField()
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()

    # Rating statistics
    average_rating = serializers.FloatField()
    total_ratings = serializers.IntegerField()
    highest_rating = serializers.FloatField()
    lowest_rating = serializers.FloatField()

    # Activity statistics
    streak_days = serializers.IntegerField()
    days_since_last_activity = serializers.IntegerField()
    total_watch_time = serializers.IntegerField()  # in minutes

    # Rating distribution
    rating_distribution = serializers.DictField()

    # Recent activity
    reviews_this_week = serializers.IntegerField()
    reviews_this_month = serializers.IntegerField()
    ratings_this_week = serializers.IntegerField()
    ratings_this_month = serializers.IntegerField()

    # Community stats
    helpful_votes_received = serializers.IntegerField()
    total_votes_received = serializers.IntegerField()
    helpfulness_ratio = serializers.FloatField()

# UserRatingSerializer has been deprecated
# Use movies.serializers.UnifiedMovieReviewSerializer with review_type='USER' instead

class UserFavoriteGenreSerializer(serializers.ModelSerializer):
    genre_name = serializers.CharField(source='genre.name')

    class Meta:
        model = UserFavoriteGenre
        fields = ['id', 'genre_name']

class UserFavoriteMovieSerializer(serializers.ModelSerializer):
    # Read-only fields for response
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    movie_poster = serializers.CharField(source='movie.poster_url', read_only=True)
    movie_id = serializers.IntegerField(source='movie.id', read_only=True)

    # Simple integer field for creation (accepts movie ID)
    movie = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = UserFavoriteMovie
        fields = ['id', 'movie', 'movie_id', 'movie_title', 'movie_poster', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        # Get movie ID from validated data
        movie_id = validated_data.pop('movie', None)
        if movie_id is None:
            raise serializers.ValidationError({'movie': 'This field is required.'})

        # Import Movie model here to avoid circular imports
        from apps.movies.models import Movie

        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            raise serializers.ValidationError({'movie': f'Movie with id {movie_id} does not exist.'})

        # Set user from context and movie object
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['movie'] = movie

        return super().create(validated_data)

class GoogleAuthSerializer(serializers.Serializer):
    access_token = serializers.CharField()

    def validate(self, data):
        access_token = data.get('access_token')

        # Verify the token with Google
        response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if response.status_code != 200:
            raise serializers.ValidationError('Invalid Google token')

        user_data = response.json()

        # Get or create user
        try:
            user = User.objects.get(email=user_data['email'])
            # Update existing user if needed
            if not user.is_google_account:
                user.is_google_account = True
            if not user.is_email_verified:
                user.is_email_verified = True
            user.save()
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username=user_data['email'].split('@')[0],
                email=user_data['email'],
                first_name=user_data.get('given_name', ''),
                last_name=user_data.get('family_name', ''),
                avatar_url=user_data.get('picture', ''),
                is_google_account=True,
                is_email_verified=True
            )

        return {
            'user': user,
            'access_token': access_token
        }

class UserWatchlistItemSerializer(serializers.ModelSerializer):
    movie_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = WatchlistItem
        fields = ['id', 'watchlist', 'movie', 'status', 'created_at', 'updated_at', 'movie_data']

    def get_movie_data(self, obj):
        return MovieSerializer(obj.movie).data

class UserWatchlistSerializer(serializers.ModelSerializer):
    items = UserWatchlistItemSerializer(many=True, read_only=True)
    class Meta:
        model = Watchlist
        fields = ['id', 'name', 'created_at', 'updated_at', 'items']
