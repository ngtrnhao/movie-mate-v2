from celery import shared_task
from .services.imdb_service import IMDBService
from .models import Movie, MovieRating, MovieMetadata, MovieGenre, Genre, MovieCast, MovieTrailer, MovieBoxOffice, MovieReview
from django.db import transaction
import logging
from django.utils import timezone
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from django.core.cache import cache

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

        # Clear cache after successful sync
        clear_movie_cache()
    except Exception as e:
        logger.error(f"Error syncing popular movies: {str(e)}")
        raise

@shared_task
def sync_top_rated_movies():
    """Sync top rated movies from IMDB"""
    try:
        tconsts = IMDBService.get_top_rated_movies()
        for tconst in tconsts:
            imdb_id = tconst.split('/')[-2] if '/' in tconst else tconst
            process_movie_data.delay(imdb_id)

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
            imdb_id = tconst.split('/')[-2] if '/' in tconst else tconst
            process_movie_data.delay(imdb_id)

        # Clear cache after successful sync
        clear_movie_cache()
    except Exception as e:
        logger.error(f"Error syncing upcoming movies: {str(e)}")
        raise

@shared_task(bind=True, max_retries=3)
def process_movie_data(self, imdb_id: str):
    """Process movie data from IMDB"""
    try:
        # Clean up imdb_id
        if isinstance(imdb_id, dict) and 'id' in imdb_id:
            imdb_id = imdb_id['id']
        imdb_id = imdb_id.split('/')[-2] if '/' in imdb_id else imdb_id

        # Get movie details
        movie_data = IMDBService.get_movie_details(imdb_id)
        if not movie_data:
            logger.error(f"Failed to get movie details for {imdb_id}")
            return

        with transaction.atomic():
            # Xác định status dựa trên release_date
            release_date = IMDBService._parse_date(movie_data.get('releaseDate'))
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
                    'title': movie_data.get('title', ''),
                    'original_title': movie_data.get('originalTitle', ''),
                    'overview': movie_data.get('plot', ''),
                    'release_date': release_date,
                    'poster_url': movie_data.get('image', ''),
                    'backdrop_url': movie_data.get('backgroundImage', ''),
                    'runtime': movie_data.get('runningTimeInMinutes'),
                    'status': status,
                    'last_synced': timezone.now()
                }
            )

            # Update movie status
            movie.is_popular = imdb_id in IMDBService.get_popular_movies()
            movie.is_top_rated = imdb_id in IMDBService.get_top_rated_movies()
            movie.is_upcoming = status == 'UPCOMING'
            movie.save()

            # Update metadata
            MovieMetadata.objects.update_or_create(
                movie=movie,
                defaults={
                    'budget': IMDBService._parse_money(movie_data.get('budget')),
                    'revenue': IMDBService._parse_money(movie_data.get('cumulativeWorldwideGross')),
                    'tagline': movie_data.get('tagline'),
                    'homepage': movie_data.get('homepage'),
                    'keywords': movie_data.get('keywords'),
                    'production_companies': movie_data.get('productionCompanies'),
                    'production_countries': movie_data.get('productionCountries'),
                    'spoken_languages': movie_data.get('languages'),
                }
            )

            # Update genres
            if 'genreList' in movie_data:
                genres = [g['value'] for g in movie_data['genreList']]
                movie.genres.set(genres)

            # Clear movie cache
            cache.delete(f'movie_{movie.id}')

            logger.info(f"Successfully processed movie data for {imdb_id}")
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
