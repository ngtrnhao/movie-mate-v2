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

from apps.movies.tasks import enrich_movie_tmdb_metadata
from apps.movies.models import Movie
from django.db.models import Q

def enrich_all_movies():
    start_time = datetime.now()
    print(f"\n=== Starting enrichment at {start_time} ===")

    # Get all movies that have IMDB ID but no backdrop_url
    movies = Movie.objects.filter(
        imdb_id__isnull=False,
        backdrop_url__isnull=True
    )
    total_movies = movies.count()
    print(f"Total movies to enrich: {total_movies}")

    processed_count = 0
    error_count = 0

    for index, movie in enumerate(movies, 1):
        print(f"\nProcessing movie {index}/{total_movies}: {movie.title} ({movie.imdb_id})")
        try:
            # Enrich movie metadata
            result = enrich_movie_tmdb_metadata.delay(movie.imdb_id)
            print(f"Task ID: {result.id}")
            processed_count += 1
            # Add a small delay to avoid overwhelming the API
            time.sleep(0.5)
        except Exception as e:
            print(f"Error processing {movie.title}: {str(e)}")
            error_count += 1

    # Print summary
    print("\n=== Enrichment Summary ===")
    print(f"Total movies processed: {total_movies}")
    print(f"Successfully queued: {processed_count}")
    print(f"Errors encountered: {error_count}")

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n=== Enrichment completed at {end_time} ===")
    print(f"Total duration: {duration}")

if __name__ == "__main__":
    enrich_all_movies()
