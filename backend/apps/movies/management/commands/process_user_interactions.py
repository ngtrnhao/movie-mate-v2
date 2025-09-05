"""
Management command để xử lý batch user interactions
Chạy định kỳ để tính toán metrics từ UserInteraction data
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import models
from datetime import timedelta
from apps.movies.services.user_data_collection_service import UserDataCollectionService
from apps.movies.services.production_metrics_service import ProductionMetricsService
from apps.movies.models import UserInteraction, Movie, ProductionMetrics
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process user interactions and calculate production metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Number of hours to look back for processing interactions (default: 24)'
        )

        parser.add_argument(
            '--movie-id',
            type=int,
            help='Process interactions for specific movie ID only'
        )

        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of movies to process in each batch (default: 100)'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes'
        )

        parser.add_argument(
            '--force-recalculate',
            action='store_true',
            help='Force recalculate production metrics for all affected movies'
        )

        parser.add_argument(
            '--stats-only',
            action='store_true',
            help='Only show statistics without processing'
        )

    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write(
            self.style.SUCCESS('User Interaction Processing Command Started')
        )

        # Get options
        hours = options['hours']
        movie_id = options.get('movie_id')
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        force_recalculate = options['force_recalculate']
        stats_only = options['stats_only']

        # Initialize services
        user_data_service = UserDataCollectionService()
        production_service = ProductionMetricsService()

        # Show current statistics
        self._show_interaction_stats(hours, movie_id)

        if stats_only:
            self.stdout.write(self.style.SUCCESS(' Stats-only mode. Exiting.'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        try:
            # Step 1: Process raw interactions into metrics
            self.stdout.write('\nStep 1: Processing user interactions...')
            processing_result = user_data_service.process_batch_interactions_from_database(
                movie_id=movie_id,
                hours=hours
            )

            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Processed {processing_result["processed_interactions"]} interactions '
                        f'for {processing_result["movies_processed"]} movies'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Would process {processing_result["processed_interactions"]} interactions '
                        f'for {processing_result["movies_processed"]} movies'
                    )
                )

            # Step 2: Recalculate production metrics if requested
            if force_recalculate or processing_result["movies_processed"] > 0:
                self.stdout.write('\nStep 2: Recalculating production metrics...')

                if movie_id:
                    movies_to_recalculate = [movie_id]
                else:
                    # Get movies that had interactions processed
                    time_threshold = timezone.now() - timedelta(hours=hours)
                    movies_to_recalculate = UserInteraction.objects.filter(
                        timestamp__gte=time_threshold,
                        processed_at__isnull=False
                    ).values_list('movie_id', flat=True).distinct()

                metrics_result = self._recalculate_production_metrics(
                    production_service,
                    list(movies_to_recalculate),
                    batch_size,
                    dry_run
                )

                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Recalculated metrics for {metrics_result["processed"]} movies '
                            f'({metrics_result["errors"]} errors)'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Would recalculate metrics for {len(movies_to_recalculate)} movies'
                        )
                    )

            # Step 3: Show final statistics
            self.stdout.write('\nFinal Statistics:')
            self._show_interaction_stats(hours, movie_id)

            self.stdout.write(
                self.style.SUCCESS('\nUser interaction processing completed successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing user interactions: {str(e)}')
            )
            logger.error(f"Error in process_user_interactions command: {str(e)}")
            raise CommandError(f'Processing failed: {str(e)}')

    def _show_interaction_stats(self, hours: int, movie_id: int = None):
        """Show interaction statistics"""
        try:
            time_threshold = timezone.now() - timedelta(hours=hours)

            # Get interaction statistics
            if movie_id:
                interactions_qs = UserInteraction.objects.filter(
                    movie_id=movie_id,
                    timestamp__gte=time_threshold
                )
                scope = f"movie {movie_id}"
            else:
                interactions_qs = UserInteraction.objects.filter(
                    timestamp__gte=time_threshold
                )
                scope = "all movies"

            total_interactions = interactions_qs.count()
            processed_interactions = interactions_qs.filter(processed_at__isnull=False).count()
            unprocessed_interactions = interactions_qs.filter(processed_at__isnull=True).count()

            # Unique movies with interactions
            unique_movies = interactions_qs.values('movie').distinct().count()

            # Top actions
            top_actions = interactions_qs.values('action').annotate(
                count=models.Count('id')
            ).order_by('-count')[:5]

            # Device breakdown
            mobile_count = interactions_qs.filter(user_agent__icontains='Mobile').count()
            tablet_count = interactions_qs.filter(user_agent__icontains='Tablet').count()
            desktop_count = total_interactions - mobile_count - tablet_count

            self.stdout.write(f'\nInteraction Statistics (last {hours} hours, {scope}):')
            self.stdout.write(f'   Total interactions: {total_interactions}')
            self.stdout.write(f'   Processed: {processed_interactions}')
            self.stdout.write(f'   Unprocessed: {unprocessed_interactions}')
            self.stdout.write(f'   Unique movies: {unique_movies}')

            if top_actions:
                self.stdout.write(f'   Top actions:')
                for action_data in top_actions:
                    self.stdout.write(f'      • {action_data["action"]}: {action_data["count"]}')

            self.stdout.write(f'   Device breakdown:')
            self.stdout.write(f'      • Mobile: {mobile_count}')
            self.stdout.write(f'      • Desktop: {desktop_count}')
            self.stdout.write(f'      • Tablet: {tablet_count}')

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not generate statistics: {str(e)}')
            )

    def _recalculate_production_metrics(self, production_service, movie_ids, batch_size, dry_run):
        """Recalculate production metrics for given movies"""
        processed_count = 0
        error_count = 0

        # Process in batches
        for i in range(0, len(movie_ids), batch_size):
            batch_ids = movie_ids[i:i + batch_size]
            batch_movies = Movie.objects.filter(id__in=batch_ids)

            for movie in batch_movies:
                try:
                    if not dry_run:
                        production_service.calculate_production_metrics(movie, save=True)
                    processed_count += 1

                    if processed_count % 50 == 0:
                        self.stdout.write(f'   Processed {processed_count} movies...')

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error recalculating metrics for movie {movie.id}: {str(e)}")

        return {
            'processed': processed_count,
            'errors': error_count
        }
