from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Movie

@registry.register_document
class MovieDocument(Document):
    #Text fields
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

    #Metadata fields
    release_date = fields.DateField()
    runtime = fields.IntegerField()
    vote_average = fields.FloatField()
    popularity_score = fields.FloatField() # chưa có

    #Filter fields
    genres = fields.KeywordField(multi=True)
    is_adult = fields.BooleanField()
    status = fields.KeywordField()
    production_countries = fields.KeywordField(multi=True)

    #Image URLS
    poster_url = fields.KeywordField()
    backdrop_url = fields.KeywordField()

    class Index:
        name = 'movies'
        settings = {
            'number_of_shards':1,
            'number_of_replicas':0,
            'analysis':{
                'analyzer':{
                    'vietnamese_analyzer':{
                        'type':'custom',
                        'tokenizer':'standard',
                        'filter':['lowercase']
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
