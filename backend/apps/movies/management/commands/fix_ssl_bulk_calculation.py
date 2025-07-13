from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.utils import timezone
from apps.movies.models import Movie, MovieQualityMetrics
from apps.movies.services.quality_calculation_service import QualityCalculationService
import logging
import time
import gc
from django.db import models
import psutil
import os

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '🔧 Fix SSL connection issues in bulk quality calculation with ultra-conservative settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=3,  # Ultra small batch for SSL stability
            help='Ultra small batch size for SSL stability'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,  # Longer delay
            help='Delay between batches (seconds)'
        )
        parser.add_argument(
            '--max-memory',
            type=int,
            default=500,  # 500MB limit
            help='Maximum memory usage in MB before cleanup'
        )
        parser.add_argument(
            '--start-id',
            type=int,
            help='Start from specific movie ID'
        )
        parser.add_argument(
            '--end-id',
            type=int,
            help='End at specific movie ID'
        )
        parser.add_argument(
            '--resume',
            action='store_true',
            help='Resume from last processed movie'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Test without making changes'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        delay = options['delay']
        max_memory = options['max_memory']
        start_id = options.get('start_id')
        end_id = options.get('end_id')
        resume = options['resume']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('🔧 SSL-Safe Bulk Quality Calculation'))
        self.stdout.write(f'📊 Ultra-conservative batch size: {batch_size}')
        self.stdout.write(f'⏱️ Extended delay: {delay}s')
        self.stdout.write(f'💾 Memory limit: {max_memory}MB')

        if dry_run:
            self.stdout.write(self.style.WARNING('🧪 DRY RUN MODE'))

        # Resume from last processed movie if requested
        if resume:
            start_id = self._get_last_processed_id() + 1
            self.stdout.write(f'🔄 Resuming from movie ID: {start_id}')

        # Build ultra-conservative queryset
        queryset = self._build_safe_queryset(start_id, end_id)
        total_count = queryset.count()

        if total_count == 0:
            self.stdout.write(self.style.WARNING('⚠️ No movies found to process'))
            return

        self.stdout.write(f'🎬 Found {total_count:,} movies to process')

        # Initialize service
        quality_service = QualityCalculationService()

        # Process with ultra-conservative approach
        processed = 0
        errors = 0
        skipped = 0
        start_time = time.time()

        for batch_start in range(0, total_count, batch_size):
            batch_end = min(batch_start + batch_size, total_count)

            try:
                # Memory check before processing
                if self._check_memory_usage() > max_memory:
                    self.stdout.write(self.style.WARNING('💾 Memory limit reached, performing cleanup'))
                    self._aggressive_cleanup()
                    time.sleep(delay * 2)  # Extra delay after cleanup

                # Get batch with minimal queries
                batch_movies = list(queryset[batch_start:batch_end])

                # Process each movie individually with full isolation
                for movie in batch_movies:
                    try:
                        if dry_run:
                            self.stdout.write(
                                f'🧪 [DRY RUN] Movie {movie.id}: {movie.title[:30]}...'
                            )
                            processed += 1
                        else:
                            # Check if already processed (avoid duplicates)
                            if self._is_already_processed(movie):
                                skipped += 1
                                continue

                            # Process with full transaction isolation
                            with transaction.atomic():
                                result = quality_service.calculate_movie_quality(movie, save=True)
                                if result:
                                    processed += 1
                                    self._save_progress(movie.id)

                        # Micro-delay between movies
                        time.sleep(0.1)

                    except Exception as e:
                        errors += 1
                        logger.error(f"Error processing movie {movie.id}: {str(e)}")

                        # Reset connection after error
                        self._reset_connection()
                        time.sleep(delay)
                        continue

                # Progress report
                if (batch_end // batch_size) % 10 == 0:
                    progress = (batch_end / total_count) * 100
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    memory_usage = self._check_memory_usage()

                    self.stdout.write(
                        f'📈 Progress: {progress:.1f}% ({batch_end:,}/{total_count:,}) - '
                        f'✅ {processed:,} | ❌ {errors:,} | ⏭️ {skipped:,} | '
                        f'🚀 {rate:.1f}/s | 💾 {memory_usage}MB'
                    )

                # Aggressive cleanup after each batch
                self._aggressive_cleanup()

                # Extended delay between batches
                time.sleep(delay)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Batch {batch_start}-{batch_end} failed: {e}')
                )
                errors += len(batch_movies) if 'batch_movies' in locals() else batch_size
                self._reset_connection()
                time.sleep(delay * 3)  # Extra long delay after batch error

        # Final report
        total_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f'🎉 Processing completed in {total_time:.1f}s'))
        self.stdout.write(f'📊 Final Results:')
        self.stdout.write(f'  ✅ Successfully processed: {processed:,}')
        self.stdout.write(f'  ❌ Errors: {errors:,}')
        self.stdout.write(f'  ⏭️ Skipped: {skipped:,}')
        self.stdout.write(f'  🚀 Average rate: {processed/total_time:.1f} movies/second')

    def _build_safe_queryset(self, start_id, end_id):
        """Build queryset with minimal database load"""
        queryset = Movie.objects.only('id', 'title', 'poster_url').filter(
            title__isnull=False
        ).exclude(
            title__exact=''
        )

        if start_id:
            queryset = queryset.filter(id__gte=start_id)
        if end_id:
            queryset = queryset.filter(id__lte=end_id)

        return queryset.order_by('id')

    def _is_already_processed(self, movie):
        """Check if movie already has recent quality metrics"""
        try:
            if hasattr(movie, 'quality_metrics') and movie.quality_metrics:
                # Check if processed within last 7 days
                if movie.quality_metrics.last_quality_check:
                    days_ago = (timezone.now() - movie.quality_metrics.last_quality_check).days
                    return days_ago < 7
            return False
        except:
            return False

    def _check_memory_usage(self):
        """Check current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def _aggressive_cleanup(self):
        """Aggressive cleanup to prevent memory/connection issues"""
        try:
            # Close all database connections
            connection.close()

            # Force garbage collection
            gc.collect()

            # Additional cleanup
            import django
            django.core.cache.cache.clear()

            # Small delay for cleanup to complete
            time.sleep(0.5)

        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

    def _reset_connection(self):
        """Reset database connection after error"""
        try:
            connection.close()
            connection.connect()
        except Exception as e:
            logger.error(f"Connection reset failed: {e}")

    def _get_last_processed_id(self):
        """Get the ID of the last processed movie"""
        try:
            last_quality = MovieQualityMetrics.objects.order_by('-movie_id').first()
            return last_quality.movie_id if last_quality else 0
        except:
            return 0

    def _save_progress(self, movie_id):
        """Save progress to a simple file for resume functionality"""
        try:
            with open('quality_calculation_progress.txt', 'w') as f:
                f.write(str(movie_id))
        except:
            pass  # Ignore file save errors
