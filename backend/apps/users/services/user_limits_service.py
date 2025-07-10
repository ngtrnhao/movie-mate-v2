from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from ..models import User, UserFavoriteMovie, Watchlist, UserFavoriteGenre
from apps.movies.models import MovieReview


class UserLimitsService:
    """Service to handle user limits validation and enforcement"""

    # User type limits mapping
    USER_LIMITS = {
        'member': {
            'favorites': 100,
            'lists': 3,
            'reviews_per_day': 20,
            'moods': 5,
        },
        'premium_basic': {
            'favorites': 500,
            'lists': 10,
            'reviews_per_day': 100,
            'moods': 15,
        },
        'premium_standard': {
            'favorites': 2000,
            'lists': 50,
            'reviews_per_day': 200,
            'moods': 30,
        },
        'premium_vip': {
            'favorites': -1,  # unlimited
            'lists': -1,      # unlimited
            'reviews_per_day': -1,  # unlimited
            'moods': -1,      # unlimited
        },
    }

    @classmethod
    def get_user_limits(cls, user):
        """Get limits for a specific user"""
        user_type = user.user_type if hasattr(user, 'user_type') else 'member'
        return cls.USER_LIMITS.get(user_type, cls.USER_LIMITS['member'])

    @classmethod
    def is_unlimited(cls, limit):
        """Check if a limit is unlimited (-1)"""
        return limit == -1

    @classmethod
    def validate_favorites_limit(cls, user):
        """Validate if user can add more favorites"""
        limits = cls.get_user_limits(user)
        max_favorites = limits['favorites']

        if cls.is_unlimited(max_favorites):
            return True, None

        current_count = UserFavoriteMovie.objects.filter(user=user).count()

        if current_count >= max_favorites:
            return False, {
                'error': 'favorites_limit_exceeded',
                'current': current_count,
                'max': max_favorites,
                'message': f'You have reached your limit of {max_favorites} favorite movies. Please upgrade your plan to add more favorites.'
            }

        return True, {
            'current': current_count,
            'max': max_favorites,
            'remaining': max_favorites - current_count
        }

    @classmethod
    def validate_lists_limit(cls, user):
        """Validate if user can create more watchlists"""
        limits = cls.get_user_limits(user)
        max_lists = limits['lists']

        if cls.is_unlimited(max_lists):
            return True, None

        current_count = Watchlist.objects.filter(user=user).count()

        if current_count >= max_lists:
            return False, {
                'error': 'lists_limit_exceeded',
                'current': current_count,
                'max': max_lists,
                'message': f'You have reached your limit of {max_lists} watchlists. Please upgrade your plan to create more lists.'
            }

        return True, {
            'current': current_count,
            'max': max_lists,
            'remaining': max_lists - current_count
        }

    @classmethod
    def validate_reviews_limit(cls, user):
        """Validate if user can write more reviews today"""
        limits = cls.get_user_limits(user)
        max_reviews_per_day = limits['reviews_per_day']

        if cls.is_unlimited(max_reviews_per_day):
            return True, None

        # Count reviews written today
        today = timezone.now().date()
        today_reviews = MovieReview.objects.filter(
            user=user,
            review_type='USER',
            created_at__date=today
        ).count()

        if today_reviews >= max_reviews_per_day:
            return False, {
                'error': 'reviews_limit_exceeded',
                'current': today_reviews,
                'max': max_reviews_per_day,
                'message': f'You have reached your daily limit of {max_reviews_per_day} reviews. Please try again tomorrow or upgrade your plan.'
            }

        return True, {
            'current': today_reviews,
            'max': max_reviews_per_day,
            'remaining': max_reviews_per_day - today_reviews
        }

    @classmethod
    def validate_moods_limit(cls, user):
        """Validate if user can add more mood-based preferences"""
        limits = cls.get_user_limits(user)
        max_moods = limits['moods']

        if cls.is_unlimited(max_moods):
            return True, None

        # This would need to be implemented based on your mood system
        # For now, returning True as placeholder
        return True, {
            'current': 0,
            'max': max_moods,
            'remaining': max_moods
        }

    @classmethod
    def get_user_usage_stats(cls, user):
        """Get comprehensive usage statistics for a user"""
        limits = cls.get_user_limits(user)

        # Count current usage
        favorites_count = UserFavoriteMovie.objects.filter(user=user).count()
        lists_count = Watchlist.objects.filter(user=user).count()

        today = timezone.now().date()
        today_reviews = MovieReview.objects.filter(
            user=user,
            review_type='USER',
            created_at__date=today
        ).count()

        return {
            'favorites': {
                'current': favorites_count,
                'max': limits['favorites'],
                'remaining': limits['favorites'] - favorites_count if not cls.is_unlimited(limits['favorites']) else -1,
                'is_unlimited': cls.is_unlimited(limits['favorites'])
            },
            'lists': {
                'current': lists_count,
                'max': limits['lists'],
                'remaining': limits['lists'] - lists_count if not cls.is_unlimited(limits['lists']) else -1,
                'is_unlimited': cls.is_unlimited(limits['lists'])
            },
            'reviews_today': {
                'current': today_reviews,
                'max': limits['reviews_per_day'],
                'remaining': limits['reviews_per_day'] - today_reviews if not cls.is_unlimited(limits['reviews_per_day']) else -1,
                'is_unlimited': cls.is_unlimited(limits['reviews_per_day'])
            },
            'moods': {
                'current': 0,  # Placeholder
                'max': limits['moods'],
                'remaining': limits['moods'] if not cls.is_unlimited(limits['moods']) else -1,
                'is_unlimited': cls.is_unlimited(limits['moods'])
            }
        }

    @classmethod
    def check_feature_access(cls, user, feature):
        """Check if user has access to a specific feature"""
        limits = cls.get_user_limits(user)

        feature_permissions = {
            'edit_reviews': user.user_type in ['premium_basic', 'premium_standard', 'premium_vip'],
            'vote_reviews': user.user_type in ['premium_basic', 'premium_standard', 'premium_vip'],
            'add_tags': user.user_type in ['premium_basic', 'premium_standard', 'premium_vip'],
            'export_data': user.user_type in ['premium_standard', 'premium_vip'],
            'compare_friends': user.user_type in ['premium_basic', 'premium_standard', 'premium_vip'],
            'priority_support': user.user_type in ['premium_standard', 'premium_vip'],
            'beta_access': user.user_type == 'premium_vip',
            'ad_free': user.user_type in ['premium_basic', 'premium_standard', 'premium_vip'],
        }

        return feature_permissions.get(feature, False)
