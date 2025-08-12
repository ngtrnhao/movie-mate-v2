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
        has_complete_profile = (
            user.age and
            user.gender and
            user.occupation and
            user.location and
            user.user_type
        )

        if not has_complete_profile:
            missing_fields = []
            if not user.age:
                missing_fields.append('age')
            if not user.gender:
                missing_fields.append('gender')
            if not user.occupation:
                missing_fields.append('occupation')
            if not user.location:
                missing_fields.append('location')
            if not user.user_type:
                missing_fields.append('user_type')

            logger.info(f"User {user_id} has incomplete profile - missing: {missing_fields} - skipping recommendation generation")
            return []

        # Clear existing recommendations for this user and context
        RecommendationResult.objects.filter(user=user, context=context).delete()

        # Generate recommendations using hybrid service
        from .services import HybridRecommendationService
        hybrid_service = HybridRecommendationService()

        # Get recommendations with full metadata from hybrid service
        recommendations = hybrid_service.generate_hybrid_recommendations(user, limit, context)

        # Get detailed recommendations from cache service (hybrid service stores them)
        from .services import RecommendationCacheService
        detailed_recommendations = RecommendationCacheService.get_cached_recommendations(
            user, 'hybrid', context, limit
        )

        if detailed_recommendations:
            # Store recommendations with proper metadata from hybrid algorithm
            for rank, rec_data in enumerate(detailed_recommendations, 1):
                RecommendationResult.objects.create(
                    user=user,
                    movie=rec_data['movie'],
                    recommendation_type='hybrid',
                    context=context,
                    rank=rank,
                    score=rec_data.get('score', 1.0 - (rank * 0.05)),
                    predicted_rating=rec_data.get('predicted_rating'),
                    confidence_score=rec_data.get('confidence', 0.8),
                    novelty_score=rec_data.get('novelty_score', 0.5),
                    explanation=rec_data.get('explanation', {
                        'reason': 'Generated using hybrid method',
                        'method': 'hybrid'
                    })
                )
        else:
            # Fallback: Store basic recommendations if detailed data not available
            seen_movie_ids = set()
            unique_recommendations = []
            for movie in recommendations:
                if movie.id not in seen_movie_ids:
                    seen_movie_ids.add(movie.id)
                    unique_recommendations.append(movie)

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
                        'reason': 'Generated using hybrid method (fallback)',
                        'method': 'hybrid'
                    }
                )

        if detailed_recommendations:
            logger.info(f"Successfully generated {len(detailed_recommendations)} recommendations with full metadata for user {user_id}")
        else:
            logger.info(f"Successfully generated {len(unique_recommendations)} recommendations with fallback metadata for user {user_id}")

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
def generate_collaborative_recommendations_async(self, user_id: int, context: str = 'homepage', limit: int = 20):
    """
    Generate collaborative filtering recommendations asynchronously
    """
    from django.core.cache import cache
    from django.contrib.auth import get_user_model
    from .services import CollaborativeFilteringService

    User = get_user_model()

    try:
        # Cache task ID for this user/context
        task_cache_key = f"cf_task:{user_id}:{context}"
        cache.set(task_cache_key, self.request.id, 300)  # Cache for 5 minutes

        logger.info(f"Starting background collaborative filtering task {self.request.id} for user {user_id}")

        # Get user
        user = User.objects.get(id=user_id)

        # Lưu recommendations cũ để làm fallback cache
        old_recommendations = list(RecommendationResult.objects.filter(
            user=user,
            recommendation_type='collaborative',
            context=context
        ).select_related('movie').order_by('rank')[:20])

        # Generate collaborative recommendations via service (service tự lưu RecommendationResult với đầy đủ metadata)
        cf_service = CollaborativeFilteringService()
        movies = cf_service.generate_collaborative_recommendations(user, limit, context)
        logger.info(f"CF service returned {len(movies)} movies; results saved via cache service")

        # Chỉ xóa recommendations cũ sau khi đã lưu recommendations mới thành công
        if movies:
            # Xóa recommendations cũ
            RecommendationResult.objects.filter(
                user=user,
                recommendation_type='collaborative',
                context=context
            ).exclude(
                movie__in=[movie for movie in movies[:limit]]
            ).delete()
            logger.info(f"✅ Đã xóa recommendations cũ và lưu {len(movies)} recommendations mới cho user {user_id}")
        else:
            # Nếu không tạo được recommendations mới, giữ lại recommendations cũ
            logger.warning(f"⚠️ Không tạo được recommendations mới, giữ lại {len(old_recommendations)} recommendations cũ cho user {user_id}")

        # Clear task cache
        cache.delete(task_cache_key)
        logger.info(f"✅ Background collaborative filtering completed for user {user_id}")
        return len(movies)

    except Exception as e:
        logger.error(f"❌ Error in background collaborative filtering for user {user_id}: {str(e)}")
        return 0

