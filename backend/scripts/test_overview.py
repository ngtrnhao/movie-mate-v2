import os
import django
import sys
import time
from typing import List

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.movies.services.movie_overview_service import MovieOverviewService
from apps.movies.models import Movie

def get_all_imdb_ids() -> List[str]:
    """Get all IMDB IDs from database"""
    return Movie.objects.exclude(imdb_id__isnull=True).values_list('imdb_id', flat=True)

def test_movie_overview(imdb_id: str):
    """Test getting movie overview from multiple sources"""
    print(f"\nTesting movie overview for IMDB ID: {imdb_id}")
    print("-" * 50)

    overviews = MovieOverviewService.get_movie_overview(imdb_id)

    if not overviews:
        print("No overviews found!")
        return

    if "vi" in overviews:
        print("\nTiếng Việt:")
        print("-" * 20)
        print(overviews["vi"])

    if "en" in overviews:
        print("\nEnglish:")
        print("-" * 20)
        print(overviews["en"])

def main():
    # Get all IMDB IDs from database
    imdb_ids = get_all_imdb_ids()
    total_movies = len(imdb_ids)

    print(f"Found {total_movies} movies in database")

    # Process each movie
    for index, imdb_id in enumerate(imdb_ids, 1):
        print(f"\nProcessing movie {index}/{total_movies}")
        test_movie_overview(imdb_id)

        # Add delay to avoid rate limiting
        if index < total_movies:
            time.sleep(1)  # 1 second delay between requests

        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()