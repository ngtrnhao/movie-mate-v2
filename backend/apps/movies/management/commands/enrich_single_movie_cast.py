from django.core.management.base import BaseCommand
from apps.movies.services.cast_profile_enrichment_service import CastProfileEnrichmentService
from apps.movies.models import Movie
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Enrich cast profiles for a single movie (fast mode - no stats)'

    def add_arguments(self, parser):
        parser.add_argument(
            'movie_id',
            type=int,
            help='Movie ID to enrich cast for'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Maximum number of cast members to update (default: 20)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        movie_id = options['movie_id']
        limit = options['limit']
        
        # Kiểm tra movie có tồn tại không
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Movie ID {movie_id} không tồn tại!")
            )
            return

        self.stdout.write(f"🎬 Enriching cast for: {movie.title} (ID: {movie_id})")
        
        if not movie.tmdb_id:
            self.stdout.write(
                self.style.ERROR(f"❌ Movie '{movie.title}' không có TMDB ID!")
            )
            return

        if options['dry_run']:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be made"))
            return

        # Chạy enrichment
        service = CastProfileEnrichmentService()
        result = service.enrich_movie_cast_profiles(movie_id, limit=limit)
        
        if result["success"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Hoàn thành! {result['updated_count']} profiles đã được cập nhật"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Lỗi: {result['error']}")
            ) 