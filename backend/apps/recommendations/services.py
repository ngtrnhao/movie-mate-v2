import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, TYPE_CHECKING, Any
from collections import defaultdict
from decimal import Decimal
import logging
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
    UserPreference, UserSimilarity, MovieSimilarity,
    RecommendationResult, DemographicCluster, RecommendationMetrics
)

User = get_user_model()
logger = logging.getLogger(__name__)

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
        Calculate similarity between two users using various methods

        Args:
            user1, user2: Django User instances
            method: 'pearson', 'cosine', 'jaccard', 'euclidean'

        Returns:
            Similarity score between -1 and 1 (for pearson/cosine) or 0 and 1 (for jaccard)
        """
        try:
            # Get ratings for both users
            user1_ratings = dict(MovieReview.objects.filter(
                user=user1,
                review_type='USER',
                rating__isnull=False
            ).values_list('movie_id', 'rating'))

            user2_ratings = dict(MovieReview.objects.filter(
                user=user2,
                review_type='USER',
                rating__isnull=False
            ).values_list('movie_id', 'rating'))

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
                    movie_interactions__movie_id__in=user_rated_movies
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
        Generate movie recommendations using collaborative filtering
        """
        try:
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
                if len(scores) >= 2:  # At least 2 similar users rated it
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

            # Store recommendations
            self._store_recommendations(user, top_recommendations, 'collaborative', context)

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
        self.cache_timeout = 3600
        self.vectorizer = AdvancedDemographicVectorizer()
        self.similarity_calculator = AdvancedDemographicSimilarityCalculator(self.vectorizer)
        self.min_similar_users = 10
        self.similarity_threshold = 0.1

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

    def generate_demographic_recommendations(self, user, limit=20, context='homepage') -> List[any]:
        """
        Generate recommendations based on user's demographic cluster
        """
        try:
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

            # Store recommendations
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

    def generate_enhanced_demographic_recommendations(self, user, limit: int = 20,
                                                    context: str = 'homepage') -> List[Movie]:
        """
        Generate enhanced demographic recommendations using advanced ML techniques
        """
        try:
            logger.info(f"Generating enhanced demographic recommendations for user {user.id}")

            # Check if advanced features are available
            if not SKLEARN_AVAILABLE:
                logger.warning("Scikit-learn not available. Using basic demographic filtering.")
                return self.generate_demographic_recommendations(user, limit, context)

            # Get users with demographic data (limit for performance in testing)
            users_with_demographics = User.objects.filter(
                Q(age__isnull=False) | Q(gender__isnull=False) | Q(occupation__isnull=False)
            ).exclude(id=user.id)[:100]  # Limit to 100 users for better performance

            if not users_with_demographics.exists():
                logger.warning("No users with demographic data found")
                return []

            # Create demographic vectors for all users
            logger.info(f"Creating demographic vectors for {len(users_with_demographics)} users...")

            target_user_vector = self.vectorizer.create_demographic_vector(user)
            similar_users = []

            # Calculate similarities using vectorized approach
            user_vectors = []
            users_list = list(users_with_demographics)

            for other_user in users_list:
                other_vector = self.vectorizer.create_demographic_vector(other_user)
                user_vectors.append(other_vector)

            # Use cosine similarity for efficiency
            user_vectors = np.array(user_vectors)
            similarities = cosine_similarity([target_user_vector], user_vectors)[0]

            # Get top similar users
            for i, similarity in enumerate(similarities):
                if similarity > self.similarity_threshold:
                    similar_users.append((users_list[i], similarity))

            # Sort by similarity and take top K
            similar_users.sort(key=lambda x: x[1], reverse=True)
            top_similar_users = similar_users[:50]

            if len(top_similar_users) < self.min_similar_users:
                logger.warning(f"Only found {len(top_similar_users)} similar users, need at least {self.min_similar_users}")
                # Fallback to basic demographic filtering
                return self.generate_demographic_recommendations(user, limit, context)

            # Generate recommendations from similar users
            recommendations = self._generate_recommendations_from_similar_users(
                user, top_similar_users, limit * 2
            )

            # Apply demographic scoring and ranking
            scored_recommendations = self._apply_enhanced_demographic_scoring(
                user, recommendations
            )

            # Sort and limit
            scored_recommendations.sort(key=lambda x: x['final_score'], reverse=True)
            top_recommendations = scored_recommendations[:limit]

            # Store recommendations
            self._store_enhanced_recommendations(user, top_recommendations, context)

            return [rec['movie'] for rec in top_recommendations]

        except Exception as e:
            logger.error(f"Error generating enhanced demographic recommendations: {str(e)}")
            # Fallback to basic demographic filtering
            return self.generate_demographic_recommendations(user, limit, context)

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
                if len(scores) >= 2:  # At least 2 similar users rated it
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
                explanation = {
                    'type': 'enhanced_demographic',
                    'avg_similarity': float(rec['avg_similarity']),
                    'support': int(rec['support']),
                    'demographic_bonus': float(rec['demographic_bonus']),
                    'similarity_bonus': float(rec.get('similarity_bonus', 0)),
                    'confidence': float(rec['confidence']),
                    'method': 'advanced_vectorization'
                }

                recommendation_objects.append(
                    RecommendationResult(
                        user=user,
                        movie=rec['movie'],
                        recommendation_type='demographic',
                        context=context,
                        predicted_rating=float(rec['avg_rating']),
                        confidence_score=float(rec['confidence']),
                        novelty_score=0.5,  # Could be enhanced
                        rank=rank,
                        score=float(rec['final_score']),
                        explanation=explanation
                    )
                )

            RecommendationResult.objects.bulk_create(recommendation_objects)

            logger.info(f"Stored {len(recommendation_objects)} enhanced demographic recommendations")

        except Exception as e:
            logger.error(f"Error storing enhanced recommendations: {str(e)}")

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

