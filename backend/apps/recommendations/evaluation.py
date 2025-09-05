"""
Evaluation Framework for Recommendation Algorithms
"""
import logging
import time
import math
from typing import Dict, List, Tuple, Any, Optional, Iterable
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
import pandas as pd
from django.db.models import Q, Count, Avg
from django.utils import timezone
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from functools import lru_cache

from apps.movies.models import Movie, MovieReview
from apps.users.models import User
from apps.recommendations.models import RecommendationResult
from apps.recommendations.services import CollaborativeFilteringService

logger = logging.getLogger(__name__)


class RecommendationEvaluator:
    """
    Comprehensive evaluation framework for recommendation algorithms
    """

    def __init__(self):
        self.cf_service = CollaborativeFilteringService()
        self.logger = logging.getLogger(__name__)

    def evaluate_collaborative_filtering(self, test_size: float = 0.2,
                                       min_ratings: int = 10,
                                       max_users: int = 1000,
                                       shrinkage_alpha: Optional[float] = None) -> Dict[str, Any]:
        """
        Evaluate Collaborative Filtering algorithm
        """
        self.logger.info("Starting Collaborative Filtering evaluation...")

        # Apply optional shrinkage alpha for this evaluation run
        original_alpha = getattr(self.cf_service, 'shrinkage_alpha', 10)
        if shrinkage_alpha is not None:
            try:
                self.cf_service.shrinkage_alpha = float(shrinkage_alpha)
            except Exception:
                self.cf_service.shrinkage_alpha = original_alpha

        # Prepare test data
        test_data = self._prepare_test_data(test_size, min_ratings, max_users)

        if not test_data:
            return {"error": "Insufficient test data"}

        # Run evaluation
        results = {
            'algorithm': 'collaborative_filtering',
            'test_config': {
                'test_size': test_size,
                'min_ratings': min_ratings,
                'max_users': max_users,
                'total_users': len(test_data['test_users']),
                'total_predictions': len(test_data['test_ratings'])
            },
            'metrics': {},
            'performance': {},
            'quality_gates': {}
        }

        # Calculate accuracy metrics
        results['metrics'] = self._calculate_accuracy_metrics(
            test_data['predictions'],
            test_data['actual_ratings']
        )

        # Calculate ranking metrics
        results['ranking'] = self._calculate_ranking_metrics(
            test_data['per_user_test'],
            test_data['per_user_predictions']
        )

        # Calculate coverage metrics
        results['coverage'] = self._calculate_coverage_metrics(
            test_data['test_users']
        )

        # Calculate diversity metrics
        results['diversity'] = self._calculate_diversity_metrics(
            test_data['test_users']
        )

        # Performance analysis
        results['performance'] = self._analyze_performance(test_data)

        # Quality gates analysis
        results['quality_gates'] = self._analyze_quality_gates(test_data)

        self.logger.info(f"Evaluation completed. MAE: {results['metrics']['mae']:.4f}")

        # Restore original alpha to avoid side effects
        try:
            self.cf_service.shrinkage_alpha = original_alpha
        except Exception:
            pass

        return results

    def evaluate_cf_alpha_grid(self,
                               alphas: List[float],
                               test_size: float = 0.2,
                               min_ratings: int = 10,
                               max_users: int = 1000) -> List[Dict[str, Any]]:
        """
        Run evaluation over a grid of shrinkage alpha values.
        Returns list of result dicts augmented with 'shrinkage_alpha'.
        """
        results: List[Dict[str, Any]] = []
        for a in alphas:
            try:
                res = self.evaluate_collaborative_filtering(
                    test_size=test_size,
                    min_ratings=min_ratings,
                    max_users=max_users,
                    shrinkage_alpha=a,
                )
                if isinstance(res, dict):
                    res = {**res, 'shrinkage_alpha': float(a)}
                results.append(res)
            except Exception as e:
                self.logger.warning("Alpha %.3f evaluation failed: %s", a, e)
                continue
        return results

    def _prepare_test_data(self, test_size: float, min_ratings: int,
                          max_users: int) -> Dict[str, Any]:
        """
        Prepare test data for evaluation.

        - Loại bỏ data leakage bằng cách tạm thời patch MovieReview.objects.filter
        - Trả về cấu trúc per-user để tính ranking metrics sau này.
        """
        # Get users with sufficient ratings
        users = User.objects.annotate(
            rating_count=Count('moviereview', filter=Q(moviereview__rating__isnull=False))
        ).filter(
            rating_count__gte=min_ratings
        ).order_by('-rating_count')[:max_users]

        if len(users) < 10:
            self.logger.warning("Không đủ users để đánh giá (found %d)", len(users))
            return None

        test_data = {
            'test_users': [],               # list user_id used in evaluation
            'test_ratings': [],             # flattened records: dicts with user/movie/pred/actual
            'predictions': [],              # flattened predicted values (for accuracy)
            'actual_ratings': [],           # flattened actual ratings
            'per_user_test': {},            # user_id -> [movie_id, ...] (ground-truth test items)
            'per_user_predictions': {},     # user_id -> [(movie_id, score), ...] (ranked)
            'skipped_users': 0
        }

        for user in users:
            # Get all ratings for user (only USER reviews with rating)
            ratings_qs = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            ).select_related('movie')

            # convert to list for train_test_split and to avoid re-evaluating queryset
            all_ratings = list(ratings_qs)
            if len(all_ratings) < min_ratings:
                self.logger.debug("User %s has < min_ratings after fetch, skipping", user.id)
                continue

            # Split into train/test (stratified is not necessary here)
            train_ratings_objs, test_ratings_objs = train_test_split(
                all_ratings, test_size=test_size, random_state=42
            )

            # Ground-truth test items
            test_movie_ids = [r.movie.id for r in test_ratings_objs]
            if not test_movie_ids:
                self.logger.debug("No test items for user %s after split, skipping", user.id)
                continue

            # Temporarily patch MovieReview.objects.filter to exclude test movies for this user
            original_filter = MovieReview.objects.filter

            def safe_filter(*args, **kwargs):
                qs = original_filter(*args, **kwargs)
                # Only exclude test movies when querying for the current user
                if 'user' in kwargs and kwargs['user'] == user:
                    qs = qs.exclude(movie_id__in=test_movie_ids)
                return qs

            MovieReview.objects.filter = safe_filter

            try:
                # Get recommendations using patched filter (no data leakage)
                recommendations = self.cf_service.generate_collaborative_recommendations(
                    user, limit=50, context='evaluation'
                )

                # Normalize recommendations into list of tuples (movie_id, score)
                per_user_preds = []
                if recommendations:
                    # case A: list of dicts with 'movie' and 'predicted_rating'
                    if isinstance(recommendations[0], dict):
                        for rec in recommendations:
                            try:
                                movie_obj = rec.get('movie')
                                score = rec.get('predicted_rating') or rec.get('score') or rec.get('pred')
                                if movie_obj is not None and score is not None:
                                    per_user_preds.append((movie_obj.id, float(score)))
                            except Exception:
                                continue
                    # case B: list of tuples (movie_id, score)
                    elif isinstance(recommendations[0], (list, tuple)) and len(recommendations[0]) >= 2:
                        for mid, score in recommendations:
                            per_user_preds.append((int(mid), float(score)))
                    # case C: list of Movie objects (cached) -> no scores
                    elif hasattr(recommendations[0], 'id'):
                        # Build movie id list; get predicted scores via predict_rating per item
                        movie_ids = [m.id for m in recommendations]
                        for mid in movie_ids:
                            # cf_service should implement predict_rating(user_id, movie_id)
                            try:
                                score = self.cf_service.predict_rating(user, mid)
                                if score is not None:
                                    per_user_preds.append((mid, float(score)))
                            except AttributeError:
                                # predict_rating not implemented -> we cannot get scores for this user
                                self.logger.info("Skipping user %s - cached recommendations without scores and no predict_rating()", user.id)
                                per_user_preds = []
                                break
                            except Exception:
                                continue

                # If after all attempts we have no predictions for this user, skip user
                if not per_user_preds:
                    self.logger.debug("No predictions with scores for user %s; skipping from eval", user.id)
                    test_data['skipped_users'] += 1
                    continue

                # Sort predictions by score desc
                per_user_preds.sort(key=lambda x: x[1], reverse=True)

                # For each test rating, try to obtain predicted rating from per_user_preds (or fallback to predict_rating)
                movie_score_map = {mid: score for mid, score in per_user_preds}
                any_prediction_for_test = False

                for r in test_ratings_objs:
                    movie_id = r.movie.id
                    actual = float(r.rating)
                    predicted = movie_score_map.get(movie_id)

                    if predicted is None:
                        # fallback: call predict_rating if available
                        try:
                            predicted = self.cf_service.predict_rating(user, movie_id)
                        except Exception:
                            predicted = None

                    if predicted is not None:
                        any_prediction_for_test = True
                        test_data['predictions'].append(float(predicted))
                        test_data['actual_ratings'].append(actual)
                        test_data['test_ratings'].append({
                            'user_id': user.id,
                            'movie_id': movie_id,
                            'predicted': float(predicted),
                            'actual': actual
                        })

                if not any_prediction_for_test:
                    self.logger.debug("User %s had no predicted values for their test items; skipping", user.id)
                    test_data['skipped_users'] += 1
                    continue

                # Populate per-user structures
                test_data['test_users'].append(user.id)
                test_data['per_user_test'][user.id] = test_movie_ids
                test_data['per_user_predictions'][user.id] = per_user_preds

            except Exception as e:
                self.logger.warning("Error generating recommendations for user %s: %s", user.id, e)
                test_data['skipped_users'] += 1
                continue
            finally:
                # Restore original filter
                MovieReview.objects.filter = original_filter

        # End for users
        return test_data

    def _calculate_accuracy_metrics(self, predictions: List[float],
                                  actuals: List[float]) -> Dict[str, float]:
        """
        Calculate accuracy metrics
        """
        if not predictions or not actuals:
            return {'mae': 0.0, 'rmse': 0.0, 'mape': 0.0}

        mae = mean_absolute_error(actuals, predictions)
        rmse = np.sqrt(mean_squared_error(actuals, predictions))

        # Calculate MAPE
        mape = np.mean(np.abs((np.array(actuals) - np.array(predictions)) / np.array(actuals))) * 100

        return {
            'mae': round(mae, 4),
            'rmse': round(rmse, 4),
            'mape': round(mape, 2)
        }

    @lru_cache(maxsize=1000)
    def _ndcg_at_k(self, ranked_list_tuple: tuple, ground_truth_tuple: tuple, k: int) -> float:
        """Compute NDCG@k (binary relevance: relevant if in ground_truth)."""
        ranked_list = list(ranked_list_tuple)
        ground_truth = set(ground_truth_tuple)

        dcg = 0.0
        for i, item in enumerate(ranked_list[:k]):
            rel = 1.0 if item in ground_truth else 0.0
            denom = math.log2(i + 2)  # i starts at 0
            dcg += (2**rel - 1) / denom
        # ideal DCG: all relevant items are ranked at top
        ideal_hits = min(len(ground_truth), k)
        idcg = sum((2**1 - 1) / math.log2(i + 2) for i in range(ideal_hits))
        return dcg / idcg if idcg > 0 else 0.0

    def _precision_recall_ndcg_user(self, ranked_list: List[int], ground_truth: Iterable[int], k: int) -> Tuple[float, float, float, float]:
        """Return (precision@k, recall@k, ndcg@k, f1@k) for single user"""
        gt_set = set(ground_truth)
        if not gt_set:
            return 0.0, 0.0, 0.0, 0.0
        topk = ranked_list[:k]
        hits = sum(1 for mid in topk if mid in gt_set)
        precision = hits / k
        recall = hits / len(gt_set)
        ndcg = self._ndcg_at_k(tuple(ranked_list), tuple(ground_truth), k)
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        return precision, recall, ndcg, f1

    def _generate_user_ranked_list_via_cf(self, user, test_movie_ids: List[int], limit: int = 100) -> List[Tuple[int, float]]:
        """
        Build a ranked candidate list for `user` using CollaborativeFilteringService.
        Optimized version with batch processing and memory efficiency.
        """
        cf = self.cf_service

        # Temporarily patch MovieReview.objects.filter to exclude test movies
        original_filter = MovieReview.objects.filter

        def safe_filter(*args, **kwargs):
            qs = original_filter(*args, **kwargs)
            if 'user' in kwargs and kwargs['user'] == user:
                qs = qs.exclude(movie_id__in=test_movie_ids)
            return qs

        MovieReview.objects.filter = safe_filter

        try:
            # Get similar users (no data leakage due to patched filter)
            similar_users = cf.find_similar_users(user, limit=100)
            if not similar_users:
                return []

            similar_user_ids = [getattr(u, 'id', u) for u, _ in similar_users]

            # Get user's already rated movies (including test movies for exclusion)
            user_seen = set(MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            ).values_list('movie_id', flat=True))
            user_seen.update(test_movie_ids)

            # Get candidate movies with limit for memory efficiency
            candidate_qs = MovieReview.objects.filter(
                user_id__in=similar_user_ids,
                review_type='USER',
                rating__gte=4.0,
                rating__isnull=False
            ).exclude(movie_id__in=user_seen).select_related('movie').order_by('-rating')[:500]  # Limit early

            # Build candidate unique list efficiently
            candidates = []
            seen_candidates = set()
            for r in candidate_qs:
                mid = r.movie.id
                if mid not in seen_candidates:
                    candidates.append(mid)
                    seen_candidates.add(mid)
                if len(candidates) >= 200:  # Reasonable limit
                    break

            if not candidates:
                return []

            # Batch predict ratings for better performance
            scored = []
            for mid in candidates:
                try:
                    pred = cf.predict_rating(user, mid)
                    if pred is not None:
                        scored.append((mid, float(pred)))
                except Exception:
                    continue

            # Sort descending
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:limit]

        finally:
            # Restore original filter
            MovieReview.objects.filter = original_filter

    def _calculate_ranking_metrics(self,
                                   per_user_test: Dict[int, List[int]],
                                   per_user_predictions: Dict[int, List[Tuple[int, float]]],
                                   k_list: List[int] = [5, 10],
                                   expand_candidates_if_needed: bool = True) -> Dict[str, float]:
        """
        Calculate Precision@K, Recall@K, NDCG@K, F1@K
        """
        # accumulators
        results = {}
        # per-k accumulators
        per_k_precisions = {k: [] for k in k_list}
        per_k_recalls = {k: [] for k in k_list}
        per_k_ndcgs = {k: [] for k in k_list}
        per_k_f1s = {k: [] for k in k_list}

        total_users_evaluated = 0

        for user_id, ground_truth in per_user_test.items():
            # get a user object
            try:
                user_obj = User.objects.get(id=user_id)
            except User.DoesNotExist:
                continue

            # get predictions for this user if provided
            preds = per_user_predictions.get(user_id, []) or []

            # If preds is empty or too small, optionally expand using CF
            if (not preds or len(preds) < max(k_list)) and expand_candidates_if_needed:
                # build ranked list via CF (this will call predict_rating for many candidates)
                scored = self._generate_user_ranked_list_via_cf(user_obj, ground_truth, limit=max(k_list, 100))
                preds = scored

            # If still no preds, skip user
            if not preds:
                continue

            # ranked movie id list
            ranked_movie_ids = [mid for mid, _ in preds]

            # compute metrics for each k
            for k in k_list:
                p, r, n, f1 = self._precision_recall_ndcg_user(ranked_movie_ids, ground_truth, k)
                per_k_precisions[k].append(p)
                per_k_recalls[k].append(r)
                per_k_ndcgs[k].append(n)
                per_k_f1s[k].append(f1)

            total_users_evaluated += 1

        # Aggregate (mean) across users with confidence intervals
        for k in k_list:
            precisions = per_k_precisions[k]
            recalls = per_k_recalls[k]
            ndcgs = per_k_ndcgs[k]
            f1s = per_k_f1s[k]

            if precisions:
                results[f'precision_at_{k}'] = float(np.mean(precisions))
                results[f'precision_at_{k}_std'] = float(np.std(precisions))
                results[f'recall_at_{k}'] = float(np.mean(recalls))
                results[f'recall_at_{k}_std'] = float(np.std(recalls))
                results[f'ndcg_at_{k}'] = float(np.mean(ndcgs))
                results[f'ndcg_at_{k}_std'] = float(np.std(ndcgs))
                results[f'f1_at_{k}'] = float(np.mean(f1s))
                results[f'f1_at_{k}_std'] = float(np.std(f1s))
            else:
                results[f'precision_at_{k}'] = 0.0
                results[f'recall_at_{k}'] = 0.0
                results[f'ndcg_at_{k}'] = 0.0
                results[f'f1_at_{k}'] = 0.0

        results['evaluated_users'] = int(total_users_evaluated)
        return results

    def _calculate_coverage_metrics(self, test_users: List[int]) -> Dict[str, float]:
        """
        Calculate coverage metrics
        """
        total_users = User.objects.count()
        total_movies = Movie.objects.count()

        # Calculate user coverage
        user_coverage = len(test_users) / total_users * 100

        # Calculate movie coverage (simplified)
        recommended_movies = RecommendationResult.objects.filter(
            user_id__in=test_users
        ).values('movie_id').distinct().count()

        movie_coverage = recommended_movies / total_movies * 100

        return {
            'user_coverage': round(user_coverage, 2),
            'movie_coverage': round(movie_coverage, 2),
            'catalog_coverage': round(movie_coverage, 2)
        }

    def _calculate_diversity_metrics(self, test_users: List[int]) -> Dict[str, float]:
        """
        Calculate diversity metrics
        """
        # This is a simplified version - can be enhanced later
        return {
            'intra_list_diversity': 0.0,
            'inter_list_diversity': 0.0,
            'novelty_score': 0.0
        }

    def _analyze_performance(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze algorithm performance
        """
        return {
            'total_predictions': len(test_data['predictions']),
            'successful_predictions': len([p for p in test_data['predictions'] if p > 0]),
            'average_prediction_time': 0.0,
            'memory_usage': 0.0
        }

    def _analyze_quality_gates(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze quality gates performance
        """
        return {
            'common_movies_gate': {
                'pass_rate': 0.0,
                'filtered_users': 0
            },
            'similarity_gate': {
                'pass_rate': 0.0,
                'filtered_users': 0
            },
            'support_gate': {
                'pass_rate': 0.0,
                'filtered_movies': 0
            }
        }

    def compare_algorithms(self, algorithms: List[str]) -> Dict[str, Any]:
        """
        Compare multiple recommendation algorithms
        """
        results = {}

        for algorithm in algorithms:
            if algorithm == 'collaborative_filtering':
                results[algorithm] = self.evaluate_collaborative_filtering()
            # Add other algorithms here

        return results

    def generate_evaluation_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a comprehensive evaluation report
        """
        report = f"""
# Recommendation Algorithm Evaluation Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Algorithm: {results.get('algorithm', 'Unknown')}

### Test Configuration
- Test Size: {results.get('test_config', {}).get('test_size', 0)}
- Min Ratings: {results.get('test_config', {}).get('min_ratings', 0)}
- Total Users: {results.get('test_config', {}).get('total_users', 0)}
- Total Predictions: {results.get('test_config', {}).get('total_predictions', 0)}

### Accuracy Metrics
- MAE: {results.get('metrics', {}).get('mae', 0):.4f}
- RMSE: {results.get('metrics', {}).get('rmse', 0):.4f}
- MAPE: {results.get('metrics', {}).get('mape', 0):.2f}%

### Ranking Metrics
- Precision@5: {results.get('ranking', {}).get('precision_at_5', 0):.4f}
- Recall@5: {results.get('ranking', {}).get('recall_at_5', 0):.4f}
- NDCG@5: {results.get('ranking', {}).get('ndcg_at_5', 0):.4f}
- F1@5: {results.get('ranking', {}).get('f1_at_5', 0):.4f}
- Precision@10: {results.get('ranking', {}).get('precision_at_10', 0):.4f}
- Recall@10: {results.get('ranking', {}).get('recall_at_10', 0):.4f}
- NDCG@10: {results.get('ranking', {}).get('ndcg_at_10', 0):.4f}
- F1@10: {results.get('ranking', {}).get('f1_at_10', 0):.4f}

### Coverage Metrics
- User Coverage: {results.get('coverage', {}).get('user_coverage', 0):.2f}%
- Movie Coverage: {results.get('coverage', {}).get('movie_coverage', 0):.2f}%
- Catalog Coverage: {results.get('coverage', {}).get('catalog_coverage', 0):.2f}%

### Performance Analysis
- Total Predictions: {results.get('performance', {}).get('total_predictions', 0)}
- Successful Predictions: {results.get('performance', {}).get('successful_predictions', 0)}
        """

        return report


# Global evaluator instance
evaluator = RecommendationEvaluator()
