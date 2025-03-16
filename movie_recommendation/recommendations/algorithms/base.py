from abc import ABC, abstractmethod
import numpy as np
from django.db.models import Avg
from users.models import Rating
from movies.models import Movie


class RecommendationAlgorithm(ABC):
    """Base abstract class for recommendation algorithms"""

    @abstractmethod
    def train(self):
        """Train the recommendation model"""
        pass

    @abstractmethod
    def recommend(self, user_id, num_recommendations=10):
        """Generate recommendations for a specific user"""
        pass

    @abstractmethod
    def save_model(self, model_path=None):
        """Save the trained model"""
        pass

    @abstractmethod
    def load_model(self, model_path=None):
        """Load a trained model"""
        pass

    def get_user_ratings_matrix(self):
        """Create a user-item rating matrix from database"""
        # Get all users and movies
        ratings = Rating.objects.all().select_related('users', 'movie')

        # Create dictionaries to map user/movie IDs to matrix indices
        unique_users = set(rating.users.id for rating in ratings)
        unique_movies = set(rating.movie.id for rating in ratings)

        user_to_idx = {user_id: idx for idx, user_id in enumerate(unique_users)}
        movie_to_idx = {movie_id: idx for idx, movie_id in enumerate(unique_movies)}

        # Create sparse matrix
        rating_matrix = np.zeros((len(unique_users), len(unique_movies)))
        for rating in ratings:
            u_idx = user_to_idx[rating.users.id]
            m_idx = movie_to_idx[rating.movie.id]
            rating_matrix[u_idx, m_idx] = rating.rating

        return rating_matrix, user_to_idx, movie_to_idx
