from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Movie

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

    # Relationship fields
    genres = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': fields.KeywordField(),
        'language': fields.KeywordField()
    })
    production_countries = fields.KeywordField(multi=True)

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
        return [{'id': genre.id, 'name': genre.name, 'language': genre.language}
                for genre in instance.genres.all()]

    def prepare_production_countries(self, instance):
        """Prepare data for production_countries field"""
        if hasattr(instance, 'moviemetadata') and instance.moviemetadata:
            countries = instance.moviemetadata.production_countries
            if countries and isinstance(countries, list):
                return [country.get('iso_3166_1', '') for country in countries]
        return []

    def prepare_vote_count(self, instance):
        """Prepare data for vote_count field"""
        return instance.cached_imdb_votes or instance.cached_tmdb_votes or 0

    def prepare_popularity(self, instance):
        """Prepare data for popularity field"""
        return instance.combined_rating_score or 0
