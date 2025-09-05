from django.core.management.base import BaseCommand
from apps.movies.services.movie_title_genre_service import MovieTitleGenreService
from apps.movies.models import Movie
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test and sync title/genre data for movies from TMDB'

    def add_arguments(self, parser):
        parser.add_argument(
            'movie_id',
            type=int,
            nargs='?',  # Optional argument
            help='Movie ID to test title/genre sync (optional)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync even if data already exists'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--popular',
            action='store_true',
            help='Sync popular movies'
        )
        parser.add_argument(
            '--top-rated',
            action='store_true',
            help='Sync top rated movies'
        )
        parser.add_argument(
            '--upcoming',
            action='store_true',
            help='Sync upcoming movies'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Limit number of movies to process (default: 50)'
        )
        parser.add_argument(
            '--missing-only',
            action='store_true',
            help='Only process movies with missing title/genre data'
        )

    def needs_update(self, movie):
        """Check if movie needs title/genre update"""
        missing_title_en = not movie.title_en or movie.title_en.strip() == ''
        missing_title_vi = not movie.title_vi or movie.title_vi.strip() == ''
        missing_genres = movie.genres.count() == 0
        return missing_title_en or missing_title_vi or missing_genres

    def get_movies_to_process(self, options):
        """Get movies based on filter options"""
        if options['popular']:
            movies = Movie.objects.filter(is_popular=True)
            self.stdout.write(f"🎯 Processing {movies.count()} popular movies")
        elif options['top_rated']:
            movies = Movie.objects.filter(is_top_rated=True)
            self.stdout.write(f"🎯 Processing {movies.count()} top rated movies")
        elif options['upcoming']:
            movies = Movie.objects.filter(is_upcoming=True)
            self.stdout.write(f"🎯 Processing {movies.count()} upcoming movies")
        else:
            # Default: all movies with IMDB ID
            movies = Movie.objects.filter(imdb_id__isnull=False)
            self.stdout.write(f"🎯 Processing {movies.count()} movies with IMDB ID")

        # Apply limit
        limit = options['limit']
        if limit:
            movies = movies[:limit]
            self.stdout.write(f"📊 Limited to {limit} movies")

        # Filter by missing data if requested
        if options['missing_only']:
            movies = [m for m in movies if self.needs_update(m)]
            self.stdout.write(f"📊 Filtered to {len(movies)} movies with missing data")

        return movies

    def process_single_movie(self, movie, options):
        """Process a single movie"""
        force = options['force']
        dry_run = options['dry_run']
        
        # Kiểm tra xem có cần update không
        needs_update = self.needs_update(movie)
        if not needs_update and not force:
            return False, "Already has complete data"

        # Hiển thị thông tin trước khi update
        self.stdout.write(f"\n🎬 Processing: {movie.title} (ID: {movie.id})")
        self.stdout.write(f"   IMDB ID: {movie.imdb_id}")
        self.stdout.write(f"   Title EN: {movie.title_en or '❌ Missing'}")
        self.stdout.write(f"   Title VI: {movie.title_vi or '❌ Missing'}")
        
        genres_en = list(movie.genres.filter(language='en').values_list('name', flat=True))
        genres_vi = list(movie.genres.filter(language='vi').values_list('name', flat=True))
        
        self.stdout.write(f"   Genres EN: {genres_en or '❌ Missing'}")
        self.stdout.write(f"   Genres VI: {genres_vi or '❌ Missing'}")

        if dry_run:
            self.stdout.write("   🔍 DRY RUN - No changes will be made")
            return True, "Dry run completed"

        # Thực hiện sync
        self.stdout.write("   🔄 Syncing from TMDB...")
        success, message = MovieTitleGenreService.sync_movie_data(movie, use_cache=False)
        
        if success:
            # Refresh movie object để lấy data mới
            movie.refresh_from_db()
            
            self.stdout.write("   ✅ Sync successful")
            self.stdout.write(f"   📊 After update:")
            self.stdout.write(f"      Title EN: {movie.title_en or '❌ Still missing'}")
            self.stdout.write(f"      Title VI: {movie.title_vi or '❌ Still missing'}")
            
            genres_en = list(movie.genres.filter(language='en').values_list('name', flat=True))
            genres_vi = list(movie.genres.filter(language='vi').values_list('name', flat=True))
            
            self.stdout.write(f"      Genres EN: {genres_en or '❌ Still missing'}")
            self.stdout.write(f"      Genres VI: {genres_vi or '❌ Still missing'}")
            
            return True, message
        else:
            self.stdout.write(f"   ❌ Sync failed: {message}")
            return False, message

    def handle(self, *args, **options):
        movie_id = options['movie_id']
        
        # Single movie mode
        if movie_id:
            try:
                movie = Movie.objects.get(id=movie_id)
            except Movie.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ Movie ID {movie_id} không tồn tại!")
                )
                return

            if not movie.imdb_id:
                self.stdout.write(
                    self.style.ERROR(f"❌ Movie '{movie.title}' không có IMDB ID!")
                )
                return

            success, message = self.process_single_movie(movie, options)
            if success:
                self.stdout.write(self.style.SUCCESS(f"\n✅ Completed: {message}"))
            else:
                self.stdout.write(self.style.ERROR(f"\n❌ Failed: {message}"))
            return

        # Batch processing mode
        movies = self.get_movies_to_process(options)
        
        if not movies:
            self.stdout.write(self.style.WARNING("⚠️  No movies found to process"))
            return

        # Process movies
        total_movies = len(movies)
        success_count = 0
        error_count = 0
        
        self.stdout.write(f"\n🚀 Starting batch processing...")
        
        for i, movie in enumerate(movies, 1):
            try:
                success, message = self.process_single_movie(movie, options)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    
                # Progress indicator
                if i % 10 == 0 or i == total_movies:
                    self.stdout.write(f"📈 Progress: {i}/{total_movies} ({i/total_movies*100:.1f}%)")
                    
            except Exception as e:
                self.stdout.write(f"   💥 Error processing movie {movie.id}: {str(e)}")
                error_count += 1
                continue

        # Final summary
        self.stdout.write(f"\n🎉 BATCH PROCESSING COMPLETED!")
        self.stdout.write(f"📊 Summary:")
        self.stdout.write(f"   Total processed: {total_movies}")
        self.stdout.write(f"   Successful: {success_count}")
        self.stdout.write(f"   Errors: {error_count}")
        self.stdout.write(f"   Success rate: {success_count/total_movies*100:.1f}%") 