import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Union, Optional
from datetime import datetime

from django.db.models import Avg, Count
from django.db import transaction
from django.conf import settings
from django.utils import timezone

from recommendations.models import Recommendation, UserSimilarity, MovieSimilarity
from recommendations.algorithms.content_based import ContentBasedFiltering
from recommendations.algorithms.collaborative_filtering import UserBasedCF
from recommendations.algorithms.matrix_factorization import MatrixFactorization
from recommendations.algorithms.hybrid import HybridRecommender
from users.models import Users, Rating
from movies.models import Movie

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Service for generating movie recommendations using different algorithms:
    - Content-based recommendations
    - Collaborative filtering
    - Matrix factorization
    - Hybrid approach (combining the above methods)
    - Popular movies (fallback)
    """

    def __init__(self):
        # Initialize all recommendation algorithms
        self.content_based = ContentBasedFiltering()
        self.collaborative = UserBasedCF()
        self.matrix_factorization = MatrixFactorization(
            num_factors=100,  # Hyperparameter for the number of latent factors
        )
        weights = {
            'collaborative_filtering': 0.4,
            'content_based': 0.3,
            'matrix_factorization': 0.3
        }

        # Initialize hybrid recommender with component algorithms
        self.hybrid = HybridRecommender()
        self.hybrid.collaborative_filtering = self.collaborative
        self.hybrid.content_based = self.content_based
        self.hybrid.matrix_factorization = self.matrix_factorization
        self.hybrid.weights = weights

    def train_all_models(self):
        """Train all recommendation models"""
        logger.info("Starting training process for all recommendation models")

        try:
            logger.info("Training content-based filtering model")
            self.content_based.train()

            logger.info("Training collaborative filtering model")
            self.collaborative.train()

            logger.info("Training matrix factorization model")
            self.matrix_factorization.train()

            logger.info("Training hybrid recommender model")
            self.hybrid.train()

            logger.info("All models trained successfully")
        except Exception as e:
            logger.error(f"Error training recommendation models: {str(e)}")
            raise

    def save_all_models(self, base_path=None):
        """Save all trained models to disk"""
        if base_path is None:
            base_path = settings.MODEL_STORAGE_PATH

        try:
            self.content_based.save_model(f"{base_path}/content_based_model")
            self.collaborative.save_model(f"{base_path}/collaborative_model")
            self.matrix_factorization.save_model(f"{base_path}/matrix_factorization_model")
            self.hybrid.save_model(f"{base_path}/hybrid_model")
            logger.info("All models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {str(e)}")
            raise

    def load_all_models(self, base_path=None):
        """Load all trained models from disk"""
        if base_path is None:
            base_path = settings.MODEL_STORAGE_PATH

        try:
            self.content_based.load_model(f"{base_path}/content_based_model")
            self.collaborative.load_model(f"{base_path}/collaborative_model")
            self.matrix_factorization.load_model(f"{base_path}/matrix_factorization_model")
            self.hybrid.load_model(f"{base_path}/hybrid_model")
            logger.info("All models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            raise

    def get_popular_recommendations(self, num_recommendations=10, min_rating_count=20):
        """
        Get popular movie recommendations based on average rating and popularity.
        This is used as a fallback when personalized recommendations cannot be generated.

        Args:
            num_recommendations (int): Number of recommendations to generate
            min_rating_count (int): Minimum number of ratings required for a movie

        Returns:
            List[Dict]: List of recommended movies with scores
        """
        logger.info(f"Generating popular recommendations (top {num_recommendations})")

        try:
            # Get popular movies based on average rating and number of ratings
            popular_movies = Movie.objects.annotate(
                avg_rating=Avg('rating__rating'),
                rating_count=Count('rating')
            ).filter(
                rating_count__gte=min_rating_count
            ).order_by('-avg_rating', '-rating_count')[:num_recommendations]

            # Format the results
            recommendations = [
                {
                    'movie_id': movie.id,
                    'title': movie.title,
                    'score': float(movie.avg_rating) if movie.avg_rating else 0.0,
                    'rating_count': movie.rating_count
                }
                for movie in popular_movies
            ]

            logger.info(f"Generated {len(recommendations)} popular recommendations")
            return recommendations

        except Exception as e:
            logger.error(f"Error generating popular recommendations: {str(e)}")
            return []

    def get_recommendations_for_user(self, user_id, method='hybrid', num_recommendations=10):
        """
        Get personalized recommendations for a user using the specified method

        Args:
            user_id (int): User ID to generate recommendations for
            method (str): Recommendation method ('hybrid', 'content_based', 'collaborative', 'matrix_factorization', 'popular')
            num_recommendations (int): Number of recommendations to generate

        Returns:
            List[Dict]: List of recommended movies with scores
        """
        logger.info(f"Generating {method} recommendations for user {user_id}")

        try:
            # Check if user exists
            if not Users.objects.filter(id=user_id).exists():
                logger.warning(f"User {user_id} not found")
                return self.get_popular_recommendations(num_recommendations)

            # Check if user has ratings
            user_ratings = Rating.objects.filter(user_id=user_id).count()
            if user_ratings == 0 and method != 'popular':
                logger.info(f"User {user_id} has no ratings, falling back to popular recommendations")
                return self.get_popular_recommendations(num_recommendations)

            # Generate recommendations based on specified method
            if method == 'content_based':
                recommendations = self.content_based.recommend(user_id, num_recommendations)
                self._save_recommendations(user_id, recommendations, 'content_based')

            elif method == 'collaborative':
                recommendations = self.collaborative.recommend(user_id, num_recommendations)
                self._save_recommendations(user_id, recommendations, 'collaborative')

            elif method == 'matrix_factorization':
                recommendations = self.matrix_factorization.recommend(user_id, num_recommendations)
                self._save_recommendations(user_id, recommendations, 'matrix_factorization')

            elif method == 'hybrid':
                recommendations = self.hybrid.recommend(user_id, num_recommendations)
                self._save_recommendations(user_id, recommendations, 'hybrid')

            else:  # Default to popular
                recommendations = self.get_popular_recommendations(num_recommendations)
                self._save_recommendations(user_id, recommendations, 'popular')

            logger.info(f"Generated {len(recommendations)} recommendations for user {user_id} using {method} method")
            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations for user {user_id}: {str(e)}")
            # Fallback to popular recommendations in case of error
            return self.get_popular_recommendations(num_recommendations)

    def generate_batch_recommendations(self, users=None, method='hybrid', num_recommendations=10):
        """
        Generate recommendations for multiple users in batch mode

        Args:
            users (List[int], optional): List of user IDs. If None, generates for all users.
            method (str): Recommendation method
            num_recommendations (int): Number of recommendations per user

        Returns:
            Dict: Summary of batch operation with counts
        """
        start_time = datetime.now()

        if users is None:
            users = Users.objects.values_list('id', flat=True)
            logger.info(f"Generating recommendations for all {len(users)} users")
        else:
            logger.info(f"Generating recommendations for {len(users)} specified users")

        success_count = 0
        error_count = 0

        for user_id in users:
            try:
                self.get_recommendations_for_user(user_id, method, num_recommendations)
                success_count += 1

                # Log progress every 100 users
                if success_count % 100 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Progress: {success_count}/{len(users)} users processed in {elapsed:.2f} seconds")

            except Exception as e:
                logger.error(f"Error generating recommendations for user {user_id}: {str(e)}")
                error_count += 1

        total_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Batch recommendation generation completed in {total_time:.2f} seconds")
        logger.info(f"Summary: {success_count} successful, {error_count} failed")

        return {
            'total_users': len(users),
            'successful': success_count,
            'failed': error_count,
            'time_seconds': total_time
        }

    def _save_recommendations(self, user_id, recommendations, algorithm_type):
        """
        Save recommendations to database

        Args:
            user_id (int): User ID
            recommendations (List[Dict]): List of recommendation dictionaries
            algorithm_type (str): Algorithm type identifier
        """
        timestamp = timezone.now()

        # Delete existing recommendations of this type for the user
        Recommendation.objects.filter(user_id=user_id, algorithm_used=algorithm_type).delete()

        # Prepare bulk recommendations
        recommendation_objects = [
            Recommendation(
                user_id=user_id,
                recommended_movie_id=rec['movie_id'],
                score=rec['score'],
                algorithm_used=algorithm_type,
                created_at=timestamp
            )
            for rec in recommendations
        ]

        # Bulk create in a transaction
        with transaction.atomic():
            Recommendation.objects.bulk_create(recommendation_objects)

        logger.info(f"Saved {len(recommendations)} {algorithm_type} recommendations for user {user_id}")
