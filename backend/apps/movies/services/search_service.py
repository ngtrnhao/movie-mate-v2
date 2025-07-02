from elasticsearch_dsl import Search, Q
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class MovieSearchService:
    def __init__(self):
        from django_elasticsearch_dsl.registries import registry
        self.client = registry.get_connection()
        self.index = 'movies'
    def search(self,params):
        """Search movies with Elasticsearch"""
        search = Search(using=self.client, index=self.index)

        #search query
        if params.get('q'):
            if params.get('language') == 'vi':
                search = search.query(
                    'multi_match',
                    query=params['q'],
                    fields=['title_vi^3','title_vi^2','overview_vi^1'],
                    type='best_fields',
                )
            else:
                search = search.query(
                    'multi_match',
                    query=params['q'],
                    fields=['title_en^3','title_en^2','overview_en^1'],
                    type='best_fields',
                )

        #Apply filters
        if params.get('genres'):
            search = search.filter('terms',genres=params['genres'])

        if params.get('year_from'):
            search = search.filter('range',release_date={'gte': f"{params['year_from']}-01-01"})

        if params.get('year_to'):
            search = search.filter('range',release_date={'lte': f"{params['year_to']}-12-31"})

        if params.get('country'):
            search = search.filter('terms',production_countries=params['country'])

        if params.get('adult') == 'false':
            search = search.filter('term',is_adult=False)

        #sorting
        sort_mapping = {
            'popularity':'-popularity_score',
            'rating':'-cached_tmdb_rating',
            'release_date':'-release_date',
            'title': 'title_en.raw' if params.get('language') == 'en' else 'title_vi.raw',
            'runtime':'-runtime',
            'vote_count':'-vote_count'
        }

        sort_field = sort_mapping.get(params.get('sort_by','popularity'))
        if sort_field:
            if params.get('order') == 'asc':
                sort_field = sort_field.lstrip('-')
            search = search.sort(sort_field)

        #Pagination
        page = int(params.get('page',1))
        page_size = (int(params.get('page_size',50)),100)
        start = (page-1) * page_size
        search = search[start:start+page_size]

        return search.execute()
