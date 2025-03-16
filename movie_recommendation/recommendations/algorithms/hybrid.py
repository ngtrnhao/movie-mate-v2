import numpy as np
from recommendations.algorithms.base import RecommendationAlgorithm
from recommendations.algorithms.collaborative_filtering import UserBasedCF
from recommendations.algorithms.content_based import ContentBasedFiltering
from recommendations.algorithms.matrix_factorization import MatrixFactorization
from recommendations.models import Recommendation


class HybridRecommender(RecommendationAlgorithm):
    """Hybrid recommender that combines multiple algorithms"""

    def __init__(self):
        # Initialize component algorithms
        self.collaborative_filtering = UserBasedCF()
        self.content_based = ContentBasedFiltering()
        self.matrix_factorization = MatrixFactorization()

        # Set algorithm weights
        self.weights = {
            'collaborative_filtering': 0.4,
            'content_based': 0.3,
            'matrix_factorization': 0.3
        }

    def train(self):
        """Train all component models"""
        print("Training User-Based Collaborative Filtering model...")
        self.collaborative_filtering.train()

        print("Training Content-Based Filtering model...")
        self.content_based.train()

        print("Training Matrix Factorization model...")
        self.matrix_factorization.train()

        return True

    def recommend(self, user_id, num_recommendations=10):
        """Generate hybrid recommendations by combining multiple algorithms"""
        # Get recommendations from each algorithm
        cf_recs = self.collaborative_filtering.recommend(user_id, num_recommendations=20)
        cb_recs = self.content_based.recommend(user_id, num_recommendations=20)
        mf_recs = self.matrix_factorization.recommend(user_id, num_recommendations=20)

        # Combine recommendations into a unified scoring dictionary
        movie_scores = {}

        # Process collaborative filtering recommendations
        for rec in cf_recs:
            movie_id = rec['movie_id']
            if movie_id not in movie_scores:
                movie_scores[movie_id] = 0
            movie_scores[movie_id] += rec['score'] * self.weights['collaborative_filtering']

        # Process content-based recommendations
        for rec in cb_recs:
            movie_id = rec['movie_id']
            if movie_id not in movie_scores:
                movie_scores[movie_id] = 0
            movie_scores[movie_id] += rec['score'] * self.weights['content_based']

        # Process matrix factorization recommendations
        for rec in mf_recs:
            movie_id = rec['movie_id']
            if movie_id not in movie_scores:
                movie_scores[movie_id] = 0
            movie_scores[movie_id] += rec['score'] * self.weights['matrix_factorization']

        # Sort by score and get top recommendations
        sorted_movies = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)
        top_recommendations = sorted_movies[:num_recommendations]

        # Format recommendations
        recommendations = []
        for movie_id, score in top_recommendations:
            recommendations.append({
                'movie_id': movie_id,
                'score': float(score)
            })

        # Save recommendations to database
        self._save_recommendations(user_id, recommendations)

        return recommendations

    def _save_recommendations(self, user_id, recommendations):
        """Save recommendations to database"""
        # Delete existing hybrid recommendations for this user
        Recommendation.objects.filter(user_id=user_id, algorithm_used='hybrid').delete()

        # Create new recommendation objects
        rec_objects = []
        for rec in recommendations:
            rec_objects.append(Recommendation(
                user_id=user_id,
                recommended_movie_id=rec['movie_id'],
                score=rec['score'],
                algorithm_used='hybrid'
            ))

        # Bulk create
        if rec_objects:
            Recommendation.objects.bulk_create(rec_objects)

    def save_model(self, model_path=None):
        """Save all component models"""
        self.collaborative_filtering.save_model()
        self.content_based.save_model()
        self.matrix_factorization.save_model()
        return True

    def load_model(self, model_path=None):
        """Load all component models"""
        self.collaborative_filtering.load_model()
        self.content_based.load_model()
        self.matrix_factorization.load_model()
        return True
