from django.core.management.base import BaseCommand
from apps.movies.models import Movie
from apps.movies.services.unified_movie_enrichment_service import UnifiedMovieEnrichmentService

class Command(BaseCommand):
    help = 'Enrich all movies in the database using UnifiedMovieEnrichmentService'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=50, help='Batch size for enrichment')
        parser.add_argument('--focus', nargs='*', default=None, help='Focus areas: basic, visual, metadata, ratings')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        focus_areas = options['focus']
        service = UnifiedMovieEnrichmentService()

        all_ids = list(Movie.objects.values_list('id', flat=True))
        total = len(all_ids)
        self.stdout.write(f"Found {total} movies to enrich.")

        for i in range(0, total, batch_size):
            batch_ids = all_ids[i:i+batch_size]
            self.stdout.write(f"Enriching movies {i+1} to {i+len(batch_ids)}...")
            result = service.batch_enrich_movies(batch_ids, focus_areas=focus_areas)
            self.stdout.write(f"Batch result: {result['processed_successfully']}/{len(batch_ids)} success, {result['errors']} errors.")

        self.stdout.write("✅ All movies enrichment completed.")
