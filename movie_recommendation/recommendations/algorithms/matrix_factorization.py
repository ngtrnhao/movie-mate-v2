import numpy as np
from scipy.sparse.linalg import svds
import joblib
import os
from django.conf import settings
from recommendations.algorithms.base import RecommendationAlgorithm
from recommendations.models import Recommendation
from users.models import Rating


class MatrixFactorization(RecommendationAlgorithm):
    """Matrix Factorization using Singular Value Decomposition (SVD)"""

    def __init__(self, num_factors=50):
        self.num_factors = num_factors
        self.user_features = None
        self.movie_features = None
        self.rating_mean = None
        self.rating_matrix = None
        self.user_to_idx = None
        self.movie_to_idx = None
        self.idx_to_movie = None
        self.idx_to_user = None

    def train(self):
        """Train the SVD model"""
        # Get user-item rating matrix
        self.rating_matrix, self.user_to_idx, self.movie_to_idx = self.get_user_ratings_matrix()

        # Create reverse mappings
        self.idx_to_movie = {idx: movie_id for movie_id, idx in self.movie_to_idx.items()}
        self.idx_to_user = {idx: user_id for user_id, idx in self.user_to_idx.items()}

        # Calculate the mean rating for each user and center the data
        self.rating_mean = np.mean(self.rating_matrix, axis=1).reshape(-1, 1)
        ratings_centered = self.rating_matrix - self.rating_mean

        # Replace NaN values with zeros
        ratings_centered = np.nan_to_num(ratings_centered)

        # Compute SVD
        u, sigma, vt = svds(ratings_centered, k=min(self.num_factors, min(ratings_centered.shape) - 1))

        # Convert sigma to diagonal matrix
        sigma_diag = np.diag(sigma)

        # Store the factorized matrices
        self.user_features = u
        self.movie_features = vt.T

        # Reconstruct the rating matrix
        predicted_ratings = np.dot(np.dot(u, sigma_diag), vt) + self.rating_mean

        return predicted_ratings

    def recommend(self, user_id, num_recommendations=10):
        """Generate recommendations for a user using matrix factorization"""
        # Check if user exists in our matrix
        if user_id not in self.user_to_idx:
            return []

        user_idx = self.user_to_idx[user_id]

        # Get predicted ratings for this user
        predicted_ratings = np.dot(self.user_features[user_idx], self.movie_features.T) + self.rating_mean[user_idx]

        # Get movies this user has already rated
        user_ratings = Rating.objects.filter(user_id=user_id).values_list('movie_id', flat=True)
        rated_movie_indices = [self.movie_to_idx[mid] for mid in user_ratings if mid in self.movie_to_idx]

        # Set rated movies to lowest value so they won't be recommended
        for idx in rated_movie_indices:
            predicted_ratings[idx] = float('-inf')

        # Get top N movie indices
        movie_indices = np.argsort(predicted_ratings)[::-1][:num_recommendations]

        # Format recommendations
        recommendations = []
        for idx in movie_indices:
            if idx in self.idx_to_movie:
                movie_id = self.idx_to_movie[idx]
                recommendations.append({
                    'movie_id': movie_id,
                    'score': float(predicted_ratings[idx])
                })

        # Save recommendations to database
        self._save_recommendations(user_id, recommendations)

        return recommendations

    def _save_recommendations(self, user_id, recommendations):
        """Save recommendations to database"""
        # Delete existing recommendations for this user
        Recommendation.objects.filter(user_id=user_id, algorithm_used='matrix_factorization').delete()

        # Create new recommendation objects
        rec_objects = []
        for rec in recommendations:
            rec_objects.append(Recommendation(
                user_id=user_id,
                recommended_movie_id=rec['movie_id'],
                score=rec['score'],
                algorithm_used='matrix_factorization'
            ))

        # Bulk create
        if rec_objects:
            Recommendation.objects.bulk_create(rec_objects)

    def save_model(self, model_path=None):
        """Save model to disk"""
        if model_path is None:
            model_path = os.path.join(settings.BASE_DIR, 'models', 'matrix_factorization.joblib')

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # Save model data
        model_data = {
            'user_features': self.user_features,
            'movie_features': self.movie_features,
            'rating_mean': self.rating_mean,
            'user_to_idx': self.user_to_idx,
            'movie_to_idx': self.movie_to_idx,
            'idx_to_movie': self.idx_to_movie,
            'idx_to_user': self.idx_to_user,
            'num_factors': self.num_factors
        }

        joblib.dump(model_data, model_path)
        return model_path

    def load_model(self, model_path=None):
        """Load model from disk"""
        if model_path is None:
            model_path = os.path.join(settings.BASE_DIR, 'models', 'matrix_factorization.joblib')

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        model_data = joblib.load(model_path)

        self.user_features = model_data['user_features']
        self.movie_features = model_data['movie_features']
        self.rating_mean = model_data['rating_mean']
        self.user_to_idx = model_data['user_to_idx']
        self.movie_to_idx = model_data['movie_to_idx']
        self.idx_to_movie = model_data['idx_to_movie']
        self.idx_to_user = model_data['idx_to_user']
        self.num_factors = model_data['num_factors']

        return True
