from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Movie
import logging

logger = logging.getLogger(__name__)

@registry.register_document
class MovieDocument(Document):
    # Text fields with proper analyzers
    title = fields.TextField(
        analyzer='standard',
        fields={'raw': fields.KeywordField()}
    )
    title_en = fields.TextField(
        analyzer='english',
        fields={'raw': fields.KeywordField()}
    )
    title_vi = fields.TextField(
        analyzer='standard',
        fields={'raw': fields.KeywordField()}
    )
    original_title = fields.TextField(
        analyzer='standard',
        fields={'raw': fields.KeywordField()}
    )
    overview_en = fields.TextField(
        analyzer='english',
        fields={'raw': fields.KeywordField()}
    )
    overview_vi = fields.TextField(
        analyzer='vietnamese_analyzer',
        fields={'raw': fields.KeywordField()}
    )

    # Metadata fields
    release_date = fields.DateField()
    runtime = fields.IntegerField()
    status = fields.KeywordField()

    # Rating fields - using FloatField to match existing mapping
    vote_average = fields.FloatField()
    vote_count = fields.IntegerField()
    popularity = fields.FloatField()
    cached_imdb_rating = fields.FloatField()
    cached_tmdb_rating = fields.FloatField()
    cached_imdb_votes = fields.IntegerField()
    cached_tmdb_votes = fields.IntegerField()
    combined_rating_score = fields.FloatField()

    # Boolean flags
    is_adult = fields.BooleanField()
    is_popular = fields.BooleanField()
    is_top_rated = fields.BooleanField()
    is_upcoming = fields.BooleanField()

    # URLs
    poster_url = fields.TextField()
    backdrop_url = fields.TextField()

    # Additional fields for better search results
    trailer_count = fields.IntegerField()
    genre_count = fields.IntegerField()
    data_completeness_score = fields.IntegerField()

    # Relationship fields
    genres = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': fields.KeywordField(),
        'language': fields.KeywordField()
    })
    production_countries = fields.KeywordField(multi=True)

    # Trailers field for consistency
    trailers = fields.NestedField(properties={
        'title': fields.TextField(),
        'youtube_key': fields.KeywordField(),
        'type': fields.KeywordField()
    })

    class Index:
        name = 'movies'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'vietnamese_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase']
                    }
                }
            }
        }

    class Django:
        model = Movie
        fields = [
            'id',
            'slug',  # Add slug field
        ]

    def prepare_genres(self, instance):
        """Prepare data for genres field"""
        try:
            genres = instance.genres.all()
            return [{'id': genre.id, 'name': genre.name, 'language': genre.language}
                    for genre in genres]
        except Exception as e:
            logger.warning(f"Error preparing genres for movie {instance.id}: {e}")
            return []

    def prepare_trailers(self, instance):
        """Prepare data for trailers field"""
        try:
            trailers = instance.trailers.filter(type='TRAILER')
            return [{'title': trailer.title, 'youtube_key': trailer.youtube_key, 'type': trailer.type}
                    for trailer in trailers]
        except Exception as e:
            logger.warning(f"Error preparing trailers for movie {instance.id}: {e}")
            return []

    def prepare_production_countries(self, instance):
        """Prepare data for production_countries field"""
        try:
            if hasattr(instance, 'moviemetadata') and instance.moviemetadata:
                countries = instance.moviemetadata.production_countries
                if countries and isinstance(countries, list):
                    return [country.get('iso_3166_1', '') for country in countries]
            return []
        except Exception as e:
            logger.warning(f"Error preparing production countries for movie {instance.id}: {e}")
            return []

    def prepare_vote_count(self, instance):
        """Prepare data for vote_count field"""
        try:
            return instance.cached_imdb_votes or instance.cached_tmdb_votes or 0
        except Exception as e:
            logger.warning(f"Error preparing vote_count for movie {instance.id}: {e}")
            return 0

    def prepare_popularity(self, instance):
        """Prepare data for popularity field"""
        try:
            return instance.combined_rating_score or 0
        except Exception as e:
            logger.warning(f"Error preparing popularity for movie {instance.id}: {e}")
            return 0

    def prepare_trailer_count(self, instance):
        """Count trailers for data completeness scoring"""
        try:
            return instance.trailers.filter(type='TRAILER').count()
        except Exception as e:
            logger.warning(f"Error counting trailers for movie {instance.id}: {e}")
            return 0

    def prepare_genre_count(self, instance):
        """Count genres for data completeness scoring"""
        try:
            return instance.genres.count()
        except Exception as e:
            logger.warning(f"Error counting genres for movie {instance.id}: {e}")
            return 0

    def prepare_data_completeness_score(self, instance):
        """Calculate data completeness score"""
        try:
            score = 0

            # Essential fields
            if instance.poster_url and instance.poster_url.strip():
                score += 2
            if instance.backdrop_url and instance.backdrop_url.strip():
                score += 1
            if instance.overview_en and instance.overview_en.strip():
                score += 2
            if instance.overview_vi and instance.overview_vi.strip():
                score += 1

            # Rating data
            if instance.cached_imdb_rating:
                score += 3
            if instance.cached_tmdb_rating:
                score += 2

            # Additional content
            if instance.trailers.filter(type='TRAILER').exists():
                score += 3
            if instance.genres.exists():
                score += 1

            return score
        except Exception as e:
            logger.warning(f"Error calculating completeness score for movie {instance.id}: {e}")
            return 0

    def prepare_title(self, instance):
        """Ensure title is not empty"""
        return instance.title or instance.original_title or f"Movie {instance.id}"

    def prepare_cached_imdb_rating(self, instance):
        """Safely prepare IMDB rating"""
        try:
            return float(instance.cached_imdb_rating) if instance.cached_imdb_rating else None
        except (ValueError, TypeError):
            return None

    def prepare_cached_tmdb_rating(self, instance):
        """Safely prepare TMDB rating"""
        try:
            return float(instance.cached_tmdb_rating) if instance.cached_tmdb_rating else None
        except (ValueError, TypeError):
            return None

    def prepare_combined_rating_score(self, instance):
        """Safely prepare combined rating score"""
        try:
            return float(instance.combined_rating_score) if instance.combined_rating_score else None
        except (ValueError, TypeError):
            return None
