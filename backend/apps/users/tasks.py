from celery import shared_task
from django.contrib.auth import get_user_model
from apps.recommendations.services import (
    CollaborativeFilteringService,
    EnhancedDemographicFilteringService,
    HybridRecommendationService
)
from apps.recommendations.models import RecommendationResult, UserPreference
from apps.recommendations.utils import with_recommendation_task_lock, ensure_single_recommendation_set
from apps.movies.models import Movie
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
@with_recommendation_task_lock(timeout=300)
def generate_hybrid_recommendations_for_user(self, user_id, action='initial'):
    """
    Generate hybrid recommendations for user (replaces both initial and regenerate)
    Uses hybrid algorithm which automatically selects best method based on user data
    """
    try:
        user = User.objects.get(id=user_id)

        # Clear existing recommendations for clean slate
        if action == 'update':
            RecommendationResult.objects.filter(
                user=user,
                context='homepage'
            ).delete()
            logger.info(f"Cleared existing recommendations for user {user_id} ({action})")

        # Initialize hybrid service (automatically selects best algorithm)
        hybrid_service = HybridRecommendationService()

        # Generate hybrid recommendations (algorithm auto-selected internally)
        logger.info(f"Generating hybrid recommendations for user {user_id} ({action})")
        try:
            recommendations = hybrid_service.generate_hybrid_recommendations(
                user, limit=20, context='homepage'
            )
            rec_type = 'hybrid'
            logger.info(f"Hybrid service generated {len(recommendations)} recommendations for user {user_id}")

            # Check if we got full recommendation objects or just movies
            if recommendations and isinstance(recommendations[0], dict):
                # Full recommendation data with metadata
                use_full_data = True
            else:
                # Just movie objects (fallback case)
                use_full_data = False
                movies = recommendations

        except Exception as e:
            logger.warning(f"Hybrid recommendations failed for user {user_id}: {str(e)}, falling back to popular movies")
            # Fallback to popular movies
            movies = Movie.objects.filter(
                cached_tmdb_rating__gte=7.0,
                cached_tmdb_votes__gte=1000
            ).order_by('-cached_tmdb_rating')[:20]
            rec_type = 'hybrid'  # Still label as hybrid for consistency
            use_full_data = False

        # Store recommendations
        recommendations_created = 0

        if use_full_data:
            # Use full recommendation data from hybrid service
            for rank, rec_data in enumerate(recommendations, 1):
                rec_result, created = RecommendationResult.objects.get_or_create(
                    user=user,
                    movie=rec_data['movie'],
                    recommendation_type=rec_type,
                    context='homepage',
                    defaults={
                        'rank': rank,
                        'score': rec_data.get('score', 1.0 - (rank * 0.05)),
                        'predicted_rating': rec_data.get('predicted_rating'),
                        'confidence_score': rec_data.get('confidence', 0.8),
                        'novelty_score': rec_data.get('novelty_score', 0.5),
                        'explanation': rec_data.get('explanation', {
                            'reason': f'Hybrid recommendation ({action})',
                            'method': 'hybrid',
                            'action': action
                        })
                    }
                )
                if created:
                    recommendations_created += 1
        else:
            # Fallback: Use simple movie objects
            for rank, movie in enumerate(movies, 1):
                rec_result, created = RecommendationResult.objects.get_or_create(
                    user=user,
                    movie=movie,
                    recommendation_type=rec_type,
                    context='homepage',
                    defaults={
                        'rank': rank,
                        'score': 1.0 - (rank * 0.05),
                        'confidence_score': 0.6,  # Lower confidence for fallback
                        'novelty_score': 0.5,
                        'explanation': {
                            'reason': f'Hybrid recommendation fallback ({action})',
                            'method': 'hybrid',
                            'action': action,
                            'fallback': True
                        }
                    }
                )
                if created:
                    recommendations_created += 1

        logger.info(f"Created {recommendations_created} hybrid recommendations for user {user_id} ({action})")
        return {'success': True, 'recommendations_created': recommendations_created, 'action': action, 'method': 'hybrid'}

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error generating hybrid recommendations for user {user_id}: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        return {'success': False, 'error': str(e), 'action': action}


