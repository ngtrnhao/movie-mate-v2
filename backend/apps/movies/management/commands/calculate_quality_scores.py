from django.core.management.base import BaseCommand
from django.db import transaction
from apps.movies.models import Movie, MovieQualityMetrics
from apps.movies.services.quality_calculation_service import QualityCalculationService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate quality scores for movies using QualityCalculationService'

    def add_arguments(self, parser):
        parser.add_argument(
            '--movie-id',
            type=int,
            help='Calculate quality for specific movie ID'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of movies to process per batch (default: 50)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of movies to process (for testing)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform calculation without saving to database'
        )
        parser.add_argument(
            '--force-recalculate',
            action='store_true',
            help='Recalculate quality for movies that already have quality metrics'
        )
        parser.add_argument(
            '--show-distribution',
            action='store_true',
            help='Show quality score distribution after calculation'
        )
        parser.add_argument(
            '--null-quality-only',
            action='store_true',
            help='Only process movies with null quality_score (default behavior)'
        )
        parser.add_argument(
            '--progress-interval',
            type=int,
            default=10,
            help='Show progress every N movies (default: 10)'
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='Continue processing even if some movies fail'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current quality score status without processing'
        )

    def handle(self, *args, **options):
        movie_id = options.get('movie_id')
        batch_size = options['batch_size']
        limit = options.get('limit')
        dry_run = options['dry_run']
        force_recalculate = options['force_recalculate']
        show_distribution = options['show_distribution']
        null_quality_only = options['null_quality_only']
        progress_interval = options['progress_interval']
        skip_errors = options['skip_errors']
        status = options['status']

        service = QualityCalculationService()

        if dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 DRY RUN MODE - No data will be saved to database')
            )

        # Show status if requested
        if status:
            self._show_quality_status()
            return

        # Single movie calculation
        if movie_id:
            self._calculate_single_movie(service, movie_id, dry_run)
            return

        # Bulk calculation
        self._calculate_bulk_movies(
            service, batch_size, limit, dry_run, force_recalculate,
            null_quality_only, progress_interval, skip_errors
        )

        # Show distribution if requested
        if show_distribution and not dry_run:
            self._show_quality_distribution(service)

    def _calculate_single_movie(self, service: QualityCalculationService, movie_id: int, dry_run: bool):
        """Calculate quality for single movie"""
        try:
            movie = Movie.objects.select_related().prefetch_related(
                'genres', 'cast', 'trailers', 'reviews'
            ).get(id=movie_id)

            self.stdout.write(f'🎬 Calculating quality for: {movie.title} (ID: {movie_id})')

            quality_data = service.calculate_movie_quality(movie, save=not dry_run)

            # Display results
            self.stdout.write('')
            self.stdout.write('📊 QUALITY CALCULATION RESULTS')
            self.stdout.write('=' * 50)
            self.stdout.write(f'🏆 Overall Quality Score: {quality_data["quality_score"]}/10.0')
            self.stdout.write(f'📈 Content Completeness: {quality_data["content_completeness"]:.2f}%')
            self.stdout.write(f'✅ Meets Minimum Quality: {quality_data["minimum_quality_met"]}')

            self.stdout.write('')
            self.stdout.write('📋 BREAKDOWN SCORES:')
            self.stdout.write(f'  • Basic Info: {quality_data["basic_info_score"]}/10.0')
            self.stdout.write(f'  • Visual Assets: {quality_data["visual_assets_score"]}/10.0')
            self.stdout.write(f'  • Metadata Richness: {quality_data["metadata_richness_score"]}/10.0')
            self.stdout.write(f'  • Rating Validity: {quality_data["rating_validity_score"]}/10.0')

            if quality_data["quality_issues"]:
                self.stdout.write('')
                self.stdout.write('⚠️ QUALITY ISSUES:')
                for issue in quality_data["quality_issues"]:
                    self.stdout.write(f'  • {issue}')

            if quality_data["quality_suggestions"]:
                self.stdout.write('')
                self.stdout.write('💡 SUGGESTIONS:')
                for suggestion in quality_data["quality_suggestions"]:
                    self.stdout.write(f'  • {suggestion}')

            if not dry_run:
                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS('✅ Quality metrics saved to database')
                )

        except Movie.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Movie with ID {movie_id} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error calculating quality: {str(e)}')
            )

    def _calculate_bulk_movies(self, service: QualityCalculationService, batch_size: int,
                              limit: int, dry_run: bool, force_recalculate: bool,
                              null_quality_only: bool, progress_interval: int, skip_errors: bool):
        """Calculate quality for multiple movies"""

        # Determine which movies to process
        if force_recalculate:
            queryset = Movie.objects.all()
            description = "all movies (forced recalculation)"
        elif null_quality_only:
            # Only movies with null quality_score in quality_metrics
            queryset = Movie.objects.filter(quality_metrics__quality_score__isnull=True)
            description = "movies with null quality_score"
        else:
            # Only movies without quality metrics
            queryset = Movie.objects.filter(quality_metrics__isnull=True)
            description = "movies without quality metrics"

        if limit:
            queryset = queryset[:limit]
            description += f" (limited to {limit})"

        total_count = queryset.count()

        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ All movies already have quality metrics calculated')
            )
            return

        self.stdout.write(f'🎯 Processing {total_count:,} {description}')
        self.stdout.write(f'🔧 Batch size: {batch_size:,}')
        self.stdout.write(f'📊 Progress interval: {progress_interval:,} movies')
        if skip_errors:
            self.stdout.write('⚠️ Skip errors mode: Will continue on failures')

        if dry_run:
            # For dry run, just show what would be processed
            sample_movies = list(queryset.select_related().prefetch_related(
                'genres', 'cast', 'trailers', 'reviews'
            )[:min(5, total_count)])

            self.stdout.write('')
            self.stdout.write('📋 SAMPLE CALCULATIONS (DRY RUN):')
            self.stdout.write('=' * 50)

            for movie in sample_movies:
                try:
                    quality_data = service.calculate_movie_quality(movie, save=False)
                    self.stdout.write(
                        f'🎬 {movie.title}: {quality_data["quality_score"]}/10.0 '
                        f'({quality_data["content_completeness"]:.1f}% complete)'
                    )
                except Exception as e:
                    self.stdout.write(
                        f'❌ {movie.title}: Error - {str(e)}'
                    )

            self.stdout.write('')
            self.stdout.write(f'🧪 Would process {total_count:,} movies total')
            return

        # Real bulk calculation with progress tracking
        movie_ids = list(queryset.values_list('id', flat=True))

        try:
            self.stdout.write('')
            self.stdout.write('🚀 Starting bulk quality calculation...')

            processed = 0
            successful = 0
            errors = 0
            error_details = []

            for i in range(0, len(movie_ids), batch_size):
                batch_ids = movie_ids[i:i + batch_size]

                self.stdout.write(f'📦 Processing batch {i//batch_size + 1}/{(len(movie_ids) + batch_size - 1)//batch_size}')

                for movie_id in batch_ids:
                    try:
                        movie = Movie.objects.select_related().prefetch_related(
                            'genres', 'cast', 'trailers', 'reviews'
                        ).get(id=movie_id)

                        quality_data = service.calculate_movie_quality(movie, save=True)
                        successful += 1

                        processed += 1
                        if processed % progress_interval == 0:
                            self.stdout.write(
                                f'✅ Progress: {processed:,}/{total_count:,} ({processed/total_count*100:.1f}%) - '
                                f'Success: {successful:,}, Errors: {errors:,}'
                            )

                    except Exception as e:
                        errors += 1
                        error_msg = f"Movie ID {movie_id}: {str(e)}"
                        error_details.append(error_msg)
                        logger.error(error_msg)

                        if not skip_errors:
                            self.stdout.write(
                                self.style.ERROR(f'❌ Failed to process movie {movie_id}: {str(e)}')
                            )
                            raise e
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'⚠️ Skipped movie {movie_id}: {str(e)}')
                            )

            # Display final results
            self.stdout.write('')
            self.stdout.write('=' * 60)
            self.stdout.write('📊 BULK CALCULATION RESULTS')
            self.stdout.write('=' * 60)
            self.stdout.write(f'🎯 Total movies processed: {processed:,}')
            self.stdout.write(f'✅ Successful calculations: {successful:,}')
            self.stdout.write(f'❌ Errors: {errors:,}')
            self.stdout.write(f'📊 Success rate: {successful/processed*100:.2f}%' if processed > 0 else '📊 Success rate: 0%')

            if errors == 0:
                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS('🎉 All movies processed successfully!')
                )
            else:
                self.stdout.write('')
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ Completed with {errors} errors. Check logs for details.'
                    )
                )

                if len(error_details) <= 10:
                    self.stdout.write('')
                    self.stdout.write('❌ ERROR DETAILS:')
                    for error in error_details:
                        self.stdout.write(f'  • {error}')
                else:
                    self.stdout.write('')
                    self.stdout.write(f'❌ First 10 errors (total {len(error_details)}):')
                    for error in error_details[:10]:
                        self.stdout.write(f'  • {error}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Bulk calculation failed: {str(e)}')
            )

    def _show_quality_distribution(self, service: QualityCalculationService):
        """Show quality score distribution"""
        try:
            distribution = service.get_quality_distribution()

            self.stdout.write('')
            self.stdout.write('=' * 60)
            self.stdout.write('📈 QUALITY SCORE DISTRIBUTION')
            self.stdout.write('=' * 60)

            quality_labels = {
                'excellent': '🏆 Excellent (8.0-10.0)',
                'good': '👍 Good (6.0-7.9)',
                'fair': '⚠️ Fair (4.0-5.9)',
                'poor': '❌ Poor (0.0-3.9)',
                'not_assessed': '❓ Not Assessed'
            }

            for category, label in quality_labels.items():
                if category in distribution:
                    count = distribution[category]['count']
                    percentage = distribution[category]['percentage']
                    self.stdout.write(f'{label}: {count:,} ({percentage:.1f}%)')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error getting distribution: {str(e)}')
            )

    def _show_quality_status(self):
        """Show current quality score status"""
        try:
            from django.db.models import Count, Q

            total_movies = Movie.objects.count()
            movies_with_quality = Movie.objects.filter(quality_metrics__quality_score__isnull=False).count()
            movies_without_quality = Movie.objects.filter(quality_metrics__quality_score__isnull=True).count()
            movies_with_metrics = Movie.objects.filter(quality_metrics__isnull=False).count()
            movies_without_metrics = Movie.objects.filter(quality_metrics__isnull=True).count()

            # Quality score distribution
            excellent = Movie.objects.filter(quality_metrics__quality_score__gte=8.0).count()
            good = Movie.objects.filter(quality_metrics__quality_score__gte=6.0, quality_metrics__quality_score__lt=8.0).count()
            fair = Movie.objects.filter(quality_metrics__quality_score__gte=4.0, quality_metrics__quality_score__lt=6.0).count()
            poor = Movie.objects.filter(quality_metrics__quality_score__lt=4.0).count()

            self.stdout.write('')
            self.stdout.write('=' * 60)
            self.stdout.write('📊 QUALITY SCORE STATUS')
            self.stdout.write('=' * 60)
            self.stdout.write(f'🎬 Total movies: {total_movies:,}')
            self.stdout.write(f'✅ Movies with quality_score: {movies_with_quality:,} ({movies_with_quality/total_movies*100:.1f}%)')
            self.stdout.write(f'❌ Movies without quality_score: {movies_without_quality:,} ({movies_without_quality/total_movies*100:.1f}%)')
            self.stdout.write('')
            self.stdout.write(f'📋 Movies with quality_metrics: {movies_with_metrics:,} ({movies_with_metrics/total_movies*100:.1f}%)')
            self.stdout.write(f'📋 Movies without quality_metrics: {movies_without_metrics:,} ({movies_without_metrics/total_movies*100:.1f}%)')

            if movies_with_quality > 0:
                self.stdout.write('')
                self.stdout.write('📈 QUALITY SCORE DISTRIBUTION:')
                self.stdout.write(f'🏆 Excellent (8.0+): {excellent:,} ({excellent/movies_with_quality*100:.1f}%)')
                self.stdout.write(f'👍 Good (6.0-7.9): {good:,} ({good/movies_with_quality*100:.1f}%)')
                self.stdout.write(f'⚠️ Fair (4.0-5.9): {fair:,} ({fair/movies_with_quality*100:.1f}%)')
                self.stdout.write(f'❌ Poor (<4.0): {poor:,} ({poor/movies_with_quality*100:.1f}%)')

            # Sample movies without quality score
            if movies_without_quality > 0:
                sample_movies = Movie.objects.filter(quality_metrics__quality_score__isnull=True)[:5]
                self.stdout.write('')
                self.stdout.write('🎬 SAMPLE MOVIES WITHOUT QUALITY SCORE:')
                for movie in sample_movies:
                    self.stdout.write(f'  • {movie.title} (ID: {movie.id})')
                if movies_without_quality > 5:
                    self.stdout.write(f'  ... and {movies_without_quality - 5:,} more')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error getting status: {str(e)}')
            )
