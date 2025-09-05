from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Movie, MovieQualityMetrics, MovieScheduling, MovieAdminControl, ProductionMetrics
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
        analyzer='vietnamese_analyzer_keep_diacritic',
        fields={'raw': fields.KeywordField()}
    )
    title_vi_no_diacritic = fields.TextField(
        analyzer='vietnamese_analyzer_no_diacritic',
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
        analyzer='vietnamese_analyzer_keep_diacritic',
        fields={'raw': fields.KeywordField()}
    )

    # Metadata fields
    release_date = fields.DateField()
    runtime = fields.IntegerField()
    status = fields.KeywordField()
    slug = fields.KeywordField()
    created_at = fields.DateField()

    # Rating fields
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
    is_published = fields.BooleanField()
    minimum_quality_met = fields.BooleanField()

    # URLs and media
    poster_url = fields.TextField()
    backdrop_url = fields.TextField()

    # Additional fields for better search results
    trailer_count = fields.IntegerField()
    genre_count = fields.IntegerField()
    data_completeness_score = fields.IntegerField()

    # Status fields
    approval_status = fields.KeywordField()
    visibility_status = fields.KeywordField()

    # LEGACY Scheduling fields (for backward compatibility)
    publish_date = fields.DateField()
    unpublish_date = fields.DateField()
    featured_from = fields.DateField()
    featured_until = fields.DateField()

    # Admin fields
    admin_featured = fields.BooleanField()
    admin_priority = fields.IntegerField()

    # NEW: Quality Metrics Fields (from MovieQualityMetrics)
    quality_score = fields.FloatField()
    content_completeness = fields.FloatField()
    basic_info_score = fields.FloatField()
    visual_assets_score = fields.FloatField()
    metadata_richness_score = fields.FloatField()
    rating_validity_score = fields.FloatField()
    quality_issues = fields.TextField()  # JSON as text for search
    quality_suggestions = fields.TextField()  # JSON as text for search
    last_quality_check = fields.DateField()
    auto_calculated = fields.BooleanField()
    calculation_version = fields.KeywordField()

    # Quality metrics for filtering and sorting
    overall_quality_rating = fields.KeywordField()  # Excellent, Good, Fair, Poor
    completion_status = fields.KeywordField()  # Complete, Nearly Complete, Partial, Incomplete

    # NEW: Scheduling Fields (from MovieScheduling)
    scheduling_publish_date = fields.DateField()
    scheduling_unpublish_date = fields.DateField()
    scheduling_featured_from = fields.DateField()
    scheduling_featured_until = fields.DateField()
    auto_publish = fields.BooleanField()
    auto_unpublish = fields.BooleanField()
    auto_feature = fields.BooleanField()
    auto_unfeature = fields.BooleanField()

    # Campaign fields
    campaign_name = fields.TextField(
        analyzer='standard',
        fields={'raw': fields.KeywordField()}
    )
    campaign_type = fields.TextField(
        analyzer='standard',
        fields={'raw': fields.KeywordField()}
    )
    campaign_priority = fields.IntegerField()
    campaign_budget = fields.FloatField()
    campaign_start_date = fields.DateField()
    campaign_end_date = fields.DateField()

    # Scheduling status
    is_published_now = fields.BooleanField()
    is_featured_now = fields.BooleanField()
    is_scheduled_for_publish = fields.BooleanField()
    is_scheduled_for_feature = fields.BooleanField()

    # Next action tracking
    next_action_date = fields.DateField()
    next_scheduled_action = fields.KeywordField()

    # 📈 NEW: Production Metrics Fields (for enhanced search scoring)
    performance_score = fields.FloatField()
    trending_score = fields.FloatField()
    engagement_rate = fields.FloatField()
    click_through_rate = fields.FloatField()
    homepage_views = fields.IntegerField()
    detail_page_views = fields.IntegerField()
    user_favorites_count = fields.IntegerField()
    user_watchlist_count = fields.IntegerField()

    # Trending category
    trending_category = fields.KeywordField()  # viral, hot, rising, stable

    # Relationship fields
    genres = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': fields.KeywordField(),
        'language': fields.KeywordField()
    })
    production_countries = fields.KeywordField(multi=True)

    # Trailers field
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
                    'vietnamese_analyzer_keep_diacritic': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': ['lowercase', 'word_delimiter_graph']
                },
                'vietnamese_analyzer_no_diacritic': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': ['lowercase', 'asciifolding', 'word_delimiter_graph']
                },
                'vietnamese_analyzer': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': ['lowercase', 'asciifolding', 'word_delimiter_graph']
                }
                }
            }
        }

    class Django:
        model = Movie
        fields = [
            'id'
        ]
        related_models = [MovieQualityMetrics, MovieScheduling, MovieAdminControl, ProductionMetrics]

    def get_instances_from_related(self, related_instance):
        """Update document when related models change"""
        if isinstance(related_instance, (MovieQualityMetrics, MovieScheduling, MovieAdminControl, ProductionMetrics)):
            return related_instance.movie

    # 📊 QUALITY METRICS PREPARE METHODS
    def prepare_quality_score(self, instance):
        """Prepare quality score from MovieQualityMetrics"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                return float(instance.quality_metrics.quality_score or 0)
            return 0.0
        except Exception as e:
            logger.warning(f"Error preparing quality_score for movie {instance.id}: {e}")
            return 0.0

    def prepare_content_completeness(self, instance):
        """Prepare content completeness from MovieQualityMetrics"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                return float(instance.quality_metrics.content_completeness or 0)
            return 0.0
        except Exception as e:
            logger.warning(f"Error preparing content_completeness for movie {instance.id}: {e}")
            return 0.0

    def prepare_basic_info_score(self, instance):
        """Prepare basic info score from MovieQualityMetrics"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                return float(instance.quality_metrics.basic_info_score or 0)
            return 0.0
        except Exception as e:
            logger.warning(f"Error preparing basic_info_score for movie {instance.id}: {e}")
            return 0.0

    def prepare_visual_assets_score(self, instance):
        """Prepare visual assets score from MovieQualityMetrics"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                return float(instance.quality_metrics.visual_assets_score or 0)
            return 0.0
        except Exception as e:
            logger.warning(f"Error preparing visual_assets_score for movie {instance.id}: {e}")
            return 0.0

    def prepare_metadata_richness_score(self, instance):
        """Prepare metadata richness score from MovieQualityMetrics"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                return float(instance.quality_metrics.metadata_richness_score or 0)
            return 0.0
        except Exception as e:
            logger.warning(f"Error preparing metadata_richness_score for movie {instance.id}: {e}")
            return 0.0

    def prepare_rating_validity_score(self, instance):
        """Prepare rating validity score from MovieQualityMetrics"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                return float(instance.quality_metrics.rating_validity_score or 0)
            return 0.0
        except Exception as e:
            logger.warning(f"Error preparing rating_validity_score for movie {instance.id}: {e}")
            return 0.0

    def prepare_quality_issues(self, instance):
        """Prepare quality issues as searchable text"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                issues = instance.quality_metrics.quality_issues
                if issues and isinstance(issues, list):
                    return ' '.join(issues)
            return ''
        except Exception as e:
            logger.warning(f"Error preparing quality_issues for movie {instance.id}: {e}")
            return ''

    def prepare_quality_suggestions(self, instance):
        """Prepare quality suggestions as searchable text"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                suggestions = instance.quality_metrics.quality_suggestions
                if suggestions and isinstance(suggestions, list):
                    return ' '.join(suggestions)
            return ''
        except Exception as e:
            logger.warning(f"Error preparing quality_suggestions for movie {instance.id}: {e}")
            return ''

    def prepare_last_quality_check(self, instance):
        """Prepare last quality check date"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                return instance.quality_metrics.last_quality_check
            return None
        except Exception as e:
            logger.warning(f"Error preparing last_quality_check for movie {instance.id}: {e}")
            return None

    def prepare_auto_calculated(self, instance):
        """Prepare auto calculated flag"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                return instance.quality_metrics.auto_calculated
            return False
        except Exception as e:
            logger.warning(f"Error preparing auto_calculated for movie {instance.id}: {e}")
            return False

    def prepare_calculation_version(self, instance):
        """Prepare calculation version"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                return instance.quality_metrics.calculation_version
            return '1.0'
        except Exception as e:
            logger.warning(f"Error preparing calculation_version for movie {instance.id}: {e}")
            return '1.0'

    def prepare_overall_quality_rating(self, instance):
        """Prepare overall quality rating category"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                return instance.quality_metrics.overall_quality_rating
            return 'Not Assessed'
        except Exception as e:
            logger.warning(f"Error preparing overall_quality_rating for movie {instance.id}: {e}")
            return 'Not Assessed'

    def prepare_completion_status(self, instance):
        """Prepare completion status category"""
        try:
            if hasattr(instance, 'quality_metrics') and instance.quality_metrics:
                return instance.quality_metrics.completion_status
            return 'Incomplete'
        except Exception as e:
            logger.warning(f"Error preparing completion_status for movie {instance.id}: {e}")
            return 'Incomplete'

    # 📅 SCHEDULING PREPARE METHODS
    def prepare_scheduling_publish_date(self, instance):
        """Prepare publish date from MovieScheduling"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.publish_date
            return None
        except Exception as e:
            logger.warning(f"Error preparing scheduling_publish_date for movie {instance.id}: {e}")
            return None

    def prepare_scheduling_unpublish_date(self, instance):
        """Prepare unpublish date from MovieScheduling"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.unpublish_date
            return None
        except Exception as e:
            logger.warning(f"Error preparing scheduling_unpublish_date for movie {instance.id}: {e}")
            return None

    def prepare_scheduling_featured_from(self, instance):
        """Prepare featured from date from MovieScheduling"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.featured_from
            return None
        except Exception as e:
            logger.warning(f"Error preparing scheduling_featured_from for movie {instance.id}: {e}")
            return None

    def prepare_scheduling_featured_until(self, instance):
        """Prepare featured until date from MovieScheduling"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.featured_until
            return None
        except Exception as e:
            logger.warning(f"Error preparing scheduling_featured_until for movie {instance.id}: {e}")
            return None

    def prepare_auto_publish(self, instance):
        """Prepare auto publish flag"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.auto_publish
            return False
        except Exception as e:
            logger.warning(f"Error preparing auto_publish for movie {instance.id}: {e}")
            return False

    def prepare_auto_unpublish(self, instance):
        """Prepare auto unpublish flag"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.auto_unpublish
            return False
        except Exception as e:
            logger.warning(f"Error preparing auto_unpublish for movie {instance.id}: {e}")
            return False

    def prepare_auto_feature(self, instance):
        """Prepare auto feature flag"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.auto_feature
            return False
        except Exception as e:
            logger.warning(f"Error preparing auto_feature for movie {instance.id}: {e}")
            return False

    def prepare_auto_unfeature(self, instance):
        """Prepare auto unfeature flag"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.auto_unfeature
            return False
        except Exception as e:
            logger.warning(f"Error preparing auto_unfeature for movie {instance.id}: {e}")
            return False

    def prepare_campaign_name(self, instance):
        """Prepare campaign name"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.campaign_name or ''
            return ''
        except Exception as e:
            logger.warning(f"Error preparing campaign_name for movie {instance.id}: {e}")
            return ''

    def prepare_campaign_type(self, instance):
        """Prepare campaign type"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.campaign_type or ''
            return ''
        except Exception as e:
            logger.warning(f"Error preparing campaign_type for movie {instance.id}: {e}")
            return ''

    def prepare_campaign_priority(self, instance):
        """Prepare campaign priority"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.campaign_priority or 0
            return 0
        except Exception as e:
            logger.warning(f"Error preparing campaign_priority for movie {instance.id}: {e}")
            return 0

    def prepare_campaign_budget(self, instance):
        """Prepare campaign budget - NOT IMPLEMENTED IN MODEL YET"""
        try:
            # Return 0 as fallback since campaign_budget field doesn't exist in MovieScheduling model yet
            return 0.0
        except Exception as e:
            logger.warning(f"Error preparing campaign_budget for movie {instance.id}: {e}")
            return 0.0

    def prepare_campaign_start_date(self, instance):
        """Prepare campaign start date - NOT IMPLEMENTED IN MODEL YET"""
        try:
            # Return None as fallback since campaign_start_date field doesn't exist in MovieScheduling model yet
            return None
        except Exception as e:
            logger.warning(f"Error preparing campaign_start_date for movie {instance.id}: {e}")
            return None

    def prepare_campaign_end_date(self, instance):
        """Prepare campaign end date - NOT IMPLEMENTED IN MODEL YET"""
        try:
            # Return None as fallback since campaign_end_date field doesn't exist in MovieScheduling model yet
            return None
        except Exception as e:
            logger.warning(f"Error preparing campaign_end_date for movie {instance.id}: {e}")
            return None

    def prepare_is_published_now(self, instance):
        """Prepare is published now status"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.is_published_now
            return instance.is_published if hasattr(instance, 'is_published') else True
        except Exception as e:
            logger.warning(f"Error preparing is_published_now for movie {instance.id}: {e}")
            return True

    def prepare_is_featured_now(self, instance):
        """Prepare is featured now status"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.is_featured_now
            return instance.admin_featured if hasattr(instance, 'admin_featured') else False
        except Exception as e:
            logger.warning(f"Error preparing is_featured_now for movie {instance.id}: {e}")
            return False

    def prepare_is_scheduled_for_publish(self, instance):
        """Prepare is scheduled for publish status"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                # Check if there's a future publish date with auto_publish enabled
                from django.utils import timezone
                now = timezone.now()
                if instance.scheduling.auto_publish and instance.scheduling.publish_date:
                    # Ensure publish_date is timezone-aware
                    publish_date = timezone.localtime(instance.scheduling.publish_date) if timezone.is_aware(instance.scheduling.publish_date) else timezone.make_aware(instance.scheduling.publish_date)
                    return publish_date > now
            return False
        except Exception as e:
            logger.warning(f"Error preparing is_scheduled_for_publish for movie {instance.id}: {e}")
            return False

    def prepare_is_scheduled_for_feature(self, instance):
        """Prepare is scheduled for feature status"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                # Check if there's a future feature date with auto_feature enabled
                from django.utils import timezone
                now = timezone.now()
                if instance.scheduling.auto_feature and instance.scheduling.featured_from:
                    # Ensure featured_from is timezone-aware
                    featured_from = timezone.localtime(instance.scheduling.featured_from) if timezone.is_aware(instance.scheduling.featured_from) else timezone.make_aware(instance.scheduling.featured_from)
                    return featured_from > now
            return False
        except Exception as e:
            logger.warning(f"Error preparing is_scheduled_for_feature for movie {instance.id}: {e}")
            return False

    def prepare_next_action_date(self, instance):
        """Prepare next action date"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.next_action_date
            return None
        except Exception as e:
            logger.warning(f"Error preparing next_action_date for movie {instance.id}: {e}")
            return None

    def prepare_next_scheduled_action(self, instance):
        """Prepare next scheduled action"""
        try:
            if hasattr(instance, 'scheduling') and instance.scheduling:
                return instance.scheduling.next_scheduled_action or ''
            return ''
        except Exception as e:
            logger.warning(f"Error preparing next_scheduled_action for movie {instance.id}: {e}")
            return ''

    # 📈 PRODUCTION METRICS PREPARE METHODS
    def prepare_performance_score(self, instance):
        """Prepare performance score from ProductionMetrics"""
        try:
            if hasattr(instance, 'production_metrics') and instance.production_metrics:
                return float(instance.production_metrics.performance_score or 0)
            return 0.0
        except Exception as e:
            logger.warning(f"Error preparing performance_score for movie {instance.id}: {e}")
            return 0.0

    def prepare_trending_score(self, instance):
        """Prepare trending score from ProductionMetrics"""
        try:
            if hasattr(instance, 'production_metrics') and instance.production_metrics:
                return float(instance.production_metrics.trending_score or 0)
            return 0.0
        except Exception as e:
            logger.warning(f"Error preparing trending_score for movie {instance.id}: {e}")
            return 0.0

    def prepare_engagement_rate(self, instance):
        """Prepare engagement rate from ProductionMetrics"""
        try:
            if hasattr(instance, 'production_metrics') and instance.production_metrics:
                return float(instance.production_metrics.engagement_rate or 0)
            return 0.0
        except Exception as e:
            logger.warning(f"Error preparing engagement_rate for movie {instance.id}: {e}")
            return 0.0

    def prepare_click_through_rate(self, instance):
        """Prepare click through rate from ProductionMetrics"""
        try:
            if hasattr(instance, 'production_metrics') and instance.production_metrics:
                return float(instance.production_metrics.click_through_rate or 0)
            return 0.0
        except Exception as e:
            logger.warning(f"Error preparing click_through_rate for movie {instance.id}: {e}")
            return 0.0

    def prepare_homepage_views(self, instance):
        """Prepare homepage views from ProductionMetrics"""
        try:
            if hasattr(instance, 'production_metrics') and instance.production_metrics:
                return instance.production_metrics.homepage_views or 0
            return 0
        except Exception as e:
            logger.warning(f"Error preparing homepage_views for movie {instance.id}: {e}")
            return 0

    def prepare_detail_page_views(self, instance):
        """Prepare detail page views from ProductionMetrics"""
        try:
            if hasattr(instance, 'production_metrics') and instance.production_metrics:
                return instance.production_metrics.detail_page_views or 0
            return 0
        except Exception as e:
            logger.warning(f"Error preparing detail_page_views for movie {instance.id}: {e}")
            return 0

    def prepare_user_favorites_count(self, instance):
        """Prepare user favorites count from ProductionMetrics"""
        try:
            if hasattr(instance, 'production_metrics') and instance.production_metrics:
                return instance.production_metrics.user_favorites_count or 0
            return 0
        except Exception as e:
            logger.warning(f"Error preparing user_favorites_count for movie {instance.id}: {e}")
            return 0

    def prepare_user_watchlist_count(self, instance):
        """Prepare user watchlist count from ProductionMetrics"""
        try:
            if hasattr(instance, 'production_metrics') and instance.production_metrics:
                return instance.production_metrics.user_watchlist_count or 0
            return 0
        except Exception as e:
            logger.warning(f"Error preparing user_watchlist_count for movie {instance.id}: {e}")
            return 0

    def prepare_trending_category(self, instance):
        """Prepare trending category from ProductionMetrics"""
        try:
            if hasattr(instance, 'production_metrics') and instance.production_metrics:
                return instance.production_metrics.trending_category or 'stable'
            return 'stable'
        except Exception as e:
            logger.warning(f"Error preparing trending_category for movie {instance.id}: {e}")
            return 'stable'

    # EXISTING PREPARE METHODS (preserved for backward compatibility)
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

    def prepare_slug(self, instance):
        """Prepare slug field"""
        return instance.slug if instance.slug else None

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

            # Metadata
            if instance.release_date:
                score += 1
            if instance.runtime and instance.runtime > 0:
                score += 1
            if instance.status and instance.status != 'UNKNOWN':
                score += 1

            # Relationships
            if instance.genres.exists():
                score += 1
            if instance.trailers.exists():
                score += 1

            return score
        except Exception as e:
            logger.warning(f"Error calculating data completeness score for movie {instance.id}: {e}")
            return 0

    def prepare_title(self, instance):
        """Prepare title field"""
        return instance.title_en or instance.title_vi or instance.title or ""

    def prepare_title_vi(self, instance):
        """Prepare title_vi field with proper encoding"""
        return instance.title_vi or ""

    def prepare_original_title(self, instance):
        """Prepare original_title field"""
        return instance.original_title or ""

    def prepare_title_vi_no_diacritic(self, instance):
        """Chuẩn hóa title_vi thành không dấu để index cho trường title_vi_no_diacritic"""
        import unicodedata
        title = instance.title_vi or ''
        # Loại bỏ dấu tiếng Việt
        title_no_diacritic = unicodedata.normalize('NFD', title)
        title_no_diacritic = ''.join([c for c in title_no_diacritic if unicodedata.category(c) != 'Mn'])
        return title_no_diacritic

    def prepare_cached_imdb_rating(self, instance):
        """Prepare cached IMDB rating"""
        try:
            return instance.cached_imdb_rating or 0
        except Exception as e:
            logger.warning(f"Error preparing cached_imdb_rating for movie {instance.id}: {e}")
            return 0

    def prepare_cached_tmdb_rating(self, instance):
        """Prepare cached TMDB rating"""
        try:
            return instance.cached_tmdb_rating or 0
        except Exception as e:
            logger.warning(f"Error preparing cached_tmdb_rating for movie {instance.id}: {e}")
            return 0

    def prepare_combined_rating_score(self, instance):
        """Prepare combined rating score"""
        try:
            return instance.combined_rating_score or 0
        except Exception as e:
            logger.warning(f"Error preparing combined_rating_score for movie {instance.id}: {e}")
            return 0

    def prepare_approval_status(self, instance):
        """Prepare approval status from MovieAdminControl"""
        try:
            if hasattr(instance, 'admin_control') and instance.admin_control:
                return instance.admin_control.approval_status
            return 'PENDING'
        except Exception as e:
            logger.warning(f"Error preparing approval_status for movie {instance.id}: {e}")
            return 'PENDING'

    def prepare_admin_featured(self, instance):
        """Prepare admin featured flag from MovieAdminControl"""
        try:
            if hasattr(instance, 'admin_control') and instance.admin_control:
                return instance.admin_control.admin_featured
            return False
        except Exception as e:
            logger.warning(f"Error preparing admin_featured for movie {instance.id}: {e}")
            return False

    def prepare_visibility_status(self, instance):
        """Prepare visibility status from MovieAdminControl"""
        try:
            if hasattr(instance, 'admin_control') and instance.admin_control:
                return instance.admin_control.visibility_status
            return 'DRAFT'
        except Exception as e:
            logger.warning(f"Error preparing visibility_status for movie {instance.id}: {e}")
            return 'DRAFT'

    def prepare_is_published(self, instance):
        """Prepare is published flag from MovieAdminControl"""
        try:
            if hasattr(instance, 'admin_control') and instance.admin_control:
                return instance.admin_control.is_published
            return False
        except Exception as e:
            logger.warning(f"Error preparing is_published for movie {instance.id}: {e}")
            return False

    def prepare_admin_priority(self, instance):
        """Prepare admin priority from MovieAdminControl"""
        try:
            if hasattr(instance, 'admin_control') and instance.admin_control:
                return instance.admin_control.admin_priority
            return 0
        except Exception as e:
            logger.warning(f"Error preparing admin_priority for movie {instance.id}: {e}")
            return 0

    def prepare_created_at(self, instance):
        """Prepare created at timestamp"""
        return instance.created_at
