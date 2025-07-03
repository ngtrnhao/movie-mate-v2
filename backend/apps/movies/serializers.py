from django.db.models import Q, Count
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Movie, MovieRating, MovieAward, MovieCast,
    MovieReview, MovieBoxOffice, MovieMetadata,
    MovieGenre, MovieTrailer, MovieImage, MovieNews
)
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

# Simple UserSerializer to avoid circular import
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar_url', 'bio', 'age', 'gender', 'location', 'is_email_verified', 'created_at', 'updated_at', 'user_type']

class MovieTrailerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieTrailer
        fields = ['title', 'youtube_key', 'type']

class MovieCastSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieCast
        fields = ['id', 'name', 'role', 'main_character', 'all_characters', 'order', 'job', 'category', 'imdb_id', 'profile_path']

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
            'id', 'slug', 'title', 'title_en', 'title_vi', 'original_title', 'overview_en', 'overview_vi', 'release_date',
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
        """Use cached rating for performance - Convert 10-star to 5-star scale"""
        try:
            raw_rating = None

            # Try cached fields first
            if obj.combined_rating_score is not None:
                raw_rating = float(obj.combined_rating_score)
            elif obj.cached_imdb_rating is not None:
                raw_rating = float(obj.cached_imdb_rating)
            elif obj.cached_tmdb_rating is not None:
                raw_rating = float(obj.cached_tmdb_rating)

            # Fallback to prefetched ratings
            if raw_rating is None and hasattr(obj, 'prefetched_ratings') and obj.prefetched_ratings:
                rating = obj.prefetched_ratings[0]
                if rating.imdb_rating:
                    raw_rating = float(rating.imdb_rating)
                elif rating.tmdb_rating:
                    raw_rating = float(rating.tmdb_rating)
                elif rating.rotten_tomatoes_rating:
                    raw_rating = float(rating.rotten_tomatoes_rating)

            # Fallback to database query
            if raw_rating is None:
                rating = obj.ratings.first()
                if rating:
                    if rating.imdb_rating:
                        raw_rating = float(rating.imdb_rating)
                    elif rating.tmdb_rating:
                        raw_rating = float(rating.tmdb_rating)
                    elif rating.rotten_tomatoes_rating:
                        raw_rating = float(rating.rotten_tomatoes_rating)

            # Convert from 10-star to 5-star scale
            if raw_rating is not None:
                return round(raw_rating / 2, 1)  # Convert 0-10 to 0-5 scale

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
    production_info = serializers.SerializerMethodField()
    directors = serializers.SerializerMethodField()
    original_language = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta(MovieListSerializer.Meta):
        fields = MovieListSerializer.Meta.fields + [
            'imdb_id', 'is_adult', 'end_year', 'is_adult', 'cast',
            'production_info', 'directors', 'original_language', 'images'
        ]

    def get_cast(self, obj):
        # Use prefetched cast to avoid N+1
        if hasattr(obj, 'prefetched_cast'):
            return MovieCastSerializer(obj.prefetched_cast, many=True).data
        return MovieCastSerializer(obj.cast.all()[:20], many=True).data  # Limit to 20 cast members

    def get_production_info(self, obj):
        """Get production companies and countries from metadata"""
        try:
            if hasattr(obj, 'moviemetadata'):
                metadata = obj.moviemetadata
                return {
                    'production_companies': metadata.production_companies or [],
                    'production_countries': metadata.production_countries or [],
                    'spoken_languages': metadata.spoken_languages or [],
                    'budget': metadata.budget,
                    'revenue': metadata.revenue,
                    'tagline': metadata.tagline,
                    'homepage': metadata.homepage
                }
        except Exception as e:
            logger.error(f"Error getting production info for movie {obj.id}: {str(e)}")

        return {
            'production_companies': [],
            'production_countries': [],
            'spoken_languages': [],
            'budget': None,
            'revenue': None,
            'tagline': None,
            'homepage': None
        }

    def get_directors(self, obj):
        """Get directors from cast"""
        try:
            if hasattr(obj, 'prefetched_cast'):
                directors = [
                    {
                        'name': cast.name,
                        'imdb_id': cast.imdb_id,
                        'tmdb_id': cast.tmdb_id,
                        'profile_path': cast.profile_path
                    }
                    for cast in obj.prefetched_cast
                    if cast.role == 'DIRECTOR'
                ]
                return directors[:3]  # Limit to 3 directors

            # Fallback to database query
            directors = obj.cast.filter(role='DIRECTOR')[:3]
            return [
                {
                    'name': director.name,
                    'imdb_id': director.imdb_id,
                    'tmdb_id': director.tmdb_id,
                    'profile_path': director.profile_path
                }
                for director in directors
            ]
        except Exception as e:
            logger.error(f"Error getting directors for movie {obj.id}: {str(e)}")

        return []

    def get_original_language(self, obj):
        """Get original language from metadata or movie"""
        try:
            # Try to get from movie field first (if it exists)
            if hasattr(obj, 'original_language') and obj.original_language:
                return obj.original_language

            # Try to get from MovieMetadata spoken_languages
            if hasattr(obj, 'moviemetadata') and obj.moviemetadata:
                metadata = obj.moviemetadata
                if metadata.spoken_languages and len(metadata.spoken_languages) > 0:
                    # Return first spoken language ISO code
                    first_lang = metadata.spoken_languages[0]
                    if isinstance(first_lang, dict):
                        iso_code = first_lang.get('iso_639_1')
                        if iso_code:
                            return iso_code
                    elif isinstance(first_lang, str) and len(first_lang) >= 2:
                        return first_lang[:2].lower()

            # Check if homepage contains clues about language
            if hasattr(obj, 'moviemetadata') and obj.moviemetadata and obj.moviemetadata.homepage:
                homepage = obj.moviemetadata.homepage.lower()
                if 'netflix.com' in homepage and '/fr/' in homepage:
                    return 'fr'
                elif 'netflix.com' in homepage:
                    return 'en'

            # Fallback based on production countries
            if hasattr(obj, 'moviemetadata') and obj.moviemetadata:
                metadata = obj.moviemetadata
                if metadata.production_countries and len(metadata.production_countries) > 0:
                    first_country = metadata.production_countries[0]
                    if isinstance(first_country, dict):
                        country_code = first_country.get('iso_3166_1', '').upper()
                        # Map common countries to languages
                        country_to_lang = {
                            'FR': 'fr', 'BE': 'fr', 'CA': 'fr',  # French countries
                            'US': 'en', 'GB': 'en', 'AU': 'en', 'NZ': 'en',  # English countries
                            'ES': 'es', 'MX': 'es', 'AR': 'es',  # Spanish countries
                            'DE': 'de', 'AT': 'de', 'CH': 'de',  # German countries
                            'IT': 'it', 'JP': 'ja', 'KR': 'ko', 'CN': 'zh'
                        }
                        if country_code in country_to_lang:
                            return country_to_lang[country_code]

            # Final fallback
            return 'en'

        except Exception as e:
            logger.error(f"Error getting original language for movie {obj.id}: {str(e)}")

        return 'en'  # Safe fallback

    def get_images(self, obj):
        """Get all movie images grouped by type"""
        try:
            # Use prefetched images to avoid N+1
            if hasattr(obj, 'prefetched_images'):
                images = obj.prefetched_images
            else:
                images = obj.movieimage_set.all()

            # Group images by type
            grouped_images = {
                'posters': [],
                'backdrops': [],
                'screenshots': []
            }

            for image in images:
                image_data = {
                    'id': image.id,
                    'image_url': image.image_url,
                    'width': image.width,
                    'height': image.height,
                    'aspect_ratio': float(image.aspect_ratio) if image.aspect_ratio else None
                }

                if image.type == 'POSTER':
                    grouped_images['posters'].append(image_data)
                elif image.type == 'BACKDROP':
                    grouped_images['backdrops'].append(image_data)
                elif image.type == 'SCREENSHOT':
                    grouped_images['screenshots'].append(image_data)

            return grouped_images
        except Exception as e:
            logger.error(f"Error getting images for movie {obj.id}: {str(e)}")
            return {
                'posters': [],
                'backdrops': [],
                'screenshots': []
            }

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'title_en', 'title_vi', 'original_title',
            'overview_en', 'overview_vi', 'release_date', 'poster_url',
            'backdrop_url', 'runtime', 'status', 'genres', 'created_at',
            'updated_at', 'is_popular', 'is_top_rated', 'is_upcoming'
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

class MovieReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for MovieReview model
    """
    user = UserSerializer(read_only=True)
    reviewer_name = serializers.CharField(read_only=True)
    reviewer_avatar = serializers.CharField(read_only=True)
    is_verified_reviewer = serializers.BooleanField(read_only=True)
    helpfulness_ratio = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_vote = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()  # 'helpful', 'not_helpful', or None
    can_reply = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    is_reply = serializers.ReadOnlyField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = MovieReview
        fields = [
            'id', 'movie', 'user', 'title', 'content', 'rating',
            'review_type', 'language', 'is_public', 'is_spoiler',
            'helpful_votes', 'total_votes', 'helpfulness_ratio',
            'reviewer_name', 'reviewer_avatar', 'is_verified_reviewer',
            'can_edit', 'can_vote', 'user_vote', 'can_reply', 'reply_count',
            'is_reply', 'parent_review', 'replies',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'helpful_votes', 'total_votes', 'helpfulness_ratio',
            'reviewer_name', 'reviewer_avatar', 'is_verified_reviewer',
            'can_edit', 'can_vote', 'user_vote', 'created_at', 'updated_at'
        ]

    def validate_rating(self, value):
        """Validate rating is between 0.0 and 5.0"""
        if value is not None:
            if value < 0.0 or value > 5.0:
                raise serializers.ValidationError("Rating must be between 0.0 and 5.0")
        return value

    def validate_content(self, value):
        """Validate content is not empty and has minimum length"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Review content must be at least 10 characters long")
        return value.strip()

    def get_helpfulness_ratio(self, obj):
        """Calculate helpfulness ratio"""
        return obj.get_helpfulness_ratio()

    def get_can_edit(self, obj):
        """Check if current user can edit this review"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.can_be_edited_by(request.user)

    def get_can_vote(self, obj):
        """Check if current user can vote on this review"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        # Users can't vote on their own reviews
        return obj.user != request.user

    def get_user_vote(self, obj):
        """Get current user's vote on this review"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        try:
            from apps.movies.models import ReviewVote
            vote = ReviewVote.objects.filter(
                review=obj,
                user=request.user
            ).first()
            return vote.vote_type if vote else None
        except:
            return None

    def get_can_reply(self, obj):
        """Check if current user can reply to this review"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        # Users can't reply to their own reviews
        return obj.user != request.user

    def get_reply_count(self, obj):
        """Get reply count for this review"""
        return obj.replies.count()

    def get_replies(self, obj):
        """Get replies for this review"""
        # Only show replies for main reviews (not for replies to avoid deep nesting)
        if obj.is_reply:
            return []

        replies = obj.get_top_level_replies()
        return MovieReplySerializer(replies, many=True, context=self.context).data

    def create(self, validated_data):
        """Set the user automatically from request"""
        validated_data['user'] = self.context['request'].user
        validated_data['review_type'] = 'USER'
        return super().create(validated_data)


class MovieReviewCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating reviews
    """
    class Meta:
        model = MovieReview
        fields = ['movie', 'title', 'content', 'rating', 'language', 'is_public', 'is_spoiler']

    def validate_rating(self, value):
        if value is not None:
            if value < 0.0 or value > 5.0:
                raise serializers.ValidationError("Rating must be between 0.0 and 5.0")
        return value

    def validate_content(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Review content must be at least 10 characters long")
        return value.strip()

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['review_type'] = 'USER'
        return super().create(validated_data)


class MovieReviewUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating reviews
    """
    class Meta:
        model = MovieReview
        fields = ['title', 'content', 'rating', 'language', 'is_public', 'is_spoiler']

    def validate_rating(self, value):
        if value is not None:
            if value < 0.0 or value > 5.0:
                raise serializers.ValidationError("Rating must be between 0.0 and 5.0")
        return value

    def validate_content(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Review content must be at least 10 characters long")
        return value.strip()


class ReviewVoteSerializer(serializers.Serializer):
    """
    Serializer for voting on reviews
    """
    vote = serializers.ChoiceField(choices=['helpful', 'not_helpful'])

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

class UnifiedMovieReviewWithDetailsSerializer(serializers.ModelSerializer):
    rating_stars = serializers.SerializerMethodField()
    reviewer_name = serializers.CharField(source='user.username')
    reviewer_avatar = serializers.URLField(source='user.avatar_url', allow_null=True)
    is_verified_reviewer = serializers.BooleanField(default=True)
    helpfulness_ratio = serializers.FloatField(default=0)
    time_ago = serializers.SerializerMethodField()
    movie_details = serializers.SerializerMethodField()

    class Meta:
        model = MovieReview
        fields = [
            'id',
            'title',
            'content',
            'rating',
            'rating_stars',
            'review_type',
            'reviewer_name',
            'reviewer_avatar',
            'is_verified_reviewer',
            'helpful_votes',
            'total_votes',
            'helpfulness_ratio',
            'is_spoiler',
            'is_public',
            'source',
            'source_url',
            'created_at',
            'time_ago',
            'movie_details'
        ]

    def get_rating_stars(self, obj):
        if not obj.rating:
            return None

        rating = float(obj.rating)
        full_stars = int(rating)
        half_star = (rating - full_stars) >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)

        return {
            'numeric': rating,
            'display': '★' * full_stars + ('½' if half_star else '') + '☆' * empty_stars,
            'full_stars': full_stars,
            'half_star': half_star,
            'empty_stars': empty_stars
        }

    def get_time_ago(self, obj):
        from django.utils import timezone
        from datetime import datetime, timedelta

        now = timezone.now()
        diff = now - obj.created_at

        if diff < timedelta(minutes=1):
            return 'vừa xong'
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f'{minutes} phút trước'
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f'{hours} giờ trước'
        elif diff < timedelta(days=30):
            days = diff.days
            return f'{days} ngày trước'
        elif diff < timedelta(days=365):
            months = int(diff.days / 30)
            return f'{months} tháng trước'
        else:
            years = int(diff.days / 365)
            return f'{years} năm trước'

    def get_movie_details(self, obj):
        movie = obj.movie
        if not movie:
            return None

        # Get the first 5 cast members with their details
        cast = movie.cast.filter(role='ACTOR').order_by('order')[:5]
        cast_details = []

        for cast_member in cast:
            cast_details.append({
                'id': cast_member.id,
                'name': cast_member.name,
                'profile_path': cast_member.profile_path,
                'character': cast_member.main_character or ''
            })

        return {
            'id': movie.id,
            'title': movie.title,
            'original_title': movie.original_title,
            'release_date': movie.release_date,
            'poster_path': movie.poster_url,
            'backdrop_path': movie.backdrop_url,
            'genres': [{'id': g.id, 'name': g.name} for g in movie.genres.all()],
            'runtime': movie.runtime,
            'vote_average': movie.cached_tmdb_rating,
            'vote_count': movie.cached_tmdb_votes,
            'overview': movie.overview_en or movie.overview_vi or '',
            'cast': cast_details
        }