@shared_task(bind=True)
def generate_hybrid_recommendations_async(self, user_id: int, context: str = 'homepage', limit: int = 20):
    """
    Generate hybrid recommendations asynchronously
    """
    from django.core.cache import cache
    from django.contrib.auth import get_user_model
    from .services import HybridRecommendationService

    User = get_user_model()

    try:
        # Cache task ID for this user/context
        task_cache_key = f"hybrid_task:{user_id}:{context}"
        cache.set(task_cache_key, self.request.id, 300)  # Cache for 5 minutes

        logger.info(f"Starting background hybrid recommendations task {self.request.id} for user {user_id}")

        # Get user
        user = User.objects.get(id=user_id)

        # Lưu recommendations cũ để làm fallback cache
        old_recommendations = list(RecommendationResult.objects.filter(
            user=user,
            recommendation_type='hybrid',
            context=context
        ).select_related('movie').order_by('rank')[:20])

        # Generate hybrid recommendations via service (service tự lưu RecommendationResult với đầy đủ metadata)
        hybrid_service = HybridRecommendationService()
        movies = hybrid_service.generate_hybrid_recommendations(user, limit, context)
        logger.info(f"Hybrid service returned {len(movies)} movies; results saved via cache service")

        # Chỉ xóa recommendations cũ sau khi đã lưu recommendations mới thành công
        if movies:
            # Xóa recommendations cũ
            RecommendationResult.objects.filter(
                user=user,
                recommendation_type='hybrid',
                context=context
            ).exclude(
                movie__in=[movie for movie in movies[:limit]]
            ).delete()
            logger.info(f"✅ Đã xóa recommendations cũ và lưu {len(movies)} hybrid recommendations mới cho user {user_id}")
        else:
            # Nếu không tạo được recommendations mới, giữ lại recommendations cũ
            logger.warning(f"⚠️ Không tạo được hybrid recommendations mới, giữ lại {len(old_recommendations)} recommendations cũ cho user {user_id}")

        # Clear task cache
        cache.delete(task_cache_key)
        logger.info(f"✅ Background hybrid recommendations completed for user {user_id}")
        return len(movies)

    except Exception as e:
        logger.error(f"❌ Error in background hybrid recommendations for user {user_id}: {str(e)}")
        return 0

@shared_task(bind=True)
def generate_demographic_recommendations_async(self, user_id: int, context: str = 'homepage', limit: int = 20):
    """
    Generate demographic recommendations asynchronously
    """
    from django.core.cache import cache
    from django.contrib.auth import get_user_model
    from .services import EnhancedDemographicFilteringService

    User = get_user_model()

    try:
        # Cache task ID for this user/context
        task_cache_key = f"demo_task:{user_id}:{context}"
        cache.set(task_cache_key, self.request.id, 300)  # Cache for 5 minutes

        logger.info(f"Starting background demographic recommendations task {self.request.id} for user {user_id}")

        # Get user
        user = User.objects.get(id=user_id)

        # Check if user has complete demographic data
        has_complete_demographic = (
            user.age and
            user.gender and
            user.occupation and
            user.location and
            user.user_type
        )

        if not has_complete_demographic:
            logger.warning(f"User {user_id} has incomplete demographic data - skipping demographic recommendations")
            return 0

        # Clear existing demographic recommendations for this user and context
        RecommendationResult.objects.filter(
            user=user,
            recommendation_type='demographic',
            context=context
        ).delete()

        # Generate enhanced demographic recommendations and let the service
        # persist full metadata (predicted_rating, confidence, novelty, explanation)
        demo_service = EnhancedDemographicFilteringService()
        recommendations = demo_service.generate_enhanced_demographic_recommendations(
            user, limit, context, store=True
        )

        # NOTE: Do not overwrite detailed metadata by re-inserting minimal rows here.
        # The service already stored enhanced recommendations in RecommendationResult.

        logger.info(f"✅ Background demographic recommendations completed for user {user_id}")
        return len(recommendations)

    except Exception as e:
        logger.error(f"❌ Error in background demographic recommendations for user {user_id}: {str(e)}")
        return 0

