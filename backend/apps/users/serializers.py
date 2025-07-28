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
    groups = serializers.SerializerMethodField()
    is_profile_complete = serializers.ReadOnlyField()
    profile_completion_percentage = serializers.ReadOnlyField()
    occupation_display = serializers.CharField(source='get_occupation_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    age_group_display = serializers.CharField(source='get_age_group_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'avatar_url', 'bio',
            'birth_date', 'age', 'age_group', 'gender', 'location', 'occupation', 'zip_code',
            'is_email_verified', 'created_at', 'updated_at', 'user_type',
            'groups', 'is_profile_complete', 'profile_completion_percentage',
            'occupation_display', 'gender_display', 'age_group_display'
        ]
        read_only_fields = ['age', 'age_group', 'is_profile_complete', 'profile_completion_percentage']

    def get_groups(self, obj):
        """Get user groups for permission checking"""
        return [
            {
                'id': group.id,
                'name': group.name,
                'permissions': list(group.permissions.values_list('codename', flat=True))
            }
            for group in obj.groups.all()
        ]

class UserProfileSerializer(serializers.ModelSerializer):
    subscription_start_date = serializers.SerializerMethodField()
    subscription_end_date = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    is_profile_complete = serializers.ReadOnlyField()
    profile_completion_percentage = serializers.ReadOnlyField()
    occupation_display = serializers.CharField(source='get_occupation_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    age_group_display = serializers.CharField(source='get_age_group_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'avatar_url', 'bio',
            'birth_date', 'age', 'age_group', 'gender', 'location', 'occupation', 'zip_code',
            'is_email_verified', 'created_at', 'updated_at', 'user_type', 'date_joined',
            'subscription_start_date', 'subscription_end_date', 'groups',
            'is_profile_complete', 'profile_completion_percentage',
            'occupation_display', 'gender_display', 'age_group_display'
        ]
        read_only_fields = [
            'email', 'is_email_verified', 'created_at', 'updated_at', 'user_type',
            'subscription_start_date', 'subscription_end_date', 'age', 'age_group',
            'is_profile_complete', 'profile_completion_percentage'
        ]

    def get_groups(self, obj):
        """Get user groups for permission checking"""
        return [
            {
                'id': group.id,
                'name': group.name,
                'permissions': list(group.permissions.values_list('codename', flat=True))
            }
            for group in obj.groups.all()
        ]

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

class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information, especially for new users.
    """
    birth_date = serializers.DateField(required=False, help_text="Birth date (YYYY-MM-DD format)")
    gender = serializers.ChoiceField(choices=User.GENDER_CHOICES, required=False)
    occupation = serializers.ChoiceField(choices=User.OCCUPATION_CHOICES, required=False)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'bio', 'birth_date', 'gender',
            'location', 'occupation', 'zip_code', 'avatar_url'
        ]

    def validate_birth_date(self, value):
        """Validate birth date is not in the future and user is not too old"""
        from datetime import date
        today = date.today()

        if value > today:
            raise serializers.ValidationError("Birth date cannot be in the future.")

        age = today.year - value.year
        if today < date(today.year, value.month, value.day):
            age -= 1

        if age > 120:
            raise serializers.ValidationError("Please enter a valid birth date.")
        if age < 13:
            raise serializers.ValidationError("You must be at least 13 years old to use this service.")

        return value

    def update(self, instance, validated_data):
        """Update user profile and auto-calculate age fields"""
        # Update all provided fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Save will trigger auto-calculation of age and age_group
        instance.save()
        return instance

class LocationDetectionSerializer(serializers.Serializer):
    """
    Serializer for handling location detection data
    """
    ip_address = serializers.IPAddressField(required=False)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    country = serializers.CharField(max_length=100, required=False)
    region = serializers.CharField(max_length=100, required=False)
    city = serializers.CharField(max_length=100, required=False)
    zip_code = serializers.CharField(max_length=20, required=False)

class ProfileChoicesSerializer(serializers.Serializer):
    """
    Serializer for returning choices for profile fields
    """
    occupation_choices = serializers.SerializerMethodField()
    gender_choices = serializers.SerializerMethodField()
    age_group_choices = serializers.SerializerMethodField()
    user_type_choices = serializers.SerializerMethodField()

    def get_occupation_choices(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in User.OCCUPATION_CHOICES]

    def get_gender_choices(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in User.GENDER_CHOICES]

    def get_age_group_choices(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in User.AGE_GROUP_CHOICES]

    def get_user_type_choices(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in User.USER_TYPE_CHOICES]

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
    # total_watch_time = serializers.IntegerField()  # in minutes

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

        # Validate user limits before creating
        from apps.users.services.user_limits_service import UserLimitsService
        can_add, limit_info = UserLimitsService.validate_favorites_limit(user)

        if not can_add:
            raise serializers.ValidationError({
                'limit_exceeded': limit_info['message'],
                'current': limit_info['current'],
                'max': limit_info['max']
            })

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
    movie = serializers.IntegerField(write_only=True)  # Accept movie ID for creation
    status = serializers.CharField(required=False, default='PLANNED')
    watchlist = serializers.PrimaryKeyRelatedField(
        queryset=Watchlist.objects.all(),
        required=True
    )

    class Meta:
        model = WatchlistItem
        fields = ['id', 'watchlist', 'movie', 'status', 'created_at', 'updated_at', 'movie_data']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_movie_data(self, obj):
        return MovieSerializer(obj.movie).data

    def validate_watchlist(self, value):
        request = self.context.get('request')
        if request and value.user != request.user:
            raise serializers.ValidationError("You can only add items to your own watchlist")
        return value

    def create(self, validated_data):
        from apps.movies.models import Movie
        movie_id = validated_data.pop('movie')
        try:
            movie = Movie.objects.get(id=movie_id)
            # Check if movie is already in the watchlist
            if WatchlistItem.objects.filter(watchlist=validated_data['watchlist'], movie=movie).exists():
                raise serializers.ValidationError({'movie': 'Movie is already in this watchlist'})
            return WatchlistItem.objects.create(movie=movie, **validated_data)
        except Movie.DoesNotExist:
            raise serializers.ValidationError({'movie': 'Movie not found'})

class UserWatchlistSerializer(serializers.ModelSerializer):
    items = UserWatchlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Watchlist
        fields = ['id', 'name', 'created_at', 'updated_at', 'items']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user

        # Validate user limits before creating
        from apps.users.services.user_limits_service import UserLimitsService
        can_create, limit_info = UserLimitsService.validate_lists_limit(user)

        if not can_create:
            raise serializers.ValidationError({
                'limit_exceeded': limit_info['message'],
                'current': limit_info['current'],
                'max': limit_info['max']
            })

        return super().create(validated_data)