class MovieReplySerializer(serializers.ModelSerializer):
    """Simplified serializer for replies to avoid infinite recursion"""
    user = UserSerializer(read_only=True)
    reviewer_name = serializers.CharField(read_only=True)
    reviewer_avatar = serializers.CharField(read_only=True)
    is_verified_reviewer = serializers.BooleanField(read_only=True)
    helpfulness_ratio = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_vote = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    can_reply = serializers.SerializerMethodField()
    is_reply = serializers.ReadOnlyField()

    class Meta:
        model = MovieReview
        fields = [
            'id', 'user', 'content', 'is_public', 'is_spoiler',
            'helpful_votes', 'total_votes', 'helpfulness_ratio',
            'reviewer_name', 'reviewer_avatar', 'is_verified_reviewer',
            'can_edit', 'can_vote', 'user_vote', 'can_reply',
            'is_reply', 'parent_review', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'helpful_votes', 'total_votes', 'helpfulness_ratio',
            'reviewer_name', 'reviewer_avatar', 'is_verified_reviewer',
            'can_edit', 'can_vote', 'user_vote', 'can_reply',
            'is_reply', 'parent_review', 'created_at', 'updated_at'
        ]

    def get_helpfulness_ratio(self, obj):
        return obj.get_helpfulness_ratio()

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.can_be_edited_by(request.user)

    def get_can_vote(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.user != request.user

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        try:
            from apps.movies.models import ReviewVote
            vote = ReviewVote.objects.filter(
                review=obj,
                user=request.user
            ).first()
            return vote.vote_type if vote else None
        except:
            return None

    def get_can_reply(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.can_reply(request.user)

class MovieReplyCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating replies to reviews
    """
    class Meta:
        model = MovieReview
        fields = ['parent_review', 'content', 'language', 'is_public', 'is_spoiler']

    def validate_content(self, value):
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("Reply content must be at least 5 characters long")
        return value.strip()

    def validate_parent_review(self, value):
        if value is None:
            raise serializers.ValidationError("Parent review is required for replies")

        # Check if parent review exists and is public
        if not value.is_public:
            raise serializers.ValidationError("Cannot reply to private reviews")

        # Check if parent is external review
        if value.review_type == 'EXTERNAL':
            raise serializers.ValidationError("Cannot reply to external reviews")

        # Check if parent is already a reply (no deep nesting)
        if value.is_reply:
            raise serializers.ValidationError("Cannot reply to replies. Please reply to the main review instead.")

        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['review_type'] = 'USER'
        validated_data['movie'] = validated_data['parent_review'].movie
        validated_data['rating'] = None  # Replies cannot have ratings
        validated_data['title'] = None   # Replies don't need titles
        return super().create(validated_data)
