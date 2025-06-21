from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import User, UserMovieRating, Watchlist, UserFavoriteGenre, PasswordResetToken
from apps.movies.serializers import MovieSerializer
from django.conf import settings
import requests

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

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'avatar_url', 'bio', 'age', 'gender',
            'location', 'is_email_verified', 'created_at', 'updated_at', 'user_type',
            'subscription_end_date'
        ]
        read_only_fields = ['email', 'is_email_verified', 'created_at', 'updated_at', 'user_type', 'subscription_end_date']

class UserStatsSerializer(serializers.Serializer):
    watched_movies_count = serializers.IntegerField()
    reviews_count = serializers.IntegerField()
    ratings_count = serializers.IntegerField()
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()

class UserRatingSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()

    class Meta:
        model = UserMovieRating
        fields = ['id', 'movie', 'rating', 'review_title', 'review_text', 'created_at']

class UserWatchlistSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()

    class Meta:
        model = Watchlist
        fields = ['id', 'movie', 'status', 'created_at']

class UserFavoriteGenreSerializer(serializers.ModelSerializer):
    genre_name = serializers.CharField(source='genre.name')

    class Meta:
        model = UserFavoriteGenre
        fields = ['id', 'genre_name']

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
