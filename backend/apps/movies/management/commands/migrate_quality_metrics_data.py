from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.movies.models import Movie, MovieQualityMetrics
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrate quality metrics data from Movie table to MovieQualityMetrics table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of movies to process per batch (default: 1000)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without making actual changes'
        )
        parser.add_argument(
            '--start-id',
            type=int,
            default=0,
            help='Start from movie ID (for resuming interrupted migration)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        start_id = options['start_id']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 DRY RUN MODE - No actual changes will be made')
            )

        # Get total count of movies that need migration
        total_movies = Movie.objects.filter(
            id__gte=start_id,
            quality_metrics__isnull=True  # Only migrate movies without quality metrics
        ).count()

        if total_movies == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ All movies already have quality metrics data')
            )
            return

        self.stdout.write(
            f'📊 Found {total_movies:,} movies needing quality metrics migration'
        )
        self.stdout.write(f'🔧 Batch size: {batch_size:,}')
        self.stdout.write(f'🚀 Starting from ID: {start_id:,}')

        migrated_count = 0
        error_count = 0
        current_id = start_id

        while current_id < float('inf'):
            # Get batch of movies
            movies_batch = list(
                Movie.objects.filter(
                    id__gte=current_id,
                    quality_metrics__isnull=True
                ).order_by('id')[:batch_size]
            )

            if not movies_batch:
                break

            batch_start_id = movies_batch[0].id
            batch_end_id = movies_batch[-1].id

            self.stdout.write(
                f'🔄 Processing batch: IDs {batch_start_id:,} - {batch_end_id:,} '
                f'({len(movies_batch)} movies)'
            )

            if not dry_run:
                with transaction.atomic():
                    try:
                        quality_metrics_to_create = []

                        for movie in movies_batch:
                            # Create MovieQualityMetrics object
                            quality_metrics = MovieQualityMetrics(
                                movie=movie,
                                quality_score=movie.quality_score,
                                content_completeness=movie.content_completeness or 0,
                                minimum_quality_met=movie.minimum_quality_met,

                                # Initialize breakdown scores to 0 (will be calculated later)
                                basic_info_score=0,
                                visual_assets_score=0,
                                metadata_richness_score=0,
                                rating_validity_score=0,

                                # Initialize empty lists for quality details
                                quality_issues=[],
                                quality_suggestions=[],
                                last_quality_check=None,

                                # Set automation flags
                                auto_calculated=False,  # Set to False since these are migrated data
                                calculation_version='1.0',

                                # Set timestamps
                                created_at=timezone.now(),
                                updated_at=timezone.now()
                            )
                            quality_metrics_to_create.append(quality_metrics)

                        # Bulk create all quality metrics for this batch
                        MovieQualityMetrics.objects.bulk_create(
                            quality_metrics_to_create,
                            batch_size=batch_size
                        )

                        migrated_count += len(movies_batch)

                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Successfully migrated batch of {len(movies_batch)} movies. '
                                f'Total: {migrated_count:,}/{total_movies:,}'
                            )
                        )

                    except Exception as e:
                        error_count += len(movies_batch)
                        self.stdout.write(
                            self.style.ERROR(
                                f'❌ Error processing batch {batch_start_id}-{batch_end_id}: {str(e)}'
                            )
                        )
                        logger.error(f'Quality metrics migration error: {str(e)}', exc_info=True)

                        # Continue with next batch instead of stopping
                        pass
            else:
                # Dry run - just count
                migrated_count += len(movies_batch)
                self.stdout.write(
                    f'🧪 Would migrate batch of {len(movies_batch)} movies. '
                    f'Total: {migrated_count:,}/{total_movies:,}'
                )

            # Move to next batch
            current_id = batch_end_id + 1

            # Progress report every 10 batches
            if migrated_count % (batch_size * 10) == 0:
                progress = (migrated_count / total_movies) * 100
                self.stdout.write(
                    self.style.HTTP_INFO(
                        f'📈 Progress: {progress:.1f}% ({migrated_count:,}/{total_movies:,})'
                    )
                )

        # Final summary
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('📋 QUALITY METRICS MIGRATION SUMMARY')
        self.stdout.write('=' * 60)
        self.stdout.write(f'🎯 Total movies to migrate: {total_movies:,}')
        self.stdout.write(f'✅ Successfully migrated: {migrated_count:,}')
        if error_count > 0:
            self.stdout.write(f'❌ Errors: {error_count:,}')

        success_rate = (migrated_count / total_movies) * 100 if total_movies > 0 else 100
        self.stdout.write(f'📊 Success rate: {success_rate:.2f}%')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 This was a DRY RUN - no actual changes were made')
            )
        else:
            self.stdout.write('')
            # Verification
            verification_count = MovieQualityMetrics.objects.count()
            self.stdout.write(f'🔍 Verification: {verification_count:,} quality metrics records in database')

            if error_count == 0:
                self.stdout.write(
                    self.style.SUCCESS('🎉 Quality metrics migration completed successfully!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ Migration completed with {error_count:,} errors. Check logs for details.'
                    )
                )
