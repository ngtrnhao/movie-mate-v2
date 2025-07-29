from django.db.models import Q, Count
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Movie, MovieRating, MovieCast,
    MovieReview, MovieBoxOffice, MovieMetadata,
    MovieGenre, MovieTrailer, MovieImage,
    ReviewReport, MovieAdminControl, MovieQualityMetrics,
    MovieScheduling, ProductionMetrics, UserInteraction
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
    popularity = serializers.SerializerMethodField()
    # Frontend compatibility fields
    adult = serializers.BooleanField(source='is_adult', read_only=True)

    class Meta:
        model = Movie
        fields = [
            'id', 'slug', 'title', 'title_en', 'title_vi', 'original_title', 'overview_en', 'overview_vi', 'release_date',
            'poster_path', 'poster_url', 'backdrop_path', 'runtime', 'status', 'genres',
            'rating', 'combined_rating_score', 'cached_imdb_rating', 'vote_average', 'vote_count', 'is_popular',
            'is_top_rated', 'is_upcoming', 'overviews', 'trailers', 'popularity', 'is_adult', 'adult',
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

        # Always return a consistent rating object structure
        return {
            'imdb': float(obj.cached_imdb_rating) if obj.cached_imdb_rating else None,
            'imdb_votes': obj.cached_imdb_votes if obj.cached_imdb_votes else 0,
            'tmdb': float(obj.cached_tmdb_rating) if obj.cached_tmdb_rating else None,
            'tmdb_votes': obj.cached_tmdb_votes if obj.cached_tmdb_votes else 0,
            'combined_score': float(obj.combined_rating_score) if obj.combined_rating_score else None,
        }

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

    def get_popularity(self, obj):
        # Always return a float, never None
        if obj.combined_rating_score is not None:
            return float(obj.combined_rating_score)
        return 0.0

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

# class MovieAwardSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MovieAward
#         fields = '__all__'

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
            'is_spoiler', 'is_public', 'source',
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
    movie = MovieSerializer(read_only=True)  # Include full movie details
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
    mentioned_username = serializers.ReadOnlyField()
    moderation_analysis = serializers.SerializerMethodField()
    report_summary = serializers.SerializerMethodField()
    moderation_feedback = serializers.SerializerMethodField()
    spoiler_confidence = serializers.FloatField(read_only=True)

    class Meta:
        model = MovieReview
        fields = [
            'id', 'movie', 'user', 'title', 'content', 'rating',
            'review_type', 'language', 'is_public', 'is_spoiler',
            'helpful_votes', 'total_votes', 'helpfulness_ratio',
            'reviewer_name', 'reviewer_avatar', 'is_verified_reviewer',
            'can_edit', 'can_vote', 'user_vote', 'can_reply', 'reply_count',
            'is_reply', 'parent_review', 'replies', 'mentioned_username',
            'is_approved', 'moderated_by', 'moderated_at', 'moderation_reason',
            'moderation_analysis', 'created_at', 'updated_at', 'report_summary',
            'moderation_feedback', 'spoiler_confidence'
        ]
        read_only_fields = [
            'id', 'user', 'helpful_votes', 'total_votes', 'helpfulness_ratio',
            'reviewer_name', 'reviewer_avatar', 'is_verified_reviewer',
            'can_edit', 'can_vote', 'user_vote', 'moderation_analysis', 'created_at', 'updated_at', 'spoiler_confidence'
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

    def get_moderation_analysis(self, obj):
        """Get moderation analysis for this review"""
        # Only return moderation analysis if it exists (added by moderation_queue)
        if hasattr(obj, 'moderation_analysis'):
            return obj.moderation_analysis
        return None

    def get_report_summary(self, obj):
        """Get report summary for this review"""
        # Only return report summary if it exists (added by reports_for_moderation)
        if hasattr(obj, 'report_summary'):
            return obj.report_summary
        return None

    def get_moderation_feedback(self, obj):
        """Get moderation feedback for this review"""
        try:
            from apps.movies.models import ModerationFeedback
            feedback_qs = ModerationFeedback.objects.filter(review=obj).select_related('moderator')
            feedback_data = []
            for feedback in feedback_qs:
                feedback_data.append({
                    'id': feedback.id,
                    'feedback_type': feedback.feedback_type,
                    'moderator_decision': feedback.moderator_decision,
                    'is_spoiler_correct': feedback.is_spoiler_correct,
                    'difficulty_level': feedback.difficulty_level,
                    'notes': feedback.notes,
                    'time_spent_seconds': feedback.time_spent_seconds,
                    'moderator': {
                        'id': feedback.moderator.id,
                        'username': feedback.moderator.username
                    } if feedback.moderator else None,
                    'created_at': feedback.created_at,
                    'updated_at': feedback.updated_at
                })
            return feedback_data
        except Exception as e:
            # Return empty list if there's an error
            return []

    def create(self, validated_data):
        """Set the user automatically from request"""
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['review_type'] = 'USER'

        # Validate user limits before creating
        from apps.users.services.user_limits_service import UserLimitsService
        can_review, limit_info = UserLimitsService.validate_reviews_limit(user)

        if not can_review:
            raise serializers.ValidationError({
                'limit_exceeded': limit_info['message'],
                'current': limit_info['current'],
                'max': limit_info['max']
            })

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
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['review_type'] = 'USER'

        # Validate user limits before creating
        from apps.users.services.user_limits_service import UserLimitsService
        can_review, limit_info = UserLimitsService.validate_reviews_limit(user)

        if not can_review:
            raise serializers.ValidationError({
                'limit_exceeded': limit_info['message'],
                'current': limit_info['current'],
                'max': limit_info['max']
            })

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

# class MovieNewsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MovieNews
#         fields = '__all__'

class UnifiedMovieReviewWithDetailsSerializer(serializers.ModelSerializer):
    rating_stars = serializers.SerializerMethodField()
    reviewer_name = serializers.CharField(source='user.username')
    reviewer_avatar = serializers.URLField(source='user.avatar_url', allow_null=True)
    is_verified_reviewer = serializers.BooleanField(default=True)
    helpfulness_ratio = serializers.FloatField(default=0)
    time_ago = serializers.SerializerMethodField()
    movie_details = serializers.SerializerMethodField()
    moderated_by = UserSerializer(read_only=True)

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
            'is_approved',
            'moderated_by',
            'moderated_at',
            'moderation_reason',
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
            'title_en': movie.title_en,
            'title_vi': movie.title_vi,
            'original_title': movie.original_title,
            'release_date': movie.release_date,
            'poster_path': movie.poster_url,
            'backdrop_path': movie.backdrop_url,
            'genres': [{'id': g.id, 'name': g.name} for g in (
                movie.genres.filter(language=self.context.get('language', 'vi')).exists() and
                movie.genres.filter(language=self.context.get('language', 'vi')) or
                movie.genres.filter(language='en').exists() and movie.genres.filter(language='en') or
                movie.genres.all()
            )],
            'runtime': movie.runtime,
            'vote_average': movie.cached_tmdb_rating,
            'vote_count': movie.cached_tmdb_votes,
            'overview_en': movie.overview_en,
            'overview_vi': movie.overview_vi,
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
    mentioned_username = serializers.ReadOnlyField()

    class Meta:
        model = MovieReview
        fields = [
            'id', 'user', 'content', 'is_public', 'is_spoiler',
            'helpful_votes', 'total_votes', 'helpfulness_ratio',
            'reviewer_name', 'reviewer_avatar', 'is_verified_reviewer',
            'can_edit', 'can_vote', 'user_vote', 'can_reply',
            'is_reply', 'parent_review', 'mentioned_username', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'helpful_votes', 'total_votes', 'helpfulness_ratio',
            'reviewer_name', 'reviewer_avatar', 'is_verified_reviewer',
            'can_edit', 'can_vote', 'user_vote', 'can_reply',
            'is_reply', 'parent_review', 'mentioned_username', 'created_at', 'updated_at'
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
    reply_to_user_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = MovieReview
        fields = ['parent_review', 'content', 'language', 'is_public', 'is_spoiler', 'reply_to_user_id']

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

        return value

    def create(self, validated_data):
        parent_review = validated_data['parent_review']
        reply_to_user_id = validated_data.pop('reply_to_user_id', None)

        validated_data['user'] = self.context['request'].user
        validated_data['review_type'] = 'USER'
        validated_data['movie'] = parent_review.movie
        validated_data['rating'] = None  # Replies cannot have ratings
        validated_data['title'] = None   # Replies don't need titles

        # Handle reply to reply - flatten to same level
        if parent_review.is_reply:
            # If replying to a reply, set parent to main review and track the mentioned user
            validated_data['parent_review'] = parent_review.parent_review
            validated_data['reply_to_user'] = parent_review.user
        else:
            # If replying to main review, check if user specified a reply_to_user
            if reply_to_user_id:
                try:
                    from apps.users.models import User
                    reply_to_user = User.objects.get(id=reply_to_user_id)
                    validated_data['reply_to_user'] = reply_to_user
                except User.DoesNotExist:
                    pass  # Ignore invalid user ID

        return super().create(validated_data)

class ReviewReportSerializer(serializers.ModelSerializer):
    reported_by = UserSerializer(read_only=True)

    class Meta:
        model = ReviewReport
        fields = ['id', 'review', 'reported_by', 'reason', 'description', 'created_at']
        read_only_fields = ['id', 'reported_by', 'created_at']

class ModerationQueueReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for moderation queue with full movie details
    """
    user = UserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)  # Include full movie details
    reviewer_name = serializers.CharField(read_only=True)
    reviewer_avatar = serializers.CharField(read_only=True)
    is_verified_reviewer = serializers.BooleanField(read_only=True)
    helpfulness_ratio = serializers.SerializerMethodField()
    moderation_analysis = serializers.SerializerMethodField()
    report_summary = serializers.SerializerMethodField()

    class Meta:
        model = MovieReview
        fields = [
            'id', 'movie', 'user', 'title', 'content', 'rating',
            'review_type', 'language', 'is_public', 'is_spoiler',
            'helpful_votes', 'total_votes', 'helpfulness_ratio',
            'reviewer_name', 'reviewer_avatar', 'is_verified_reviewer',
            'is_approved', 'moderated_by', 'moderated_at', 'moderation_reason',
            'moderation_analysis', 'created_at', 'updated_at', 'report_summary'
        ]
        read_only_fields = [
            'id', 'user', 'movie', 'helpful_votes', 'total_votes', 'helpfulness_ratio',
            'reviewer_name', 'reviewer_avatar', 'is_verified_reviewer',
            'moderation_analysis', 'created_at', 'updated_at'
        ]

    def get_helpfulness_ratio(self, obj):
        """Calculate helpfulness ratio"""
        return obj.get_helpfulness_ratio()

    def get_moderation_analysis(self, obj):
        """Get moderation analysis for this review"""
        # Only return moderation analysis if it exists (added by moderation_queue)
        if hasattr(obj, 'moderation_analysis'):
            return obj.moderation_analysis
        return None

    def get_report_summary(self, obj):
        """Get report summary for this review"""
        # Only return report summary if it exists (added by reports_for_moderation)
        if hasattr(obj, 'report_summary'):
            return obj.report_summary
        return None

# 🆕 NEW SERIALIZERS FOR NORMALIZED STRUCTURE

class MovieQualityMetricsSerializer(serializers.ModelSerializer):
    """
    Serializer for MovieQualityMetrics model - handles quality assessment data
    """
    overall_quality_rating = serializers.CharField(read_only=True)
    completion_status = serializers.CharField(read_only=True)

    class Meta:
        model = MovieQualityMetrics
        fields = [
            # Core quality scores
            'quality_score', 'content_completeness', 'minimum_quality_met',

            # Quality breakdown
            'basic_info_score', 'visual_assets_score', 'metadata_richness_score', 'rating_validity_score',

            # Quality details
            'quality_issues', 'quality_suggestions', 'last_quality_check',

            # Automation
            'auto_calculated', 'calculation_version',

            # Computed fields
            'overall_quality_rating', 'completion_status',

            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'overall_quality_rating', 'completion_status']


class MovieSchedulingSerializer(serializers.ModelSerializer):
    """
    Serializer for MovieScheduling model - handles scheduling and campaign data
    """
    is_published_now = serializers.BooleanField(read_only=True)
    is_featured_now = serializers.BooleanField(read_only=True)
    has_active_campaign = serializers.BooleanField(read_only=True)
    next_action_info = serializers.SerializerMethodField()

    class Meta:
        model = MovieScheduling
        fields = [
            # Publication scheduling
            'publish_date', 'unpublish_date', 'auto_publish', 'auto_unpublish',

            # Featured scheduling
            'featured_from', 'featured_until', 'auto_feature', 'auto_unfeature',

            # Recurring & advanced
            'recurring_pattern', 'timezone',

            # Status tracking
            'next_scheduled_action', 'next_action_date', 'last_action_executed', 'last_action_date',

            # Campaign info
            'campaign_name', 'campaign_type', 'campaign_priority',

            # Computed fields
            'is_published_now', 'is_featured_now', 'has_active_campaign', 'next_action_info',

            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_published_now', 'is_featured_now', 'has_active_campaign']

    def get_next_action_info(self, obj):
        """Get information about next scheduled action"""
        action, date = obj.get_next_scheduled_action()
        return {
            'action': action,
            'date': date,
            'description': self._get_action_description(action)
        }

    def _get_action_description(self, action):
        """Get human-readable description for action"""
        descriptions = {
            'publish': 'Tự động xuất bản',
            'unpublish': 'Tự động ngừng hiển thị',
            'feature': 'Tự động đánh dấu featured',
            'unfeature': 'Tự động bỏ featured'
        }
        return descriptions.get(action, action)


class AdminControlSerializer(serializers.ModelSerializer):
    """
    Serializer for MovieAdminControl model - handles all admin workflow logic
    """
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    last_modified_by_username = serializers.CharField(source='last_modified_by.username', read_only=True)

    # Computed fields for UI
    can_approve = serializers.SerializerMethodField()
    can_reject = serializers.SerializerMethodField()
    needs_attention = serializers.SerializerMethodField()
    is_featured_active = serializers.SerializerMethodField()

    class Meta:
        model = MovieAdminControl
        fields = [
            # Core workflow fields
            'approval_status', 'approved_by', 'approved_by_username', 'approved_at', 'rejection_reason',
            'visibility_status', 'is_published',
            'admin_featured', 'admin_priority', 'manual_override',
            'target_regions', 'age_rating', 'content_warnings',

            # Audit fields
            'created_by', 'created_by_username', 'last_modified_by', 'last_modified_by_username',
            'created_at', 'updated_at',

            # Computed fields
            'can_approve', 'can_reject', 'needs_attention', 'is_featured_active'
        ]
        read_only_fields = ['created_at', 'updated_at', 'approved_at']

    def get_can_approve(self, obj):
        """Check if movie can be approved"""
        return obj.approval_status in ['PENDING', 'NEEDS_REVIEW']

    def get_can_reject(self, obj):
        """Check if movie can be rejected"""
        return obj.approval_status in ['PENDING', 'APPROVED', 'NEEDS_REVIEW']

    def get_needs_attention(self, obj):
        """Check if admin action is needed"""
        return obj.needs_attention

    def get_is_featured_active(self, obj):
        """Check if featured period is currently active"""
        if not obj.admin_featured:
            return False

        from django.utils import timezone
        now = timezone.now()

        # No scheduling = always active if featured
        if not hasattr(obj.movie, 'scheduling') or not obj.movie.scheduling:
            return True

        # Check scheduling if exists
        scheduling = obj.movie.scheduling
        featured_from = scheduling.featured_from
        featured_until = scheduling.featured_until

        return (
            (not featured_from or featured_from <= now) and
            (not featured_until or featured_until > now)
        )

class AdminMovieListSerializer(OptimizedMovieListSerializer):
    """
    🆕 UPDATED: Lightweight admin serializer using new normalized structure
    """
    # NEW: Nested serializers for normalized data
    admin_control = AdminControlSerializer(read_only=True)
    quality_metrics = MovieQualityMetricsSerializer(read_only=True)
    scheduling = MovieSchedulingSerializer(read_only=True)
    production_metrics = serializers.SerializerMethodField()

    # Keep direct fields for backwards compatibility during transition
    approval_status = serializers.CharField(source='admin_control.approval_status', read_only=True)
    visibility_status = serializers.CharField(source='admin_control.visibility_status', read_only=True)
    admin_featured = serializers.BooleanField(source='admin_control.admin_featured', read_only=True)
    admin_priority = serializers.IntegerField(source='admin_control.admin_priority', read_only=True)

    # Legacy quality fields (with fallbacks to new structure)
    minimum_quality_met = serializers.SerializerMethodField()
    quality_score = serializers.SerializerMethodField()
    content_completeness = serializers.SerializerMethodField()
    combined_rating_score = serializers.DecimalField(max_digits=3, decimal_places=1, read_only=True)

    # Legacy scheduling fields (with fallbacks to new structure)
    publish_date = serializers.SerializerMethodField()
    unpublish_date = serializers.SerializerMethodField()
    featured_from = serializers.SerializerMethodField()
    featured_until = serializers.SerializerMethodField()

    # Enhanced computed fields
    approval_info = serializers.SerializerMethodField()

    class Meta(OptimizedMovieListSerializer.Meta):
        fields = OptimizedMovieListSerializer.Meta.fields + [
            # NEW: Nested normalized structure
            'admin_control', 'quality_metrics', 'scheduling',

            # BACKWARDS COMPATIBILITY: Direct access fields
            'approval_status', 'visibility_status', 'admin_featured', 'admin_priority',

            # LEGACY: With smart fallbacks to normalized structure
            'minimum_quality_met', 'quality_score', 'content_completeness',
            'publish_date', 'unpublish_date', 'featured_from', 'featured_until',
            'combined_rating_score',

            # Computed fields
            'approval_info', 'production_metrics'
        ]

    # Smart getters with fallbacks to normalized structure
    def get_minimum_quality_met(self, obj):
        """Get minimum_quality_met with fallback to normalized structure"""
        if hasattr(obj, 'quality_metrics') and obj.quality_metrics:
            return obj.quality_metrics.minimum_quality_met
        return getattr(obj, 'minimum_quality_met', True)

    def get_quality_score(self, obj):
        """Get quality_score with fallback to normalized structure"""
        if hasattr(obj, 'quality_metrics') and obj.quality_metrics:
            return obj.quality_metrics.quality_score
        return getattr(obj, 'quality_score', None)

    def get_content_completeness(self, obj):
        """Get content_completeness with fallback to normalized structure"""
        if hasattr(obj, 'quality_metrics') and obj.quality_metrics:
            return obj.quality_metrics.content_completeness
        return getattr(obj, 'content_completeness', 0)

    def get_publish_date(self, obj):
        """Get publish_date with fallback to normalized structure"""
        if hasattr(obj, 'scheduling') and obj.scheduling:
            return obj.scheduling.publish_date
        return getattr(obj, 'publish_date', None)

    def get_unpublish_date(self, obj):
        """Get unpublish_date with fallback to normalized structure"""
        if hasattr(obj, 'scheduling') and obj.scheduling:
            return obj.scheduling.unpublish_date
        return getattr(obj, 'unpublish_date', None)

    def get_featured_from(self, obj):
        """Get featured_from with fallback to normalized structure"""
        if hasattr(obj, 'scheduling') and obj.scheduling:
            return obj.scheduling.featured_from
        return getattr(obj, 'featured_from', None)

    def get_featured_until(self, obj):
        """Get featured_until with fallback to normalized structure"""
        if hasattr(obj, 'scheduling') and obj.scheduling:
            return obj.scheduling.featured_until
        return getattr(obj, 'featured_until', None)

    def get_approval_info(self, obj):
        """Enhanced approval information using new structure"""
        if not hasattr(obj, 'admin_control') or not obj.admin_control:
            return {
                'status': 'PENDING',
                'can_approve': True,
                'can_reject': False,
                'requires_review': False
            }

        admin_control = obj.admin_control
        return {
            'status': admin_control.approval_status,
            'can_approve': admin_control.approval_status in ['PENDING', 'NEEDS_REVIEW'],
            'can_reject': admin_control.approval_status in ['PENDING', 'APPROVED', 'NEEDS_REVIEW'],
            'requires_review': admin_control.approval_status == 'NEEDS_REVIEW',
            'approved_by': admin_control.approved_by.username if admin_control.approved_by else None,
            'approved_at': admin_control.approved_at
        }

    def get_production_metrics(self, obj):
        """Enhanced production metrics using ProductionMetrics model"""
        # Initialize with defaults
        base_metrics = {
            'homepage_views': 0,
            'detail_page_views': 0,
            'trailer_plays': 0,
            # 'search_appearances': 0,
            'click_through_rate': 0.0,
            'engagement_rate': 0.0,
            'performance_score': 0.0,
            'trending_score': 0.0,
            'trending_category': 'stable',
            'trailer_completion_rate': 0.0,
            'last_featured_date': None,
            'last_calculated_at': None,
            # 'total_featured_days': 0,
            'review_count': 0,
            'average_user_rating': None,
            'positive_review_ratio': 0.0
        }

        # Use ProductionMetrics if available
        if hasattr(obj, 'production_metrics') and obj.production_metrics:
            metrics = obj.production_metrics
            base_metrics.update({
                'homepage_views': metrics.homepage_views,
                'detail_page_views': metrics.detail_page_views,
                'trailer_plays': metrics.trailer_plays,
                'click_through_rate': float(metrics.click_through_rate),
                'engagement_rate': float(metrics.engagement_rate),
                'performance_score': float(metrics.performance_score),
                'trending_score': float(metrics.trending_score),
                'trending_category': metrics.trending_category,
                'trailer_completion_rate': float(metrics.trailer_completion_rate),
                'last_featured_date': metrics.last_featured_date,
                'last_calculated_at': metrics.last_calculated_at,
                # 'total_featured_days': metrics.total_featured_days,
                'review_count': metrics.review_count,
                'average_user_rating': float(metrics.average_user_rating) if metrics.average_user_rating else None,
                # 'positive_review_ratio': float(metrics.positive_review_ratio)
            })
        else:
            # Fallback: use combined_rating_score as performance_score
            if hasattr(obj, 'combined_rating_score') and obj.combined_rating_score:
                base_metrics['performance_score'] = float(obj.combined_rating_score)

        return base_metrics

class AdminMovieSerializer(MovieDetailSerializer):
    """
    Admin-specific serializer with production control fields
    """
    production_metrics = serializers.SerializerMethodField()
    approval_info = serializers.SerializerMethodField()
    visibility_info = serializers.SerializerMethodField()
    quality_metrics = serializers.SerializerMethodField()
    admin_controls = serializers.SerializerMethodField()
    content_status = serializers.SerializerMethodField()

    class Meta(MovieDetailSerializer.Meta):
        fields = MovieDetailSerializer.Meta.fields + [
            # Production control fields
            'is_published', 'visibility_status', 'publish_date', 'unpublish_date',
            'featured_from', 'featured_until', 'admin_featured', 'admin_priority',
            'manual_override', 'approval_status', 'approved_by', 'approved_at',
            'target_regions', 'age_rating', 'content_warnings',
            'quality_score', 'content_completeness', 'minimum_quality_met',

            # Computed fields
            'production_metrics', 'approval_info', 'visibility_info',
            'quality_metrics', 'admin_controls', 'content_status'
        ]

    def get_production_metrics(self, obj):
        """Get production performance metrics"""
        try:
            if hasattr(obj, 'production_metrics'):
                metrics = obj.production_metrics
                return {
                    'homepage_views': metrics.homepage_views,
                    'detail_page_views': metrics.detail_page_views,
                    'trailer_plays': metrics.trailer_plays,
                    'click_through_rate': float(metrics.click_through_rate) if metrics.click_through_rate else 0,
                    'engagement_rate': float(metrics.engagement_rate) if metrics.engagement_rate else 0,
                    'performance_score': float(metrics.performance_score) if metrics.performance_score else 0,
                    'trending_score': float(metrics.trending_score) if metrics.trending_score else 0,
                    'trending_category': metrics.trending_category,
                    'trailer_completion_rate': float(metrics.trailer_completion_rate) if metrics.trailer_completion_rate else 0,
                    'last_featured_date': metrics.last_featured_date,
                    'last_calculated_at': metrics.last_calculated_at
                }
        except:
            pass
        return {
            'homepage_views': 0,
            'detail_page_views': 0,
            'trailer_plays': 0,
            'click_through_rate': 0,
            'engagement_rate': 0,
            'performance_score': 0,
            'trending_score': 0,
            'trending_category': 'stable',
            'trailer_completion_rate': 0,
            'last_featured_date': None,
            'last_calculated_at': None
        }

    def get_approval_info(self, obj):
        """Get approval workflow information"""
        return {
            'status': obj.approval_status,
            'approved_by': obj.approved_by.username if obj.approved_by else None,
            'approved_at': obj.approved_at,
            'can_approve': obj.approval_status in ['PENDING', 'NEEDS_REVIEW'],
            'can_reject': obj.approval_status in ['PENDING', 'APPROVED'],
            'rejection_reason': obj.manual_override.get('rejection_reason') if obj.manual_override else None
        }

    def get_visibility_info(self, obj):
        """Get visibility settings and status"""
        from django.utils import timezone
        now = timezone.now()

        # Check if currently visible
        is_currently_visible = (
            obj.is_published and
            obj.visibility_status == 'PUBLISHED' and
            obj.approval_status == 'APPROVED' and
            obj.minimum_quality_met and
            (not obj.publish_date or obj.publish_date <= now) and
            (not obj.unpublish_date or obj.unpublish_date > now)
        )

        # Check if scheduled
        is_scheduled = (
            obj.visibility_status == 'SCHEDULED' and
            obj.publish_date and obj.publish_date > now
        )

        return {
            'status': obj.visibility_status,
            'is_published': obj.is_published,
            'is_currently_visible': is_currently_visible,
            'is_scheduled': is_scheduled,
            'publish_date': obj.publish_date,
            'unpublish_date': obj.unpublish_date,
            'target_regions': obj.target_regions,
            'age_rating': obj.age_rating,
            'content_warnings': obj.content_warnings
        }

    def get_quality_metrics(self, obj):
        """Get content quality information"""
        return {
            'quality_score': float(obj.quality_score) if obj.quality_score else None,
            'content_completeness': float(obj.content_completeness) if obj.content_completeness else 0,
            'minimum_quality_met': obj.minimum_quality_met,
            'has_poster': bool(obj.poster_url),
            'has_backdrop': bool(obj.backdrop_url),
            'has_overview': bool(obj.overview_en or obj.overview_vi),
            'has_trailers': obj.trailers.filter(type='TRAILER').exists(),
            'has_cast': obj.cast.exists(),
            'has_ratings': obj.ratings.exists()
        }

    def get_admin_controls(self, obj):
        """Get admin control settings"""
        from django.utils import timezone
        now = timezone.now()

        # Check if featured period is active
        is_featured_active = (
            obj.admin_featured and
            (not obj.featured_from or obj.featured_from <= now) and
            (not obj.featured_until or obj.featured_until > now)
        )

        return {
            'admin_featured': obj.admin_featured,
            'admin_priority': obj.admin_priority,
            'is_featured_active': is_featured_active,
            'featured_from': obj.featured_from,
            'featured_until': obj.featured_until,
            'manual_override': obj.manual_override or {},
            'can_feature': not obj.admin_featured,
            'can_unfeature': obj.admin_featured,
            'can_change_priority': obj.admin_featured
        }

    def get_content_status(self, obj):
        """Get overall content status summary"""
        issues = []

        # Quality issues
        if not obj.minimum_quality_met:
            issues.append('Quality standards not met')
        if not obj.poster_url:
            issues.append('Missing poster')
        if not (obj.overview_en or obj.overview_vi):
            issues.append('Missing overview')
        if not obj.trailers.filter(type='TRAILER').exists():
            issues.append('Missing trailers')

        # Approval issues
        if obj.approval_status == 'PENDING':
            issues.append('Awaiting approval')
        elif obj.approval_status == 'REJECTED':
            issues.append('Rejected')
        elif obj.approval_status == 'NEEDS_REVIEW':
            issues.append('Needs review')

        # Visibility issues
        if not obj.is_published:
            issues.append('Not published')
        if obj.visibility_status != 'PUBLISHED':
            issues.append(f'Visibility: {obj.visibility_status}')

        return {
            'overall_status': 'ready' if not issues else 'issues',
            'issues': issues,
            'issue_count': len(issues),
            'production_ready': (
                obj.is_published and
                obj.visibility_status == 'PUBLISHED' and
                obj.approval_status == 'APPROVED' and
                obj.minimum_quality_met
            )
        }

class AdminDashboardMovieSerializer(serializers.ModelSerializer):
    """
    Ultra-lightweight serializer for dashboard overview with minimal queries
    """
    rating_score = serializers.DecimalField(max_digits=3, decimal_places=1, source='combined_rating_score', read_only=True)
    approval_by_username = serializers.CharField(source='approved_by.username', read_only=True)

    # Add minimal versions of fields that frontend expects
    approval_info = serializers.SerializerMethodField()
    production_metrics = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            'id', 'slug', 'title', 'title_en', 'poster_url', 'release_date',
            'approval_status', 'visibility_status', 'admin_featured', 'admin_priority',
            'minimum_quality_met', 'quality_score', 'content_completeness',
            'is_published', 'rating_score', 'approval_by_username', 'created_at',
            'approval_info', 'production_metrics'
        ]

    def get_approval_info(self, obj):
        """Minimal approval info for dashboard"""
        return {
            'status': obj.approval_status,
            'can_approve': obj.approval_status in ['PENDING', 'NEEDS_REVIEW'],
            'can_reject': obj.approval_status in ['PENDING', 'APPROVED'],
        }

    def get_production_metrics(self, obj):
        """Minimal production metrics for dashboard"""
        return {
            'homepage_views': 0,  # Placeholder - avoid additional queries
            'performance_score': 0,
        }

class UserInteractionSerializer(serializers.ModelSerializer):
    """
    Serializer for UserInteraction model
    Dùng cho analytics và reporting
    """
    user_identifier = serializers.CharField(read_only=True)
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    movie_poster = serializers.URLField(source='movie.poster_url', read_only=True)

    class Meta:
        model = UserInteraction
        fields = [
            'id', 'movie', 'movie_title', 'movie_poster', 'user', 'user_identifier',
            'session_id', 'action', 'interaction_type', 'page_url', 'referrer',
            'user_agent', 'screen_resolution', 'viewport_size', 'metadata',
            'timestamp', 'processed_at', 'duration_seconds', 'is_unique_session'
        ]
        read_only_fields = ['id', 'timestamp', 'processed_at', 'user_identifier', 'movie_title', 'movie_poster']

class UserInteractionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating UserInteraction
    Dùng cho API endpoints
    """

    class Meta:
        model = UserInteraction
        fields = [
            'movie', 'user', 'session_id', 'action', 'interaction_type',
            'page_url', 'referrer', 'user_agent', 'screen_resolution',
            'viewport_size', 'metadata', 'duration_seconds'
        ]

    def validate(self, data):
        """Validate interaction data"""
        # Ensure either user or session_id is provided
        if not data.get('user') and not data.get('session_id'):
            raise serializers.ValidationError("Either user or session_id must be provided")

        # Validate action
        if not data.get('action'):
            raise serializers.ValidationError("Action is required")

        return data

class UserInteractionStatsSerializer(serializers.Serializer):
    """
    Serializer for user interaction statistics
    """
    total_interactions = serializers.IntegerField()
    unique_users = serializers.IntegerField()
    unique_sessions = serializers.IntegerField()
    top_actions = serializers.ListField(child=serializers.DictField())
    hourly_distribution = serializers.ListField(child=serializers.DictField())
    daily_trends = serializers.ListField(child=serializers.DictField())
    device_breakdown = serializers.DictField()
    avg_session_duration = serializers.FloatField()

class MovieInteractionSummarySerializer(serializers.Serializer):
    """
    Serializer for movie interaction summary
    """
    movie_id = serializers.IntegerField()
    movie_title = serializers.CharField()
    total_interactions = serializers.IntegerField()
    unique_users = serializers.IntegerField()
    homepage_views = serializers.IntegerField()
    detail_views = serializers.IntegerField()
    favorites = serializers.IntegerField()
    shares = serializers.IntegerField()
    avg_engagement_rate = serializers.FloatField()
    trending_score = serializers.FloatField()
    last_activity = serializers.DateTimeField()