@shared_task(bind=True)
def refresh_all_recommendations_async(self, user_id: int, context: str = 'homepage', limit: int = 20):
    """
    Refresh all types of recommendations asynchronously
    """
    from django.core.cache import cache
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        # Cache task ID for this user/context
        task_cache_key = f"refresh_all_task:{user_id}:{context}"
        cache.set(task_cache_key, self.request.id, 600)  # Cache for 10 minutes

        logger.info(f"Starting background refresh all recommendations task {self.request.id} for user {user_id}")

        # Get user
        user = User.objects.get(id=user_id)

        # Generate all types of recommendations in parallel
        tasks = [
            generate_collaborative_recommendations_async.delay(user_id, context, limit),
            generate_hybrid_recommendations_async.delay(user_id, context, limit),
            generate_demographic_recommendations_async.delay(user_id, context, limit)
        ]

        # Wait for all tasks to complete
        results = []
        for task in tasks:
            try:
                result = task.get(timeout=300)  # 5 minutes timeout per task
                results.append(result)
            except Exception as e:
                logger.error(f"Task failed: {str(e)}")
                results.append(0)

        total_recommendations = sum(results)
        logger.info(f"✅ Background refresh all recommendations completed for user {user_id}. Total: {total_recommendations}")

        return total_recommendations

    except Exception as e:
        logger.error(f"❌ Error in background refresh all recommendations for user {user_id}: {str(e)}")
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
def batch_generate_collaborative_recommendations(self, user_ids: list = None, context: str = 'homepage', limit: int = 20):
    """
    Generate collaborative filtering recommendations for multiple users in batch
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        # Get users to process
        if user_ids is None:
            # Get active users with stale recommendations
            cutoff_date = timezone.now() - timedelta(hours=24)
            users = User.objects.filter(
                recommendationresult__created_at__lt=cutoff_date,
                recommendationresult__recommendation_type='collaborative'
            ).distinct()[:50]  # Limit to 50 users per batch
        else:
            users = User.objects.filter(id__in=user_ids)

        logger.info(f"🔄 Starting batch collaborative filtering for {users.count()} users")

        total_recommendations = 0
        for user in users:
            try:
                result = generate_collaborative_recommendations_async.delay(user.id, context, limit)
                total_recommendations += result.get(timeout=60) or 0
            except Exception as e:
                logger.error(f"Error processing user {user.id}: {str(e)}")
                continue

        logger.info(f"✅ Batch collaborative filtering completed. Total recommendations: {total_recommendations}")
        return total_recommendations

    except Exception as e:
        logger.error(f"❌ Error in batch collaborative filtering: {str(e)}")
        return 0

@shared_task(bind=True)
def batch_generate_hybrid_recommendations(self, user_ids: list = None, context: str = 'homepage', limit: int = 20):
    """
    Generate hybrid recommendations for multiple users in batch
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        # Get users to process
        if user_ids is None:
            # Get active users with stale recommendations
            cutoff_date = timezone.now() - timedelta(hours=24)
            users = User.objects.filter(
                recommendationresult__created_at__lt=cutoff_date,
                recommendationresult__recommendation_type='hybrid'
            ).distinct()[:50]  # Limit to 50 users per batch
        else:
            users = User.objects.filter(id__in=user_ids)

        logger.info(f"🔄 Starting batch hybrid recommendations for {users.count()} users")

        total_recommendations = 0
        for user in users:
            try:
                result = generate_hybrid_recommendations_async.delay(user.id, context, limit)
                total_recommendations += result.get(timeout=60) or 0
            except Exception as e:
                logger.error(f"Error processing user {user.id}: {str(e)}")
                continue

        logger.info(f"✅ Batch hybrid recommendations completed. Total recommendations: {total_recommendations}")
        return total_recommendations

    except Exception as e:
        logger.error(f"❌ Error in batch hybrid recommendations: {str(e)}")
        return 0

