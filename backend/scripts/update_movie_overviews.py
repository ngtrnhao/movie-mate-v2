import os
import django
import sys
import time
import logging
from typing import List, Dict
from datetime import datetime
from django.db import models

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.movies.services.movie_overview_service import MovieOverviewService
from apps.movies.models import Movie

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'overview_update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_movies_without_overview() -> List[Movie]:
    """Get all movies that need overview update (cả tiếng Anh và Việt đều chưa có hoặc rỗng)"""
    return Movie.objects.filter(
        imdb_id__isnull=False
    ).filter(
        (models.Q(overview_vi__isnull=True) | models.Q(overview_vi__exact='')) &
        (models.Q(overview_en__isnull=True) | models.Q(overview_en__exact=''))
    )

def update_movie_overview(movie: Movie) -> bool:
    """Update movie overview in database"""
    try:
        overviews = MovieOverviewService.get_movie_overview(movie.imdb_id)

        if not overviews:
            logger.warning(f"No overviews found for movie {movie.imdb_id}")
            return False

        # Update movie with new overviews
        if "vi" in overviews and overviews["vi"]:
            movie.overview_vi = overviews["vi"]
        if "en" in overviews and overviews["en"]:
            movie.overview_en = overviews["en"]

        movie.save()
        logger.info(f"Updated overviews for movie {movie.imdb_id}")
        return True

    except Exception as e:
        logger.error(f"Error updating overview for movie {movie.imdb_id}: {str(e)}")
        return False

def main():
    # Get movies that need overview update
    movies = get_movies_without_overview()
    total_movies = len(movies)

    logger.info(f"Found {total_movies} movies without overviews")

    # Process each movie
    success_count = 0
    for index, movie in enumerate(movies, 1):
        logger.info(f"Processing movie {index}/{total_movies}: {movie.imdb_id}")

        if update_movie_overview(movie):
            success_count += 1

        # Add delay to avoid rate limiting
        if index < total_movies:
            time.sleep(1)  # 1 second delay between requests

    # Log summary
    logger.info(f"Update completed. Successfully updated {success_count}/{total_movies} movies")

if __name__ == "__main__":
    main()
