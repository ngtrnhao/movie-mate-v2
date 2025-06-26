from rest_framework import serializers
from .models import (
    Movie, MovieRating, MovieAward, MovieCast,
    MovieReview, MovieBoxOffice, MovieMetadata,
    MovieGenre, MovieTrailer, MovieImage, MovieNews
)
import logging

logger = logging.getLogger(__name__)

class MovieTrailerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieTrailer
        fields = ['title', 'youtube_key', 'type']

class MovieCastSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieCast
        fields = ['id', 'name', 'role', 'main_character', 'all_characters', 'order', 'job', 'category', 'imdb_id']

class OptimizedMovieListSerializer(serializers.ModelSerializer):
    """Optimized serializer for movie list with cached rating fields"""
    genres = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    vote_average = serializers.SerializerMethodField()
    vote_count = serializers.SerializerMethodField()
    overviews = serializers.SerializerMethodField()
    poster_path = serializers.CharField(source='poster_url', allow_null=True)
    backdrop_path = serializers.CharField(source='backdrop_url', allow_null=True)
    trailers = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'title_vi', 'original_title', 'overview_en', 'overview_vi', 'release_date',
            'poster_path', 'backdrop_path', 'runtime', 'status', 'genres',
            'rating', 'vote_average', 'vote_count', 'is_popular',
            'is_top_rated', 'is_upcoming', 'overviews', 'trailers'
        ]

    def get_genres(self, obj):
        # Use prefetched genres to avoid N+1
        if hasattr(obj, 'prefetched_genres'):
            return [{'id': genre.id, 'name': genre.name, 'language': genre.language}
                   for genre in obj.prefetched_genres]
        return [{'id': genre.id, 'name': genre.name, 'language': genre.language}
               for genre in obj.genres.all()]

    def get_rating(self, obj):
        """Use cached rating fields for performance"""
        try:
            # Try cached fields first
            if obj.cached_imdb_rating is not None or obj.cached_tmdb_rating is not None:
                return {
                    'imdb': float(obj.cached_imdb_rating) if obj.cached_imdb_rating else None,
                    'imdb_votes': obj.cached_imdb_votes,
                    'tmdb': float(obj.cached_tmdb_rating) if obj.cached_tmdb_rating else None,
                    'tmdb_votes': obj.cached_tmdb_votes,
                    'combined_score': float(obj.combined_rating_score) if obj.combined_rating_score else None,
                }

            # Fallback to prefetched ratings
            if hasattr(obj, 'prefetched_ratings') and obj.prefetched_ratings:
                rating = obj.prefetched_ratings[0]
                return {
                    'imdb': float(rating.imdb_rating) if rating.imdb_rating else None,
                    'imdb_votes': rating.imdb_votes,
                    'metacritic': rating.metacritic_rating,
                    'tmdb': float(rating.tmdb_rating) if rating.tmdb_rating else None,
                    'tmdb_votes': rating.tmdb_votes,
                    'rotten_tomatoes': float(rating.rotten_tomatoes_rating) if rating.rotten_tomatoes_rating else None,
                    'rotten_tomatoes_votes': rating.rotten_tomatoes_votes,
                    'film_affinity': float(rating.film_affinity_rating) if rating.film_affinity_rating else None,
                    'film_affinity_votes': rating.film_affinity_votes
                }

            # Fallback to database query (least efficient)
            rating = obj.ratings.first()
            if rating:
                return {
                    'imdb': float(rating.imdb_rating) if rating.imdb_rating else None,
                    'imdb_votes': rating.imdb_votes,
                    'metacritic': rating.metacritic_rating,
                    'tmdb': float(rating.tmdb_rating) if rating.tmdb_rating else None,
                    'tmdb_votes': rating.tmdb_votes,
                    'rotten_tomatoes': float(rating.rotten_tomatoes_rating) if rating.rotten_tomatoes_rating else None,
                    'rotten_tomatoes_votes': rating.rotten_tomatoes_votes,
                    'film_affinity': float(rating.film_affinity_rating) if rating.film_affinity_rating else None,
                    'film_affinity_votes': rating.film_affinity_votes
                }
        except (AttributeError, TypeError, ValueError) as e:
            logger.error(f"Error getting rating for movie {obj.id}: {str(e)}")
        return None

    def get_vote_average(self, obj):
        """Use cached rating for performance"""
        try:
            # Try cached fields first
            if obj.combined_rating_score is not None:
                return float(obj.combined_rating_score)
            if obj.cached_imdb_rating is not None:
                return float(obj.cached_imdb_rating)
            if obj.cached_tmdb_rating is not None:
                return float(obj.cached_tmdb_rating)

            # Fallback to prefetched ratings
            if hasattr(obj, 'prefetched_ratings') and obj.prefetched_ratings:
                rating = obj.prefetched_ratings[0]
                if rating.imdb_rating:
                    return float(rating.imdb_rating)
                elif rating.tmdb_rating:
                    return float(rating.tmdb_rating)
                elif rating.rotten_tomatoes_rating:
                    return float(rating.rotten_tomatoes_rating)

            # Fallback to database query
            rating = obj.ratings.first()
            if rating:
                if rating.imdb_rating:
                    return float(rating.imdb_rating)
                elif rating.tmdb_rating:
                    return float(rating.tmdb_rating)
                elif rating.rotten_tomatoes_rating:
                    return float(rating.rotten_tomatoes_rating)
        except (AttributeError, TypeError, ValueError) as e:
            logger.error(f"Error getting vote average for movie {obj.id}: {str(e)}")
        return None

    def get_vote_count(self, obj):
        """Use cached votes for performance"""
        try:
            # Try cached fields first
            total_votes = 0
            if obj.cached_imdb_votes:
                total_votes += obj.cached_imdb_votes
            if obj.cached_tmdb_votes:
                total_votes += obj.cached_tmdb_votes
            if total_votes > 0:
                return total_votes

            # Fallback to prefetched ratings
            if hasattr(obj, 'prefetched_ratings') and obj.prefetched_ratings:
                rating = obj.prefetched_ratings[0]
                total_votes = 0
                if rating.imdb_votes:
                    total_votes += rating.imdb_votes
                if rating.tmdb_votes:
                    total_votes += rating.tmdb_votes
                if rating.rotten_tomatoes_votes:
                    total_votes += rating.rotten_tomatoes_votes
                return total_votes if total_votes > 0 else None

            # Fallback to database query
            rating = obj.ratings.first()
            if rating:
                total_votes = 0
                if rating.imdb_votes:
                    total_votes += rating.imdb_votes
                if rating.tmdb_votes:
                    total_votes += rating.tmdb_votes
                if rating.rotten_tomatoes_votes:
                    total_votes += rating.rotten_tomatoes_votes
                return total_votes if total_votes > 0 else None
        except (AttributeError, TypeError, ValueError) as e:
            logger.error(f"Error getting vote count for movie {obj.id}: {str(e)}")
        return None

    def get_overviews(self, obj):
        return {
            'en': obj.overview_en,
            'vi': obj.overview_vi
        }

    def get_trailers(self, obj):
        # Use prefetched trailers to avoid N+1
        if hasattr(obj, 'prefetched_trailers'):
            return MovieTrailerSerializer(obj.prefetched_trailers, many=True).data
        return MovieTrailerSerializer(obj.trailers.all(), many=True).data