@shared_task(bind=True)
def batch_generate_demographic_recommendations(self, user_ids: list = None, context: str = 'homepage', limit: int = 20):
    """
    Generate demographic recommendations for multiple users in batch
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        # Get users to process
        if user_ids is None:
            # Get active users with stale recommendations
            cutoff_date = timezone.now() - timedelta(hours=24)
            users = User.objects.filter(
                recommendationresult__created_at__lt=cutoff_date,
                recommendationresult__recommendation_type='demographic'
            ).distinct()[:50]  # Limit to 50 users per batch
        else:
            users = User.objects.filter(id__in=user_ids)

        logger.info(f"🔄 Starting batch demographic recommendations for {users.count()} users")

        total_recommendations = 0
        for user in users:
            try:
                result = generate_demographic_recommendations_async.delay(user.id, context, limit)
                total_recommendations += result.get(timeout=60) or 0
            except Exception as e:
                logger.error(f"Error processing user {user.id}: {str(e)}")
                continue

        logger.info(f"✅ Batch demographic recommendations completed. Total recommendations: {total_recommendations}")
        return total_recommendations

    except Exception as e:
        logger.error(f"❌ Error in batch demographic recommendations: {str(e)}")
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

# @shared_task(bind=True)
# def refresh_demographic_clusters(self):
#     """
#     Refresh demographic clustering for recommendations
#     """
#     try:
#         logger.info("🔄 Starting demographic cluster refresh...")

#         from apps.recommendations.services import EnhancedDemographicFilteringService

#         # Initialize service
#         demographic_service = EnhancedDemographicFilteringService()

#         # Get current statistics
#         from apps.users.models import User
#         from apps.recommendations.models import DemographicCluster

#         total_users = User.objects.count()
#         users_with_demographics = User.objects.filter(
#             age__isnull=False,
#             gender__isnull=False
#         ).count()
#         current_clusters = DemographicCluster.objects.count()

#         logger.info(f"📊 Current statistics: {total_users} users, {users_with_demographics} with demographics, {current_clusters} clusters")

#         # Create K-means clusters
#         logger.info("🤖 Creating K-means clusters...")
#         demographic_service.create_kmeans_clusters(recalculate=True, n_clusters=8)

#         # Get updated statistics
#         new_clusters = DemographicCluster.objects.count()
#         kmeans_clusters = DemographicCluster.objects.filter(cluster_id__startswith='kmeans_').count()

#         logger.info(f"✅ Created {kmeans_clusters} K-means clusters (total: {new_clusters})")

#         return {
#             'status': 'success',
#             'message': f'Demographic clusters refreshed: {kmeans_clusters} K-means clusters created',
#             'total_clusters': new_clusters,
#             'kmeans_clusters': kmeans_clusters,
#             'users_processed': users_with_demographics
#         }

#     except Exception as e:
#         logger.error(f"❌ Error in refresh_demographic_clusters: {str(e)}")
#         raise self.retry(exc=e, countdown=300, max_retries=2)

@shared_task(bind=True)
def cleanup_expired_recommendations(self):
    """
    Clean up expired recommendations (alias for cleanup_old_recommendations)
    """
    return cleanup_old_recommendations(days_old=7)

