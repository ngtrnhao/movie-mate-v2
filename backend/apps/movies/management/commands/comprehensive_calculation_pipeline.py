from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.utils import timezone
from apps.movies.models import Movie, MovieQualityMetrics, ProductionMetrics, MovieScheduling
from apps.movies.services.quality_calculation_service import QualityCalculationService
from apps.movies.services.user_data_collection_service import UserDataCollectionService
from apps.movies.services.production_metrics_service import ProductionMetricsService
import logging
import time
import gc
from django.db import models
from typing import Dict, List
import sys

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '🚀 Comprehensive calculation pipeline: Quality → User Data → Production Metrics with connection stability'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=25,
            help='Batch size for processing (smaller for stability)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.8,
            help='Delay between batches (seconds)'
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
            '--phase',
            type=str,
            choices=['quality', 'user-data', 'production', 'all'],
            default='all',
            help='Which phase to run'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Test without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recalculate existing metrics'
        )
        parser.add_argument(
            '--connection-check',
            action='store_true',
            help='Enable connection health monitoring'
        )
        parser.add_argument(
            '--progress-interval',
            type=int,
            default=10,
            help='Progress report interval'
        )

    def handle(self, *args, **options):
        # Initialize parameters
        batch_size = options['batch_size']
        delay = options['delay']
        start_id = options.get('start_id')
        end_id = options.get('end_id')
        phase = options['phase']
        dry_run = options['dry_run']
        force = options['force']
        connection_check = options['connection_check']
        progress_interval = options['progress_interval']

        self.stdout.write(self.style.SUCCESS('🚀 Starting Comprehensive Calculation Pipeline'))
        self.stdout.write(f'📊 Phase: {phase}')
        self.stdout.write(f'📈 Batch size: {batch_size}')
        self.stdout.write(f'⏱️ Delay: {delay}s')
        self.stdout.write(f'🔄 Connection monitoring: {connection_check}')

        if dry_run:
            self.stdout.write(self.style.WARNING('🧪 DRY RUN MODE'))

        # Build queryset
        queryset = self._build_queryset(start_id, end_id, force)
        total_count = queryset.count()

        if total_count == 0:
            self.stdout.write(self.style.WARNING('⚠️ No movies found'))
            return

        self.stdout.write(f'🎬 Found {total_count} movies to process')

        # Initialize services
        quality_service = QualityCalculationService()
        user_data_service = UserDataCollectionService()
        production_service = ProductionMetricsService()

        # Start pipeline
        start_time = time.time()
        results = {
            'quality': {'processed': 0, 'errors': 0, 'skipped': 0},
            'user_data': {'processed': 0, 'errors': 0, 'skipped': 0},
            'production': {'processed': 0, 'errors': 0, 'skipped': 0}
        }

        # Process based on phase
        if phase in ['quality', 'all']:
            self.stdout.write(self.style.SUCCESS('🎯 Phase 1: Quality Calculation'))
            results['quality'] = self._process_quality_metrics(
                queryset, quality_service, batch_size, delay, dry_run,
                connection_check, progress_interval
            )

        if phase in ['user-data', 'all']:
            self.stdout.write(self.style.SUCCESS('👥 Phase 2: User Data Collection'))
            results['user_data'] = self._process_user_data_collection(
                queryset, user_data_service, batch_size, delay, dry_run,
                connection_check, progress_interval
            )

        if phase in ['production', 'all']:
            self.stdout.write(self.style.SUCCESS('📈 Phase 3: Production Metrics'))
            results['production'] = self._process_production_metrics(
                queryset, production_service, batch_size, delay, dry_run,
                connection_check, progress_interval
            )

        # Final report
        total_time = time.time() - start_time
        self._generate_final_report(results, total_time, total_count)

    def _build_queryset(self, start_id, end_id, force):
        """Build optimized queryset"""
        queryset = Movie.objects.select_related(
            'quality_metrics', 'production_metrics', 'scheduling'
        ).prefetch_related(
            'genres', 'cast', 'trailers', 'reviews'
        ).filter(
            title__isnull=False,
            poster_url__isnull=False
        ).exclude(
            title__exact='',
            poster_url__exact=''
        )

        if start_id:
            queryset = queryset.filter(id__gte=start_id)
        if end_id:
            queryset = queryset.filter(id__lte=end_id)

        if not force:
            # Only process movies that need updates
            queryset = queryset.filter(
                models.Q(quality_metrics__isnull=True) |
                models.Q(production_metrics__isnull=True) |
                models.Q(quality_metrics__last_quality_check__isnull=True) |
                models.Q(production_metrics__last_metrics_update__isnull=True)
            )

        return queryset.order_by('id')

    def _process_quality_metrics(self, queryset, service, batch_size, delay, dry_run, connection_check, progress_interval):
        """Process quality metrics with connection stability"""
        processed = 0
        errors = 0
        skipped = 0
        total_count = queryset.count()

        for batch_start in range(0, total_count, batch_size):
            batch_end = min(batch_start + batch_size, total_count)

            try:
                # Connection health check
                if connection_check:
                    self._check_connection_health()

                # Get batch with optimized query
                batch_movies = list(queryset[batch_start:batch_end])

                # Process each movie in batch
                for movie in batch_movies:
                    try:
                        if dry_run:
                            self.stdout.write(
                                f'🧪 [DRY RUN] Quality calculation for movie {movie.id}: {movie.title[:30]}...'
                            )
                            processed += 1
                        else:
                            # Check if already has recent quality metrics
                            has_recent_quality = hasattr(movie, 'quality_metrics') and \
                                movie.quality_metrics and \
                                movie.quality_metrics.last_quality_check and \
                                (timezone.now() - movie.quality_metrics.last_quality_check).days < 7

                            if has_recent_quality:
                                skipped += 1
                                continue

                            # Calculate quality metrics
                            result = service.calculate_movie_quality(movie, save=True)
                            if result:
                                processed += 1
                                logger.info(f"Quality calculated for movie {movie.id}: {result['quality_score']}")

                    except Exception as e:
                        errors += 1
                        logger.error(f"Error processing quality for movie {movie.id}: {str(e)}")
                        continue

                # Progress report
                if (batch_end // batch_size) % progress_interval == 0:
                    progress = (batch_end / total_count) * 100
                    self.stdout.write(
                        f'📊 Quality Progress: {progress:.1f}% - '
                        f'✅ {processed} | ❌ {errors} | ⏭️ {skipped}'
                    )

                # Cleanup and delay
                self._cleanup_batch(delay)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Quality batch {batch_start}-{batch_end} failed: {e}')
                )
                errors += len(batch_movies) if 'batch_movies' in locals() else batch_size
                self._reset_connection()
                time.sleep(delay * 2)

        return {'processed': processed, 'errors': errors, 'skipped': skipped}

    def _process_user_data_collection(self, queryset, service, batch_size, delay, dry_run, connection_check, progress_interval):
        """Process user data collection with existing data fallback"""
        processed = 0
        errors = 0
        skipped = 0
        total_count = queryset.count()

        for batch_start in range(0, total_count, batch_size):
            batch_end = min(batch_start + batch_size, total_count)

            try:
                if connection_check:
                    self._check_connection_health()

                batch_movies = list(queryset[batch_start:batch_end])

                for movie in batch_movies:
                    try:
                        if dry_run:
                            self.stdout.write(
                                f'🧪 [DRY RUN] User data collection for movie {movie.id}: {movie.title[:30]}...'
                            )
                            processed += 1
                        else:
                            # Check if already has production metrics
                            has_production_metrics = hasattr(movie, 'production_metrics') and \
                                movie.production_metrics and \
                                movie.production_metrics.last_metrics_update

                            if has_production_metrics:
                                skipped += 1
                                continue

                            # Calculate from existing data (fallback approach)
                            service._calculate_from_existing_data(movie)
                            processed += 1
                            logger.info(f"User data processed for movie {movie.id}")

                    except Exception as e:
                        errors += 1
                        logger.error(f"Error processing user data for movie {movie.id}: {str(e)}")
                        continue

                # Progress report
                if (batch_end // batch_size) % progress_interval == 0:
                    progress = (batch_end / total_count) * 100
                    self.stdout.write(
                        f'👥 User Data Progress: {progress:.1f}% - '
                        f'✅ {processed} | ❌ {errors} | ⏭️ {skipped}'
                    )

                self._cleanup_batch(delay)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ User data batch {batch_start}-{batch_end} failed: {e}')
                )
                errors += len(batch_movies) if 'batch_movies' in locals() else batch_size
                self._reset_connection()
                time.sleep(delay * 2)

        return {'processed': processed, 'errors': errors, 'skipped': skipped}

    def _process_production_metrics(self, queryset, service, batch_size, delay, dry_run, connection_check, progress_interval):
        """Process production metrics with quality metrics dependency"""
        processed = 0
        errors = 0
        skipped = 0
        total_count = queryset.count()

        for batch_start in range(0, total_count, batch_size):
            batch_end = min(batch_start + batch_size, total_count)

            try:
                if connection_check:
                    self._check_connection_health()

                batch_movies = list(queryset[batch_start:batch_end])

                for movie in batch_movies:
                    try:
                        if dry_run:
                            self.stdout.write(
                                f'🧪 [DRY RUN] Production metrics for movie {movie.id}: {movie.title[:30]}...'
                            )
                            processed += 1
                        else:
                            # Check if has quality metrics (dependency)
                            has_quality_metrics = hasattr(movie, 'quality_metrics') and movie.quality_metrics

                            if not has_quality_metrics:
                                skipped += 1
                                logger.warning(f"Movie {movie.id} skipped - no quality metrics")
                                continue

                            # Calculate production metrics
                            result = service.calculate_production_metrics(movie, save=True)
                            if result:
                                processed += 1
                                logger.info(f"Production metrics calculated for movie {movie.id}")

                    except Exception as e:
                        errors += 1
                        logger.error(f"Error processing production metrics for movie {movie.id}: {str(e)}")
                        continue

                # Progress report
                if (batch_end // batch_size) % progress_interval == 0:
                    progress = (batch_end / total_count) * 100
                    self.stdout.write(
                        f'📈 Production Progress: {progress:.1f}% - '
                        f'✅ {processed} | ❌ {errors} | ⏭️ {skipped}'
                    )

                self._cleanup_batch(delay)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Production batch {batch_start}-{batch_end} failed: {e}')
                )
                errors += len(batch_movies) if 'batch_movies' in locals() else batch_size
                self._reset_connection()
                time.sleep(delay * 2)

        return {'processed': processed, 'errors': errors, 'skipped': skipped}

    def _check_connection_health(self):
        """Check database connection health"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.warning(f"Connection health check failed: {e}")
            self._reset_connection()
            return False

    def _cleanup_batch(self, delay):
        """Cleanup after batch processing"""
        try:
            # Close old connections
            connection.close()

            # Force garbage collection
            gc.collect()

            # Wait before next batch
            if delay > 0:
                time.sleep(delay)

        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

    def _reset_connection(self):
        """Reset database connection"""
        try:
            connection.close()
            connection.connect()
        except Exception as e:
            logger.error(f"Connection reset failed: {e}")

    def _generate_final_report(self, results, total_time, total_count):
        """Generate comprehensive final report"""
        self.stdout.write(self.style.SUCCESS('\n🎉 Comprehensive Pipeline Completed'))
        self.stdout.write(f'⏱️ Total time: {total_time:.1f}s')
        self.stdout.write(f'🎬 Total movies: {total_count:,}')
        self.stdout.write(f'🚀 Average rate: {total_count/total_time:.1f} movies/second')

        self.stdout.write('\n📊 Phase Results:')
        self.stdout.write('-' * 60)

        for phase, data in results.items():
            if data['processed'] > 0 or data['errors'] > 0:
                success_rate = (data['processed'] / (data['processed'] + data['errors'])) * 100 if (data['processed'] + data['errors']) > 0 else 0
                self.stdout.write(
                    f'{phase.upper():15} | '
                    f'✅ {data["processed"]:6,} | '
                    f'❌ {data["errors"]:6,} | '
                    f'⏭️ {data["skipped"]:6,} | '
                    f'📈 {success_rate:5.1f}%'
                )

        # Database statistics
        self.stdout.write('\n📈 Database Statistics:')
        self.stdout.write('-' * 60)

        try:
            quality_count = MovieQualityMetrics.objects.count()
            production_count = ProductionMetrics.objects.count()

            self.stdout.write(f'📊 Movies with quality metrics: {quality_count:,}')
            self.stdout.write(f'📈 Movies with production metrics: {production_count:,}')

            # Sample recent results
            self._show_sample_results()

        except Exception as e:
            logger.error(f"Error generating database statistics: {e}")

    def _show_sample_results(self):
        """Show sample results from recent processing"""
        try:
            self.stdout.write('\n🔍 Sample Recent Results:')
            self.stdout.write('-' * 60)

            # Recent quality metrics
            recent_quality = MovieQualityMetrics.objects.filter(
                last_quality_check__gte=timezone.now() - timezone.timedelta(minutes=30)
            ).select_related('movie')[:5]

            for qm in recent_quality:
                self.stdout.write(
                    f'🎬 {qm.movie.title[:35]:35} | '
                    f'Quality: {qm.quality_score:4.1f} | '
                    f'Complete: {qm.content_completeness:5.1f}% | '
                    f'Min Quality: {"✅" if qm.minimum_quality_met else "❌"}'
                )

            # Recent production metrics
            recent_production = ProductionMetrics.objects.filter(
                last_metrics_update__gte=timezone.now() - timezone.timedelta(minutes=30)
            ).select_related('movie')[:5]

            if recent_production:
                self.stdout.write('\n📈 Recent Production Metrics:')
                for pm in recent_production:
                    self.stdout.write(
                        f'🎬 {pm.movie.title[:35]:35} | '
                        f'Performance: {pm.performance_score:4.1f} | '
                        f'Trending: {pm.trending_category:10} | '
                        f'Views: {pm.homepage_views + pm.detail_page_views:,}'
                    )

        except Exception as e:
            logger.error(f"Error showing sample results: {e}")
