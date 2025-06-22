from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from apps.metadata.models import GenreSummary
import time
import requests
import json

class Command(BaseCommand):
    help = 'Test performance of categories API with new summary table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=10,
            help='Number of iterations to test',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear cache before testing',
        )
        parser.add_argument(
            '--language',
            type=str,
            default='en',
            help='Language to test (en/vi)',
        )

    def handle(self, *args, **options):
        iterations = options['iterations']
        clear_cache = options['clear_cache']
        language = options['language']

        if clear_cache:
            cache.delete_pattern('movie_categories_summary_*')
            self.stdout.write(
                self.style.SUCCESS('Cache cleared')
            )

        self.stdout.write(
            self.style.SUCCESS(f'Testing categories API performance for {iterations} iterations...')
        )

        # Test Summary Table performance
        self.test_summary_table_performance(language, iterations)

        # Test Raw SQL performance
        self.test_raw_sql_performance(language, iterations)

        # Test API endpoint performance (if server is running)
        self.test_api_endpoint_performance(language, iterations)

    def test_summary_table_performance(self, language, iterations):
        """Test performance using Summary Table"""
        self.stdout.write('\n=== Testing Summary Table Performance ===')

        times = []
        for i in range(iterations):
            start_time = time.time()

            try:
                with connection.cursor() as cursor:
                    sql = """
                    SELECT
                        g.id,
                        g.name,
                        g.slug,
                        g.description,
                        g.language,
                        gs.movie_count as count,
                        gs.latest_movie_data as latest_movie
                    FROM metadata_genre g
                    INNER JOIN metadata_genre_summary gs ON g.id = gs.genre_id
                    WHERE gs.language = %s AND gs.movie_count > 0
                    ORDER BY g.name
                    """

                    cursor.execute(sql, [language])
                    results = cursor.fetchall()

                query_time = time.time() - start_time
                times.append(query_time)

                if i == 0:  # First iteration
                    self.stdout.write(f'Found {len(results)} categories')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error in iteration {i}: {str(e)}')
                )

        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            self.stdout.write(f'Summary Table Performance:')
            self.stdout.write(f'  Average: {avg_time:.3f}s ({avg_time*1000:.1f}ms)')
            self.stdout.write(f'  Min: {min_time:.3f}s ({min_time*1000:.1f}ms)')
            self.stdout.write(f'  Max: {max_time:.3f}s ({max_time*1000:.1f}ms)')

    def test_raw_sql_performance(self, language, iterations):
        """Test performance using Raw SQL (fallback method)"""
        self.stdout.write('\n=== Testing Raw SQL Performance ===')

        times = []
        for i in range(iterations):
            start_time = time.time()

            try:
                with connection.cursor() as cursor:
                    sql = """
                    SELECT
                        g.id,
                        g.name,
                        g.slug,
                        g.description,
                        g.language,
                        COUNT(mg.movie_id) as count,
                        (
                            SELECT json_build_object(
                                'id', m.id,
                                'title', m.title,
                                'poster_url', m.poster_url,
                                'release_date', m.release_date
                            )
                            FROM movies_movie m
                            INNER JOIN movies_movie_genres mg2 ON m.id = mg2.movie_id
                            WHERE mg2.genre_id = g.id
                            AND m.poster_url IS NOT NULL
                            AND m.poster_url != ''
                            ORDER BY m.release_date DESC
                            LIMIT 1
                        ) as latest_movie
                    FROM metadata_genre g
                    INNER JOIN movies_movie_genres mg ON g.id = mg.genre_id
                    WHERE g.language = %s
                    GROUP BY g.id, g.name, g.slug, g.description, g.language
                    HAVING COUNT(mg.movie_id) > 0
                    ORDER BY g.name
                    """

                    cursor.execute(sql, [language])
                    results = cursor.fetchall()

                query_time = time.time() - start_time
                times.append(query_time)

                if i == 0:  # First iteration
                    self.stdout.write(f'Found {len(results)} categories')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error in iteration {i}: {str(e)}')
                )

        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            self.stdout.write(f'Raw SQL Performance:')
            self.stdout.write(f'  Average: {avg_time:.3f}s ({avg_time*1000:.1f}ms)')
            self.stdout.write(f'  Min: {min_time:.3f}s ({min_time*1000:.1f}ms)')
            self.stdout.write(f'  Max: {max_time:.3f}s ({max_time*1000:.1f}ms)')

    def test_api_endpoint_performance(self, language, iterations):
        """Test performance of actual API endpoint"""
        self.stdout.write('\n=== Testing API Endpoint Performance ===')

        # Check if server is running
        try:
            response = requests.get('http://localhost:8000/api/categories/', timeout=5)
            if response.status_code != 200:
                self.stdout.write(
                    self.style.WARNING('Server not running or API not accessible')
                )
                return
        except:
            self.stdout.write(
                self.style.WARNING('Server not running or API not accessible')
            )
            return

        times = []
        for i in range(iterations):
            start_time = time.time()

            try:
                response = requests.get(
                    f'http://localhost:8000/api/categories/?language={language}',
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    query_time = time.time() - start_time
                    times.append(query_time)

                    if i == 0:  # First iteration
                        self.stdout.write(f'Found {data.get("count", 0)} categories')
                        self.stdout.write(f'Method used: {data.get("method", "Unknown")}')
                        if 'performance' in data:
                            perf = data['performance']
                            self.stdout.write(f'Query time: {perf.get("query_time_ms", 0):.1f}ms')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error in iteration {i}: {str(e)}')
                )

        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            self.stdout.write(f'API Endpoint Performance:')
            self.stdout.write(f'  Average: {avg_time:.3f}s ({avg_time*1000:.1f}ms)')
            self.stdout.write(f'  Min: {min_time:.3f}s ({min_time*1000:.1f}ms)')
            self.stdout.write(f'  Max: {max_time:.3f}s ({max_time*1000:.1f}ms)')
