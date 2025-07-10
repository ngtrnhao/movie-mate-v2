from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from django.conf import settings
from django.core.cache import cache
import logging
from apps.metadata.models import Genre
from ..serializers import OptimizedMovieListSerializer
from ..models import Movie
from django.db.models import Prefetch
from ..models import MovieTrailer

logger = logging.getLogger(__name__)

class MovieSearchService:
    def __init__(self):
        try:
            # Check if cloud configuration is available
            if (hasattr(settings, 'ELASTICSEARCH_CLOUD_ID') and
                hasattr(settings, 'ELASTICSEARCH_USERNAME') and
                hasattr(settings, 'ELASTICSEARCH_PASSWORD') and
                settings.ELASTICSEARCH_CLOUD_ID and
                settings.ELASTICSEARCH_USERNAME and
                settings.ELASTICSEARCH_PASSWORD):

                # Initialize Elasticsearch client with cloud configuration
                self.client = Elasticsearch(
                    cloud_id=settings.ELASTICSEARCH_CLOUD_ID,
                    basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD)
                )
                logger.info("Using Elasticsearch Cloud configuration")
            else:
                # Fall back to local Elasticsearch configuration
                hosts = [settings.ELASTICSEARCH_DSL['default']['hosts'][0]] if hasattr(settings, 'ELASTICSEARCH_DSL') else ['localhost:9200']
                self.client = Elasticsearch(hosts=hosts)
                logger.info(f"Using local Elasticsearch configuration: {hosts}")

            # Test connection
            info = self.client.info()
            logger.info(f"Connected to Elasticsearch cluster: {info.get('cluster_name')}")

            self.index = 'movies'
            self.connection_available = True
        except Exception as e:
            logger.error(f"Elasticsearch connection failed during init: {str(e)}")
            self.client = None
            self.index = 'movies'
            self.connection_available = False

    def search(self, params, admin_mode=False):
        """Search movies with Elasticsearch, hỗ trợ admin_mode cho filter đặc biệt"""
        if not self.connection_available or not self.client:
            logger.warning("Elasticsearch connection not available, falling back to database search")
            return None

        try:
            search = Search(using=self.client, index=self.index)

            # Search query with enhanced fuzzy matching
            if params.get('q'):
                query_text = params['q'].strip()
                if params.get('language') == 'vi':
                    search = search.query(
                        'bool',
                        should=[
                            {
                                'multi_match': {
                                    'query': query_text,
                                    'fields': ['title_vi^4', 'title_en^3', 'title^2'],
                                    'type': 'cross_fields',
                                    'operator': 'or',
                                    'minimum_should_match': '60%',
                                    'analyzer': 'vietnamese_analyzer'
                                }
                            },
                            {
                                'multi_match': {
                                    'query': query_text,
                                    'fields': ['overview_vi^2', 'overview_en^1'],
                                    'type': 'best_fields',
                                    'operator': 'or',
                                    'minimum_should_match': '50%',
                                    'analyzer': 'vietnamese_analyzer'
                                }
                            }
                        ]
                    )
                else:
                    search = search.query(
                        'bool',
                        should=[
                            {
                                'multi_match': {
                                    'query': query_text,
                                    'fields': ['title_en^4', 'title^3', 'title_vi^2'],
                                    'type': 'cross_fields',
                                    'operator': 'or',
                                    'minimum_should_match': '60%',
                                    'analyzer': 'english'
                                }
                            },
                            {
                                'multi_match': {
                                    'query': query_text,
                                    'fields': ['overview_en^2', 'overview_vi^1'],
                                    'type': 'best_fields',
                                    'operator': 'or',
                                    'minimum_should_match': '50%',
                                    'analyzer': 'english'
                                }
                            }
                        ]
                    )

            # Apply filters
            if params.get('genres'):
                try:
                    # Convert genres to list if it's a string
                    genre_list = params['genres']
                    if isinstance(genre_list, str):
                        genre_list = [int(g) for g in genre_list.split(',') if g.strip()]
                    elif not isinstance(genre_list, list):
                        genre_list = [int(genre_list)]

                    # Convert genre IDs to names
                    genre_names = list(Genre.objects.filter(id__in=genre_list).values_list('name', flat=True))
                    if genre_names:
                        search = search.filter('terms', genres=genre_names)
                    else:
                        logger.warning(f"No genre names found for IDs: {genre_list}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing genres: {str(e)}")
                    # Don't return None here, continue with search without genre filter

            if params.get('year_from'):
                search = search.filter('range', release_date={'gte': f"{params['year_from']}-01-01"})

            if params.get('year_to'):
                search = search.filter('range', release_date={'lte': f"{params['year_to']}-12-31"})

            if params.get('country'):
                search = search.filter('terms', production_countries=[params['country']])

            if params.get('status'):
                search = search.filter('term', status=params['status'])

            if params.get('adult') == 'false':
                search = search.filter('term', is_adult=False)

            # --- ADMIN FILTERS ---
            if admin_mode:
                # Các filter đặc biệt cho admin
                if params.get('approval_status'):
                    search = search.filter('term', approval_status=params['approval_status'])
                if params.get('admin_featured') is not None:
                    val = params['admin_featured']
                    if isinstance(val, str):
                        val = val.lower() == 'true'
                    search = search.filter('term', admin_featured=val)
                if params.get('visibility_status'):
                    search = search.filter('term', visibility_status=params['visibility_status'])
                if params.get('is_published') is not None:
                    val = params['is_published']
                    if isinstance(val, str):
                        val = val.lower() == 'true'
                    search = search.filter('term', is_published=val)
                if params.get('admin_priority') is not None:
                    try:
                        search = search.filter('term', admin_priority=int(params['admin_priority']))
                    except Exception:
                        pass
                # Keyset pagination: after_created_at
                if params.get('after_created_at'):
                    search = search.filter('range', created_at={'lt': params['after_created_at']})

            # Sorting with enhanced options
            sort_mapping = {
                'popularity': '-popularity',
                'rating': '-vote_average',
                'release_date': '-release_date',
                'title': 'title_en.raw' if params.get('language') == 'en' else 'title_vi.raw',
                'runtime': '-runtime',
                'vote_count': '-vote_count',
                # Admin sort
                'created_at': '-created_at',
                'admin_priority': '-admin_priority',
                'approval_status': 'approval_status',
            }
            sort_field = sort_mapping.get(params.get('sort_by', 'created_at'))
            if sort_field:
                if params.get('order') == 'asc':
                    sort_field = sort_field.lstrip('-')
                search = search.sort(sort_field)
            # Default secondary sort by created_at for admin
            if params.get('sort_by') != 'created_at':
                search = search.sort('-created_at')

            # Pagination
            page = int(params.get('page', 1))
            page_size = min(int(params.get('page_size', 50)), 100)
            start = (page - 1) * page_size
            search = search[start:start + page_size]

            # Execute search with error handling
            logger.info(f"Executing Elasticsearch query: {search.to_dict()}")
            response = search.execute()

            # Get total hits
            total_hits = response.hits.total.value

            # Extract movie IDs from Elasticsearch results while preserving order
            movie_ids = [int(hit.meta.id) for hit in response.hits]

            # Fetch movies from database with proper prefetching
            movies_dict = {}
            movies = Movie.objects.select_related(
                'moviemetadata'
            ).prefetch_related(
                Prefetch('ratings', to_attr='prefetched_ratings'),
                Prefetch('genres', to_attr='prefetched_genres'),
                Prefetch(
                    'trailers',
                    queryset=MovieTrailer.objects.filter(type='TRAILER'),
                    to_attr='prefetched_trailers'
                ),
                Prefetch('cast', to_attr='prefetched_cast'),
                Prefetch('movieimage_set', to_attr='prefetched_images')
            ).filter(id__in=movie_ids)

            # Create a dictionary for O(1) lookup while preserving ES order
            for movie in movies:
                movies_dict[movie.id] = movie

            # Maintain Elasticsearch result order
            ordered_movies = [movies_dict[movie_id] for movie_id in movie_ids if movie_id in movies_dict]

            # Serialize using OptimizedMovieListSerializer
            serializer = OptimizedMovieListSerializer(ordered_movies, many=True)

            logger.info(f"Successfully serialized {len(ordered_movies)} movies from Elasticsearch results")

            # Keyset pagination markers
            next_after_created_at = None
            prev_after_created_at = None
            if ordered_movies:
                next_after_created_at = getattr(ordered_movies[-1], 'created_at', None)
                prev_after_created_at = getattr(ordered_movies[0], 'created_at', None)

            return {
                'total': total_hits,
                'results': serializer.data,
                'search_engine': 'elasticsearch',
                'next_after_created_at': next_after_created_at,
                'prev_after_created_at': prev_after_created_at,
            }

        except Exception as e:
            logger.error(f"Elasticsearch search error: {str(e)}")
            return None

    def get_suggestions(self, query, language='en', limit=5):
        """Get search suggestions based on query"""
        if not self.connection_available or not self.client:
            logger.warning("Elasticsearch connection not available for suggestions, falling back to database")
            return []

        try:
            logger.info(f"Getting suggestions for query: {query}, language: {language}, limit: {limit}")
            search = Search(using=self.client, index=self.index)

            # Build multi-match query for better suggestions
            if language == 'vi':
                logger.debug("Using Vietnamese search fields")
                search = search.query(
                    'multi_match',
                    query=query,
                    fields=['title_vi^4', 'title_en^3', 'title^2', 'overview_vi^1', 'overview_en^0.5'],
                    type='cross_fields',
                    operator='or',
                    minimum_should_match='60%',
                    analyzer='standard'
                )
            else:
                logger.debug("Using English search fields")
                search = search.query(
                    'multi_match',
                    query=query,
                    fields=['title_en^4', 'title^3', 'title_vi^2', 'overview_en^1', 'overview_vi^0.5'],
                    type='cross_fields',
                    operator='or',
                    minimum_should_match='60%',
                    analyzer='standard'
                )

            # Filter conditions for quality suggestions
            search = search.filter('exists', field='poster_url')
            search = search.filter('range', poster_url={'gt': ''})
            search = search.filter('exists', field='release_date')
            search = search.filter('term', status='RELEASED')
            search = search.filter('range', vote_count={'gt': 100})  # Ensure movie has sufficient votes
            search = search.filter('range', vote_average={'gt': 0})  # Ensure movie has rating

            # Language-specific filters
            if language == 'vi':
                # For Vietnamese, ensure title_vi and overview_vi exist and are not empty
                search = search.filter('exists', field='title_vi')
                search = search.filter('range', title_vi={'gt': ''})
                search = search.filter('exists', field='overview_vi')
                search = search.filter('range', overview_vi={'gt': ''})
            else:
                # For English, ensure title_en and overview_en exist and are not empty
                search = search.filter('exists', field='title_en')
                search = search.filter('range', title_en={'gt': ''})
                search = search.filter('exists', field='overview_en')
                search = search.filter('range', overview_en={'gt': ''})

            # Boost more popular and recent movies
            search = search.query(
                'function_score',
                query=search.query,
                functions=[
                    {
                        'gauss': {
                            'release_date': {
                                'scale': '365d',
                                'offset': '7d',
                                'decay': 0.5
                            }
                        },
                        'weight': 5
                    },
                    {
                        'field_value_factor': {
                            'field': 'vote_average',
                            'factor': 1,
                            'modifier': 'log1p',
                            'missing': 0
                        },
                        'weight': 3
                    },
                    {
                        'field_value_factor': {
                            'field': 'popularity',
                            'factor': 1,
                            'modifier': 'log1p',
                            'missing': 0
                        },
                        'weight': 2
                    }
                ],
                score_mode='sum',
                boost_mode='multiply'
            )

            # Sort by score and popularity
            search = search.sort('_score', '-popularity', '-release_date')

            # Limit results
            search = search[:limit]

            # Log the query being executed
            logger.debug(f"Elasticsearch query: {search.to_dict()}")

            # Execute search
            response = search.execute()
            logger.info(f"Found {len(response.hits)} suggestions")

            # Format suggestions with more detailed information
            suggestions = []
            for hit in response.hits:
                movie_data = hit.to_dict()
                suggestion = {
                    'id': hit.meta.id,
                    'title': movie_data.get('title_vi' if language == 'vi' else 'title_en') or movie_data.get('title'),
                    'title_en': movie_data.get('title_en'),
                    'title_vi': movie_data.get('title_vi'),
                    'poster_url': movie_data.get('poster_url'),
                    'release_date': movie_data.get('release_date'),
                    'rating': {
                        'imdb': float(movie_data.get('cached_imdb_rating')) if movie_data.get('cached_imdb_rating') else None,
                        'tmdb': float(movie_data.get('cached_tmdb_rating')) if movie_data.get('cached_tmdb_rating') else None,
                        'vote_average': float(movie_data.get('vote_average')) if movie_data.get('vote_average') else None,
                        'vote_count': movie_data.get('vote_count')
                    },
                    'genres': movie_data.get('genres', [])[:3],  # Limit to top 3 genres
                    'status': movie_data.get('status'),
                    'popularity': movie_data.get('popularity')
                }
                logger.debug(f"Formatted suggestion: {suggestion}")
                suggestions.append(suggestion)

            return suggestions
        except Exception as e:
            logger.error(f"Elasticsearch suggestions error: {str(e)}", exc_info=True)
            return []

    def health_check(self):
        """Check if Elasticsearch is available"""
        if not self.connection_available or not self.client:
            logger.error("Elasticsearch client not initialized")
            return False

        try:
            health = self.client.cluster.health()
            logger.info(f"Elasticsearch cluster health: {health.get('status')}")
            return True
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {str(e)}")
            return False

    def test_connection(self):
        """Test Elasticsearch connection and configuration"""
        try:
            # Check if cloud configuration is available
            if (hasattr(settings, 'ELASTICSEARCH_CLOUD_ID') and
                hasattr(settings, 'ELASTICSEARCH_USERNAME') and
                hasattr(settings, 'ELASTICSEARCH_PASSWORD') and
                settings.ELASTICSEARCH_CLOUD_ID and
                settings.ELASTICSEARCH_USERNAME and
                settings.ELASTICSEARCH_PASSWORD):

                # Try to connect with cloud configuration
                client = Elasticsearch(
                    cloud_id=settings.ELASTICSEARCH_CLOUD_ID,
                    basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD)
                )
                logger.info("Testing Elasticsearch Cloud configuration")
            else:
                # Try to connect with local configuration
                hosts = [settings.ELASTICSEARCH_DSL['default']['hosts'][0]] if hasattr(settings, 'ELASTICSEARCH_DSL') else ['localhost:9200']
                client = Elasticsearch(hosts=hosts)
                logger.info(f"Testing local Elasticsearch configuration: {hosts}")

            # Get cluster info
            info = client.info()
            logger.info(f"Successfully connected to Elasticsearch cluster: {info.get('cluster_name')}")
            logger.info(f"Elasticsearch version: {info.get('version', {}).get('number')}")

            # Check index existence
            if not client.indices.exists(index=self.index):
                logger.warning(f"Index '{self.index}' does not exist")
                return False

            # Get index stats
            stats = client.indices.stats(index=self.index)
            doc_count = stats['indices'][self.index]['total']['docs']['count']
            logger.info(f"Index '{self.index}' contains {doc_count} documents")

            return True
        except Exception as e:
            logger.error(f"Elasticsearch connection test failed: {str(e)}")
            return False

