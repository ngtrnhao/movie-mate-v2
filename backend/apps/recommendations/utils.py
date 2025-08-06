"""
Utilities for recommendation system including task locking to prevent race conditions
"""
import time
import logging
from functools import wraps
from django.core.cache import cache

logger = logging.getLogger(__name__)

class RecommendationTaskLock:
    """
    Task-level locking for recommendation generation to prevent race conditions
    """

    @staticmethod
    def get_lock_key(user_id: int, context: str = 'homepage') -> str:
        """Generate cache key for recommendation task lock"""
        return f"rec_task_lock:user_{user_id}:context_{context}"

    @staticmethod
    def acquire_lock(user_id: int, context: str = 'homepage', timeout: int = 300) -> bool:
        """
        Acquire lock for recommendation generation task
        Returns True if lock acquired, False if already locked
        """
        lock_key = RecommendationTaskLock.get_lock_key(user_id, context)

        # Try to acquire lock with timeout using cache.add() which is atomic
        acquired = cache.add(lock_key, True, timeout=timeout)

        if acquired:
            logger.info(f"Acquired recommendation task lock for user {user_id}, context {context}")
        else:
            logger.warning(f"Failed to acquire recommendation task lock for user {user_id}, context {context} - already locked")

        return acquired

    @staticmethod
    def release_lock(user_id: int, context: str = 'homepage'):
        """Release lock for recommendation generation task"""
        lock_key = RecommendationTaskLock.get_lock_key(user_id, context)
        cache.delete(lock_key)
        logger.info(f"Released recommendation task lock for user {user_id}, context {context}")

    @staticmethod
    def is_locked(user_id: int, context: str = 'homepage') -> bool:
        """Check if user recommendation generation is currently locked"""
        lock_key = RecommendationTaskLock.get_lock_key(user_id, context)
        return cache.get(lock_key) is not None

    @staticmethod
    def extend_lock(user_id: int, context: str = 'homepage', timeout: int = 300):
        """Extend existing lock timeout"""
        lock_key = RecommendationTaskLock.get_lock_key(user_id, context)
        if cache.get(lock_key):
            cache.set(lock_key, True, timeout=timeout)
            logger.debug(f"Extended recommendation task lock for user {user_id}, context {context}")


def with_recommendation_task_lock(timeout=300):
    """
    Decorator to ensure recommendation task is locked during execution

    Usage:
    @with_recommendation_task_lock(timeout=300)
    def some_recommendation_task(user_id):
        # This will be locked per user
        pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user_id from function arguments
            user_id = None
            context = 'homepage'

            # Try to find user_id in different argument positions
            if args:
                # First argument might be self for bound methods
                first_arg = args[0]
                if hasattr(first_arg, 'request') and hasattr(first_arg.request, 'id'):
                    # For Celery tasks with self as first arg
                    if len(args) > 1:
                        user_id = args[1]
                elif isinstance(first_arg, int):
                    # Direct user_id as first argument
                    user_id = first_arg
                elif len(args) > 1 and isinstance(args[1], int):
                    # user_id as second argument
                    user_id = args[1]

            # Try to get from kwargs
            if user_id is None:
                user_id = kwargs.get('user_id')

            # Get context
            context = kwargs.get('context', 'homepage')

            if user_id is None:
                logger.warning(f"Could not extract user_id from {func.__name__} arguments - skipping lock")
                return func(*args, **kwargs)

            # Try to acquire lock
            if not RecommendationTaskLock.acquire_lock(user_id, context, timeout):
                logger.warning(f"Skipping {func.__name__} for user {user_id} - already generating recommendations")
                return {'success': False, 'error': 'Already generating recommendations', 'skipped': True}

            try:
                # Execute the original function
                result = func(*args, **kwargs)
                return result
            finally:
                # Always release lock
                RecommendationTaskLock.release_lock(user_id, context)

        return wrapper
    return decorator


def safe_recommendation_generation(user_id: int, context: str = 'homepage'):
    """
    Context manager for safe recommendation generation with automatic locking

    Usage:
    with safe_recommendation_generation(user_id, context):
        # Generate recommendations safely
        pass
    """
    class SafeRecommendationContext:
        def __init__(self, user_id, context):
            self.user_id = user_id
            self.context = context
            self.acquired = False

        def __enter__(self):
            self.acquired = RecommendationTaskLock.acquire_lock(self.user_id, self.context)
            if not self.acquired:
                raise RuntimeError(f"Could not acquire recommendation lock for user {self.user_id}")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.acquired:
                RecommendationTaskLock.release_lock(self.user_id, self.context)

    return SafeRecommendationContext(user_id, context)


def ensure_single_recommendation_set(user_id: int, context: str = 'homepage'):
    """
    Utility to ensure a user has only one set of recommendations
    Returns True if cleanup was needed, False if already clean
    """
    from apps.recommendations.models import RecommendationResult
    from django.db.models import Count

    # Find duplicate movies for this user/context
    user_recs = RecommendationResult.objects.filter(
        user_id=user_id,
        context=context
    )

    duplicates = user_recs.values('movie_id').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    if not duplicates.exists():
        return False  # No cleanup needed

    logger.info(f"Cleaning up {duplicates.count()} duplicate movies for user {user_id}")

    # For each duplicate movie, keep the most recent recommendation
    cleaned_count = 0
    for dup in duplicates:
        movie_id = dup['movie_id']
        movie_recs = user_recs.filter(movie_id=movie_id).order_by('-created_at')

        # Keep the most recent, delete others
        keep_rec = movie_recs.first()
        old_recs = movie_recs.exclude(id=keep_rec.id)

        count = old_recs.count()
        old_recs.delete()
        cleaned_count += count

    logger.info(f"Cleaned up {cleaned_count} duplicate recommendations for user {user_id}")
    return True  # Cleanup was performed
