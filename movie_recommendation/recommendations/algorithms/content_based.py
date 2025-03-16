import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import os
from django.conf import settings
from recommendations.algorithms.base import RecommendationAlgorithm
from recommendations.models import MovieSimilarity, Recommendation
from movies.models import Movie
from metadata.models import Genre
from users.models import Rating


class ContentBasedFiltering(RecommendationAlgorithm):
    """Content-based filtering using TF-IDF on movie metadata"""

    def __init__(self):
        self.movie_features = None
        self.movie_ids = None
        self.tfidf_matrix = None
        self.vectorizer = None
        self.movie_similarity_matrix = None

    def train(self):
        """Train the model by computing movie content features"""
        # Get all movies with their metadata
        movies = Movie.objects.all().prefetch_related('genres')

        # Prepare data for TF-IDF
        movie_data = []
        self.movie_ids = []

        for movie in movies:
            # Combine movie metadata into a single text document
            genres = ' '.join([genre.name for genre in movie.genres.all()])
            text_data = f"{movie.title} {movie.overview} {genres}"
            movie_data.append(text_data)
            self.movie_ids.append(movie.id)

        # Create TF-IDF vectors
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        self.tfidf_matrix = self.vectorizer.fit_transform(movie_data)

        # Compute movie similarity matrix
        self.movie_similarity_matrix = cosine_similarity(self.tfidf_matrix)

        # Save similarities to database for future use
        self._save_similarities_to_db()

        return self.movie_similarity_matrix

    def _save_similarities_to_db(self):
        """Save computed movie similarities to database"""
        # Clear existing similarities
        MovieSimilarity.objects.all().delete()

        # Bulk create new similarities
        similarities = []

        # Only save similarities above threshold to save space
        threshold = 0.3

        for i in range(len(self.movie_similarity_matrix)):
            # Only consider top 20 similar movies for each movie to save space
            sim_scores = self.movie_similarity_matrix[i]
            top_indices = np.argsort(sim_scores)[::-1][:21]  # Include self at index 0

            for j in top_indices[1:]:  # Skip self (first index)
                sim_score = float(sim_scores[j])
                if sim_score > threshold:
                    similarities.append(MovieSimilarity(
                        movie1_id=self.movie_ids[i],
                        movie2_id=self.movie_ids[j],
                        similarity_score=sim_score
                    ))

            if len(similarities) >= 1000:  # Bulk create in batches
                MovieSimilarity.objects.bulk_create(similarities)
                similarities = []

        # Create any remaining similarities
        if similarities:
            MovieSimilarity.objects.bulk_create(similarities)

    def recommend(self, user_id, num_recommendations=10):
        """Generate content-based recommendations for a user"""
        # Get movies rated highly by this user (rating >= 4)
        user_ratings = Rating.objects.filter(
            user_id=user_id, rating__gte=4
        ).select_related('movie')

        if not user_ratings:
            return []  # Can't make content-based recommendations without ratings

        # Calculate scores for each movie based on similarity to liked movies
        movie_scores = {}

        for rating in user_ratings:
            # Find the index of this movie in our movie_ids list
            try:
                movie_idx = self.movie_ids.index(rating.movie_id)
            except ValueError:
                continue  # Movie not in our content matrix

            # Get similarity scores for this movie
            similarity_scores = self.movie_similarity_matrix[movie_idx]

            # Update scores, weighted by user rating
            for i, sim_score in enumerate(similarity_scores):
                movie_id = self.movie_ids[i]
                if movie_id not in movie_scores:
                    movie_scores[movie_id] = 0

                # Weight by both similarity and user's rating
                movie_scores[movie_id] += sim_score * (rating.rating / 5.0)

        # Remove movies the user has already rated
        rated_movie_ids = set(rating.movie_id for rating in user_ratings)
        for movie_id in rated_movie_ids:
            if movie_id in movie_scores:
                del movie_scores[movie_id]

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
        # Delete existing recommendations for this user with this algorithm
        Recommendation.objects.filter(user_id=user_id, algorithm_used='content_based').delete()

        # Create new recommendation objects
        rec_objects = []
        for rec in recommendations:
            rec_objects.append(Recommendation(
                user_id=user_id,
                recommended_movie_id=rec['movie_id'],
                score=rec['score'],
                algorithm_used='content_based'
            ))

        # Bulk create
        if rec_objects:
            Recommendation.objects.bulk_create(rec_objects)

    def save_model(self, model_path=None):
        """Save model to disk"""
        if model_path is None:
            model_path = os.path.join(settings.BASE_DIR, 'models', 'content_based.joblib')

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # Save model data
        model_data = {
            'movie_ids': self.movie_ids,
            'tfidf_matrix': self.tfidf_matrix,
            'vectorizer': self.vectorizer,
            'movie_similarity_matrix': self.movie_similarity_matrix
        }

        joblib.dump(model_data, model_path)
        return model_path

    def load_model(self, model_path=None):
        """Load model from disk"""
        if model_path is None:
            model_path = os.path.join(settings.BASE_DIR, 'models', 'content_based.joblib')

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        model_data = joblib.load(model_path)

        self.movie_ids = model_data['movie_ids']
        self.tfidf_matrix = model_data['tfidf_matrix']
        self.vectorizer = model_data['vectorizer']
        self.movie_similarity_matrix = model_data['movie_similarity_matrix']

        return True
