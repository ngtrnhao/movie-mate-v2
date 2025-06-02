from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import User, Rating, Watchlist, UserFavoriteGenre
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
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'avatar_url', 'bio', 'age', 'gender',
            'location', 'is_email_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['email', 'is_email_verified', 'created_at', 'updated_at']

class UserStatsSerializer(serializers.Serializer):
    watched_movies_count = serializers.IntegerField()
    reviews_count = serializers.IntegerField()
    ratings_count = serializers.IntegerField()
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()

class UserRatingSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()

    class Meta:
        model = Rating
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
