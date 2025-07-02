from django.core.management.base import BaseCommand
from django.conf import settings
from apps.movies.services.search_service import MovieSearchService
from apps.movies.views import OptimizedMovieViewSet
from django.test import RequestFactory
import time
import json

class Command(BaseCommand):
    help = 'Test search integration between Elasticsearch and Django ORM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--query',
            type=str,
            default='avenger',
            help='Search query to test'
        )
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare Elasticsearch vs Django ORM performance',
        )

    def handle(self, *args, **options):
        query = options.get('query', 'avenger')
        compare = options.get('compare', False)

        self.stdout.write(self.style.SUCCESS(f'Testing search integration with query: "{query}"'))

        # Test Elasticsearch connection
        self.test_elasticsearch_connection()

        # Test search functionality
        self.test_search_functionality(query)

        if compare:
            self.compare_search_performance(query)

    def test_elasticsearch_connection(self):
        """Test Elasticsearch connection and health"""
        self.stdout.write('\n=== Testing Elasticsearch Connection ===')

        try:
            search_service = MovieSearchService()

            # Test health check
            if search_service.health_check():
                self.stdout.write(self.style.SUCCESS('✅ Elasticsearch connection successful'))
            else:
                self.stdout.write(self.style.ERROR('❌ Elasticsearch connection failed'))
                return False

            # Test index existence
            from elasticsearch_dsl import Search
            search = Search(using=search_service.client, index='movies')

            try:
                response = search.execute()
                total_docs = response.hits.total.value
                self.stdout.write(self.style.SUCCESS(f'✅ Movies index found with {total_docs:,} documents'))
                return True
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error accessing movies index: {str(e)}'))
                return False

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Elasticsearch setup error: {str(e)}'))
            return False

    def test_search_functionality(self, query):
        """Test search functionality with various filters"""
        self.stdout.write(f'\n=== Testing Search Functionality ===')

        try:
            search_service = MovieSearchService()

            # Test 1: Basic search
            self.stdout.write(f'🔍 Testing basic search for: "{query}"')
            params = {'q': query, 'page_size': 5}
            results = search_service.search(params)

            if results.hits:
                self.stdout.write(self.style.SUCCESS(f'✅ Found {len(results.hits)} results'))
                for hit in results.hits[:3]:
                    title = hit.title_en or hit.title_vi or 'Unknown Title'
                    self.stdout.write(f'   📽️  {title}')
            else:
                self.stdout.write(self.style.WARNING('⚠️  No results found'))

            # Test 2: Search with filters
            self.stdout.write(f'\n🔍 Testing search with genre filter')
            params = {
                'q': query,
                'genres': ['Action'],
                'page_size': 5
            }
            results = search_service.search(params)
            self.stdout.write(self.style.SUCCESS(f'✅ Found {len(results.hits)} Action movies'))

            # Test 3: Search with year filter
            self.stdout.write(f'\n🔍 Testing search with year filter (2020+)')
            params = {
                'q': query,
                'year_from': '2020',
                'page_size': 5
            }
            results = search_service.search(params)
            self.stdout.write(self.style.SUCCESS(f'✅ Found {len(results.hits)} movies from 2020+'))

            # Test 4: Sorting
            self.stdout.write(f'\n🔍 Testing sorting by rating')
            params = {
                'q': query,
                'sort_by': 'rating',
                'order': 'desc',
                'page_size': 3
            }
            results = search_service.search(params)
            self.stdout.write(self.style.SUCCESS(f'✅ Found {len(results.hits)} movies sorted by rating'))

            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Search functionality error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
            return False

    def compare_search_performance(self, query):
        """Compare Elasticsearch vs Django ORM performance"""
        self.stdout.write(f'\n=== Performance Comparison ===')

        # Prepare request factory
        factory = RequestFactory()

        # Test Elasticsearch
        self.stdout.write('⏱️  Testing Elasticsearch performance...')
        es_start = time.time()

        try:
            search_service = MovieSearchService()
            params = {
                'q': query,
                'page_size': 20,
                'sort_by': 'popularity'
            }
            es_results = search_service.search(params)
            es_time = time.time() - es_start
            es_count = len(es_results.hits)
            es_total = es_results.hits.total.value

            self.stdout.write(self.style.SUCCESS(
                f'✅ Elasticsearch: {es_time:.3f}s, {es_count} results, {es_total:,} total'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Elasticsearch error: {str(e)}'))
            es_time = float('inf')
            es_count = 0
            es_total = 0

        # Test Django ORM
        self.stdout.write('⏱️  Testing Django ORM performance...')
        orm_start = time.time()

        try:
            # Create mock request for Django ORM
            request = factory.get('/api/movies/search/', {
                'q': query,
                'page_size': 20,
                'sort_by': 'popularity',
                'use_django': 'true'  # Force Django ORM
            })

            # Create viewset instance
            viewset = OptimizedMovieViewSet()
            viewset.request = request

            # Call search method
            response = viewset.search(request)
            orm_time = time.time() - orm_start

            if response.status_code == 200:
                data = response.data
                orm_count = len(data.get('data', []))
                orm_total = data.get('count', 0)

                self.stdout.write(self.style.SUCCESS(
                    f'✅ Django ORM: {orm_time:.3f}s, {orm_count} results, {orm_total:,} total'
                ))
            else:
                raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Django ORM error: {str(e)}'))
            orm_time = float('inf')
            orm_count = 0
            orm_total = 0

        # Compare results
        self.stdout.write('\n📊 Performance Summary:')
        self.stdout.write('-' * 50)

        if es_time != float('inf') and orm_time != float('inf'):
            speedup = orm_time / es_time if es_time > 0 else 1

            if speedup > 1:
                self.stdout.write(self.style.SUCCESS(
                    f'🚀 Elasticsearch is {speedup:.1f}x faster than Django ORM'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'⚠️  Django ORM is {1/speedup:.1f}x faster than Elasticsearch'
                ))

        # Results comparison
        if es_total != orm_total:
            self.stdout.write(self.style.WARNING(
                f'⚠️  Result count difference: ES={es_total:,}, ORM={orm_total:,}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'✅ Both engines returned same total count: {es_total:,}'
            ))

    def test_api_integration(self, query):
        """Test API integration end-to-end"""
        self.stdout.write(f'\n=== Testing API Integration ===')

        factory = RequestFactory()

        # Test with Elasticsearch (default)
        request = factory.get('/api/movies/search/', {
            'q': query,
            'page_size': 5
        })

        viewset = OptimizedMovieViewSet()
        viewset.request = request

        try:
            response = viewset.search(request)

            if response.status_code == 200:
                data = response.data
                engine = data.get('search_engine', 'unknown')
                count = len(data.get('data', []))

                self.stdout.write(self.style.SUCCESS(
                    f'✅ API Integration successful: {engine} engine, {count} results'
                ))

                # Show sample results
                if data.get('data'):
                    self.stdout.write('📝 Sample results:')
                    for movie in data['data'][:3]:
                        title = movie.get('title_en') or movie.get('title_vi') or movie.get('title', 'Unknown')
                        rating = movie.get('vote_average') or movie.get('cached_imdb_rating', 'N/A')
                        self.stdout.write(f'   📽️  {title} (Rating: {rating})')

                return True
            else:
                self.stdout.write(self.style.ERROR(f'❌ API returned status {response.status_code}'))
                return False

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ API integration error: {str(e)}'))
            return False
