from celery import shared_task
from django.core.cache import cache
from .models import GenreSummary
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def refresh_genre_summary_task(self):
    """
    Celery task để refresh genre summary table
    Chạy định kỳ để đảm bảo dữ liệu luôn mới nhất
    """
    try:
        logger.info("Starting genre summary refresh task")

        # Refresh all summaries
        GenreSummary.refresh_all_summaries()

        # Clear cache
        cache.delete_pattern('movie_categories_summary_*')

        logger.info("Genre summary refresh task completed successfully")
        return {
            'status': 'success',
            'message': 'Genre summary refreshed successfully'
        }

    except Exception as e:
        logger.error(f"Error in genre summary refresh task: {str(e)}", exc_info=True)
        # Retry task
        raise self.retry(countdown=60, max_retries=3)

@shared_task(bind=True)
def update_genre_summary_for_movie(self, movie_id):
    """
    Celery task để cập nhật summary cho một movie cụ thể
    """
    try:
        from apps.movies.models import Movie

        movie = Movie.objects.get(id=movie_id)

        # Cập nhật summary cho tất cả genres của movie này
        for genre in movie.genres.all():
            GenreSummary.update_summary_for_genre(genre.id)

        logger.info(f"Updated genre summary for movie {movie_id}")
        return {
            'status': 'success',
            'message': f'Genre summary updated for movie {movie_id}'
        }

    except Movie.DoesNotExist:
        logger.warning(f"Movie {movie_id} not found")
        return {
            'status': 'warning',
            'message': f'Movie {movie_id} not found'
        }
    except Exception as e:
        logger.error(f"Error updating genre summary for movie {movie_id}: {str(e)}", exc_info=True)
        raise self.retry(countdown=30, max_retries=2)