@shared_task(bind=True)
def detect_and_generate_missing_cf_recommendations(self):
    """
    Detect users without CF recommendations và trigger generation
    Automatically finds users missing pure CF recommendations and generates them
    """
    try:
        logger.info("🔍 Starting detection of users missing CF recommendations...")

        from django.db.models import Count, Q
        from datetime import timedelta
        from django.utils import timezone

        # Find users WITHOUT any CF recommendations
        users_without_cf = User.objects.filter(
            is_active=True,
            age__isnull=False,
            gender__isnull=False
        ).exclude(
            recommendations__recommendation_type='collaborative',
            recommendations__context='homepage'
        ).distinct()

        # Find users with OLD CF recommendations (>7 days)
        cutoff_date = timezone.now() - timedelta(days=7)
        users_with_stale_cf = User.objects.filter(
            recommendations__recommendation_type='collaborative',
            recommendations__context='homepage',
            recommendations__created_at__lt=cutoff_date
        ).distinct()

        # Combine both groups
        users_needing_cf = users_without_cf.union(users_with_stale_cf)[:200]  # Limit

        logger.info(f"👥 Found {len(users_needing_cf)} users needing CF recommendations")
        logger.info(f"   - {users_without_cf.count()} users without CF recs")
        logger.info(f"   - {users_with_stale_cf.count()} users with stale CF recs")

        # Trigger CF generation for each user
        triggered_count = 0
        for user in users_needing_cf:
            try:
                # Check if user has enough ratings for CF
                from apps.movies.models import MovieReview
                rating_count = MovieReview.objects.filter(
                    user=user,
                    review_type='USER'
                ).count()

                if rating_count >= 10:  # Minimum ratings for CF
                    generate_collaborative_recommendations_async.delay(
                        user.id, 'homepage', 20
                    )
                    triggered_count += 1
                else:
                    logger.debug(f"User {user.id} has only {rating_count} ratings, skipping CF")

            except Exception as e:
                logger.error(f"Error triggering CF for user {user.id}: {str(e)}")
                continue

        logger.info(f"✅ CF generation triggered for {triggered_count} users")

        return {
            'status': 'success',
            'users_found': len(users_needing_cf),
            'cf_triggered': triggered_count
        }

    except Exception as e:
        logger.error(f"❌ Error in detect_and_generate_missing_cf_recommendations: {str(e)}")
        raise self.retry(exc=e, countdown=300, max_retries=2)

@shared_task(bind=True)
def smart_cf_recommendation_prioritization(self):
    """
    Intelligent prioritization for CF recommendation generation
    Prioritizes active users and those with recent activity for CF recommendations
    """
    try:
        logger.info("🎯 Starting smart CF prioritization...")

        from django.db.models import Count
        from datetime import timedelta
        from django.utils import timezone

        # Priority 1: Active users without ANY recommendations
        priority_1_users = User.objects.filter(
            is_active=True,
            last_login__gte=timezone.now() - timedelta(days=7)
        ).exclude(
            recommendations__context='homepage'
        ).annotate(
            rating_count=Count('moviereview')
        ).filter(
            rating_count__gte=20  # High-activity users
        ).order_by('-rating_count')[:50]

        # Priority 2: Users with recent activity but old CF recs
        priority_2_users = User.objects.filter(
            is_active=True,
            last_login__gte=timezone.now() - timedelta(days=3),
            recommendations__recommendation_type='collaborative',
            recommendations__created_at__lt=timezone.now() - timedelta(days=14)
        ).annotate(
            rating_count=Count('moviereview')
        ).filter(
            rating_count__gte=15
        ).order_by('-last_login')[:30]

        # Process Priority 1 first
        for user in priority_1_users:
            generate_collaborative_recommendations_async.apply_async(
                args=[user.id, 'homepage', 20],
                priority=9,  # High priority
                queue='high_priority'
            )

        # Process Priority 2
        for user in priority_2_users:
            generate_collaborative_recommendations_async.apply_async(
                args=[user.id, 'homepage', 20],
                priority=5,  # Medium priority
                queue='normal'
            )

        logger.info(f"✅ Smart prioritization completed: {len(priority_1_users)} P1, {len(priority_2_users)} P2")

        return {
            'priority_1_count': len(priority_1_users),
            'priority_2_count': len(priority_2_users)
        }

    except Exception as e:
        logger.error(f"❌ Error in smart_cf_recommendation_prioritization: {str(e)}")
        raise self.retry(exc=e, countdown=300, max_retries=2)

