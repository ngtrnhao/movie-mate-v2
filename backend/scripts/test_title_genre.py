import os
import django
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.movies.services.movie_title_genre_service import MovieTitleGenreService
from apps.movies.models import Movie

def needs_update(movie):
    missing_title_en = not movie.title_en or movie.title_en.strip() == ''
    missing_title_vi = not movie.title_vi or movie.title_vi.strip() == ''
    missing_genres = movie.genres.count() == 0
    return missing_title_en or missing_title_vi or missing_genres

def update_and_report(movie):
    print(f"\nChecking movie: {movie.imdb_id} | {movie.display_title}")
    print("-" * 50)
    before = {
        'title_en': movie.title_en,
        'title_vi': movie.title_vi,
        'genres_en': list(movie.genres.filter(language='en').values_list('name', flat=True)),
        'genres_vi': list(movie.genres.filter(language='vi').values_list('name', flat=True)),
    }
    print("Before update:", before)
    success, message = MovieTitleGenreService.sync_movie_data(movie)
    after = {
        'title_en': movie.title_en,
        'title_vi': movie.title_vi,
        'genres_en': list(movie.genres.filter(language='en').values_list('name', flat=True)),
        'genres_vi': list(movie.genres.filter(language='vi').values_list('name', flat=True)),
    }
    print("After update:", after)
    print("Sync result:", message)
    print("=" * 50)

if __name__ == "__main__":
    movies = Movie.objects.exclude(imdb_id__isnull=True)
    print(f"Found {movies.count()} movies in database.")
    updated = 0
    for movie in movies:
        if needs_update(movie):
            update_and_report(movie)
            updated += 1
    print(f"\nTotal movies updated: {updated}")
