from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, connections
from apps.movies.models import Movie, MovieQualityMetrics, MovieScheduling
from apps.movies.document import MovieDocument
from apps.movies.services.search_service import MovieSearchService
import os
import json
import time

class Command(BaseCommand):
    help = 'Comprehensive test of Elasticsearch integration with normalized structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--connection-only',
            action='store_true',
            help='Only test connection, skip search tests'
        )
        parser.add_argument(
            '--search-only',
            action='store_true',
            help='Only test search functionality'
        )
        parser.add_argument(
            '--quality-metrics',
            action='store_true',
            help='Test quality metrics integration'
        )
        parser.add_argument(
            '--scheduling',
            action='store_true',
            help='Test scheduling integration'
        )
        parser.add_argument(
            '--performance',
            action='store_true',
            help='Run performance benchmarks'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed results'
        )

    def handle(self, *args, **options):
        self.detailed = options.get('detailed', False)

        self.stdout.write(self.style.SUCCESS('🔍 Enhanced Elasticsearch Integration Test'))
        self.stdout.write('=' * 70)

        # Test connection
        if not options.get('search_only'):
            self.test_connection()

        # Test search functionality
        if not options.get('connection_only'):
            self.test_search_functionality()

        # Test quality metrics
        if options.get('quality_metrics'):
            self.test_quality_metrics_integration()

        # Test scheduling
        if options.get('scheduling'):
            self.test_scheduling_integration()

        # Performance benchmarks
        if options.get('performance'):
            self.run_performance_benchmarks()

        self.stdout.write(self.style.SUCCESS('✅ All tests completed!'))

    def test_connection(self):
        """Test Elasticsearch connection and configuration"""
        self.stdout.write('\n🔌 Testing Elasticsearch Connection')
        self.stdout.write('-' * 50)

        try:
            # Test connection settings
            if hasattr(settings, 'ELASTICSEARCH_DSL'):
                es_settings = settings.ELASTICSEARCH_DSL['default']
                self.stdout.write(f"📡 Host: {es_settings.get('hosts', ['localhost:9200'])}")

                # Mask sensitive information
                if 'http_auth' in es_settings:
                    username = es_settings['http_auth'][0] if es_settings['http_auth'] else 'None'
                    self.stdout.write(f"👤 Username: {username}")
                    self.stdout.write(f"🔒 Password: {'*' * len(es_settings['http_auth'][1]) if es_settings['http_auth'] and len(es_settings['http_auth']) > 1 else 'None'}")

            # Test connection
            es = connections.get_connection()

            # Cluster health
            health = es.cluster.health()
            status = health['status']
            status_icon = '🟢' if status == 'green' else '🟡' if status == 'yellow' else '🔴'
            self.stdout.write(f"{status_icon} Cluster Status: {status}")
            self.stdout.write(f"📊 Nodes: {health['number_of_nodes']}")
            self.stdout.write(f"🔢 Data Nodes: {health['number_of_data_nodes']}")

            # Cluster info
            info = es.info()
            self.stdout.write(f"🏷️ Cluster Name: {info['cluster_name']}")
            self.stdout.write(f"📦 Version: {info['version']['number']}")

            # Index information
            if es.indices.exists(index='movies'):
                stats = es.indices.stats(index='movies')
                movie_stats = stats['indices']['movies']

                doc_count = movie_stats['total']['docs']['count']
                index_size = movie_stats['total']['store']['size_in_bytes']

                self.stdout.write(f"📄 Documents: {doc_count:,}")
                self.stdout.write(f"💾 Index Size: {index_size / (1024*1024):.1f} MB")

                # Test mapping
                mapping = es.indices.get_mapping(index='movies')
                properties = mapping['movies']['mappings']['properties']

                # Check for new normalized fields
                normalized_fields = [
                    'quality_score', 'content_completeness', 'overall_quality_rating',
                    'scheduling_publish_date', 'campaign_name', 'campaign_type',
                    'performance_score', 'trending_score', 'trending_category'
                ]

                self.stdout.write(f"🗂️ Mapping Fields: {len(properties)}")
                missing_fields = [field for field in normalized_fields if field not in properties]

                if missing_fields:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ Missing normalized fields: {', '.join(missing_fields)}")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS("✅ All normalized fields present in mapping")
                    )

            else:
                self.stdout.write(self.style.ERROR("❌ Movies index does not exist"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Connection test failed: {e}"))

    def test_search_functionality(self):
        """Test search functionality with normalized fields"""
        self.stdout.write('\n🔍 Testing Search Functionality')
        self.stdout.write('-' * 50)

        search_service = MovieSearchService()

        if not search_service.connection_available:
            self.stdout.write(self.style.ERROR("❌ Search service not available"))
            return

        # Test basic search
        test_queries = [
            'action',
            'comedy',
            'spider',
            'avengers',
            'batman'
        ]

        for query in test_queries:
            try:
                start_time = time.time()
                result = search_service.search({'q': query, 'page_size': 10})
                end_time = time.time()

                if result:
                    self.stdout.write(
                        f"🔍 Query '{query}': {result['total_count']} results in {(end_time - start_time)*1000:.0f}ms"
                    )

                    if self.detailed and result['results']:
                        # Show first result details
                        first_result = result['results'][0]
                        self.stdout.write(f"  📄 First result: {first_result.get('title', 'N/A')}")
                        self.stdout.write(f"     Quality Score: {first_result.get('quality_score', 'N/A')}")
                        self.stdout.write(f"     Completeness: {first_result.get('content_completeness', 'N/A')}%")
                else:
                    self.stdout.write(f"❌ Query '{query}' failed")

            except Exception as e:
                self.stdout.write(f"❌ Query '{query}' error: {e}")

        # Test advanced search with normalized fields
        self.stdout.write('\n🎯 Testing Advanced Search Features')

        advanced_tests = [
            {
                'name': 'Quality Score Filter',
                'params': {'q': 'action', 'quality_score_min': 7.0, 'page_size': 5}
            },
            {
                'name': 'Content Completeness Filter',
                'params': {'q': 'drama', 'content_completeness_min': 80.0, 'page_size': 5}
            },
            {
                'name': 'Trending Category Filter',
                'params': {'trending_category': ['viral', 'hot'], 'page_size': 5}
            },
            {
                'name': 'Performance Score Filter',
                'params': {'performance_score_min': 6.0, 'page_size': 5}
            }
        ]

        for test in advanced_tests:
            try:
                start_time = time.time()
                result = search_service.search(test['params'])
                end_time = time.time()

                if result:
                    self.stdout.write(
                        f"🎯 {test['name']}: {result['total_count']} results in {(end_time - start_time)*1000:.0f}ms"
                    )
                else:
                    self.stdout.write(f"❌ {test['name']} failed")

            except Exception as e:
                self.stdout.write(f"❌ {test['name']} error: {e}")

    def test_quality_metrics_integration(self):
        """Test quality metrics integration"""
        self.stdout.write('\n📊 Testing Quality Metrics Integration')
        self.stdout.write('-' * 50)

        try:
            # Check database quality metrics
            quality_metrics_count = MovieQualityMetrics.objects.count()
            movies_with_quality = Movie.objects.filter(quality_metrics__isnull=False).count()

            self.stdout.write(f"📊 Quality Metrics Records: {quality_metrics_count:,}")
            self.stdout.write(f"🎬 Movies with Quality Data: {movies_with_quality:,}")

            # Test quality aggregations
            search_service = MovieSearchService()
            insights = search_service.get_quality_insights()

            if insights:
                quality_data = insights['quality_insights']
                self.stdout.write(f"📈 Average Quality Score: {quality_data.get('avg_quality_score', 0):.1f}")
                self.stdout.write(f"📊 Average Completeness: {quality_data.get('avg_content_completeness', 0):.1f}%")
                self.stdout.write(f"⚠️ Quality Issues: {quality_data.get('quality_issues_count', 0):,}")
                self.stdout.write(f"❌ Below Minimum Quality: {quality_data.get('minimum_quality_not_met', 0):,}")
                self.stdout.write(f"🔍 Need Review: {quality_data.get('needs_quality_review', 0):,}")

            # Test quality-based search
            quality_search = search_service.search({
                'quality_score_min': 8.0,
                'content_completeness_min': 90.0,
                'page_size': 10
            })

            if quality_search:
                self.stdout.write(f"🌟 High Quality Movies: {quality_search['total_count']:,}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Quality metrics test failed: {e}"))

    def test_scheduling_integration(self):
        """Test scheduling integration"""
        self.stdout.write('\n📅 Testing Scheduling Integration')
        self.stdout.write('-' * 50)

        try:
            # Check database scheduling data
            scheduling_count = MovieScheduling.objects.count()
            movies_with_scheduling = Movie.objects.filter(scheduling__isnull=False).count()

            self.stdout.write(f"📅 Scheduling Records: {scheduling_count:,}")
            self.stdout.write(f"🎬 Movies with Scheduling: {movies_with_scheduling:,}")

            # Test scheduling aggregations
            search_service = MovieSearchService()
            insights = search_service.get_quality_insights()

            if insights:
                scheduling_data = insights['scheduling_insights']
                self.stdout.write(f"📤 Scheduled for Publish: {scheduling_data.get('scheduled_for_publish', 0):,}")
                self.stdout.write(f"⭐ Scheduled for Feature: {scheduling_data.get('scheduled_for_feature', 0):,}")
                self.stdout.write(f"⏰ Pending Actions: {scheduling_data.get('pending_actions', 0):,}")

            # Test scheduling-based search
            scheduling_search = search_service.search({
                'is_published_now': True,
                'is_featured_now': True,
                'page_size': 10
            })

            if scheduling_search:
                self.stdout.write(f"🌟 Currently Published & Featured: {scheduling_search['total_count']:,}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Scheduling test failed: {e}"))

    def run_performance_benchmarks(self):
        """Run performance benchmarks"""
        self.stdout.write('\n🚀 Performance Benchmarks')
        self.stdout.write('-' * 50)

        search_service = MovieSearchService()

        # Test queries with different complexities
        benchmark_queries = [
            {'name': 'Simple Search', 'params': {'q': 'action', 'page_size': 20}},
            {'name': 'Complex Search', 'params': {
                'q': 'action',
                'quality_score_min': 6.0,
                'content_completeness_min': 70.0,
                'trending_category': ['viral', 'hot'],
                'page_size': 20
            }},
            {'name': 'Admin Search', 'params': {
                'q': 'drama',
                'quality_score_min': 5.0,
                'has_quality_issues': True,
                'page_size': 20
            }},
            {'name': 'Large Result Set', 'params': {'q': 'the', 'page_size': 100}}
        ]

        for benchmark in benchmark_queries:
            times = []

            # Run each query 5 times
            for i in range(5):
                start_time = time.time()
                result = search_service.search(benchmark['params'])
                end_time = time.time()

                if result:
                    times.append((end_time - start_time) * 1000)
                else:
                    times.append(None)

            # Calculate statistics
            valid_times = [t for t in times if t is not None]

            if valid_times:
                avg_time = sum(valid_times) / len(valid_times)
                min_time = min(valid_times)
                max_time = max(valid_times)

                self.stdout.write(f"⚡ {benchmark['name']}:")
                self.stdout.write(f"   Average: {avg_time:.0f}ms")
                self.stdout.write(f"   Range: {min_time:.0f}ms - {max_time:.0f}ms")

                if result:
                    self.stdout.write(f"   Results: {result['total_count']:,}")
            else:
                self.stdout.write(f"❌ {benchmark['name']}: All queries failed")

        # Test fallback performance
        self.stdout.write('\n🔄 Testing Fallback Performance')

        # Temporarily disable Elasticsearch to test fallback
        original_connection = search_service.connection_available
        search_service.connection_available = False

        try:
            start_time = time.time()
            fallback_result = search_service.fallback_search({'q': 'action', 'page_size': 20})
            end_time = time.time()

            if fallback_result:
                self.stdout.write(f"🔄 Fallback Search: {(end_time - start_time)*1000:.0f}ms")
                self.stdout.write(f"   Results: {fallback_result['total_count']:,}")
            else:
                self.stdout.write("❌ Fallback search failed")

        finally:
            search_service.connection_available = original_connection

        # Compare Elasticsearch vs Django ORM performance
        self.stdout.write('\n⚔️ Performance Comparison')

        test_query = {'q': 'action', 'page_size': 50}

        # Elasticsearch
        es_times = []
        for i in range(3):
            start_time = time.time()
            es_result = search_service.search(test_query)
            end_time = time.time()
            if es_result:
                es_times.append((end_time - start_time) * 1000)

        # Django ORM
        orm_times = []
        for i in range(3):
            start_time = time.time()
            orm_result = search_service.fallback_search(test_query)
            end_time = time.time()
            if orm_result:
                orm_times.append((end_time - start_time) * 1000)

        if es_times and orm_times:
            es_avg = sum(es_times) / len(es_times)
            orm_avg = sum(orm_times) / len(orm_times)
            speedup = orm_avg / es_avg if es_avg > 0 else 0

            self.stdout.write(f"🔍 Elasticsearch: {es_avg:.0f}ms average")
            self.stdout.write(f"🗃️ Django ORM: {orm_avg:.0f}ms average")
            self.stdout.write(f"⚡ Speedup: {speedup:.1f}x faster" if speedup > 1 else f"⚠️ Slower: {1/speedup:.1f}x")

    def test_admin_features(self):
        """Test admin-specific features"""
        self.stdout.write('\n👨‍💼 Testing Admin Features')
        self.stdout.write('-' * 50)

        search_service = MovieSearchService()

        # Test admin mode search
        admin_tests = [
            {
                'name': 'Quality Issues Filter',
                'params': {'has_quality_issues': True, 'page_size': 10}
            },
            {
                'name': 'Needs Review Filter',
                'params': {'needs_quality_review': True, 'page_size': 10}
            },
            {
                'name': 'Pending Actions Filter',
                'params': {'scheduled_actions_pending': True, 'page_size': 10}
            }
        ]

        for test in admin_tests:
            try:
                result = search_service.search(test['params'], admin_mode=True)
                if result:
                    self.stdout.write(f"👨‍💼 {test['name']}: {result['total_count']} results")
                else:
                    self.stdout.write(f"❌ {test['name']} failed")
            except Exception as e:
                self.stdout.write(f"❌ {test['name']} error: {e}")

        # Test advanced search with analytics
        try:
            advanced_result = search_service.advanced_search({'q': 'action'})
            if advanced_result and 'analytics' in advanced_result:
                analytics = advanced_result['analytics']
                self.stdout.write(f"📊 Analytics available: {list(analytics.keys())}")

                if self.detailed:
                    for key, data in analytics.items():
                        self.stdout.write(f"  {key}: {len(data)} buckets")
        except Exception as e:
            self.stdout.write(f"❌ Advanced search analytics error: {e}")

    def get_db_statistics(self):
        """Get database statistics for comparison"""
        self.stdout.write('\n📊 Database Statistics')
        self.stdout.write('-' * 50)

        try:
            total_movies = Movie.objects.count()
            movies_with_poster = Movie.objects.filter(
                poster_url__isnull=False
            ).exclude(poster_url__exact='').count()

            quality_metrics = MovieQualityMetrics.objects.count()
            scheduling_records = MovieScheduling.objects.count()

            self.stdout.write(f"🎬 Total Movies: {total_movies:,}")
            self.stdout.write(f"🖼️ Movies with Poster: {movies_with_poster:,}")
            self.stdout.write(f"📊 Quality Metrics: {quality_metrics:,}")
            self.stdout.write(f"📅 Scheduling Records: {scheduling_records:,}")

            # Coverage statistics
            quality_coverage = (quality_metrics / total_movies) * 100 if total_movies > 0 else 0
            scheduling_coverage = (scheduling_records / total_movies) * 100 if total_movies > 0 else 0

            self.stdout.write(f"📈 Quality Coverage: {quality_coverage:.1f}%")
            self.stdout.write(f"📈 Scheduling Coverage: {scheduling_coverage:.1f}%")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Database statistics error: {e}"))
