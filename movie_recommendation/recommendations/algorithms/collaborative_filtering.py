import numpy as np
from scipy.sparse.linalg import svds
from sklearn.metrics.pairwise import cosine_similarity
from recommendations.algorithms.base import RecommendationAlgorithm
from recommendations.models import UserSimilarity, Recommendation
import joblib
import os
from django.conf import settings
from users.models import Users, Rating
from movies.models import Movie


class UserBasedCF(RecommendationAlgorithm):
    """User-based Collaborative Filtering using cosine similarity"""

    def __init__(self):
        self.user_similarity_matrix = None
        self.rating_matrix = None
        self.user_to_idx = None
        self.movie_to_idx = None
        self.idx_to_movie = None

    def train(self):
        """Train the model by computing user similarity matrix"""
        self.rating_matrix, self.user_to_idx, self.movie_to_idx = self.get_user_ratings_matrix()

        # Create reverse mapping
        self.idx_to_movie = {idx: movie_id for movie_id, idx in self.movie_to_idx.items()}

        # Compute user similarity matrix using cosine similarity
        self.user_similarity_matrix = cosine_similarity(self.rating_matrix)

        # Save similarities to database for future use
        self._save_similarities_to_db()

        return self.user_similarity_matrix

    def _save_similarities_to_db(self):
        """Save computed similarities to database"""
        # Clear existing similarities
        UserSimilarity.objects.all().delete()

        # Bulk create new similarities
        similarities = []
        idx_to_user = {idx: user_id for user_id, idx in self.user_to_idx.items()}

        # Only save similarities above threshold to save space
        threshold = 0.1

        for i in range(len(self.user_similarity_matrix)):
            for j in range(i + 1, len(self.user_similarity_matrix)):  # Only upper triangle
                sim_score = self.user_similarity_matrix[i, j]
                if sim_score > threshold:
                    similarities.append(UserSimilarity(
                        user1_id=idx_to_user[i],
                        user2_id=idx_to_user[j],
                        similarity_score=sim_score
                    ))

                    if len(similarities) >= 1000:  # Bulk create in batches
                        UserSimilarity.objects.bulk_create(similarities)
                        similarities = []

        # Create any remaining similarities
        if similarities:
            UserSimilarity.objects.bulk_create(similarities)

    def recommend(self, user_id, num_recommendations=10):
        """Generate recommendations for a user using user-based collaborative filtering"""
        # Check if user exists in our matrix
        if user_id not in self.user_to_idx:
            return []

        user_idx = self.user_to_idx[user_id]

        # Get movies this user has already rated
        user_ratings = Rating.objects.filter(user_id=user_id).values_list('movie_id', flat=True)
        rated_movie_indices = [self.movie_to_idx[mid] for mid in user_ratings if mid in self.movie_to_idx]

        # Get user's row from rating matrix
        user_ratings_vector = self.rating_matrix[user_idx]

        # Initialize predicted ratings
        predicted_ratings = np.zeros(self.rating_matrix.shape[1])

        # For each movie the user hasn't rated
        for movie_idx in range(len(predicted_ratings)):
            if movie_idx in rated_movie_indices:
                continue  # Skip already rated movies

            # Get all users who rated this movie
            movie_raters = np.where(self.rating_matrix[:, movie_idx] > 0)[0]

            if len(movie_raters) == 0:
                continue  # No one rated this movie

            # Calculate weighted average rating based on similarity
            similarities = self.user_similarity_matrix[user_idx, movie_raters]
            ratings = self.rating_matrix[movie_raters, movie_idx]

            # Weighted average
            if np.sum(similarities) > 0:
                predicted_ratings[movie_idx] = np.sum(similarities * ratings) / np.sum(similarities)

        # Get top N recommendations
        movie_indices = np.argsort(predicted_ratings)[::-1][:num_recommendations]
        recommendations = []

        # Convert indices back to movie IDs and create recommendations
        for idx in movie_indices:
            if predicted_ratings[idx] > 0:
                movie_id = self.idx_to_movie[idx]
                recommendations.append({
                    'movie_id': movie_id,
                    'score': float(predicted_ratings[idx]),
                })

        # Save recommendations to database
        self._save_recommendations(user_id, recommendations)

        return recommendations

    def _save_recommendations(self, user_id, recommendations):
        """Save recommendations to database"""
        # Delete existing recommendations for this user
        Recommendation.objects.filter(user_id=user_id, algorithm_used='user_based_cf').delete()

        # Create new recommendation objects
        rec_objects = []
        for rec in recommendations:
            rec_objects.append(Recommendation(
                user_id=user_id,
                recommended_movie_id=rec['movie_id'],
                score=rec['score'],
                algorithm_used='user_based_cf'
            ))

        # Bulk create
        if rec_objects:
            Recommendation.objects.bulk_create(rec_objects)

    def save_model(self, model_path=None):
        """Save model to disk"""
        if model_path is None:
            model_path = os.path.join(settings.BASE_DIR, 'models', 'user_based_cf.joblib')

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # Save model data
        model_data = {
            'user_similarity_matrix': self.user_similarity_matrix,
            'rating_matrix': self.rating_matrix,
            'user_to_idx': self.user_to_idx,
            'movie_to_idx': self.movie_to_idx,
            'idx_to_movie': self.idx_to_movie
        }

        joblib.dump(model_data, model_path)
        return model_path

    def load_model(self, model_path=None):
        """Load model from disk"""
        if model_path is None:
            model_path = os.path.join(settings.BASE_DIR, 'models', 'user_based_cf.joblib')

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        model_data = joblib.load(model_path)

        self.user_similarity_matrix = model_data['user_similarity_matrix']
        self.rating_matrix = model_data['rating_matrix']
        self.user_to_idx = model_data['user_to_idx']
        self.movie_to_idx = model_data['movie_to_idx']
        self.idx_to_movie = model_data['idx_to_movie']

        return True
