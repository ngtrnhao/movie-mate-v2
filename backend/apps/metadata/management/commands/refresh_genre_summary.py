from django.core.management.base import BaseCommand
from django.core.cache import cache
from apps.metadata.models import GenreSummary
import logging
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Refresh genre summary table for optimal performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh even if not needed',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear cache after refresh',
        )

    def handle(self, *args, **options):
        start_time = time.time()

        try:
            self.stdout.write(
                self.style.SUCCESS('Starting genre summary refresh...')
            )

            # Refresh all summaries
            GenreSummary.refresh_all_summaries()

            # Clear cache if requested
            if options['clear_cache']:
                cache.delete_pattern('movie_categories_summary_*')
                self.stdout.write(
                    self.style.SUCCESS('Cache cleared')
                )

            total_time = time.time() - start_time

            # Get summary stats
            total_summaries = GenreSummary.objects.count()
            summaries_with_movies = GenreSummary.objects.filter(movie_count__gt=0).count()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Genre summary refresh completed in {total_time:.3f}s'
                )
            )
            self.stdout.write(
                f'Total summaries: {total_summaries}'
            )
            self.stdout.write(
                f'Summaries with movies: {summaries_with_movies}'
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error refreshing genre summary: {str(e)}')
            )
            logger.error(f"Error in refresh_genre_summary command: {str(e)}", exc_info=True)
