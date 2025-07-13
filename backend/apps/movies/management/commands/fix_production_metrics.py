from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.utils import timezone
from apps.movies.models import Movie, ProductionMetrics
from apps.movies.services.user_data_collection_service import UserDataCollectionService
from apps.movies.services.production_metrics_service import ProductionMetricsService
import logging
import time
import gc
from django.db import models

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix connection issues and recalculate production metrics with proper error handling'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of movies to process per batch (smaller for connection stability)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            help='Delay between batches in seconds to prevent connection timeout'
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
            '--dry-run',
            action='store_true',
            help='Test without making actual changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recalculate even for existing metrics'
        )
        parser.add_argument(
            '--use-existing-data',
            action='store_true',
            help='Calculate from existing database data instead of real user data'
        )
        parser.add_argument(
            '--fix-missing-only',
            action='store_true',
            help='Only process movies without production metrics'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        delay = options['delay']
        start_id = options.get('start_id')
        end_id = options.get('end_id')
        dry_run = options['dry_run']
        force = options['force']
        use_existing_data = options['use_existing_data']
        fix_missing_only = options['fix_missing_only']

        self.stdout.write(self.style.SUCCESS('🔧 Fixing Production Metrics with Connection Stability'))
        self.stdout.write(f'📊 Batch size: {batch_size} (optimized for connection stability)')
        self.stdout.write(f'⏱️ Delay between batches: {delay}s')

        if dry_run:
            self.stdout.write(self.style.WARNING('🧪 DRY RUN MODE - No changes will be made'))

        # Initialize services
        if use_existing_data:
            service = UserDataCollectionService()
            self.stdout.write('📊 Using UserDataCollectionService (existing data calculation)')
        else:
            service = ProductionMetricsService()
            self.stdout.write('📈 Using ProductionMetricsService (advanced calculation)')

        # Build queryset
        queryset = self._build_queryset(start_id, end_id, fix_missing_only, force)
        total_count = queryset.count()

        if total_count == 0:
            self.stdout.write(self.style.WARNING('⚠️ No movies found to process'))
            return

        self.stdout.write(f'🎬 Found {total_count} movies to process')

        # Process in batches with connection management
        processed = 0
        errors = 0
        skipped = 0
        start_time = time.time()

        for batch_start in range(0, total_count, batch_size):
            batch_end = min(batch_start + batch_size, total_count)

            try:
                # Get batch
                batch_movies = list(queryset[batch_start:batch_end])

                # Process batch with connection management
                batch_result = self._process_batch_safe(
                    batch_movies, service, dry_run, use_existing_data
                )

                processed += batch_result['processed']
                errors += batch_result['errors']
                skipped += batch_result['skipped']

                # Progress report
                progress = (batch_end / total_count) * 100
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                eta = (total_count - batch_end) / rate if rate > 0 else 0

                self.stdout.write(
                    f'📈 Progress: {progress:.1f}% ({batch_end}/{total_count}) - '
                    f'✅ {processed} | ❌ {errors} | ⏭️ {skipped} | '
                    f'🚀 {rate:.1f}/s | ⏰ ETA: {eta:.0f}s'
                )

                # Cleanup and delay to prevent connection issues
                self._cleanup_connections()

                if delay > 0:
                    time.sleep(delay)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Batch {batch_start}-{batch_end} failed: {e}')
                )
                errors += len(batch_movies) if 'batch_movies' in locals() else batch_size

                # Reset connection after error
                self._reset_connection()
                time.sleep(delay * 2)  # Longer delay after error

        # Final report
        total_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f'🎉 Processing completed in {total_time:.1f}s'))
        self.stdout.write(f'📊 Final Results:')
        self.stdout.write(f'  ✅ Successfully processed: {processed}')
        self.stdout.write(f'  ❌ Errors: {errors}')
        self.stdout.write(f'  ⏭️ Skipped: {skipped}')
        self.stdout.write(f'  🚀 Average rate: {processed/total_time:.1f} movies/second')

        # Show sample results
        if not dry_run and processed > 0:
            self._show_sample_results()

    def _build_queryset(self, start_id, end_id, fix_missing_only, force):
        """Build optimized queryset with connection efficiency"""
        queryset = Movie.objects.select_related('production_metrics').filter(
            poster_url__isnull=False,
            title__isnull=False
        ).exclude(
            poster_url__exact='',
            title__exact=''
        )

        if start_id:
            queryset = queryset.filter(id__gte=start_id)
            self.stdout.write(f'🎯 Starting from movie ID: {start_id}')

        if end_id:
            queryset = queryset.filter(id__lte=end_id)
            self.stdout.write(f'🎯 Ending at movie ID: {end_id}')

        if fix_missing_only:
            queryset = queryset.filter(production_metrics__isnull=True)
            self.stdout.write('🎯 Processing only movies without production metrics')
        elif not force:
            queryset = queryset.filter(
                models.Q(production_metrics__isnull=True) |
                models.Q(production_metrics__last_metrics_update__isnull=True)
            )
            self.stdout.write('🎯 Processing movies without recent metrics')

        return queryset.order_by('id')

    def _process_batch_safe(self, movies, service, dry_run, use_existing_data):
        """Process batch with proper error handling and connection management"""
        processed = 0
        errors = 0
        skipped = 0

        for movie in movies:
            try:
                if dry_run:
                    # Simulate processing
                    self._simulate_calculation(movie, use_existing_data)
                    processed += 1
                else:
                    # Actual processing
                    if use_existing_data:
                        service._calculate_from_existing_data(movie)
                    else:
                        result = service.calculate_production_metrics(movie)
                        if result:
                            processed += 1
                        else:
                            skipped += 1
                            continue

                    processed += 1

            except Exception as e:
                logger.error(f"Error processing movie {movie.id}: {str(e)}")
                errors += 1
                continue

        return {
            'processed': processed,
            'errors': errors,
            'skipped': skipped
        }

    def _simulate_calculation(self, movie, use_existing_data):
        """Simulate calculation for dry run"""
        try:
            # Fix Decimal/float conversion issues
            combined_rating = movie.combined_rating_score
            if combined_rating is None:
                combined_rating = 0.0
            else:
                combined_rating = float(combined_rating)  # Convert Decimal to float

            if use_existing_data:
                # Simulate existing data calculation
                base_score = combined_rating / 10.0
                estimated_performance = min(10.0, base_score * 7.5)
            else:
                # Simulate advanced calculation
                estimated_performance = min(10.0, combined_rating * 0.8)

            self.stdout.write(
                f'🧪 [DRY RUN] Movie {movie.id}: {movie.title[:30]}... '
                f'-> Performance: {estimated_performance:.1f}/10.0'
            )
        except Exception as e:
            logger.error(f"Error in simulation for movie {movie.id}: {str(e)}")
            raise

    def _cleanup_connections(self):
        """Clean up connections and memory to prevent timeout"""
        try:
            # Close database connections
            connection.close()

            # Force garbage collection
            gc.collect()

        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}")

    def _reset_connection(self):
        """Reset database connection after error"""
        try:
            connection.close()
            connection.connect()
        except Exception as e:
            logger.error(f"Error resetting connection: {str(e)}")

    def _show_sample_results(self):
        """Show sample results from processed movies"""
        try:
            self.stdout.write('\n📊 Sample Results:')
            self.stdout.write('-' * 50)

            # Get recent metrics
            recent_metrics = ProductionMetrics.objects.filter(
                last_metrics_update__gte=timezone.now() - timezone.timedelta(minutes=10)
            ).select_related('movie')[:5]

            for metrics in recent_metrics:
                movie = metrics.movie
                self.stdout.write(
                    f'🎬 {movie.title[:40]}... '
                    f'(Performance: {metrics.performance_score:.1f}, '
                    f'Trending: {metrics.trending_category}, '
                    f'Views: {metrics.homepage_views + metrics.detail_page_views})'
                )

            # Overall statistics
            total_metrics = ProductionMetrics.objects.count()
            avg_performance = ProductionMetrics.objects.aggregate(
                avg_score=models.Avg('performance_score')
            )['avg_score']

            self.stdout.write(f'\n📈 Overall Statistics:')
            self.stdout.write(f'  📊 Total movies with metrics: {total_metrics:,}')
            self.stdout.write(f'  🎯 Average performance score: {avg_performance:.1f}' if avg_performance else '  🎯 Average performance score: N/A')

        except Exception as e:
            logger.error(f"Error showing sample results: {str(e)}")

    def _get_connection_status(self):
        """Get current database connection status"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return "Connected"
        except Exception as e:
            return f"Disconnected: {str(e)}"
