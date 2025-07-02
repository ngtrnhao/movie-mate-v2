from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Movie

@registry.register_document
class MovieDocument(Document):
    # Text fields
    title_en = fields.TextField(
        analyzer='english',
        fields={'raw': fields.KeywordField()}
    )
    title_vi = fields.TextField(
        analyzer='standard',
        fields={'raw': fields.KeywordField()}
    )
    overview_en = fields.TextField(analyzer='english')
    overview_vi = fields.TextField(analyzer='standard')

    # Metadata fields
    release_date = fields.DateField()
    runtime = fields.IntegerField()
    vote_average = fields.FloatField()
    vote_count = fields.IntegerField()
    popularity = fields.FloatField()  # Sửa từ popularity_score

    # Filter fields
    genres = fields.KeywordField(multi=True)
    is_adult = fields.BooleanField()
    status = fields.KeywordField()
    production_countries = fields.KeywordField(multi=True)

    # Image URLs
    poster_url = fields.KeywordField()
    backdrop_url = fields.KeywordField()

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
            'cached_imdb_rating',
            'cached_tmdb_rating',
            'is_popular',
            'is_top_rated',
        ]

    def prepare_genres(self, instance):
        """Chuẩn bị data cho genres field"""
        return [genre.name for genre in instance.genres.all()]

    def prepare_production_countries(self, instance):
        """Chuẩn bị data cho production_countries field"""
        if hasattr(instance, 'moviemetadata') and instance.moviemetadata:
            countries = instance.moviemetadata.production_countries
            if countries and isinstance(countries, list):
                return [country.get('iso_3166_1', '') for country in countries]
        return []

    def prepare_vote_count(self, instance):
        """Chuẩn bị data cho vote_count field"""
        return instance.cached_imdb_votes or instance.cached_tmdb_votes or 0

    def prepare_popularity(self, instance):
        """Chuẩn bị data cho popularity field"""
        return instance.combined_rating_score or 0
