import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, TYPE_CHECKING, Any
from collections import defaultdict
from decimal import Decimal
import logging
import time
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models, transaction
from django.db.models import Avg, Count, Q, F, Sum
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
import math
import random
import json
import pickle
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None


# Advanced ML Libraries for Enhanced Demographic Filtering
try:
    from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
    from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
    from sklearn.cluster import KMeans, DBSCAN
    from scipy.sparse import csr_matrix, save_npz, load_npz
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available. Advanced demographic filtering will be limited.")

# Type checking imports to resolve Django model types
if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from apps.movies.models import Movie
    from .models import DemographicCluster

from apps.movies.models import Movie, MovieReview
from apps.users.models import UserFavoriteGenre
from apps.metadata.models import Genre
from .models import (
    UserPreference, UserSimilarity,
    RecommendationResult, DemographicCluster, RecommendationMetrics
)

User = get_user_model()
logger = logging.getLogger(__name__)

class RecommendationLockService:
    """
    Service to handle locking for recommendation generation to prevent race conditions
    """

    @staticmethod
    def get_lock_key(user_id: int, context: str = 'homepage') -> str:
        """Generate cache key for recommendation lock"""
        return f"rec_lock:user_{user_id}:context_{context}"

    @staticmethod
    def acquire_lock(user_id: int, context: str = 'homepage', timeout: int = 300) -> bool:
        """
        Acquire lock for recommendation generation
        Returns True if lock acquired, False if already locked
        """
        lock_key = RecommendationLockService.get_lock_key(user_id, context)

        # Try to acquire lock with 5-minute timeout using cache.add() which is atomic
        acquired = cache.add(lock_key, True, timeout=timeout)

        if acquired:
            logger.info(f"Acquired recommendation lock for user {user_id}, context {context}")
        else:
            logger.warning(f"Failed to acquire recommendation lock for user {user_id}, context {context} - already locked")

        return acquired

    @staticmethod
    def release_lock(user_id: int, context: str = 'homepage'):
        """Release lock for recommendation generation"""
        lock_key = RecommendationLockService.get_lock_key(user_id, context)
        cache.delete(lock_key)
        logger.info(f"Released recommendation lock for user {user_id}, context {context}")

    @staticmethod
    def is_locked(user_id: int, context: str = 'homepage') -> bool:
        """Check if user recommendation generation is currently locked"""
        lock_key = RecommendationLockService.get_lock_key(user_id, context)
        return cache.get(lock_key) is not None

    @staticmethod
    def wait_for_lock_release(user_id: int, context: str = 'homepage', max_wait: int = 60):
        """
        Wait for lock to be released (for cooperative tasks)
        Returns True when lock is released, False if timeout
        """
        start_time = time.time()

        while RecommendationLockService.is_locked(user_id, context):
            if time.time() - start_time > max_wait:
                logger.warning(f"Timeout waiting for lock release for user {user_id}, context {context}")
                return False

            time.sleep(1)  # Wait 1 second before checking again

        logger.info(f"Lock released for user {user_id}, context {context} after {time.time() - start_time:.1f}s")
        return True


def with_recommendation_lock(func):
    """
    Decorator to ensure recommendation generation is locked
    """
    def wrapper(self, user, *args, **kwargs):
        user_id = user.id if hasattr(user, 'id') else user
        context = kwargs.get('context', 'homepage')

        # Try to acquire lock
        if not RecommendationLockService.acquire_lock(user_id, context):
            logger.warning(f"Skipping {func.__name__} for user {user_id} - already generating recommendations")

            # For API calls, wait briefly and try to return existing recommendations
            if hasattr(self, '_return_existing_recommendations'):
                RecommendationLockService.wait_for_lock_release(user_id, context, max_wait=10)
                return self._return_existing_recommendations(user, *args, **kwargs)

            return []  # Return empty for background tasks

        try:
            # Execute the original function
            result = func(self, user, *args, **kwargs)
            return result
        finally:
            # Always release lock
            RecommendationLockService.release_lock(user_id, context)

    return wrapper


