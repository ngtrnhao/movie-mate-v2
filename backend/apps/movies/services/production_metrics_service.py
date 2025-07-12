from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q, F
from apps.movies.models import Movie, ProductionMetrics
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class ProductionMetricsService:
    """
    Service để tính toán production metrics tự động cho movies
    Cải thiện MovieProductionMetrics với calculated values
    """

    # Performance score weights
    PERFORMANCE_WEIGHTS = {
        'views': 0.35,          # Page views
        'user_engagement': 0.30, # Reviews, ratings, favorites
        'content_quality': 0.25, # Based on quality score
        'freshness': 0.10       # Recent activity
    }

    # Score calculation constants
    VIEW_SCORE_THRESHOLD = 10000  # Views needed for max view score
    ENGAGEMENT_SCORE_THRESHOLD = 100  # Engagements for max score

    def __init__(self):
        self.calculation_version = "1.0"

    def calculate_production_metrics(self, movie: Movie, save: bool = True) -> Dict:
        """
        Tính toán toàn bộ production metrics cho một movie

        Args:
            movie: Movie instance
            save: Có lưu vào database không

        Returns:
            Dict chứa tất cả production metrics
        """
        try:
            # Get or create production metrics record
            production_metrics, created = ProductionMetrics.objects.get_or_create(
                movie=movie,
                defaults={
                    'homepage_views': 0,
                    'detail_page_views': 0,
                    'trailer_plays': 0,
                    'search_appearances': 0,
                    'mobile_views': 0,
                    'desktop_views': 0,
                    'tablet_views': 0,
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                }
            )

            # Calculate current metrics
            current_metrics = self._calculate_current_metrics(movie, production_metrics)

            # Calculate performance scores
            performance_scores = self._calculate_performance_scores(movie, current_metrics)

            # Calculate engagement rates
            engagement_rates = self._calculate_engagement_rates(current_metrics)

            # Calculate overall performance score
            overall_performance = self._calculate_overall_performance(
                current_metrics, performance_scores
            )

            # Get trending information
            trending_info = self._calculate_trending_metrics(movie, current_metrics)

            # Prepare metrics data
            metrics_data = {
                **current_metrics,
                **performance_scores,
                **engagement_rates,
                'overall_performance_score': overall_performance,
                **trending_info,
                'last_calculated_at': timezone.now(),
                'auto_calculated': True,
                'calculation_version': self.calculation_version,
                'updated_at': timezone.now()
            }

            # Save to database if requested
            if save:
                self._save_production_metrics(production_metrics, metrics_data)

            logger.info(f"Production metrics calculated for movie {movie.id}: {overall_performance:.1f}/10.0")
            return metrics_data

        except Exception as e:
            logger.error(f"Error calculating production metrics for movie {movie.id}: {str(e)}")
            raise

    def _calculate_current_metrics(self, movie: Movie, production_metrics: ProductionMetrics) -> Dict:
        """Tính toán current metrics từ database"""

        # Get basic metrics from ProductionMetrics model
        homepage_views = production_metrics.homepage_views
        detail_page_views = production_metrics.detail_page_views
        trailer_plays = production_metrics.trailer_plays

        # Reviews and ratings count from existing fields
        reviews_count = production_metrics.review_count
        avg_user_rating = production_metrics.average_user_rating

        # Calculate engagement from recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_reviews = 0
        recent_favorites = 0

        # Try to get recent reviews if reviews relationship exists
        try:
            if hasattr(movie, 'reviews'):
                recent_reviews = movie.reviews.filter(created_at__gte=thirty_days_ago).count()
        except:
            recent_reviews = 0

        # Estimate favorites count from engagement rate and views if available
        total_views = homepage_views + detail_page_views
        estimated_favorites = int(total_views * (production_metrics.engagement_rate / 100)) if total_views > 0 else 0

        # Total engagement score
        total_engagement = estimated_favorites + reviews_count + recent_reviews

        return {
            'homepage_views': homepage_views,
            'detail_page_views': detail_page_views,
            'trailer_plays': trailer_plays,
            'search_appearances': production_metrics.search_appearances,
            'mobile_views': production_metrics.mobile_views,
            'desktop_views': production_metrics.desktop_views,
            'tablet_views': production_metrics.tablet_views,
            'reviews_count': reviews_count,
            'avg_user_rating': round(float(avg_user_rating), 2) if avg_user_rating else 0.0,
            'recent_reviews_count': recent_reviews,
            'recent_favorites_count': recent_favorites,
            'estimated_favorites_count': estimated_favorites,
            'total_engagement_count': total_engagement,
            'click_through_rate': float(production_metrics.click_through_rate),
            'engagement_rate': float(production_metrics.engagement_rate),
            'performance_score': float(production_metrics.performance_score),
            'trending_score': float(production_metrics.trending_score)
        }

    def _calculate_performance_scores(self, movie: Movie, current_metrics: Dict) -> Dict:
        """Tính toán performance scores"""

        # Views performance (0-10 scale)
        total_views = current_metrics['homepage_views'] + current_metrics['detail_page_views']
        views_score = min((total_views / self.VIEW_SCORE_THRESHOLD) * 10, 10.0)

        # User engagement performance
        engagement_score = min(
            (current_metrics['total_engagement_count'] / self.ENGAGEMENT_SCORE_THRESHOLD) * 10,
            10.0
        )

        # Content quality performance (from quality metrics)
        content_quality_score = 0.0
        if hasattr(movie, 'quality_metrics') and movie.quality_metrics:
            content_quality_score = movie.quality_metrics.quality_score or 0.0

        # Freshness score (based on recent activity)
        freshness_score = 0.0
        if current_metrics['recent_reviews_count'] > 0:
            freshness_score += 3.0
        if current_metrics['recent_favorites_count'] > 0:
            freshness_score += 2.0

        # Release date freshness (newer movies get higher score)
        if movie.release_date:
            days_since_release = (timezone.now().date() - movie.release_date).days
            if days_since_release < 30:
                freshness_score += 5.0
            elif days_since_release < 180:
                freshness_score += 3.0
            elif days_since_release < 365:
                freshness_score += 1.0

        freshness_score = min(freshness_score, 10.0)

        return {
            'views_performance_score': round(views_score, 2),
            'engagement_performance_score': round(engagement_score, 2),
            'content_quality_performance_score': round(content_quality_score, 2),
            'freshness_performance_score': round(freshness_score, 2)
        }

    def _calculate_engagement_rates(self, current_metrics: Dict) -> Dict:
        """Tính toán engagement rates"""

        total_views = current_metrics['homepage_views'] + current_metrics['detail_page_views']

        # Calculate rates (avoid division by zero)
        if total_views > 0:
            favorites_rate = (current_metrics['estimated_favorites_count'] / total_views) * 100
            reviews_rate = (current_metrics['reviews_count'] / total_views) * 100
            trailer_play_rate = (current_metrics['trailer_plays'] / total_views) * 100
        else:
            favorites_rate = reviews_rate = trailer_play_rate = 0.0

        # Detail page conversion rate
        if current_metrics['homepage_views'] > 0:
            detail_conversion_rate = (current_metrics['detail_page_views'] / current_metrics['homepage_views']) * 100
        else:
            detail_conversion_rate = 0.0

        return {
            'favorites_rate': round(favorites_rate, 4),
            'reviews_rate': round(reviews_rate, 4),
            'trailer_play_rate': round(trailer_play_rate, 4),
            'detail_conversion_rate': round(detail_conversion_rate, 4)
        }

    def _calculate_overall_performance(self, current_metrics: Dict, performance_scores: Dict) -> float:
        """Tính toán overall performance score"""

        overall_score = (
            performance_scores['views_performance_score'] * self.PERFORMANCE_WEIGHTS['views'] +
            performance_scores['engagement_performance_score'] * self.PERFORMANCE_WEIGHTS['user_engagement'] +
            performance_scores['content_quality_performance_score'] * self.PERFORMANCE_WEIGHTS['content_quality'] +
            performance_scores['freshness_performance_score'] * self.PERFORMANCE_WEIGHTS['freshness']
        )

        return round(overall_score, 2)

    def _calculate_trending_metrics(self, movie: Movie, current_metrics: Dict) -> Dict:
        """Tính toán trending metrics"""

        # Is trending if has significant recent activity
        is_trending = (
            current_metrics['recent_reviews_count'] >= 5 or
            current_metrics['recent_favorites_count'] >= 10 or
            current_metrics['total_engagement_count'] >= 50
        )

        # Trending score based on recent activity velocity
        trending_score = 0.0
        if current_metrics['recent_reviews_count'] > 0:
            trending_score += min(current_metrics['recent_reviews_count'] * 2, 20)
        if current_metrics['recent_favorites_count'] > 0:
            trending_score += min(current_metrics['recent_favorites_count'], 30)

        trending_score = min(trending_score, 100.0)

        # Trending category
        if trending_score >= 80:
            trending_category = "viral"
        elif trending_score >= 50:
            trending_category = "hot"
        elif trending_score >= 20:
            trending_category = "rising"
        else:
            trending_category = "stable"

        return {
            'is_trending': is_trending,
            'trending_score': round(trending_score, 2),
            'trending_category': trending_category
        }

    def _save_production_metrics(self, production_metrics: ProductionMetrics, metrics_data: Dict):
        """Lưu production metrics vào database"""
        try:
            with transaction.atomic():
                # Update existing record
                for key, value in metrics_data.items():
                    if hasattr(production_metrics, key):
                        setattr(production_metrics, key, value)

                production_metrics.save()
                logger.info(f"Production metrics updated for movie {production_metrics.movie.id}")

        except Exception as e:
            logger.error(f"Error saving production metrics for movie {production_metrics.movie.id}: {str(e)}")
            raise

    def bulk_calculate_production_metrics(self, movie_ids: List[int] = None, batch_size: int = 100) -> Dict:
        """
        Bulk calculate production metrics cho nhiều movies

        Args:
            movie_ids: List movie IDs cần tính. None = tất cả movies
            batch_size: Số movies xử lý mỗi batch

        Returns:
            Dict chứa statistics
        """
        if movie_ids:
            queryset = Movie.objects.filter(id__in=movie_ids)
        else:
            queryset = Movie.objects.all()

        total_count = queryset.count()
        processed_count = 0
        error_count = 0

        logger.info(f"Starting bulk production metrics calculation for {total_count} movies")

        # Process in batches
        for i in range(0, total_count, batch_size):
            batch_movies = list(queryset[i:i+batch_size].select_related().prefetch_related(
                'quality_metrics'
            ))

            for movie in batch_movies:
                try:
                    self.calculate_production_metrics(movie, save=True)
                    processed_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error calculating production metrics for movie {movie.id}: {str(e)}")

            logger.info(f"Processed batch {i//batch_size + 1}: {processed_count}/{total_count}")

        return {
            'total_movies': total_count,
            'processed_successfully': processed_count,
            'errors': error_count,
            'success_rate': (processed_count / total_count) * 100 if total_count > 0 else 0
        }

    @classmethod
    def get_performance_distribution(cls) -> Dict:
        """Lấy thống kê phân bố performance scores"""
        from django.db.models import Q

        performance_ranges = [
            ('excellent', Q(overall_performance_score__gte=8.0)),
            ('good', Q(overall_performance_score__gte=6.0, overall_performance_score__lt=8.0)),
            ('fair', Q(overall_performance_score__gte=4.0, overall_performance_score__lt=6.0)),
            ('poor', Q(overall_performance_score__lt=4.0)),
            ('not_assessed', Q(overall_performance_score__isnull=True))
        ]

        distribution = {}
        total_count = ProductionMetrics.objects.count()

        for range_name, filter_q in performance_ranges:
            count = ProductionMetrics.objects.filter(filter_q).count()
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            distribution[range_name] = {
                'count': count,
                'percentage': round(percentage, 2)
            }

        return distribution

    @classmethod
    def get_trending_movies(cls, limit: int = 10) -> List[Dict]:
        """Lấy danh sách movies đang trending"""
        trending_movies = ProductionMetrics.objects.filter(
            trending_score__gte=20.0  # Consider movies with trending score >= 20 as trending
        ).order_by('-trending_score', '-performance_score')[:limit]

        results = []
        for metrics in trending_movies:
            # Determine trending category based on score
            if metrics.trending_score >= 80:
                trending_category = "viral"
            elif metrics.trending_score >= 50:
                trending_category = "hot"
            elif metrics.trending_score >= 20:
                trending_category = "rising"
            else:
                trending_category = "stable"

            results.append({
                'movie_id': metrics.movie.id,
                'movie_title': metrics.movie.title,
                'trending_score': float(metrics.trending_score),
                'trending_category': trending_category,
                'overall_performance_score': float(metrics.performance_score),
                'total_engagement_count': metrics.review_count  # Use available field
            })

        return results

    def update_view_count(self, movie: Movie, view_type: str = 'detail'):
        """
        Update view count và recalculate metrics

        Args:
            movie: Movie instance
            view_type: 'homepage' hoặc 'detail'
        """
        try:
            production_metrics, created = ProductionMetrics.objects.get_or_create(
                movie=movie,
                defaults={
                    'homepage_views': 0,
                    'detail_page_views': 0,
                    'trailer_plays': 0,
                    'search_appearances': 0,
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                }
            )

            # Update view count
            if view_type == 'homepage':
                production_metrics.homepage_views = F('homepage_views') + 1
            elif view_type == 'detail':
                production_metrics.detail_page_views = F('detail_page_views') + 1
            elif view_type == 'trailer':
                production_metrics.trailer_plays = F('trailer_plays') + 1

            production_metrics.updated_at = timezone.now()
            production_metrics.save(update_fields=['homepage_views', 'detail_page_views', 'trailer_plays', 'updated_at'])

            # Recalculate metrics periodically (every 100 views)
            production_metrics.refresh_from_db()
            total_views = production_metrics.homepage_views + production_metrics.detail_page_views

            if total_views % 100 == 0:  # Recalculate every 100 views
                self.calculate_production_metrics(movie, save=True)

        except Exception as e:
            logger.error(f"Error updating view count for movie {movie.id}: {str(e)}")
            raise