@shared_task(bind=True)
def precompute_user_similarities_batch(self):
    """
    Precompute similarities cho active users để improve CF performance
    Background task to precompute user similarities for faster CF recommendations
    """
    try:
        logger.info("🔄 Starting similarity precomputation for active users...")

        from django.db.models import Count
        from datetime import timedelta
        from django.utils import timezone
        from apps.recommendations.models import UserSimilarity
        from apps.recommendations.services import CollaborativeFilteringService
        from django.db.models import Q

        # Get top 500 most active users
        active_users = User.objects.annotate(
            rating_count=Count('moviereview')
        ).filter(
            rating_count__gte=20,
            last_login__gte=timezone.now() - timedelta(days=30)
        ).order_by('-rating_count')[:500]

        logger.info(f"🔄 Starting similarity precomputation for {len(active_users)} users")

        # Compute similarities for active users only
        cf_service = CollaborativeFilteringService()
        similarities_created = 0

        for i, user in enumerate(active_users[:100], 1):  # Limit to 100 users per run
            try:
                # Check if similarities already exist
                existing_count = UserSimilarity.objects.filter(
                    Q(user1=user) | Q(user2=user)
                ).count()

                if existing_count < 10:  # Need more similarities
                    similar_users = cf_service.find_similar_users(user, limit=50)

                    similarities_to_create = []
                    for similar_user, similarity_score in similar_users:
                        similarities_to_create.append(UserSimilarity(
                            user1=user,
                            user2=similar_user,
                            similarity_score=similarity_score,
                            similarity_type='collaborative'
                        ))

                    if similarities_to_create:
                        UserSimilarity.objects.bulk_create(
                            similarities_to_create,
                            ignore_conflicts=True
                        )
                        similarities_created += len(similarities_to_create)

                if i % 10 == 0:
                    logger.info(f"🔄 Processed {i}/100 users, created {similarities_created} similarities")

            except Exception as e:
                logger.error(f"Error processing user {user.id}: {str(e)}")
                continue

        logger.info(f"✅ Similarity precomputation completed: {similarities_created} similarities created")
        return similarities_created

    except Exception as e:
        logger.error(f"❌ Error in precompute_user_similarities_batch: {str(e)}")
        raise self.retry(exc=e, countdown=300, max_retries=2)

@shared_task(bind=True)
def monitor_cf_system_health(self):
    """
    Monitor và báo cáo health của CF recommendation system
    Health monitoring task for CF system performance and coverage
    """
    try:
        logger.info("📊 Starting CF system health monitoring...")

        from apps.recommendations.models import RecommendationResult, UserSimilarity
        from django.db.models import Count
        from datetime import timedelta
        from django.utils import timezone

        # Basic stats
        total_users = User.objects.count()
        active_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=7)
        ).count()

        # CF Coverage stats
        cf_users = RecommendationResult.objects.filter(
            recommendation_type='collaborative'
        ).values_list('user_id', flat=True).distinct().count()

        recent_cf = RecommendationResult.objects.filter(
            recommendation_type='collaborative',
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()

        # Similarity stats
        total_similarities = UserSimilarity.objects.count()
        recent_similarities = UserSimilarity.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()

        # Calculate coverage percentages
        cf_coverage = (cf_users / total_users * 100) if total_users > 0 else 0
        active_cf_coverage = (cf_users / active_users * 100) if active_users > 0 else 0

        health_report = {
            'timestamp': timezone.now().isoformat(),
            'total_users': total_users,
            'active_users_7d': active_users,
            'cf_coverage_users': cf_users,
            'cf_coverage_percentage': round(cf_coverage, 2),
            'active_cf_coverage_percentage': round(active_cf_coverage, 2),
            'recent_cf_recommendations_24h': recent_cf,
            'total_similarities': total_similarities,
            'recent_similarities_7d': recent_similarities,
            'status': 'healthy' if cf_coverage > 50 else 'needs_attention'
        }

        logger.info(f"📊 CF System Health Report:")
        logger.info(f"   - Total users: {total_users}")
        logger.info(f"   - Active users (7d): {active_users}")
        logger.info(f"   - CF coverage: {cf_users}/{total_users} ({cf_coverage:.1f}%)")
        logger.info(f"   - Recent CF recs (24h): {recent_cf}")
        logger.info(f"   - Total similarities: {total_similarities}")
        logger.info(f"   - Status: {health_report['status']}")

        return health_report

    except Exception as e:
        logger.error(f"❌ Error in monitor_cf_system_health: {str(e)}")
        return {'status': 'error', 'error': str(e)}