class CollaborativeFilteringService:
    """
    Enhanced Collaborative Filtering Service với multiple algorithms
    """

    def __init__(self):
        # Quality gate: tối thiểu số phim đồng‑đánh‑giá để tính Pearson
        self.min_common_ratings = 5
        # Ngưỡng "đủ giàu" cho precomputed similarities (không phải gate phục vụ)
        self.min_similar_users = 10
        # Quality gate: ngưỡng tương đồng tối thiểu để nhận láng giềng
        self.similarity_threshold = 0.1
        # TTL cache similarities
        self.cache_timeout = 3600 * 24 * 7

    def calculate_user_similarity(self, user1, user2, method='pearson') -> float:
        """
        Calculate similarity between two users using specified method
        """
        try:
            # Get ratings for both users and cast to float
            user1_ratings = dict(MovieReview.objects.filter(
                user=user1,
                review_type='USER',
                rating__isnull=False
            ).values_list('movie_id', 'rating'))

            # Cast Decimal to float
            user1_ratings = {movie_id: float(rating) for movie_id, rating in user1_ratings.items()}

            user2_ratings = dict(MovieReview.objects.filter(
                user=user2,
                review_type='USER',
                rating__isnull=False
            ).values_list('movie_id', 'rating'))

            # Cast Decimal to float
            user2_ratings = {movie_id: float(rating) for movie_id, rating in user2_ratings.items()}

            if not user1_ratings or not user2_ratings:
                return 0.0

            # Find common movies (J(u,v))
            common_movies = set(user1_ratings.keys()) & set(user2_ratings.keys())

            # Quality gate: không đủ phim chung ⇒ bỏ (sim=0)
            if len(common_movies) < self.min_common_ratings:
                return 0.0

            # Calculate similarity based on method
            if method == 'pearson':
                return self._pearson_correlation(user1_ratings, user2_ratings, common_movies)
            elif method == 'cosine':
                return self._cosine_similarity(user1_ratings, user2_ratings, common_movies)
            elif method == 'jaccard':
                return self._jaccard_similarity(user1_ratings, user2_ratings)
            elif method == 'euclidean':
                return self._euclidean_similarity(user1_ratings, user2_ratings, common_movies)
            else:
                return self._pearson_correlation(user1_ratings, user2_ratings, common_movies)

        except Exception as e:
            logger.error(f"Error calculating user similarity: {str(e)}")
            return 0.0

    def _pearson_correlation(self, ratings1: Dict, ratings2: Dict, common_movies: set) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(common_movies) == 0:
            return 0.0

        # Calculate means
        mean1 = sum([ratings1[movie] for movie in common_movies]) / len(common_movies)
        mean2 = sum([ratings2[movie] for movie in common_movies]) / len(common_movies)

        # Calculate numerator and denominators
        numerator = sum([(ratings1[movie] - mean1) * (ratings2[movie] - mean2) for movie in common_movies])

        sum_sq1 = sum([(ratings1[movie] - mean1) ** 2 for movie in common_movies])
        sum_sq2 = sum([(ratings2[movie] - mean2) ** 2 for movie in common_movies])

        denominator = math.sqrt(sum_sq1 * sum_sq2)

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _cosine_similarity(self, ratings1: Dict, ratings2: Dict, common_movies: set) -> float:
        """Calculate cosine similarity"""
        if len(common_movies) == 0:
            return 0.0

        # Calculate dot product and magnitudes
        dot_product = sum([ratings1[movie] * ratings2[movie] for movie in common_movies])

        magnitude1 = math.sqrt(sum([ratings1[movie] ** 2 for movie in common_movies]))
        magnitude2 = math.sqrt(sum([ratings2[movie] ** 2 for movie in common_movies]))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _jaccard_similarity(self, ratings1: Dict, ratings2: Dict, threshold=3.5) -> float:
        """Calculate Jaccard similarity based on liked movies"""
        liked1 = set([movie for movie, rating in ratings1.items() if rating >= threshold])
        liked2 = set([movie for movie, rating in ratings2.items() if rating >= threshold])

        if len(liked1) == 0 and len(liked2) == 0:
            return 0.0

        intersection = len(liked1 & liked2)
        union = len(liked1 | liked2)

        return intersection / union if union > 0 else 0.0

    def _euclidean_similarity(self, ratings1: Dict, ratings2: Dict, common_movies: set) -> float:
        """Calculate Euclidean distance similarity (normalized)"""
        if len(common_movies) == 0:
            return 0.0

        distance = math.sqrt(sum([(ratings1[movie] - ratings2[movie]) ** 2 for movie in common_movies]))

        # Normalize to 0-1 scale (assuming max rating difference is 5.0)
        max_distance = math.sqrt(len(common_movies) * 25)  # 5^2 = 25

        return 1 - (distance / max_distance) if max_distance > 0 else 0.0

    def find_similar_users(self, user, limit=50, method='pearson') -> List[Tuple[any, float]]:
        """
        Find similar users for collaborative filtering

        Returns:
            List of (user, similarity_score) tuples sorted by similarity
        """
        cache_key = f"similar_users:{user.id}:{method}:{limit}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        try:
            # Get user's ratings
            user_ratings = dict(MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            ).values_list('movie_id', 'rating'))

            if not user_ratings:
                return []

            user_rated_movies = set(user_ratings.keys())
            similar_users = []

            # Check precomputed similarities first
            # Precomputed similarities: chỉ lấy bản ghi đạt ngưỡng sim≥threshold
            precomputed = UserSimilarity.objects.filter(
                Q(user1=user) | Q(user2=user),
                similarity_type='collaborative',
                similarity_score__gte=self.similarity_threshold
            ).select_related('user1', 'user2')

            precomputed_users = {}
            for sim in precomputed:
                other_user = sim.user2 if sim.user1 == user else sim.user1
                precomputed_users[other_user.id] = (other_user, sim.similarity_score)

            if len(precomputed_users) >= self.min_similar_users:
                # Use precomputed similarities
                similar_users = list(precomputed_users.values())
            else:
                # Calculate similarities on-the-fly
                # Pool ứng viên on‑the‑fly: user đã chấm ÍT NHẤT 1 phim user hiện tại đã chấm; cap 500
                candidate_users = User.objects.filter(
                    moviereview__movie_id__in=user_rated_movies,
                    moviereview__review_type='USER',
                    moviereview__rating__isnull=False
                ).exclude(
                    id=user.id
                ).distinct()[:500]  # Limit candidates for performance

                for other_user in candidate_users:
                    similarity = self.calculate_user_similarity(user, other_user, method)

                    # Quality gate: chỉ giữ láng giềng có sim≥threshold
                    if similarity > self.similarity_threshold:
                        similar_users.append((other_user, similarity))

            # Sort by similarity score
            similar_users.sort(key=lambda x: x[1], reverse=True)
            result = similar_users[:limit]

            # Cache result
            cache.set(cache_key, result, self.cache_timeout)

            return result

        except Exception as e:
            logger.error(f"Error finding similar users: {str(e)}")
            return []

    def predict_rating(self, user, movie, similar_users: List[Tuple[any, float]]) -> Optional[float]:
        """
        Predict rating for a movie using weighted average of similar users
        """
        predicted, _ = self.predict_rating_with_details(user, movie, similar_users)
        return predicted

    def predict_rating_with_details(self, user, movie, similar_users: List[Tuple[any, float]]) -> Tuple[Optional[float], Dict]:
        """
        Predict rating and return calculation details for explanation.

        Returns: (predicted_rating or None, details_dict)
        details_dict includes keys: user_avg, contributors, weighted_delta_sum, similarity_sum_abs, neighbors_used
        """
        try:
            details: Dict[str, any] = {
                'user_avg': None,
                'contributors': [],
                'weighted_delta_sum': 0.0,
                'similarity_sum_abs': 0.0,
                'neighbors_used': 0,
            }

            if not similar_users:
                return None, details

            weighted_sum = 0.0
            similarity_sum = 0.0

            # Get user's average rating for normalization
            # User base (bias term) cho dự đoán: trung bình tất cả ratings của user
            user_avg = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 3.0
            user_avg = float(user_avg)
            details['user_avg'] = user_avg

            contributors: List[Dict[str, float]] = []

            for similar_user, similarity in similar_users:
                # Get similar user's rating for this movie
                similar_user_rating = MovieReview.objects.filter(
                    user=similar_user,
                    movie=movie,
                    review_type='USER',
                    rating__isnull=False
                ).first()

                if similar_user_rating:
                    # Get similar user's average for normalization
                    similar_avg = MovieReview.objects.filter(
                        user=similar_user,
                        review_type='USER',
                        rating__isnull=False
                    ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 3.0
                    similar_avg = float(similar_avg)

                    # Normalize rating
                    normalized_rating = float(similar_user_rating.rating) - similar_avg

                    weighted_sum += similarity * normalized_rating
                    similarity_sum += abs(similarity)

                    contributors.append({
                        'user_id': getattr(similar_user, 'id', None),
                        'similarity': float(similarity),
                        'rating': float(similar_user_rating.rating),
                        'similar_user_avg': similar_avg,
                        'delta': float(normalized_rating),
                    })

            # Quality gate: không có đóng góp hữu ích (Σ|sim|=0) ⇒ không dự đoán
            if similarity_sum == 0:
                details['contributors'] = contributors
                details['weighted_delta_sum'] = weighted_sum
                details['similarity_sum_abs'] = similarity_sum
                details['neighbors_used'] = len(contributors)
                return None, details

            # Bias‑corrected weighted average + clamp về [0,5]
            predicted_raw = user_avg + (weighted_sum / similarity_sum)
            predicted_clamped = max(0.0, min(5.0, predicted_raw))

            details['contributors'] = contributors
            details['weighted_delta_sum'] = float(weighted_sum)
            details['similarity_sum_abs'] = float(similarity_sum)
            details['neighbors_used'] = len(contributors)
            details['predicted_raw'] = float(predicted_raw)
            details['predicted_clamped'] = float(predicted_clamped)

            return predicted_clamped, details

        except Exception as e:
            logger.error(f"Error predicting rating (with details): {str(e)}")
            return None, {
                'user_avg': None,
                'contributors': [],
                'weighted_delta_sum': 0.0,
                'similarity_sum_abs': 0.0,
                'neighbors_used': 0,
            }

    def generate_collaborative_recommendations(self, user, limit=20, context='homepage') -> List[any]:
        """
        Generate collaborative filtering recommendations for a user
        """
        try:
            # Check cache first using unified cache service
            cached_recommendations = RecommendationCacheService.get_cached_recommendations(
                user, 'collaborative', context, limit
            )

            if cached_recommendations:
                return cached_recommendations

            # Track recommendation generation
            logger.info(f"🔄 Generating NEW collaborative recommendations for user {user.id} (no cache found)")
            metrics_service.track_recommendation_generation(
                recommendation_type='collaborative',
                user_count=1,
                movie_count=limit,
                context=context
            )

            # Find similar users
            similar_users = self.find_similar_users(user, limit=50)

            if not similar_users:
                logger.info(f"No similar users found for user {user.id}")
                return []

            # Get movies rated highly by similar users
            similar_user_ids = [u.id for u, _ in similar_users]
            user_similarity_map = {u.id: sim for u, sim in similar_users}

            # Get user's already rated movies
            user_rated_movies = set(MovieReview.objects.filter(
                user=user,
                review_type='USER'
            ).values_list('movie_id', flat=True))

            # Get candidate movies
            # Candidates: chỉ lấy phim láng giềng chấm tích cực (rating≥4.0) và u chưa xem
            candidate_ratings = MovieReview.objects.filter(
                user_id__in=similar_user_ids,
                review_type='USER',
                rating__gte=4.0,
                rating__isnull=False
            ).exclude(
                movie_id__in=user_rated_movies
            ).select_related('movie', 'user').order_by('-rating')

            # Calculate weighted scores for each movie
            movie_scores = defaultdict(list)

            for rating in candidate_ratings:
                similarity = user_similarity_map.get(rating.user_id, 0.0)
                weighted_score = float(rating.rating) * similarity
                movie_scores[rating.movie].append(weighted_score)

            # Calculate final scores and create recommendation objects
            recommendations = []

            for movie, scores in movie_scores.items():
                # Quality gate: support ≥ 1 (ít nhất 1 láng giềng chấm phim này)
                if len(scores) >= 1:  # At least 1 similar user rated it (reduced from 2)
                    avg_score = sum(scores) / len(scores)
                    # Confidence đơn giản theo support (min(1, support/5))
                    confidence = min(1.0, len(scores) / 5.0)

                    # Predict rating with details
                    predicted_rating, pred_details = self.predict_rating_with_details(user, movie, similar_users)

                    # Build richer explanation
                    contributors = pred_details.get('contributors', [])
                    neighbors_used = pred_details.get('neighbors_used', 0)
                    avg_similarity = (sum(c.get('similarity', 0.0) for c in contributors) / neighbors_used) if neighbors_used else 0.0
                    # Top 5 contributors by similarity
                    top_contributors = sorted(contributors, key=lambda c: c.get('similarity', 0.0), reverse=True)[:5]
                    # Keep lightweight fields for top contributors
                    top_contributors = [
                        {
                            'user_id': tc.get('user_id'),
                            'similarity': float(tc.get('similarity', 0.0)),
                            'rating': float(tc.get('rating', 0.0)),
                        }
                        for tc in top_contributors
                    ]

                    recommendations.append({
                        'movie': movie,
                        'score': avg_score,
                        'confidence': confidence,
                        'predicted_rating': predicted_rating,
                        'explanation': {
                            'type': 'collaborative',
                            'similar_users_count': len(scores),
                            'support': neighbors_used,
                            'average_weighted_rating': float(avg_score),
                            'avg_similarity': float(avg_similarity),
                            'user_avg': float(pred_details.get('user_avg', 0.0) or 0.0),
                            'prediction_components': {
                                'weighted_delta_sum': float(pred_details.get('weighted_delta_sum', 0.0)),
                                'similarity_sum_abs': float(pred_details.get('similarity_sum_abs', 0.0)),
                            },
                            'predicted_raw': float(pred_details.get('predicted_raw', predicted_rating or 0.0)) if pred_details.get('predicted_raw') is not None else None,
                            'top_contributors': top_contributors,
                        }
                    })

            # Sort by score and take top recommendations
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            top_recommendations = recommendations[:limit]

            # Store recommendations using unified cache service
            RecommendationCacheService.store_recommendations(user, top_recommendations, 'collaborative', context)

            return [rec['movie'] for rec in top_recommendations]

        except Exception as e:
            logger.error(f"Error generating collaborative recommendations: {str(e)}")
            return []

    def _store_recommendations(self, user, recommendations: List[Dict], rec_type: str, context: str):
        """Store recommendations in database"""
        try:
            # Clear existing recommendations for this user/type/context
            RecommendationResult.objects.filter(
                user=user,
                recommendation_type=rec_type,
                context=context
            ).delete()

            # Create new recommendations (dedupe by (user, movie, type, context))
            recommendation_objects = []
            existing_pairs = set(RecommendationResult.objects.filter(
                user=user,
                recommendation_type=rec_type,
                context=context
            ).values_list('movie_id', flat=True))

            for rank, rec in enumerate(recommendations, 1):
                recommendation_objects.append(
                    RecommendationResult(
                        user=user,
                        movie=rec['movie'],
                        recommendation_type=rec_type,
                        context=context,
                        predicted_rating=rec.get('predicted_rating'),
                        confidence_score=rec.get('confidence', 0.5),
                        novelty_score=rec.get('novelty_score', 0.5),
                        rank=rank,
                        score=rec['score'],
                        explanation=rec.get('explanation', {})
                    )
                )

            RecommendationResult.objects.bulk_create(recommendation_objects)

        except Exception as e:
            logger.error(f"Error storing recommendations: {str(e)}")

    def update_user_similarities(self, user) -> int:
        """
        Update user similarities for a specific user
        Returns the number of similarities updated
        """
        try:
            # Find similar users for this user
            similar_users = self.find_similar_users(user, limit=50, method='pearson')

            # Store similarities
            similarities_to_create = []
            for similar_user, similarity in similar_users:
                if similarity > self.similarity_threshold:  # Only store meaningful similarities
                    similarities_to_create.append(
                        UserSimilarity(
                            user1=user,
                            user2=similar_user,
                            similarity_score=similarity,
                            similarity_type='collaborative',
                            calculation_method='pearson',
                            confidence=1.0,
                            common_ratings_count=self._get_common_ratings_count(user, similar_user)
                        )
                    )

            # Bulk create similarities with ignore_conflicts to handle duplicates
            if similarities_to_create:
                UserSimilarity.objects.bulk_create(
                    similarities_to_create,
                    ignore_conflicts=True
                )
                logger.info(f"Updated {len(similarities_to_create)} similarities for user {user.id}")
                return len(similarities_to_create)
            else:
                logger.info(f"No meaningful similarities found for user {user.id}")
                return 0

        except Exception as e:
            logger.error(f"Error updating similarities for user {user.id}: {str(e)}")
            return 0

    def _get_common_ratings_count(self, user1, user2) -> int:
        """Get the number of common movies rated by both users"""
        try:
            user1_movies = set(MovieReview.objects.filter(
                user=user1,
                review_type='USER',
                rating__isnull=False
            ).values_list('movie_id', flat=True))

            user2_movies = set(MovieReview.objects.filter(
                user=user2,
                review_type='USER',
                rating__isnull=False
            ).values_list('movie_id', flat=True))

            return len(user1_movies & user2_movies)
        except Exception as e:
            logger.error(f"Error getting common ratings count: {str(e)}")
            return 0

class EnhancedDemographicFilteringService:
    """
    Enhanced Demographic Filtering Service with advanced ML capabilities
    """

    def __init__(self):
        self.cache_timeout = None  # No expiration - cache forever
        self.vectorizer = AdvancedDemographicVectorizer()
        self.similarity_calculator = AdvancedDemographicSimilarityCalculator(self.vectorizer)
        self.min_similar_users = 1  # Giảm từ 3 xuống 1 để DF có thể hoạt động
        self.similarity_threshold = 0.1
        self.kmeans_model = None
        self.scaler = None
        self.use_kmeans_clustering = True  # Flag to enable/disable K-means

        # Tự động load K-means model nếu có clusters trong database
        self._load_kmeans_model()

        # Do NOT initialize a blank scaler in production. If scaler is missing,
        # fallback logic will use unscaled vectors (and we should fix payload).
        # This prevents unfitted StandardScaler errors during transform.
        if self.kmeans_model is not None and self.scaler is None:
            logger.warning("K-means model loaded without fitted scaler; using unscaled vectors until scaler payload is provided")

    def _get_model_cache_path(self) -> str:
        """
        Get the cache path for K-means model
        """
        import os
        from django.conf import settings

        # Tạo thư mục cache nếu chưa tồn tại
        cache_dir = os.path.join(settings.BASE_DIR, 'cache', 'models')
        os.makedirs(cache_dir, exist_ok=True)

        return os.path.join(cache_dir, 'kmeans_demographic_model.pkl')

    def _save_model_to_cache(self):
        """
        Save K-means model and scaler to cache
        """
        try:
            if self.kmeans_model is None or self.scaler is None:
                logger.warning("No model to save to cache")
                return False

            import joblib
            import os

            cache_path = self._get_model_cache_path()

            # Save both model and scaler
            model_data = {
                'kmeans_model': self.kmeans_model,
                'scaler': self.scaler,
                'timestamp': time.time()
            }

            joblib.dump(model_data, cache_path)
            logger.info(f"✅ Model saved to cache: {cache_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving model to cache: {str(e)}")
            return False

    def _load_model_from_cache(self):
        """
        Load K-means model and scaler from cache
        """
        try:
            import joblib
            import os
            import time

            cache_path = self._get_model_cache_path()

            if not os.path.exists(cache_path):
                logger.info("No cached model found")
                return False

            # Check cache age (only if timeout is set)
            if self.cache_timeout is not None:
                cache_age = time.time() - os.path.getmtime(cache_path)
                if cache_age > self.cache_timeout:
                    logger.info("Cache expired, will reload model")
                    return False

            # Load model data
            model_data = joblib.load(cache_path)

            self.kmeans_model = model_data['kmeans_model']
            self.scaler = model_data['scaler']

            logger.info(f"✅ Model loaded from cache: {cache_path}")
            return True

        except Exception as e:
            logger.error(f"Error loading model from cache: {str(e)}")
            return False

    def _load_kmeans_model(self):
        """
        Load K-means model from cache or existing clusters in database
        """
        try:
            if not SKLEARN_AVAILABLE:
                logger.warning("Scikit-learn not available. Cannot load K-means model.")
                return

            # Thử load từ cache trước
            if self._load_model_from_cache():
                logger.info("✅ Model loaded from cache successfully")
                return

            # Nếu không có cache, thử load từ ModelStorage
            logger.info("🔄 Cache not available, trying ModelStorage...")

            from apps.recommendations.models import ModelStorage
            model_storage = ModelStorage.objects.filter(
                model_name__icontains='kmeans',
                is_active=True
            ).first()

            if model_storage:
                try:
                    import pickle
                    loaded_obj = pickle.loads(model_storage.model_data)

                    # Case 1: New format -> dict payload with 'model'/'scaler'
                    if isinstance(loaded_obj, dict):
                        model = loaded_obj.get('model') or loaded_obj.get('kmeans_model')
                        scaler = loaded_obj.get('scaler')
                        if model is not None:
                            self.kmeans_model = model
                            self.scaler = scaler
                            logger.info("✅ Model loaded from ModelStorage successfully")
                            return

                    # Case 2: Backward compatibility -> raw KMeans object
                    self.kmeans_model = loaded_obj
                    # scaler có thể không tồn tại trong định dạng cũ
                    if not hasattr(self, 'scaler') or self.scaler is None:
                        self.scaler = None
                    logger.info("✅ Model loaded from ModelStorage (raw model)")
                    return
                except Exception as e:
                    logger.warning(f"Error loading from ModelStorage: {str(e)}")

            # Fallback: Sử dụng OptimizedKMeansProductionService
            logger.info("🔄 Using OptimizedKMeansProductionService for model loading...")

            try:
                from apps.recommendations.services import OptimizedKMeansProductionService
                optimized_service = OptimizedKMeansProductionService()

                # Kiểm tra xem có model trong cache không
                from django.core.cache import cache
                model_data = cache.get('kmeans_model')

                if model_data:
                    import pickle
                    model = pickle.loads(model_data)
                    self.kmeans_model = model
                    # Don't use scaler if none exists - avoid unfitted scaler errors
                    if not hasattr(self, 'scaler') or self.scaler is None:
                        self.scaler = None
                        logger.info("✅ Model loaded from OptimizedKMeansProductionService cache without scaler")
                    else:
                        logger.info("✅ Model loaded from OptimizedKMeansProductionService cache")
                    return

            except Exception as e:
                logger.warning(f"Error with OptimizedKMeansProductionService: {str(e)}")

            logger.warning("No K-means model available. Please run training first.")
            self.kmeans_model = None
            self.scaler = None

        except Exception as e:
            logger.error(f"Error loading K-means model: {str(e)}")
            self.kmeans_model = None
            self.scaler = None

    def create_kmeans_clusters(self, recalculate=False, n_clusters=8, adaptive=True, k_min=4, k_max=12):
        """
        Create demographic clusters using K-means clustering
        """
        try:
            if not SKLEARN_AVAILABLE:
                logger.warning("Scikit-learn not available. Using rule-based clustering.")
                return self.create_demographic_clusters(recalculate)

            if not recalculate and DemographicCluster.objects.filter(cluster_id__startswith='kmeans_').exists():
                logger.info("K-means clusters already exist")
                # Load model nếu chưa có
                if self.kmeans_model is None:
                    self._load_kmeans_model()
                return

            logger.info(f"Creating K-means clusters with {n_clusters} clusters...")

            # Clear existing K-means clusters if recalculating
            if recalculate:
                DemographicCluster.objects.filter(cluster_id__startswith='kmeans_').delete()

            # Get users with demographic data
            users_with_data = User.objects.filter(
                age__isnull=False,
                gender__isnull=False
            ).exclude(age__isnull=True)

            if users_with_data.count() < n_clusters * 5:
                logger.warning(f"Not enough users for {n_clusters} clusters. Using rule-based clustering.")
                return self.create_demographic_clusters(recalculate)

            # Create demographic vectors for all users
            user_vectors = []
            users_list = []

            logger.info(f"📊 Creating demographic vectors for {users_with_data.count()} users...")

            for user in users_with_data:
                try:
                    vector = self.vectorizer.create_demographic_vector(user)
                    user_vectors.append(vector)
                    users_list.append(user)
                except Exception as e:
                    logger.warning(f"Error creating vector for user {user.id}: {str(e)}")
                    continue

            if len(user_vectors) < n_clusters * 3:
                logger.warning("Not enough valid vectors for K-means clustering")
                return self.create_demographic_clusters(recalculate)

            # Convert to numpy array
            X = np.array(user_vectors)

            # Standardize features
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Optionally select optimal K adaptively (silhouette)
            optimal_k = n_clusters
            if adaptive:
                try:
                    from sklearn.cluster import MiniBatchKMeans
                    from sklearn.metrics import silhouette_score

                    # Boundaries for K
                    k_lower = max(2, k_min)
                    k_upper = min(k_max, len(X_scaled) - 1)
                    if k_upper <= k_lower:
                        k_upper = max(k_lower + 1, 3)

                    best_score = -1.0
                    best_k = n_clusters

                    # Sample size for silhouette to reduce cost
                    sample_size = min(5000, len(X_scaled))

                    for k in range(k_lower, k_upper + 1):
                        try:
                            mbk = MiniBatchKMeans(n_clusters=k, random_state=42, batch_size=min(1000, len(X_scaled)), n_init=5)
                            labels = mbk.fit_predict(X_scaled)
                            score = silhouette_score(X_scaled, labels, sample_size=sample_size)
                            if score > best_score:
                                best_score = score
                                best_k = k
                        except Exception as e:
                            logger.debug(f"Silhouette failed for k={k}: {e}")
                            continue

                    optimal_k = best_k
                    logger.info(f"✅ Adaptive K selection chose k={optimal_k} (silhouette={best_score:.4f})")
                except Exception as e:
                    logger.warning(f"Adaptive K selection failed, using n_clusters={n_clusters}: {e}")

            # Perform K-means clustering
            logger.info(" Running K-means clustering...")
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)

            # Store the model for future use
            self.kmeans_model = kmeans
            self.scaler = scaler

            # Create clusters in database
            logger.info(" Creating cluster records in database...")

            for cluster_id in range(self.kmeans_model.n_clusters):
                # Get users in this cluster
                cluster_users = [users_list[i] for i in range(len(users_list)) if cluster_labels[i] == cluster_id]

                if len(cluster_users) < 3:
                    continue

                # Calculate cluster characteristics
                ages = [user.age for user in cluster_users if user.age]
                genders = [user.gender for user in cluster_users if user.gender]
                occupations = [user.occupation for user in cluster_users if user.occupation]

                # Most common gender
                from collections import Counter
                gender_counts = Counter(genders)
                primary_gender = gender_counts.most_common(1)[0][0] if gender_counts else 'M'

                # Age range
                age_min = min(ages) if ages else 0
                age_max = max(ages) if ages else 100

                # Calculate genre preferences for this cluster
                genre_preferences = self._calculate_cluster_genre_preferences(cluster_users)

                # Calculate average rating
                rating_stats = MovieReview.objects.filter(
                    user__in=cluster_users,
                    review_type='USER',
                    rating__isnull=False
                ).aggregate(
                    avg_rating=Avg('rating'),
                    count=Count('rating')
                )

                # Create cluster record
                cluster = DemographicCluster.objects.create(
                    cluster_id=f"kmeans_{cluster_id}",
                    name=f"K-means Cluster {cluster_id}",
                    description=f"K-means cluster {cluster_id}: {len(cluster_users)} users, age {age_min}-{age_max}, gender {primary_gender}",
                    age_range_min=age_min,
                    age_range_max=age_max,
                    primary_gender=primary_gender,
                    common_occupations=list(set(occupations)),  # All occupations
                    preferred_genres=genre_preferences,
                    average_rating=rating_stats['avg_rating'] or 3.0,
                    user_count=len(cluster_users)
                )

                # Assign users to this cluster
                for user in cluster_users:
                    user_pref, created = UserPreference.objects.get_or_create(user=user)
                    user_pref.demographic_cluster = f"kmeans_{cluster_id}"
                    user_pref.save()

            logger.info(f"✅ Created {n_clusters} K-means clusters successfully")

            # Lưu model vào cache để lần sau load nhanh hơn
            self._save_model_to_cache()

        except Exception as e:
            logger.error(f"Error creating K-means clusters: {str(e)}")
            # Fallback to rule-based clustering
            return self.create_demographic_clusters(recalculate)

    def get_user_kmeans_cluster(self, user) -> Optional[any]:
        """
        Get K-means cluster for a user using the trained model
        """
        try:
            # Check if user already has a K-means cluster assigned
            user_pref = UserPreference.objects.filter(user=user).first()
            if user_pref and user_pref.demographic_cluster and user_pref.demographic_cluster.startswith('kmeans_'):
                cluster = DemographicCluster.objects.filter(
                    cluster_id=user_pref.demographic_cluster
                ).first()
                if cluster:
                    return cluster

            # If K-means model is not available, try to find best matching existing cluster
            if not self.kmeans_model or not SKLEARN_AVAILABLE:
                logger.info(f"K-means model not available for user {user.id}, finding best matching cluster")
                return self._find_best_matching_kmeans_cluster(user)

            # Create user vector and predict cluster
            if user.age and user.gender:
                user_vector = self.vectorizer.create_demographic_vector(user)
                if user_vector is not None:
                    # Ensure consistent dtype
                    user_vector = np.array(user_vector, dtype=np.float64)

                    # Handle scaler properly
                    if self.scaler is not None:
                        try:
                            user_vector_scaled = self.scaler.transform([user_vector])
                            cluster_label = self.kmeans_model.predict(user_vector_scaled)[0]
                        except Exception as e:
                            logger.warning(f"Scaler transform failed for user {user.id}: {str(e)}, using unscaled vector")
                            # Fallback to unscaled vector
                            cluster_label = self.kmeans_model.predict([user_vector])[0]
                    else:
                        # No scaler available, use unscaled vector
                        cluster_label = self.kmeans_model.predict([user_vector])[0]

                # Find or create cluster
                cluster = DemographicCluster.objects.filter(
                    cluster_id=f"kmeans_{cluster_label}"
                ).first()

                if cluster:
                    # Update user preference
                    user_pref, created = UserPreference.objects.get_or_create(user=user)
                    user_pref.demographic_cluster = f"kmeans_{cluster_label}"
                    user_pref.save()

                    return cluster

            return None

        except Exception as e:
            logger.error(f"Error getting user K-means cluster: {str(e)}")
            return self._find_best_matching_kmeans_cluster(user)

    def _find_best_matching_kmeans_cluster(self, user) -> Optional[any]:
        """
        Find the best matching K-means cluster for a user based on demographics
        when the K-means model is not available
        """
        try:
            if not user.age or not user.gender:
                return None

            # Get all existing K-means clusters
            kmeans_clusters = DemographicCluster.objects.filter(
                cluster_id__startswith='kmeans_'
            )

            if not kmeans_clusters.exists():
                logger.info("No K-means clusters found in database")
                return None

            best_cluster = None
            best_score = -1

            for cluster in kmeans_clusters:
                score = 0

                # Create user vector for similarity calculation
                user_vector = self.vectorizer.create_demographic_vector(user)

                # Get sample users from cluster to calculate average similarity
                cluster_users = User.objects.filter(
                    recommendation_preference__demographic_cluster=cluster.cluster_id
                )[:10]  # Sample 10 users for performance

                if cluster_users.exists():
                    # Calculate average vector similarity with cluster users
                    cluster_vectors = []
                    for cluster_user in cluster_users:
                        try:
                            cluster_vector = self.vectorizer.create_demographic_vector(cluster_user)
                            cluster_vectors.append(cluster_vector)
                        except Exception as e:
                            logger.warning(f"Error creating vector for cluster user {cluster_user.id}: {e}")
                            continue

                    if cluster_vectors:
                        # Calculate average similarity
                        from sklearn.metrics.pairwise import cosine_similarity
                        similarities = cosine_similarity([user_vector], cluster_vectors)[0]
                        avg_similarity = np.mean(similarities)

                        # Vector similarity is the primary factor (0-1 scale, multiply by 10 for scoring)
                        score += avg_similarity * 10  # Up to 10 points for perfect similarity

                        logger.debug(f"Cluster {cluster.cluster_id} average similarity: {avg_similarity:.3f}, score: {avg_similarity * 10:.1f}")
                    else:
                        # Fallback to old logic if vector creation fails
                        logger.warning(f"Failed to create vectors for cluster {cluster.cluster_id}, using fallback logic")
                        if cluster.age_range_min <= user.age <= cluster.age_range_max:
                            score += 3
                        if cluster.primary_gender == user.gender:
                            score += 2
                else:
                    # Empty cluster - use basic logic
                    if cluster.age_range_min <= user.age <= cluster.age_range_max:
                        score += 3
                    if cluster.primary_gender == user.gender:
                        score += 2

                # Check if user has ratings
                user_has_ratings = MovieReview.objects.filter(
                    user=user,
                    review_type='USER',
                    rating__isnull=False
                ).exists()

                # Get cluster statistics
                cluster_users_with_ratings = User.objects.filter(
                    recommendation_preference__demographic_cluster=cluster.cluster_id,
                    moviereview__review_type='USER',
                    moviereview__rating__isnull=False
                ).distinct().count()
                cluster_total_users = User.objects.filter(
                    recommendation_preference__demographic_cluster=cluster.cluster_id
                ).count()
                cluster_rating_ratio = cluster_users_with_ratings / cluster_total_users if cluster_total_users > 0 else 0

                # Behavioral compatibility score (secondary factor)
                if user_has_ratings:
                    # User has ratings - prefer clusters with more users who have ratings
                    score += min(cluster_rating_ratio * 2, 2)  # Reduced weight, max 2 points
                else:
                    # New user - prefer clusters with users who have ratings
                    if cluster_rating_ratio > 0.3:
                        score += 2
                    elif cluster_rating_ratio > 0.1:
                        score += 1
                    else:
                        score -= 1  # Reduced penalty

                # Prefer clusters with more users (more data)
                score += min(cluster.user_count / 100, 1)  # Bonus for larger clusters

                if score > best_score:
                    best_score = score
                    best_cluster = cluster

            if best_cluster and best_score > 0:
                # Update user preference
                user_pref, created = UserPreference.objects.get_or_create(user=user)
                user_pref.demographic_cluster = best_cluster.cluster_id
                user_pref.save()

                logger.info(f"Assigned user {user.id} to K-means cluster {best_cluster.cluster_id} with score {best_score}")
                return best_cluster

            return None

        except Exception as e:
            logger.error(f"Error finding best matching K-means cluster: {str(e)}")
            return None

    def refresh_clusters(self, method='kmeans', recalculate=True, n_clusters=8):
        """
        Refresh demographic clusters using specified method

        Args:
            method: 'kmeans' or 'rule-based'
            recalculate: Whether to recalculate existing clusters
            n_clusters: Number of clusters for K-means
        """
        try:
            logger.info(f"🔄 Refreshing demographic clusters using {method} method...")

            if method == 'kmeans':
                return self.create_kmeans_clusters(recalculate=recalculate, n_clusters=n_clusters)
            else:
                return self.create_demographic_clusters(recalculate=recalculate)

        except Exception as e:
            logger.error(f"Error refreshing clusters: {str(e)}")
            raise

    def create_demographic_clusters(self, recalculate=False):
        """
        Create demographic clusters based on user characteristics
        """
        try:
            if not recalculate and DemographicCluster.objects.exists():
                logger.info("Demographic clusters already exist")
                return

            # Clear existing clusters if recalculating
            if recalculate:
                DemographicCluster.objects.all().delete()

            # Define age groups
            age_groups = [
                (0, 17, "Under 18"),
                (18, 24, "18-24"),
                (25, 34, "25-34"),
                (35, 44, "35-44"),
                (45, 54, "45-54"),
                (55, 100, "55+")
            ]

            genders = ['M', 'F', 'O']

            # Create clusters for each age group + gender combination
            cluster_id = 1

            for age_min, age_max, age_label in age_groups:
                for gender in genders:
                    cluster_name = f"{age_label}_{gender}"

                    # Calculate cluster characteristics
                    cluster_users = User.objects.filter(
                        age__gte=age_min,
                        age__lte=age_max,
                        gender=gender
                    ).exclude(age__isnull=True)

                    if cluster_users.count() < 5:  # Skip small clusters
                        continue

                    # Calculate genre preferences for this cluster
                    genre_preferences = self._calculate_cluster_genre_preferences(cluster_users)

                    # Calculate average rating and variance
                    rating_stats = MovieReview.objects.filter(
                        user__in=cluster_users,
                        review_type='USER',
                        rating__isnull=False
                    ).aggregate(
                        avg_rating=Avg('rating'),
                        count=Count('rating')
                    )

                    # Get common occupations
                    common_occupations = list(cluster_users.filter(
                        occupation__isnull=False
                    ).values_list('occupation', flat=True).distinct())

                    # Create cluster
                    DemographicCluster.objects.create(
                        cluster_id=f"demo_{cluster_id}",
                        name=cluster_name,
                        description=f"Users aged {age_min}-{age_max}, gender {gender}",
                        age_range_min=age_min,
                        age_range_max=age_max,
                        primary_gender=gender,
                        common_occupations=common_occupations,
                        preferred_genres=genre_preferences,
                        average_rating=rating_stats['avg_rating'] or 3.0,
                        user_count=cluster_users.count()
                    )

                    # Update user preferences with cluster assignment
                    for user in cluster_users:
                        user_pref, created = UserPreference.objects.get_or_create(user=user)
                        user_pref.demographic_cluster = f"demo_{cluster_id}"
                        user_pref.save()

                    cluster_id += 1

            logger.info(f"Created {cluster_id - 1} demographic clusters")

        except Exception as e:
            logger.error(f"Error creating demographic clusters: {str(e)}")

    def _calculate_cluster_genre_preferences(self, users) -> Dict:
        """Calculate genre preferences for a cluster of users"""
        try:
            # Get all genres
            genres = Genre.objects.all()
            genre_preferences = {}

            for genre in genres:
                # Calculate average rating for this genre within the cluster
                genre_ratings = MovieReview.objects.filter(
                    user__in=users,
                    movie__genres=genre,
                    review_type='USER',
                    rating__isnull=False
                ).aggregate(
                    avg_rating=Avg('rating'),
                    count=Count('rating')
                )

                if genre_ratings['count'] and genre_ratings['count'] > 5:
                    genre_preferences[str(genre.id)] = {
                        'average_rating': float(genre_ratings['avg_rating']),
                        'rating_count': genre_ratings['count'],
                        'preference_score': float(genre_ratings['avg_rating']) / 5.0  # Normalize to 0-1
                    }

            return genre_preferences

        except Exception as e:
            logger.error(f"Error calculating cluster genre preferences: {str(e)}")
            return {}

    def get_user_demographic_cluster(self, user) -> Optional[any]:
        """Get demographic cluster for a user"""
        try:
            # Check if user already has a cluster assigned
            user_pref = UserPreference.objects.filter(user=user).first()
            if user_pref and user_pref.demographic_cluster:
                return DemographicCluster.objects.filter(
                    cluster_id=user_pref.demographic_cluster
                ).first()

            # Find matching cluster based on demographics
            if user.age and user.gender:
                cluster = DemographicCluster.objects.filter(
                    age_range_min__lte=user.age,
                    age_range_max__gte=user.age,
                    primary_gender=user.gender
                ).first()

                if cluster:
                    # Update user preference
                    user_pref, created = UserPreference.objects.get_or_create(user=user)
                    user_pref.demographic_cluster = cluster.cluster_id
                    user_pref.save()

                    return cluster

            return None

        except Exception as e:
            logger.error(f"Error getting user demographic cluster: {str(e)}")
            return None

    def assign_user_to_cluster(self, user) -> Optional[any]:
        """
        Assign a user to the most appropriate demographic cluster
        """
        try:
            if not user.age or not user.gender:
                logger.info(f"User {user.id} lacks demographic data for clustering")
                return None

            # Find matching cluster based on demographics
            cluster = DemographicCluster.objects.filter(
                age_range_min__lte=user.age,
                age_range_max__gte=user.age,
                primary_gender=user.gender
            ).first()

            if cluster:
                # Update user preference
                user_pref, created = UserPreference.objects.get_or_create(user=user)
                user_pref.demographic_cluster = cluster.cluster_id
                user_pref.save()

                # Update cluster user count
                cluster.user_count = User.objects.filter(
                    recommendation_preference__demographic_cluster=cluster.cluster_id
                ).count()
                cluster.save()

                logger.info(f"Assigned user {user.id} to cluster {cluster.cluster_id}")
                return cluster
            else:
                # Create a new cluster if none exists for this demographic
                cluster_id = f"demo_{user.age}_{user.gender}_{timezone.now().timestamp()}"
                cluster = DemographicCluster.objects.create(
                    cluster_id=cluster_id,
                    name=f"Age {user.age} - {user.gender}",
                    description=f"Users aged {user.age}, gender {user.gender}",
                    age_range_min=max(0, user.age - 2),
                    age_range_max=user.age + 2,
                    primary_gender=user.gender,
                    user_count=1,
                    average_rating=3.0  # Default
                )

                # Assign user to new cluster
                user_pref, created = UserPreference.objects.get_or_create(user=user)
                user_pref.demographic_cluster = cluster.cluster_id
                user_pref.save()

                logger.info(f"Created new cluster {cluster_id} for user {user.id}")
                return cluster

        except Exception as e:
            logger.error(f"Error assigning user {user.id} to cluster: {str(e)}")
            return None

    def generate_demographic_recommendations(self, user, limit=20, context='homepage', store=True) -> List[any]:
        """
        Generate recommendations based on user's demographic cluster
        """
        try:
            # Check cache first using unified cache service
            cached_recommendations = RecommendationCacheService.get_cached_recommendations(
                user, 'demographic', context, limit
            )

            if cached_recommendations:
                return cached_recommendations

            # Track recommendation generation
            metrics_service.track_recommendation_generation(
                recommendation_type='demographic',
                user_count=1,
                movie_count=limit,
                context=context
            )

            # Get user's demographic cluster
            cluster = self.get_user_demographic_cluster(user)

            if not cluster:
                logger.info(f"No demographic cluster found for user {user.id}")
                return []

            # Get user's already rated movies
            user_rated_movies = set(MovieReview.objects.filter(
                user=user,
                review_type='USER'
            ).values_list('movie_id', flat=True))

            # Get highly rated movies by users in the same cluster
            cluster_users = User.objects.filter(
                recommendation_preference__demographic_cluster=cluster.cluster_id
            ).exclude(id=user.id)

            if not cluster_users.exists():
                return []

            # Get movies highly rated by cluster users
            cluster_recommendations = MovieReview.objects.filter(
                user__in=cluster_users,
                review_type='USER',
                rating__gte=4.0,
                rating__isnull=False
            ).exclude(
                movie_id__in=user_rated_movies
            ).values('movie').annotate(
                avg_rating=Avg('rating'),
                rating_count=Count('rating')
            ).filter(
                rating_count__gte=3  # At least 3 ratings from cluster
            ).order_by('-avg_rating', '-rating_count')

            # Score movies based on cluster preferences
            recommendations = []

            for rec in cluster_recommendations[:limit * 2]:  # Get more candidates
                try:
                    movie = Movie.objects.select_related().prefetch_related('genres').get(
                        id=rec['movie']
                    )

                    # Calculate comprehensive demographic score với component breakdown
                    age_score = self._calculate_age_preference_score(movie, cluster)
                    gender_score = self._calculate_gender_preference_score(movie, cluster)
                    occupation_score = self._calculate_occupation_preference_score(movie, cluster)
                    location_score = self._calculate_location_preference_score(movie, cluster)
                    demographic_score = self._calculate_demographic_score(movie, cluster)

                    # Combine with cluster rating (theo lý thuyết weighted hybrid scoring)
                    avg_rating_float = float(rec['avg_rating']) if rec['avg_rating'] else 0.0
                    final_score = (avg_rating_float / 5.0 * 0.7) + (demographic_score * 0.3)

                    recommendations.append({
                        'movie': movie,
                        'score': final_score,
                        'confidence': min(1.0, rec['rating_count'] / 10.0),
                        'predicted_rating': rec['avg_rating'],
                        'novelty_score': 0.5,
                        'explanation': {
                            'type': 'demographic',
                            'cluster_name': cluster.name,
                            'cluster_avg_rating': rec['avg_rating'],
                            'cluster_rating_count': rec['rating_count'],
                            'demographic_score': demographic_score,
                            'component_scores': {
                                'age_score': round(age_score, 3),
                                'gender_score': round(gender_score, 3),
                                'occupation_score': round(occupation_score, 3),
                                'location_score': round(location_score, 3)
                            },
                            'calculation': f'({avg_rating_float}/5.0) × 0.7 + ({demographic_score:.3f} × 0.3) = {final_score:.3f}',
                            'confidence_calculation': f'min(1.0, {rec["rating_count"]}/10) = {min(1.0, rec["rating_count"] / 10.0):.3f}'
                        }
                    })

                except Movie.DoesNotExist:
                    continue

            # Sort by final score
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            top_recommendations = recommendations[:limit]

            # Store recommendations only if requested
            if store:
                self._store_recommendations(user, top_recommendations, 'demographic', context)

            return [rec['movie'] for rec in top_recommendations]

        except Exception as e:
            logger.error(f"Error generating demographic recommendations: {str(e)}")
            return []

    def _calculate_demographic_score(self, movie, cluster) -> float:
        """
        Calculate comprehensive demographic score theo lý thuyết thuần túy
        SIMPLIFICATION: Sử dụng cluster.preferred_genres (đã học từ toàn bộ cluster data)
        """
        try:
            if not cluster or not cluster.preferred_genres:
                return 0.5

            # Sử dụng cluster.preferred_genres (đã được tính từ tất cả users trong cluster)
            # Đây là approach đơn giản hơn nhưng vẫn đúng lý thuyết
            movie_genres = movie.genres.all()
            if not movie_genres.exists():
                return 0.5

            total_score = 0.0
            genre_count = 0

            for genre in movie_genres:
                genre_id_str = str(genre.id)
                if genre_id_str in cluster.preferred_genres:
                    genre_pref = cluster.preferred_genres[genre_id_str]

                    # Handle different preference data structures
                    if isinstance(genre_pref, dict):
                        score = genre_pref.get('preference_score', 0.5)
                    elif isinstance(genre_pref, (int, float)):
                        score = float(genre_pref)
                    else:
                        score = 0.5

                    total_score += score
                    genre_count += 1

            if genre_count == 0:
                return 0.5  # No preference data available

            return total_score / genre_count

        except Exception as e:
            logger.error(f"Error calculating demographic score: {str(e)}")
            return 0.5

    def _calculate_age_preference_score(self, movie, cluster) -> float:
        """
        Calculate age-based preference score từ DATA THỰC TẾ (không hardcode)
        Học genre preferences từ cluster users' rating history
        """
        try:
            if not cluster or not cluster.preferred_genres:
                return 0.5

            # Get actual genre preferences từ cluster data
            # (đã được tính toán và lưu trong cluster.preferred_genres)
            movie_genres = movie.genres.all()
            if not movie_genres.exists():
                return 0.5

            total_score = 0.0
            genre_count = 0

            for genre in movie_genres:
                genre_id_str = str(genre.id)
                if genre_id_str in cluster.preferred_genres:
                    genre_pref = cluster.preferred_genres[genre_id_str]

                    # Handle different preference data structures
                    if isinstance(genre_pref, dict):
                        score = genre_pref.get('preference_score', 0.5)
                    elif isinstance(genre_pref, (int, float)):
                        score = float(genre_pref)
                    else:
                        score = 0.5

                    total_score += score
                    genre_count += 1

            if genre_count == 0:
                return 0.5  # No preference data available

            return total_score / genre_count

        except Exception as e:
            logger.warning(f"Error calculating age preference score: {e}")
            return 0.5

    def _calculate_gender_preference_score(self, movie, cluster) -> float:
        """Calculate gender-based preference score từ DATA THỰC TẾ (không hardcode)"""
        try:
            # Sử dụng cluster.preferred_genres (đã học từ data thực tế)
            return self._calculate_age_preference_score(movie, cluster)

        except Exception as e:
            logger.warning(f"Error calculating gender preference score: {e}")
            return 0.5

    def _calculate_occupation_preference_score(self, movie, cluster) -> float:
        """Calculate occupation-based preference score từ DATA THỰC TẾ (không hardcode)"""
        try:
            # Sử dụng cluster.preferred_genres (đã học từ data thực tế)
            return self._calculate_age_preference_score(movie, cluster)

        except Exception as e:
            logger.warning(f"Error calculating occupation preference score: {e}")
            return 0.5

    def _calculate_location_preference_score(self, movie, cluster) -> float:
        """Calculate location-based preference score từ DATA THỰC TẾ (không hardcode)"""
        try:
            # Sử dụng cluster.preferred_genres (đã học từ data thực tế)
            return self._calculate_age_preference_score(movie, cluster)

        except Exception as e:
            logger.warning(f"Error calculating location preference score: {e}")
            return 0.5

    def _store_recommendations(self, user, recommendations: List[Dict], rec_type: str, context: str):
        """Store recommendations in database (same as collaborative filtering)"""
        try:
            # Clear existing recommendations for this user/type/context
            RecommendationResult.objects.filter(
                user=user,
                recommendation_type=rec_type,
                context=context
            ).delete()

            # Create new recommendations
            recommendation_objects = []
            existing_pairs = set()

            for rank, rec in enumerate(recommendations, 1):
                # Convert all values to ensure JSON serialization
                predicted_rating = float(rec.get('predicted_rating', 0)) if rec.get('predicted_rating') is not None else None
                confidence_score = float(rec.get('confidence', 0.5))
                novelty_score = float(rec.get('novelty_score', 0.5))
                score = float(rec['score']) if isinstance(rec['score'], (int, float, str)) else 0.5

                # Ensure explanation is JSON serializable
                explanation = rec.get('explanation', {})
                if isinstance(explanation, dict):
                    # Convert any Decimal values to float recursively
                    def convert_decimals(obj):
                        if hasattr(obj, '__float__'):
                            return float(obj)
                        elif isinstance(obj, dict):
                            return {key: convert_decimals(value) for key, value in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_decimals(item) for item in obj]
                        else:
                            return obj

                    explanation = convert_decimals(explanation)

                if getattr(rec['movie'], 'id') in existing_pairs:
                    continue
                recommendation_objects.append(RecommendationResult(
                    user=user,
                    movie=rec['movie'],
                    recommendation_type=rec_type,
                    context=context,
                    predicted_rating=predicted_rating,
                    confidence_score=confidence_score,
                    novelty_score=novelty_score,
                    rank=rank,
                    score=score,
                    explanation=explanation
                ))

            RecommendationResult.objects.bulk_create(recommendation_objects)

        except Exception as e:
            logger.error(f"Error storing recommendations: {str(e)}")
            import traceback
            traceback.print_exc()

    def generate_enhanced_demographic_recommendations(self, user, limit: int = 20,
                                                    context: str = 'homepage', store: bool = False) -> List[Movie]:
        """
        Generate enhanced demographic recommendations using K-means clustering and similar users
        """
        try:
            # Check if we have recent stored recommendations first
            from django.utils import timezone
            from datetime import timedelta

            # Check cache with longer timeout để tránh regenerate quá thường xuyên
            recent_cutoff = timezone.now() - timedelta(hours=24)  # Tăng từ 1 giờ lên 24 giờ
            stored_recommendations = RecommendationResult.objects.filter(
                user=user,
                recommendation_type='demographic',
                context=context,
                created_at__gte=recent_cutoff
            ).select_related('movie').order_by('rank')[:limit]

            if stored_recommendations.exists():
                logger.info(f"✅ Using cached demographic recommendations for user {user.id} (from {stored_recommendations.first().created_at})")
                return [rec.movie for rec in stored_recommendations]

            # Log cache miss cho debugging
            logger.info(f"❌ No cached demographic recommendations found for user {user.id} (cutoff: {recent_cutoff})")

            logger.info(f"Generating enhanced demographic recommendations for user {user.id}")

            # Track recommendation generation
            metrics_service.track_recommendation_generation(
                recommendation_type='demographic',
                user_count=1,
                movie_count=limit,
                context=context
            )

            # Get user's demographic cluster
            user_cluster = self.get_user_kmeans_cluster(user)
            if not user_cluster:
                logger.warning(f"User {user.id} not assigned to any demographic cluster")
                return []

            # Get similar users from the same cluster
            similar_users = self._get_similar_users_from_cluster(user, user_cluster, limit=20)
            if not similar_users:
                logger.warning(f"No similar users found in cluster {user_cluster} for user {user.id}")
                logger.info(f"Using cluster-based cold start logic for user {user.id}")
                # Pass empty list - cold start logic sẽ handle trong _generate_recommendations
                similar_users = []

            # Generate recommendations from similar users (handles cold start internally)
            recommendations = self._generate_recommendations_from_similar_users(
                user, similar_users, limit=limit
            )

            # Apply enhanced demographic scoring
            enhanced_recommendations = self._apply_enhanced_demographic_scoring(
                user, recommendations
            )

            # Sort by final score
            enhanced_recommendations.sort(key=lambda x: x['final_score'], reverse=True)
            top_recommendations = enhanced_recommendations[:limit]

            # Store recommendations if requested
            if store:
                self._store_enhanced_recommendations(user, top_recommendations, context)

            # Return movie objects
            return [rec['movie'] for rec in top_recommendations]

        except Exception as e:
            logger.error(f"Error generating enhanced demographic recommendations: {str(e)}")
            return []

    def _generate_recommendations_from_similar_users(self, target_user,
                                                   similar_users: List[Tuple],
                                                   limit: int) -> List[Dict]:
        """
        Generate candidate recommendations from similar users
        FIXED: Theo lý thuyết Demographic Filtering - xử lý cold start
        """
        try:
            # Get movies user has already interacted with
            user_movie_ids = set(MovieReview.objects.filter(
                user=target_user,
                review_type='USER'
            ).values_list('movie_id', flat=True))

            # Collect candidate movies from similar users
            candidate_movies = defaultdict(list)
            users_with_ratings = []

            # First pass: collect movies from similar users who have ratings
            for similar_user, similarity_score in similar_users:
                similar_user_ratings = MovieReview.objects.filter(
                    user=similar_user,
                    review_type='USER',
                    rating__gte=4.0,
                    rating__isnull=False
                ).exclude(
                    movie_id__in=user_movie_ids
                ).select_related('movie')

                if similar_user_ratings.exists():
                    users_with_ratings.append((similar_user, similarity_score))
                    for rating in similar_user_ratings:
                        rating_value = float(rating.rating) if rating.rating else 0.0
                        weighted_score = rating_value * similarity_score
                        candidate_movies[rating.movie].append({
                            'weighted_score': weighted_score,
                            'similarity': similarity_score,
                            'rating': rating_value
                        })

            # If no similar users have ratings (cold start), use cluster-based approach
            if not users_with_ratings:
                logger.info(f"No ratings from similar users for cold start user {target_user.id}")
                # Get all users from target user's cluster who have ratings
                from apps.recommendations.models import UserPreference
                target_cluster = UserPreference.objects.filter(user=target_user).first()
                if target_cluster and target_cluster.demographic_cluster:
                    cluster_users = User.objects.filter(
                        recommendation_preference__demographic_cluster=target_cluster.demographic_cluster
                    ).exclude(id=target_user.id)

                    cluster_ratings = MovieReview.objects.filter(
                        user__in=cluster_users,
                        review_type='USER',
                        rating__gte=4.0,
                        rating__isnull=False
                    ).exclude(
                        movie_id__in=user_movie_ids
                    ).select_related('movie')

                    for rating in cluster_ratings:
                        rating_value = float(rating.rating) if rating.rating else 0.0
                        # Use average similarity for cluster members
                        default_similarity = 0.5
                        weighted_score = rating_value * default_similarity
                        candidate_movies[rating.movie].append({
                            'weighted_score': weighted_score,
                            'similarity': default_similarity,
                            'rating': rating_value
                        })

            # Calculate final scores for candidates
            recommendations = []

            for movie, scores in candidate_movies.items():
                # Check if user has ratings to determine threshold
                user_has_ratings = MovieReview.objects.filter(
                    user=target_user,
                    review_type='USER',
                    rating__isnull=False
                ).exists()

                # Lower threshold for new users (1 user) vs users with ratings (2 users)
                min_support = 1 if not user_has_ratings else 2

                if len(scores) >= min_support:
                    avg_weighted_score = np.mean([s['weighted_score'] for s in scores])
                    avg_similarity = np.mean([s['similarity'] for s in scores])
                    # Weighted average rating theo similarity để dự đoán rating hợp lý hơn
                    sum_w = sum(s['similarity'] for s in scores) or 1.0
                    weighted_avg_rating = sum((s['rating'] * s['similarity']) for s in scores) / sum_w
                    avg_rating = weighted_avg_rating
                    support = len(scores)

                    recommendations.append({
                        'movie': movie,
                        'avg_weighted_score': avg_weighted_score,
                        'avg_similarity': avg_similarity,
                        'avg_rating': avg_rating,
                        'support': support,
                        'confidence': min(1.0, support / 5.0)
                    })

            # Sort by weighted score and take top candidates
            recommendations.sort(key=lambda x: x['avg_weighted_score'], reverse=True)
            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error generating recommendations from similar users: {str(e)}")
            return []

    def _apply_enhanced_demographic_scoring(self, user, recommendations: List[Dict]) -> List[Dict]:
        """Apply enhanced demographic-specific scoring to recommendations"""
        try:
            # Get user's demographic cluster if exists
            user_cluster = self._get_user_demographic_cluster(user)

            for rec in recommendations:
                demographic_bonus = 0.0

                if user_cluster:
                    # Get movie's popularity in user's demographic cluster
                    cluster_users = User.objects.filter(
                        recommendation_preference__demographic_cluster=user_cluster.cluster_id
                    )

                    if cluster_users.exists():
                        cluster_ratings = MovieReview.objects.filter(
                            user__in=cluster_users,
                            movie=rec['movie'],
                            review_type='USER',
                            rating__isnull=False
                        ).aggregate(
                            avg_rating=Avg('rating'),
                            count=Count('rating')
                        )

                        if cluster_ratings['count'] and cluster_ratings['count'] >= 3:
                            # Bonus based on cluster popularity
                            avg_rating = float(cluster_ratings['avg_rating']) if cluster_ratings['avg_rating'] else 0.0
                            cluster_score = avg_rating / 5.0
                            demographic_bonus = cluster_score * 0.2

                # Calculate enhanced final score
                base_score = rec['avg_weighted_score']
                confidence_bonus = rec['confidence'] * 0.1
                support_bonus = min(rec['support'] / 10, 0.1)
                similarity_bonus = rec['avg_similarity'] * 0.1

                final_score = base_score + demographic_bonus + confidence_bonus + support_bonus + similarity_bonus

                rec['demographic_bonus'] = demographic_bonus
                rec['similarity_bonus'] = similarity_bonus
                rec['final_score'] = final_score
                # Ensure predicted_rating present (use avg_rating ~ 0..5 when available)
                if rec.get('predicted_rating') is None:
                    avg_rating_val = rec.get('avg_rating')
                    rec['predicted_rating'] = float(min(5.0, max(1.0, float(avg_rating_val)))) if avg_rating_val is not None else None
                # Calculate component scores cho enhanced explanations
                if user_cluster:
                    age_score = self._calculate_age_preference_score(rec['movie'], user_cluster)
                    gender_score = self._calculate_gender_preference_score(rec['movie'], user_cluster)
                    occupation_score = self._calculate_occupation_preference_score(rec['movie'], user_cluster)
                    location_score = self._calculate_location_preference_score(rec['movie'], user_cluster)
                    composite_demographic_score = self._calculate_demographic_score(rec['movie'], user_cluster)
                else:
                    age_score = gender_score = occupation_score = location_score = composite_demographic_score = 0.5

                # Attach enhanced explanation details với component breakdown
                if not rec.get('explanation'):
                    rec['explanation'] = {
                        'type': 'enhanced_demographic',
                        'cluster': getattr(user_cluster, 'cluster_id', None) if user_cluster else None,
                        'cluster_name': getattr(user_cluster, 'name', None) if user_cluster else None,
                        'base_scores': {
                            'avg_weighted_score': round(rec.get('avg_weighted_score', 0), 3),
                            'avg_similarity': round(rec.get('avg_similarity', 0), 3),
                            'avg_rating': round(rec.get('avg_rating', 0), 3),
                            'support': rec.get('support', 0)
                        },
                        'demographic_analysis': {
                            'age_score': round(age_score, 3),
                            'gender_score': round(gender_score, 3),
                            'occupation_score': round(occupation_score, 3),
                            'location_score': round(location_score, 3),
                            'composite_score': round(composite_demographic_score, 3)
                        },
                        'scoring_components': {
                            'demographic_bonus': round(demographic_bonus, 3),
                            'similarity_bonus': round(similarity_bonus, 3),
                            'confidence_bonus': round(confidence_bonus, 3),
                            'support_bonus': round(support_bonus, 3)
                        },
                        'calculation': f'base({base_score:.3f}) + demo({demographic_bonus:.3f}) + conf({confidence_bonus:.3f}) + support({support_bonus:.3f}) + sim({similarity_bonus:.3f}) = {final_score:.3f}',
                        'final_score': round(final_score, 3)
                    }

            return recommendations

        except Exception as e:
            logger.error(f"Error applying enhanced demographic scoring: {str(e)}")
            return recommendations

    def _store_enhanced_recommendations(self, user, recommendations: List[Dict], context: str):
        """Store enhanced recommendations in database"""
        try:
            # Clear existing demographic recommendations
            RecommendationResult.objects.filter(
                user=user,
                recommendation_type='demographic',
                context=context
            ).delete()

            # Create new recommendations
            recommendation_objects = []

            for rank, rec in enumerate(recommendations, 1):
                # Convert all values to ensure JSON serialization
                predicted_rating = float(rec.get('predicted_rating', 0)) if rec.get('predicted_rating') is not None else None
                confidence_score = float(rec.get('confidence', 0.5))
                novelty_score = float(rec.get('novelty_score', 0.5))
                score = float(rec.get('final_score', rec.get('avg_weighted_score', 0.5))) if isinstance(rec.get('final_score', rec.get('avg_weighted_score', 0.5)), (int, float, str)) else 0.5

                # Ensure explanation is JSON serializable
                explanation = rec.get('explanation', {})
                if isinstance(explanation, dict):
                    # Convert any Decimal values to float recursively
                    def convert_decimals(obj):
                        if hasattr(obj, '__float__'):
                            return float(obj)
                        elif isinstance(obj, dict):
                            return {key: convert_decimals(value) for key, value in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_decimals(item) for item in obj]
                        else:
                            return obj

                    explanation = convert_decimals(explanation)

                recommendation_objects.append(
                    RecommendationResult(
                        user=user,
                        movie=rec['movie'],
                        recommendation_type='demographic',
                        context=context,
                        predicted_rating=predicted_rating,
                        confidence_score=confidence_score,
                        novelty_score=novelty_score,
                        rank=rank,
                        score=score,
                        explanation=explanation
                    )
                )

            RecommendationResult.objects.bulk_create(recommendation_objects)

            logger.info(f"Stored {len(recommendation_objects)} enhanced demographic recommendations")

        except Exception as e:
            logger.error(f"Error storing enhanced recommendations: {str(e)}")
            import traceback
            traceback.print_exc()

    def _get_user_demographic_cluster(self, user) -> Optional[DemographicCluster]:
        """Get user's demographic cluster"""
        try:
            # Check if user has preference with demographic cluster
            user_preference = UserPreference.objects.filter(user=user).first()
            if user_preference and user_preference.demographic_cluster:
                return DemographicCluster.objects.filter(
                    cluster_id=user_preference.demographic_cluster
                ).first()

            # If no cluster assigned, find best matching cluster based on demographics
            matching_clusters = DemographicCluster.objects.filter(
                age_range_min__lte=user.age or 25,
                age_range_max__gte=user.age or 25,
                primary_gender=user.gender
            )

            return matching_clusters.first()

        except Exception as e:
            logger.error(f"Error getting user demographic cluster: {str(e)}")
            return None

    def _get_stored_recommendations(self, user, context: str = 'homepage'):
        """Get stored recommendations for user"""
        from .models import RecommendationResult
        return RecommendationResult.objects.filter(
            user=user,
            recommendation_type='demographic',
            context=context
        ).order_by('-created_at')

    def _get_similar_users_from_cluster(self, user, cluster, limit=20):
        """
        Get similar users from the same demographic cluster
        FIXED: Theo lý thuyết Demographic Filtering - KHÔNG cần user mới có ratings
        """
        try:
            # Get ALL users from the same cluster (demographic principle)
            cluster_users = User.objects.filter(
                recommendation_preference__demographic_cluster=cluster.cluster_id
            ).exclude(id=user.id)[:limit * 2]  # Get more candidates

            if not cluster_users.exists():
                logger.warning(f"No users found in cluster {cluster}")
                return []

            # Calculate similarities based on demographic vectors only
            similar_users = []
            target_user_vector = self.vectorizer.create_demographic_vector(user)

            for other_user in cluster_users:
                other_vector = self.vectorizer.create_demographic_vector(other_user)
                similarity = cosine_similarity([target_user_vector], [other_vector])[0][0]

                if similarity > self.similarity_threshold:
                    similar_users.append((other_user, similarity))

            # Sort by similarity
            similar_users.sort(key=lambda x: x[1], reverse=True)

            logger.info(f"Found {len(similar_users)} similar users in cluster {cluster}")
            return similar_users[:limit]

        except Exception as e:
            logger.error(f"Error getting similar users from cluster: {str(e)}")
            return []

