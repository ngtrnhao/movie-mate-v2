import logging
import time
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from apps.movies.models import Movie
from apps.movies.services.tmdb_service import TMDBService
from django_redis import get_redis_connection
import redis
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update missing poster URLs for movies with optimized batch processing and Redis monitoring'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=50, help='Batch size for processing (default: 50)')
        parser.add_argument('--max-workers', type=int, default=5, help='Number of worker threads (default: 5)')
        parser.add_argument('--retry-count', type=int, default=3, help='Number of retries for failed operations (default: 3)')
        parser.add_argument('--retry-delay', type=float, default=1.0, help='Delay between retries in seconds (default: 1.0)')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
        parser.add_argument('--check-only', action='store_true', help='Only check missing posters count')
        parser.add_argument('--limit', type=int, help='Limit number of movies to process')
        parser.add_argument('--start-from', type=int, default=0, help='Start from specific movie ID')
        parser.add_argument('--memory-limit', type=int, default=1000, help='Memory limit in MB before clearing cache')

    def log_with_timestamp(self, message, level='info'):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"

        if level == 'error':
            self.stdout.write(self.style.ERROR(formatted_message))
            logger.error(message)
        elif level == 'warning':
            self.stdout.write(self.style.WARNING(formatted_message))
            logger.warning(message)
        elif level == 'success':
            self.stdout.write(self.style.SUCCESS(formatted_message))
            logger.info(message)
        else:
            self.stdout.write(formatted_message)
            logger.info(message)

    def check_redis_connection(self):
        """Check Redis connection and log status"""
        try:
            redis_conn = get_redis_connection("default")
            redis_conn.ping()
            self.log_with_timestamp("✅ Redis connection: OK")
            return True
        except redis.ConnectionError as e:
            self.log_with_timestamp(f"❌ Redis connection failed: {str(e)}", 'error')
            return False
        except Exception as e:
            self.log_with_timestamp(f"❌ Redis error: {str(e)}", 'error')
            return False

    def clear_redis_cache_if_needed(self, memory_limit_mb=1000):
        """Clear Redis cache if memory usage is high"""
        try:
            redis_conn = get_redis_connection("default")
            info = redis_conn.info()

            used_memory_mb = info.get('used_memory', 0) / (1024 * 1024)

            if used_memory_mb > memory_limit_mb:
                self.log_with_timestamp(f"🧹 Clearing Redis cache (memory: {used_memory_mb:.1f}MB > {memory_limit_mb}MB)")
                redis_conn.flushdb()
                self.log_with_timestamp("✅ Redis cache cleared")
                return True

        except Exception as e:
            self.log_with_timestamp(f"⚠️  Error checking/clearing Redis cache: {str(e)}", 'warning')

        return False

    def retry_operation(self, operation, max_retries=3, delay=1.0, operation_name="Operation"):
        """Retry operation with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return operation()
            except redis.ConnectionError as e:
                if attempt < max_retries - 1:
                    wait_time = delay * (2 ** attempt)
                    self.log_with_timestamp(f"⚠️  Redis connection error on attempt {attempt + 1}/{max_retries}. Retrying in {wait_time}s...", 'warning')
                    time.sleep(wait_time)
                else:
                    self.log_with_timestamp(f"❌ {operation_name} failed after {max_retries} attempts: {str(e)}", 'error')
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = delay * (2 ** attempt)
                    self.log_with_timestamp(f"⚠️  {operation_name} failed on attempt {attempt + 1}/{max_retries}. Retrying in {wait_time}s...", 'warning')
                    time.sleep(wait_time)
                else:
                    self.log_with_timestamp(f"❌ {operation_name} failed after {max_retries} attempts: {str(e)}", 'error')
                    raise

    def get_missing_posters_count(self):
        """Get count of movies missing posters"""
        missing_qs = Movie.objects.filter(
            poster_url__isnull=True
        ) | Movie.objects.filter(
            poster_url__exact=''
        )
        return missing_qs.count()

    def get_missing_posters_queryset(self, limit=None, start_from=0):
        """Get queryset of movies missing posters"""
        missing_qs = Movie.objects.filter(
            poster_url__isnull=True
        ) | Movie.objects.filter(
            poster_url__exact=''
        )

        if start_from > 0:
            missing_qs = missing_qs.filter(id__gte=start_from)

        if limit:
            missing_qs = missing_qs[:limit]

        return missing_qs

    def update_single_poster(self, movie, dry_run=False):
        """Update poster for a single movie"""
        try:
            if dry_run:
                return True, "Dry run - no changes made"

            # Get TMDB data with retry mechanism
            def get_tmdb_data():
                tmdb_service = TMDBService()
                tmdb_data = tmdb_service.get_movie_details(movie.tmdb_id) if getattr(movie, 'tmdb_id', None) else None

                if not tmdb_data and movie.imdb_id:
                    # Try to find TMDB ID from IMDB ID
                    find_result = tmdb_service.get_movie_by_imdb_id(movie.imdb_id)
                    if find_result and find_result.get("movie_results"):
                        tmdb_id = find_result["movie_results"][0]["id"]
                        movie.tmdb_id = tmdb_id
                        tmdb_data = tmdb_service.get_movie_details(tmdb_id)

                return tmdb_data

            tmdb_data = self.retry_operation(
                get_tmdb_data,
                max_retries=3,
                delay=2.0,
                operation_name=f"TMDB data fetch for {movie.imdb_id}"
            )

            if tmdb_data and tmdb_data.get('poster_path'):
                old_poster = movie.poster_url
                movie.poster_url = f"https://image.tmdb.org/t/p/w500{tmdb_data.get('poster_path')}"
                movie.save(update_fields=['poster_url', 'tmdb_id'])

                if movie.poster_url != old_poster:
                    return True, f"Updated poster: {movie.poster_url[:50]}..."
                else:
                    return False, "Poster already exists"
            else:
                return False, "No poster found in TMDB data"

        except Exception as e:
            logger.error(f"Error updating poster for movie {movie.imdb_id}: {str(e)}")
            return False, f"Error: {str(e)}"

    def process_batch(self, movies, dry_run=False, retry_count=3):
        """Process a batch of movies"""
        batch_results = {
            'success': 0,
            'error': 0,
            'redis_errors': 0,
            'timeout_errors': 0,
            'no_poster_found': 0
        }

        for movie in movies:
            try:
                success, message = self.update_single_poster(movie, dry_run)
                if success:
                    batch_results['success'] += 1
                else:
                    batch_results['error'] += 1
                    if "No poster found" in message:
                        batch_results['no_poster_found'] += 1

            except redis.ConnectionError as e:
                batch_results['redis_errors'] += 1
                batch_results['error'] += 1
                self.log_with_timestamp(f"💥 Redis connection error for movie {movie.imdb_id}: {str(e)}", 'error')
            except Exception as e:
                batch_results['error'] += 1
                if "Timeout" in str(e) or "timeout" in str(e).lower():
                    batch_results['timeout_errors'] += 1
                self.log_with_timestamp(f"💥 Error updating poster for movie {movie.imdb_id}: {str(e)}", 'error')

        return batch_results

    def handle(self, *args, **options):
        start_time = time.time()

        # Parse options
        batch_size = options['batch_size']
        max_workers = options['max_workers']
        retry_count = options['retry_count']
        retry_delay = options['retry_delay']
        dry_run = options['dry_run']
        check_only = options['check_only']
        limit = options['limit']
        start_from = options['start_from']
        memory_limit = options['memory_limit']

        # Check Redis connection first
        self.log_with_timestamp("🔍 Checking Redis connection...")
        redis_ok = self.check_redis_connection()

        if not redis_ok:
            self.log_with_timestamp("⚠️  Continuing without Redis cache...", 'warning')

        if check_only:
            total = Movie.objects.count()
            missing_count = self.get_missing_posters_count()
            percent = (missing_count / total) * 100 if total > 0 else 0
            self.log_with_timestamp(f"❌ Movies missing poster: {missing_count:,} / {total:,} ({percent:.1f}%)")
            self.log_with_timestamp(f"🔍 Sample movies without poster:")
            missing_qs = self.get_missing_posters_queryset(limit=5)
            for movie in missing_qs:
                self.log_with_timestamp(f"   - ID: {movie.id}, Title: {movie.title}, IMDB: {movie.imdb_id}")
            return

        # Get movies to process
        missing_qs = self.get_missing_posters_queryset(limit=limit, start_from=start_from)
        total_movies = missing_qs.count()

        if total_movies == 0:
            self.log_with_timestamp("✅ No movies found missing posters!", 'success')
            return

        percent = (total_movies / Movie.objects.count()) * 100
        self.log_with_timestamp(f"🚀 Updating poster for {total_movies:,} movies missing poster ({percent:.1f}%)")

        if dry_run:
            self.log_with_timestamp("🔍 DRY RUN MODE - No changes will be made")

        # Initialize counters
        overall_results = {
            'success': 0,
            'error': 0,
            'redis_errors': 0,
            'timeout_errors': 0,
            'no_poster_found': 0,
            'processed': 0
        }

        # Process in batches
        batch_number = 0
        for i in range(0, total_movies, batch_size):
            batch_number += 1
            batch_start = i
            batch_end = min(i + batch_size, total_movies)

            # Get batch of movies
            batch_movies = list(missing_qs[batch_start:batch_end])

            self.log_with_timestamp(f"📦 Processing batch {batch_number}: movies {batch_start+1}-{batch_end} of {total_movies}")

            # Clear Redis cache if needed
            self.clear_redis_cache_if_needed(memory_limit)

            # Process batch
            batch_results = self.process_batch(batch_movies, dry_run, retry_count)

            # Update overall results
            for key in batch_results:
                overall_results[key] += batch_results[key]
            overall_results['processed'] += len(batch_movies)

            # Real-time progress with detailed stats
            elapsed_time = time.time() - start_time
            avg_time_per_movie = elapsed_time / overall_results['processed']
            remaining_movies = total_movies - overall_results['processed']
            estimated_remaining_time = remaining_movies * avg_time_per_movie

            self.log_with_timestamp(f"📊 Batch {batch_number} Summary:")
            self.log_with_timestamp(f"   ✅ Success: {batch_results['success']} | ❌ Errors: {batch_results['error']}")
            self.log_with_timestamp(f"   🔴 Redis Errors: {batch_results['redis_errors']} | ⏰ Timeout: {batch_results['timeout_errors']}")
            self.log_with_timestamp(f"   📈 No Poster Found: {batch_results['no_poster_found']}")

            self.log_with_timestamp(f"📊 Overall Progress: {overall_results['processed']:,}/{total_movies:,} ({overall_results['processed']/total_movies*100:.1f}%)")
            self.log_with_timestamp(f"   ✅ Total Success: {overall_results['success']:,} | ❌ Total Errors: {overall_results['error']:,}")
            self.log_with_timestamp(f"   ⏱️  Elapsed: {elapsed_time/60:.1f}m | ⏳ ETA: {estimated_remaining_time/60:.1f}m")
            self.log_with_timestamp(f"   🎯 Success Rate: {overall_results['success']/overall_results['processed']*100:.1f}%")

            # Small delay between batches to prevent overwhelming
            if batch_number % 10 == 0:
                self.log_with_timestamp("⏳ Taking a short break between batches...")
                time.sleep(2)

        # Final summary with detailed error breakdown
        total_time = time.time() - start_time
        self.log_with_timestamp(f"\n✅ Poster update completed!", 'success')
        self.log_with_timestamp(f"📊 Final Summary:")
        self.log_with_timestamp(f"   ⏱️  Total Time: {total_time/60:.1f} minutes")
        self.log_with_timestamp(f"   📈 Total Processed: {overall_results['processed']:,}")
        self.log_with_timestamp(f"   ✅ Successful: {overall_results['success']:,}")
        self.log_with_timestamp(f"   ❌ Total Errors: {overall_results['error']:,}")
        self.log_with_timestamp(f"   🔴 Redis Errors: {overall_results['redis_errors']:,}")
        self.log_with_timestamp(f"   ⏰ Timeout Errors: {overall_results['timeout_errors']:,}")
        self.log_with_timestamp(f"   📈 No Poster Found: {overall_results['no_poster_found']:,}")

        if overall_results['processed'] > 0:
            self.log_with_timestamp(f"   🎯 Success Rate: {overall_results['success']/overall_results['processed']*100:.1f}%")
            self.log_with_timestamp(f"   📊 Avg Time per Movie: {total_time/overall_results['processed']:.2f}s")

        # Show remaining missing posters
        remaining_missing = self.get_missing_posters_count()
        self.log_with_timestamp(f"   📊 Remaining Missing Posters: {remaining_missing:,}")

        if dry_run:
            self.log_with_timestamp("🔍 DRY RUN COMPLETED - No actual changes were made")
