from django.db import transaction
from django.utils import timezone
from apps.movies.models import Movie, MovieQualityMetrics
import logging
from typing import Dict, List, Tuple, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class QualityCalculationService:
    """
    Service để tính toán quality metrics tự động cho movies
    Sử dụng normalized MovieQualityMetrics table
    """

    # Quality calculation weights
    QUALITY_WEIGHTS = {
        'basic_info': 0.30,      # Title, overview, release_date
        'visual_assets': 0.25,   # Poster, backdrop
        'metadata_richness': 0.25, # Cast, genres, trailers, keywords
        'rating_validity': 0.20  # Valid ratings from external sources
    }

    # Minimum thresholds for quality standards
    MINIMUM_QUALITY_THRESHOLD = 6.0
    COMPLETENESS_THRESHOLDS = {
        'complete': 90.0,
        'nearly_complete': 70.0,
        'partial': 50.0
    }

    def __init__(self):
        self.calculation_version = "1.0"

    def calculate_movie_quality(self, movie: Movie, save: bool = True) -> Dict:
        """
        Tính toán toàn bộ quality metrics cho một movie

        Args:
            movie: Movie instance
            save: Có lưu vào database không

        Returns:
            Dict chứa tất cả quality metrics
        """
        try:
            # Calculate individual quality scores
            basic_info_score = self._calculate_basic_info_score(movie)
            visual_assets_score = self._calculate_visual_assets_score(movie)
            metadata_richness_score = self._calculate_metadata_richness_score(movie)
            rating_validity_score = self._calculate_rating_validity_score(movie)

            # Calculate overall quality score
            overall_quality_score = (
                basic_info_score * self.QUALITY_WEIGHTS['basic_info'] +
                visual_assets_score * self.QUALITY_WEIGHTS['visual_assets'] +
                metadata_richness_score * self.QUALITY_WEIGHTS['metadata_richness'] +
                rating_validity_score * self.QUALITY_WEIGHTS['rating_validity']
            )

            # Calculate content completeness
            content_completeness = self._calculate_content_completeness(movie)

            # Check if meets minimum quality standards
            minimum_quality_met = overall_quality_score >= self.MINIMUM_QUALITY_THRESHOLD

            # Identify quality issues and suggestions
            quality_issues = self._identify_quality_issues(movie, {
                'basic_info': basic_info_score,
                'visual_assets': visual_assets_score,
                'metadata_richness': metadata_richness_score,
                'rating_validity': rating_validity_score
            })

            quality_suggestions = self._generate_quality_suggestions(quality_issues)

            # Prepare quality metrics data
            quality_data = {
                'quality_score': round(overall_quality_score, 1),
                'content_completeness': round(content_completeness, 2),
                'minimum_quality_met': minimum_quality_met,
                'basic_info_score': round(basic_info_score, 1),
                'visual_assets_score': round(visual_assets_score, 1),
                'metadata_richness_score': round(metadata_richness_score, 1),
                'rating_validity_score': round(rating_validity_score, 1),
                'quality_issues': quality_issues,
                'quality_suggestions': quality_suggestions,
                'last_quality_check': timezone.now(),
                'auto_calculated': True,
                'calculation_version': self.calculation_version
            }

            # Save to database if requested
            if save:
                self._save_quality_metrics(movie, quality_data)

            logger.info(f"Quality calculated for movie {movie.id}: {overall_quality_score:.1f}/10.0")
            return quality_data

        except Exception as e:
            logger.error(f"Error calculating quality for movie {movie.id}: {str(e)}")
            raise

    def _calculate_basic_info_score(self, movie: Movie) -> float:
        """Tính điểm thông tin cơ bản (title, overview, release_date)"""
        score = 0.0
        max_score = 10.0

        # Title (required - 40% of basic info score)
        if movie.title and movie.title.strip():
            score += 4.0

            # Bonus for having both EN and VI titles
            if movie.title_en and movie.title_vi:
                score += 1.0
            elif movie.title_en or movie.title_vi:
                score += 0.5

        # Overview (important - 40% of basic info score)
        overview_score = 0.0
        if movie.overview_en and len(movie.overview_en.strip()) > 50:
            overview_score += 2.0
        elif movie.overview_en and len(movie.overview_en.strip()) > 10:
            overview_score += 1.0

        if movie.overview_vi and len(movie.overview_vi.strip()) > 50:
            overview_score += 2.0
        elif movie.overview_vi and len(movie.overview_vi.strip()) > 10:
            overview_score += 1.0

        score += min(overview_score, 4.0)  # Cap at 4.0

        # Release date (important - 20% of basic info score)
        if movie.release_date:
            score += 2.0

        return min(score, max_score)

    def _calculate_visual_assets_score(self, movie: Movie) -> float:
        """Tính điểm tài sản hình ảnh (poster, backdrop)"""
        score = 0.0
        max_score = 10.0

        # Poster (critical - 60% of visual score)
        if movie.poster_url and movie.poster_url.strip():
            score += 6.0

        # Backdrop (good to have - 40% of visual score)
        if movie.backdrop_url and movie.backdrop_url.strip():
            score += 4.0

        return min(score, max_score)

    def _calculate_metadata_richness_score(self, movie: Movie) -> float:
        """Tính điểm độ phong phú metadata (cast, genres, trailers, keywords)"""
        score = 0.0
        max_score = 10.0

        # Genres (important - 25% of metadata score)
        genre_count = movie.genres.count()
        if genre_count >= 3:
            score += 2.5
        elif genre_count >= 1:
            score += 1.5

        # Cast (important - 35% of metadata score)
        cast_count = movie.cast.count()
        if cast_count >= 10:
            score += 3.5
        elif cast_count >= 5:
            score += 2.5
        elif cast_count >= 1:
            score += 1.5

        # Trailers (good to have - 25% of metadata score)
        trailer_count = movie.trailers.count()
        if trailer_count >= 2:
            score += 2.5
        elif trailer_count >= 1:
            score += 1.5

        # Additional metadata (15% of metadata score)
        additional_score = 0.0

        # Runtime info
        if movie.runtime and movie.runtime > 0:
            additional_score += 0.5

        # Status info
        if movie.status:
            additional_score += 0.5

        # Original title
        if movie.original_title and movie.original_title != movie.title:
            additional_score += 0.5

        score += min(additional_score, 1.5)

        return min(score, max_score)

    def _calculate_rating_validity_score(self, movie: Movie) -> float:
        """Tính điểm tính hợp lệ của rating"""
        score = 0.0
        max_score = 10.0

        # Check cached ratings
        rating_sources = 0
        total_rating_quality = 0.0

        # IMDB rating
        if movie.cached_imdb_rating and movie.cached_imdb_votes:
            rating_sources += 1
            # Higher vote count = higher quality
            if movie.cached_imdb_votes >= 10000:
                total_rating_quality += 3.0
            elif movie.cached_imdb_votes >= 1000:
                total_rating_quality += 2.5
            elif movie.cached_imdb_votes >= 100:
                total_rating_quality += 2.0
            else:
                total_rating_quality += 1.0

        # TMDB rating
        if movie.cached_tmdb_rating and movie.cached_tmdb_votes:
            rating_sources += 1
            if movie.cached_tmdb_votes >= 1000:
                total_rating_quality += 2.5
            elif movie.cached_tmdb_votes >= 100:
                total_rating_quality += 2.0
            else:
                total_rating_quality += 1.5

        # Combined rating score
        if movie.combined_rating_score:
            total_rating_quality += 2.0

        # User reviews
        user_review_count = movie.reviews.filter(review_type='USER').count()
        if user_review_count >= 10:
            total_rating_quality += 2.5
        elif user_review_count >= 5:
            total_rating_quality += 1.5
        elif user_review_count >= 1:
            total_rating_quality += 1.0

        return min(total_rating_quality, max_score)

    def _calculate_content_completeness(self, movie: Movie) -> float:
        """Tính % hoàn thiện content"""
        total_points = 0
        max_points = 0

        # Essential fields (40 points total)
        max_points += 40
        if movie.title and movie.title.strip():
            total_points += 15
        if movie.overview_en or movie.overview_vi:
            total_points += 10
        if movie.release_date:
            total_points += 10
        if movie.poster_url:
            total_points += 5

        # Important fields (35 points total)
        max_points += 35
        if movie.backdrop_url:
            total_points += 5
        if movie.genres.count() > 0:
            total_points += 10
        if movie.cast.count() > 0:
            total_points += 10
        if movie.trailers.count() > 0:
            total_points += 5
        if movie.runtime:
            total_points += 5

        # Ratings and reviews (15 points total)
        max_points += 15
        if movie.cached_imdb_rating or movie.cached_tmdb_rating:
            total_points += 10
        if movie.reviews.count() > 0:
            total_points += 5

        # Advanced metadata (10 points total)
        max_points += 10
        if movie.original_title:
            total_points += 2
        if movie.status:
            total_points += 2
        if hasattr(movie, 'moviemetadata'):
            total_points += 6

        completeness_percentage = (total_points / max_points) * 100 if max_points > 0 else 0
        return min(completeness_percentage, 100.0)

    def _identify_quality_issues(self, movie: Movie, scores: Dict[str, float]) -> List[str]:
        """Xác định các vấn đề chất lượng"""
        issues = []

        # Basic info issues
        if scores['basic_info'] < 6.0:
            if not movie.title or not movie.title.strip():
                issues.append("Missing movie title")
            if not (movie.overview_en or movie.overview_vi):
                issues.append("Missing movie overview/description")
            if not movie.release_date:
                issues.append("Missing release date")

        # Visual assets issues
        if scores['visual_assets'] < 6.0:
            if not movie.poster_url:
                issues.append("Missing movie poster")
            if not movie.backdrop_url:
                issues.append("Missing backdrop image")

        # Metadata richness issues
        if scores['metadata_richness'] < 6.0:
            if movie.genres.count() == 0:
                issues.append("No genres assigned")
            if movie.cast.count() == 0:
                issues.append("No cast information")
            if movie.trailers.count() == 0:
                issues.append("No trailers available")

        # Rating validity issues
        if scores['rating_validity'] < 4.0:
            if not (movie.cached_imdb_rating or movie.cached_tmdb_rating):
                issues.append("No external ratings available")
            if movie.reviews.count() == 0:
                issues.append("No user reviews")

        return issues

    def _generate_quality_suggestions(self, issues: List[str]) -> List[str]:
        """Tạo gợi ý cải thiện chất lượng"""
        suggestions = []

        # Map issues to suggestions
        issue_suggestions = {
            "Missing movie title": "Add a clear, descriptive movie title",
            "Missing movie overview/description": "Add movie overview in English and/or Vietnamese",
            "Missing release date": "Set the official release date",
            "Missing movie poster": "Upload high-quality movie poster image",
            "Missing backdrop image": "Add backdrop/banner image for visual appeal",
            "No genres assigned": "Assign relevant movie genres",
            "No cast information": "Add main cast and crew members",
            "No trailers available": "Upload movie trailers or teasers",
            "No external ratings available": "Sync with IMDB/TMDB for ratings",
            "No user reviews": "Encourage user reviews for community engagement"
        }

        for issue in issues:
            if issue in issue_suggestions:
                suggestions.append(issue_suggestions[issue])

        # Add general suggestions based on issue patterns
        if len(issues) > 5:
            suggestions.append("Consider comprehensive content review and update")
        elif len(issues) > 2:
            suggestions.append("Focus on completing essential movie information")

        return suggestions

    def _save_quality_metrics(self, movie: Movie, quality_data: Dict):
        """Lưu quality metrics vào database"""
        try:
            with transaction.atomic():
                quality_metrics, created = MovieQualityMetrics.objects.get_or_create(
                    movie=movie,
                    defaults=quality_data
                )

                if not created:
                    # Update existing record
                    for key, value in quality_data.items():
                        setattr(quality_metrics, key, value)
                    quality_metrics.save()

                logger.info(f"Quality metrics {'created' if created else 'updated'} for movie {movie.id}")

        except Exception as e:
            logger.error(f"Error saving quality metrics for movie {movie.id}: {str(e)}")
            raise

    def bulk_calculate_quality(self, movie_ids: List[int] = None, batch_size: int = 100) -> Dict:
        """
        Bulk calculate quality cho nhiều movies

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

        logger.info(f"Starting bulk quality calculation for {total_count} movies")

        # Process in batches
        for i in range(0, total_count, batch_size):
            batch_movies = list(queryset[i:i+batch_size].select_related().prefetch_related(
                'genres', 'cast', 'trailers', 'reviews'
            ))

            for movie in batch_movies:
                try:
                    self.calculate_movie_quality(movie, save=True)
                    processed_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error calculating quality for movie {movie.id}: {str(e)}")

            logger.info(f"Processed batch {i//batch_size + 1}: {processed_count}/{total_count}")

        return {
            'total_movies': total_count,
            'processed_successfully': processed_count,
            'errors': error_count,
            'success_rate': (processed_count / total_count) * 100 if total_count > 0 else 0
        }

    @classmethod
    def get_quality_distribution(cls) -> Dict:
        """Lấy thống kê phân bố quality scores"""
        from django.db.models import Count, Q

        quality_ranges = [
            ('excellent', Q(quality_score__gte=8.0)),
            ('good', Q(quality_score__gte=6.0, quality_score__lt=8.0)),
            ('fair', Q(quality_score__gte=4.0, quality_score__lt=6.0)),
            ('poor', Q(quality_score__lt=4.0)),
            ('not_assessed', Q(quality_score__isnull=True))
        ]

        distribution = {}
        total_count = MovieQualityMetrics.objects.count()

        for range_name, filter_q in quality_ranges:
            count = MovieQualityMetrics.objects.filter(filter_q).count()
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            distribution[range_name] = {
                'count': count,
                'percentage': round(percentage, 2)
            }

        return distribution