class HybridRecommendationService:
    """
    Hybrid recommendation service combining multiple filtering methods
    """

    def __init__(self):
        self.collaborative_service = CollaborativeFilteringService()
        self.demographic_service = EnhancedDemographicFilteringService()
        self.weights = {
            'collaborative': 0.5,
            'demographic': 0.4,
            'trending': 0.1
        }
        self.store_min_count = 20  # số lượng tối thiểu cần lưu để cache có ý nghĩa
        self.df_min_count_to_store = 10  # cần tối thiểu X phim DF trước khi lưu hybrid

    @staticmethod
    def _is_profile_complete(user) -> bool:
        """Check minimal profile required for demographic & hybrid to be meaningful."""
        return getattr(user, 'age', None) is not None and getattr(user, 'gender', None) is not None

    def generate_hybrid_recommendations(self, user, limit=20, context='homepage') -> List[any]:
        """
        Generate hybrid recommendations combining multiple methods
        """
        try:
            # Check cache first using unified cache service
            cached_recommendations = RecommendationCacheService.get_cached_recommendations(
                user, 'hybrid', context, limit
            )

            if cached_recommendations:
                return cached_recommendations

            # Track recommendation generation
            logger.info(f"🔄 Generating NEW hybrid recommendations for user {user.id} (no cache found)")
            metrics_service.track_recommendation_generation(
                recommendation_type='hybrid',
                user_count=1,
                movie_count=limit,
                context=context
            )

            all_recommendations = {}

            # Get collaborative filtering recommendations
            collaborative_recs = self.collaborative_service.generate_collaborative_recommendations(
                user, limit=limit*2, context=context
            )

            # Get ENHANCED demographic filtering recommendations (with behavioral features)
            demographic_recs = self.demographic_service.generate_enhanced_demographic_recommendations(
                user, limit=limit*2, context=context, store=False
            )

            # Get trending recommendations
            trending_recs = self._get_trending_recommendations(user, limit=limit//2)

            # Guard: If profile incomplete and no CF/DF yet, return trending only (do not store as hybrid)
            if not self._is_profile_complete(user) and not collaborative_recs and not demographic_recs:
                logger.info("⏳ Profile incomplete and no CF/DF candidates. Returning trending only without storing hybrid meta.")
                return trending_recs

            # Combine recommendations with weights
            for movie in collaborative_recs:
                if movie.id not in all_recommendations:
                    all_recommendations[movie.id] = {
                        'movie': movie,
                        'score': 0.0,
                        'methods': []
                    }
                all_recommendations[movie.id]['score'] += self.weights['collaborative']
                all_recommendations[movie.id]['methods'].append('collaborative')

            for movie in demographic_recs:
                if movie.id not in all_recommendations:
                    all_recommendations[movie.id] = {
                        'movie': movie,
                        'score': 0.0,
                        'methods': []
                    }
                all_recommendations[movie.id]['score'] += self.weights['demographic']
                all_recommendations[movie.id]['methods'].append('demographic')



            for movie in trending_recs:
                if movie.id not in all_recommendations:
                    all_recommendations[movie.id] = {
                        'movie': movie,
                        'score': 0.0,
                        'methods': []
                    }
                all_recommendations[movie.id]['score'] += self.weights['trending']
                all_recommendations[movie.id]['methods'].append('trending')

            # Sort by combined score
            sorted_recommendations = sorted(
                all_recommendations.values(),
                key=lambda x: x['score'],
                reverse=True
            )

            # Quy ước: luôn chuẩn bị nhiều hơn để lưu cache (tránh trường hợp chỉ lưu 1 phim khi limit nhỏ)
            store_count = max(limit, self.store_min_count)

            # Prepare for storage with full metadata
            final_recommendations = []
            for rec in sorted_recommendations[:store_count]:
                # Calculate predicted rating based on methods used with conditional logic
                predicted_rating = None
                methods = rec['methods']
                hybrid_score = rec['score']

                # Priority-based predicted rating calculation
                if 'collaborative' in methods:
                    # If has Collaborative: Base Rating = 3.5, Multiplier = 1.5
                    base_rating = 3.5
                    multiplier = 1.5
                elif 'demographic' in methods:
                    # If has Demographic: Base_Rating = 3.0, Multiplier = 2.0
                    base_rating = 3.0
                    multiplier = 2.0
                elif 'trending' in methods:
                    # If only has Trending: Base_Rating = 2.5, Multiplier = 2.5
                    base_rating = 2.5
                    multiplier = 2.5
                else:
                    # Fallback case
                    base_rating = 2.5
                    multiplier = 2.5

                predicted_rating = min(5.0, base_rating + hybrid_score * multiplier)

                # Calculate confidence score based on methods used
                # Weights: w_CF = 0.5, w_DF = 0.4, w_TR = 0.1
                method_weights = {
                    'collaborative': 0.5,
                    'demographic': 0.4,
                    'trending': 0.1
                }
                confidence = min(1.0, sum(method_weights.get(method, 0.0) for method in methods))

                # Calculate novelty score
                # novelty = 0.5 + (0.3 if trending in methods else 0.0)
                novelty = 0.5 + (0.3 if 'trending' in methods else 0.0)

                final_recommendations.append({
                    'movie': rec['movie'],
                    'score': rec['score'],
                    'predicted_rating': predicted_rating,
                    'confidence': confidence,
                    'novelty_score': novelty,
                    'explanation': {
                        'type': 'hybrid',
                        'methods': rec['methods'],
                        'methods_count': len(rec['methods']),
                        'hybrid_score': hybrid_score,
                        'predicted_rating': predicted_rating,
                        'predicted_rating_calculation': f'min(5.0, {base_rating} + {hybrid_score:.3f} × {multiplier}) = {predicted_rating:.2f}',
                        'confidence_score': confidence,
                        'confidence_calculation': f'min(1.0, {" + ".join([f"{method_weights.get(m, 0.0)}" for m in methods])}) = {confidence:.2f}',
                        'novelty_score': novelty,
                        'novelty_calculation': f'0.5 + {"0.3" if "trending" in methods else "0.0"} = {novelty:.1f}',
                        'algorithm_count': len(rec['methods'])
                    }
                })

            # Store hybrid recommendations using proper method
            # Don't auto-store - let the calling code handle storage
            # self.demographic_service._store_recommendations(
            #     user, final_recommendations, 'hybrid', context
            # )

            # Return list of Movie objects
            # Decide whether to store: skip nếu profile chưa đủ, trending-only, chưa có DF gần đây, hoặc DF quá ít
            trending_only = all((rec.get('methods') == ['trending']) for rec in final_recommendations)
            has_recent_df = RecommendationResult.objects.filter(
                user=user,
                recommendation_type='demographic',
                context=context,
                created_at__gte=timezone.now() - timedelta(minutes=5)
            ).exists()

            enough_df_candidates = len(demographic_recs) >= self.df_min_count_to_store

            # Relaxed: ignore `has_recent_df` gating to allow storing when DF pool is sufficient
            if self._is_profile_complete(user) and not trending_only and enough_df_candidates:
                # Store recommendations using unified cache service
                RecommendationCacheService.store_recommendations(user, final_recommendations, 'hybrid', context)
            else:
                logger.info("ℹ️ Skip storing hybrid (profile incomplete / no recent DF / trending-only / DF too few) to prevent rank pollution.")

            # Return: trả theo limit yêu cầu (nếu DF còn ít, ưu tiên trả trending để UI không rỗng)
            had_cache = bool(cached_recommendations)
            if had_cache:
                return cached_recommendations
            if enough_df_candidates:
                return [rec['movie'] for rec in final_recommendations[:limit]]
            else:
                # DF chưa đủ → trả trending-only không lưu
                return trending_recs[:limit]

        except Exception as e:
            logger.error(f"Error generating hybrid recommendations: {str(e)}")
            return []



    def _get_trending_recommendations(self, user, limit=10) -> List[any]:
        """Get trending movies for diversity"""
        try:
            # Get user's already rated movies
            user_rated_movies = set(MovieReview.objects.filter(
                user=user,
                review_type='USER'
            ).values_list('movie_id', flat=True))

            # Get trending movies (based on recent interactions)
            trending_movies = Movie.objects.filter(
                user_interactions__timestamp__gte=timezone.now() - timedelta(days=7),
                poster_url__isnull=False
            ).exclude(
                id__in=user_rated_movies
            ).annotate(
                interaction_count=Count('user_interactions')
            ).order_by('-interaction_count')[:limit]

            return list(trending_movies)

        except Exception as e:
            logger.error(f"Error getting trending recommendations: {str(e)}")
            return []


# ============================================================================
# ENHANCED DEMOGRAPHIC FILTERING IMPLEMENTATION
# ============================================================================

class AdvancedDemographicVectorizer:
    """
    Advanced demographic feature engineering và vector hóa
    """

    def __init__(self):
        self.age_bins = [(0, 18), (18, 25), (25, 35), (35, 45), (45, 55), (55, 100)]
        self.occupation_groups = {
            'technical': ['engineer', 'programmer', 'scientist', 'technician', 'developer'],
            'creative': ['artist', 'writer', 'designer', 'musician', 'photographer'],
            'business': ['manager', 'executive', 'sales', 'marketing', 'administrator'],
            'education': ['teacher', 'professor', 'academic', 'researcher'],
            'healthcare': ['doctor', 'nurse', 'medical', 'therapist'],
            'service': ['retail', 'hospitality', 'customer service', 'support'],
            'manual': ['construction', 'manufacturing', 'maintenance', 'labor'],
            'other': ['student', 'retired', 'unemployed', 'homemaker', 'other']
        }

        self.location_regions = {
            'north_america': ['US', 'CA', 'MX'],
            'europe': ['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI'],
            'asia': ['JP', 'KR', 'CN', 'IN'],
            'southeast_asia': ['VN', 'SG', 'MY', 'ID', 'PH', 'TH', 'TW', 'HK'],
            'other': []
        }

        self.encoders = {}
        self.scalers = {}

    def create_demographic_vector(self, user) -> np.ndarray:
        """
        Tạo vector demographic comprehensive cho user với error handling

        Returns:
            np.ndarray: Vector representing user demographics
        """
        try:
            features = []

            # 1. Age features (one-hot encoded bins)
            age_vector = self._encode_age_bins(user.age)
            features.extend(age_vector)

            # 2. Gender features (one-hot)
            gender_vector = self._encode_gender(user.gender)
            features.extend(gender_vector)

            # 3. Occupation group features
            occupation_vector = self._encode_occupation_groups(user.occupation)
            features.extend(occupation_vector)

            # 4. Geographic features
            location_vector = self._encode_location(user.location, user.zip_code)
            features.extend(location_vector)

            # 5. User type features
            user_type_vector = self._encode_user_type(user.user_type)
            features.extend(user_type_vector)

            # 6. Behavioral features (if available)
            behavioral_vector = self._encode_behavioral_features(user)
            features.extend(behavioral_vector)

            # Ensure all features are numeric and have consistent length
            numeric_features = []
            for feature in features:
                if isinstance(feature, (list, tuple)):
                    numeric_features.extend([float(x) if x is not None else 0.0 for x in feature])
                else:
                    numeric_features.append(float(feature) if feature is not None else 0.0)

            return np.array(numeric_features, dtype=np.float64)

        except Exception as e:
            # Fallback: return simple age/gender vector
            logger.warning(f"Error creating demographic vector for user {user.id}: {str(e)}")
            age_normalized = min(user.age / 100.0, 1.0) if user.age else 0.5
            gender_encoded = 1.0 if user.gender == 'M' else 0.0
            return np.array([age_normalized, gender_encoded], dtype=np.float64)

    def _encode_age_bins(self, age) -> List[float]:
        """Encode age into bins using one-hot encoding"""
        if not age:
            return [0.0] * len(self.age_bins)

        age_vector = []
        for min_age, max_age in self.age_bins:
            if min_age <= age < max_age:
                age_vector.append(1.0)
            else:
                age_vector.append(0.0)
        return age_vector

    def _encode_gender(self, gender) -> List[float]:
        """One-hot encode gender"""
        gender_options = ['M', 'F', 'O']
        gender_vector = []

        for option in gender_options:
            if gender == option:
                gender_vector.append(1.0)
            else:
                gender_vector.append(0.0)

        return gender_vector

    def _encode_occupation_groups(self, occupation) -> List[float]:
        """Encode occupation into predefined groups"""
        if not occupation:
            return [0.0] * len(self.occupation_groups)

        occupation_lower = occupation.lower()
        occupation_vector = []

        for group_name, group_occupations in self.occupation_groups.items():
            # Check if user's occupation matches any in this group
            match = any(occ in occupation_lower for occ in group_occupations)
            occupation_vector.append(1.0 if match else 0.0)

        return occupation_vector

    def _encode_location(self, location, zip_code) -> List[float]:
        """Encode geographic location with improved country mapping"""
        location_vector = [0.0] * len(self.location_regions)

        if location or zip_code:
            # Country name to code mapping
            country_mapping = {
                'Vietnam': 'VN', 'Việt Nam': 'VN', 'VIETNAM': 'VN',
                'Singapore': 'SG', 'Singapura': 'SG', 'SINGAPORE': 'SG',
                'Thailand': 'TH', 'ประเทศไทย': 'TH', 'THAILAND': 'TH',
                'Malaysia': 'MY', 'MALAYSIA': 'MY',
                'Indonesia': 'ID', 'INDONESIA': 'ID',
                'Philippines': 'PH', 'Pilipinas': 'PH', 'PHILIPPINES': 'PH',
                'Taiwan': 'TW', 'TAIWAN': 'TW',
                'Hong Kong': 'HK', 'HONG KONG': 'HK',
                'United Kingdom': 'GB', 'UK': 'GB', 'UNITED KINGDOM': 'GB',
                'Japan': 'JP', 'JAPAN': 'JP',
                'South Korea': 'KR', 'Korea': 'KR', 'SOUTH KOREA': 'KR',
                'China': 'CN', 'CHINA': 'CN',
                'India': 'IN', 'INDIA': 'IN',
                'United States': 'US', 'USA': 'US', 'UNITED STATES': 'US',
                'Canada': 'CA', 'CANADA': 'CA',
                'Mexico': 'MX', 'MEXICO': 'MX',
                'Germany': 'DE', 'GERMANY': 'DE',
                'France': 'FR', 'FRANCE': 'FR',
                'Italy': 'IT', 'ITALY': 'IT',
                'Spain': 'ES', 'SPAIN': 'ES',
            }

            # Create location string
            location_str = f"{location or ''} {zip_code or ''}".upper()

            # Map country names to codes
            mapped_location = location_str
            for country_name, country_code in country_mapping.items():
                if country_name.upper() in location_str:
                    mapped_location = location_str.replace(country_name.upper(), country_code)
                    break

            # Check regions with improved matching
            import re
            # Split by spaces and remove punctuation, then filter out empty strings
            location_words = [word.strip() for word in re.split(r'[,\s]+', mapped_location) if word.strip()]

            for i, (region, countries) in enumerate(self.location_regions.items()):
                for country in countries:
                    if country in location_words:  # Word-based matching
                        location_vector[i] = 1.0
                        return location_vector

            # Default to 'other' if no match
            location_vector[-1] = 1.0

        return location_vector

    def _encode_user_type(self, user_type) -> List[float]:
        """Encode user membership type"""
        user_types = ['member', 'premium_basic', 'premium_standard', 'premium_vip']
        user_type_vector = []

        for utype in user_types:
            if user_type == utype:
                user_type_vector.append(1.0)
            else:
                user_type_vector.append(0.0)

        return user_type_vector

    def _encode_behavioral_features(self, user) -> List[float]:
        """Encode behavioral characteristics"""
        try:
            # Get user's rating behavior
            user_reviews = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            )

            if not user_reviews.exists():
                return [0.0, 0.0, 0.0, 0.0]  # No behavioral data

            # Calculate behavioral metrics
            ratings = user_reviews.values_list('rating', flat=True)
            avg_rating = np.mean(ratings)
            rating_variance = np.var(ratings)
            rating_count = len(ratings)

            # Normalize behavioral features
            normalized_avg = (avg_rating - 1) / 4  # Scale 1-5 to 0-1
            normalized_variance = min(rating_variance / 2, 1.0)  # Cap variance
            normalized_count = min(rating_count / 100, 1.0)  # Cap count

            # Activity level (recent vs old ratings)
            recent_ratings = user_reviews.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()
            activity_level = min(recent_ratings / 10, 1.0)

            return [normalized_avg, normalized_variance, normalized_count, activity_level]

        except Exception as e:
            logger.error(f"Error encoding behavioral features: {str(e)}")
            return [0.0, 0.0, 0.0, 0.0]

    def get_feature_names(self) -> List[str]:
        """Get names of all features in the vector"""
        feature_names = []

        # Age bin names
        for min_age, max_age in self.age_bins:
            feature_names.append(f"age_{min_age}_{max_age}")

        # Gender names
        for gender in ['M', 'F', 'O']:
            feature_names.append(f"gender_{gender}")

        # Occupation group names
        for group in self.occupation_groups.keys():
            feature_names.append(f"occupation_{group}")

        # Location region names
        for region in self.location_regions.keys():
            feature_names.append(f"location_{region}")

        # User type names
        for utype in ['member', 'premium_basic', 'premium_standard', 'premium_vip']:
            feature_names.append(f"user_type_{utype}")

        # Behavioral feature names
        feature_names.extend(['avg_rating', 'rating_variance', 'rating_count', 'activity_level'])

        return feature_names


