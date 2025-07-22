import os
import sys
import django
import logging
from datetime import datetime
import time

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.movies.models import Movie, MovieTrailer
from apps.movies.services.movie_tmdb_enrich_service import MovieTMDBEnrichService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'enrich_missing_trailers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_movies_without_trailer():
    """Lấy tất cả movies chưa có trailer hoặc clip."""
    # Không có bất kỳ MovieTrailer nào với type=TRAILER hoặc CLIP
    movie_ids_with_trailer = set(
        MovieTrailer.objects.filter(type__in=["TRAILER", "CLIP"]).values_list("movie_id", flat=True)
    )
    return Movie.objects.exclude(id__in=movie_ids_with_trailer)

def enrich_missing_trailers():
    movies = get_movies_without_trailer()
    total = movies.count()
    logger.info(f"Found {total} movies without trailer or clip.")
    updated = 0
    failed = 0
    for idx, movie in enumerate(movies, 1):
        logger.info(f"[{idx}/{total}] Enriching trailers for movie: {movie.title} (ID: {movie.id})")
        try:
            MovieTMDBEnrichService.enrich_movie_trailers(movie)
            logger.info(f"✅ Updated trailers for movie: {movie.title}")
            updated += 1
        except Exception as e:
            logger.error(f"❌ Failed to update trailers for movie: {movie.title} - {e}")
            failed += 1
        time.sleep(0.5)  # Avoid rate limit
    logger.info(f"\n=== SUMMARY ===")
    logger.info(f"Total movies processed: {total}")
    logger.info(f"Successfully updated: {updated}")
    logger.info(f"Failed: {failed}")

if __name__ == "__main__":
    enrich_missing_trailers()
