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

        # Try to acquire lock with 5-minute timeout
        acquired = cache.set(lock_key, True, timeout=timeout, nx=True)

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
        self.min_common_ratings = 5
        self.min_similar_users = 10
        self.similarity_threshold = 0.1
        self.cache_timeout = 3600  # 1 hour

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

            # Find common movies
            common_movies = set(user1_ratings.keys()) & set(user2_ratings.keys())

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
                candidate_users = User.objects.filter(
                    moviereview__movie_id__in=user_rated_movies,
                    moviereview__review_type='USER',
                    moviereview__rating__isnull=False
                ).exclude(
                    id=user.id
                ).distinct()[:500]  # Limit candidates for performance

                for other_user in candidate_users:
                    similarity = self.calculate_user_similarity(user, other_user, method)

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
        try:
            if not similar_users:
                return None

            weighted_sum = 0.0
            similarity_sum = 0.0

            # Get user's average rating for normalization
            user_avg = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 3.0
            user_avg = float(user_avg)  # Cast to float

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
                    similar_avg = float(similar_avg)  # Cast to float

                    # Normalize rating
                    normalized_rating = float(similar_user_rating.rating) - similar_avg

                    weighted_sum += similarity * normalized_rating
                    similarity_sum += abs(similarity)

            if similarity_sum == 0:
                return None

            # Denormalize prediction
            predicted = user_avg + (weighted_sum / similarity_sum)

            # Clamp to valid range
            return max(0.0, min(5.0, predicted))

        except Exception as e:
            logger.error(f"Error predicting rating: {str(e)}")
            return None

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
                if len(scores) >= 1:  # At least 1 similar user rated it (reduced from 2)
                    avg_score = sum(scores) / len(scores)
                    confidence = min(1.0, len(scores) / 5.0)  # Higher confidence with more ratings

                    # Predict rating
                    predicted_rating = self.predict_rating(user, movie, similar_users)

                    recommendations.append({
                        'movie': movie,
                        'score': avg_score,
                        'confidence': confidence,
                        'predicted_rating': predicted_rating,
                        'explanation': {
                            'type': 'collaborative',
                            'similar_users_count': len(scores),
                            'average_rating': sum(scores) / len(scores)
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

            # Create new recommendations
            recommendation_objects = []

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

            # Nếu không có cache, tạo lại từ database
            logger.info("🔄 Cache not available, creating model from database...")

            # Kiểm tra xem có K-means clusters trong database không
            kmeans_clusters = DemographicCluster.objects.filter(cluster_id__startswith='kmeans_')
            if not kmeans_clusters.exists():
                logger.info("No K-means clusters found in database")
                return

            logger.info(f"🔄 Loading K-means model from {kmeans_clusters.count()} existing clusters...")

            # Lấy users với demographics để tạo lại model
            users_with_data = User.objects.filter(
                age__isnull=False,
                gender__isnull=False
            ).exclude(age__isnull=True)

            if users_with_data.count() < 10:
                logger.warning("Not enough users with demographics to load K-means model")
                return

            # Tạo demographic vectors cho tất cả users
            user_vectors = []
            users_list = []

            for user in users_with_data:
                try:
                    vector = self.vectorizer.create_demographic_vector(user)
                    user_vectors.append(vector)
                    users_list.append(user)
                except Exception as e:
                    logger.warning(f"Error creating vector for user {user.id}: {str(e)}")
                    continue

            if len(user_vectors) < 10:
                logger.warning("Not enough valid vectors to load K-means model")
                return

            # Convert to numpy array
            X = np.array(user_vectors)

            # Standardize features
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Tạo K-means model với số clusters bằng với số clusters trong database
            n_clusters = kmeans_clusters.count()
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)

            # Fit model với dữ liệu hiện tại
            cluster_labels = kmeans.fit_predict(X_scaled)

            # Lưu model và scaler
            self.kmeans_model = kmeans
            self.scaler = scaler

            # Lưu vào cache để lần sau load nhanh hơn
            self._save_model_to_cache()

            logger.info(f"✅ Successfully loaded K-means model with {n_clusters} clusters")

        except Exception as e:
            logger.error(f"Error loading K-means model: {str(e)}")
            self.kmeans_model = None
            self.scaler = None

    def create_kmeans_clusters(self, recalculate=False, n_clusters=8):
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

            logger.info(f"🔄 Creating K-means clusters with {n_clusters} clusters...")

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

            # Perform K-means clustering
            logger.info(" Running K-means clustering...")
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)

            # Store the model for future use
            self.kmeans_model = kmeans
            self.scaler = scaler

            # Create clusters in database
            logger.info(" Creating cluster records in database...")

            for cluster_id in range(n_clusters):
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
                    common_occupations=list(set(occupations))[:5],  # Top 5 occupations
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
                    user_vector_scaled = self.scaler.transform([user_vector])
                    cluster_label = self.kmeans_model.predict(user_vector_scaled)[0]

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

                    # Calculate demographic score based on genre preferences
                    demographic_score = self._calculate_demographic_score(movie, cluster)

                    # Combine with cluster rating
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
                            'demographic_score': demographic_score
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
        """Calculate how well a movie matches cluster preferences"""
        try:
            if not cluster.preferred_genres:
                return 0.5  # Neutral score

            movie_genres = movie.genres.all()
            total_score = 0.0
            genre_count = 0

            for genre in movie_genres:
                genre_pref = cluster.preferred_genres.get(str(genre.id))
                if genre_pref:
                    total_score += genre_pref['preference_score']
                    genre_count += 1

            if genre_count == 0:
                return 0.5  # Neutral score for movies without preferred genres

            return total_score / genre_count

        except Exception as e:
            logger.error(f"Error calculating demographic score: {str(e)}")
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

                recommendation_objects.append(
                    RecommendationResult(
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
                    )
                )

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

            recent_cutoff = timezone.now() - timedelta(hours=1)
            stored_recommendations = RecommendationResult.objects.filter(
                user=user,
                recommendation_type='demographic',
                context=context,
                created_at__gte=recent_cutoff
            ).select_related('movie').order_by('rank')[:limit]

            if stored_recommendations.exists():
                logger.info(f"✅ Using cached demographic recommendations for user {user.id}")
                return [rec.movie for rec in stored_recommendations]

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
                return []

            # Generate recommendations from similar users
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
        """Generate candidate recommendations from similar users"""
        try:
            # Get movies user has already interacted with
            user_movie_ids = set(MovieReview.objects.filter(
                user=target_user,
                review_type='USER'
            ).values_list('movie_id', flat=True))

            # Collect candidate movies from similar users
            candidate_movies = defaultdict(list)

            for similar_user, similarity_score in similar_users:
                # Get highly rated movies from similar user
                similar_user_ratings = MovieReview.objects.filter(
                    user=similar_user,
                    review_type='USER',
                    rating__gte=4.0,
                    rating__isnull=False
                ).exclude(
                    movie_id__in=user_movie_ids
                ).select_related('movie')

                for rating in similar_user_ratings:
                    rating_value = float(rating.rating) if rating.rating else 0.0
                    weighted_score = rating_value * similarity_score
                    candidate_movies[rating.movie].append({
                        'weighted_score': weighted_score,
                        'similarity': similarity_score,
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
                    avg_rating = np.mean([s['rating'] for s in scores])
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

            return recommendations

        except Exception as e:
            logger.error(f"Error applying enhanced demographic scoring: {str(e)}")
            return recommendations

    def _store_enhanced_recommendations(self, user, recommendations: List[Dict], context: str):
        """Store enhanced recommendations in database"""
        try:
            # Clear existing recommendations
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
        """
        try:
            # Get users from the same cluster with ratings
            users_with_ratings = User.objects.filter(
                recommendation_preference__demographic_cluster=cluster,
                moviereview__review_type='USER',
                moviereview__rating__isnull=False
            ).exclude(id=user.id).distinct()[:limit]

            if not users_with_ratings.exists():
                logger.warning(f"No users with ratings found in cluster {cluster}")
                return []

            # Calculate similarities
            similar_users = []
            target_user_vector = self.vectorizer.create_demographic_vector(user)

            for other_user in users_with_ratings:
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

            # Get basic demographic filtering recommendations (DON'T auto-store)
            demographic_recs = self.demographic_service.generate_demographic_recommendations(
                user, limit=limit*2, context=context, store=False
            )



            # Get trending recommendations
            trending_recs = self._get_trending_recommendations(user, limit=limit//2)

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

            # Prepare for storage with full metadata
            final_recommendations = []
            for rec in sorted_recommendations[:limit]:
                # Calculate predicted rating based on methods used
                predicted_rating = None
                if 'collaborative' in rec['methods']:
                    predicted_rating = min(5.0, 3.5 + (rec['score'] * 1.5))
                elif 'demographic' in rec['methods']:
                    predicted_rating = min(5.0, 3.0 + (rec['score'] * 2.0))
                else:
                    predicted_rating = min(5.0, 2.5 + (rec['score'] * 2.5))

                confidence = min(1.0, len(rec['methods']) / 4.0)
                novelty = 0.5 + (0.3 if 'trending' in rec['methods'] else 0.0)

                final_recommendations.append({
                    'movie': rec['movie'],
                    'score': rec['score'],
                    'predicted_rating': predicted_rating,
                    'confidence': confidence,
                    'novelty_score': novelty,
                    'explanation': {
                        'type': 'hybrid',
                        'methods': rec['methods'],
                        'combined_score': rec['score'],
                        'predicted_rating': predicted_rating,
                        'algorithm_count': len(rec['methods'])
                    }
                })

            # Store hybrid recommendations using proper method
            # Don't auto-store - let the calling code handle storage
            # self.demographic_service._store_recommendations(
            #     user, final_recommendations, 'hybrid', context
            # )

            # Return list of Movie objects
            # Store recommendations using unified cache service
            RecommendationCacheService.store_recommendations(user, final_recommendations, 'hybrid', context)

            return [rec['movie'] for rec in final_recommendations]

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
        Tạo vector demographic comprehensive cho user

        Returns:
            np.ndarray: Vector representing user demographics
        """
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

        return np.array(features, dtype=np.float64)

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
                logger.info(f"✅ Using cached {rec_type} recommendations for user {user.id}")
                return [rec.movie for rec in stored_recommendations]

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
            # Clear existing recommendations for this user/type
            RecommendationResult.objects.filter(
                user=user,
                recommendation_type=rec_type
            ).delete()

            # Store new recommendations
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
