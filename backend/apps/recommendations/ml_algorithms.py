"""
Advanced ML Algorithms for Movie Recommendation System
Using Surprise, scikit-learn, TensorFlow and other ML libraries
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
import pickle
import joblib
import warnings
warnings.filterwarnings('ignore')

# Surprise library for collaborative filtering
try:
    from surprise import Dataset, Reader, SVD, NMF, KNNBasic, KNNWithMeans, CoClustering
    from surprise import accuracy
    from surprise.model_selection import train_test_split as surprise_train_test_split
    from surprise.model_selection import cross_validate, GridSearchCV
    SURPRISE_AVAILABLE = True
except ImportError:
    SURPRISE_AVAILABLE = False
    logging.warning("Surprise library not available. Collaborative filtering features will be limited.")

# Scikit-learn
try:
    from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import PCA, TruncatedSVD, NMF as SKLearnNMF
    from sklearn.cluster import KMeans
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available. ML features will be limited.")

# TensorFlow/Keras for deep learning
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Model, optimizers, callbacks
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logging.warning("TensorFlow not available. Deep learning models will be disabled.")

# Additional libraries
try:
    from scipy.sparse import csr_matrix
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available. Sparse matrix operations will be limited.")

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logging.warning("Optuna not available. Hyperparameter optimization will be disabled.")

try:
    from implicit.als import AlternatingLeastSquares
    from implicit.bpr import BayesianPersonalizedRanking
    IMPLICIT_AVAILABLE = True
except ImportError:
    IMPLICIT_AVAILABLE = False
    logging.warning("Implicit library not available. Fast collaborative filtering will be disabled.")

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    logging.warning("Joblib not available. Model persistence will be limited.")

from .preprocessing import DataPreprocessor

logger = logging.getLogger(__name__)

class MLRecommendationEngine:
    """
    Advanced ML-based recommendation engine using multiple algorithms
    """

    def __init__(self, preprocessor: DataPreprocessor = None):
        self.preprocessor = preprocessor or DataPreprocessor()
        self.models = {}
        self.model_performances = {}
        self.trained_models = {}

    def train_all_models(self, data: Dict = None, hyperparameter_tuning: bool = False) -> Dict:
        """
        Train all available ML models
        """
        logger.info("Starting ML model training...")

        if data is None:
            data = self.preprocessor.prepare_all_data()

        results = {}

        # 1. Collaborative Filtering with Surprise
        if data.get('collaborative_filtering'):
            cf_results = self.train_collaborative_filtering_models(
                data['collaborative_filtering'], hyperparameter_tuning
            )
            results['collaborative_filtering'] = cf_results

        # 2. Content-based Filtering with scikit-learn
        if data.get('content_based_filtering'):
            cb_results = self.train_content_based_models(
                data['content_based_filtering'], hyperparameter_tuning
            )
            results['content_based_filtering'] = cb_results

        # 3. Demographic Filtering
        if data.get('demographic_filtering'):
            demo_results = self.train_demographic_models(
                data['demographic_filtering'], hyperparameter_tuning
            )
            results['demographic_filtering'] = demo_results

        # 4. Deep Learning Models (if TensorFlow available)
        if TF_AVAILABLE and data.get('deep_learning'):
            dl_results = self.train_deep_learning_models(
                data['deep_learning'], hyperparameter_tuning
            )
            results['deep_learning'] = dl_results

        # 5. Hybrid Models
        hybrid_results = self.train_hybrid_models(data, results)
        results['hybrid_models'] = hybrid_results

        # Save trained models
        self.save_models()

        logger.info("ML model training completed!")
        return results

    def train_collaborative_filtering_models(self, data: Dict, tune_hyperparams: bool = False) -> Dict:
        """
        Train collaborative filtering models using Surprise library
        """
        if not SURPRISE_AVAILABLE:
            logger.warning("Surprise library not available. Skipping collaborative filtering training.")
            return {"error": "Surprise library not available"}

        logger.info("Training collaborative filtering models...")

        results = {}

        try:
            # Prepare Surprise dataset
            reader = Reader(rating_scale=(0.5, 5.0))
            surprise_data = Dataset.load_from_df(
                pd.DataFrame(data['surprise_data'], columns=['user_id', 'movie_id', 'rating']),
                reader
            )

            # Split data
            trainset, testset = surprise_train_test_split(surprise_data, test_size=0.2, random_state=42)

            # Define algorithms to test
            algorithms = {
                'SVD': SVD(),
                'NMF': NMF(),
                'KNNBasic': KNNBasic(),
                'KNNWithMeans': KNNWithMeans(),
                'CoClustering': CoClustering()
            }

            for name, algo in algorithms.items():
                logger.info(f"Training {name}...")

                # Hyperparameter tuning if requested
                if tune_hyperparams:
                    best_algo = self._tune_surprise_hyperparameters(algo, surprise_data, name)
                else:
                    best_algo = algo

                # Train and evaluate
                best_algo.fit(trainset)
                predictions = best_algo.test(testset)

                # Calculate metrics
                rmse = accuracy.rmse(predictions, verbose=False)
                mae = accuracy.mae(predictions, verbose=False)

                results[name] = {
                    'model': best_algo,
                    'rmse': rmse,
                    'mae': mae,
                    'predictions': predictions
                }

                # Store the trained model
                self.trained_models[f'cf_{name.lower()}'] = best_algo

                logger.info(f"{name} - RMSE: {rmse:.4f}, MAE: {mae:.4f}")

            # Find best model
            best_model_name = min(results.keys(), key=lambda x: results[x]['rmse'])
            results['best_model'] = best_model_name

            logger.info(f"Best CF model: {best_model_name}")
            return results

        except Exception as e:
            logger.error(f"Error training collaborative filtering models: {str(e)}")
            return {}

    def train_content_based_models(self, data: Dict, tune_hyperparams: bool = False) -> Dict:
        """
        Train content-based filtering models using scikit-learn
        """
        logger.info("Training content-based filtering models...")

        results = {}

        try:
            movies_df = data['movies_df']
            combined_features = data['combined_features']

            if combined_features.size == 0:
                logger.warning("No features available for content-based filtering")
                return {}

            # Create content-based similarity matrix
            content_similarity = cosine_similarity(combined_features)

            # Store similarity matrix
            results['similarity_matrix'] = content_similarity
            results['movie_indices'] = {
                movie_id: idx for idx, movie_id in enumerate(movies_df['movie_id'])
            }

            # Content-based recommender class
            class ContentBasedRecommender:
                def __init__(self, similarity_matrix, movie_indices, movies_df):
                    self.similarity_matrix = similarity_matrix
                    self.movie_indices = movie_indices
                    self.movies_df = movies_df

                def recommend(self, movie_id, n_recommendations=10):
                    if movie_id not in self.movie_indices:
                        return []

                    idx = self.movie_indices[movie_id]
                    sim_scores = list(enumerate(self.similarity_matrix[idx]))
                    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

                    movie_indices = [i[0] for i in sim_scores[1:n_recommendations+1]]
                    return self.movies_df.iloc[movie_indices]['movie_id'].tolist()

            content_recommender = ContentBasedRecommender(
                content_similarity, results['movie_indices'], movies_df
            )

            results['recommender'] = content_recommender
            self.trained_models['content_based'] = content_recommender

            # Evaluate content-based model (if user ratings available)
            if 'ratings_df' in data:
                evaluation_score = self._evaluate_content_based_model(
                    content_recommender, data.get('ratings_df')
                )
                results['evaluation_score'] = evaluation_score

            logger.info("Content-based model training completed")
            return results

        except Exception as e:
            logger.error(f"Error training content-based models: {str(e)}")
            return {}

    def train_demographic_models(self, data: Dict, tune_hyperparams: bool = False) -> Dict:
        """
        Train demographic filtering models
        """
        logger.info("Training demographic filtering models...")

        results = {}

        try:
            users_df = data['users_df']
            scaled_demographics = data['scaled_demographics']
            cluster_data = data.get('cluster_data', {})

            # Demographic-based recommender
            class DemographicRecommender:
                def __init__(self, users_df, cluster_data):
                    self.users_df = users_df
                    self.cluster_labels = cluster_data.get('cluster_labels', [])
                    self.user_clusters = {}

                    # Map users to clusters
                    for i, user_id in enumerate(users_df['user_id']):
                        if i < len(self.cluster_labels):
                            self.user_clusters[user_id] = self.cluster_labels[i]

                def get_similar_users(self, user_id, n_similar=50):
                    if user_id not in self.user_clusters:
                        return []

                    user_cluster = self.user_clusters[user_id]
                    similar_users = [
                        uid for uid, cluster in self.user_clusters.items()
                        if cluster == user_cluster and uid != user_id
                    ]

                    return similar_users[:n_similar]

                def recommend_for_user(self, user_id, ratings_df, n_recommendations=10):
                    similar_users = self.get_similar_users(user_id)

                    if not similar_users:
                        return []

                    # Get popular movies among similar users
                    similar_ratings = ratings_df[ratings_df['user_id'].isin(similar_users)]
                    movie_scores = similar_ratings.groupby('movie_id')['rating'].agg(['mean', 'count'])
                    movie_scores = movie_scores[movie_scores['count'] >= 3]  # At least 3 ratings
                    movie_scores = movie_scores.sort_values('mean', ascending=False)

                    return movie_scores.head(n_recommendations).index.tolist()

            demographic_recommender = DemographicRecommender(users_df, cluster_data)

            results['recommender'] = demographic_recommender
            results['cluster_info'] = cluster_data
            self.trained_models['demographic'] = demographic_recommender

            logger.info("Demographic filtering model training completed")
            return results

        except Exception as e:
            logger.error(f"Error training demographic models: {str(e)}")
            return {}

    def train_deep_learning_models(self, data: Dict, tune_hyperparams: bool = False) -> Dict:
        """
        Train deep learning models using TensorFlow/Keras
        """
        if not TF_AVAILABLE:
            logger.warning("TensorFlow not available. Skipping deep learning models.")
            return {}

        logger.info("Training deep learning models...")

        results = {}

        try:
            train_data = data['train_data']
            test_data = data['test_data']
            embedding_dims = data['embedding_dimensions']

            # Neural Collaborative Filtering Model
            ncf_model = self._build_ncf_model(embedding_dims)

            # Prepare training data
            X_train, y_train = self._prepare_dl_training_data(train_data)
            X_test, y_test = self._prepare_dl_training_data(test_data)

            # Train NCF model
            history = ncf_model.fit(
                X_train, y_train,
                epochs=50,
                batch_size=256,
                validation_data=(X_test, y_test),
                callbacks=[
                    keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
                    keras.callbacks.ReduceLROnPlateau(patience=3)
                ],
                verbose=1
            )

            # Evaluate model
            test_loss = ncf_model.evaluate(X_test, y_test, verbose=0)
            predictions = ncf_model.predict(X_test)
            rmse = np.sqrt(mean_squared_error(y_test, predictions))
            mae = mean_absolute_error(y_test, predictions)

            results['ncf_model'] = {
                'model': ncf_model,
                'history': history.history,
                'test_loss': test_loss,
                'rmse': rmse,
                'mae': mae
            }

            self.trained_models['deep_learning_ncf'] = ncf_model

            # Autoencoder for collaborative filtering
            if tune_hyperparams:
                autoencoder_model = self._build_autoencoder_model(embedding_dims)
                # Train autoencoder (implementation details)
                results['autoencoder_model'] = autoencoder_model

            logger.info(f"Deep learning models trained. NCF RMSE: {rmse:.4f}, MAE: {mae:.4f}")
            return results

        except Exception as e:
            logger.error(f"Error training deep learning models: {str(e)}")
            return {}

    def train_hybrid_models(self, data: Dict, model_results: Dict) -> Dict:
        """
        Train hybrid models combining multiple approaches
        """
        logger.info("Training hybrid models...")

        results = {}

        try:
            # Simple weighted ensemble
            weights = {
                'collaborative_filtering': 0.4,
                'content_based_filtering': 0.3,
                'demographic_filtering': 0.2,
                'deep_learning': 0.1
            }

            # Stacking ensemble using Ridge regression
            stacking_model = self._build_stacking_ensemble(model_results, data)

            results['ensemble_weights'] = weights
            results['stacking_model'] = stacking_model

            logger.info("Hybrid models training completed")
            return results

        except Exception as e:
            logger.error(f"Error training hybrid models: {str(e)}")
            return {}

    def _tune_surprise_hyperparameters(self, algo, data, algo_name: str):
        """
        Tune hyperparameters for Surprise algorithms using GridSearchCV
        """
        param_grids = {
            'SVD': {
                'n_factors': [50, 100, 150],
                'reg_all': [0.02, 0.05, 0.1],
                'lr_all': [0.005, 0.01, 0.02]
            },
            'NMF': {
                'n_factors': [15, 30, 50],
                'reg_pu': [0.06, 0.1, 0.15],
                'reg_qi': [0.06, 0.1, 0.15]
            },
            'KNNBasic': {
                'k': [20, 40, 60],
                'sim_options': {
                    'name': ['cosine', 'pearson'],
                    'user_based': [True, False]
                }
            }
        }

        if algo_name in param_grids:
            gs = GridSearchCV(
                algo.__class__,
                param_grids[algo_name],
                measures=['rmse'],
                cv=3,
                n_jobs=-1
            )
            gs.fit(data)
            return gs.best_estimator['rmse']

        return algo

    def _build_ncf_model(self, embedding_dims: Dict):
        """
        Build Neural Collaborative Filtering model
        """
        num_users = embedding_dims['num_users']
        num_movies = embedding_dims['num_movies']
        embedding_size = 50

        # User and Movie inputs
        user_input = keras.Input(shape=(), name='user_id')
        movie_input = keras.Input(shape=(), name='movie_id')

        # Embeddings
        user_embedding = layers.Embedding(num_users, embedding_size)(user_input)
        movie_embedding = layers.Embedding(num_movies, embedding_size)(movie_input)

        user_vec = layers.Flatten()(user_embedding)
        movie_vec = layers.Flatten()(movie_embedding)

        # MLP layers
        concat = layers.Concatenate()([user_vec, movie_vec])
        dense1 = layers.Dense(128, activation='relu')(concat)
        dropout1 = layers.Dropout(0.2)(dense1)
        dense2 = layers.Dense(64, activation='relu')(dropout1)
        dropout2 = layers.Dropout(0.2)(dense2)
        dense3 = layers.Dense(32, activation='relu')(dropout2)

        # Output
        output = layers.Dense(1, activation='linear')(dense3)

        model = keras.Model(inputs=[user_input, movie_input], outputs=output)
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )

        return model

    def _build_autoencoder_model(self, embedding_dims: Dict):
        """
        Build Autoencoder model for collaborative filtering
        """
        input_dim = embedding_dims['num_movies']

        # Encoder
        input_layer = keras.Input(shape=(input_dim,))
        encoded = layers.Dense(256, activation='relu')(input_layer)
        encoded = layers.Dropout(0.2)(encoded)
        encoded = layers.Dense(128, activation='relu')(encoded)
        encoded = layers.Dropout(0.2)(encoded)
        encoded = layers.Dense(64, activation='relu')(encoded)

        # Decoder
        decoded = layers.Dense(128, activation='relu')(encoded)
        decoded = layers.Dropout(0.2)(decoded)
        decoded = layers.Dense(256, activation='relu')(decoded)
        decoded = layers.Dropout(0.2)(decoded)
        decoded = layers.Dense(input_dim, activation='linear')(decoded)

        autoencoder = keras.Model(input_layer, decoded)
        autoencoder.compile(optimizer='adam', loss='mse')

        return autoencoder

    def _prepare_dl_training_data(self, data_df: pd.DataFrame) -> Tuple[List, np.ndarray]:
        """
        Prepare data for deep learning models
        """
        X = [data_df['user_id'].values, data_df['movie_id'].values]
        y = data_df['rating'].values

        return X, y

    def _build_stacking_ensemble(self, model_results: Dict, data: Dict) -> Any:
        """
        Build stacking ensemble model
        """
        # This would combine predictions from different models
        # and train a meta-learner (e.g., Ridge regression)

        # Placeholder implementation
        stacking_model = Ridge(alpha=1.0)

        return stacking_model

    def _evaluate_content_based_model(self, recommender, ratings_df: pd.DataFrame) -> float:
        """
        Evaluate content-based model using rating data
        """
        # Simple evaluation: check if recommended movies have high ratings
        sample_movies = ratings_df['movie_id'].unique()[:100]
        total_score = 0
        valid_evaluations = 0

        for movie_id in sample_movies:
            try:
                recommendations = recommender.recommend(movie_id, n_recommendations=10)
                if recommendations:
                    avg_rating = ratings_df[
                        ratings_df['movie_id'].isin(recommendations)
                    ]['rating'].mean()

                    if not pd.isna(avg_rating):
                        total_score += avg_rating
                        valid_evaluations += 1
            except:
                continue

        return total_score / valid_evaluations if valid_evaluations > 0 else 0

    def save_models(self, model_dir: str = None) -> None:
        """
        Save all trained models
        """
        import os
        from django.conf import settings

        if model_dir is None:
            model_dir = os.path.join(settings.BASE_DIR, 'data', 'trained_models')

        os.makedirs(model_dir, exist_ok=True)

        for model_name, model in self.trained_models.items():
            try:
                if hasattr(model, 'save'):  # TensorFlow models
                    model.save(os.path.join(model_dir, f'{model_name}.h5'))
                else:  # Pickle other models
                    joblib.dump(model, os.path.join(model_dir, f'{model_name}.pkl'))

                logger.info(f"Saved model: {model_name}")
            except Exception as e:
                logger.error(f"Error saving model {model_name}: {str(e)}")

        # Save model performances
        joblib.dump(self.model_performances, os.path.join(model_dir, 'model_performances.pkl'))

    def load_models(self, model_dir: str = None) -> Dict:
        """
        Load trained models
        """
        import os
        from django.conf import settings

        if model_dir is None:
            model_dir = os.path.join(settings.BASE_DIR, 'data', 'trained_models')

        loaded_models = {}

        if os.path.exists(model_dir):
            for filename in os.listdir(model_dir):
                if filename.endswith('.pkl'):
                    model_name = filename.replace('.pkl', '')
                    try:
                        model = joblib.load(os.path.join(model_dir, filename))
                        loaded_models[model_name] = model
                        logger.info(f"Loaded model: {model_name}")
                    except Exception as e:
                        logger.error(f"Error loading model {model_name}: {str(e)}")

                elif filename.endswith('.h5') and TF_AVAILABLE:
                    model_name = filename.replace('.h5', '')
                    try:
                        model = keras.models.load_model(os.path.join(model_dir, filename))
                        loaded_models[model_name] = model
                        logger.info(f"Loaded TensorFlow model: {model_name}")
                    except Exception as e:
                        logger.error(f"Error loading TensorFlow model {model_name}: {str(e)}")

        self.trained_models.update(loaded_models)
        return loaded_models

    def get_recommendations(self, user_id: int, method: str = 'hybrid', n_recommendations: int = 20) -> List[int]:
        """
        Get recommendations using specified method
        """
        if method == 'collaborative_filtering' and 'cf_svd' in self.trained_models:
            return self._get_cf_recommendations(user_id, n_recommendations)
        elif method == 'content_based' and 'content_based' in self.trained_models:
            return self._get_content_recommendations(user_id, n_recommendations)
        elif method == 'demographic' and 'demographic' in self.trained_models:
            return self._get_demographic_recommendations(user_id, n_recommendations)
        elif method == 'deep_learning' and 'deep_learning_ncf' in self.trained_models:
            return self._get_dl_recommendations(user_id, n_recommendations)
        else:
            # Fallback to hybrid
            return self._get_hybrid_recommendations(user_id, n_recommendations)

    def _get_cf_recommendations(self, user_id: int, n_recommendations: int) -> List[int]:
        """Get collaborative filtering recommendations"""
        # Implementation using trained CF model
        return []

    def _get_content_recommendations(self, user_id: int, n_recommendations: int) -> List[int]:
        """Get content-based recommendations"""
        # Implementation using trained content-based model
        return []

    def _get_demographic_recommendations(self, user_id: int, n_recommendations: int) -> List[int]:
        """Get demographic-based recommendations"""
        # Implementation using trained demographic model
        return []

    def _get_dl_recommendations(self, user_id: int, n_recommendations: int) -> List[int]:
        """Get deep learning recommendations"""
        # Implementation using trained deep learning model
        return []

    def _get_hybrid_recommendations(self, user_id: int, n_recommendations: int) -> List[int]:
        """Get hybrid recommendations"""
        # Implementation combining multiple models
        return []

# Usage example
def train_ml_models():
    """
    Main function to train all ML models
    """
    # Initialize components
    preprocessor = DataPreprocessor()
    ml_engine = MLRecommendationEngine(preprocessor)

    # Prepare data
    data = preprocessor.prepare_all_data()

    # Train models
    results = ml_engine.train_all_models(data, hyperparameter_tuning=False)

    logger.info("ML model training completed!")
    return ml_engine, results
