from celery import shared_task
from .services.imdb_service import IMDBService
from .models import Movie, MovieRating, MovieMetadata, MovieGenre, Genre, MovieCast, MovieTrailer, MovieBoxOffice, MovieReview
from django.db import transaction
import logging
from django.utils import timezone
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from django.core.cache import cache
import time

logger = get_task_logger(__name__)

def clear_movie_cache():
    """Clear all movie-related caches"""
    cache.delete_pattern('movie_*')
    cache.delete('popular_movies')
    cache.delete('top_rated_movies')
    cache.delete('upcoming_movies')

@shared_task
def sync_popular_movies():
    """Sync popular movies from IMDB"""
    try:
        tconsts = IMDBService.get_popular_movies()
        for tconst in tconsts:
            imdb_id = tconst.split('/')[-2] if '/' in tconst else tconst
            process_movie_data.delay(imdb_id)
            time.sleep(2)  # Thêm delay để tránh rate limit

        # Clear cache after successful sync
        clear_movie_cache()
    except Exception as e:
        logger.error(f"Error syncing popular movies: {str(e)}")
        raise

@shared_task
def sync_top_rated_movies():
    """Sync top rated movies from IMDB"""
    try:
        tconsts = IMDBService.get_top_rated_movies(limit=50)
        for tconst in tconsts:
            imdb_id = tconst.split('/')[-2] if '/' in tconst else tconst
            process_movie_data.delay(imdb_id)
            time.sleep(2)  # Thêm delay để tránh rate limit

        # Clear cache after successful sync
        clear_movie_cache()
    except Exception as e:
        logger.error(f"Error syncing top rated movies: {str(e)}")
        raise

@shared_task
def sync_upcoming_movies():
    """Sync upcoming movies from IMDB"""
    try:
        tconsts = IMDBService.get_upcoming_movies()
        for tconst in tconsts:
            imdb_id = tconst['id'].split('/')[-2] if isinstance(tconst, dict) and 'id' in tconst else tconst
            process_movie_data.delay(imdb_id)
            time.sleep(2)  # Thêm delay để tránh rate limit

        # Clear cache after successful sync
        clear_movie_cache()
    except Exception as e:
        logger.error(f"Error syncing upcoming movies: {str(e)}")
        raise

@shared_task(bind=True, max_retries=3, rate_limit='20/m')  # Rate limit 1 task per minute
def process_movie_data(self, imdb_id: str):
    """Process movie data from IMDB"""
    try:
        # Clean up imdb_id - handle all possible cases
        if isinstance(imdb_id, dict):
            if 'id' in imdb_id:
                if isinstance(imdb_id['id'], dict) and 'id' in imdb_id['id']:
                    imdb_id = imdb_id['id']['id']
                else:
                    imdb_id = imdb_id['id']

        # Extract ttxxxxxxx from /title/ttxxxxxxx/
        imdb_id = imdb_id.split('/')[-2] if '/' in imdb_id else imdb_id

        # Validate imdb_id format
        if not imdb_id.startswith('tt'):
            logger.error(f"Invalid IMDB ID format: {imdb_id}")
            return False

        # Get movie details
        movie_data = IMDBService.get_movie_details(imdb_id)
        print(f"[DEBUG] Movie data for {imdb_id}: {movie_data}")
        if not movie_data:
            logger.error(f"Failed to get movie details for {imdb_id}")
            return False

        # Mapping với cấu trúc mới
        try:
            title_data = movie_data.get('data', {}).get('title', {}) or movie_data
            title = title_data.get('titleText', {}).get('text', '') or title_data.get('title', '')
            original_title = title_data.get('originalTitleText', {}).get('text', '')
            release_date = IMDBService.get_release_date(imdb_id)
            poster_url = title_data.get('primaryImage', {}).get('url', '')
            runtime_seconds = title_data.get('runtime', {}).get('seconds')
            runtime = runtime_seconds // 60 if runtime_seconds else None
            # Ngôn ngữ
            languages = []
            spoken_languages = title_data.get('spokenLanguages', {}).get('spokenLanguages', [])
            for lang in spoken_languages:
                if 'text' in lang:
                    languages.append(lang['text'])
            # Quốc gia
            countries = []
            country_list = title_data.get('countriesOfOrigin', {}).get('countries', [])
            for c in country_list:
                if 'text' in c:
                    countries.append(c['text'])
            # Homepage/links
            links = []
            for edge in title_data.get('officialLinks', {}).get('edges', []):
                node = edge.get('node', {})
                if 'url' in node:
                    links.append(node['url'])
        except Exception as e:
            logger.error(f"Error mapping movie data for {imdb_id}: {e}")
            return

        with transaction.atomic():
            # Xác định status dựa trên release_date
            current_date = timezone.now().date()
            if not release_date:
                status = 'RUMORED'
            elif release_date > current_date:
                status = 'UPCOMING'
            else:
                status = 'RELEASED'

            # Get or create movie
            movie, created = Movie.objects.update_or_create(
                imdb_id=imdb_id,
                defaults={
                    'title': title,
                    'original_title': original_title,
                    'overview': '',  # Không có trong response
                    'release_date': release_date,
                    'poster_url': poster_url,
                    'backdrop_url': '',  # Không có trong response
                    'runtime': runtime,
                    'status': status,
                    'last_synced': timezone.now()
                }
            )

            # Update metadata
            MovieMetadata.objects.update_or_create(
                movie=movie,
                defaults={
                    'budget': None,  # Không có trong response
                    'revenue': None,  # Không có trong response
                    'tagline': None,  # Không có trong response
                    'homepage': links[0] if links else None,
                    'keywords': None,  # Không có trong response
                    'production_companies': None,  # Không có trong response
                    'production_countries': countries,
                    'spoken_languages': languages,
                }
            )

            # Không update genres vì không có trong response

            # Clear movie cache
            cache.delete(f'movie_{movie.id}')

            print(f"[DEBUG] Successfully processed movie data for {imdb_id}")
            return True

    except Exception as e:
        logger.error(f"Error processing movie {imdb_id}: {str(e)}")
        try:
            self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for movie {imdb_id}")
            raise

@shared_task
def update_movie_data(days: int = 7, limit: int = 50):
    """Update data for recently modified movies"""
    try:
        # Get movies updated in the last X days
        movies = Movie.objects.filter(
            updated_at__gte=timezone.now() - timezone.timedelta(days=days)
        )[:limit]

        for movie in movies:
            process_movie_data.delay(movie.imdb_id)

        # Clear cache after update
        clear_movie_cache()

        return f"Successfully queued {movies.count()} movies for update"
    except Exception as e:
        logger.error(f"Error updating movie data: {str(e)}")
        raise
