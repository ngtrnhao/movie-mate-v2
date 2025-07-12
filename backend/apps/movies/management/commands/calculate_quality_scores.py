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
            default=100,
            help='Number of movies to process per batch (default: 100)'
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

    def handle(self, *args, **options):
        movie_id = options.get('movie_id')
        batch_size = options['batch_size']
        limit = options.get('limit')
        dry_run = options['dry_run']
        force_recalculate = options['force_recalculate']
        show_distribution = options['show_distribution']

        service = QualityCalculationService()

        if dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 DRY RUN MODE - No data will be saved to database')
            )

        # Single movie calculation
        if movie_id:
            self._calculate_single_movie(service, movie_id, dry_run)
            return

        # Bulk calculation
        self._calculate_bulk_movies(service, batch_size, limit, dry_run, force_recalculate)

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
                              limit: int, dry_run: bool, force_recalculate: bool):
        """Calculate quality for multiple movies"""

        # Determine which movies to process
        if force_recalculate:
            queryset = Movie.objects.all()
            description = "all movies (forced recalculation)"
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

        if dry_run:
            # For dry run, just show what would be processed
            sample_movies = list(queryset.select_related().prefetch_related(
                'genres', 'cast', 'trailers', 'reviews'
            )[:min(5, total_count)])

            self.stdout.write('')
            self.stdout.write('📋 SAMPLE CALCULATIONS (DRY RUN):')
            self.stdout.write('=' * 50)

            for movie in sample_movies:
                quality_data = service.calculate_movie_quality(movie, save=False)
                self.stdout.write(
                    f'🎬 {movie.title}: {quality_data["quality_score"]}/10.0 '
                    f'({quality_data["content_completeness"]:.1f}% complete)'
                )

            self.stdout.write('')
            self.stdout.write(f'🧪 Would process {total_count:,} movies total')
            return

        # Real bulk calculation
        movie_ids = list(queryset.values_list('id', flat=True))

        try:
            self.stdout.write('')
            self.stdout.write('🚀 Starting bulk quality calculation...')

            results = service.bulk_calculate_quality(
                movie_ids=movie_ids,
                batch_size=batch_size
            )

            # Display results
            self.stdout.write('')
            self.stdout.write('=' * 60)
            self.stdout.write('📊 BULK CALCULATION RESULTS')
            self.stdout.write('=' * 60)
            self.stdout.write(f'🎯 Total movies processed: {results["total_movies"]:,}')
            self.stdout.write(f'✅ Successful calculations: {results["processed_successfully"]:,}')
            self.stdout.write(f'❌ Errors: {results["errors"]:,}')
            self.stdout.write(f'📊 Success rate: {results["success_rate"]:.2f}%')

            if results["errors"] == 0:
                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS('🎉 All movies processed successfully!')
                )
            else:
                self.stdout.write('')
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ Completed with {results["errors"]} errors. Check logs for details.'
                    )
                )

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
