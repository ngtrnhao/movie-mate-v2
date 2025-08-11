from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from apps.recommendations.models import UserPreference, RecommendationResult
from apps.movies.models import Movie
from apps.recommendations.services import EnhancedDemographicFilteringService
from apps.recommendations.utils import RecommendationTaskLock
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def setup_user_recommendation_profile(sender, instance, created, **kwargs):
    """
    Setup user recommendation profile ONLY when user completes profile with demographic data
    Registration does NOTHING - wait for complete demographic profile
    """
    # Skip entirely for new user registration
    if created:
        logger.info(f"User {instance.id} registered - no setup until profile completion")
        return

    # Only proceed if user has COMPLETE demographic data
    has_complete_demographic_data = (
        instance.age is not None and
        instance.gender and instance.gender.strip() and
        instance.occupation and instance.occupation.strip() and
        instance.location and instance.location.strip() and
        instance.user_type and instance.user_type.strip()
    )

    if not has_complete_demographic_data:
        missing_fields = []
        if instance.age is None:
            missing_fields.append('age')
        if not instance.gender or not instance.gender.strip():
            missing_fields.append('gender')
        if not instance.occupation or not instance.occupation.strip():
            missing_fields.append('occupation')
        if not instance.location or not instance.location.strip():
            missing_fields.append('location')
        if not instance.user_type or not instance.user_type.strip():
            missing_fields.append('user_type')

        logger.info(f"User {instance.id} profile incomplete - missing: {missing_fields} - no setup")
        return

    # Check if this is the first time user completes their profile
    user_pref = UserPreference.objects.filter(user=instance).first()
    existing_recs = RecommendationResult.objects.filter(
        user=instance,
        context='homepage'
    ).count()

    # If user already has both UserPreference AND recommendations, skip
    if user_pref and existing_recs > 0:
        logger.info(f"User {instance.id} already has complete setup (UserPreference + {existing_recs} recommendations) - no action needed")
        return

    # If user has UserPreference but no recommendations, this means previous setup was incomplete
    if user_pref and existing_recs == 0:
        logger.info(f"User {instance.id} has UserPreference but no recommendations - completing setup")

    # If no UserPreference, this is truly first time
    if not user_pref:
        logger.info(f"User {instance.id} first time profile completion - full setup")

    logger.info(f"Complete demographic profile update for user {instance.id}: age={instance.age}, gender={instance.gender}, occupation={instance.occupation}")
    logger.info(f"User {instance.id} profile completion - starting recommendation setup")

    try:
        with transaction.atomic():
            # Create UserPreference with demographic data
            user_pref, pref_created = UserPreference.objects.get_or_create(
                user=instance,
                defaults={
                    'novelty_preference': 0.5,
                    'diversity_preference': 0.5,
                    'recency_preference': 0.5,
                    'rating_count': 0,
                    'average_rating': 0.0,
                    'rating_variance': 0.0,
                    'interaction_count': 0,
                    'last_calculated': timezone.now()
                }
            )

            if pref_created:
                logger.info(f"Created UserPreference for user {instance.id} after profile completion")

            # Assign to demographic cluster - prefer K-means over rule-based
            demographic_service = EnhancedDemographicFilteringService()

            # First try to get existing K-means cluster assignment
            existing_cluster = None
            if user_pref.demographic_cluster and user_pref.demographic_cluster.startswith('kmeans_'):
                existing_cluster = demographic_service.get_user_kmeans_cluster(instance)

            # If no existing K-means cluster, try to assign to K-means cluster
            if not existing_cluster:
                cluster = demographic_service.get_user_kmeans_cluster(instance)
                if cluster:
                    user_pref.demographic_cluster = cluster.cluster_id
                    user_pref.save()
                    logger.info(f"Assigned user {instance.id} to K-means cluster {cluster.cluster_id}")
                else:
                    # Only fall back to rule-based if no K-means cluster available
                    cluster = demographic_service.assign_user_to_cluster(instance)
                    if cluster:
                        user_pref.demographic_cluster = cluster.cluster_id
                        user_pref.save()
                        logger.info(f"Assigned user {instance.id} to rule-based cluster {cluster.cluster_id}")
            else:
                # Keep existing K-means cluster assignment
                logger.info(f"User {instance.id} already assigned to K-means cluster {existing_cluster.cluster_id}")

            # Generate initial recommendations
            logger.info(f"Scheduling initial hybrid recommendations for user {instance.id}")

            try:
                from .tasks import generate_hybrid_recommendations_for_user
                generate_hybrid_recommendations_for_user.delay(instance.id, action='initial')
                logger.info(f"Scheduled initial recommendation task for user {instance.id}")
            except Exception as e:
                logger.warning(f"Failed to schedule recommendation task for user {instance.id}: {str(e)}")

                # Fallback ONLY when Celery fails after profile completion
                try:
                    logger.info(f"Creating immediate fallback recommendations for user {instance.id}")
                    popular_movies = Movie.objects.filter(
                        cached_tmdb_rating__gte=7.0,
                        cached_tmdb_votes__gte=1000
                    ).order_by('-cached_tmdb_rating')[:10]

                    for rank, movie in enumerate(popular_movies, 1):
                        predicted_rating = min(5.0, max(1.0, movie.cached_tmdb_rating or 3.0))
                        confidence = min(0.9, 0.4 + (min(movie.cached_tmdb_votes or 0, 10000) / 20000))

                        RecommendationResult.objects.get_or_create(
                            user=instance,
                            movie=movie,
                            recommendation_type='hybrid',
                            context='homepage',
                            defaults={
                                'rank': rank,
                                'score': 1.0 - (rank * 0.05),
                                'predicted_rating': predicted_rating,
                                'confidence_score': confidence,
                                'novelty_score': 0.3,
                                'explanation': {
                                    'reason': 'Profile completion fallback',
                                    'method': 'popular',
                                    'algorithm': 'hybrid',
                                    'fallback': True,
                                    'trigger': 'profile_complete_celery_failed'
                                }
                            }
                        )
                    logger.info(f"Created {len(popular_movies)} fallback recommendations for user {instance.id}")
                except Exception as fallback_error:
                    logger.error(f"Failed to create fallback recommendations for user {instance.id}: {str(fallback_error)}")

    except Exception as e:
        logger.error(f"Error in profile completion setup for user {instance.id}: {str(e)}")



