import os
import sys
import time
from datetime import datetime

import django

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.movies.tasks import (
    sync_popular_movies,
    sync_top_rated_movies,
    sync_upcoming_movies,
    process_movie_data,
)
from apps.movies.services.imdb_service import IMDBService
from apps.movies.models import Movie
from django.core.cache import cache


def test_cache_and_tasks():
    start_time = datetime.now()
    print(f"\n=== Starting test at {start_time} ===")

    # Clear all movie caches first
    print("\n1. Clearing movie caches...")
    cache.delete("popular_movies")
    cache.delete("top_rated_movies")
    cache.delete("upcoming_movies")

    # # Test popular movies
    # print("\n2. Testing popular movies task...")
    # result = sync_popular_movies.delay()
    # print(f"Task ID: {result.id}")
    # time.sleep(5)  # Wait for task to complete

    # # Check cache
    # popular_movies = cache.get("popular_movies")
    # print(f"Popular movies in cache: {popular_movies is not None}")

    # # Test top rated movies
    # print("\n3. Testing top rated movies task...")
    # result = sync_top_rated_movies.delay()
    # print(f"Task ID: {result.id}")
    # time.sleep(5)  # Wait for task to complete

    # # Check cache
    # top_rated_movies = cache.get("top_rated_movies")
    # print(f"Top rated movies in cache: {top_rated_movies is not None}")

    # # Test upcoming movies
    # print("\n4. Testing upcoming movies task...")
    # result = sync_upcoming_movies.delay()
    # print(f"Task ID: {result.id}")
    # time.sleep(5)  # Wait for task to complete

    # # Check cache
    # upcoming_movies = cache.get("upcoming_movies")
    # print(f"Upcoming movies in cache: {upcoming_movies is not None}")

    # Test movie overviews for all movies
    print("\n2. Testing movie overviews for all movies...")
    movies = Movie.objects.all()
    total_movies = movies.count()
    print(f"Total movies in database: {total_movies}")

    # Count movies with and without IMDB IDs
    movies_with_imdb = movies.exclude(imdb_id__isnull=True).count()
    movies_without_imdb = movies.filter(imdb_id__isnull=True).count()
    print(f"Movies with IMDB ID: {movies_with_imdb}")
    print(f"Movies without IMDB ID: {movies_without_imdb}")

    processed_count = 0
    skipped_count = 0
    error_count = 0

    for index, movie in enumerate(movies, 1):
        print(f"\nProcessing movie {index}/{total_movies}: {movie.title} ({movie.imdb_id})")
        if not movie.imdb_id:
            print(f"Skipping {movie.title} - No IMDB ID")
            skipped_count += 1
            continue

        # Test getting overviews directly
        try:
            overviews = IMDBService.get_movie_overview(movie.imdb_id)
            print(f"Direct API call overviews: {overviews}")

            # Test processing movie data (which includes overviews)
            result = process_movie_data.delay(movie.imdb_id)
            print(f"Task ID: {result.id}")
            time.sleep(2)  # Wait for task to complete
            processed_count += 1
        except Exception as e:
            print(f"Error processing {movie.title}: {str(e)}")
            error_count += 1

    # Print summary
    print("\n=== Processing Summary ===")
    print(f"Total movies in database: {total_movies}")
    print(f"Successfully processed: {processed_count}")
    print(f"Skipped (no IMDB ID): {skipped_count}")
    print(f"Errors encountered: {error_count}")

    # Print cache keys
    print("\n3. All movie-related cache keys:")
    all_keys = cache.keys("*")
    movie_keys = [k for k in all_keys if k.startswith("movie_")]
    print(f"Found keys: {movie_keys}")

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n=== Test completed at {end_time} ===")
    print(f"Total duration: {duration}")


if __name__ == "__main__":
    test_cache_and_tasks()
