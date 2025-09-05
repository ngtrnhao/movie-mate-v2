from django.core.management.base import BaseCommand
from apps.movies.services.cast_profile_enrichment_service import CastProfileEnrichmentService
from apps.movies.models import MovieCast, Movie
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Enrich MovieCast records with profile images from TMDB by matching names'

    def add_arguments(self, parser):
        parser.add_argument(
            '--movie-id',
            type=int,
            help='Enrich cast for specific movie ID'
        )
        parser.add_argument(
            '--popular',
            type=int,
            default=50,
            help='Number of popular movies to process (default: 50)'
        )
        parser.add_argument(
            '--batch',
            type=int,
            default=10,
            help='Number of movies to process in batch mode (default: 10)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        service = CastProfileEnrichmentService()

        # Chỉ hiển thị stats khi không phải single movie mode
        if not options['movie_id']:
            # Show current stats
            total_cast = MovieCast.objects.count()
            cast_with_profiles = MovieCast.objects.filter(profile_path__isnull=False).count()
            movies_with_tmdb = Movie.objects.filter(tmdb_id__isnull=False).count()

            self.stdout.write(f"📊 Current Status:")
            self.stdout.write(f"   Total cast members: {total_cast:,}")
            self.stdout.write(f"   With profiles: {cast_with_profiles:,}")
            self.stdout.write(f"   Missing profiles: {total_cast - cast_with_profiles:,}")
            self.stdout.write(f"   Movies with TMDB ID: {movies_with_tmdb:,}")
            self.stdout.write("")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be made"))
            return

        if options['movie_id']:
            # Process specific movie - không cần stats
            movie_id = options['movie_id']
            self.stdout.write(f"🎬 Enriching cast for movie ID: {movie_id}")

            result = service.enrich_movie_cast_profiles(movie_id)
            if result["success"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Successfully enriched movie '{result['movie_title']}' - "
                        f"{result['updated_count']} profiles updated"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Failed: {result['error']}")
                )
            return  # Thoát sớm, không cần final stats

        elif options.get('popular'):
            # Process popular movies
            limit = options['popular']
            self.stdout.write(f"🌟 Enriching cast for {limit} popular movies")
            self.stdout.write("🔍 Strategy: Match IMDB cast names with TMDB movie credits")
            self.stdout.write("")

            result = service.enrich_popular_movies(limit)
            if result["success"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Processed {result['movies_processed']}/{result['total_movies']} movies\n"
                        f"📈 Total profiles updated: {result['total_profiles_updated']}"
                    )
                )
            else:
                self.stdout.write(self.style.ERROR("❌ Failed to process popular movies"))

        else:
            # Process batch mode
            batch_size = options['batch']
            self.stdout.write(f"📦 Processing {batch_size} movies with both IMDB and TMDB IDs")

            result = service.enrich_cast_by_tmdb_id_mapping(batch_size)
            if result["success"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Processed {result['movies_processed']} movies\n"
                        f"📈 Total profiles updated: {result['total_updated']}"
                    )
                )

        # Final stats - chỉ hiển thị khi không phải single movie mode
        if not options['movie_id']:
            total_cast = MovieCast.objects.count()
            cast_with_profiles = MovieCast.objects.filter(profile_path__isnull=False).count()
            new_cast_with_profiles = MovieCast.objects.filter(profile_path__isnull=False).count()
            newly_added = new_cast_with_profiles - cast_with_profiles

            self.stdout.write("")
            self.stdout.write(f"📈 Results:")
            self.stdout.write(f"   Profiles added: {newly_added:,}")
            self.stdout.write(f"   Total with profiles: {new_cast_with_profiles:,}")
            if total_cast > 0:
                completion = (new_cast_with_profiles/total_cast)*100
                self.stdout.write(f"   Completion: {completion:.1f}%")

            self.stdout.write("")
            self.stdout.write("💡 Next steps:")
            self.stdout.write("   1. Run with --popular 100 for more movies")
            self.stdout.write("   2. Check frontend to see profile images")
            self.stdout.write("   3. Consider running as Celery task for large batches")
