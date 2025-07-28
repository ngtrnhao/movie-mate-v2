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