class HybridRecommendationService:
    """
    Hybrid recommendation service combining multiple filtering methods
    """

    def __init__(self):
        self.collaborative_service = CollaborativeFilteringService()
        self.demographic_service = EnhancedDemographicFilteringService()
        self.weights = {
            'collaborative': 0.4,
            'demographic': 0.3,
            'content_based': 0.2,
            'trending': 0.1
        }

    def generate_hybrid_recommendations(self, user, limit=20, context='homepage') -> List[any]:
        """
        Generate hybrid recommendations combining multiple methods
        """
        try:
            all_recommendations = {}

            # Get collaborative filtering recommendations
            collaborative_recs = self.collaborative_service.generate_collaborative_recommendations(
                user, limit=limit*2, context=context
            )

            # Get enhanced demographic filtering recommendations
            demographic_recs = self.demographic_service.generate_enhanced_demographic_recommendations(
                user, limit=limit*2, context=context
            )

            # Get content-based recommendations (using existing genre preferences)
            content_recs = self._get_content_based_recommendations(user, limit=limit*2)

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

            for movie in content_recs:
                if movie.id not in all_recommendations:
                    all_recommendations[movie.id] = {
                        'movie': movie,
                        'score': 0.0,
                        'methods': []
                    }
                all_recommendations[movie.id]['score'] += self.weights['content_based']
                all_recommendations[movie.id]['methods'].append('content_based')

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

            # Prepare for storage
            final_recommendations = []
            for rec in sorted_recommendations[:limit]:
                final_recommendations.append({
                    'movie': rec['movie'],
                    'score': rec['score'],
                    'confidence': min(1.0, len(rec['methods']) / 4.0),
                    'novelty_score': 0.5,
                    'explanation': {
                        'type': 'hybrid',
                        'methods': rec['methods'],
                        'combined_score': rec['score']
                    }
                })

            # Store hybrid recommendations
            self.demographic_service._store_recommendations(
                user, final_recommendations, 'hybrid', context
            )

            return [rec['movie'] for rec in final_recommendations]

        except Exception as e:
            logger.error(f"Error generating hybrid recommendations: {str(e)}")
            return []

    def _get_content_based_recommendations(self, user, limit=20) -> List[any]:
        """Get content-based recommendations using user's favorite genres"""
        try:
            # Get user's favorite genres
            favorite_genres = UserFavoriteGenre.objects.filter(user=user).values_list('genre', flat=True)

            if not favorite_genres:
                # Infer from high ratings
                high_rated_movies = MovieReview.objects.filter(
                    user=user,
                    review_type='USER',
                    rating__gte=4.0
                ).values_list('movie', flat=True)

                if high_rated_movies:
                    favorite_genres = Movie.objects.filter(
                        id__in=high_rated_movies
                    ).values_list('genres', flat=True).distinct()

            if not favorite_genres:
                return []

            # Get user's already rated movies
            user_rated_movies = set(MovieReview.objects.filter(
                user=user,
                review_type='USER'
            ).values_list('movie_id', flat=True))

            # Get movies from favorite genres
            content_movies = Movie.objects.filter(
                genres__in=favorite_genres,
                poster_url__isnull=False
            ).exclude(
                id__in=user_rated_movies
            ).annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__review_type='USER'))
            ).filter(
                avg_rating__gte=3.5
            ).order_by('-avg_rating')[:limit]

            return list(content_movies)

        except Exception as e:
            logger.error(f"Error getting content-based recommendations: {str(e)}")
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

        return np.array(features, dtype=np.float32)

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

            # Check regions with word-based matching
            import re
            location_words = re.findall(r'\b\w+\b', mapped_location)

            for i, (region, countries) in enumerate(self.location_regions.items()):
                for country in countries:
                    if country in location_words:  # Word-based matching instead of substring
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
