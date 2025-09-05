import os
import sys
import time
from datetime import datetime
import logging
from typing import List

import django

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db.models import Q
from apps.movies.models import Movie, MovieMetadata
from apps.movies.services.movie_tmdb_enrich_service import MovieTMDBEnrichService
from apps.movies.services.tmdb_service import TMDBService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s %(asctime)s %(name)s %(process)d %(thread)d %(message)s',
    handlers=[
        logging.FileHandler(f'metadata_enrich_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_movies_without_metadata() -> List[Movie]:
    """Get all movies that don't have metadata or have incomplete metadata."""
    return Movie.objects.filter(
        Q(moviemetadata__isnull=True) |  # Movies without metadata
        Q(moviemetadata__budget__isnull=True) |  # Movies with incomplete metadata
        Q(moviemetadata__revenue__isnull=True) |
        Q(moviemetadata__tagline__isnull=True) |
        Q(moviemetadata__homepage__isnull=True) |
        Q(moviemetadata__keywords=[]) |  # Empty list fields
        Q(moviemetadata__production_companies=[]) |
        Q(moviemetadata__production_countries=[]) |
        Q(moviemetadata__spoken_languages=[])
    ).distinct()

def enrich_movie_metadata():
    """Enrich metadata for movies that don't have it."""
    start_time = datetime.now()
    logger.info(f"=== Starting metadata enrichment at {start_time} ===")

    # Get movies without metadata
    movies = get_movies_without_metadata()
    total_movies = movies.count()
    logger.info(f"Found {total_movies} movies without complete metadata")

    processed_count = 0
    error_count = 0
    success_count = 0
    empty_lists_count = 0
    tmdb_service = TMDBService()

    for index, movie in enumerate(movies, 1):
        logger.info(f"\nProcessing movie {index}/{total_movies}: {movie.title} ({movie.imdb_id})")

        try:
            # Get current metadata state for logging
            old_metadata = MovieMetadata.objects.filter(movie=movie).first()
            old_state = {
                'budget': getattr(old_metadata, 'budget', None),
                'revenue': getattr(old_metadata, 'revenue', None),
                'tagline': getattr(old_metadata, 'tagline', None),
                'homepage': getattr(old_metadata, 'homepage', None),
                'keywords': getattr(old_metadata, 'keywords', []),
                'production_companies': getattr(old_metadata, 'production_companies', []),
                'production_countries': getattr(old_metadata, 'production_countries', []),
                'spoken_languages': getattr(old_metadata, 'spoken_languages', [])
            }

            # Check for empty lists
            empty_lists = [
                field for field in ['keywords', 'production_companies', 'production_countries', 'spoken_languages']
                if not old_state[field]
            ]
            if empty_lists:
                logger.info("Found empty list fields:")
                for field in empty_lists:
                    logger.info(f"  - {field}")
                empty_lists_count += 1

            # First ensure we have TMDB ID
            if not movie.tmdb_id and movie.imdb_id:
                tmdb_id = TMDBService.get_tmdb_id_from_imdb(movie.imdb_id)
                if tmdb_id:
                    movie.tmdb_id = tmdb_id
                    movie.save()
                    logger.info(f"Found and saved TMDB ID: {tmdb_id}")

            # Enrich metadata
            if movie.tmdb_id:
                # Get movie details from TMDB
                tmdb_data = TMDBService.get_movie_details(movie.tmdb_id)
                if tmdb_data:
                    # Create or update metadata
                    metadata, created = MovieMetadata.objects.get_or_create(movie=movie)
                    metadata.budget = tmdb_data.get("budget")
                    metadata.revenue = tmdb_data.get("revenue")
                    metadata.tagline = tmdb_data.get("tagline")
                    metadata.homepage = tmdb_data.get("homepage")
                    metadata.keywords = [kw["name"] for kw in tmdb_data.get("keywords", {}).get("keywords", [])] if "keywords" in tmdb_data else []
                    metadata.production_companies = tmdb_data.get("production_companies", [])
                    metadata.production_countries = tmdb_data.get("production_countries", [])
                    metadata.spoken_languages = tmdb_data.get("spoken_languages", [])
                    metadata.save()

                    # Get new metadata state for comparison
                    movie.refresh_from_db()
                    new_metadata = MovieMetadata.objects.filter(movie=movie).first()
                    new_state = {
                        'budget': getattr(new_metadata, 'budget', None),
                        'revenue': getattr(new_metadata, 'revenue', None),
                        'tagline': getattr(new_metadata, 'tagline', None),
                        'homepage': getattr(new_metadata, 'homepage', None),
                        'keywords': getattr(new_metadata, 'keywords', []),
                        'production_companies': getattr(new_metadata, 'production_companies', []),
                        'production_countries': getattr(new_metadata, 'production_countries', []),
                        'spoken_languages': getattr(new_metadata, 'spoken_languages', [])
                    }

                    # Log changes
                    changes = []
                    for key in old_state:
                        if old_state[key] != new_state[key]:
                            if isinstance(old_state[key], list):
                                changes.append(f"{key}: {len(old_state[key])} items -> {len(new_state[key])} items")
                                if len(new_state[key]) > 0:
                                    logger.info(f"New {key}:")
                                    for item in new_state[key][:5]:  # Show first 5 items
                                        if isinstance(item, dict) and 'name' in item:
                                            logger.info(f"  - {item['name']}")
                                        else:
                                            logger.info(f"  - {item}")
                                    if len(new_state[key]) > 5:
                                        logger.info(f"  ... and {len(new_state[key]) - 5} more items")
                            else:
                                changes.append(f"{key}: {old_state[key]} -> {new_state[key]}")

                    if changes:
                        logger.info("Metadata changes:")
                        for change in changes:
                            logger.info(f"  {change}")
                        success_count += 1
                    else:
                        logger.warning("No metadata changes detected")
                else:
                    logger.warning(f"Could not get TMDB data for movie: {movie.title} (TMDB ID: {movie.tmdb_id})")
            else:
                logger.warning(f"Could not find TMDB ID for movie: {movie.title} (IMDB: {movie.imdb_id})")

            processed_count += 1

            # Add a small delay to avoid overwhelming the API
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"Error processing {movie.title}: {str(e)}")
            error_count += 1

    # Print summary
    logger.info("\n=== Enrichment Summary ===")
    logger.info(f"Total movies processed: {total_movies}")
    logger.info(f"Successfully processed: {processed_count}")
    logger.info(f"Successful updates: {success_count}")
    logger.info(f"Movies with empty lists: {empty_lists_count}")
    logger.info(f"Errors encountered: {error_count}")

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"\n=== Enrichment completed at {end_time} ===")
    logger.info(f"Total duration: {duration}")

if __name__ == "__main__":
    enrich_movie_metadata()
