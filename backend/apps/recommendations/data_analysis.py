"""
Data Analysis and Preprocessing Assessment for ML-based Recommendation System
Using Surprise, scikit-learn, TensorFlow and other ML libraries
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
from django.db import models
from django.db.models import Count, Avg, Max, Min, Q
from django.contrib.auth import get_user_model

# Optional visualization imports
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logging.warning("Matplotlib/Seaborn not available. Visualization features will be disabled.")

from apps.movies.models import Movie, MovieReview, MovieRating
from apps.users.models import UserFavoriteGenre
from apps.metadata.models import Genre
from .models import UserPreference, DemographicCluster

User = get_user_model()
logger = logging.getLogger(__name__)

class DatasetAnalyzer:
    """
    Comprehensive analysis of current dataset for ML recommendation algorithms
    """

    def __init__(self):
        self.user_count = 0
        self.movie_count = 0
        self.rating_count = 0
        self.sparsity = 0.0
        self.analysis_results = {}

    def analyze_dataset_completeness(self) -> Dict:
        """
        Analyze dataset completeness and quality for ML algorithms
        """
        results = {
            'dataset_quality': {},
            'preprocessing_needed': [],
            'ml_readiness': {},
            'recommended_libraries': []
        }

        # 1. Basic Statistics
        basic_stats = self._analyze_basic_statistics()
        results['dataset_quality']['basic_stats'] = basic_stats

        # 2. Rating Matrix Analysis
        rating_analysis = self._analyze_rating_matrix()
        results['dataset_quality']['rating_matrix'] = rating_analysis

        # 3. User Demographics Analysis
        demographics_analysis = self._analyze_user_demographics()
        results['dataset_quality']['demographics'] = demographics_analysis

        # 4. Movie Features Analysis
        movie_features = self._analyze_movie_features()
        results['dataset_quality']['movie_features'] = movie_features

        # 5. Temporal Analysis
        temporal_analysis = self._analyze_temporal_patterns()
        results['dataset_quality']['temporal'] = temporal_analysis

        # 6. Determine preprocessing needs
        preprocessing_needs = self._determine_preprocessing_needs(results['dataset_quality'])
        results['preprocessing_needed'] = preprocessing_needs

        # 7. ML Algorithm Readiness
        ml_readiness = self._assess_ml_readiness(results['dataset_quality'])
        results['ml_readiness'] = ml_readiness

        # 8. Recommend appropriate libraries
        library_recommendations = self._recommend_libraries(results)
        results['recommended_libraries'] = library_recommendations

        return results

    def _analyze_basic_statistics(self) -> Dict:
        """Analyze basic dataset statistics"""
        try:
            # User statistics
            user_stats = User.objects.aggregate(
                total_users=Count('id'),
                users_with_ratings=Count('movie_interactions', distinct=True),
                users_with_demographics=Count('age', filter=Q(age__isnull=False))
            )

            # Movie statistics
            movie_stats = Movie.objects.aggregate(
                total_movies=Count('id'),
                movies_with_ratings=Count('reviews', filter=Q(reviews__review_type='USER')),
                movies_with_metadata=Count('overview_en', filter=Q(overview_en__isnull=False) | Q(overview_vi__isnull=False))
            )

            # Rating statistics
            rating_stats = MovieReview.objects.filter(
                review_type='USER',
                rating__isnull=False
            ).aggregate(
                total_ratings=Count('id'),
                avg_rating=Avg('rating'),
                min_rating=Min('rating'),
                max_rating=Max('rating'),
                unique_users=Count('user', distinct=True),
                unique_movies=Count('movie', distinct=True)
            )

            # Calculate sparsity
            if rating_stats['unique_users'] and rating_stats['unique_movies']:
                possible_ratings = rating_stats['unique_users'] * rating_stats['unique_movies']
                actual_ratings = rating_stats['total_ratings']
                sparsity = 1 - (actual_ratings / possible_ratings)
            else:
                sparsity = 1.0

            self.user_count = user_stats['total_users']
            self.movie_count = movie_stats['total_movies']
            self.rating_count = rating_stats['total_ratings']
            self.sparsity = sparsity

            return {
                'users': user_stats,
                'movies': movie_stats,
                'ratings': rating_stats,
                'sparsity': sparsity,
                'density': 1 - sparsity
            }

        except Exception as e:
            logger.error(f"Error analyzing basic statistics: {str(e)}")
            return {}

    def _analyze_rating_matrix(self) -> Dict:
        """Analyze rating matrix properties for collaborative filtering"""
        try:
            # Get rating distribution
            rating_distribution = MovieReview.objects.filter(
                review_type='USER',
                rating__isnull=False
            ).values('rating').annotate(count=Count('rating')).order_by('rating')

            # User rating behavior
            user_rating_stats = MovieReview.objects.filter(
                review_type='USER',
                rating__isnull=False
            ).values('user').annotate(
                rating_count=Count('rating'),
                avg_rating=Avg('rating'),
                rating_std=models.StdDev('rating')
            ).aggregate(
                avg_ratings_per_user=Avg('rating_count'),
                min_ratings_per_user=Min('rating_count'),
                max_ratings_per_user=Max('rating_count'),
                users_with_5plus_ratings=Count('rating_count', filter=Q(rating_count__gte=5)),
                users_with_20plus_ratings=Count('rating_count', filter=Q(rating_count__gte=20))
            )

            # Movie rating behavior
            movie_rating_stats = MovieReview.objects.filter(
                review_type='USER',
                rating__isnull=False
            ).values('movie').annotate(
                rating_count=Count('rating'),
                avg_rating=Avg('rating')
            ).aggregate(
                avg_ratings_per_movie=Avg('rating_count'),
                min_ratings_per_movie=Min('rating_count'),
                max_ratings_per_movie=Max('rating_count'),
                movies_with_5plus_ratings=Count('rating_count', filter=Q(rating_count__gte=5)),
                movies_with_20plus_ratings=Count('rating_count', filter=Q(rating_count__gte=20))
            )

            return {
                'rating_distribution': list(rating_distribution),
                'user_stats': user_rating_stats,
                'movie_stats': movie_rating_stats,
                'sparsity': self.sparsity,
                'cf_readiness': {
                    'sufficient_ratings': self.rating_count > 1000,
                    'sufficient_users': user_rating_stats['users_with_5plus_ratings'] > 100,
                    'sufficient_movies': movie_rating_stats['movies_with_5plus_ratings'] > 100,
                    'acceptable_sparsity': self.sparsity < 0.99
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing rating matrix: {str(e)}")
            return {}

    def _analyze_user_demographics(self) -> Dict:
        """Analyze user demographic data for demographic filtering"""
        try:
            # Demographics completeness
            demographics_stats = User.objects.aggregate(
                total_users=Count('id'),
                users_with_age=Count('age', filter=Q(age__isnull=False)),
                users_with_gender=Count('gender', filter=Q(gender__isnull=False)),
                users_with_occupation=Count('occupation', filter=Q(occupation__isnull=False)),
                users_with_location=Count('location', filter=Q(location__isnull=False)),
                users_with_complete_demographics=Count(
                    'id',
                    filter=Q(
                        age__isnull=False,
                        gender__isnull=False,
                        occupation__isnull=False
                    )
                )
            )

            # Age distribution
            age_distribution = User.objects.filter(
                age__isnull=False
            ).values('age_group').annotate(count=Count('age_group')).order_by('age_group')

            # Gender distribution
            gender_distribution = User.objects.filter(
                gender__isnull=False
            ).values('gender').annotate(count=Count('gender')).order_by('gender')

            # Occupation distribution
            occupation_distribution = User.objects.filter(
                occupation__isnull=False
            ).values('occupation').annotate(count=Count('occupation')).order_by('-count')[:10]

            # Calculate demographics completeness percentage
            total_users = demographics_stats['total_users']
            demographics_completeness = {
                'age': (demographics_stats['users_with_age'] / total_users * 100) if total_users > 0 else 0,
                'gender': (demographics_stats['users_with_gender'] / total_users * 100) if total_users > 0 else 0,
                'occupation': (demographics_stats['users_with_occupation'] / total_users * 100) if total_users > 0 else 0,
                'location': (demographics_stats['users_with_location'] / total_users * 100) if total_users > 0 else 0,
                'complete': (demographics_stats['users_with_complete_demographics'] / total_users * 100) if total_users > 0 else 0
            }

            return {
                'stats': demographics_stats,
                'completeness_percentage': demographics_completeness,
                'age_distribution': list(age_distribution),
                'gender_distribution': list(gender_distribution),
                'occupation_distribution': list(occupation_distribution),
                'demographic_filtering_readiness': {
                    'sufficient_demographic_coverage': demographics_completeness['complete'] > 30,
                    'age_coverage': demographics_completeness['age'] > 50,
                    'gender_coverage': demographics_completeness['gender'] > 50,
                    'occupation_coverage': demographics_completeness['occupation'] > 30
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing user demographics: {str(e)}")
            return {}

    def _analyze_movie_features(self) -> Dict:
        """Analyze movie features for content-based filtering"""
        try:
            # Basic movie metadata completeness
            movie_metadata = Movie.objects.aggregate(
                total_movies=Count('id'),
                movies_with_overview=Count('overview_en', filter=Q(overview_en__isnull=False) | Q(overview_vi__isnull=False)),
                movies_with_genres=Count('genres', filter=Q(genres__isnull=False)),
                movies_with_cast=Count('cast', filter=Q(cast__isnull=False)),
                movies_with_poster=Count('poster_url', filter=Q(poster_url__isnull=False)),
                movies_with_release_date=Count('release_date', filter=Q(release_date__isnull=False))
            )

            # Genre analysis
            genre_stats = Genre.objects.aggregate(
                total_genres=Count('id'),
                avg_movies_per_genre=Avg('movie_set__count')
            )

            # Genre distribution
            genre_distribution = Genre.objects.annotate(
                movie_count=Count('movie_set')
            ).order_by('-movie_count')[:15]

            # Calculate content features completeness
            total_movies = movie_metadata['total_movies']
            content_completeness = {
                'overview': (movie_metadata['movies_with_overview'] / total_movies * 100) if total_movies > 0 else 0,
                'genres': (movie_metadata['movies_with_genres'] / total_movies * 100) if total_movies > 0 else 0,
                'cast': (movie_metadata['movies_with_cast'] / total_movies * 100) if total_movies > 0 else 0,
                'poster': (movie_metadata['movies_with_poster'] / total_movies * 100) if total_movies > 0 else 0,
                'release_date': (movie_metadata['movies_with_release_date'] / total_movies * 100) if total_movies > 0 else 0
            }

            return {
                'metadata_stats': movie_metadata,
                'genre_stats': genre_stats,
                'content_completeness': content_completeness,
                'genre_distribution': [
                    {'name': g.name, 'movie_count': g.movie_count}
                    for g in genre_distribution
                ],
                'content_based_readiness': {
                    'sufficient_text_features': content_completeness['overview'] > 70,
                    'sufficient_genre_coverage': content_completeness['genres'] > 80,
                    'sufficient_cast_info': content_completeness['cast'] > 60,
                    'sufficient_metadata': content_completeness['overview'] > 50 and content_completeness['genres'] > 70
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing movie features: {str(e)}")
            return {}

    def _analyze_temporal_patterns(self) -> Dict:
        """Analyze temporal patterns in ratings and interactions"""
        try:
            # Rating temporal patterns
            rating_temporal = MovieReview.objects.filter(
                review_type='USER',
                rating__isnull=False
            ).aggregate(
                oldest_rating=Min('created_at'),
                newest_rating=Max('created_at'),
                total_ratings=Count('id')
            )

            # Calculate time span
            if rating_temporal['oldest_rating'] and rating_temporal['newest_rating']:
                time_span = (rating_temporal['newest_rating'] - rating_temporal['oldest_rating']).days
            else:
                time_span = 0

            # Recent activity (last 30 days)
            recent_cutoff = datetime.now() - timedelta(days=30)
            recent_activity = MovieReview.objects.filter(
                review_type='USER',
                rating__isnull=False,
                created_at__gte=recent_cutoff
            ).count()

            return {
                'time_span_days': time_span,
                'total_ratings': rating_temporal['total_ratings'],
                'recent_ratings_30d': recent_activity,
                'activity_rate': recent_activity / 30 if recent_activity > 0 else 0,
                'temporal_readiness': {
                    'sufficient_history': time_span > 30,
                    'active_community': recent_activity > 10,
                    'consistent_activity': recent_activity / 30 > 1 if recent_activity > 0 else False
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing temporal patterns: {str(e)}")
            return {}

    def _determine_preprocessing_needs(self, dataset_quality: Dict) -> List[str]:
        """Determine what preprocessing steps are needed"""
        preprocessing_needs = []

        # Check rating matrix
        if 'rating_matrix' in dataset_quality:
            rating_stats = dataset_quality['rating_matrix']
            if self.sparsity > 0.95:
                preprocessing_needs.append("Matrix factorization/dimensionality reduction needed due to high sparsity")
            if rating_stats.get('user_stats', {}).get('avg_ratings_per_user', 0) < 5:
                preprocessing_needs.append("User clustering needed due to insufficient ratings per user")

        # Check demographics
        if 'demographics' in dataset_quality:
            demo_stats = dataset_quality['demographics']
            completeness = demo_stats.get('completeness_percentage', {})
            if completeness.get('complete', 0) < 50:
                preprocessing_needs.append("Demographic imputation needed for missing values")
            if completeness.get('age', 0) < 70:
                preprocessing_needs.append("Age group binning and normalization needed")

        # Check movie features
        if 'movie_features' in dataset_quality:
            content_stats = dataset_quality['movie_features']
            completeness = content_stats.get('content_completeness', {})
            if completeness.get('overview', 0) > 50:
                preprocessing_needs.append("Text preprocessing needed for movie overviews (TF-IDF, word2vec)")
            if completeness.get('genres', 0) > 70:
                preprocessing_needs.append("Genre encoding and feature engineering needed")
            if completeness.get('cast', 0) > 50:
                preprocessing_needs.append("Cast information extraction and encoding needed")

        # Always needed preprocessing
        preprocessing_needs.extend([
            "Feature scaling and normalization for numerical features",
            "Categorical encoding for demographics and genres",
            "Train/validation/test split preparation",
            "Cross-validation setup for model evaluation"
        ])

        return preprocessing_needs

    def _assess_ml_readiness(self, dataset_quality: Dict) -> Dict:
        """Assess readiness for different ML approaches"""
        readiness = {
            'collaborative_filtering': False,
            'demographic_filtering': False,
            'content_based_filtering': False,
            'deep_learning': False,
            'hybrid_approaches': False
        }

        # Collaborative Filtering readiness
        if 'rating_matrix' in dataset_quality:
            cf_ready = dataset_quality['rating_matrix'].get('cf_readiness', {})
            readiness['collaborative_filtering'] = all([
                cf_ready.get('sufficient_ratings', False),
                cf_ready.get('sufficient_users', False),
                cf_ready.get('sufficient_movies', False),
                cf_ready.get('acceptable_sparsity', False)
            ])

        # Demographic Filtering readiness
        if 'demographics' in dataset_quality:
            demo_ready = dataset_quality['demographics'].get('demographic_filtering_readiness', {})
            readiness['demographic_filtering'] = demo_ready.get('sufficient_demographic_coverage', False)

        # Content-based Filtering readiness
        if 'movie_features' in dataset_quality:
            content_ready = dataset_quality['movie_features'].get('content_based_readiness', {})
            readiness['content_based_filtering'] = content_ready.get('sufficient_metadata', False)

        # Deep Learning readiness (needs more data)
        readiness['deep_learning'] = (
            self.rating_count > 10000 and
            self.user_count > 1000 and
            self.movie_count > 1000
        )

        # Hybrid approaches (if at least 2 methods are ready)
        ready_methods = sum([
            readiness['collaborative_filtering'],
            readiness['demographic_filtering'],
            readiness['content_based_filtering']
        ])
        readiness['hybrid_approaches'] = ready_methods >= 2

        return readiness

    def _recommend_libraries(self, analysis_results: Dict) -> List[Dict]:
        """Recommend appropriate ML libraries based on analysis"""
        recommendations = []

        ml_readiness = analysis_results.get('ml_readiness', {})

        # Surprise for Collaborative Filtering
        if ml_readiness.get('collaborative_filtering', False):
            recommendations.append({
                'library': 'Surprise',
                'use_case': 'Collaborative Filtering',
                'algorithms': ['SVD', 'NMF', 'KNNBasic', 'KNNWithMeans', 'CoClustering'],
                'priority': 'High',
                'reason': 'Specialized for collaborative filtering with rating matrices'
            })

        # scikit-learn for general ML
        recommendations.append({
            'library': 'scikit-learn',
            'use_case': 'Feature Engineering, Clustering, Classification',
            'algorithms': ['KMeans', 'TF-IDF', 'RandomForest', 'PCA', 'MinMaxScaler'],
            'priority': 'High',
            'reason': 'Essential for preprocessing and traditional ML algorithms'
        })

        # TensorFlow/Keras for Deep Learning
        if ml_readiness.get('deep_learning', False):
            recommendations.append({
                'library': 'TensorFlow/Keras',
                'use_case': 'Neural Collaborative Filtering, Deep Learning',
                'algorithms': ['Neural CF', 'Autoencoders', 'Deep Factorization Machines'],
                'priority': 'Medium',
                'reason': 'Advanced deep learning approaches for large datasets'
            })

        # Additional libraries
        recommendations.extend([
            {
                'library': 'pandas',
                'use_case': 'Data manipulation and analysis',
                'algorithms': ['Data cleaning', 'Feature engineering', 'EDA'],
                'priority': 'High',
                'reason': 'Essential for data preprocessing and analysis'
            },
            {
                'library': 'numpy',
                'use_case': 'Numerical computations',
                'algorithms': ['Matrix operations', 'Statistical calculations'],
                'priority': 'High',
                'reason': 'Core numerical operations for ML'
            },
            {
                'library': 'scipy',
                'use_case': 'Statistical analysis and optimization',
                'algorithms': ['Sparse matrices', 'Distance metrics', 'Optimization'],
                'priority': 'Medium',
                'reason': 'Advanced statistical operations and sparse matrix handling'
            }
        ])

        # Text processing libraries
        if analysis_results.get('dataset_quality', {}).get('movie_features', {}).get('content_completeness', {}).get('overview', 0) > 50:
            recommendations.extend([
                {
                    'library': 'nltk/spacy',
                    'use_case': 'Text preprocessing',
                    'algorithms': ['Tokenization', 'Lemmatization', 'Named Entity Recognition'],
                    'priority': 'Medium',
                    'reason': 'Text processing for movie descriptions and reviews'
                },
                {
                    'library': 'gensim',
                    'use_case': 'Topic modeling and word embeddings',
                    'algorithms': ['Word2Vec', 'Doc2Vec', 'LDA'],
                    'priority': 'Low',
                    'reason': 'Advanced text analysis for content-based filtering'
                }
            ])

        return recommendations

    def generate_analysis_report(self) -> str:
        """Generate a comprehensive analysis report"""
        results = self.analyze_dataset_completeness()

        report = f"""
# Dataset Analysis Report for ML-based Recommendation System

## Dataset Overview
- Total Users: {self.user_count:,}
- Total Movies: {self.movie_count:,}
- Total Ratings: {self.rating_count:,}
- Matrix Sparsity: {self.sparsity:.4f} ({(1-self.sparsity)*100:.2f}% density)

## ML Readiness Assessment
"""

        ml_readiness = results.get('ml_readiness', {})
        for approach, ready in ml_readiness.items():
            status = "✅ Ready" if ready else "❌ Not Ready"
            report += f"- {approach.replace('_', ' ').title()}: {status}\n"

        report += "\n## Preprocessing Requirements\n"
        for need in results.get('preprocessing_needed', []):
            report += f"- {need}\n"

        report += "\n## Recommended Libraries\n"
        for lib in results.get('recommended_libraries', []):
            report += f"- **{lib['library']}** ({lib['priority']} priority): {lib['reason']}\n"

        return report

# Usage example
def run_dataset_analysis():
    """Run complete dataset analysis"""
    analyzer = DatasetAnalyzer()
    results = analyzer.analyze_dataset_completeness()
    report = analyzer.generate_analysis_report()

    print(report)
    return results
