import os
import sys
import time

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
)
from django.core.cache import cache


def test_cache_and_tasks():
    print("Testing cache and tasks...")

    # Clear all movie caches first
    print("\n1. Clearing movie caches...")
    cache.delete("popular_movies")
    cache.delete("top_rated_movies")
    cache.delete("upcoming_movies")

    # Test popular movies
    print("\n2. Testing popular movies task...")
    result = sync_popular_movies.delay()
    print(f"Task ID: {result.id}")
    time.sleep(5)  # Wait for task to complete

    # Check cache
    popular_movies = cache.get("popular_movies")
    print(f"Popular movies in cache: {popular_movies is not None}")

    # Test top rated movies
    print("\n3. Testing top rated movies task...")
    result = sync_top_rated_movies.delay()
    print(f"Task ID: {result.id}")
    time.sleep(5)  # Wait for task to complete

    # Check cache
    top_rated_movies = cache.get("top_rated_movies")
    print(f"Top rated movies in cache: {top_rated_movies is not None}")

    # Test upcoming movies
    print("\n4. Testing upcoming movies task...")
    result = sync_upcoming_movies.delay()
    print(f"Task ID: {result.id}")
    time.sleep(5)  # Wait for task to complete

    # Check cache
    upcoming_movies = cache.get("upcoming_movies")
    print(f"Upcoming movies in cache: {upcoming_movies is not None}")

    # Print cache keys
    print("\n5. All movie-related cache keys:")
    all_keys = cache.keys("*")
    movie_keys = [k for k in all_keys if k.startswith("movie_")]
    print(f"Found keys: {movie_keys}")


if __name__ == "__main__":
    test_cache_and_tasks()