class AdvancedDemographicSimilarityCalculator:
    """
    Advanced demographic similarity calculation với multiple methods
    """

    def __init__(self, vectorizer: AdvancedDemographicVectorizer):
        self.vectorizer = vectorizer
        self.feature_weights = {
            'age': 0.25,
            'gender': 0.30,
            'occupation': 0.25,
            'location': 0.10,
            'user_type': 0.05,
            'behavioral': 0.05
        }

    def calculate_cosine_similarity(self, user1_vector: np.ndarray, user2_vector: np.ndarray) -> float:
        """Cosine similarity between demographic vectors"""
        try:
            if not SKLEARN_AVAILABLE:
                return 0.0
            similarity = cosine_similarity([user1_vector], [user2_vector])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0

    def calculate_euclidean_similarity(self, user1_vector: np.ndarray, user2_vector: np.ndarray) -> float:
        """Euclidean distance converted to similarity (0-1 scale)"""
        try:
            if not SKLEARN_AVAILABLE:
                return 0.0
            distance = euclidean_distances([user1_vector], [user2_vector])[0][0]
            # Convert distance to similarity (inverse relationship)
            max_distance = np.sqrt(len(user1_vector))  # Maximum possible distance
            similarity = 1 - (distance / max_distance)
            return max(0.0, float(similarity))
        except Exception as e:
            logger.error(f"Error calculating euclidean similarity: {str(e)}")
            return 0.0

    def calculate_weighted_similarity(self, user1, user2) -> float:
        """
        Weighted similarity với different importance cho features
        """
        try:
            total_similarity = 0.0
            total_weight = 0.0

            # Age similarity với Gaussian kernel
            if user1.age and user2.age:
                age_diff = abs(user1.age - user2.age)
                age_similarity = np.exp(-(age_diff ** 2) / (2 * 10 ** 2))  # sigma=10
                total_similarity += self.feature_weights['age'] * age_similarity
                total_weight += self.feature_weights['age']

            # Gender exact match
            if user1.gender and user2.gender:
                gender_similarity = 1.0 if user1.gender == user2.gender else 0.0
                total_similarity += self.feature_weights['gender'] * gender_similarity
                total_weight += self.feature_weights['gender']

            # Occupation group similarity
            if user1.occupation and user2.occupation:
                occupation_similarity = self._calculate_occupation_similarity(
                    user1.occupation, user2.occupation
                )
                total_similarity += self.feature_weights['occupation'] * occupation_similarity
                total_weight += self.feature_weights['occupation']

            # Location similarity
            if user1.location and user2.location:
                location_similarity = self._calculate_location_similarity(
                    user1.location, user2.location
                )
                total_similarity += self.feature_weights['location'] * location_similarity
                total_weight += self.feature_weights['location']

            # User type similarity
            user_type_similarity = 1.0 if user1.user_type == user2.user_type else 0.0
            total_similarity += self.feature_weights['user_type'] * user_type_similarity
            total_weight += self.feature_weights['user_type']

            # Behavioral similarity
            behavioral_similarity = self._calculate_behavioral_similarity(user1, user2)
            total_similarity += self.feature_weights['behavioral'] * behavioral_similarity
            total_weight += self.feature_weights['behavioral']

            return total_similarity / total_weight if total_weight > 0 else 0.0

        except Exception as e:
            logger.error(f"Error calculating weighted similarity: {str(e)}")
            return 0.0

    def _calculate_occupation_similarity(self, occupation1: str, occupation2: str) -> float:
        """Calculate similarity between occupations"""
        if occupation1 == occupation2:
            return 1.0

        # Check if they belong to the same occupation group
        occupation1_lower = occupation1.lower()
        occupation2_lower = occupation2.lower()

        for group_occupations in self.vectorizer.occupation_groups.values():
            in_group1 = any(occ in occupation1_lower for occ in group_occupations)
            in_group2 = any(occ in occupation2_lower for occ in group_occupations)

            if in_group1 and in_group2:
                return 0.7  # Same group but different specific occupation

        return 0.0  # Different groups

    def _calculate_location_similarity(self, location1: str, location2: str) -> float:
        """Calculate similarity between locations with improved logic"""
        if location1 == location2:
            return 1.0

        # Country name to code mapping (same as in _encode_location)
        country_mapping = {
            'Vietnam': 'VN', 'Việt Nam': 'VN', 'VIETNAM': 'VN',
            'Singapore': 'SG', 'Singapura': 'SG', 'SINGAPORE': 'SG',
            'Thailand': 'TH', 'ประเทศไทย': 'TH', 'THAILAND': 'TH',
            'Malaysia': 'MY', 'MALAYSIA': 'MY',
            'Indonesia': 'ID', 'INDONESIA': 'ID',
            'Philippines': 'PH', 'Pilipinas': 'PH', 'PHILIPPINES': 'PH',
            'Taiwan': 'TW', 'TAIWAN': 'TW',
            'Hong Kong': 'HK', 'HONG KONG': 'HK',
            'United Kingdom': 'GB', 'UK': 'GB', 'UNITED KINGDOM': 'GB',
            'Japan': 'JP', 'JAPAN': 'JP',
            'South Korea': 'KR', 'Korea': 'KR', 'SOUTH KOREA': 'KR',
            'China': 'CN', 'CHINA': 'CN',
            'India': 'IN', 'INDIA': 'IN',
            'United States': 'US', 'USA': 'US', 'UNITED STATES': 'US',
            'Canada': 'CA', 'CANADA': 'CA',
            'Mexico': 'MX', 'MEXICO': 'MX',
            'Germany': 'DE', 'GERMANY': 'DE',
            'France': 'FR', 'FRANCE': 'FR',
            'Italy': 'IT', 'ITALY': 'IT',
            'Spain': 'ES', 'SPAIN': 'ES',
        }

        # Map country names to codes for both locations
        location1_upper = location1.upper()
        location2_upper = location2.upper()

        mapped_location1 = location1_upper
        mapped_location2 = location2_upper

        for country_name, country_code in country_mapping.items():
            if country_name.upper() in location1_upper:
                mapped_location1 = location1_upper.replace(country_name.upper(), country_code)
            if country_name.upper() in location2_upper:
                mapped_location2 = location2_upper.replace(country_name.upper(), country_code)

        # Check if they're in the same region with word-based matching
        import re
        location1_words = re.findall(r'\b\w+\b', mapped_location1)
        location2_words = re.findall(r'\b\w+\b', mapped_location2)

        for region_countries in self.vectorizer.location_regions.values():
            in_region1 = any(country in location1_words for country in region_countries)
            in_region2 = any(country in location2_words for country in region_countries)

            if in_region1 and in_region2:
                return 0.6  # Same region

        return 0.0  # Different regions

    def _calculate_behavioral_similarity(self, user1, user2) -> float:
        """Calculate behavioral similarity between users"""
        try:
            # Get behavioral metrics for both users
            user1_stats = self._get_user_behavioral_stats(user1)
            user2_stats = self._get_user_behavioral_stats(user2)

            if not user1_stats or not user2_stats:
                return 0.5  # Neutral similarity if no data

            # Calculate similarity for each behavioral dimension
            avg_rating_sim = 1 - abs(user1_stats['avg_rating'] - user2_stats['avg_rating']) / 4
            variance_sim = 1 - abs(user1_stats['rating_variance'] - user2_stats['rating_variance']) / 2
            activity_sim = 1 - abs(user1_stats['activity_level'] - user2_stats['activity_level'])

            # Weighted average
            behavioral_similarity = (avg_rating_sim * 0.4 + variance_sim * 0.3 + activity_sim * 0.3)

            return max(0.0, min(1.0, behavioral_similarity))

        except Exception as e:
            logger.error(f"Error calculating behavioral similarity: {str(e)}")
            return 0.5

    def _get_user_behavioral_stats(self, user) -> Optional[Dict]:
        """Get behavioral statistics for a user"""
        try:
            user_reviews = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            )

            if not user_reviews.exists():
                return None

            ratings = list(user_reviews.values_list('rating', flat=True))

            # Recent activity level
            recent_count = user_reviews.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()

            return {
                'avg_rating': np.mean(ratings),
                'rating_variance': np.var(ratings),
                'rating_count': len(ratings),
                'activity_level': recent_count / 30 if recent_count > 0 else 0  # per day
            }

        except Exception as e:
            logger.error(f"Error getting user behavioral stats: {str(e)}")
            return None

