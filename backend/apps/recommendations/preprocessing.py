"""
Advanced Data Preprocessing Pipeline for ML-based Recommendation System
Supports Surprise, scikit-learn, TensorFlow and other ML frameworks
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
# Scikit-learn imports with error handling
try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import PCA, TruncatedSVD
    from sklearn.model_selection import train_test_split
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available. Preprocessing features will be limited.")

# SciPy imports with error handling
try:
    from scipy.sparse import csr_matrix, save_npz, load_npz
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available. Sparse matrix operations will be limited.")

# Joblib imports with error handling
try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    logging.warning("Joblib not available. Model persistence will be limited.")
import json
import os

from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.movies.models import Movie, MovieReview
from apps.users.models import UserFavoriteGenre
from apps.metadata.models import Genre
from .models import UserPreference, DemographicCluster

User = get_user_model()
logger = logging.getLogger(__name__)

class DataPreprocessor:
    """
    Comprehensive data preprocessing pipeline for ML recommendation algorithms
    """

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.join(settings.BASE_DIR, 'data', 'ml_processed')
        os.makedirs(self.output_dir, exist_ok=True)

        # Preprocessors storage
        self.scalers = {}
        self.encoders = {}
        self.vectorizers = {}
        self.preprocessed_data = {}

        # Data matrices
        self.rating_matrix = None
        self.user_features = None
        self.movie_features = None

    def prepare_all_data(self, test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]:
        """
        Complete data preparation pipeline for all ML algorithms

        Returns:
            Dict containing all processed datasets
        """
        logger.info("Starting comprehensive data preprocessing...")

        results = {
            'collaborative_filtering': {},
            'demographic_filtering': {},
            'deep_learning': {},
            'metadata': {}
        }

        # 1. Prepare data for Collaborative Filtering (Surprise)
        cf_data = self.prepare_collaborative_filtering_data()
        results['collaborative_filtering'] = cf_data

        # 2. Prepare data for Demographic Filtering
        demo_data = self.prepare_demographic_data()
        results['demographic_filtering'] = demo_data



        # 4. Prepare data for Deep Learning (TensorFlow)
        dl_data = self.prepare_deep_learning_data(test_size, random_state)
        results['deep_learning'] = dl_data

        # 5. Generate metadata and save preprocessors
        metadata = self.generate_metadata()
        results['metadata'] = metadata

        # Save all processed data
        self.save_processed_data(results)

        logger.info("Data preprocessing completed successfully!")
        return results

    def prepare_collaborative_filtering_data(self) -> Dict[str, Any]:
        """
        Prepare data for Surprise library (collaborative filtering)
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("Scikit-learn not available. Limited preprocessing functionality.")

        logger.info("Preparing collaborative filtering data...")

        try:
            # Get rating data
            ratings_df = self._get_ratings_dataframe()

            if ratings_df.empty:
                logger.warning("No rating data available for collaborative filtering")
                return {}

            # Create user-item matrix
            rating_matrix = self._create_rating_matrix(ratings_df)

            # Surprise format data
            surprise_data = self._format_for_surprise(ratings_df)

            # Calculate statistics
            stats = self._calculate_cf_statistics(ratings_df, rating_matrix)

            result = {
                'ratings_df': ratings_df,
                'rating_matrix': rating_matrix,
                'surprise_data': surprise_data,
                'statistics': stats,
                'user_mapping': dict(enumerate(rating_matrix.index)),
                'movie_mapping': dict(enumerate(rating_matrix.columns))
            }

            # Save sparse matrix
            sparse_matrix = csr_matrix(rating_matrix.fillna(0).values)
            save_npz(os.path.join(self.output_dir, 'rating_matrix_sparse.npz'), sparse_matrix)

            logger.info(f"CF data prepared: {len(ratings_df)} ratings, {rating_matrix.shape[0]} users, {rating_matrix.shape[1]} movies")
            return result

        except Exception as e:
            logger.error(f"Error preparing collaborative filtering data: {str(e)}")
            return {}

    def prepare_demographic_data(self) -> Dict[str, Any]:
        """
        Prepare demographic data for demographic filtering
        """
        logger.info("Preparing demographic data...")

        try:
            # Get user demographic data
            users_df = self._get_users_dataframe()

            if users_df.empty:
                logger.warning("No user demographic data available")
                return {}

            # Encode categorical variables
            encoded_demographics = self._encode_demographics(users_df)

            # Create demographic clusters
            cluster_data = self._create_demographic_clusters(encoded_demographics)

            # Scale numerical features
            scaled_demographics = self._scale_demographic_features(encoded_demographics)

            result = {
                'users_df': users_df,
                'encoded_demographics': encoded_demographics,
                'scaled_demographics': scaled_demographics,
                'cluster_data': cluster_data,
                'demographic_statistics': self._calculate_demographic_statistics(users_df)
            }

            logger.info(f"Demographic data prepared: {len(users_df)} users with demographics")
            return result

        except Exception as e:
            logger.error(f"Error preparing demographic data: {str(e)}")
            return {}



    def prepare_deep_learning_data(self, test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]:
        """
        Prepare data for deep learning models (TensorFlow/Keras)
        """
        logger.info("Preparing deep learning data...")

        try:
            # Get comprehensive dataset
            interactions_df = self._get_interactions_dataframe()

            if interactions_df.empty:
                logger.warning("No interaction data available for deep learning")
                return {}

            # Create user and movie embeddings preparation
            user_features = self._prepare_user_embeddings(interactions_df)
            movie_features = self._prepare_movie_embeddings(interactions_df)

            # Create training sequences
            sequences = self._create_interaction_sequences(interactions_df)

            # Split data for training
            train_data, test_data = self._split_deep_learning_data(
                interactions_df, test_size, random_state
            )

            result = {
                'interactions_df': interactions_df,
                'user_features': user_features,
                'movie_features': movie_features,
                'sequences': sequences,
                'train_data': train_data,
                'test_data': test_data,
                'embedding_dimensions': {
                    'user_embedding_dim': len(user_features.columns),
                    'movie_embedding_dim': len(movie_features.columns),
                    'num_users': interactions_df['user_id'].nunique(),
                    'num_movies': interactions_df['movie_id'].nunique()
                }
            }

            logger.info(f"Deep learning data prepared: {len(interactions_df)} interactions")
            return result

        except Exception as e:
            logger.error(f"Error preparing deep learning data: {str(e)}")
            return {}

    def _get_ratings_dataframe(self) -> pd.DataFrame:
        """Get ratings data as pandas DataFrame"""
        ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).select_related('user', 'movie').values(
            'user_id', 'movie_id', 'rating', 'created_at'
        )

        df = pd.DataFrame(ratings)
        if not df.empty:
            df['rating'] = df['rating'].astype(float)
            df['user_id'] = df['user_id'].astype(int)
            df['movie_id'] = df['movie_id'].astype(int)
            df['timestamp'] = pd.to_datetime(df['created_at']).astype(int) // 10**9

        return df

    def _get_users_dataframe(self) -> pd.DataFrame:
        """Get users demographic data as pandas DataFrame"""
        users = User.objects.all().values(
            'id', 'age', 'gender', 'occupation', 'location', 'age_group', 'zip_code'
        )

        df = pd.DataFrame(users)
        if not df.empty:
            df = df.rename(columns={'id': 'user_id'})
            # Handle missing values
            df['age'] = df['age'].fillna(df['age'].median())
            df['gender'] = df['gender'].fillna('Unknown')
            df['occupation'] = df['occupation'].fillna('Other')

        return df

    def _get_movies_dataframe(self) -> pd.DataFrame:
        """Get movies content data as pandas DataFrame"""
        movies = Movie.objects.all().values(
            'id', 'title', 'overview_en', 'overview_vi', 'release_date', 'runtime',
            'avg_rating', 'rating_count', 'popularity_score'
        )

        df = pd.DataFrame(movies)
        if not df.empty:
            df = df.rename(columns={'id': 'movie_id'})
            # Get genres
            movie_genres = self._get_movie_genres_data()
            df = df.merge(movie_genres, on='movie_id', how='left')

            # Handle missing values
            # Combine overview fields
            df['overview'] = (df['overview_en'].fillna('') + ' ' + df['overview_vi'].fillna('')).str.strip()
            df['runtime'] = df['runtime'].fillna(df['runtime'].median())
            df['avg_rating'] = df['avg_rating'].fillna(0)
            df['rating_count'] = df['rating_count'].fillna(0)

        return df

    def _get_interactions_dataframe(self) -> pd.DataFrame:
        """Get comprehensive user-movie interactions"""
        # Combine ratings and other interactions
        ratings_df = self._get_ratings_dataframe()

        # Add implicit feedback data if available
        # This could include views, clicks, favorites, etc.

        return ratings_df

    def _create_rating_matrix(self, ratings_df: pd.DataFrame) -> pd.DataFrame:
        """Create user-item rating matrix"""
        return ratings_df.pivot_table(
            index='user_id',
            columns='movie_id',
            values='rating',
            fill_value=np.nan
        )

    def _format_for_surprise(self, ratings_df: pd.DataFrame) -> List[Tuple]:
        """Format data for Surprise library"""
        return list(ratings_df[['user_id', 'movie_id', 'rating']].itertuples(index=False, name=None))

    def _encode_demographics(self, users_df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical demographic variables"""
        encoded_df = users_df.copy()

        # Label encode categorical variables
        categorical_columns = ['gender', 'occupation', 'age_group']

        for col in categorical_columns:
            if col in encoded_df.columns:
                le = LabelEncoder()
                encoded_df[f'{col}_encoded'] = le.fit_transform(encoded_df[col].astype(str))
                self.encoders[f'{col}_encoder'] = le

        return encoded_df

    def _create_demographic_clusters(self, demographics_df: pd.DataFrame) -> Dict:
        """Create demographic clusters using KMeans"""
        # Select features for clustering
        cluster_features = []
        for col in ['age', 'gender_encoded', 'occupation_encoded']:
            if col in demographics_df.columns:
                cluster_features.append(col)

        if not cluster_features:
            return {}

        # Prepare data for clustering
        X = demographics_df[cluster_features].fillna(0)

        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Perform clustering
        n_clusters = min(8, len(X) // 10)  # Adaptive number of clusters
        if n_clusters < 2:
            n_clusters = 2

        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(X_scaled)

        # Store clustering objects
        self.encoders['demographic_scaler'] = scaler
        self.encoders['demographic_kmeans'] = kmeans

        return {
            'cluster_labels': cluster_labels,
            'n_clusters': n_clusters,
            'cluster_centers': kmeans.cluster_centers_
        }

    def _process_text_features(self, movies_df: pd.DataFrame) -> np.ndarray:
        """Process text features using TF-IDF"""
        # Combine overview fields for text processing
        if 'overview' not in movies_df.columns:
            movies_df['overview'] = (movies_df['overview_en'].fillna('') + ' ' + movies_df['overview_vi'].fillna('')).str.strip()
        text_data = movies_df['overview'].fillna('')

        # TF-IDF Vectorization
        tfidf = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2)
        )

        tfidf_matrix = tfidf.fit_transform(text_data)

        # Dimensionality reduction
        svd = TruncatedSVD(n_components=100, random_state=42)
        reduced_features = svd.fit_transform(tfidf_matrix)

        # Store vectorizers
        self.vectorizers['tfidf'] = tfidf
        self.vectorizers['svd'] = svd

        return reduced_features

    def _process_movie_categorical_features(self, movies_df: pd.DataFrame) -> pd.DataFrame:
        """Process categorical movie features"""
        categorical_df = pd.DataFrame()

        # Process genres if available
        if 'genres' in movies_df.columns:
            # One-hot encode genres
            genres_encoded = self._encode_genres(movies_df)
            categorical_df = pd.concat([categorical_df, genres_encoded], axis=1)

        return categorical_df

    def _process_movie_numerical_features(self, movies_df: pd.DataFrame) -> pd.DataFrame:
        """Process numerical movie features"""
        numerical_columns = ['runtime', 'avg_rating', 'rating_count', 'popularity_score']
        available_columns = [col for col in numerical_columns if col in movies_df.columns]

        if not available_columns:
            return pd.DataFrame()

        numerical_df = movies_df[available_columns].copy()

        # Scale numerical features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(numerical_df.fillna(0))

        scaled_df = pd.DataFrame(
            scaled_features,
            columns=[f'{col}_scaled' for col in available_columns],
            index=numerical_df.index
        )

        self.scalers['movie_numerical_scaler'] = scaler

        return scaled_df

    def save_processed_data(self, results: Dict) -> None:
        """Save all processed data and preprocessors"""
        # Save preprocessors
        joblib.dump(self.scalers, os.path.join(self.output_dir, 'scalers.pkl'))
        joblib.dump(self.encoders, os.path.join(self.output_dir, 'encoders.pkl'))
        joblib.dump(self.vectorizers, os.path.join(self.output_dir, 'vectorizers.pkl'))

        # Save data summaries (not full DataFrames to save space)
        summary = {
            'preprocessing_timestamp': datetime.now().isoformat(),
            'data_shapes': {},
            'feature_counts': {},
            'statistics': {}
        }

        for method, data in results.items():
            if isinstance(data, dict) and data:
                summary['data_shapes'][method] = {}
                for key, value in data.items():
                    if hasattr(value, 'shape'):
                        summary['data_shapes'][method][key] = value.shape
                    elif isinstance(value, dict) and 'statistics' in key:
                        summary['statistics'][method] = value

        # Save summary
        with open(os.path.join(self.output_dir, 'preprocessing_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"Processed data saved to {self.output_dir}")

    def load_processed_data(self) -> Dict:
        """Load previously processed data"""
        try:
            # Load preprocessors
            if os.path.exists(os.path.join(self.output_dir, 'scalers.pkl')):
                self.scalers = joblib.load(os.path.join(self.output_dir, 'scalers.pkl'))

            if os.path.exists(os.path.join(self.output_dir, 'encoders.pkl')):
                self.encoders = joblib.load(os.path.join(self.output_dir, 'encoders.pkl'))

            if os.path.exists(os.path.join(self.output_dir, 'vectorizers.pkl')):
                self.vectorizers = joblib.load(os.path.join(self.output_dir, 'vectorizers.pkl'))

            # Load summary
            summary_path = os.path.join(self.output_dir, 'preprocessing_summary.json')
            if os.path.exists(summary_path):
                with open(summary_path, 'r') as f:
                    summary = json.load(f)
                return summary

            return {}

        except Exception as e:
            logger.error(f"Error loading processed data: {str(e)}")
            return {}

    # Additional helper methods would go here...
    def _get_movie_genres_data(self) -> pd.DataFrame:
        """Helper to get movie genres data"""
        # This would be implemented based on your genre model structure
        return pd.DataFrame()

    def _encode_genres(self, movies_df: pd.DataFrame) -> pd.DataFrame:
        """Helper to encode movie genres"""
        # This would be implemented based on your genre structure
        return pd.DataFrame()

    def _scale_demographic_features(self, demographics_df: pd.DataFrame) -> pd.DataFrame:
        """Scale demographic features"""
        numerical_cols = ['age']
        available_cols = [col for col in numerical_cols if col in demographics_df.columns]

        if not available_cols:
            return demographics_df

        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(demographics_df[available_cols].fillna(0))

        scaled_df = demographics_df.copy()
        for i, col in enumerate(available_cols):
            scaled_df[f'{col}_scaled'] = scaled_features[:, i]

        self.scalers['demographic_scaler'] = scaler
        return scaled_df

    def _calculate_cf_statistics(self, ratings_df: pd.DataFrame, rating_matrix: pd.DataFrame) -> Dict:
        """Calculate collaborative filtering statistics"""
        return {
            'total_ratings': len(ratings_df),
            'unique_users': ratings_df['user_id'].nunique(),
            'unique_movies': ratings_df['movie_id'].nunique(),
            'sparsity': 1 - (len(ratings_df) / (rating_matrix.shape[0] * rating_matrix.shape[1])),
            'avg_rating': ratings_df['rating'].mean(),
            'rating_std': ratings_df['rating'].std()
        }

    def _calculate_demographic_statistics(self, users_df: pd.DataFrame) -> Dict:
        """Calculate demographic statistics"""
        return {
            'total_users': len(users_df),
            'avg_age': users_df['age'].mean() if 'age' in users_df.columns else None,
            'gender_distribution': users_df['gender'].value_counts().to_dict() if 'gender' in users_df.columns else {},
            'occupation_distribution': users_df['occupation'].value_counts().head(10).to_dict() if 'occupation' in users_df.columns else {}
        }



    def _prepare_user_embeddings(self, interactions_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare user features for embeddings"""
        return pd.DataFrame()  # Implementation would depend on available user features

    def _prepare_movie_embeddings(self, interactions_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare movie features for embeddings"""
        return pd.DataFrame()  # Implementation would depend on available movie features

    def _create_interaction_sequences(self, interactions_df: pd.DataFrame) -> List:
        """Create interaction sequences for sequential models"""
        return []  # Implementation for sequential recommendation models

    def _split_deep_learning_data(self, interactions_df: pd.DataFrame, test_size: float, random_state: int) -> Tuple:
        """Split data for deep learning training"""
        return train_test_split(interactions_df, test_size=test_size, random_state=random_state)

    def _combine_movie_features(self, text_features: np.ndarray, categorical_features: pd.DataFrame, numerical_features: pd.DataFrame) -> np.ndarray:
        """Combine all movie features into a single matrix"""
        features_list = []

        if text_features is not None and text_features.size > 0:
            features_list.append(text_features)

        if not categorical_features.empty:
            features_list.append(categorical_features.values)

        if not numerical_features.empty:
            features_list.append(numerical_features.values)

        if features_list:
            return np.hstack(features_list)
        else:
            return np.array([])

    def generate_metadata(self) -> Dict:
        """Generate metadata about the preprocessing"""
        return {
            'timestamp': datetime.now().isoformat(),
            'scalers_available': list(self.scalers.keys()),
            'encoders_available': list(self.encoders.keys()),
            'vectorizers_available': list(self.vectorizers.keys()),
            'output_directory': self.output_dir
        }
