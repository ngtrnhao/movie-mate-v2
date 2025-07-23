from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.movies.models import Movie, MovieAdminControl, MovieQualityMetrics, MovieScheduling, ProductionMetrics,MovieRating
from apps.movies.services.elasticsearch_service import update_movie_index

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


@receiver(post_save, sender=Movie)
@receiver(post_save, sender=MovieAdminControl)
@receiver(post_save, sender=MovieQualityMetrics)
@receiver(post_save, sender=MovieScheduling)
@receiver(post_save, sender=ProductionMetrics)
def auto_update_movie_index(sender, instance, **kwargs):
    movie_id = instance.movie.id if hasattr(instance, 'movie') else instance.id
    update_movie_index(movie_id)

@receiver(post_delete, sender=Movie)
def auto_delete_movie_index(sender, instance, **kwargs):
    try:
        from apps.movies.document import MovieDocument
        MovieDocument.get(id=instance.id).delete()
    except Exception:
        pass


@receiver(post_save, sender=Movie)
def create_related_records_for_new_movie(sender, instance, created, **kwargs):
    """Tự động tạo các record liên quan khi Movie mới được tạo"""
    if created:
        MovieQualityMetrics.objects.get_or_create(movie=instance)
        MovieAdminControl.objects.get_or_create(movie=instance)
        ProductionMetrics.objects.get_or_create(movie=instance)
        MovieScheduling.objects.get_or_create(movie=instance)
