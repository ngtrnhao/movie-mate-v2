from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import MovieRating
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MovieRating)
def update_movie_cached_ratings_on_save(sender, instance, created, **kwargs):
    """Update movie cached ratings when a MovieRating is created or updated"""
    try:
        if instance.movie:
            instance.movie.update_cached_ratings()
            logger.info(f"Updated cached ratings for movie {instance.movie.id} after rating {'created' if created else 'updated'}")
    except Exception as e:
        logger.error(f"Error updating cached ratings for movie {instance.movie.id}: {str(e)}")


@receiver(post_delete, sender=MovieRating)
def update_movie_cached_ratings_on_delete(sender, instance, **kwargs):
    """Update movie cached ratings when a MovieRating is deleted"""
    try:
        if instance.movie:
            instance.movie.update_cached_ratings()
            logger.info(f"Updated cached ratings for movie {instance.movie.id} after rating deleted")
    except Exception as e:
        logger.error(f"Error updating cached ratings for movie {instance.movie.id}: {str(e)}")