class RecommendationMetricsService:
    """
    Service to track and analyze recommendation system performance metrics
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def track_recommendation_generation(self, recommendation_type: str, user_count: int,
                                      movie_count: int, context: str = 'homepage'):
        """Track when recommendations are generated"""
        try:
            date = timezone.now().date()
            metrics, created = RecommendationMetrics.objects.get_or_create(
                date=date,
                recommendation_type=recommendation_type,
                defaults={
                    'total_recommendations': 0,
                    'unique_users': 0,
                    'unique_movies': 0,
                }
            )

            if not created:
                metrics.total_recommendations += user_count * 20  # Assume 20 recs per user
                metrics.unique_users = max(metrics.unique_users, user_count)
                metrics.unique_movies = max(metrics.unique_movies, movie_count)

            metrics.save()
            self.logger.info(f"Tracked recommendation generation: {recommendation_type}, users: {user_count}")

        except Exception as e:
            self.logger.error(f"Error tracking recommendation generation: {e}")

    def track_user_engagement(self, user_id: int, recommendation_type: str,
                            action: str, movie_id: int = None):
        """Track user engagement with recommendations"""
        try:
            date = timezone.now().date()
            metrics, created = RecommendationMetrics.objects.get_or_create(
                date=date,
                recommendation_type=recommendation_type,
                defaults={
                    'total_recommendations': 0,
                    'unique_users': 0,
                    'unique_movies': 0,
                    'click_through_rate': 0.0,
                    'conversion_rate': 0.0,
                }
            )

            # Update engagement metrics based on action
            if action == 'click':
                metrics.click_through_rate = self._update_rate(metrics.click_through_rate, 1, 1)
            elif action == 'rate':
                metrics.conversion_rate = self._update_rate(metrics.conversion_rate, 1, 1)
                if movie_id:
                    # Track actual rating vs predicted
                    self._track_rating_accuracy(user_id, movie_id, recommendation_type)

            metrics.save()

        except Exception as e:
            self.logger.error(f"Error tracking user engagement: {e}")

    def _update_rate(self, current_rate: float, numerator: int, denominator: int) -> float:
        """Update rate metric with new data"""
        if current_rate == 0.0:
            return numerator / denominator
        else:
            # Simple moving average
            return (current_rate + (numerator / denominator)) / 2

    def _track_rating_accuracy(self, user_id: int, movie_id: int, recommendation_type: str):
        """Track rating prediction accuracy"""
        try:
            # Get predicted rating from RecommendationResult
            result = RecommendationResult.objects.filter(
                user_id=user_id,
                movie_id=movie_id,
                recommendation_type=recommendation_type
            ).first()

            if result and result.predicted_rating:
                # Get actual rating
                actual_rating = MovieReview.objects.filter(
                    user_id=user_id,
                    movie_id=movie_id,
                    review_type='USER',
                    rating__isnull=False
                ).first()

                if actual_rating and actual_rating.rating:
                    # Calculate error
                    error = abs(result.predicted_rating - actual_rating.rating)

                    # Update metrics
                    date = timezone.now().date()
                    metrics, created = RecommendationMetrics.objects.get_or_create(
                        date=date,
                        recommendation_type=recommendation_type,
                        defaults={
                            'rmse': 0.0,
                            'mae': 0.0,
                            'average_predicted_rating': 0.0,
                            'average_actual_rating': 0.0,
                        }
                    )

                    # Update accuracy metrics
                    metrics.mae = self._update_average(metrics.mae, error)
                    metrics.average_predicted_rating = self._update_average(
                        metrics.average_predicted_rating, result.predicted_rating
                    )
                    metrics.average_actual_rating = self._update_average(
                        metrics.average_actual_rating, actual_rating.rating
                    )

                    metrics.save()

        except Exception as e:
            self.logger.error(f"Error tracking rating accuracy: {e}")

    def _update_average(self, current_avg: float, new_value: float) -> float:
        """Update running average"""
        if current_avg == 0.0:
            return new_value
        else:
            # Simple moving average
            return (current_avg + new_value) / 2

    def calculate_diversity_metrics(self, recommendation_type: str, date: datetime.date = None):
        """Calculate diversity metrics for recommendations"""
        try:
            if not date:
                date = timezone.now().date()

            # Get recommendations for the day
            results = RecommendationResult.objects.filter(
                created_at__date=date,
                recommendation_type=recommendation_type
            ).select_related('movie')

            if not results.exists():
                return

            # Calculate intra-list diversity
            diversity_scores = []
            novelty_scores = []

            # Group by user
            user_recommendations = {}
            for result in results:
                if result.user_id not in user_recommendations:
                    user_recommendations[result.user_id] = []
                user_recommendations[result.user_id].append(result.movie)

            for user_id, movies in user_recommendations.items():
                if len(movies) < 2:
                    continue

                # Calculate genre diversity
                genres = set()
                for movie in movies:
                    genres.update(movie.genres.values_list('name', flat=True))

                diversity = len(genres) / len(movies) if movies else 0
                diversity_scores.append(diversity)

                # Calculate novelty (based on average rating count)
                avg_rating_count = sum(
                    movie.moviereview_set.filter(review_type='USER').count()
                    for movie in movies
                ) / len(movies)
                novelty = 1 / (1 + avg_rating_count / 100)  # Normalize
                novelty_scores.append(novelty)

            # Update metrics
            if diversity_scores:
                metrics, created = RecommendationMetrics.objects.get_or_create(
                    date=date,
                    recommendation_type=recommendation_type,
                    defaults={}
                )

                metrics.intra_list_diversity = sum(diversity_scores) / len(diversity_scores)
                metrics.novelty_score = sum(novelty_scores) / len(novelty_scores)
                metrics.save()

        except Exception as e:
            self.logger.error(f"Error calculating diversity metrics: {e}")

    def get_performance_summary(self, days: int = 7) -> Dict:
        """Get performance summary for the last N days"""
        try:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)

            metrics = RecommendationMetrics.objects.filter(
                date__range=[start_date, end_date]
            ).values('recommendation_type').annotate(
                avg_click_rate=Avg('click_through_rate'),
                avg_conversion_rate=Avg('conversion_rate'),
                avg_mae=Avg('mae'),
                avg_diversity=Avg('intra_list_diversity'),
                avg_novelty=Avg('novelty_score'),
                total_recommendations=Sum('total_recommendations'),
                total_users=Sum('unique_users')
            )

            return {
                'period': f"{start_date} to {end_date}",
                'metrics': list(metrics)
            }

        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {}

    def cleanup_old_metrics(self, days_to_keep: int = 90):
        """Clean up old metrics data"""
        try:
            cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)
            deleted_count = RecommendationMetrics.objects.filter(
                date__lt=cutoff_date
            ).delete()[0]

            self.logger.info(f"Cleaned up {deleted_count} old metrics records")

        except Exception as e:
            self.logger.error(f"Error cleaning up old metrics: {e}")

# Initialize global metrics service
metrics_service = RecommendationMetricsService()

class RecommendationCacheService:
    """
    Unified cache service for recommendation system
    """

    @staticmethod
    def get_cache_timeout():
        """Get cache timeout from settings"""
        return getattr(settings, 'RECOMMENDATION_CACHE_SETTINGS', {}).get('CACHE_TIMEOUT_HOURS', 24)

    @staticmethod
    def get_cached_recommendations(user, rec_type, context='homepage', limit=20):
        """
        Get cached recommendations with unified logic
        """
        try:
            cache_timeout = RecommendationCacheService.get_cache_timeout()
            recent_cutoff = timezone.now() - timedelta(hours=cache_timeout)

            # Check if context agnostic is enabled
            context_agnostic = getattr(settings, 'RECOMMENDATION_CACHE_SETTINGS', {}).get('CONTEXT_AGNOSTIC', True)

            if context_agnostic:
                # Ignore context when checking cache
                stored_recommendations = RecommendationResult.objects.filter(
                    user=user,
                    recommendation_type=rec_type,
                    created_at__gte=recent_cutoff
                ).select_related('movie').order_by('rank')[:limit]
            else:
                # Use context in cache check
                stored_recommendations = RecommendationResult.objects.filter(
                    user=user,
                    recommendation_type=rec_type,
                    context=context,
                    created_at__gte=recent_cutoff
                ).select_related('movie').order_by('rank')[:limit]

            if stored_recommendations.exists():
                logger.info(f"✅ Using cached {rec_type} recommendations for user {user.id} (created: {stored_recommendations.first().created_at})")
                return [rec.movie for rec in stored_recommendations]

            logger.info(f"❌ No cached {rec_type} recommendations found for user {user.id} (cutoff: {recent_cutoff})")
            return []

        except Exception as e:
            logger.error(f"Error getting cached recommendations: {str(e)}")
            return []

    @staticmethod
    def store_recommendations(user, recommendations, rec_type, context='homepage'):
        """
        Store recommendations with unified logic
        """
        try:
            # Check if we already have recent recommendations (within cache timeout)
            cache_timeout = RecommendationCacheService.get_cache_timeout()
            recent_cutoff = timezone.now() - timedelta(hours=cache_timeout)

            existing_qs = RecommendationResult.objects.filter(
                user=user,
                recommendation_type=rec_type,
                created_at__gte=recent_cutoff
            )

            if existing_qs.exists():
                # Update missing metadata instead of skipping entirely
                logger.info(
                    f"🔄 Updating existing {rec_type} recommendations metadata for user {user.id}"
                )
                # Build map from incoming recs
                incoming = {}
                for rank, rec in enumerate(recommendations, 1):
                    if isinstance(rec, dict):
                        incoming[getattr(rec['movie'], 'id')] = {
                            'rank': rank,
                            'score': rec.get('score'),
                            'predicted_rating': rec.get('predicted_rating'),
                            'confidence_score': rec.get('confidence'),
                            'explanation': rec.get('explanation', {}),
                        }
                    else:
                        incoming[getattr(rec, 'id')] = {
                            'rank': rank,
                            'score': getattr(rec, 'recommendation_score', None),
                            'predicted_rating': None,
                            'confidence_score': 0.5,
                            'explanation': {},
                        }

                to_update = []
                for er in existing_qs.select_related('movie'):
                    data = incoming.get(er.movie_id)
                    if not data:
                        continue
                    changed = False
                    # Only update if missing
                    if er.predicted_rating is None and data.get('predicted_rating') is not None:
                        er.predicted_rating = float(data['predicted_rating'])
                        changed = True
                    if (er.confidence_score is None or er.confidence_score == 0) and data.get('confidence_score') is not None:
                        er.confidence_score = float(data['confidence_score'])
                        changed = True
                    if (er.score is None or er.score == 0) and data.get('score') is not None:
                        er.score = float(data['score'])
                        changed = True
                    if (not er.explanation) and data.get('explanation'):
                        er.explanation = data['explanation']
                        changed = True
                    if changed:
                        to_update.append(er)

                if to_update:
                    RecommendationResult.objects.bulk_update(
                        to_update,
                        ['predicted_rating', 'confidence_score', 'score', 'explanation']
                    )
                return

            # No recent data: replace all
            RecommendationResult.objects.filter(
                user=user,
                recommendation_type=rec_type
            ).delete()

            # Store new recommendations fully
            for rank, rec in enumerate(recommendations, 1):
                if isinstance(rec, dict):
                    movie = rec['movie']
                    score = rec.get('score', 0.0)
                    confidence = rec.get('confidence', 0.5)
                    predicted_rating = rec.get('predicted_rating')
                    explanation = rec.get('explanation', {})
                else:
                    movie = rec
                    score = getattr(rec, 'recommendation_score', 0.0)
                    confidence = 0.5
                    predicted_rating = None
                    explanation = {}

                RecommendationResult.objects.create(
                    user=user,
                    movie=movie,
                    recommendation_type=rec_type,
                    context=context,
                    rank=rank,
                    score=score,
                    confidence_score=confidence,
                    predicted_rating=predicted_rating,
                    explanation=explanation
                )

            logger.info(f"✅ Stored {len(recommendations)} {rec_type} recommendations for user {user.id}")

        except Exception as e:
            logger.error(f"Error storing recommendations: {str(e)}")

class OptimizedKMeansProductionService:
    """
    🎯 Tối ưu K-means cho production với Render yếu
    Sử dụng hybrid approach: Pre-computed + Caching + Fallback
    """

    def __init__(self):
        self.cache_ttl = 3600 * 24 * 7  # 7 ngày thay vì 24 giờ
        self.batch_size = 500  # Nhỏ để tiết kiệm memory
        # Thiết lập mặc định K thích ứng cho production
        self.adaptive_k = True
        self.k_min = 4
        self.k_max = 12
        self.silhouette_sample_size = 5000
        self.max_clusters = 6  # Giá trị fallback nếu tắt adaptive
        self.memory_limit_mb = 256  # Giới hạn memory
        # Không cần redis_client vì sử dụng Django cache framework

    def _refresh_db_connection(self):
        """Đảm bảo kết nối DB còn sống trong các vòng lặp dài."""
        try:
            from django.db import close_old_connections, connection
            close_old_connections()
            # ensure_connection sẽ mở lại nếu đã đóng/timeout
            connection.ensure_connection()
        except Exception as e:
            # Chỉ log ở mức debug để tránh spam log
            logger.debug(f"Skip DB connection refresh: {e}")

    def train_offline_and_deploy(self, force_retrain=False):
        """
        🚀 Train offline và deploy model lên production
        Chỉ chạy trên development environment
        """
        if not settings.DEBUG and not force_retrain:
            logger.warning("Training chỉ được phép trên development")
            return False

        try:
            logger.info("🔄 Bắt đầu offline training...")

            # 1. Collect user data in batches
            users_data = self._collect_users_data_batches()

            # 2. Train model với memory optimization
            model = self._train_with_memory_optimization(users_data)

            # 3. Save model to multiple storages
            self._save_model_multi_storage(model)

            # 4. Pre-compute clusters cho tất cả users
            self._precompute_all_clusters(model)

            logger.info("✅ Offline training hoàn thành!")
            return True

        except Exception as e:
            logger.error(f"❌ Training failed: {str(e)}")
            return False

    def _collect_users_data_batches(self):
        """Collect user data theo batches để tiết kiệm memory"""
        users = User.objects.filter(
            age__isnull=False,
            gender__isnull=False
        ).values('id', 'age', 'gender')

        batches = []
        for i in range(0, users.count(), self.batch_size):
            batch = list(users[i:i+self.batch_size])
            batches.append(batch)

        return batches

    def _train_with_memory_optimization(self, users_batches):
        """Train với memory optimization và chọn K thích ứng (nếu bật)."""
        from sklearn.cluster import MiniBatchKMeans
        from sklearn.metrics import silhouette_score

        vectorizer = AdvancedDemographicVectorizer()

        # 1) Thu thập mẫu đặc trưng để chọn K (giới hạn sample để tiết kiệm bộ nhớ)
        sample_features = []
        sample_limit = self.silhouette_sample_size
        for batch in users_batches:
            # Làm mới kết nối per-batch để tránh "connection already closed"
            self._refresh_db_connection()
            if len(sample_features) >= sample_limit:
                break
            # Giảm N+1 queries: lấy toàn bộ user của batch bằng in_bulk
            try:
                user_ids = [u.get('id') for u in batch if u.get('id')]
                if not user_ids:
                    continue
                user_map = User.objects.only(
                    'id', 'age', 'gender', 'occupation', 'location', 'zip_code', 'user_type'
                ).in_bulk(user_ids)
            except Exception as e:
                logger.warning(f"Batch user fetch failed: {e}")
                continue

            for user_id in user_ids:
                if len(sample_features) >= sample_limit:
                    break
                user = user_map.get(user_id)
                if not user:
                    continue
                try:
                    fv = vectorizer.create_demographic_vector(user)
                    sample_features.append(fv)
                except Exception as e:
                    logger.warning(f"Error creating vector for user {user_id}: {e}")
                    continue

        optimal_k = self.max_clusters
        if self.adaptive_k and len(sample_features) >= max(100, self.k_min * 5):  # cần mẫu tối thiểu
            try:
                Xs = np.array(sample_features)
                k_lower = max(2, self.k_min)
                k_upper = min(self.k_max, len(Xs) - 1)
                if k_upper <= k_lower:
                    k_upper = max(k_lower + 1, 3)

                best_score = -1.0
                best_k = optimal_k
                batch_for_test = min(1000, len(Xs))

                for k in range(k_lower, k_upper + 1):
                    try:
                        mbk = MiniBatchKMeans(n_clusters=k, random_state=42, batch_size=batch_for_test, n_init=5)
                        labels = mbk.fit_predict(Xs)
                        score = silhouette_score(Xs, labels, sample_size=min(len(Xs), 5000))
                        if score > best_score:
                            best_score = score
                            best_k = k
                    except Exception as e:
                        logger.debug(f"Silhouette failed for k={k}: {e}")
                        continue

                optimal_k = best_k
                logger.info(f"✅ Adaptive K (production) chọn k={optimal_k} (silhouette={best_score:.4f})")
            except Exception as e:
                logger.warning(f"Adaptive K selection (production) failed, dùng mặc định {optimal_k}: {e}")

        # 2) Khởi tạo scaler (nếu có sample) và mô hình với K tối ưu, train qua toàn bộ batches bằng partial_fit
        scaler = None
        try:
            if 'Xs' in locals() and isinstance(Xs, np.ndarray) and Xs.size > 0:
                from sklearn.preprocessing import StandardScaler
                scaler = StandardScaler()
                scaler.fit(Xs)
                self.scaler = scaler
            else:
                self.scaler = None
        except Exception as e:
            logger.warning(f"Could not fit StandardScaler on sample: {e}")
            scaler = None
            self.scaler = None

        kmeans = MiniBatchKMeans(
            n_clusters=optimal_k,
            batch_size=self.batch_size,
            random_state=42,
            max_iter=100,
            n_init=3
        )

        for batch in users_batches:
            # Refresh kết nối mỗi batch
            self._refresh_db_connection()
            features = []
            # Lấy user theo batch bằng in_bulk để giảm số lần truy vấn
            try:
                user_ids = [u.get('id') for u in batch if u.get('id')]
                if user_ids:
                    user_map = User.objects.only(
                        'id', 'age', 'gender', 'occupation', 'location', 'zip_code', 'user_type'
                    ).in_bulk(user_ids)
                else:
                    user_map = {}
            except Exception as e:
                logger.warning(f"Batch user fetch failed: {e}")
                user_map = {}

            for user_id in user_ids:
                user = user_map.get(user_id)
                if not user:
                    continue
                try:
                    fv = vectorizer.create_demographic_vector(user)
                    features.append(fv)
                except Exception as e:
                    logger.warning(f"Error creating vector for user {user_id}: {e}")
                    continue

            if features:
                features_array = np.array(features)
                # Chuẩn hoá theo scaler nếu có
                if scaler is not None:
                    try:
                        features_array = scaler.transform(features_array)
                    except Exception as e:
                        logger.warning(f"Scaler transform failed during training: {e}")
                kmeans.partial_fit(features_array)

            if self._check_memory_usage() > self.memory_limit_mb:
                logger.warning("⚠️ Memory limit reached, clearing cache...")
                cache.clear()

        return kmeans

    def _save_model_multi_storage(self, model):
        """Save model vào multiple storages để đảm bảo availability"""

        # Chuẩn hóa định dạng lưu trữ để load tương thích
        payload = {
            'model': model,
            'scaler': getattr(self, 'scaler', None)
        }

        # 1. Save to Redis cache (đồng bộ định dạng)
        model_bytes = pickle.dumps(payload)
        cache.set('kmeans_model', model_bytes, timeout=self.cache_ttl)

        # 2. Save to database (serialized, kèm is_active)
        from apps.recommendations.models import ModelStorage
        ModelStorage.objects.update_or_create(
            model_name='kmeans_demographic',
            defaults={
                'model_data': model_bytes,
                'version': '1.0',
                'created_at': timezone.now(),
                'is_active': True,
            }
        )

        # 3. Save metadata
        metadata = {
            'n_clusters': model.n_clusters,
            'cluster_centers': model.cluster_centers_.tolist(),
            'version': '1.0',
            'created_at': timezone.now().isoformat()
        }
        cache.set('kmeans_metadata', json.dumps(metadata), timeout=self.cache_ttl)

        logger.info("💾 Model saved to multiple storages")

    def _precompute_all_clusters(self, model):
        """Pre-compute clusters cho tất cả users với đầy đủ thông tin demographics"""
        from apps.recommendations.models import DemographicCluster
        from apps.recommendations.services import EnhancedDemographicFilteringService

        # Clear existing clusters
        DemographicCluster.objects.filter(cluster_id__startswith='kmeans_').delete()

        users = User.objects.filter(age__isnull=False, gender__isnull=False).only(
            'id', 'age', 'gender', 'occupation', 'location', 'zip_code', 'user_type'
        )
        total_users = users.count()

        logger.info(f"🔄 Pre-computing clusters for {total_users} users...")

        # Phase 1: Assign users to clusters using the trained model
        cluster_assignments = {}  # cluster_id -> list of users

        # Sử dụng AdvancedDemographicVectorizer như refresh_cluster
        vectorizer = AdvancedDemographicVectorizer()

        for i in range(0, total_users, self.batch_size):
            # Làm mới kết nối trước khi xử lý mỗi batch
            self._refresh_db_connection()
            batch_users = list(users[i:i+self.batch_size])

            for user in batch_users:
                try:
                    # Extract features using comprehensive vectorizer
                    features = vectorizer.create_demographic_vector(user)

                    # Predict cluster with proper scaling to match training space
                    try:
                        if getattr(self, 'scaler', None) is not None:
                            try:
                                features_scaled = self.scaler.transform([features])[0]
                            except Exception as e:
                                logger.warning(f"Scaler transform failed for user {user.id}: {str(e)}; using unscaled features")
                                features_scaled = features
                        else:
                            features_scaled = features

                        cluster_label = model.predict([features_scaled])[0]
                    except Exception as e:
                        logger.warning(f"Cluster prediction failed for user {user.id}: {str(e)}; assigning default cluster 0")
                        cluster_label = 0
                    cluster_id = f"kmeans_{cluster_label}"

                    # Group users by cluster
                    if cluster_id not in cluster_assignments:
                        cluster_assignments[cluster_id] = []
                    cluster_assignments[cluster_id].append(user)

                    # Update user preference
                    user_pref, _ = UserPreference.objects.get_or_create(user=user)
                    user_pref.demographic_cluster = cluster_id
                    user_pref.save()

                except Exception as e:
                    logger.warning(f"Failed to process user {user.id}: {str(e)}")
                    continue

        # Phase 2: Create clusters with full demographic information
        logger.info("📊 Creating clusters with demographic information...")

        for cluster_id, cluster_users in cluster_assignments.items():
            if len(cluster_users) < 3:  # Skip small clusters
                continue

            # Calculate cluster characteristics
            ages = [user.age for user in cluster_users if user.age]
            genders = [user.gender for user in cluster_users if user.gender]
            occupations = [user.occupation for user in cluster_users if user.occupation]

            # Most common gender
            from collections import Counter
            gender_counts = Counter(genders)
            primary_gender = gender_counts.most_common(1)[0][0] if gender_counts else 'M'

            # Age range
            age_min = min(ages) if ages else 0
            age_max = max(ages) if ages else 100

            # Calculate genre preferences for this cluster
            demographic_service = EnhancedDemographicFilteringService()
            genre_preferences = demographic_service._calculate_cluster_genre_preferences(cluster_users)

            # Calculate average rating and variance
            from django.db.models import Variance
            rating_stats = MovieReview.objects.filter(
                user__in=cluster_users,
                review_type='USER',
                rating__isnull=False
            ).aggregate(
                avg_rating=Avg('rating'),
                rating_variance=Variance('rating'),
                count=Count('rating')
            )

            # Create cluster with full information including rating variance
            cluster_variance = rating_stats['rating_variance'] or 0.0
            DemographicCluster.objects.create(
                cluster_id=cluster_id,
                name=f"K-means Cluster {cluster_id.split('_')[1]}",
                description=f"K-means cluster {cluster_id.split('_')[1]}: {len(cluster_users)} users, age {age_min}-{age_max}, gender {primary_gender}, avg_rating={rating_stats['avg_rating'] or 3.0:.2f}, variance={cluster_variance:.3f}",
                age_range_min=age_min,
                age_range_max=age_max,
                primary_gender=primary_gender,
                common_occupations=list(set(occupations)),  # All occupations
                preferred_genres=genre_preferences,
                average_rating=rating_stats['avg_rating'] or 3.0,
                rating_variance=cluster_variance,
                user_count=len(cluster_users)
            )

        logger.info("✅ Pre-computation completed with full demographic information!")

    def get_user_cluster_production(self, user):
        """
        🎯 Production-ready cluster lookup
        Fast lookup từ pre-computed data + caching với performance optimization
        """
        try:
            # Chấp nhận cả user object hoặc user id
            if hasattr(user, 'id'):
                user_obj = user
                user_id = user.id
            else:
                user_id = int(user)
                # đảm bảo có object để fallback rule-based
                user_obj = User.objects.only(
                    'id', 'age', 'gender', 'occupation', 'location', 'zip_code', 'user_type'
                ).get(id=user_id)

            # 1. Try database lookup first
            # Use values() to get only the field we need
            user_pref_data = UserPreference.objects.filter(
                user=user_id
            ).values('demographic_cluster').first()

            if user_pref_data and user_pref_data.get('demographic_cluster'):
                cluster_id = user_pref_data['demographic_cluster']

                # Try to cache (async, don't wait for it)
                try:
                    cache_key = f"user_cluster:{user_id}"
                    cache.set(cache_key, cluster_id, timeout=self.cache_ttl)
                except Exception:
                    pass  # Ignore cache errors

                return cluster_id

            # 2. Try cache as fallback (if DB lookup failed)
            try:
                cache_key = f"user_cluster:{user_id}"
                cached_cluster = cache.get(cache_key)

                if cached_cluster:
                    return cached_cluster
            except Exception:
                pass  # Ignore cache errors

            # 3. Fallback to rule-based clustering
            return self._rule_based_fallback(user_obj)

        except Exception as e:
            try:
                uid = user.id if hasattr(user, 'id') else user
            except Exception:
                uid = 'unknown'
            logger.error(f"Cluster lookup failed for user {uid}: {str(e)}")
            # Fallback an toàn
            if hasattr(user, 'id'):
                return self._rule_based_fallback(user)
            try:
                user_obj = User.objects.only(
                    'id', 'age', 'gender', 'occupation', 'location', 'zip_code', 'user_type'
                ).get(id=int(user))
                return self._rule_based_fallback(user_obj)
            except Exception:
                # Fallback cuối cùng
                return "kmeans_6"

    def _rule_based_fallback(self, user):
        """Rule-based clustering fallback"""
        if not user.age or not user.gender:
            return "kmeans_6"  # Default cluster

        # Simple rule-based logic
        if user.age < 25:
            if user.gender == 'M':
                return "kmeans_2"  # Young male
            else:
                return "kmeans_3"  # Young female
        elif user.age < 45:
            if user.gender == 'M':
                return "kmeans_1"  # Adult male
            else:
                return "kmeans_5"  # Adult female
        else:
            if user.gender == 'M':
                return "kmeans_0"  # Senior male
            else:
                return "kmeans_5"  # Senior female

    def _extract_user_features(self, user):
        """Extract features từ user data"""
        # Normalize age (0-1 scale)
        age_normalized = min(user.age / 100.0, 1.0) if user.age else 0.5

        # Encode gender (0=female, 1=male)
        gender_encoded = 1 if user.gender == 'M' else 0

        return [age_normalized, gender_encoded]

    def _extract_features(self, users_batch):
        """Extract features từ batch users"""
        features = []
        for user_data in users_batch:
            age = user_data.get('age', 25)
            gender = user_data.get('gender', 'M')

            age_normalized = min(age / 100.0, 1.0)
            gender_encoded = 1 if gender == 'M' else 0

            features.append([age_normalized, gender_encoded])

        return features

    def _check_memory_usage(self):
        """Check memory usage"""
        if PSUTIL_AVAILABLE and psutil:
            return psutil.virtual_memory().percent
        else:
            return 50.0  # Default value if psutil not available

    def get_cluster_statistics(self):
        """Get statistics về clusters"""
        from apps.recommendations.models import DemographicCluster

        # Use string filtering for Django ORM
        clusters = DemographicCluster.objects.filter(
            cluster_id__startswith='kmeans_'
        )

        stats = {
            'total_clusters': clusters.count(),
            'cluster_distribution': {},
            'total_users': UserPreference.objects.filter(
                demographic_cluster__startswith='kmeans_'
            ).count()
        }

        for cluster in clusters:
            user_count = UserPreference.objects.filter(
                demographic_cluster=cluster.cluster_id
            ).count()
            stats['cluster_distribution'][cluster.cluster_id] = user_count

        return stats

class OptimizedRecommendationService:
    """
    🚀 Tối ưu hóa recommendation service với background generation và fallback cache
    Giải quyết vấn đề timeout khi tạo recommendation
    """

    def __init__(self):
        self.collaborative_service = CollaborativeFilteringService()
        self.hybrid_service = HybridRecommendationService()
        self.demographic_service = EnhancedDemographicFilteringService()
        self.cache_service = RecommendationCacheService()
        self.settings = getattr(settings, 'RECOMMENDATION_CACHE_SETTINGS', {})

    def get_recommendations_with_fallback(self, user, rec_type='hybrid', limit=20, context='homepage'):
        """
        Lấy recommendations với fallback strategy:
        1. Kiểm tra cache chính (7 ngày)
        2. Kiểm tra fallback cache (24 giờ)
        3. Tạo recommendations ngay lập tức nếu không có cache
        4. Luôn trả về recommendations (không bao giờ empty)
        """
        try:
            # 1. Kiểm tra cache chính (7 ngày)
            recommendations = self.cache_service.get_cached_recommendations(
                user, rec_type, context, limit
            )

            if recommendations:
                logger.info(f"✅ Sử dụng cache chính cho {rec_type} recommendations (user {user.id})")
                # Trigger background generation để cập nhật cache cho lần sau
                self._trigger_background_generation(user, rec_type, context)
                return recommendations

            # 2. Kiểm tra fallback cache (24 giờ)
            fallback_hours = self.settings.get('FALLBACK_CACHE_HOURS', 24)
            fallback_cutoff = timezone.now() - timedelta(hours=fallback_hours)

            fallback_recommendations = RecommendationResult.objects.filter(
                user=user,
                recommendation_type=rec_type,
                created_at__gte=fallback_cutoff
            ).select_related('movie').order_by('rank')[:limit]

            if fallback_recommendations.exists():
                logger.info(f"🔄 Sử dụng fallback cache cho {rec_type} recommendations (user {user.id})")
                # Trigger background generation để cập nhật cache chính
                self._trigger_background_generation(user, rec_type, context)
                return [rec.movie for rec in fallback_recommendations]

            # 3. Không có cache - tạo recommendations ngay lập tức
            logger.warning(f"⚠️ Không có cache cho {rec_type} recommendations (user {user.id}) - tạo ngay lập tức")
            try:
                # Tạo recommendations ngay lập tức
                immediate_recommendations = self._generate_recommendations_immediately(
                    user, rec_type, limit, context
                )

                if immediate_recommendations:
                    # Với hybrid/demographic: service đã lưu metadata đầy đủ qua RecommendationCacheService
                    # Chỉ dùng fallback cache cho collaborative để đơn giản
                    if rec_type == 'collaborative':
                        self._save_to_fallback_cache(user, rec_type, context, immediate_recommendations)
                    logger.info(f"Tạo thành công {len(immediate_recommendations)} {rec_type} recommendations cho user {user.id}")

                    # Trigger background generation để cập nhật cache cho lần sau
                    self._trigger_background_generation(user, rec_type, context)
                    return immediate_recommendations
                else:
                    logger.warning(f" Immediate generation trả về empty, fallback về trending")

            except Exception as e:
                logger.error(f" Lỗi khi tạo immediate recommendations: {str(e)}")

            # 4. Fallback cuối cùng - trả về trending/popular movies
            logger.warning(f" Fallback về trending movies cho user {user.id}")
            # Trigger background generation để tạo cache cho lần sau
            self._trigger_background_generation(user, rec_type, context)
            return self._get_trending_fallback(limit)

        except Exception as e:
            logger.error(f"Error in get_recommendations_with_fallback: {str(e)}")
            # Fallback cuối cùng
            return self._get_trending_fallback(limit)

    def _trigger_background_generation(self, user, rec_type, context):
        """
        Trigger background generation để tránh timeout
        Sử dụng Celery tasks cho background processing
        """
        try:
            if self.settings.get('BACKGROUND_GENERATION', True):
                # Import tasks
                from .tasks import (
                    generate_collaborative_recommendations_async,
                    generate_hybrid_recommendations_async,
                    generate_demographic_recommendations_async,
                    refresh_all_recommendations_async
                )

                if rec_type == 'hybrid':
                    # Trigger hybrid recommendations background task với priority cao
                    task = generate_hybrid_recommendations_async.apply_async(
                        args=[user.id, context, 20],
                        kwargs={},
                        priority=9,
                        queue='high_priority'
                    )
                    logger.info(f" Triggered background hybrid generation cho user {user.id} (task: {task.id}) với priority cao")

                elif rec_type == 'collaborative':
                    # Trigger collaborative filtering background task với priority cao
                    task = generate_collaborative_recommendations_async.apply_async(
                        args=[user.id, context, 20],
                        kwargs={},
                        priority=9,
                        queue='high_priority'
                    )
                    logger.info(f" Triggered background collaborative generation cho user {user.id} (task: {task.id}) với priority cao")

                elif rec_type == 'demographic':
                    # Trigger demographic recommendations background task với priority cao
                    task = generate_demographic_recommendations_async.apply_async(
                        args=[user.id, context, 20],
                        kwargs={},
                        priority=9,
                        queue='high_priority'
                    )
                    logger.info(f" Triggered background demographic generation cho user {user.id} (task: {task.id}) với priority cao")

                else:
                    # Trigger all types of recommendations với priority cao
                    task = refresh_all_recommendations_async.apply_async(
                        args=[user.id, context, 20],
                        kwargs={},
                        priority=9,
                        queue='high_priority'
                    )
                    logger.info(f"Triggered background refresh all recommendations cho user {user.id} (task: {task.id}) với priority cao")

        except Exception as e:
            logger.error(f"Error triggering background generation: {str(e)}")

    def _generate_recommendations_immediately(self, user, rec_type, limit, context):
        """
        Tạo recommendations ngay lập tức dựa trên rec_type
        """
        try:
            logger.info(f" immediate {rec_type} recommendations for user {user.id}")

            if rec_type == 'collaborative':
                return self.collaborative_service.generate_collaborative_recommendations(
                    user, limit=limit, context=context
                )
            elif rec_type == 'hybrid':
                return self.hybrid_service.generate_hybrid_recommendations(
                    user, limit=limit, context=context
                )
            elif rec_type == 'demographic':
                return self.demographic_service.generate_enhanced_demographic_recommendations(
                    user, limit=limit, context=context, store=True
                )
            else:
                # Fallback to hybrid
                return self.hybrid_service.generate_hybrid_recommendations(
                    user, limit=limit, context=context
                )

        except Exception as e:
            logger.error(f"Error generating immediate {rec_type} recommendations: {str(e)}")
            return []

    def _save_to_fallback_cache(self, user, rec_type, context, recommendations):
        """
        Lưu recommendations vào fallback cache ngay lập tức
        """
        try:
            # Chỉ áp dụng fallback cache cho collaborative để tránh làm bẩn hybrid/demographic meta
            if rec_type != 'collaborative':
                logger.info(f"ℹ️ Skip fallback cache for {rec_type} to prevent rank pollution")
                return

            # Xóa recommendations cũ (chỉ collaborative)
            RecommendationResult.objects.filter(
                user=user,
                recommendation_type=rec_type,
                context=context
            ).delete()

            # Lưu recommendations mới
            for rank, movie in enumerate(recommendations, 1):
                RecommendationResult.objects.create(
                    user=user,
                    movie=movie,
                    recommendation_type=rec_type,
                    context=context,
                    rank=rank,
                    score=1.0 - (rank * 0.05),
                    confidence_score=0.7,  # Lower confidence cho fallback cache
                    explanation={
                        'source': 'immediate_generation',
                        'generated_at': timezone.now().isoformat(),
                        'cache_type': 'fallback',
                        'reason': f'Generated immediately for {rec_type} recommendations'
                    }
                )

            logger.info(f"💾 Lưu {len(recommendations)} recommendations vào fallback cache cho user {user.id}")

        except Exception as e:
            logger.error(f"Error saving to fallback cache: {str(e)}")

    def _get_trending_fallback(self, limit):
        """
        Fallback cuối cùng - trả về trending movies
        """
        try:
            from apps.movies.models import Movie

            # Lấy trending movies dựa trên combined_rating_score và cached ratings
            trending_movies = Movie.objects.filter(
                poster_url__isnull=False,
                poster_url__gt='',
                combined_rating_score__isnull=False,
                combined_rating_score__gte=6.0  # Ít nhất 6.0 rating
            ).order_by('-combined_rating_score', '-cached_imdb_votes')[:limit]

            logger.info(f"📈 Trả về {len(trending_movies)} trending movies làm fallback")
            return list(trending_movies)

        except Exception as e:
            logger.error(f"Error getting trending fallback: {str(e)}")
            # Fallback cuối cùng - lấy movies có poster
            try:
                fallback_movies = Movie.objects.filter(
                    poster_url__isnull=False,
                    poster_url__gt=''
                ).order_by('-created_at')[:limit]
                logger.info(f"📈 Trả về {len(fallback_movies)} fallback movies")
                return list(fallback_movies)
            except Exception as e2:
                logger.error(f"Error getting fallback movies: {str(e2)}")
                return []

    def _generate_collaborative_background(self, user, context):
        """
        Generate collaborative recommendations trong background (legacy method)
        """
        try:
            # Sử dụng threading để tránh blocking
            import threading

            def generate_async():
                try:
                    recommendations = self.collaborative_service.generate_collaborative_recommendations(
                        user, limit=20, context=context
                    )
                    logger.info(f"✅ Background collaborative generation completed cho user {user.id}")
                except Exception as e:
                    logger.error(f"Error in background collaborative generation: {str(e)}")

            thread = threading.Thread(target=generate_async)
            thread.daemon = True
            thread.start()

        except Exception as e:
            logger.error(f"Error starting background collaborative generation: {str(e)}")