# Keep the old serializer for backward compatibility
class MovieListSerializer(OptimizedMovieListSerializer):
    """Backward compatibility alias"""
    pass

class MovieDetailSerializer(MovieListSerializer):
    """Serializer for detailed movie information"""
    cast = serializers.SerializerMethodField()

    class Meta(MovieListSerializer.Meta):
        fields = MovieListSerializer.Meta.fields + [
            'imdb_id', 'adult', 'end_year', 'is_adult', 'cast'
        ]

    def get_cast(self, obj):
        # Use prefetched cast to avoid N+1
        if hasattr(obj, 'prefetched_cast'):
            return MovieCastSerializer(obj.prefetched_cast, many=True).data
        return MovieCastSerializer(obj.cast.all()[:20], many=True).data  # Limit to 20 cast members

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'original_title', 'overview', 'release_date',
            'poster_url', 'backdrop_url', 'imdb_rating', 'tmdb_id',
            'runtime', 'status'
        ]

class MovieRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieRating
        fields = '__all__'

class MovieAwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieAward
        fields = '__all__'

class UnifiedMovieReviewSerializer(serializers.ModelSerializer):
    """Unified serializer for both user and external reviews"""
    reviewer_name = serializers.ReadOnlyField()
    reviewer_avatar = serializers.ReadOnlyField()
    is_verified_reviewer = serializers.ReadOnlyField()
    helpfulness_ratio = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    rating_stars = serializers.SerializerMethodField()

    class Meta:
        model = MovieReview
        fields = [
            'id', 'title', 'content', 'rating', 'rating_stars', 'review_type',
            'reviewer_name', 'reviewer_avatar', 'is_verified_reviewer',
            'helpful_votes', 'total_votes', 'helpfulness_ratio',
            'is_spoiler', 'is_public', 'source', 'source_url',
            'created_at', 'time_ago'
        ]
        read_only_fields = ['reviewer_name', 'reviewer_avatar', 'is_verified_reviewer', 'rating_stars']

    def get_helpfulness_ratio(self, obj):
        return obj.get_helpfulness_ratio()

    def get_rating_stars(self, obj):
        """Convert numeric rating to star display"""
        if obj.rating is None:
            return None

        rating = float(obj.rating)
        full_stars = int(rating)
        half_star = (rating - full_stars) >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)

        return {
            'numeric': rating,
            'display': '★' * full_stars + ('☆' if half_star else '') + '☆' * empty_stars,
            'full_stars': full_stars,
            'half_star': half_star,
            'empty_stars': empty_stars
        }

    def get_time_ago(self, obj):
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        diff = now - obj.created_at

        if diff.days > 0:
            return f"{diff.days} ngày trước"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} giờ trước"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} phút trước"
        else:
            return "Vừa xong"

class MovieReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user reviews"""
    class Meta:
        model = MovieReview
        fields = ['movie', 'title', 'content', 'rating', 'is_public', 'is_spoiler']

    def create(self, validated_data):
        # Set review_type to USER and link with current user
        validated_data['review_type'] = 'USER'
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def validate_rating(self, value):
        """Validate rating is within 5-star system (0.0 - 5.0)"""
        if value is not None:
            if value < 0.0 or value > 5.0:
                raise serializers.ValidationError("Rating must be between 0.0 and 5.0 stars")
            # Allow only half-star increments (0.0, 0.5, 1.0, 1.5, etc.)
            if (value * 2) % 1 != 0:
                raise serializers.ValidationError("Rating must be in half-star increments (e.g. 0.5, 1.0, 1.5)")
        return value

    def validate(self, data):
        user = self.context['request'].user
        movie = data['movie']

        # Check if user already has a review for this movie
        if MovieReview.objects.filter(user=user, movie=movie, review_type='USER').exists():
            raise serializers.ValidationError("Bạn đã có review cho phim này rồi.")

        return data

# Keep old name for backward compatibility
class MovieReviewSerializer(UnifiedMovieReviewSerializer):
    """Backward compatibility alias"""
    pass

class MovieBoxOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieBoxOffice
        fields = '__all__'

class MovieMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieMetadata
        fields = '__all__'

class MovieGenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieGenre
        fields = '__all__'

class MovieImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieImage
        fields = '__all__'

class MovieNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieNews
        fields = '__all__'
