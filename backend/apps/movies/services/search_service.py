from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q as ES_Q
from django.conf import settings
from django.core.cache import cache
import logging
from apps.metadata.models import Genre
from ..serializers import OptimizedMovieListSerializer
from ..models import Movie, MovieQualityMetrics, MovieScheduling, MovieTrailer
from django.db.models import Prefetch, Q as Django_Q

logger = logging.getLogger(__name__)

class MovieSearchService:
    # 🎛️ ELASTICSEARCH TOGGLE - Set to False to force ORM fallback
    ELASTICSEARCH_ENABLED = True

    def __init__(self):
        # Check if Elasticsearch is manually disabled
        if not self.ELASTICSEARCH_ENABLED:
            logger.info("Elasticsearch manually disabled - using ORM fallback")
            self.client = None
            self.index = 'movies'
            self.connection_available = False
            return

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
            elif hasattr(settings, 'ELASTICSEARCH_DSL') and settings.ELASTICSEARCH_DSL:
                # Use DSL configuration (production settings)
                es_config = settings.ELASTICSEARCH_DSL['default']

                # Build connection parameters
                connection_params = {
                    'hosts': es_config['hosts'],
                    'timeout': es_config.get('timeout', 30),
                    'retry_on_timeout': es_config.get('retry_on_timeout', True),
                    'max_retries': es_config.get('max_retries', 3),
                }

                # Add authentication if available
                if es_config.get('http_auth'):
                    connection_params['http_auth'] = es_config['http_auth']

                # Add SSL configuration if available (using newer parameter names)
                if es_config.get('use_ssl', False):
                    connection_params['scheme'] = 'https'
                    if es_config.get('verify_certs') is not None:
                        connection_params['verify_certs'] = es_config['verify_certs']
                    if es_config.get('ca_certs'):
                        connection_params['ca_certs'] = es_config['ca_certs']
                    if es_config.get('client_cert'):
                        connection_params['client_cert'] = es_config['client_cert']
                    if es_config.get('client_key'):
                        connection_params['client_key'] = es_config['client_key']

                self.client = Elasticsearch(**connection_params)
                logger.info(f"Using Elasticsearch DSL configuration: {es_config['hosts']}")
            else:
                # Fall back to local Elasticsearch configuration
                hosts = ['localhost:9200']
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
        """Search movies with Elasticsearch with enhanced quality and scheduling filters"""
        # Check if Elasticsearch is manually disabled
        if not self.ELASTICSEARCH_ENABLED:
            logger.info("Elasticsearch manually disabled - forcing ORM fallback")
            return None

        if not self.connection_available or not self.client:
            logger.warning("Elasticsearch connection not available, falling back to database search")
            return None

        try:
            search = Search(using=self.client, index=self.index)
            if not admin_mode:
                search = search.filter('exists', field='poster_url')
                search = search.filter('range', poster_url={'gt':''})

            #  Enhanced search query with quality scoring
            if params.get('q'):
                query_text = params['q'].strip()
                search = self._build_enhanced_query(search, query_text, params)

            # QUALITY FILTERS: Only return documents with proper titles for better UX
            search = search.filter('bool', should=[
                ES_Q('exists', field='title_en'),
                ES_Q('exists', field='title_vi')
            ], minimum_should_match=1)

            # EXISTING FILTERS (preserved for both user and admin)
            if params.get('genres'):
                genre_values = params['genres'] if isinstance(params['genres'], list) else [params['genres']]

                # Convert genre IDs to names if necessary
                genre_names = []
                for value in genre_values:
                    try:
                        # Try to convert to int - if successful, it's an ID
                        genre_id = int(value)
                        from apps.metadata.models import Genre
                        genre = Genre.objects.filter(id=genre_id).first()
                        if genre:
                            genre_names.append(genre.name)
                        else:
                            logger.warning(f"Genre ID {genre_id} not found")
                    except ValueError:
                        # Not an integer, assume it's already a name
                        genre_names.append(value)

                if genre_names:
                    search = search.filter('nested', path='genres', query=ES_Q('terms', **{'genres.name': genre_names}))

            if params.get('year_from'):
                search = search.filter('range', release_date={'gte': f"{params['year_from']}-01-01"})

            if params.get('year_to'):
                search = search.filter('range', release_date={'lte': f"{params['year_to']}-12-31"})

            if params.get('rating_min'):
                search = search.filter('range', combined_rating_score={'gte': float(params['rating_min'])})

            if params.get('rating_max'):
                search = search.filter('range', combined_rating_score={'lte': float(params['rating_max'])})

            if params.get('runtime_min'):
                search = search.filter('range', runtime={'gte': int(params['runtime_min'])})

            if params.get('runtime_max'):
                search = search.filter('range', runtime={'lte': int(params['runtime_max'])})

            if params.get('status'):
                status_values = params['status']
                if isinstance(status_values, str):
                    status_values = [status_values]
                search = search.filter('terms', **{'status': status_values})

            if params.get('countries'):
                country_values = params['countries']
                if isinstance(country_values, str):
                    country_values = [country_values]
                search = search.filter('terms', **{'production_countries': country_values})

            if params.get('adult') is not None:
                # Convert string boolean to actual boolean
                adult_value = params['adult']
                if isinstance(adult_value, str):
                    adult_value = adult_value.lower() in ('true', '1', 'yes')
                elif isinstance(adult_value, bool):
                    adult_value = adult_value
                else:
                    adult_value = bool(adult_value)
                search = search.filter('term', is_adult=adult_value)

            # 🎯 ADMIN MODE FILTERS (enhanced for normalized structure)
            if admin_mode:
                # Basic admin filters
                if params.get('approval_status'):
                    approval_values = params['approval_status']
                    if isinstance(approval_values, str):
                        approval_values = [approval_values]
                    search = search.filter('terms', approval_status=approval_values)

                if params.get('visibility_status'):
                    visibility_values = params['visibility_status']
                    if isinstance(visibility_values, str):
                        visibility_values = [visibility_values]
                    search = search.filter('terms', visibility_status=visibility_values)

                if params.get('admin_featured') is not None:
                    search = search.filter('term', admin_featured=params['admin_featured'])

                if params.get('admin_priority_min'):
                    search = search.filter('range', admin_priority={'gte': int(params['admin_priority_min'])})

                if params.get('is_published') is not None:
                    search = search.filter('term', is_published=params['is_published'])

                # 📊 ADVANCED QUALITY FILTERS (admin only)
                if params.get('quality_score_min'):
                    search = search.filter('range', quality_score={'gte': float(params['quality_score_min'])})

                if params.get('quality_score_max'):
                    search = search.filter('range', quality_score={'lte': float(params['quality_score_max'])})

                if params.get('content_completeness_min'):
                    search = search.filter('range', content_completeness={'gte': float(params['content_completeness_min'])})

                if params.get('overall_quality_rating'):
                    quality_rating_values = params['overall_quality_rating']
                    if isinstance(quality_rating_values, str):
                        quality_rating_values = [quality_rating_values]
                    search = search.filter('terms', overall_quality_rating=quality_rating_values)

                if params.get('completion_status'):
                    completion_values = params['completion_status']
                    if isinstance(completion_values, str):
                        completion_values = [completion_values]
                    search = search.filter('terms', completion_status=completion_values)

                if params.get('minimum_quality_met') is not None:
                    search = search.filter('term', minimum_quality_met=params['minimum_quality_met'])

                # 📅 ADVANCED SCHEDULING FILTERS (admin only)
                if params.get('campaign_type'):
                    campaign_type_values = params['campaign_type']
                    if isinstance(campaign_type_values, str):
                        campaign_type_values = [campaign_type_values]
                    search = search.filter('terms', campaign_type=campaign_type_values)

                if params.get('campaign_priority_min'):
                    search = search.filter('range', campaign_priority={'gte': int(params['campaign_priority_min'])})

                if params.get('is_published_now') is not None:
                    search = search.filter('term', is_published_now=params['is_published_now'])

                if params.get('is_featured_now') is not None:
                    search = search.filter('term', is_featured_now=params['is_featured_now'])

                if params.get('is_scheduled_for_publish') is not None:
                    search = search.filter('term', is_scheduled_for_publish=params['is_scheduled_for_publish'])

                if params.get('is_scheduled_for_feature') is not None:
                    search = search.filter('term', is_scheduled_for_feature=params['is_scheduled_for_feature'])

                if params.get('auto_publish') is not None:
                    search = search.filter('term', auto_publish=params['auto_publish'])

                if params.get('auto_feature') is not None:
                    search = search.filter('term', auto_feature=params['auto_feature'])

                # 📈 ADVANCED PRODUCTION METRICS FILTERS (admin only)
                if params.get('performance_score_min'):
                    search = search.filter('range', performance_score={'gte': float(params['performance_score_min'])})

                if params.get('trending_score_min'):
                    search = search.filter('range', trending_score={'gte': float(params['trending_score_min'])})

                if params.get('trending_category'):
                    trending_values = params['trending_category']
                    if isinstance(trending_values, str):
                        trending_values = [trending_values]
                    search = search.filter('terms', trending_category=trending_values)

                if params.get('engagement_rate_min'):
                    search = search.filter('range', engagement_rate={'gte': float(params['engagement_rate_min'])})

                if params.get('homepage_views_min'):
                    search = search.filter('range', homepage_views={'gte': int(params['homepage_views_min'])})

                if params.get('user_favorites_min'):
                    search = search.filter('range', user_favorites_count={'gte': int(params['user_favorites_min'])})

                # Enhanced admin filters for quality control
                if params.get('has_quality_issues'):
                    if params['has_quality_issues']:
                        search = search.filter('exists', field='quality_issues')
                    else:
                        search = search.filter('bool', must_not=[{'exists': {'field': 'quality_issues'}}])

                if params.get('needs_quality_review'):
                    # Movies that haven't been quality checked recently or have low scores
                    search = search.filter('bool', should=[
                        {'range': {'last_quality_check': {'lte': 'now-7d'}}},
                        {'range': {'quality_score': {'lt': 6.0}}},
                        {'bool': {'must_not': [{'exists': {'field': 'last_quality_check'}}]}}
                    ])

                if params.get('scheduled_actions_pending'):
                    search = search.filter('range', next_action_date={'gte': 'now/d', 'lte': 'now+7d'})



            # 🚀 ENHANCED FUNCTION SCORE for quality-weighted results
            if params.get('q') and params.get('quality_weighted', True):
                search = search.query(
                    'function_score',
                    query=search.query,
                    functions=[
                        # Boost high-quality content
                        {
                            'filter': {'range': {'quality_score': {'gte': 8.0}}},
                            'weight': 2.0
                        },
                        # Boost complete content
                        {
                            'filter': {'range': {'content_completeness': {'gte': 90.0}}},
                            'weight': 1.5
                        },
                        # Boost trending content
                        {
                            'filter': {'range': {'trending_score': {'gte': 7.0}}},
                            'weight': 1.3
                        },
                        # Boost engaged content
                        {
                            'filter': {'range': {'engagement_rate': {'gte': 0.1}}},
                            'weight': 1.2
                        }
                    ],
                    score_mode='multiply',
                    boost_mode='multiply'
                )

            # Keyset Pagination for Elasticsearch
            page_size = int(params.get('page_size', 20))

            # Handle search_after for keyset pagination
            if params.get('search_after'):
                search_after_values = params['search_after']
                if isinstance(search_after_values, list):
                    search = search.extra(search_after=search_after_values)
                else:
                    # Single value, convert to list
                    search = search.extra(search_after=[search_after_values])
                # Set page size for keyset pagination
                search = search[:page_size]
            elif params.get('page'):
                # Fallback to page-based pagination if page is provided
                page = int(params.get('page', 1))
                start = (page - 1) * page_size
                search = search[start:start + page_size]
            else:
                # Default: first page with page size
                search = search[:page_size]

            # 📊 ENHANCED SORTING with consistent keyset pagination
            sort_by = params.get('sort_by', 'created_at')
            order = params.get('order', 'desc')

            # Map sort fields
            sort_field_mapping = {
                'quality_score': 'quality_score',
                'content_completeness': 'content_completeness',
                'performance_score': 'performance_score',
                'trending_score': 'trending_score',
                'engagement_rate': 'engagement_rate',
                'homepage_views': 'homepage_views',
                'user_favorites': 'user_favorites_count',
                'campaign_priority': 'campaign_priority',
                'popularity': 'combined_rating_score',
                'rating': 'combined_rating_score',
                'date': 'release_date',
                'title': 'title.raw',
                'runtime': 'runtime',
                'vote_count': 'vote_count',
                'created_at': 'created_at'
            }

            # Get the field name for sorting
            sort_field = sort_field_mapping.get(sort_by, 'created_at')

            # Create sort array for consistent keyset pagination
            sort_order = [
                {sort_field: {'order': order}},
                {'id': {'order': order}}  # Always add id as tie-breaker
            ]

            search = search.sort(*sort_order)

            # Execute search
            response = search.execute()

            # Calculate next_search_after for keyset pagination
            next_search_after = None
            if response.hits and len(response.hits) == page_size:
                # Use the last hit's sort values as search_after for next page
                last_hit = response.hits[-1]
                if hasattr(last_hit.meta, 'sort'):
                    next_search_after = list(last_hit.meta.sort)

            # Convert Elasticsearch hits to Movie objects and serialize them
            movie_ids = [int(hit.meta.id) for hit in response.hits]

            # Get Movie objects with proper prefetching for serialization
            orm_filter = {'id__in': movie_ids}
            if not admin_mode:
                orm_filter.update({'poster_url__isnull': False, 'poster_url__gt': ''})

            movies = Movie.objects.select_related(
                'moviemetadata'
            ).prefetch_related(
                'genres',
                'ratings',
                Prefetch('trailers', queryset=MovieTrailer.objects.filter(type='TRAILER'))
            ).filter(**orm_filter)

            # Maintain the order from Elasticsearch results
            movie_dict = {movie.id: movie for movie in movies}
            ordered_movies = [movie_dict[movie_id] for movie_id in movie_ids if movie_id in movie_dict]

            # Serialize using the same serializer as ORM
            serializer = OptimizedMovieListSerializer(ordered_movies, many=True)

            return {
                'total_count': response.hits.total.value,
                'results': serializer.data,
                'search_engine': 'elasticsearch',
                'took': response.took,
                'max_score': response.hits.max_score,
                'next_search_after': next_search_after,
                'from_cache': False
            }

        except Exception as e:
            logger.error(f"Elasticsearch search failed: {str(e)}")
            return None

    def _build_enhanced_query(self, search, query_text, params):
        """Build enhanced search query with quality and relevance scoring"""
        try:
            language = params.get('language', 'en')

            if language == 'vi':
                # Vietnamese-optimized search
                    search = search.query(
                        'bool',
                        should=[
                        # Title search with high boost
                            {
                                'multi_match': {
                                    'query': query_text,
                                'fields': ['title_vi^5', 'title_en^4', 'title^3'],
                                    'type': 'cross_fields',
                                    'operator': 'or',
                                    'minimum_should_match': '60%',
                                    'analyzer': 'vietnamese_analyzer'
                                }
                            },
                        # Overview search
                            {
                                'multi_match': {
                                    'query': query_text,
                                'fields': ['overview_vi^3', 'overview_en^2'],
                                    'type': 'best_fields',
                                    'operator': 'or',
                                    'minimum_should_match': '50%',
                                    'analyzer': 'vietnamese_analyzer'
                                }
                        },
                        # Quality-weighted content search
                        {
                            'multi_match': {
                                'query': query_text,
                                'fields': ['quality_issues^1', 'quality_suggestions^1'],
                                'type': 'phrase_prefix',
                                'boost': 0.5
                            }
                        },
                        # Campaign and scheduling search
                        {
                            'multi_match': {
                                'query': query_text,
                                'fields': ['campaign_name^2', 'campaign_type^1'],
                                'type': 'phrase_prefix',
                                'boost': 0.3
                            }
                            }
                        ]
                    )
            else:
                # English-optimized search
                    search = search.query(
                        'bool',
                        should=[
                        # Title search with high boost
                            {
                                'multi_match': {
                                    'query': query_text,
                                'fields': ['title_en^5', 'title_vi^3', 'title^4', 'original_title^3'],
                                    'type': 'cross_fields',
                                    'operator': 'or',
                                    'minimum_should_match': '60%',
                                    'analyzer': 'english'
                                }
                            },
                        # Overview search
                            {
                                'multi_match': {
                                    'query': query_text,
                                'fields': ['overview_en^3', 'overview_vi^2'],
                                    'type': 'best_fields',
                                    'operator': 'or',
                                    'minimum_should_match': '50%',
                                    'analyzer': 'english'
                                }
                        },
                        # Fuzzy search for typos
                        {
                            'multi_match': {
                                'query': query_text,
                                'fields': ['title_en^3', 'title_vi^2'],
                                'type': 'most_fields',
                                'fuzziness': 'AUTO',
                                'prefix_length': 2,
                                'boost': 0.7
                            }
                        },
                        # Quality-weighted content search
                        {
                            'multi_match': {
                                'query': query_text,
                                'fields': ['quality_issues^1', 'quality_suggestions^1'],
                                'type': 'phrase_prefix',
                                'boost': 0.5
                            }
                        },
                        # Campaign and scheduling search
                        {
                            'multi_match': {
                                'query': query_text,
                                'fields': ['campaign_name^2', 'campaign_type^1'],
                                'type': 'phrase_prefix',
                                'boost': 0.3
                            }
                        }
                    ]
                )

            return search

        except Exception as e:
            logger.error(f"Error building enhanced query: {str(e)}")
            # Fallback to simple query
            return search.query('multi_match', query=query_text, fields=['title_en^3', 'title_vi^3', 'overview_en^1'])

    def advanced_search(self, params):
        """Advanced search with quality and performance analytics"""
        if not self.connection_available or not self.client:
            return None

        try:
            search = Search(using=self.client, index=self.index)

            # Quality analytics aggregations
            search.aggs.bucket('quality_distribution', 'range', field='quality_score', ranges=[
                {'from': 0, 'to': 3, 'key': 'poor'},
                {'from': 3, 'to': 6, 'key': 'fair'},
                {'from': 6, 'to': 8, 'key': 'good'},
                {'from': 8, 'to': 10, 'key': 'excellent'}
            ])

            # Content completeness analytics
            search.aggs.bucket('completeness_distribution', 'range', field='content_completeness', ranges=[
                {'from': 0, 'to': 50, 'key': 'incomplete'},
                {'from': 50, 'to': 70, 'key': 'partial'},
                {'from': 70, 'to': 90, 'key': 'nearly_complete'},
                {'from': 90, 'to': 100, 'key': 'complete'}
            ])

            # Performance analytics
            search.aggs.bucket('performance_distribution', 'range', field='performance_score', ranges=[
                {'from': 0, 'to': 3, 'key': 'low'},
                {'from': 3, 'to': 6, 'key': 'medium'},
                {'from': 6, 'to': 8, 'key': 'high'},
                {'from': 8, 'to': 10, 'key': 'excellent'}
            ])

            # Trending categories
            search.aggs.bucket('trending_categories', 'terms', field='trending_category', size=10)

            # Campaign types
            search.aggs.bucket('campaign_types', 'terms', field='campaign_type', size=10)

            # Apply filters
            if params.get('q'):
                search = self._build_enhanced_query(search, params['q'], params)

            # Execute search
            response = search.execute()

            return {
                'total_count': response.hits.total.value,
                'results': [hit.to_dict() for hit in response.hits],
                'analytics': {
                    'quality_distribution': response.aggregations.quality_distribution.buckets,
                    'completeness_distribution': response.aggregations.completeness_distribution.buckets,
                    'performance_distribution': response.aggregations.performance_distribution.buckets,
                    'trending_categories': response.aggregations.trending_categories.buckets,
                    'campaign_types': response.aggregations.campaign_types.buckets
                }
            }

        except Exception as e:
            logger.error(f"Advanced search failed: {str(e)}")
            return None

    def get_quality_insights(self, params=None):
        """Get quality insights for admin dashboard"""
        if not self.connection_available or not self.client:
            return None

        try:
            search = Search(using=self.client, index=self.index)
            search = search.filter('match_all')

            # Quality insights aggregations
            search.aggs.metric('avg_quality_score', 'avg', field='quality_score')
            search.aggs.metric('avg_content_completeness', 'avg', field='content_completeness')
            search.aggs.bucket('quality_issues_count', 'filter', {'exists': {'field': 'quality_issues'}})
            search.aggs.bucket('minimum_quality_not_met', 'filter', {'term': {'minimum_quality_met': False}})
            search.aggs.bucket('needs_quality_review', 'filter', {
                'bool': {
                    'should': [
                        {'range': {'last_quality_check': {'lte': 'now-7d'}}},
                        {'range': {'quality_score': {'lt': 6.0}}},
                        {'bool': {'must_not': [{'exists': {'field': 'last_quality_check'}}]}}
                    ]
                }
            })

            # Performance insights
            search.aggs.metric('avg_performance_score', 'avg', field='performance_score')
            search.aggs.metric('avg_engagement_rate', 'avg', field='engagement_rate')
            search.aggs.bucket('high_performing_content', 'filter', {'range': {'performance_score': {'gte': 8.0}}})

            # Scheduling insights
            search.aggs.bucket('scheduled_for_publish', 'filter', {'term': {'is_scheduled_for_publish': True}})
            search.aggs.bucket('scheduled_for_feature', 'filter', {'term': {'is_scheduled_for_feature': True}})
            search.aggs.bucket('pending_actions', 'filter', {'range': {'next_action_date': {'gte': 'now/d', 'lte': 'now+7d'}}})

            # Limit results since we only need aggregations
            search = search[:0]

            response = search.execute()

            return {
                'quality_insights': {
                    'avg_quality_score': response.aggregations.avg_quality_score.value,
                    'avg_content_completeness': response.aggregations.avg_content_completeness.value,
                    'quality_issues_count': response.aggregations.quality_issues_count.doc_count,
                    'minimum_quality_not_met': response.aggregations.minimum_quality_not_met.doc_count,
                    'needs_quality_review': response.aggregations.needs_quality_review.doc_count
                },
                'performance_insights': {
                    'avg_performance_score': response.aggregations.avg_performance_score.value,
                    'avg_engagement_rate': response.aggregations.avg_engagement_rate.value,
                    'high_performing_content': response.aggregations.high_performing_content.doc_count
                },
                'scheduling_insights': {
                    'scheduled_for_publish': response.aggregations.scheduled_for_publish.doc_count,
                    'scheduled_for_feature': response.aggregations.scheduled_for_feature.doc_count,
                    'pending_actions': response.aggregations.pending_actions.doc_count
                }
            }

        except Exception as e:
            logger.error(f"Quality insights failed: {str(e)}")
            return None

    def fallback_search(self, params, admin_mode=False):
        """Fallback database search with optimized queries for normalized structure"""
        try:
            logger.info("Using fallback database search with normalized structure")

            # Enhanced queryset with normalized relationships
            queryset = Movie.objects.select_related(
                'moviemetadata',
                'quality_metrics',  # NEW: Include quality metrics
                'scheduling',       # NEW: Include scheduling
                'production_metrics'  # NEW: Include production metrics
            ).prefetch_related(
                'genres',
                'ratings',
                Prefetch('trailers', queryset=MovieTrailer.objects.filter(type='TRAILER'))
            )

            # Basic filtering
            if params.get('q'):
                query_text = params['q']
                queryset = queryset.filter(
                    Django_Q(title_en__icontains=query_text) |
                    Django_Q(title_vi__icontains=query_text) |
                    Django_Q(overview_en__icontains=query_text) |
                    Django_Q(overview_vi__icontains=query_text)
                )

            # Quality filters (NEW)
            if params.get('quality_score_min'):
                queryset = queryset.filter(quality_metrics__quality_score__gte=params['quality_score_min'])

            if params.get('content_completeness_min'):
                queryset = queryset.filter(quality_metrics__content_completeness__gte=params['content_completeness_min'])

            if params.get('minimum_quality_met') is not None:
                queryset = queryset.filter(quality_metrics__minimum_quality_met=params['minimum_quality_met'])

            # Scheduling filters (NEW)
            if params.get('is_published_now') is not None:
                queryset = queryset.filter(scheduling__is_published_now=params['is_published_now'])

            if params.get('is_featured_now') is not None:
                queryset = queryset.filter(scheduling__is_featured_now=params['is_featured_now'])

            if params.get('campaign_type'):
                queryset = queryset.filter(scheduling__campaign_type__in=params['campaign_type'])

            # Performance filters (NEW)
            if params.get('performance_score_min'):
                queryset = queryset.filter(production_metrics__performance_score__gte=params['performance_score_min'])

            if params.get('trending_category'):
                queryset = queryset.filter(production_metrics__trending_category__in=params['trending_category'])

            # Existing filters
            if params.get('genres'):
                genre_values = params['genres'] if isinstance(params['genres'], list) else [params['genres']]

                # Handle both genre IDs and names
                genre_ids = []
                genre_names = []
                for value in genre_values:
                    try:
                        # Try to convert to int - if successful, it's an ID
                        genre_id = int(value)
                        genre_ids.append(genre_id)
                    except ValueError:
                        # Not an integer, assume it's a name
                        genre_names.append(value)

                # Filter by both IDs and names
                if genre_ids and genre_names:
                    queryset = queryset.filter(
                        Django_Q(genres__id__in=genre_ids) | Django_Q(genres__name__in=genre_names)
                    )
                elif genre_ids:
                    queryset = queryset.filter(genres__id__in=genre_ids)
                elif genre_names:
                    queryset = queryset.filter(genres__name__in=genre_names)

            if params.get('year_from'):
                queryset = queryset.filter(release_date__year__gte=params['year_from'])

            if params.get('year_to'):
                queryset = queryset.filter(release_date__year__lte=params['year_to'])

            if params.get('rating_min'):
                queryset = queryset.filter(combined_rating_score__gte=params['rating_min'])

            if params.get('adult') is not None:
                # Convert string boolean to actual boolean
                adult_value = params['adult']
                if isinstance(adult_value, str):
                    adult_value = adult_value.lower() in ('true', '1', 'yes')
                elif isinstance(adult_value, bool):
                    adult_value = adult_value
                else:
                    adult_value = bool(adult_value)
                queryset = queryset.filter(is_adult=adult_value)

            # Enhanced sorting with new fields
            sort_mapping = {
                'quality_score': 'quality_metrics__quality_score',
                'content_completeness': 'quality_metrics__content_completeness',
                'performance_score': 'production_metrics__performance_score',
                'trending_score': 'production_metrics__trending_score',
                'engagement_rate': 'production_metrics__engagement_rate',
                'campaign_priority': 'scheduling__campaign_priority',
                'popularity': 'combined_rating_score',
                'rating': 'combined_rating_score',
                'date': 'release_date',
                'title': 'title_en',
                'runtime': 'runtime',
                'vote_count': 'cached_imdb_votes',
                'created_at': 'created_at'
            }

            sort_by = params.get('sort_by', 'popularity')
            order = params.get('order', 'desc')

            if sort_by in sort_mapping:
                order_prefix = '-' if order == 'desc' else ''
                queryset = queryset.order_by(f"{order_prefix}{sort_mapping[sort_by]}")

                        # Pagination with keyset support for ORM fallback
            page_size = int(params.get('page_size', 20))
            order = params.get('order', 'desc')

            # Handle keyset pagination for ORM
            if params.get('search_after'):
                # For ORM fallback, we use created_at and id for pagination
                search_after_values = params['search_after']
                if isinstance(search_after_values, list) and len(search_after_values) >= 2:
                    created_at_value = search_after_values[0]
                    id_value = search_after_values[1]
                    # Filter for keyset pagination
                    if order == 'desc':
                        queryset = queryset.filter(
                            Django_Q(created_at__lt=created_at_value) |
                            Django_Q(created_at=created_at_value, id__lt=id_value)
                        )
                    else:
                        queryset = queryset.filter(
                            Django_Q(created_at__gt=created_at_value) |
                            Django_Q(created_at=created_at_value, id__gt=id_value)
                        )
            elif params.get('page'):
                # Fallback to page-based pagination
                page = int(params.get('page', 1))
                start = (page - 1) * page_size
                queryset = queryset[start:start + page_size]
            else:
                # Default: first page
                queryset = queryset[:page_size]

            total_count = queryset.count()
            results = list(queryset[:page_size])

            # Calculate next_search_after for keyset pagination (ORM version)
            next_search_after = None
            if results and len(results) == page_size:
                last_result = results[-1]
                # Use created_at and id as sort values
                next_search_after = [
                    last_result.created_at.isoformat(),
                    last_result.id
                ]

            # Serialize results
            serializer = OptimizedMovieListSerializer(results, many=True)

            return {
                'total_count': total_count,
                'results': serializer.data,
                'search_engine': 'django_orm_fallback',
                'enhanced_with_normalized_data': True,
                'next_search_after': next_search_after,
                'from_cache': False
            }

        except Exception as e:
            logger.error(f"Fallback search failed: {str(e)}")
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

            return True
        except Exception as e:
            logger.error(f"Elasticsearch connection test failed: {str(e)}")
            return False

