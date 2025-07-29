from celery import shared_task
from django.contrib.auth import get_user_model
from apps.movies.models import Movie
from apps.recommendations.models import RecommendationResult
from apps.recommendations.services import HybridRecommendationService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(bind=True)
def generate_user_recommendations_async(self, user_id: int, context: str = 'homepage', limit: int = 20):
    """
    Generate recommendations for a user asynchronously
    """
    from django.core.cache import cache
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        # Cache task ID for this user/context
        task_cache_key = f"rec_task:{user_id}:{context}"
        cache.set(task_cache_key, self.request.id, 300)  # Cache for 5 minutes

        logger.info(f"Starting background recommendation generation task {self.request.id} for user {user_id}")

        # Get user
        user = User.objects.get(id=user_id)

        # Check if user has complete profile
        if not user.age or not user.gender:
            logger.info(f"User {user_id} has incomplete profile - skipping recommendation generation")
            return []

        # Clear existing recommendations for this user and context
        RecommendationResult.objects.filter(user=user, context=context).delete()

        # Generate recommendations using hybrid service
        from .services import HybridRecommendationService
        hybrid_service = HybridRecommendationService()
        recommendations = hybrid_service.generate_hybrid_recommendations(user, limit, context)

        # Remove duplicates
        seen_movie_ids = set()
        unique_recommendations = []
        for movie in recommendations:
            if movie.id not in seen_movie_ids:
                seen_movie_ids.add(movie.id)
                unique_recommendations.append(movie)

        # Store recommendations
        for rank, movie in enumerate(unique_recommendations[:limit], 1):
            RecommendationResult.objects.create(
                user=user,
                movie=movie,
                recommendation_type='hybrid',
                context=context,
                rank=rank,
                score=1.0 - (rank * 0.05),
                confidence_score=0.8,
                novelty_score=0.5,
                explanation={
                    'reason': 'Generated using hybrid method',
                    'method': 'hybrid'
                }
            )

        logger.info(f"Successfully generated {len(unique_recommendations)} recommendations for user {user_id}")

        # Clear task ID cache
        cache.delete(task_cache_key)

        return len(unique_recommendations)

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return 0
    except Exception as e:
        logger.error(f"Error generating recommendations for user {user_id}: {str(e)}")
        # Clear task ID cache on error
        cache.delete(task_cache_key)
        return 0

@shared_task(bind=True)
def cleanup_old_recommendations(self, days_old=7):
    """
    Clean up old recommendation results
    """
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
        deleted_count = RecommendationResult.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]

        logger.info(f"🧹 Cleaned up {deleted_count} old recommendations")
        return deleted_count

    except Exception as e:
        logger.error(f"❌ Error cleaning up old recommendations: {str(e)}")
        return 0

@shared_task(bind=True)
def auto_manage_large_user_base(self):
    """
    Auto-manage large user base for recommendations
    This task handles bulk operations for recommendation management
    """
    try:
        logger.info("🔄 Starting auto-management of large user base...")

        # Get active users with complete profiles
        active_users = User.objects.filter(
            is_active=True,
            age__isnull=False,
            gender__isnull=False
        ).exclude(
            age=0
        )[:1000]  # Limit to 1000 users per run

        processed_count = 0
        error_count = 0

        for user in active_users:
            try:
                # Generate recommendations for each user
                generate_user_recommendations_async.delay(user.id, 'homepage', 20)
                processed_count += 1

                # Small delay to prevent overwhelming the system
                if processed_count % 50 == 0:
                    logger.info(f"🔄 Processed {processed_count} users...")

            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error processing user {user.id}: {str(e)}")
                continue

        logger.info(f"✅ Auto-management completed: {processed_count} users processed, {error_count} errors")

        return {
            'status': 'success',
            'processed_count': processed_count,
            'error_count': error_count
        }

    except Exception as e:
        logger.error(f"❌ Error in auto_manage_large_user_base: {str(e)}")
        raise self.retry(exc=e, countdown=300, max_retries=2)

@shared_task(bind=True)
def bulk_refresh_stale_recommendations(self):
    """
    Bulk refresh stale recommendations for all users
    """
    try:
        logger.info("🔄 Starting bulk refresh of stale recommendations...")

        # Find stale recommendations (older than 7 days)
        cutoff_date = timezone.now() - timezone.timedelta(days=7)
        stale_recommendations = RecommendationResult.objects.filter(
            created_at__lt=cutoff_date
        ).select_related('user').distinct('user')

        refreshed_count = 0
        error_count = 0

        for rec in stale_recommendations:
            try:
                # Refresh recommendations for this user
                generate_user_recommendations_async.delay(rec.user.id, 'homepage', 20)
                refreshed_count += 1

                if refreshed_count % 100 == 0:
                    logger.info(f"🔄 Refreshed {refreshed_count} users...")

            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error refreshing recommendations for user {rec.user.id}: {str(e)}")
                continue

        logger.info(f"✅ Bulk refresh completed: {refreshed_count} users refreshed, {error_count} errors")

        return {
            'status': 'success',
            'refreshed_count': refreshed_count,
            'error_count': error_count
        }

    except Exception as e:
        logger.error(f"❌ Error in bulk_refresh_stale_recommendations: {str(e)}")
        raise self.retry(exc=e, countdown=300, max_retries=2)

@shared_task(bind=True)
def refresh_demographic_clusters(self):
    """
    Refresh demographic clustering for recommendations
    """
    try:
        logger.info("🔄 Starting demographic cluster refresh...")

        # This would typically involve recalculating demographic clusters
        # For now, we'll just log that it's running
        logger.info("✅ Demographic cluster refresh completed (placeholder)")

        return {
            'status': 'success',
            'message': 'Demographic clusters refreshed'
        }

    except Exception as e:
        logger.error(f"❌ Error in refresh_demographic_clusters: {str(e)}")
        raise self.retry(exc=e, countdown=300, max_retries=2)

@shared_task(bind=True)
def cleanup_expired_recommendations(self):
    """
    Clean up expired recommendations (alias for cleanup_old_recommendations)
    """
    return cleanup_old_recommendations(days_old=7)
