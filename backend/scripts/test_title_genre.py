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

def test_title_genre(imdb_id: str):
    print(f"\nTesting title/genres for IMDB ID: {imdb_id}")
    print("-" * 50)
    data = MovieTitleGenreService.get_title_and_genres(imdb_id)
    print("Title (EN):", data["title"].get("en"))
    print("Title (VI):", data["title"].get("vi"))
    print("Genres (EN):", data["genres"].get("en"))
    print("Genres (VI):", data["genres"].get("vi"))
    print("=" * 50)

if __name__ == "__main__":
    imdb_ids = list(Movie.objects.exclude(imdb_id__isnull=True).values_list('imdb_id', flat=True))
    print(f"Found {len(imdb_ids)} movies in database.")
    for imdb_id in imdb_ids:
        test_title_genre(imdb_id)