# Legacy task aliases for backward compatibility (redirect to hybrid)
@shared_task(bind=True, max_retries=3)
def generate_initial_recommendations_for_user(self, user_id):
    """Legacy alias - redirects to hybrid recommendations"""
    return generate_hybrid_recommendations_for_user.delay(user_id, action='initial')

@shared_task(bind=True, max_retries=3)
def regenerate_recommendations_for_user(self, user_id):
    """Legacy alias - redirects to hybrid recommendations"""
    return generate_hybrid_recommendations_for_user.delay(user_id, action='update')


@shared_task
def update_user_similarities_batch():
    """
    Background task to update user similarities in batches
    """
    try:
        collaborative_service = CollaborativeFilteringService()

        # Get users with ratings
        users_with_ratings = User.objects.filter(
            reviews__review_type='USER',
            reviews__rating__isnull=False
        ).distinct()

        batch_size = 50
        similarities_updated = 0

        for i in range(0, users_with_ratings.count(), batch_size):
            batch_users = users_with_ratings[i:i + batch_size]

            for user in batch_users:
                try:
                    similarities_updated += collaborative_service.update_user_similarities(user)
                except Exception as e:
                    logger.error(f"Error updating similarities for user {user.id}: {str(e)}")

        logger.info(f"Updated {similarities_updated} user similarities")
        return {'success': True, 'similarities_updated': similarities_updated}

    except Exception as e:
        logger.error(f"Error in batch similarity update: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def generate_recommendations_for_active_users():
    """
    Generate recommendations for all active users
    """
    try:
        from django.utils import timezone
        from datetime import timedelta

        # Get users who have been active in the last 7 days
        active_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=7)
        )

        hybrid_service = HybridRecommendationService()
        recommendations_generated = 0

        for user in active_users:
            try:
                from apps.recommendations.utils import RecommendationTaskLock

                # Try to acquire lock for this user
                if not RecommendationTaskLock.acquire_lock(user.id, 'homepage', timeout=60):
                    logger.info(f"Skipping user {user.id} - recommendations already being generated")
                    continue

                try:
                    # Check if user needs new recommendations
                    latest_rec = RecommendationResult.objects.filter(
                        user=user,
                        context='homepage'
                    ).order_by('-created_at').first()

                    # Generate new recommendations if none exist or older than 24 hours
                    if not latest_rec or latest_rec.created_at < timezone.now() - timedelta(hours=24):
                        movies = hybrid_service.generate_hybrid_recommendations(
                            user, limit=20, context='homepage'
                        )

                        # Clear old recommendations
                        RecommendationResult.objects.filter(
                            user=user,
                            context='homepage'
                        ).delete()

                        # Store new recommendations
                        for rank, movie in enumerate(movies, 1):
                            RecommendationResult.objects.create(
                                user=user,
                                movie=movie,
                                recommendation_type='hybrid',
                                context='homepage',
                                rank=rank,
                                score=1.0 - (rank * 0.05),
                                confidence_score=0.9,
                                novelty_score=0.5
                            )

                        recommendations_generated += len(movies)

                        # Ensure no duplicates remain
                        ensure_single_recommendation_set(user.id, 'homepage')

                finally:
                    # Always release lock for this user
                    RecommendationTaskLock.release_lock(user.id, 'homepage')

            except Exception as e:
                logger.error(f"Error generating recommendations for user {user.id}: {str(e)}")

        logger.info(f"Generated {recommendations_generated} recommendations for active users")
        return {'success': True, 'recommendations_generated': recommendations_generated}

    except Exception as e:
        logger.error(f"Error in active users recommendation generation: {str(e)}")
        return {'success': False, 'error': str(e)}
