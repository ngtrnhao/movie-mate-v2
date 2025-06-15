from rest_framework import serializers
from .models import (
    Movie, MovieRating, MovieAward, MovieCast,
    MovieReview, MovieBoxOffice, MovieMetadata,
    MovieGenre, MovieTrailer, MovieImage, MovieNews, Genre
)
import logging

logger = logging.getLogger(__name__)

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class MovieListSerializer(serializers.ModelSerializer):
    genres = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    vote_average = serializers.SerializerMethodField()
    vote_count = serializers.SerializerMethodField()
    overviews = serializers.SerializerMethodField()
    poster_path = serializers.CharField(source='poster_url', allow_null=True)
    backdrop_path = serializers.CharField(source='backdrop_url', allow_null=True)

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'original_title', 'overview_en', 'overview_vi', 'release_date',
            'poster_path', 'backdrop_path', 'runtime', 'status', 'genres',
            'rating', 'vote_average', 'vote_count', 'is_popular',
            'is_top_rated', 'is_upcoming', 'overviews'
        ]

    def get_genres(self, obj):
        return [{'id': genre.id, 'name': genre.name} for genre in obj.genres.all()]

    def get_rating(self, obj):
        try:
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
            pass
        return None

    def get_vote_average(self, obj):
        try:
            rating = obj.ratings.first()
            if rating and rating.imdb_rating:
                return float(rating.imdb_rating)
            elif rating and rating.tmdb_rating:
                return float(rating.tmdb_rating)
            elif rating and rating.rotten_tomatoes_rating:
                return float(rating.rotten_tomatoes_rating)
        except (AttributeError, TypeError, ValueError) as e:
            logger.error(f"Error getting vote average for movie {obj.id}: {str(e)}")
            pass
        return None

    def get_vote_count(self, obj):
        try:
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
            pass
        return None

    def get_overviews(self, obj):
        return {
            'en': obj.overview_en,
            'vi': obj.overview_vi
        }

class MovieDetailSerializer(MovieListSerializer):
    """Serializer for detailed movie information"""
    class Meta(MovieListSerializer.Meta):
        fields = MovieListSerializer.Meta.fields + [
            'imdb_id', 'adult', 'end_year', 'is_adult'
        ]

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

class MovieCastSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieCast
        fields = '__all__'

class MovieReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieReview
        fields = '__all__'

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

class MovieTrailerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieTrailer
        fields = '__all__'

class MovieImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieImage
        fields = '__all__'

class MovieNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieNews
        fields = '__all__'
